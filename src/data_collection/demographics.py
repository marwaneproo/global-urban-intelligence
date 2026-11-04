"""
Demographics data collection module.

Fetches development indicators from the World Bank API v2 or generates
realistic synthetic demographic data for demonstration purposes.
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

def fetch_world_bank_data(
    country_code: str,
    indicator_id: str,
    year_range: str = "2018:2023",
    settings: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Fetch a single indicator from the World Bank API v2.

    Args:
        country_code: ISO-3166 alpha-2 country code (e.g. ``"MA"``).
        indicator_id: World Bank indicator ID
            (e.g. ``"SP.POP.TOTL"``).
        year_range: Colon-separated year range (e.g. ``"2018:2023"``).
        settings: Optional dict of World Bank settings from
            ``settings.yaml``.

    Returns:
        A :class:`~pandas.DataFrame` with columns:
        ``country, country_code, indicator_id, indicator_name, year,
        value, geographic_level, source``.
    """
    cfg = settings or {}
    base_url = cfg.get("base_url", "https://api.worldbank.org/v2")
    per_page = cfg.get("per_page", 100)
    timeout = cfg.get("timeout_seconds", 30)

    url = f"{base_url}/country/{country_code}/indicator/{indicator_id}"
    params = {
        "date": year_range,
        "format": "json",
        "per_page": per_page,
    }

    retries = 3
    for attempt in range(1, retries + 1):
        try:
            logger.info(
                "World Bank request: %s / %s attempt=%d",
                country_code, indicator_id, attempt,
            )
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()

            # The World Bank API returns a list:
            #   [metadata_dict, list_of_records]
            if not isinstance(payload, list) or len(payload) < 2:
                logger.warning(
                    "Unexpected World Bank response for %s / %s",
                    country_code, indicator_id,
                )
                return pd.DataFrame()

            raw_records = payload[1]
            if raw_records is None:
                logger.warning(
                    "No data returned for %s / %s",
                    country_code, indicator_id,
                )
                return pd.DataFrame()

            records: List[Dict[str, Any]] = []
            for rec in raw_records:
                records.append({
                    "country": rec.get("country", {}).get("value", ""),
                    "country_code": country_code,
                    "indicator_id": indicator_id,
                    "indicator_name": rec.get("indicator", {}).get("value", ""),
                    "year": int(rec.get("date", 0)),
                    "value": rec.get("value"),
                    "geographic_level": "country",
                    "source": "World Bank",
                })

            df = pd.DataFrame(records)
            logger.info(
                "World Bank fetched %d rows for %s / %s",
                len(df), country_code, indicator_id,
            )
            return df

        except requests.exceptions.Timeout:
            logger.warning(
                "Timeout on attempt %d for %s / %s",
                attempt, country_code, indicator_id,
            )
            time.sleep(2 * attempt)
        except requests.exceptions.RequestException as exc:
            logger.error(
                "Request error on attempt %d for %s / %s: %s",
                attempt, country_code, indicator_id, exc,
            )
            time.sleep(2 * attempt)

    logger.error(
        "All retries exhausted for %s / %s", country_code, indicator_id,
    )
    return pd.DataFrame()


def collect_demographics(
    cities_config: Dict[str, Any],
    settings: Dict[str, Any],
) -> pd.DataFrame:
    """Collect demographic indicators for all configured countries.

    Args:
        cities_config: Parsed ``cities.json`` dict.
        settings: Parsed ``settings.yaml`` dict.

    Returns:
        Concatenated :class:`~pandas.DataFrame` of all country / indicator
        combinations.
    """
    dc = settings.get("data_collection", {})
    wb = dc.get("world_bank", {})
    indicators = wb.get("indicators", [])
    year_range = wb.get("year_range", "2018:2023")

    if isinstance(cities_config, list):
        wb_countries = {c.get("country_code", ""): c.get("country", "") for c in cities_config}
    else:
        wb_countries = cities_config.get("world_bank_countries") or {
            c.get("country_code", ""): c.get("country", "") for c in cities_config.get("cities", [])
        }
    frames: List[pd.DataFrame] = []

    for code, country_name in wb_countries.items():
        for ind in indicators:
            logger.info(
                "Collecting demographics: %s (%s) / %s",
                country_name, code, ind["id"],
            )
            df = fetch_world_bank_data(
                country_code=code,
                indicator_id=ind["id"],
                year_range=year_range,
                settings=wb,
            )
            if not df.empty:
                frames.append(df)

    if frames:
        result = pd.concat(frames, ignore_index=True)
        logger.info(
            "Demographics collection complete: %d total rows", len(result),
        )
        return result

    logger.warning("No demographics data collected from API.")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

