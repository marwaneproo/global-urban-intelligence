"""
Data integration functions for the Global Urban Intelligence project.

Merges air-quality, weather, and demographic datasets into a single
analytical dataset, with detailed join diagnostics and reporting.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Reproducibility
np.random.seed(42)


# ---------------------------------------------------------------------------
# Core integration functions
# ---------------------------------------------------------------------------

def integrate_air_quality_weather(
    aq_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    on_city: str = "city",
    on_date: str = "date",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Integrate air-quality and weather DataFrames via a left join.

    The join is performed on ``(on_city, on_date)``. A LEFT join preserves all
    air-quality rows and attaches matching weather observations.

    Args:
        aq_df: Cleaned/transformed air-quality DataFrame (left side).
        weather_df: Cleaned/transformed weather DataFrame (right side).
        on_city: Column name for the city key.
        on_date: Column name for the date key.

    Returns:
        Tuple of (merged DataFrame, integration report dictionary).

    Raises:
        ValueError: If either DataFrame is empty.
    """
    report: Dict[str, Any] = {
        "step": "air_quality_weather_integration",
        "join_type": "left",
        "join_keys": [on_city, on_date],
    }

    if aq_df.empty:
        logger.warning("Air-quality DataFrame is empty — returning empty result.")
        report["status"] = "skipped_empty_aq"
        return pd.DataFrame(), report

    if weather_df.empty:
        logger.warning("Weather DataFrame is empty — returning air-quality data only.")
        report["status"] = "weather_empty"
        report["aq_rows"] = len(aq_df)
        report["weather_rows"] = 0
        report["merged_rows"] = len(aq_df)
        return aq_df.copy(), report

    # Validate join keys exist
    for key, label in [(on_city, "city"), (on_date, "date")]:
        if key not in aq_df.columns:
            logger.error("Join key '%s' missing from air-quality DataFrame.", key)
            report["error"] = f"Missing key '{key}' in aq_df"
            return aq_df.copy(), report
        if key not in weather_df.columns:
            logger.error("Join key '%s' missing from weather DataFrame.", key)
            report["error"] = f"Missing key '{key}' in weather_df"
            return aq_df.copy(), report

    # Ensure date columns are the same dtype for join
    aq_join = aq_df.copy()
    weather_join = weather_df.copy()
    aq_join[on_date] = pd.to_datetime(aq_join[on_date], errors="coerce")
    weather_join[on_date] = pd.to_datetime(weather_join[on_date], errors="coerce")

    # Normalise city for case-insensitive matching
    aq_join[on_city] = aq_join[on_city].astype(str).str.strip()
    weather_join[on_city] = weather_join[on_city].astype(str).str.strip()

    # Identify overlapping non-key columns to apply suffixes
    aq_other = set(aq_join.columns) - {on_city, on_date}
    weather_other = set(weather_join.columns) - {on_city, on_date}
    overlap = aq_other & weather_other
    if overlap:
        logger.info(
            "Overlapping columns will get suffixes: %s", sorted(overlap)
        )

    # Perform left join
    merged = pd.merge(
        aq_join,
        weather_join,
        on=[on_city, on_date],
        how="left",
        suffixes=("", "_weather"),
    )

    # Cardinality diagnostics
    aq_keys = set(zip(aq_join[on_city], aq_join[on_date]))
    weather_keys = set(zip(weather_join[on_city], weather_join[on_date]))
    matched = aq_keys & weather_keys
    unmatched_aq = aq_keys - weather_keys

    report.update({
        "status": "success",
        "aq_rows": len(aq_df),
        "weather_rows": len(weather_df),
        "merged_rows": len(merged),
        "aq_unique_keys": len(aq_keys),
        "weather_unique_keys": len(weather_keys),
        "matched_keys": len(matched),
        "unmatched_aq_keys": len(unmatched_aq),
        "match_rate_pct": round(
            len(matched) / len(aq_keys) * 100 if aq_keys else 0, 2
        ),
    })

    logger.info(
        "Integrated AQ + Weather: %d merged rows | match rate: %.1f%% "
        "(%d/%d AQ keys matched).",
        len(merged),
        report["match_rate_pct"],
        len(matched),
        len(aq_keys),
    )

    return merged, report


