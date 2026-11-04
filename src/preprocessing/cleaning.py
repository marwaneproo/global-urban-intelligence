"""
Data cleaning functions for the Global Urban Intelligence project.

Provides column standardisation, deduplication, type coercion, missing-value
handling, and domain-specific cleaning pipelines for air-quality, weather,
and demographic datasets.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Reproducibility
np.random.seed(42)


# ---------------------------------------------------------------------------
# Generic cleaning utilities
# ---------------------------------------------------------------------------

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip whitespace, and replace spaces with underscores in column names.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with standardised column names (copy).
    """
    df = df.copy()
    original_cols = list(df.columns)
    df.columns = [
        str(c).strip().lower().replace(" ", "_") for c in df.columns
    ]
    renamed = {o: n for o, n in zip(original_cols, df.columns) if o != n}
    if renamed:
        logger.info(
            "Standardised %d column name(s): %s",
            len(renamed),
            renamed,
        )
    else:
        logger.debug("All column names already standardised.")
    return df


def remove_exact_duplicates(
    df: pd.DataFrame,
    dataset_name: str = "dataset",
) -> pd.DataFrame:
    """Remove exact duplicate rows from the DataFrame.

    Args:
        df: Input DataFrame.
        dataset_name: Human-readable name for log messages.

    Returns:
        DataFrame with duplicates removed (copy).
    """
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    if removed > 0:
        logger.info(
            "[%s] Removed %d exact duplicate row(s) (%d → %d).",
            dataset_name,
            removed,
            before,
            len(df),
        )
    else:
        logger.debug("[%s] No exact duplicates found.", dataset_name)
    return df


