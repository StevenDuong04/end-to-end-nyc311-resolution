# end-to-end-nyc311-resolution
Collected NYC 311 and weather data via APIs, analyzed resolution times, and built a model to predict slow requests

# NYC 311: Predicting Slow Service Request Resolution

**Business question:** A city operations manager wants to understand which complaint types and boroughs have the slowest resolution times, and predict which requests will take longer than 7 days, so they can allocate staff more effectively.

**Data sources:** NYC Open Data 311 Service Requests (Socrata API) and Open-Meteo historical weather API

**Tools:** Python, pandas, scikit-learn, requests

**Data collection:**
- **311 requests:** NYC Open Data Socrata API (no app token), pulled in pages of 25,000 rows with retry and backoff on throttling. Requests created 1 to 31 January 2025, 348,180 rows (the full month, below the 500,000 row cap).
- **Weather:** Open-Meteo historical archive API for NYC, hourly values (Open-Meteo, America/ New York timezone) aggregated to daily (mean temperature, humidity, wind speed, wind direction and cloud cover; summed precipitation, rain and snowfall) and joined on request creation date.
- Both collection scripts and the cleaning script are rerunnable from `src/`. Raw data is not committed.
- All data comes from a single coordinate in Manhattan, so every borough gets the same weather, so local differences such as snowfall variation is not captured.

**Cleaning log (before/after row counts):**
| Step | Rows before | Rows after | Removed | Reason |
|---|---|---|---|---|
| Load raw 311 data | 348,180 | 348,180 | 0 | Starting point |
| Drop duplicate unique_key | 348,180 | 348,180 | 0 | Same request pulled twice |
| Drop missing/unparseable created_date | 348,180 | 348,180 | 0 | Cannot compute timing without a creation date |
| Standardize borough, complaint_type, agency | 348,180 | 348,180 | 0 | Trim, uppercase, 'Unspecified' -> 'UNKNOWN' (no rows removed) |
| Remove closed_date earlier than created_date | 348,180 | 348,081 | 99 | Impossible timing (data entry error) |
| Remove coordinates outside NYC | 348,081| 348,081 | 0 | Points present but outsidethe NYC bounding box (rows with missing coordinates are kept) |
| Flag open requests (no closed_date) | 348,081 | 348,081 | 0 | 2,592 flagged as open, kept in file and labeled slow (open for 7+ days), excluded from resolution-time analysis |
| Merge daily weather on date | 348,081 | 348,081 | 0 | Left join, row count must notchange |

**Issues found:**
- **Impossible timing:** 99 requests (0.03%) had a closed date earlier than the created date and were removed.
- **Open requests:** 2,592 requests (0.7%) had no closed date. They had been open for 647 to 677 days (median 663) as of the data pull in November 2026, so they are labeled slow rather than dropped. Dropping them would have removed some of the slowest cases and made resolution times look better than they are. They are excluded from resolution-time statistics because they have no completed duration.
- **Missing coordinates:** 3,099 requests (0.9%) had no latitude or longitude. They were kept and flagged, since location is only needed for some analysis. No coordinates fell outside the NYC bounding box.
- **Extreme resolutions:** 425 closed requests (0.12%) took over 365 days. They were kept (still correctly "slow") and medians are used instead of means for resolution time.
- **Class imbalance:** 14.8% of requests are slow overall (14.2% of closed requests), so accuracy alone is not a useful model metric.
- **Duplicates, missing created dates, and missing weather:** none found.

**Key findings:**
-

**Recommendations:**
-

**Model and limitations:**
- Covers a single month (January 2025), so it does not capture seasonal variation. Winter weather effects may not generalize to summer.
- "Slow" is defined as taking more than 7 days to close. Some agencies close requests administratively, so a closed date may not always mean the problem was fixed.
- Open requests are assumed slow because they had been open far longer than 7 days, but their true resolution time is unknown.

**How to reproduce:**
1. Install `requirements.txt`
2. Run the collection script in `src/`
3. Run the notebooks in order

## Definition of Done
- [ ] Rerunnable collection scripts for 311 and weather
- [ ] Cleaning log with before/after row counts
- [ ] EDA: resolution time by agency, borough, complaint type, weather
- [ ] Written recommendations with estimated impact
- [ ] Feature engineering and train/test split
- [ ] 2+ models compared with cross-validation
- [ ] Feature importance and limitations section
