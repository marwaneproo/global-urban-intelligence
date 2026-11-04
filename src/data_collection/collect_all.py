"""
Master data collection orchestrator.

Provides :func:`run_collection` which loads project configuration,
invokes all data-collection modules (live API or synthetic fallback),
saves raw CSV files, and writes collection metadata.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd
import yaml

from src.data_collection.air_quality import (
    collect_air_quality,
    generate_synthetic_air_quality,
)
from src.data_collection.weather import (
    collect_weather,
    generate_synthetic_weather,
)
from src.data_collection.demographics import (
    collect_demographics,
    generate_synthetic_demographics,
)

logger = logging.getLogger(__name__)


def _load_config(project_root: str) -> tuple:
    """Load cities.json and settings.yaml from the config/ directory.

    Args:
        project_root: Absolute path to the project root.

    Returns:
        A tuple of ``(cities_config, settings)``.

    Raises:
        FileNotFoundError: If a required config file is missing.
    """
    cities_path = os.path.join(project_root, "config", "cities.json")
    settings_path = os.path.join(project_root, "config", "settings.yaml")

    with open(cities_path, "r", encoding="utf-8") as fh:
        cities_config = json.load(fh)
    logger.info("Loaded cities config from %s", cities_path)

    with open(settings_path, "r", encoding="utf-8") as fh:
        settings = yaml.safe_load(fh)
    logger.info("Loaded settings from %s", settings_path)

    return cities_config, settings


def _save_dataframe(
    df: pd.DataFrame,
    filepath: str,
    label: str,
) -> int:
    """Save a DataFrame as CSV and return the row count.

    Args:
        df: DataFrame to persist.
        filepath: Absolute destination path.
        label: Human-readable label for log messages.

    Returns:
        Number of rows written.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8")
    n_rows = len(df)
    logger.info("Saved %s -> %s (%d rows)", label, filepath, n_rows)
    return n_rows


def run_collection(
    mode: str = "demo",
    project_root: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """Execute the full data-collection pipeline.

    Workflow:
    1. Load ``config/cities.json`` and ``config/settings.yaml``.
    2. Depending on *mode*:
       - ``"demo"`` – generate synthetic data for all domains.
       - ``"live"`` – attempt API calls; fall back to synthetic on failure.
    3. Save raw CSV files under ``data/raw/``.
    4. Write ``data/raw/collection_metadata.json``.
    5. Return a dict of DataFrames keyed by domain name.

    Args:
        mode: Either ``"demo"`` (synthetic only) or ``"live"``
            (API-first with fallback).
        project_root: Absolute path to the project root.  When *None*,
            defaults to the directory four levels up from this file
            (i.e. the repo root).

    Returns:
        ``{"air_quality": df, "weather": df, "demographics": df}``
    """
    # Resolve project root -------------------------------------------------
    if project_root is None:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
        )
    logger.info("Project root: %s", project_root)
    logger.info("Collection mode: %s", mode)

    # Load configuration ----------------------------------------------------
    cities_config, settings = _load_config(project_root)

    # Prepare output directory ----------------------------------------------
    raw_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)

    # Retrieve optional API key from environment ----------------------------
    api_key = os.environ.get("OPENAQ_API_KEY")

    # Container for results -------------------------------------------------
    dataframes: Dict[str, pd.DataFrame] = {}
    metadata: Dict[str, Any] = {
        "collection_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "project_root": project_root,
        "datasets": {},
    }

    # ── Air Quality ────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("COLLECTING AIR QUALITY DATA")
    logger.info("=" * 60)
    try:
        if mode == "live":
            df_aq = collect_air_quality(cities_config, settings, api_key=api_key)
            if df_aq.empty:
                logger.warning(
                    "Live air quality collection returned no data – "
                    "falling back to synthetic."
                )
                df_aq = generate_synthetic_air_quality(cities_config, settings)
                aq_source = "synthetic_fallback"
            else:
                aq_source = "live_api"
        else:
            df_aq = generate_synthetic_air_quality(cities_config, settings)
            aq_source = "synthetic_demo"
    except Exception:
        logger.exception("Air quality collection failed – using synthetic.")
        df_aq = generate_synthetic_air_quality(cities_config, settings)
        aq_source = "synthetic_fallback_after_error"

    aq_path = os.path.join(raw_dir, "air_quality_raw.csv")
    aq_rows = _save_dataframe(df_aq, aq_path, "air_quality")
    dataframes["air_quality"] = df_aq
    metadata["datasets"]["air_quality"] = {
        "file": "air_quality_raw.csv",
        "rows": aq_rows,
        "columns": list(df_aq.columns),
        "source": aq_source,
    }

    # ── Weather ────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("COLLECTING WEATHER DATA")
    logger.info("=" * 60)
    try:
        if mode == "live":
            df_wx = collect_weather(cities_config, settings)
            if df_wx.empty:
                logger.warning(
                    "Live weather collection returned no data – "
                    "falling back to synthetic."
                )
                df_wx = generate_synthetic_weather(cities_config, settings)
                wx_source = "synthetic_fallback"
            else:
                wx_source = "live_api"
        else:
            df_wx = generate_synthetic_weather(cities_config, settings)
            wx_source = "synthetic_demo"
    except Exception:
        logger.exception("Weather collection failed – using synthetic.")
        df_wx = generate_synthetic_weather(cities_config, settings)
        wx_source = "synthetic_fallback_after_error"

    wx_path = os.path.join(raw_dir, "weather_raw.csv")
    wx_rows = _save_dataframe(df_wx, wx_path, "weather")
    dataframes["weather"] = df_wx
    metadata["datasets"]["weather"] = {
        "file": "weather_raw.csv",
        "rows": wx_rows,
        "columns": list(df_wx.columns),
        "source": wx_source,
    }

    # ── Demographics ──────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("COLLECTING DEMOGRAPHICS DATA")
    logger.info("=" * 60)
    try:
        if mode == "live":
            df_demo = collect_demographics(cities_config, settings)
            if df_demo.empty:
                logger.warning(
                    "Live demographics collection returned no data – "
                    "falling back to synthetic."
                )
                df_demo = generate_synthetic_demographics(cities_config, settings)
                demo_source = "synthetic_fallback"
            else:
                demo_source = "live_api"
        else:
            df_demo = generate_synthetic_demographics(cities_config, settings)
            demo_source = "synthetic_demo"
    except Exception:
        logger.exception("Demographics collection failed – using synthetic.")
        df_demo = generate_synthetic_demographics(cities_config, settings)
        demo_source = "synthetic_fallback_after_error"

    demo_path = os.path.join(raw_dir, "demographics_raw.csv")
    demo_rows = _save_dataframe(df_demo, demo_path, "demographics")
    dataframes["demographics"] = df_demo
    metadata["datasets"]["demographics"] = {
        "file": "demographics_raw.csv",
        "rows": demo_rows,
        "columns": list(df_demo.columns),
        "source": demo_source,
    }

    # ── Metadata ──────────────────────────────────────────────────────────
    meta_path = os.path.join(raw_dir, "collection_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, default=str)
    logger.info("Saved collection metadata → %s", meta_path)

    # Summary ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("DATA COLLECTION SUMMARY")
    logger.info("=" * 60)
    for name, info in metadata["datasets"].items():
        logger.info(
            "  %-15s  %6d rows  [%s]", name, info["rows"], info["source"],
        )
    logger.info("=" * 60)

    return dataframes