def parse_dates(
    df: pd.DataFrame,
    date_cols: List[str],
    formats: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Parse specified columns as datetime, coercing errors to NaT.

    Args:
        df: Input DataFrame.
        date_cols: Column names to parse.
        formats: Optional mapping ``{col: strftime_format}``.  When a format is
            provided it is tried first; on failure the column falls back to
            pandas' general parser.

    Returns:
        DataFrame with parsed date columns (copy).
    """
    df = df.copy()
    formats = formats or {}

    for col in date_cols:
        if col not in df.columns:
            logger.warning("Date column '%s' not found — skipping.", col)
            continue

        before_nat = int(df[col].isna().sum())

        if col in formats:
            try:
                df[col] = pd.to_datetime(df[col], format=formats[col], errors="coerce")
            except Exception:
                logger.warning(
                    "Format '%s' failed for column '%s'; falling back to infer.",
                    formats[col],
                    col,
                )
                df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        after_nat = int(df[col].isna().sum())
        new_nats = after_nat - before_nat
        if new_nats > 0:
            logger.warning(
                "Column '%s': %d value(s) could not be parsed and became NaT.",
                col,
                new_nats,
            )
        else:
            logger.info("Column '%s' parsed as datetime successfully.", col)

    return df


def convert_numeric(
    df: pd.DataFrame,
    numeric_cols: List[str],
) -> pd.DataFrame:
    """Convert columns to numeric dtype, coercing errors to NaN.

    Args:
        df: Input DataFrame.
        numeric_cols: Columns to convert.

    Returns:
        DataFrame with converted columns (copy).
    """
    df = df.copy()

    for col in numeric_cols:
        if col not in df.columns:
            logger.warning("Numeric column '%s' not found — skipping.", col)
            continue

        before_nan = int(df[col].isna().sum())
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after_nan = int(df[col].isna().sum())
        new_nans = after_nan - before_nan

        if new_nans > 0:
            logger.warning(
                "Column '%s': %d value(s) coerced to NaN during numeric conversion.",
                col,
                new_nans,
            )
        else:
            logger.info("Column '%s' converted to numeric successfully.", col)

    return df


def validate_units(
    df: pd.DataFrame,
    unit_col: str,
    expected_units: List[str],
) -> pd.DataFrame:
    """Check for unexpected unit values and log them.

    This function does **not** modify the DataFrame; it only reports.

    Args:
        df: Input DataFrame.
        unit_col: Column containing unit strings.
        expected_units: List of acceptable unit values.

    Returns:
        The original DataFrame (unchanged).
    """
    if unit_col not in df.columns:
        logger.warning("Unit column '%s' not found — skipping unit validation.", unit_col)
        return df

    # Normalise comparison to lowercase
    expected_lower: Set[str] = {u.lower().strip() for u in expected_units}
    actual_units = df[unit_col].dropna().astype(str).str.lower().str.strip().unique()
    unexpected = [u for u in actual_units if u not in expected_lower]

    if unexpected:
        logger.warning(
            "Unexpected units found in '%s': %s (expected: %s).",
            unit_col,
            unexpected,
            list(expected_lower),
        )
    else:
        logger.info(
            "Unit validation on '%s' passed — all values in expected set.",
            unit_col,
        )

    return df


def handle_missing_values(
    df: pd.DataFrame,
    strategy_map: Dict[str, str],
) -> pd.DataFrame:
    """Handle missing values per column according to the specified strategy.

    Supported strategies:
        - ``'drop'`` — drop rows where this column is NaN.
        - ``'mean'`` — fill NaN with column mean.
        - ``'median'`` — fill NaN with column median.
        - ``'ffill'`` — forward-fill NaN values.
        - ``'flag_only'`` (default) — add a boolean ``<col>_is_missing`` flag
          without altering the original column.

    **Never** replaces missing values with 0 blindly.

    Args:
        df: Input DataFrame.
        strategy_map: ``{column_name: strategy_string}``.

    Returns:
        DataFrame with missing values handled (copy).
    """
    df = df.copy()

    for col, strategy in strategy_map.items():
        if col not in df.columns:
            logger.warning(
                "Column '%s' not found — skipping missing-value handling.", col
            )
            continue

        missing_count = int(df[col].isna().sum())
        if missing_count == 0:
            logger.debug("Column '%s': no missing values — nothing to do.", col)
            continue

        strategy = strategy.lower().strip()

        if strategy == "drop":
            before = len(df)
            df = df.dropna(subset=[col]).reset_index(drop=True)
            logger.info(
                "Column '%s': dropped %d row(s) with missing values.",
                col,
                before - len(df),
            )

        elif strategy == "mean":
            mean_val = df[col].mean()
            df[col] = df[col].fillna(mean_val)
            logger.info(
                "Column '%s': filled %d missing value(s) with mean (%.4f).",
                col,
                missing_count,
                mean_val,
            )

        elif strategy == "median":
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info(
                "Column '%s': filled %d missing value(s) with median (%.4f).",
                col,
                missing_count,
                median_val,
            )

        elif strategy == "ffill":
            df[col] = df[col].ffill()
            remaining = int(df[col].isna().sum())
            logger.info(
                "Column '%s': forward-filled %d missing value(s) (%d still missing).",
                col,
                missing_count - remaining,
                remaining,
            )

        elif strategy == "flag_only":
            flag_col = f"{col}_is_missing"
            df[flag_col] = df[col].isna().astype(int)
            logger.info(
                "Column '%s': flagged %d missing value(s) in '%s' (no imputation).",
                col,
                missing_count,
                flag_col,
            )

        else:
            logger.warning(
                "Column '%s': unknown strategy '%s' — defaulting to flag_only.",
                col,
                strategy,
            )
            flag_col = f"{col}_is_missing"
            df[flag_col] = df[col].isna().astype(int)

    return df


def flag_suspicious_values(
    df: pd.DataFrame,
    rules: Dict[str, Tuple[Optional[float], Optional[float]]],
) -> pd.DataFrame:
    """Flag values outside expected ranges as suspicious.

    Adds a boolean ``<col>_suspicious`` column for each rule. A value is
    suspicious when it is outside the ``(min, max)`` range (exclusive at the
    boundaries defined in *rules*). ``None`` can be used to indicate no bound.

    Args:
        df: Input DataFrame.
        rules: ``{column_name: (min_val, max_val)}``.

    Returns:
        DataFrame with added ``_suspicious`` flag columns (copy).
    """
    df = df.copy()

    for col, (lo, hi) in rules.items():
        if col not in df.columns:
            logger.warning(
                "Column '%s' not found — skipping suspicious-value flagging.", col
            )
            continue

        numeric = pd.to_numeric(df[col], errors="coerce")
        suspicious = pd.Series(False, index=df.index)

        if lo is not None:
            suspicious = suspicious | (numeric < lo)
        if hi is not None:
            suspicious = suspicious | (numeric > hi)

        flag_col = f"{col}_suspicious"
        df[flag_col] = suspicious.astype(int)
        flagged_count = int(suspicious.sum())

        if flagged_count > 0:
            logger.warning(
                "Column '%s': %d value(s) flagged as suspicious (outside [%s, %s]).",
                col,
                flagged_count,
                lo,
                hi,
            )
        else:
            logger.debug(
                "Column '%s': no suspicious values (all within [%s, %s]).",
                col,
                lo,
                hi,
            )

    return df


# ---------------------------------------------------------------------------
# Domain-specific cleaning pipelines
# ---------------------------------------------------------------------------

def clean_air_quality(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Apply all relevant cleaning steps to air-quality data.

    Steps:
        1. Standardise column names.
        2. Remove exact duplicates.
        3. Parse date columns.
        4. Convert numeric columns.
        5. Validate units (if a ``unit`` column exists).
        6. Handle missing values.
        7. Flag suspicious values.

    Args:
        df: Raw air-quality DataFrame.
        config: Optional overrides for cleaning parameters.

    Returns:
        Cleaned air-quality DataFrame.
    """
    config = config or {}
    dataset_name = "air_quality"
    logger.info("=== Cleaning %s dataset (%d rows) ===", dataset_name, len(df))

    df = standardize_columns(df)
    df = remove_exact_duplicates(df, dataset_name)

    # Date columns
    date_cols = config.get("date_cols", ["date"])
    df = parse_dates(df, date_cols)

    # Numeric columns
    numeric_cols = config.get(
        "numeric_cols",
        ["value", "pm25", "pm10", "latitude", "longitude"],
    )
    existing_numeric = [c for c in numeric_cols if c in df.columns]
    if existing_numeric:
        df = convert_numeric(df, existing_numeric)

    # Unit validation
    unit_col = config.get("unit_col", "unit")
    expected_units = config.get("expected_units", ["µg/m³", "ug/m3", "µg/m3"])
    if unit_col in df.columns:
        df = validate_units(df, unit_col, expected_units)

    # Missing value strategy
    default_strategy = {}
    for col in ["pm25", "pm10", "value"]:
        if col in df.columns:
            default_strategy[col] = "flag_only"
    strategy_map = config.get("missing_strategy", default_strategy)
    df = handle_missing_values(df, strategy_map)

    # Suspicious value flagging
    default_rules: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    if "pm25" in df.columns:
        default_rules["pm25"] = (0.0, 500.0)
    if "pm10" in df.columns:
        default_rules["pm10"] = (0.0, 600.0)
    if "value" in df.columns and "pm25" not in df.columns:
        default_rules["value"] = (0.0, 500.0)
    rules = config.get("suspicious_rules", default_rules)
    if rules:
        df = flag_suspicious_values(df, rules)

    logger.info(
        "=== %s cleaning complete (%d rows remaining) ===",
        dataset_name,
        len(df),
    )
    return df


def clean_weather(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Apply all relevant cleaning steps to weather data.

    Steps mirror :func:`clean_air_quality` with weather-specific defaults.

    Args:
        df: Raw weather DataFrame.
        config: Optional overrides for cleaning parameters.

    Returns:
        Cleaned weather DataFrame.
    """
    config = config or {}
    dataset_name = "weather"
    logger.info("=== Cleaning %s dataset (%d rows) ===", dataset_name, len(df))

    df = standardize_columns(df)
    df = remove_exact_duplicates(df, dataset_name)

    # Date columns
    date_cols = config.get("date_cols", ["date"])
    df = parse_dates(df, date_cols)

    # Numeric columns
    numeric_cols = config.get(
        "numeric_cols",
        [
            "temperature_2m_mean",
            "temperature_2m_min",
            "temperature_2m_max",
            "relative_humidity_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_mean",
            "wind_direction_10m_dominant",
        ],
    )
    existing_numeric = [c for c in numeric_cols if c in df.columns]
    if existing_numeric:
        df = convert_numeric(df, existing_numeric)

    # Missing value strategy
    default_strategy: Dict[str, str] = {}
    for col in existing_numeric:
        default_strategy[col] = "flag_only"
    strategy_map = config.get("missing_strategy", default_strategy)
    df = handle_missing_values(df, strategy_map)

    # Suspicious value flagging
    default_rules: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    temp_cols = [c for c in df.columns if "temperature" in c]
    for tc in temp_cols:
        default_rules[tc] = (-50.0, 60.0)
    if "relative_humidity_2m_mean" in df.columns:
        default_rules["relative_humidity_2m_mean"] = (0.0, 100.0)
    if "precipitation_sum" in df.columns:
        default_rules["precipitation_sum"] = (0.0, 500.0)
    if "wind_speed_10m_mean" in df.columns:
        default_rules["wind_speed_10m_mean"] = (0.0, 200.0)
    rules = config.get("suspicious_rules", default_rules)
    if rules:
        df = flag_suspicious_values(df, rules)

    logger.info(
        "=== %s cleaning complete (%d rows remaining) ===",
        dataset_name,
        len(df),
    )
    return df


def clean_demographics(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Apply all relevant cleaning steps to demographics data.

    Steps mirror :func:`clean_air_quality` with demographics-specific defaults.

    Args:
        df: Raw demographics DataFrame.
        config: Optional overrides for cleaning parameters.

    Returns:
        Cleaned demographics DataFrame.
    """
    config = config or {}
    dataset_name = "demographics"
    logger.info("=== Cleaning %s dataset (%d rows) ===", dataset_name, len(df))

    df = standardize_columns(df)
    df = remove_exact_duplicates(df, dataset_name)

    # Date / year column
    date_cols = config.get("date_cols", [])
    if date_cols:
        df = parse_dates(df, date_cols)

    # If there's a 'year' column, ensure it is integer-like
    if "year" in df.columns:
        df = convert_numeric(df, ["year"])

    # Numeric columns (indicators)
    numeric_cols = config.get(
        "numeric_cols",
        [
            "total_population",
            "population_growth",
            "urban_population_pct",
            "urban_population_growth",
            "value",
        ],
    )
    existing_numeric = [c for c in numeric_cols if c in df.columns]
    if existing_numeric:
        df = convert_numeric(df, existing_numeric)

    # Missing value strategy
    default_strategy: Dict[str, str] = {}
    for col in existing_numeric:
        default_strategy[col] = "flag_only"
    strategy_map = config.get("missing_strategy", default_strategy)
    df = handle_missing_values(df, strategy_map)

    # Suspicious values: population should be positive
    default_rules: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    if "total_population" in df.columns:
        default_rules["total_population"] = (0.0, 2e10)
    if "population_growth" in df.columns:
        default_rules["population_growth"] = (-10.0, 15.0)
    if "urban_population_pct" in df.columns:
        default_rules["urban_population_pct"] = (0.0, 100.0)
    rules = config.get("suspicious_rules", default_rules)
    if rules:
        df = flag_suspicious_values(df, rules)

    logger.info(
        "=== %s cleaning complete (%d rows remaining) ===",
        dataset_name,
        len(df),
    )
    return df


# ---------------------------------------------------------------------------
# Cleaning report
# ---------------------------------------------------------------------------

def generate_cleaning_report(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    dataset_name: str,
    output_path: Union[str, Path],
) -> Path:
    """Generate and save a cleaning summary comparing original and cleaned DataFrames.

    Args:
        original_df: DataFrame *before* cleaning.
        cleaned_df: DataFrame *after* cleaning.
        dataset_name: Human-readable dataset name.
        output_path: File path for the CSV report.

    Returns:
        Resolved ``Path`` of the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []

    # Row-level summary
    rows.append({
        "metric": "total_rows_original",
        "value": len(original_df),
    })
    rows.append({
        "metric": "total_rows_cleaned",
        "value": len(cleaned_df),
    })
    rows.append({
        "metric": "rows_removed",
        "value": len(original_df) - len(cleaned_df),
    })
    rows.append({
        "metric": "columns_original",
        "value": len(original_df.columns),
    })
    rows.append({
        "metric": "columns_cleaned",
        "value": len(cleaned_df.columns),
    })
    rows.append({
        "metric": "columns_added",
        "value": len(cleaned_df.columns) - len(original_df.columns),
    })

    # Per-column missing comparison (only for columns present in both)
    common_cols = [c for c in original_df.columns if c in cleaned_df.columns]
    for col in common_cols:
        orig_missing = int(original_df[col].isna().sum())
        clean_missing = int(cleaned_df[col].isna().sum()) if col in cleaned_df.columns else 0
        rows.append({
            "metric": f"missing_{col}_original",
            "value": orig_missing,
        })
        rows.append({
            "metric": f"missing_{col}_cleaned",
            "value": clean_missing,
        })

    # Flag / suspicious columns added
    flag_cols = [c for c in cleaned_df.columns if c.endswith("_is_missing") or c.endswith("_suspicious")]
    for fc in flag_cols:
        flagged_count = int(cleaned_df[fc].sum()) if fc in cleaned_df.columns else 0
        rows.append({
            "metric": f"flagged_{fc}",
            "value": flagged_count,
        })

    report_df = pd.DataFrame(rows)
    report_df.insert(0, "dataset", dataset_name)
    report_df.to_csv(output_path, index=False)
    logger.info("[%s] Cleaning report saved to %s", dataset_name, output_path)

    return output_path
