"""
Air quality data collection module.

Fetches air quality measurements from the OpenAQ v2 API or generates
realistic synthetic data for demonstration purposes.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)


# Live API helpers


def fetch_openaq_data(
    city_name: str,
    lat: float,
    lon: float,
    parameter: str,
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Fetch air quality measurements from the OpenAQ v2 API.

    Makes paginated HTTP requests with retry logic, rate limiting, and
    timeout handling.

    Args:
        city_name: Human-readable city name (e.g. ``"Casablanca"``).
        lat: Latitude of the city centre.
        lon: Longitude of the city centre.
        parameter: Pollutant parameter name (``"pm25"`` or ``"pm10"``).
        start_date: ISO-format start date (inclusive).
        end_date: ISO-format end date (inclusive).
        api_key: Optional OpenAQ API key for higher rate limits.
        settings: Optional dict of OpenAQ-related settings from
            ``settings.yaml``.  When *None* sensible defaults are used.

    Returns:
        A :class:`~pandas.DataFrame` with columns:
        ``city, parameter, value, unit, date_utc, latitude, longitude,
        source, station_id``.
    """
    # Unpack settings with defaults ----------------------------------------
    cfg = settings or {}
    base_url = cfg.get("base_url", "https://api.openaq.org/v2")
    limit = cfg.get("limit_per_page", 1000)
    max_pages = cfg.get("max_pages", 10)
    timeout = cfg.get("timeout_seconds", 30)
    retries = cfg.get("retry_attempts", 3)
    retry_delay = cfg.get("retry_delay_seconds", 5)
    rate_pause = cfg.get("rate_limit_pause_seconds", 1.0)

    headers: Dict[str, str] = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    all_records: List[Dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        params = {
            "city": city_name,
            "parameter": parameter,
            "date_from": start_date,
            "date_to": end_date,
            "limit": limit,
            "page": page,
            "coordinates": f"{lat},{lon}",
            "radius": 25000,  # 25 km radius
            "order_by": "datetime",
            "sort": "asc",
        }

        success = False
        for attempt in range(1, retries + 1):
            try:
                logger.info(
                    "OpenAQ request: city=%s param=%s page=%d attempt=%d",
                    city_name, parameter, page, attempt,
                )
                resp = requests.get(
                    f"{base_url}/measurements",
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )

                if resp.status_code == 429:
                    wait = retry_delay * attempt
                    logger.warning(
                        "Rate-limited by OpenAQ. Waiting %.1fs …", wait,
                    )
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])

                for rec in results:
                    all_records.append({
                        "city": city_name,
                        "parameter": rec.get("parameter", parameter),
                        "value": rec.get("value"),
                        "unit": rec.get("unit", "µg/m³"),
                        "date_utc": rec.get("date", {}).get("utc"),
                        "latitude": rec.get("coordinates", {}).get("latitude", lat),
                        "longitude": rec.get("coordinates", {}).get("longitude", lon),
                        "source": "OpenAQ",
                        "station_id": rec.get("location"),
                    })

                logger.info(
                    "  → fetched %d records (page %d)", len(results), page,
                )
                success = True
                break  # success – leave retry loop

            except requests.exceptions.Timeout:
                logger.warning(
                    "Timeout on attempt %d for %s/%s page %d",
                    attempt, city_name, parameter, page,
                )
                time.sleep(retry_delay)
            except requests.exceptions.RequestException as exc:
                logger.error(
                    "Request error on attempt %d for %s/%s page %d: %s",
                    attempt, city_name, parameter, page, exc,
                )
                time.sleep(retry_delay)

        if not success:
            logger.error(
                "All %d retries exhausted for %s/%s page %d",
                retries, city_name, parameter, page,
            )
            break  # stop paginating on persistent failure

        # If we got fewer results than the limit, we've reached the last page
        if len(results) < limit:
            break

        # Rate-limit pause between pages
        time.sleep(rate_pause)

    df = pd.DataFrame(all_records)
    logger.info(
        "OpenAQ total for %s/%s: %d rows", city_name, parameter, len(df),
    )
    return df


