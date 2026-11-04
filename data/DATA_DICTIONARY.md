# Data Dictionary — Global Urban Intelligence

## Overview

This document describes all datasets used in the project, their columns, data types, units, valid ranges, and provenance.

---

## 1. Air Quality Data (`air_quality_raw.csv` → `air_quality_cleaned.csv`)

| Column | Type | Unit | Description | Valid Range | Source |
|--------|------|------|-------------|-------------|--------|
| city | string | — | City name where measurement was taken | Casablanca, Rabat, Paris, Madrid, Lisbon | Config |
| country | string | — | Country name | Morocco, France, Spain, Portugal | Config |
| parameter | string | — | Air quality parameter measured | pm25, pm10 | OpenAQ / Synthetic |
| value | float | µg/m³ | Measured concentration value | PM2.5: 0–500, PM10: 0–600 | OpenAQ / Synthetic |
| unit | string | — | Measurement unit | µg/m³ | OpenAQ / Synthetic |
| date | datetime | — | Date of measurement (UTC) | 2024-01-01 to 2024-12-31 | OpenAQ / Synthetic |
| latitude | float | degrees | Latitude of monitoring station | -90 to 90 | OpenAQ / Config |
| longitude | float | degrees | Longitude of monitoring station | -180 to 180 | OpenAQ / Config |
| source | string | — | Data provenance label | "OpenAQ" or "SYNTHETIC_DEMO" | System |
| station_id | string | — | Monitoring station identifier | — | OpenAQ / Generated |

### Derived columns (after transformation)

| Column | Type | Description |
|--------|------|-------------|
| year | int | Year extracted from date |
| month | int | Month (1–12) |
| quarter | int | Quarter (1–4) |
| day | int | Day of month |
| day_of_week | int | Day of week (0=Monday, 6=Sunday) |
| day_name | string | Day name (Monday–Sunday) |
| is_weekend | bool | True if Saturday or Sunday |
| season | string | Season (Winter, Spring, Summer, Autumn) |
| aqi_category | string | AQI category based on PM2.5 value |
| value_is_missing | bool | Flag indicating original value was missing |
| value_suspicious | bool | Flag for values outside expected range |

---

## 2. Weather Data (`weather_raw.csv` → `weather_cleaned.csv`)

| Column | Type | Unit | Description | Valid Range | Source |
|--------|------|------|-------------|-------------|--------|
| city | string | — | City name | Casablanca, Rabat, Paris, Madrid, Lisbon | Config |
| date | datetime | — | Date of observation | 2024-01-01 to 2024-12-31 | Open-Meteo / Synthetic |
| latitude | float | degrees | Latitude | -90 to 90 | Config |
| longitude | float | degrees | Longitude | -180 to 180 | Config |
| temperature_mean | float | °C | Mean daily temperature | -50 to 60 | Open-Meteo / Synthetic |
| temperature_min | float | °C | Minimum daily temperature | -50 to 60 | Open-Meteo / Synthetic |
| temperature_max | float | °C | Maximum daily temperature | -50 to 60 | Open-Meteo / Synthetic |
| humidity_mean | float | % | Mean relative humidity | 0 to 100 | Open-Meteo / Synthetic |
| precipitation_sum | float | mm | Total daily precipitation | 0 to 500 | Open-Meteo / Synthetic |
| wind_speed_mean | float | km/h | Mean wind speed at 10m | 0 to 200 | Open-Meteo / Synthetic |
| wind_direction_dominant | float | degrees | Dominant wind direction | 0 to 360 | Open-Meteo / Synthetic |
| source | string | — | Data provenance | "Open-Meteo" or "SYNTHETIC_DEMO" | System |

### Derived columns (after transformation)

| Column | Type | Description |
|--------|------|-------------|
| year | int | Year extracted from date |
| month | int | Month (1–12) |
| quarter | int | Quarter (1–4) |
| season | string | Season |
| temperature_range | float | temperature_max - temperature_min |
| is_rainy | bool | True if precipitation_sum > 0.1 mm |

---

## 3. Demographics Data (`demographics_raw.csv` → `demographics_cleaned.csv`)

