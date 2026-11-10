
import requests
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

URL = "https://archive-api.open-meteo.com/v1/archive"

# New York City coordinates
LATITUDE = 40.7128
LONGITUDE = -74.0060

START = "2025-01-01"
END = "2025-01-31"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START,
    "end_date": END,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "rain",
        "snowfall",
        "wind_speed_10m",
        "wind_direction_10m",
        "cloud_cover"
    ],
    "timezone": "America/New_York"
}

response = requests.get(URL, params=params, timeout=120)
response.raise_for_status()

data = response.json()

# Convert hourly observations into a DataFrame
df = pd.DataFrame(data["hourly"])

# Save raw weather data
df.to_csv(RAW / "weather_raw.csv", index=False)

print(f"Saved {len(df)} weather observations")
print(df.head())
print(df.info())
