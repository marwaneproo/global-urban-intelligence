#!/usr/bin/env python3
"""
Tests for data collection modules.

Tests the synthetic data generators to verify correct schema, ranges,
and labeling without requiring network access.
"""

import json
import os
import sys

import pandas as pd
import pytest
import yaml

# ---------------------------------------------------------------------------
# Path setup – ensure project root is on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.data_collection.air_quality import generate_synthetic_air_quality
from src.data_collection.weather import generate_synthetic_weather
from src.data_collection.demographics import generate_synthetic_demographics

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def config():
    """Load cities.json and settings.yaml once for the module."""
    cities_path = os.path.join(PROJECT_ROOT, "config", "cities.json")
    settings_path = os.path.join(PROJECT_ROOT, "config", "settings.yaml")

    with open(cities_path, "r", encoding="utf-8") as f:
        cities_cfg = json.load(f)

    with open(settings_path, "r", encoding="utf-8") as f:
        settings_cfg = yaml.safe_load(f)

    return {"cities": cities_cfg, "settings": settings_cfg}


@pytest.fixture(scope="module")
def cities_list(config):
    """Return the list of city dicts from config."""
    return config["cities"]["cities"]


@pytest.fixture(scope="module")
def settings(config):
    """Return the settings dict."""
    return config["settings"]


@pytest.fixture(scope="module")
def synthetic_air_quality(cities_list, settings):
    """Generate synthetic air quality data once for the module."""
    return generate_synthetic_air_quality(cities_list, settings)


@pytest.fixture(scope="module")
def synthetic_weather(cities_list, settings):
    """Generate synthetic weather data once for the module."""
    return generate_synthetic_weather(cities_list, settings)


@pytest.fixture(scope="module")
def synthetic_demographics(cities_list, settings):
    """Generate synthetic demographics data once for the module."""
    return generate_synthetic_demographics(cities_list, settings)


# ---------------------------------------------------------------------------
# Air Quality Tests
# ---------------------------------------------------------------------------

class TestSyntheticAirQuality:
    """Tests for the synthetic air quality data generator."""

    def test_synthetic_air_quality_shape(self, synthetic_air_quality: pd.DataFrame):
        """Verify output has expected columns and > 0 rows."""
        df = synthetic_air_quality
        assert isinstance(df, pd.DataFrame), "Output must be a DataFrame"
        assert len(df) > 0, "DataFrame must have at least one row"
        assert len(df.columns) >= 9, "DataFrame must have at least 9 columns"

    def test_synthetic_air_quality_columns(self, synthetic_air_quality: pd.DataFrame):
        """Verify all required columns are present."""
        required_columns = {
            "city", "parameter", "value", "unit", "date",
            "latitude", "longitude", "source", "station_id",
        }
        actual_columns = set(synthetic_air_quality.columns.str.lower())
        missing = required_columns - actual_columns
        assert not missing, f"Missing required columns: {missing}"

    def test_synthetic_air_quality_values(self, synthetic_air_quality: pd.DataFrame):
        """Verify PM2.5 values in [0, 500] and PM10 values in [0, 600]."""
        df = synthetic_air_quality

        pm25_mask = df["parameter"].str.lower() == "pm25"
        if pm25_mask.any():
            pm25_values = df.loc[pm25_mask, "value"]
            assert pm25_values.min() >= 0, "PM2.5 values must be >= 0"
            assert pm25_values.max() <= 500, "PM2.5 values must be <= 500"

        pm10_mask = df["parameter"].str.lower() == "pm10"
        if pm10_mask.any():
            pm10_values = df.loc[pm10_mask, "value"]
            assert pm10_values.min() >= 0, "PM10 values must be >= 0"
            assert pm10_values.max() <= 600, "PM10 values must be <= 600"

    def test_synthetic_air_quality_cities(self, synthetic_air_quality: pd.DataFrame, cities_list):
        """Verify all 5 cities are present in the data."""
        expected_cities = {city["name"] for city in cities_list}
        actual_cities = set(synthetic_air_quality["city"].unique())
        missing = expected_cities - actual_cities
        assert not missing, f"Missing cities: {missing}"
        assert len(expected_cities) == 5, "Expected exactly 5 cities"

    def test_synthetic_air_quality_source_label(self, synthetic_air_quality: pd.DataFrame):
        """Verify source column is 'SYNTHETIC_DEMO'."""
        sources = synthetic_air_quality["source"].unique()
        assert len(sources) == 1, "Expected exactly one source label"
        assert sources[0] == "SYNTHETIC_DEMO", (
            f"Source must be 'SYNTHETIC_DEMO', got '{sources[0]}'"
        )


# ---------------------------------------------------------------------------
# Weather Tests
# ---------------------------------------------------------------------------

class TestSyntheticWeather:
    """Tests for the synthetic weather data generator."""

    def test_synthetic_weather_shape(self, synthetic_weather: pd.DataFrame):
        """Verify output has rows and columns."""
        df = synthetic_weather
        assert isinstance(df, pd.DataFrame), "Output must be a DataFrame"
        assert len(df) > 0, "DataFrame must have at least one row"
        assert len(df.columns) >= 5, "DataFrame must have at least 5 columns"

    def test_synthetic_weather_columns(self, synthetic_weather: pd.DataFrame):
        """Verify required columns are present."""
        required_columns = {"city", "date"}
        actual_columns = set(synthetic_weather.columns.str.lower())
        missing = required_columns - actual_columns
        assert not missing, f"Missing required columns: {missing}"

    def test_synthetic_weather_temperature_range(self, synthetic_weather: pd.DataFrame):
        """Verify temperatures fall within [-50, 60] °C."""
        df = synthetic_weather
        # Find temperature columns (could be named differently)
        temp_cols = [
            c for c in df.columns
            if "temperature" in c.lower() or "temp" in c.lower()
        ]
        assert len(temp_cols) > 0, "No temperature column found"
        for col in temp_cols:
            numeric_vals = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(numeric_vals) > 0:
                assert numeric_vals.min() >= -50, (
                    f"{col} has value below -50: {numeric_vals.min()}"
                )
                assert numeric_vals.max() <= 60, (
                    f"{col} has value above 60: {numeric_vals.max()}"
                )


# ---------------------------------------------------------------------------
# Demographics Tests
# ---------------------------------------------------------------------------

class TestSyntheticDemographics:
    """Tests for the synthetic demographics data generator."""

    def test_synthetic_demographics_shape(self, synthetic_demographics: pd.DataFrame):
        """Verify output has rows and columns."""
        df = synthetic_demographics
        assert isinstance(df, pd.DataFrame), "Output must be a DataFrame"
        assert len(df) > 0, "DataFrame must have at least one row"

    def test_synthetic_demographics_geographic_level(
        self, synthetic_demographics: pd.DataFrame
    ):
        """Verify geographic_level column contains 'country'."""
        df = synthetic_demographics
        # Column might be named geographic_level or similar
        level_cols = [
            c for c in df.columns if "geographic" in c.lower() or "level" in c.lower()
        ]
        if level_cols:
            col = level_cols[0]
            values = df[col].str.lower().unique()
            assert "country" in values, (
                f"Expected 'country' in geographic_level, got {values}"
            )
        else:
            # If no explicit column, check that data is at country level
            # by verifying country_code or country column presence
            assert (
                "country" in df.columns or "country_code" in df.columns
            ), "No geographic level indicator found in demographics data"
