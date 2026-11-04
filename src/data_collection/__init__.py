"""
Data collection subpackage for Global Urban Intelligence.

Provides modules for fetching air quality, weather, and demographic data
from public APIs, with synthetic data generation as a fallback.
"""

from src.data_collection.air_quality import (
    fetch_openaq_data,
    collect_air_quality,
    generate_synthetic_air_quality,
)
from src.data_collection.weather import (
    fetch_open_meteo_data,
    collect_weather,
    generate_synthetic_weather,
)
from src.data_collection.demographics import (
    fetch_world_bank_data,
    collect_demographics,
    generate_synthetic_demographics,
)
from src.data_collection.collect_all import run_collection

__all__ = [
    "fetch_openaq_data",
    "collect_air_quality",
    "generate_synthetic_air_quality",
    "fetch_open_meteo_data",
    "collect_weather",
    "generate_synthetic_weather",
    "fetch_world_bank_data",
    "collect_demographics",
    "generate_synthetic_demographics",
    "run_collection",
]