def generate_synthetic_demographics(
    cities_config: Dict[str, Any],
    settings: Dict[str, Any],
) -> pd.DataFrame:
    """Generate realistic synthetic demographic data at the **country** level.

    Uses realistic base values for:
    * **Morocco** – ~37 M pop, 1.2 % growth, 64 % urban
    * **France** – ~67 M pop, 0.3 % growth, 81 % urban
    * **Spain** – ~47 M pop, 0.1 % growth, 81 % urban
    * **Portugal** – ~10 M pop, −0.3 % growth, 66 % urban

    Args:
        cities_config: Parsed ``cities.json`` dict.
        settings: Parsed ``settings.yaml`` dict.

    Returns:
        A :class:`~pandas.DataFrame` with columns:
        ``country, country_code, indicator_id, indicator_name, year,
        value, geographic_level, source``.
    """
    np.random.seed(42)

    dc = settings.get("data_collection", {})
    wb = dc.get("world_bank", {})
    syn = settings.get("synthetic", {})
    source_label = syn.get("label", "SYNTHETIC_DEMO")

    year_range_str = wb.get("year_range", "2018:2023")
    yr_start, yr_end = (int(y) for y in year_range_str.split(":"))
    years = list(range(yr_start, yr_end + 1))

    indicators = wb.get("indicators", [
        {"id": "SP.POP.TOTL", "name": "Total Population"},
        {"id": "SP.POP.GROW", "name": "Population Growth (%)"},
        {"id": "SP.URB.TOTL.IN.ZS", "name": "Urban Population (%)"},
        {"id": "SP.URB.GROW", "name": "Urban Population Growth (%)"},
    ])

    # Country-level baselines
    country_profiles: Dict[str, Dict[str, Any]] = {
        "MA": {
            "country": "Morocco",
            "SP.POP.TOTL": {"base": 36_500_000, "annual_growth": 0.012},
            "SP.POP.GROW": {"base": 1.2, "std": 0.05},
            "SP.URB.TOTL.IN.ZS": {"base": 63.5, "annual_delta": 0.3},
            "SP.URB.GROW": {"base": 1.8, "std": 0.1},
        },
        "FR": {
            "country": "France",
            "SP.POP.TOTL": {"base": 67_000_000, "annual_growth": 0.003},
            "SP.POP.GROW": {"base": 0.3, "std": 0.05},
            "SP.URB.TOTL.IN.ZS": {"base": 80.7, "annual_delta": 0.15},
            "SP.URB.GROW": {"base": 0.6, "std": 0.05},
        },
        "ES": {
            "country": "Spain",
            "SP.POP.TOTL": {"base": 47_000_000, "annual_growth": 0.001},
            "SP.POP.GROW": {"base": 0.1, "std": 0.1},
            "SP.URB.TOTL.IN.ZS": {"base": 80.5, "annual_delta": 0.1},
            "SP.URB.GROW": {"base": 0.3, "std": 0.05},
        },
        "PT": {
            "country": "Portugal",
            "SP.POP.TOTL": {"base": 10_300_000, "annual_growth": -0.003},
            "SP.POP.GROW": {"base": -0.3, "std": 0.1},
            "SP.URB.TOTL.IN.ZS": {"base": 65.5, "annual_delta": 0.2},
            "SP.URB.GROW": {"base": 0.4, "std": 0.08},
        },
    }

    if isinstance(cities_config, list):
        wb_countries = {c.get("country_code", ""): c.get("country", "") for c in cities_config}
    else:
        wb_countries = cities_config.get("world_bank_countries") or {
            c.get("country_code", ""): c.get("country", "") for c in cities_config.get("cities", [])
        }
    records: List[Dict[str, Any]] = []

    for code, country_name in wb_countries.items():
        profile = country_profiles.get(code)
        if profile is None:
            logger.warning("No synthetic profile for country code %s", code)
            continue

        for ind in indicators:
            ind_id = ind["id"]
            ind_name = ind["name"]
            spec = profile.get(ind_id)
            if spec is None:
                continue

            for year in years:
                year_offset = year - yr_start

                if ind_id == "SP.POP.TOTL":
                    value = spec["base"] * (
                        (1 + spec["annual_growth"]) ** year_offset
                    )
                    value = int(round(value + np.random.normal(0, 50_000)))
                elif ind_id in ("SP.POP.GROW", "SP.URB.GROW"):
                    value = round(
                        spec["base"] + np.random.normal(0, spec["std"]),
                        2,
                    )
                elif ind_id == "SP.URB.TOTL.IN.ZS":
                    value = round(
                        spec["base"]
                        + spec["annual_delta"] * year_offset
                        + np.random.normal(0, 0.1),
                        2,
                    )
                else:
                    value = round(np.random.uniform(0, 100), 2)

                records.append({
                    "country": profile["country"],
                    "country_code": code,
                    "indicator_id": ind_id,
                    "indicator_name": ind_name,
                    "year": year,
                    "value": value,
                    "geographic_level": "country",
                    "source": source_label,
                })

    df = pd.DataFrame(records)
    logger.info("Generated synthetic demographics data: %d rows", len(df))
    return df
