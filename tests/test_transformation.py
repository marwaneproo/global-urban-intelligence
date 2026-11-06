#!/usr/bin/env python3
"""
Tests for transformation and feature engineering modules.
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.transformation import (
    add_date_features,
    add_season,
    compute_monthly_aggregates,
    compute_city_summaries,
    compute_rolling_averages,
    create_air_quality_index_category,
)


@pytest.fixture

def sample_timeseries_df():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    return pd.DataFrame({
        "city": ["Casablanca"] * 50 + ["Paris"] * 50,
        "date": dates.tolist()[:50] + dates.tolist()[:50],
        "value": np.random.uniform(10, 60, size=100),
    })


def test_add_date_features(sample_timeseries_df):
    df_transformed = add_date_features(sample_timeseries_df, date_col="date")
    expected_cols = ["year", "month", "quarter", "day", "day_of_week", "day_name", "is_weekend"]
    for col in expected_cols:
        assert col in df_transformed.columns, f"Missing feature {col}"
    assert df_transformed["year"].iloc[0] == 2024
    assert df_transformed["month"].iloc[0] == 1


def test_add_season(sample_timeseries_df):
    df_transformed = add_season(sample_timeseries_df, date_col="date", hemisphere="north")
    assert "season" in df_transformed.columns
    # Jan 1st is Winter in Northern hemisphere
    assert df_transformed["season"].iloc[0] == "Winter"


def test_monthly_aggregates(sample_timeseries_df):
    df_with_dates = add_date_features(sample_timeseries_df, date_col="date")
    monthly = compute_monthly_aggregates(
        df_with_dates,
        group_cols=["city"],
        value_cols=["value"],
        date_col="date",
    )
    assert not monthly.empty
    assert "city" in monthly.columns


def test_city_summaries(sample_timeseries_df):
    summaries = compute_city_summaries(
        sample_timeseries_df,
        city_col="city",
        value_cols=["value"],
    )
    assert len(summaries) == 2
    assert "city" in summaries.columns
    assert "value_mean" in summaries.columns
    assert "value_median" in summaries.columns


def test_compute_rolling_averages(sample_timeseries_df):
    df_rolling = compute_rolling_averages(
        sample_timeseries_df,
        value_col="value",
        windows=[7, 30],
        date_col="date",
        group_col="city",
    )
    assert "value_rolling_7" in df_rolling.columns
    assert "value_rolling_30" in df_rolling.columns


def test_aqi_category():
    assert create_air_quality_index_category(10.0) == "Good"
    assert create_air_quality_index_category(25.0) == "Moderate"
    assert create_air_quality_index_category(45.0) == "Unhealthy for Sensitive Groups"
    assert create_air_quality_index_category(100.0) == "Unhealthy"
    assert create_air_quality_index_category(200.0) == "Very Unhealthy"
    assert create_air_quality_index_category(300.0) == "Hazardous"
    assert create_air_quality_index_category(None) == "Unknown"
