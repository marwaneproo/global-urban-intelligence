#!/usr/bin/env python3
"""
Tests for data cleaning / preprocessing modules.

Validates column standardization, duplicate removal, date parsing,
numeric conversion, suspicious-value flagging, and missing-value handling.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.cleaning import (
    clean_air_quality,
    clean_weather,
    clean_demographics,
    generate_cleaning_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_air_quality_df() -> pd.DataFrame:
    """Create a small sample air-quality DataFrame for testing."""
    return pd.DataFrame({
        "City": ["Paris", "Paris", "Madrid", "Madrid", "Lisbon"],
        "Parameter": ["pm25", "pm25", "pm10", "pm10", "pm25"],
        "Value": [12.5, 12.5, 45.0, "invalid", 28.3],
        "Unit": ["µg/m³"] * 5,
        "Date": [
            "2024-01-15", "2024-01-15", "2024-02-20",
            "2024-03-10", "2024-04-05",
        ],
        "Latitude": [48.8566, 48.8566, 40.4168, 40.4168, 38.7223],
        "Longitude": [2.3522, 2.3522, -3.7038, -3.7038, -9.1393],
        "Source": ["SYNTHETIC_DEMO"] * 5,
        "Station Id": ["S1", "S1", "S2", "S2", "S3"],
    })


def _sample_weather_df() -> pd.DataFrame:
    """Create a small sample weather DataFrame for testing."""
    return pd.DataFrame({
        "City": ["Paris", "Paris", "Madrid"],
        "Date": ["2024-01-15", "2024-02-20", "2024-03-10"],
        "Temperature 2m Mean": [5.2, 8.1, 15.0],
        "Relative Humidity 2m Mean": [75.0, 70.0, 55.0],
        "Precipitation Sum": [2.3, 0.0, 0.5],
        "Wind Speed 10m Mean": [12.0, 8.5, 6.0],
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCleaning:
    """Tests for the cleaning module's utility functions."""

    def test_standardize_columns(self):
        """Verify column names are lowercased and spaces replaced with underscores."""
        df = _sample_air_quality_df()
        cleaned = clean_air_quality(df)
        for col in cleaned.columns:
            assert col == col.lower(), f"Column '{col}' is not lowercased"
            assert " " not in col, f"Column '{col}' contains spaces"

    def test_remove_duplicates(self):
        """Create df with duplicates, verify removal."""
        df = _sample_air_quality_df()
        # The first two rows of our sample data are duplicates
        assert len(df) == 5
        cleaned = clean_air_quality(df)
        # After cleaning, duplicates should be removed
        assert len(cleaned) < len(df), (
            "Cleaned DataFrame should have fewer rows after duplicate removal"
        )

    def test_parse_dates(self):
        """Verify date parsing produces datetime objects."""
        df = _sample_air_quality_df()
        cleaned = clean_air_quality(df)
        date_col = "date" if "date" in cleaned.columns else None
        if date_col is None:
            # Try finding a date-like column
            date_cols = [c for c in cleaned.columns if "date" in c.lower()]
            assert date_cols, "No date column found after cleaning"
            date_col = date_cols[0]
        assert pd.api.types.is_datetime64_any_dtype(cleaned[date_col]), (
            f"Column '{date_col}' should be datetime type, "
            f"got {cleaned[date_col].dtype}"
        )

    def test_convert_numeric(self):
        """Verify numeric conversion handles invalid strings."""
        df = _sample_air_quality_df()
        # Row index 3 has "invalid" as value
        cleaned = clean_air_quality(df)
        value_col = "value" if "value" in cleaned.columns else None
        if value_col is None:
            value_cols = [c for c in cleaned.columns if "value" in c.lower()]
            assert value_cols, "No value column found after cleaning"
            value_col = value_cols[0]
        # After numeric conversion, "invalid" should become NaN (not crash)
        assert pd.api.types.is_numeric_dtype(cleaned[value_col]), (
            f"Column '{value_col}' should be numeric after cleaning"
        )

    def test_flag_suspicious_values(self):
        """Verify suspicious-value flags are added."""
        # Create data with extreme values that should be flagged
        df = pd.DataFrame({
            "City": ["Paris", "Madrid"],
            "Parameter": ["pm25", "pm25"],
            "Value": [999.0, 15.0],  # 999.0 is suspicious
            "Unit": ["µg/m³", "µg/m³"],
            "Date": ["2024-01-15", "2024-02-20"],
            "Latitude": [48.8566, 40.4168],
            "Longitude": [2.3522, -3.7038],
            "Source": ["SYNTHETIC_DEMO", "SYNTHETIC_DEMO"],
            "Station Id": ["S1", "S2"],
        })
        cleaned = clean_air_quality(df)
        # Look for suspicious / flag columns
        flag_cols = [
            c for c in cleaned.columns
            if "suspicious" in c.lower() or "flag" in c.lower() or "outlier" in c.lower()
        ]
        assert flag_cols, (
            "Expected at least one flag/suspicious column after cleaning "
            f"extreme values. Columns: {list(cleaned.columns)}"
        )

    def test_handle_missing_no_zero_fill(self):
        """Verify that missing values are NOT replaced with 0 by default."""
        df = pd.DataFrame({
            "City": ["Paris", "Madrid", "Lisbon"],
            "Parameter": ["pm25", "pm25", "pm25"],
            "Value": [12.5, np.nan, 28.3],
            "Unit": ["µg/m³"] * 3,
            "Date": ["2024-01-15", "2024-02-20", "2024-03-10"],
            "Latitude": [48.8566, 40.4168, 38.7223],
            "Longitude": [2.3522, -3.7038, -9.1393],
            "Source": ["SYNTHETIC_DEMO"] * 3,
            "Station Id": ["S1", "S2", "S3"],
        })
        cleaned = clean_air_quality(df)
        value_col = "value" if "value" in cleaned.columns else None
        if value_col is None:
            value_cols = [c for c in cleaned.columns if "value" in c.lower()]
            if value_cols:
                value_col = value_cols[0]

        if value_col and len(cleaned) == 3:
            # The NaN should NOT have been replaced with 0
            # (it may be NaN or dropped, but not 0)
            middle_val = cleaned[value_col].iloc[1] if len(cleaned) > 1 else None
            if middle_val is not None and not pd.isna(middle_val):
                assert middle_val != 0.0, (
                    "Missing values should NOT be filled with 0 by default"
                )
