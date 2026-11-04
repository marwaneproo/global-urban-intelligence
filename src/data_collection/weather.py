"""
Weather data collection module.

Fetches historical daily weather data from the Open-Meteo Archive API or
generates realistic synthetic data for demonstration purposes.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Live API helpers
# ---------------------------------------------------------------------------

def fetch_open_meteo_data(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    variables: Optional[List[str]] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Fetch historical daily weather data from Open-Meteo Archive API.

    Args:
        lat: Latitude.
        lon: Longitude.
        start_date: ISO-format start date (inclusive).
        end_date: ISO-format end date (inclusive).
        variables: List of Open-Meteo daily variable names.  Defaults to
            the standard set defined in ``settings.yaml``.
        settings: Optional dict of Open-Meteo settings from
            ``settings.yaml``.

    Returns:
        A :class:`~pandas.DataFrame` with columns:
        ``date, latitude, longitude, temperature_mean, temperature_min,
        temperature_max, humidity_mean, precipitation_sum,
        wind_speed_mean, wind_direction_dominant``.
    """
    cfg = settings or {}
    base_url = cfg.get(
        "base_url", "https://archive-api.open-meteo.com/v1/archive",
    )
    timeout = cfg.get("timeout_seconds", 30)
    retries = cfg.get("retry_attempts", 3)

    if variables is None:
        variables = cfg.get("variables", [
            "temperature_2m_mean",
            "temperature_2m_min",
            "temperature_2m_max",
            "relative_humidity_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_mean",
            "wind_direction_10m_dominant",
        ])

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(variables),
        "timezone": "UTC",
    }

    for attempt in range(1, retries + 1):
        try:
            logger.info(
                "Open-Meteo request: lat=%.4f lon=%.4f attempt=%d",
                lat, lon, attempt,
            )
            resp = requests.get(base_url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()

            daily = data.get("daily", {})
            if not daily:
                logger.warning("Open-Meteo returned no daily data.")
                return pd.DataFrame()

            # Map API variable names → our canonical column names
            col_map = {
                "time": "date",
                "temperature_2m_mean": "temperature_mean",
                "temperature_2m_min": "temperature_min",
                "temperature_2m_max": "temperature_max",
                "relative_humidity_2m_mean": "humidity_mean",
                "precipitation_sum": "precipitation_sum",
                "wind_speed_10m_mean": "wind_speed_mean",
                "wind_direction_10m_dominant": "wind_direction_dominant",
            }

            df = pd.DataFrame(daily)
            df = df.rename(columns=col_map)
            df["latitude"] = lat
            df["longitude"] = lon

            logger.info("Open-Meteo fetched %d rows for (%.4f, %.4f)",
                        len(df), lat, lon)
            return df

        except requests.exceptions.Timeout:
            logger.warning(
                "Timeout on attempt %d for (%.4f, %.4f)",
                attempt, lat, lon,
            )
            time.sleep(2 * attempt)
        except requests.exceptions.RequestException as exc:
            logger.error(
                "Request error on attempt %d for (%.4f, %.4f): %s",
                attempt, lat, lon, exc,
            )
            time.sleep(2 * attempt)

    logger.error("All retries exhausted for (%.4f, %.4f)", lat, lon)
    return pd.DataFrame()


def collect_weather(
    cities_config: Dict[str, Any],
    settings: Dict[str, Any],
) -> pd.DataFrame:
    """Collect weather data for all configured cities.

    Args:
        cities_config: Parsed ``cities.json`` dict.
        settings: Parsed ``settings.yaml`` dict.

    Returns:
        Concatenated :class:`~pandas.DataFrame` with an added ``city``
        column.
    """
    dc = settings.get("data_collection", {})
    om = dc.get("open_meteo", {})
    start_date = dc.get("start_date", "2024-01-01")
    end_date = dc.get("end_date", "2024-12-31")

    frames: List[pd.DataFrame] = []

    cities = cities_config if isinstance(cities_config, list) else cities_config.get("cities", [])
    for city in cities:
        logger.info("Collecting weather for %s", city["name"])
        df = fetch_open_meteo_data(
            lat=city["latitude"],
            lon=city["longitude"],
            start_date=start_date,
            end_date=end_date,
            settings=om,
        )
        if not df.empty:
            df["city"] = city["name"]
            df["country"] = city["country"]
            frames.append(df)

    if frames:
        result = pd.concat(frames, ignore_index=True)
        logger.info("Weather collection complete: %d total rows", len(result))
        return result

    logger.warning("No weather data collected from API.")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

def generate_synthetic_weather(
    cities_config: Dict[str, Any],
    settings: Dict[str, Any],
) -> pd.DataFrame:
    """Generate realistic synthetic daily weather data.

    City-specific seasonal patterns:
    * **Casablanca / Rabat** – mild winters, warm summers, low precip.
    * **Paris** – cold winters, warm summers, moderate precip.
    * **Madrid** – cold winters, hot dry summers, low precip.
    * **Lisbon** – mild winters, warm summers, moderate precip.

    Additional realism:
    * Daily random variation
    * Humidity inversely correlated with temperature
    * Precipitation more likely in winter
    * ``source`` column set to ``"SYNTHETIC_DEMO"``

    Args:
        cities_config: Parsed ``cities.json`` dict.
        settings: Parsed ``settings.yaml`` dict.

    Returns:
        A :class:`~pandas.DataFrame` with the standard weather schema.
    """
    np.random.seed(42)

    dc = settings.get("data_collection", {})
    syn = settings.get("synthetic", {})

    start_date = dc.get("start_date", "2024-01-01")
    end_date = dc.get("end_date", "2024-12-31")
    source_label = syn.get("label", "SYNTHETIC_DEMO")

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(dates)

    # City-specific temperature profiles:
    #   (winter_min, winter_max, summer_min, summer_max)
    city_profiles: Dict[str, Dict[str, Any]] = {
        "Casablanca": {
            "winter_temp": (12.0, 18.0),
            "summer_temp": (22.0, 30.0),
            "precip_winter_prob": 0.25,
            "precip_summer_prob": 0.05,
            "precip_mean": 4.0,
        },
        "Rabat": {
            "winter_temp": (11.0, 17.0),
            "summer_temp": (21.0, 29.0),
            "precip_winter_prob": 0.28,
            "precip_summer_prob": 0.04,
            "precip_mean": 4.5,
        },
        "Paris": {
            "winter_temp": (2.0, 8.0),
            "summer_temp": (18.0, 26.0),
            "precip_winter_prob": 0.40,
            "precip_summer_prob": 0.25,
            "precip_mean": 5.0,
        },
        "Madrid": {
            "winter_temp": (4.0, 10.0),
            "summer_temp": (25.0, 38.0),
            "precip_winter_prob": 0.30,
            "precip_summer_prob": 0.08,
            "precip_mean": 3.5,
        },
        "Lisbon": {
            "winter_temp": (10.0, 15.0),
            "summer_temp": (22.0, 30.0),
            "precip_winter_prob": 0.35,
            "precip_summer_prob": 0.06,
            "precip_mean": 5.0,
        },
    }

    records: List[Dict[str, Any]] = []

    cities = cities_config if isinstance(cities_config, list) else cities_config.get("cities", [])
    for city in cities:
        city_name = city["name"]
        lat = city["latitude"]
        lon = city["longitude"]
        country = city["country"]

        profile = city_profiles.get(city_name, city_profiles["Paris"])
        wt = profile["winter_temp"]
        st = profile["summer_temp"]
        pw_prob = profile["precip_winter_prob"]
        ps_prob = profile["precip_summer_prob"]
        p_mean = profile["precip_mean"]

        for i, date in enumerate(dates):
            month = date.month
            # Day-of-year fraction for smooth seasonal interpolation
            day_frac = date.dayofyear / 365.0
            # Cosine-based seasonal factor: 1.0 in winter, 0.0 in summer
            seasonal = 0.5 * (1.0 + np.cos(2.0 * np.pi * (day_frac - 0.05)))
            # seasonal ≈ 1 near Jan 1, ≈ 0 near Jul 1

            # Temperature --------------------------------------------------
            t_min_range = wt[0] + (st[0] - wt[0]) * (1.0 - seasonal)
            t_max_range = wt[1] + (st[1] - wt[1]) * (1.0 - seasonal)
            temp_mean_base = (t_min_range + t_max_range) / 2.0
            daily_noise = np.random.normal(0, 1.5)
            temp_mean = round(temp_mean_base + daily_noise, 1)
            diurnal = np.random.uniform(2.0, 5.0)
            temp_min = round(temp_mean - diurnal, 1)
            temp_max = round(temp_mean + diurnal, 1)

            # Humidity (inversely correlated with temperature) ---------------
            # Base humidity ~ 70 %, decreases with higher temperature
            humidity = 75.0 - 0.6 * temp_mean + np.random.normal(0, 5)
            humidity = round(float(np.clip(humidity, 20, 95)), 1)

            # Precipitation --------------------------------------------------
            precip_prob = pw_prob * seasonal + ps_prob * (1.0 - seasonal)
            if np.random.rand() < precip_prob:
                precip = round(float(np.random.exponential(p_mean)), 1)
                precip = min(precip, 50.0)
            else:
                precip = 0.0

            # Wind -----------------------------------------------------------
            wind_speed = round(float(
                np.random.gamma(2.0, 3.0) + 1.0
            ), 1)
            wind_speed = min(wind_speed, 35.0)
            wind_direction = int(np.random.uniform(0, 360))

            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "city": city_name,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "temperature_mean": temp_mean,
                "temperature_min": temp_min,
                "temperature_max": temp_max,
                "humidity_mean": humidity,
                "precipitation_sum": precip,
                "wind_speed_mean": wind_speed,
                "wind_direction_dominant": wind_direction,
                "source": source_label,
            })

    df = pd.DataFrame(records)
    logger.info("Generated synthetic weather data: %d rows", len(df))
    return df
