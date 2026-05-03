import pandas as pd
from pollution.models import PollutionData

print("⚡ Fast loading started...")

df = pd.read_csv(
    'combined_data.csv',
    usecols=['NO2 (ug/m3)'],
    nrows=5000
)

# Clean column names
df.columns = df.columns.str.strip()

# 🔥 REMOVE EMPTY / NULL VALUES
df = df.dropna(subset=['NO2 (ug/m3)'])

objects = [
    PollutionData(
        lat=20.0,
        lon=77.0,
        no2=float(row),   # ensure number
        level="Medium"
    )
    for row in df['NO2 (ug/m3)']
]

PollutionData.objects.bulk_create(objects)

print("✅ DONE successfully without errors!")0