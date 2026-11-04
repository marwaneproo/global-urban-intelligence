#!/usr/bin/env python3
"""
End-to-end pipeline execution and integration tests.
"""

import os
import sys
import pandas as pd
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import run_pipeline


@pytest.fixture(scope="session")
def executed_pipeline():
    """Execute the pipeline in demo mode once for the test session."""
    run_pipeline.main(mode="demo")
    return True


def test_demo_pipeline_runs(executed_pipeline):
    """Verify that the full demo pipeline executes cleanly."""
    assert executed_pipeline is True


def test_output_files_exist(executed_pipeline):
    """Verify all key deliverable files exist."""
    expected_files = [
        os.path.join(PROJECT_ROOT, "data", "processed", "urban_analytics.csv"),
        os.path.join(PROJECT_ROOT, "outputs", "reports", "data_quality_report.csv"),
        os.path.join(PROJECT_ROOT, "outputs", "reports", "pairwise_correlations.csv"),
        os.path.join(PROJECT_ROOT, "outputs", "reports", "analysis_summary.md"),
        os.path.join(PROJECT_ROOT, "outputs", "reports", "data_collection_report.md"),
        os.path.join(PROJECT_ROOT, "outputs", "reports", "cleaning_report.md"),
        os.path.join(PROJECT_ROOT, "outputs", "figures", "30_dashboard_overview.png"),
        os.path.join(PROJECT_ROOT, "outputs", "figures", "17_correlation_heatmap.png"),
    ]
    for filepath in expected_files:
        assert os.path.exists(filepath), f"Expected file not found: {filepath}"


def test_processed_data_not_empty(executed_pipeline):
    """Verify that the analytical dataset contains observations."""
    csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "urban_analytics.csv")
    df = pd.read_csv(csv_path)
    assert len(df) > 500, f"Expected > 500 rows, found {len(df)}"


def test_processed_data_columns(executed_pipeline):
    """Verify that key columns exist in the processed dataset."""
    csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "urban_analytics.csv")
    df = pd.read_csv(csv_path)
    expected_cols = ["city", "date", "parameter", "value", "temperature_mean", "source"]
    for col in expected_cols:
        assert col in df.columns, f"Column '{col}' missing from final dataset"


def test_synthetic_data_labeled(executed_pipeline):
    """Verify data provenance is correctly tagged."""
    csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "urban_analytics.csv")
    df = pd.read_csv(csv_path)
    assert "source" in df.columns
    unique_sources = df["source"].dropna().unique()
    assert any("SYNTHETIC" in s or "Open" in s for s in unique_sources)