def add_demographics_context(
    integrated_df: pd.DataFrame,
    demo_df: pd.DataFrame,
    city_country_map: Dict[str, str],
) -> pd.DataFrame:
    """Add COUNTRY-level demographics to an integrated dataset.

    Because demographic indicators are at the country level, a
    ``demographic_level`` column is set to ``'country'`` to make this explicit.

    The *city_country_map* maps city names to country codes, enabling the join
    between the city-level integrated data and country-level demographics.

    Args:
        integrated_df: Merged air-quality + weather DataFrame.
        demo_df: Demographics DataFrame with a ``country_code`` column.
        city_country_map: ``{city_name: country_code}`` mapping.

    Returns:
        DataFrame with demographics columns appended.
    """
    if integrated_df.empty:
        logger.warning("Integrated DataFrame is empty — skipping demographics.")
        return integrated_df.copy()

    if demo_df.empty:
        logger.warning("Demographics DataFrame is empty — returning integrated data as-is.")
        result = integrated_df.copy()
        result["demographic_level"] = "country"
        return result

    df = integrated_df.copy()

    # Add country_code based on city → country mapping
    city_col = "city"
    if city_col not in df.columns:
        logger.warning("Column 'city' not found — cannot map to country codes.")
        df["demographic_level"] = "country"
        return df

    df["country_code"] = df[city_col].map(city_country_map)
    unmapped = df["country_code"].isna().sum()
    if unmapped > 0:
        logger.warning(
            "%d rows could not be mapped to a country_code (unmapped cities: %s).",
            unmapped,
            df.loc[df["country_code"].isna(), city_col].unique().tolist(),
        )

    # Prepare demographics for merge
    demo = demo_df.copy()
    if "country_code" not in demo.columns:
        logger.warning("Demographics missing 'country_code' — cannot merge.")
        df["demographic_level"] = "country"
        return df

    demo["country_code"] = demo["country_code"].astype(str).str.upper().str.strip()

    # If demographics have a year column, pick the latest year per country
    if "year" in demo.columns:
        demo["year"] = pd.to_numeric(demo["year"], errors="coerce")
        latest_idx = demo.groupby("country_code")["year"].idxmax()
        demo = demo.loc[latest_idx].reset_index(drop=True)
        logger.info("Using latest-year demographics per country for merge.")

    # Drop columns from demo that would clash (except join key)
    demo_merge_cols = [c for c in demo.columns if c not in df.columns or c == "country_code"]
    demo_for_merge = demo[demo_merge_cols].drop_duplicates(subset=["country_code"])

    # Left join
    before_cols = len(df.columns)
    df = pd.merge(df, demo_for_merge, on="country_code", how="left", suffixes=("", "_demo"))
    after_cols = len(df.columns)

    df["demographic_level"] = "country"

    logger.info(
        "Added %d demographic column(s) at country level.",
        after_cols - before_cols,
    )

    return df


# ---------------------------------------------------------------------------
# Master analytical dataset builder
# ---------------------------------------------------------------------------

def create_analytical_dataset(
    aq_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    demo_df: pd.DataFrame,
    cities_config: Dict[str, Any],
) -> pd.DataFrame:
    """Create the final analytical dataset by integrating all data sources.

    Steps:
        1. Integrate air-quality and weather data.
        2. Add demographics context at the country level.
        3. Validate the merged result.
        4. Save to ``data/processed/urban_analytics.csv``.

    Args:
        aq_df: Cleaned/transformed air-quality DataFrame.
        weather_df: Cleaned/transformed weather DataFrame.
        demo_df: Cleaned/transformed demographics DataFrame.
        cities_config: Cities configuration dict (from ``config/cities.json``).
            Must include a ``cities`` list with ``name`` and ``country_code``
            fields.

    Returns:
        Final merged analytical DataFrame.
    """
    logger.info("=== Creating analytical dataset ===")

    # 1. AQ + Weather integration
    merged, aq_weather_report = integrate_air_quality_weather(aq_df, weather_df)

    # 2. Build city → country_code map from config
    city_country_map: Dict[str, str] = {}
    for city in cities_config.get("cities", []):
        city_country_map[city["name"]] = city.get("country_code", "")
    logger.info("City-country map: %s", city_country_map)

    # 3. Add demographics
    final = add_demographics_context(merged, demo_df, city_country_map)

    # 4. Basic validation
    logger.info(
        "Analytical dataset shape: %d rows × %d columns.", len(final), len(final.columns)
    )
    if final.empty:
        logger.warning("Analytical dataset is EMPTY — check upstream data.")
    else:
        missing_summary = final.isnull().sum()
        cols_with_missing = missing_summary[missing_summary > 0]
        if len(cols_with_missing) > 0:
            logger.info(
                "Columns with missing values:\n%s",
                cols_with_missing.to_string(),
            )

    # 5. Save to disk
    output_path = Path("data/processed/urban_analytics.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(output_path, index=False)
    logger.info("Analytical dataset saved to %s", output_path)

    # 6. Also save integration report alongside
    report_path = Path("outputs/reports/integration_report.csv")
    generate_integration_report(aq_weather_report, report_path)

    return final


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_integration_report(
    report_dict: Dict[str, Any],
    output_path: Union[str, Path],
) -> Path:
    """Save an integration report as a CSV file.

    Args:
        report_dict: Dictionary of integration diagnostics (output of
            :func:`integrate_air_quality_weather`).
        output_path: File path for the CSV report.

    Returns:
        Resolved ``Path`` of the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [{"metric": k, "value": v} for k, v in report_dict.items()]
    report_df = pd.DataFrame(rows)
    report_df.to_csv(output_path, index=False)
    logger.info("Integration report saved to %s", output_path)

    return output_path
