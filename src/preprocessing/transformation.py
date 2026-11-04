"""
Data transformation functions for the Global Urban Intelligence project.

Provides temporal feature engineering, aggregation, rolling statistics, AQI
categorisation, and domain-specific transformation pipelines.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Reproducibility
np.random.seed(42)


# ---------------------------------------------------------------------------
# Temporal feature engineering
# ---------------------------------------------------------------------------

def add_date_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add calendar-based features derived from a datetime column.

    Adds: ``year``, ``month``, ``quarter``, ``day``, ``day_of_week``,
    ``day_name``, ``is_weekend``.

    Args:
        df: Input DataFrame.
        date_col: Name of the datetime column.

    Returns:
        DataFrame with added date-feature columns (copy).
    """
    df = df.copy()

    if date_col not in df.columns:
        logger.warning("Date column '%s' not found — skipping date features.", date_col)
        return df

    dt = pd.to_datetime(df[date_col], errors="coerce")

    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["quarter"] = dt.dt.quarter
    df["day"] = dt.dt.day
    df["day_of_week"] = dt.dt.dayofweek  # Monday=0 … Sunday=6
    df["day_name"] = dt.dt.day_name()
    df["is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)

    logger.info("Added 7 date-feature columns from '%s'.", date_col)
    return df


def add_season(
    df: pd.DataFrame,
    date_col: str = "date",
    hemisphere: str = "north",
) -> pd.DataFrame:
    """Add a ``season`` column based on month and hemisphere.

    Northern hemisphere mapping:
        - Winter: Dec, Jan, Feb
        - Spring: Mar, Apr, May
        - Summer: Jun, Jul, Aug
        - Autumn: Sep, Oct, Nov

    Southern hemisphere reverses Summer ↔ Winter and Spring ↔ Autumn.

    Args:
        df: Input DataFrame.
        date_col: Name of the datetime column.
        hemisphere: ``'north'`` or ``'south'``.

    Returns:
        DataFrame with an added ``season`` column (copy).
    """
    df = df.copy()

    if date_col not in df.columns:
        logger.warning("Date column '%s' not found — skipping season.", date_col)
        return df

    dt = pd.to_datetime(df[date_col], errors="coerce")
    month = dt.dt.month

    if hemisphere.lower().startswith("n"):
        season_map = {
            12: "Winter", 1: "Winter", 2: "Winter",
            3: "Spring", 4: "Spring", 5: "Spring",
            6: "Summer", 7: "Summer", 8: "Summer",
            9: "Autumn", 10: "Autumn", 11: "Autumn",
        }
    else:
        season_map = {
            12: "Summer", 1: "Summer", 2: "Summer",
            3: "Autumn", 4: "Autumn", 5: "Autumn",
            6: "Winter", 7: "Winter", 8: "Winter",
            9: "Spring", 10: "Spring", 11: "Spring",
        }

    df["season"] = month.map(season_map)
    logger.info("Added 'season' column (hemisphere=%s).", hemisphere)
    return df


# ---------------------------------------------------------------------------
# Aggregation functions
# ---------------------------------------------------------------------------

def compute_monthly_aggregates(
    df: pd.DataFrame,
    group_cols: List[str],
    value_cols: List[str],
    date_col: str = "date",
) -> pd.DataFrame:
    """Compute monthly aggregates (mean, median, min, max, count) per group.

    A ``year_month`` column is derived from *date_col* and used together with
    *group_cols* for grouping.

    Args:
        df: Input DataFrame.
        group_cols: Columns to group by (e.g., ``['city']``).
        value_cols: Numeric columns to aggregate.
        date_col: Datetime column used to extract year-month.

    Returns:
        Aggregated DataFrame with one row per group × month.
    """
    df = df.copy()

    if date_col not in df.columns:
        logger.warning("Date column '%s' not found — returning empty DataFrame.", date_col)
        return pd.DataFrame()

    dt = pd.to_datetime(df[date_col], errors="coerce")
    df["year_month"] = dt.dt.to_period("M").astype(str)

    existing_values = [c for c in value_cols if c in df.columns]
    if not existing_values:
        logger.warning("No value columns found — returning empty DataFrame.")
        return pd.DataFrame()

    existing_groups = [c for c in group_cols if c in df.columns]
    all_group = existing_groups + ["year_month"]

    agg_dict = {
        col: ["mean", "median", "min", "max", "count"] for col in existing_values
    }
    result = df.groupby(all_group, as_index=False).agg(agg_dict)

    # Flatten multi-level columns
    result.columns = [
        f"{a}_{b}" if b else a for a, b in result.columns
    ]

    logger.info(
        "Computed monthly aggregates: %d rows, grouped by %s.",
        len(result),
        all_group,
    )
    return result


def compute_daily_aggregates(
    df: pd.DataFrame,
    group_cols: List[str],
    value_cols: List[str],
    date_col: str = "date",
) -> pd.DataFrame:
    """Compute daily aggregates when multiple measurements exist per day.

    Produces mean, median, min, max, and count per day × group.

    Args:
        df: Input DataFrame.
        group_cols: Columns to group by (e.g., ``['city']``).
        value_cols: Numeric columns to aggregate.
        date_col: Datetime column used to extract the date part.

    Returns:
        Aggregated DataFrame with one row per group × day.
    """
    df = df.copy()

    if date_col not in df.columns:
        logger.warning("Date column '%s' not found — returning empty DataFrame.", date_col)
        return pd.DataFrame()

    dt = pd.to_datetime(df[date_col], errors="coerce")
    df["date_day"] = dt.dt.date

    existing_values = [c for c in value_cols if c in df.columns]
    if not existing_values:
        logger.warning("No value columns found — returning empty DataFrame.")
        return pd.DataFrame()

    existing_groups = [c for c in group_cols if c in df.columns]
    all_group = existing_groups + ["date_day"]

    agg_dict = {
        col: ["mean", "median", "min", "max", "count"] for col in existing_values
    }
    result = df.groupby(all_group, as_index=False).agg(agg_dict)

    # Flatten multi-level columns
    result.columns = [
        f"{a}_{b}" if b else a for a, b in result.columns
    ]

    logger.info(
        "Computed daily aggregates: %d rows, grouped by %s.",
        len(result),
        all_group,
    )
    return result


def compute_city_summaries(
    df: pd.DataFrame,
    city_col: str = "city",
    value_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute per-city summary statistics for specified value columns.

    Produces: mean, median, std, min, max, count, q25, q75 per city.

    Args:
        df: Input DataFrame.
        city_col: Column identifying the city.
        value_cols: Numeric columns to summarise. If ``None``, all numeric
            columns are used.

    Returns:
        Summary DataFrame with one row per city.
    """
    if city_col not in df.columns:
        logger.warning("City column '%s' not found — returning empty DataFrame.", city_col)
        return pd.DataFrame()

    if value_cols is None:
        value_cols = list(df.select_dtypes(include=[np.number]).columns)

    existing_values = [c for c in value_cols if c in df.columns]
    if not existing_values:
        logger.warning("No numeric value columns available for city summaries.")
        return pd.DataFrame()

    def _summary(group: pd.DataFrame) -> pd.Series:
        stats: Dict[str, Any] = {}
        for col in existing_values:
            s = group[col].dropna()
            stats[f"{col}_mean"] = s.mean() if len(s) > 0 else np.nan
            stats[f"{col}_median"] = s.median() if len(s) > 0 else np.nan
            stats[f"{col}_std"] = s.std() if len(s) > 0 else np.nan
            stats[f"{col}_min"] = s.min() if len(s) > 0 else np.nan
            stats[f"{col}_max"] = s.max() if len(s) > 0 else np.nan
            stats[f"{col}_count"] = len(s)
            stats[f"{col}_q25"] = s.quantile(0.25) if len(s) > 0 else np.nan
            stats[f"{col}_q75"] = s.quantile(0.75) if len(s) > 0 else np.nan
        return pd.Series(stats)

    result = df.groupby(city_col).apply(_summary, include_groups=False).reset_index()
    logger.info("Computed city summaries for %d cities.", result[city_col].nunique())
    return result


def compute_rolling_averages(
    df: pd.DataFrame,
    value_col: str,
    windows: List[int],
    date_col: str = "date",
    group_col: Optional[str] = None,
) -> pd.DataFrame:
    """Compute rolling mean(s) for a value column over specified window sizes.

    The DataFrame is sorted by ``(group_col, date_col)`` before rolling.

    Args:
        df: Input DataFrame.
        value_col: Numeric column to compute rolling averages on.
        windows: List of window sizes in number of rows (e.g., ``[7, 30]``).
        date_col: Datetime column used for sorting.
        group_col: Optional grouping column (e.g., ``'city'``).

    Returns:
        DataFrame with added ``<value_col>_rolling_<w>`` columns (copy).
    """
    df = df.copy()

    if value_col not in df.columns:
        logger.warning(
            "Value column '%s' not found — skipping rolling averages.", value_col
        )
        return df

    sort_cols = []
    if group_col and group_col in df.columns:
        sort_cols.append(group_col)
    if date_col in df.columns:
        sort_cols.append(date_col)
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)

    for w in windows:
        new_col = f"{value_col}_rolling_{w}"
        if group_col and group_col in df.columns:
            df[new_col] = (
                df.groupby(group_col)[value_col]
                .transform(lambda s: s.rolling(window=w, min_periods=1).mean())
            )
        else:
            df[new_col] = (
                df[value_col].rolling(window=w, min_periods=1).mean()
            )
        logger.info("Added rolling average column '%s' (window=%d).", new_col, w)

    return df


# ---------------------------------------------------------------------------
# AQI categorisation
# ---------------------------------------------------------------------------

def create_air_quality_index_category(pm25_value: Optional[float]) -> str:
    """Return the AQI category string for a PM2.5 concentration value.

    Categories follow the US EPA breakpoints:
        - **Good**: 0.0–12.0 µg/m³
        - **Moderate**: 12.1–35.4 µg/m³
        - **Unhealthy for Sensitive Groups**: 35.5–55.4 µg/m³
        - **Unhealthy**: 55.5–150.4 µg/m³
        - **Very Unhealthy**: 150.5–250.4 µg/m³
        - **Hazardous**: ≥ 250.5 µg/m³

    Args:
        pm25_value: PM2.5 concentration in µg/m³.

    Returns:
        AQI category as a string. Returns ``'Unknown'`` for ``NaN`` or
        negative values.
    """
    if pm25_value is None or (isinstance(pm25_value, float) and np.isnan(pm25_value)):
        return "Unknown"

    try:
        val = float(pm25_value)
    except (TypeError, ValueError):
        return "Unknown"

    if val < 0:
        return "Unknown"
    elif val <= 12.0:
        return "Good"
    elif val <= 35.4:
        return "Moderate"
    elif val <= 55.4:
        return "Unhealthy for Sensitive Groups"
    elif val <= 150.4:
        return "Unhealthy"
    elif val <= 250.4:
        return "Very Unhealthy"
    else:
        return "Hazardous"


# ---------------------------------------------------------------------------
# Domain-specific transformation pipelines
# ---------------------------------------------------------------------------

def transform_air_quality(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Master transformation pipeline for air-quality data.

    Steps:
        1. Add date features (year, month, quarter, etc.).
        2. Add season.
        3. Add AQI category column.
        4. Compute rolling averages (7-day, 30-day) per city.

    Args:
        df: Cleaned air-quality DataFrame.
        config: Optional overrides. Keys: ``date_col``, ``pm25_col``,
            ``city_col``, ``rolling_windows``, ``hemisphere``.

    Returns:
        Transformed air-quality DataFrame.
    """
    config = config or {}
    date_col = config.get("date_col", "date")
    pm25_col = config.get("pm25_col", "pm25")
    city_col = config.get("city_col", "city")
    hemisphere = config.get("hemisphere", "north")
    rolling_windows = config.get("rolling_windows", [7, 30])

    logger.info("=== Transforming air_quality dataset (%d rows) ===", len(df))

    # Date features
    df = add_date_features(df, date_col)
    df = add_season(df, date_col, hemisphere=hemisphere)

    # AQI category
    if pm25_col in df.columns:
        df["aqi_category"] = df[pm25_col].apply(create_air_quality_index_category)
        logger.info("Added 'aqi_category' column from '%s'.", pm25_col)
    else:
        # Fallback: try 'value' column if parameter indicates PM2.5
        if "value" in df.columns:
            df["aqi_category"] = df["value"].apply(create_air_quality_index_category)
            logger.info("Added 'aqi_category' column from 'value' (fallback).")

    # Rolling averages
    rolling_col = pm25_col if pm25_col in df.columns else "value"
    if rolling_col in df.columns:
        group = city_col if city_col in df.columns else None
        df = compute_rolling_averages(df, rolling_col, rolling_windows, date_col, group)

    logger.info(
        "=== air_quality transformation complete (%d rows, %d cols) ===",
        len(df),
        len(df.columns),
    )
    return df


def transform_weather(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Master transformation pipeline for weather data.

    Steps:
        1. Add date features.
        2. Add season.
        3. Compute temperature rolling averages.

    Args:
        df: Cleaned weather DataFrame.
        config: Optional overrides. Keys: ``date_col``, ``city_col``,
            ``hemisphere``, ``rolling_windows``, ``temp_col``.

    Returns:
        Transformed weather DataFrame.
    """
    config = config or {}
    date_col = config.get("date_col", "date")
    city_col = config.get("city_col", "city")
    hemisphere = config.get("hemisphere", "north")
    rolling_windows = config.get("rolling_windows", [7, 30])
    temp_col = config.get("temp_col", "temperature_2m_mean")

    logger.info("=== Transforming weather dataset (%d rows) ===", len(df))

    df = add_date_features(df, date_col)
    df = add_season(df, date_col, hemisphere=hemisphere)

    # Rolling averages on temperature
    if temp_col in df.columns:
        group = city_col if city_col in df.columns else None
        df = compute_rolling_averages(df, temp_col, rolling_windows, date_col, group)

    logger.info(
        "=== weather transformation complete (%d rows, %d cols) ===",
        len(df),
        len(df.columns),
    )
    return df


def transform_demographics(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Master transformation pipeline for demographics data.

    Demographics are typically annual and country-level. This function
    ensures consistent column naming and derives any additional features.

    Steps:
        1. Ensure ``country_code`` is uppercase.
        2. Sort by country + year for easy inspection.

    Args:
        df: Cleaned demographics DataFrame.
        config: Optional overrides. Keys: ``country_col``, ``year_col``.

    Returns:
        Transformed demographics DataFrame.
    """
    config = config or {}
    country_col = config.get("country_col", "country_code")
    year_col = config.get("year_col", "year")

    logger.info("=== Transforming demographics dataset (%d rows) ===", len(df))

    df = df.copy()

    # Uppercase country codes
    if country_col in df.columns:
        df[country_col] = df[country_col].astype(str).str.upper().str.strip()
        logger.info("Uppercased '%s' column.", country_col)

    # Sort for readability
    sort_cols = [c for c in [country_col, year_col] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)
        logger.info("Sorted demographics by %s.", sort_cols)

    logger.info(
        "=== demographics transformation complete (%d rows, %d cols) ===",
        len(df),
        len(df.columns),
    )
    return df
