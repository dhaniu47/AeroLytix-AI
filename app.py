import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import ee
import pandas as pd
import numpy as np
from datetime import datetime   # ✅ ADDED

ee.Initialize()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ADDED (DOES NOT TOUCH YOUR LOGIC)
history = []

@app.get("/pollution")
def get_pollution(lat: float, lon: float, user: str = "guest"):  # ✅ added user

    point = ee.Geometry.Point([lon, lat])

    no2 = ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2") \
        .filterDate('2023-11-01', '2023-12-31') \
        .select('tropospheric_NO2_column_number_density') \
        .mean() \
        .multiply(1e6)

    value = no2.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=10000
    ).getInfo()

    no2_value = value.get('tropospheric_NO2_column_number_density', 0)

    if no2_value < 30:
        level = "LOW"
    elif no2_value < 80:
        level = "MEDIUM"
    else:
        level = "HIGH"

    # ✅ ADD ONLY THIS BLOCK (does not affect anything else)
    history.append({
        "user": user,
        "value": no2_value,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    # YOUR ORIGINAL DJANGO CALL (UNCHANGED)
    try:
        response = requests.post("http://127.0.0.1:8000/save/", json={
            "lat": lat,
            "lon": lon,
            "no2": no2_value,
            "level": level
        })
        print("Django response:", response.text)
    except Exception as e:
        print("Error sending to Django:", e)

    return {"NO2": no2_value, "level": level}


# ✅ ADD NEW API (does not interfere with anything)
@app.get("/history")
def get_history(user: str):
    return [h for h in history if h["user"] == user][-10:]


# ✅ ADD AI PREDICTION (separate, safe)
from sklearn.linear_model import LinearRegression

@app.get("/predict")
def predict(user: str):
    user_data = [h for h in history if h["user"] == user][-10:]

    if len(user_data) < 2:
        return {"prediction": 0}

    values = [d["value"] for d in user_data]

    X = np.arange(len(values)).reshape(-1, 1)
    y = np.array(values)

    model = LinearRegression()
    model.fit(X, y)

    pred = model.predict([[len(values)]])[0]

    return {"prediction": float(pred)}


# YOUR ORIGINAL TILE CODE (UNCHANGED)
@app.get("/tiles")
def get_tiles():
    india = ee.FeatureCollection("FAO/GAUL/2015/level0") \
        .filter(ee.Filter.eq('ADM0_NAME', 'India'))

    no2 = ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2") \
        .filterDate('2023-11-01', '2023-12-31') \
        .select('tropospheric_NO2_column_number_density') \
        .mean() \
        .multiply(1e6)

    smooth = no2.focal_mean(20000, 'circle', 'meters')
    zones = smooth.clip(india)

    zones = zones \
        .where(zones.lt(30), 0) \
        .where(zones.gte(30).And(zones.lt(80)), 1) \
        .where(zones.gte(80), 2)

    vis = {
        "min": 0,
        "max": 2,
        "palette": ["green", "yellow", "red"]
    }

    map_id = zones.getMapId(vis)

    return {"tile_url": map_id["tile_fetcher"].url_format}