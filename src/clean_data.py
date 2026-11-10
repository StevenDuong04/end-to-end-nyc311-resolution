from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

# Date ran in collect_311.py. Open-request age is measured from this date.
PULL_DATE = pd.Timestamp.today().normalize()

# NYC bounding box (approximate)
LAT_MIN, LAT_MAX = 40.4951, 40.9155
LON_MIN, LON_MAX = -74.2557, -73.7002

log = []


def log_step(step, before, after, reason):
    """Record row counts for one cleaning step."""
    log.append({"step": step, "rows_before": before, "rows_after": after,
                "rows_removed": before - after, "reason": reason})
    print(f"{step}: {before:,} -> {after:,} ({before - after:,} removed)")


# ---------------------------------------------------------------- load
df = pd.read_csv(RAW / "311_raw.csv", low_memory=False)
wr = pd.read_csv(RAW / "weather_raw.csv")
log_step("Load raw 311 data", len(df), len(df), "Starting point")

# ---------------------------------------------------------------- duplicates
before = len(df)
df = df.drop_duplicates(subset=["unique_key"], keep="first")
log_step("Drop duplicate unique_key", before, len(df), "Same request pulled twice")

# ---------------------------------------------------------------- dates
df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce")

before = len(df)
df = df.dropna(subset=["created_date"])
log_step("Drop missing/unparseable created_date", before, len(df),
         "Cannot compute timing without a creation date")

# ---------------------------------------------------------------- standardize text
before = len(df)
df["borough"] = df["borough"].str.strip().str.upper().replace("UNSPECIFIED", "UNKNOWN")
df["borough"] = df["borough"].fillna("UNKNOWN")
df["complaint_type"] = df["complaint_type"].str.strip().str.upper()
df["agency"] = df["agency"].str.strip().str.upper()
log_step("Standardize borough, complaint_type, agency", before, len(df),
         "Trim, uppercase, 'Unspecified' -> 'UNKNOWN' (no rows removed)")

# ---------------------------------------------------------------- invalid closed dates
before = len(df)
invalid_closed = df["closed_date"].notna() & (df["closed_date"] < df["created_date"])
df = df[~invalid_closed]
log_step("Remove closed_date earlier than created_date", before, len(df),
         "Impossible timing (data entry error)")

# ---------------------------------------------------------------- coordinates
has_coords = df["latitude"].notna() & df["longitude"].notna()
out_of_bounds = has_coords & ~(
    df["latitude"].between(LAT_MIN, LAT_MAX) & df["longitude"].between(LON_MIN, LON_MAX)
)
print(f"Missing coordinates (kept, flagged): {(~has_coords).sum():,}")

before = len(df)
df = df[~out_of_bounds].copy()
df["has_coords"] = df["latitude"].notna() & df["longitude"].notna()
log_step("Remove coordinates outside NYC", before, len(df),
         "Points present but outside the NYC bounding box (rows with missing coordinates are kept)")

# ---------------------------------------------------------------- open requests (flagged, not removed)
df["is_open"] = df["closed_date"].isna()
n_open = int(df["is_open"].sum())
log_step("Flag open requests (no closed_date)", len(df), len(df),
         f"{n_open:,} flagged as open, kept in file and labeled slow (open for 7+ days), excluded from resolution-time analysis")

if n_open:
    open_age = (PULL_DATE - df.loc[df["is_open"], "created_date"]).dt.days
    print("\nOpen request age (days since created, as of pull date):")
    print(open_age.describe())

# ---------------------------------------------------------------- resolution time and target
df["resolution_hours"] = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600
df["resolution_days"] = df["resolution_hours"] / 24

closed_mask = df["resolution_hours"].notna()
df["is_slow"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
df.loc[closed_mask, "is_slow"] = (df.loc[closed_mask, "resolution_hours"] > 7 * 24).astype(int)
open_mask = df["is_open"]
df.loc[open_mask, "is_slow"] = (
    (PULL_DATE - df.loc[open_mask, "created_date"]).dt.days > 7
).astype(int)

print("\nClosed requests:", int(closed_mask.sum()))
print("Slow (> 7 days):", int((df["is_slow"] == 1).sum()))
print("Over 365 days:", int((df["resolution_days"] > 365).sum()))

# ---------------------------------------------------------------- time features
df["created_hour"] = df["created_date"].dt.hour
df["day_of_week"] = df["created_date"].dt.day_name()
df["month"] = df["created_date"].dt.month
df["is_weekend"] = df["created_date"].dt.day_of_week >= 5

# ---------------------------------------------------------------- weather: hourly -> daily
df["date"] = df["created_date"].dt.date

wr["time"] = pd.to_datetime(wr["time"], errors="coerce")
wr = wr.dropna(subset=["time"]).copy()
wr["date"] = wr["time"].dt.date

daily_weather = (
    wr.groupby("date")
    .agg({
        "temperature_2m": "mean",
        "relative_humidity_2m": "mean",
        "precipitation": "sum",
        "rain": "sum",
        "snowfall": "sum",
        "wind_speed_10m": "mean",
        "wind_direction_10m": "mean",
        "cloud_cover": "mean",
    })
    .reset_index()
)

before = len(df)
df = df.merge(daily_weather, on="date", how="left", validate="many_to_one")
log_step("Merge daily weather on date", before, len(df),
         "Left join, row count must not change")
print("Missing weather values:", int(df["temperature_2m"].isna().sum()))

# ---------------------------------------------------------------- coverage check
print("\nDate coverage:", df["created_date"].min(), "to", df["created_date"].max())

# ---------------------------------------------------------------- save
df.to_csv(PROC / "311_clean.csv", index=False)
log_df = pd.DataFrame(log)
log_df.to_csv(PROC / "cleaning_log.csv", index=False)
print(f"\nSaved {len(df):,} rows to {PROC / '311_clean.csv'}")

# Markdown table for the README
print("\n| Step | Rows before | Rows after | Removed | Reason |")
print("|---|---|---|---|---|")
for r in log:
    print(f"| {r['step']} | {r['rows_before']:,} | {r['rows_after']:,} | "
          f"{r['rows_removed']:,} | {r['reason']} |")