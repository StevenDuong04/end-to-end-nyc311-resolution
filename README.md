# end-to-end-nyc311-resolution
Collected NYC 311 and weather data via APIs, analyzed resolution times, and built a model to predict slow requests

# NYC 311: Predicting Slow Service Request Resolution

**Business question:** A city operations manager wants to understand which complaint types and boroughs have the slowest resolution times, and predict which requests will take longer than 7 days, so they can allocate staff more effectively.

**Data sources:** NYC Open Data 311 Service Requests (Socrata API) and Open-Meteo historical weather API

**Tools:** Python, pandas, scikit-learn, requests

**Data collection:**
-

**Cleaning log (before/after row counts):**
-

**Key findings:**
-

**Recommendations:**
-

**Model and limitations:**
-

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