| Column | Type | Unit | Description | Valid Range | Source |
|--------|------|------|-------------|-------------|--------|
| country | string | — | Country name | Morocco, France, Spain, Portugal | Config |
| country_code | string | — | ISO 2-letter country code | MA, FR, ES, PT | Config |
| indicator_id | string | — | World Bank indicator code | See below | World Bank / Synthetic |
| indicator_name | string | — | Human-readable indicator name | — | World Bank / Synthetic |
| year | int | — | Year of observation | 2018–2023 | World Bank / Synthetic |
| value | float | varies | Indicator value | varies by indicator | World Bank / Synthetic |
| geographic_level | string | — | **Always "country"** — these are NOT city-level data | "country" | System |
| source | string | — | Data provenance | "World Bank" or "SYNTHETIC_DEMO" | System |

### Indicator details

| Indicator ID | Name | Unit | Typical Range |
|-------------|------|------|---------------|
| SP.POP.TOTL | Total Population | persons | varies |
| SP.POP.GROW | Population Growth | % annual | -2 to 5 |
| SP.URB.TOTL.IN.ZS | Urban Population (% of total) | % | 30 to 100 |
| SP.URB.GROW | Urban Population Growth | % annual | -2 to 5 |

> **⚠️ IMPORTANT:** Demographic indicators are at the **country level**, not the city level. A country's total population is NOT the population of any single city within it. This distinction is maintained throughout the analysis.

---

## 4. Integrated Analytical Dataset (`urban_analytics.csv`)

This is the final integrated dataset combining air quality, weather, and demographic context.

| Column | Type | Description | Source Dataset |
|--------|------|-------------|----------------|
| city | string | City name | All |
| date | datetime | Date | Air Quality + Weather |
| parameter | string | Air quality parameter | Air Quality |
| value | float | Pollutant concentration (µg/m³) | Air Quality |
| temperature_mean | float | Mean temperature (°C) | Weather |
| temperature_min | float | Min temperature (°C) | Weather |
| temperature_max | float | Max temperature (°C) | Weather |
| humidity_mean | float | Mean humidity (%) | Weather |
| precipitation_sum | float | Precipitation (mm) | Weather |
| wind_speed_mean | float | Wind speed (km/h) | Weather |
| season | string | Season | Derived |
| month | int | Month | Derived |
| aqi_category | string | AQI category | Derived from PM2.5 |
| country | string | Country name | Config |
| country_population | float | Country population (NOT city) | Demographics |
| urban_population_pct | float | Urban population % (country level) | Demographics |
| demographic_level | string | Always "country" | System |
| source | string | Data provenance label | System |

### Join Strategy

1. **Air Quality ↔ Weather**: LEFT JOIN on `city` + `date`
2. **Integrated ↔ Demographics**: LEFT JOIN on `country` (most recent year)

### Important Notes

- Missing weather data for a given city+date results in NaN weather columns (not dropped)
- Demographic data is repeated for all rows of the same country (country-level, not city-level)
- The `demographic_level` column explicitly marks this distinction
- The `source` column indicates whether data is real or synthetic

---

## 5. Data Quality Considerations

| Issue | Description | Handling |
|-------|-------------|----------|
| Missing values | Some measurements may be absent | Flagged with `_is_missing` columns; NOT replaced with zero |
| Suspicious values | Values outside expected physical ranges | Flagged with `_suspicious` columns; retained unless clearly erroneous |
| Temporal gaps | Not all cities have data for every day | Gaps are documented; analysis accounts for unequal coverage |
| Spatial representativeness | Monitoring stations may not represent the whole city | Documented as a limitation |
| Unit inconsistencies | Different sources may use different units | Validated and standardized during cleaning |
| Synthetic data | When real data is unavailable | Clearly labeled as "SYNTHETIC_DEMO" in source column |

---

## 6. File Naming Convention

| Layer | Directory | Pattern | Example |
|-------|-----------|---------|---------|
| Raw | `data/raw/` | `{dataset}_raw.csv` | `air_quality_raw.csv` |
| Interim | `data/interim/` | `{dataset}_cleaned.csv`, `{dataset}_transformed.csv` | `air_quality_cleaned.csv` |
| Processed | `data/processed/` | descriptive names | `urban_analytics.csv` |
| Outputs | `outputs/datasets/` | descriptive names | `city_summaries.csv` |