def collect_air_quality(
    cities_config: Dict[str, Any],
    settings: Dict[str, Any],
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Collect air quality data for all configured cities and parameters.

    Args:
        cities_config: Parsed ``cities.json`` dict.
        settings: Parsed ``settings.yaml`` dict.
        api_key: Optional OpenAQ API key.

    Returns:
        Concatenated :class:`~pandas.DataFrame` of all city / parameter
        combinations.
    """
    dc = settings.get("data_collection", {})
    oaq = dc.get("openaq", {})
    parameters = oaq.get("parameters", ["pm25", "pm10"])
    start_date = dc.get("start_date", "2024-01-01")
    end_date = dc.get("end_date", "2024-12-31")

    frames: List[pd.DataFrame] = []

    cities = cities_config if isinstance(cities_config, list) else cities_config.get("cities", [])
    for city in cities:
        for param in parameters:
            logger.info(
                "Collecting air quality: %s / %s", city["name"], param,
            )
            df = fetch_openaq_data(
                city_name=city["name"],
                lat=city["latitude"],
                lon=city["longitude"],
                parameter=param,
                start_date=start_date,
                end_date=end_date,
                api_key=api_key,
                settings=oaq,
            )
            if not df.empty:
                frames.append(df)

    if frames:
        result = pd.concat(frames, ignore_index=True)
        logger.info("Air quality collection complete: %d total rows", len(result))
        return result

    logger.warning("No air quality data collected from API.")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

def generate_synthetic_air_quality(
    cities_config: Dict[str, Any],
    settings: Dict[str, Any],
) -> pd.DataFrame:
    """Generate realistic synthetic air quality data.

    Creates daily PM2.5 and PM10 values with:
    * Seasonal patterns (winter months have 20-40 % higher values)
    * City-specific baselines
    * Daily random variation
    * Occasional pollution spikes
    * ~5 % randomly missing values

    Args:
        cities_config: Parsed ``cities.json`` dict.
        settings: Parsed ``settings.yaml`` dict.

    Returns:
        A :class:`~pandas.DataFrame` matching the live-data schema, with
        ``source`` set to ``"SYNTHETIC_DEMO"``.
    """
    np.random.seed(42)

    dc = settings.get("data_collection", {})
    syn = settings.get("synthetic", {})

    start_date = dc.get("start_date", "2024-01-01")
    end_date = dc.get("end_date", "2024-12-31")
    source_label = syn.get("label", "SYNTHETIC_DEMO")
    pm25_range = syn.get("pm25_range", [5.0, 75.0])
    pm10_range = syn.get("pm10_range", [10.0, 120.0])

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(dates)

    # City-specific baseline multipliers (relative to a "neutral" 1.0)
    city_baselines: Dict[str, float] = {
        "Casablanca": 1.15,
        "Rabat": 1.05,
        "Paris": 1.00,
        "Madrid": 1.12,
        "Lisbon": 0.95,
    }

    # Parameter-level mean / std relative to range
    param_specs: Dict[str, Dict[str, Any]] = {
        "pm25": {
            "base_mean": 22.0,
            "base_std": 8.0,
            "unit": "µg/m³",
            "clip_lo": pm25_range[0],
            "clip_hi": pm25_range[1],
        },
        "pm10": {
            "base_mean": 38.0,
            "base_std": 14.0,
            "unit": "µg/m³",
            "clip_lo": pm10_range[0],
            "clip_hi": pm10_range[1],
        },
    }

    records: List[Dict[str, Any]] = []

    cities = cities_config if isinstance(cities_config, list) else cities_config.get("cities", [])
    for city in cities:
        city_name = city["name"]
        lat = city["latitude"]
        lon = city["longitude"]
        country = city["country"]
        baseline_mult = city_baselines.get(city_name, 1.0)

        for param_name, spec in param_specs.items():
            base_mean = spec["base_mean"] * baseline_mult
            base_std = spec["base_std"]
            unit = spec["unit"]
            clip_lo = spec["clip_lo"]
            clip_hi = spec["clip_hi"]

            for i, date in enumerate(dates):
                month = date.month

                # Seasonal multiplier: winter (Nov-Feb) → 1.20 – 1.40
                if month in (11, 12, 1, 2):
                    seasonal = 1.0 + 0.20 + 0.20 * np.random.rand()
                elif month in (3, 4, 9, 10):
                    seasonal = 1.0 + 0.05 * np.random.rand()
                else:  # summer
                    seasonal = 0.85 + 0.10 * np.random.rand()

                # Daily variation
                daily_noise = np.random.normal(0, base_std)

                # Occasional spikes (~3 % of days)
                spike = 0.0
                if np.random.rand() < 0.03:
                    spike = np.random.uniform(15.0, 40.0)

                value = base_mean * seasonal + daily_noise + spike
                value = float(np.clip(value, clip_lo, clip_hi))

                records.append({
                    "city": city_name,
                    "country": country,
                    "parameter": param_name,
                    "value": round(value, 2),
                    "unit": unit,
                    "date": date.strftime("%Y-%m-%d"),
                    "latitude": lat,
                    "longitude": lon,
                    "source": source_label,
                    "station_id": f"{city_name.upper()}-AQ-001",
                })

    df = pd.DataFrame(records)

    # Inject ~5 % missing values into the 'value' column
    n_total = len(df)
    n_missing = int(n_total * 0.05)
    missing_idx = np.random.choice(df.index, size=n_missing, replace=False)
    df.loc[missing_idx, "value"] = np.nan

    logger.info(
        "Generated synthetic air quality data: %d rows (%d missing values)",
        n_total, n_missing,
    )
    return df
