import os
import pandas as pd
from pollution.models import PollutionData

def load_all_csv(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    for file in files:
        try:
            path = os.path.join(folder_path, file)
            df = pd.read_csv(path)

            columns = df.columns.str.lower()

            def find_col(possible_names):
                for name in possible_names:
                    if name in columns:
                        return name
                return None

            lat_col = find_col(["lat", "latitude"])
            lon_col = find_col(["lon", "longitude"])
            pm25_col = find_col(["pm25", "pm2.5", "pm_2_5", "pm25_value"])
            no2_col = find_col(["no2"])
            city_col = find_col(["city", "location"])

            for _, row in df.iterrows():
                PollutionData.objects.create(
                    city=row.get(city_col, "Unknown") if city_col else "Unknown",
                    lat=row.get(lat_col, 0),
                    lon=row.get(lon_col, 0),
                    pm25=row.get(pm25_col) if pm25_col else None,
                    no2=row.get(no2_col) if no2_col else None,
                )

            print(f"✅ Loaded: {file}")

        except Exception as e:
            print(f"❌ Error in {file}: {e}")