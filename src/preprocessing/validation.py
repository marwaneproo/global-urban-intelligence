"""
Data quality validation functions for the Global Urban Intelligence project.

Provides a suite of validation checks that report quality issues without raising
exceptions, enabling downstream decisions about data fitness. Only truly critical
structural failures (e.g., input is not a DataFrame) raise exceptions.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual validation functions
# ---------------------------------------------------------------------------

def validate_required_columns(
    df: pd.DataFrame,
    required_cols: List[str],
    dataset_name: str = "dataset",
) -> Dict[str, Any]:
    """Validate that all required columns are present in the DataFrame.

    Args:
        df: Input DataFrame to validate.
        required_cols: List of column names that must exist.
        dataset_name: Human-readable name for log messages.

    Returns:
        Dictionary with keys ``passed``, ``missing_columns``, ``present_columns``.

    Raises:
        TypeError: If *df* is not a ``pd.DataFrame``.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pd.DataFrame, got {type(df).__name__}")

    present = [c for c in required_cols if c in df.columns]
    missing = [c for c in required_cols if c not in df.columns]
    passed = len(missing) == 0

    if passed:
        logger.info(
            "[%s] Required-columns check PASSED — all %d columns present.",
            dataset_name,
            len(required_cols),
        )
    else:
        logger.warning(
            "[%s] Required-columns check FAILED — missing %d column(s): %s",
            dataset_name,
            len(missing),
            missing,
        )

    return {
        "check": "required_columns",
        "dataset": dataset_name,
        "passed": passed,
        "missing_columns": missing,
        "present_columns": present,
    }


def validate_date_range(
    df: pd.DataFrame,
    date_col: str,
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate that date values fall within an expected range.

    Non-parseable values are counted as invalid. ``min_date`` and ``max_date``
    are inclusive boundaries expressed as ISO-8601 strings.

    Args:
        df: Input DataFrame.
        date_col: Name of the date column.
        min_date: Earliest acceptable date (inclusive).
        max_date: Latest acceptable date (inclusive).

    Returns:
        Dictionary with ``passed``, ``invalid_count``, ``out_of_range_count``,
        ``date_min``, ``date_max``.
    """
    if date_col not in df.columns:
        logger.warning("Date column '%s' not found in DataFrame.", date_col)
        return {
            "check": "date_range",
            "column": date_col,
            "passed": False,
            "error": f"Column '{date_col}' not found",
            "invalid_count": len(df),
            "out_of_range_count": 0,
        }

    dates = pd.to_datetime(df[date_col], errors="coerce")
    invalid_count = int(dates.isna().sum() - df[date_col].isna().sum())
    # Count values that were already NaN separately; they are *missing*, not invalid.

    valid_dates = dates.dropna()
    out_of_range = 0
    if min_date is not None:
        out_of_range += int((valid_dates < pd.Timestamp(min_date)).sum())
    if max_date is not None:
        out_of_range += int((valid_dates > pd.Timestamp(max_date)).sum())

    passed = invalid_count == 0 and out_of_range == 0

    if passed:
        logger.info(
            "Date-range check on '%s' PASSED (range: %s to %s).",
            date_col,
            valid_dates.min() if len(valid_dates) > 0 else "N/A",
            valid_dates.max() if len(valid_dates) > 0 else "N/A",
        )
    else:
        logger.warning(
            "Date-range check on '%s' FAILED — %d invalid, %d out-of-range.",
            date_col,
            invalid_count,
            out_of_range,
        )

    return {
        "check": "date_range",
        "column": date_col,
        "passed": passed,
        "invalid_count": invalid_count,
        "out_of_range_count": out_of_range,
        "date_min": str(valid_dates.min()) if len(valid_dates) > 0 else None,
        "date_max": str(valid_dates.max()) if len(valid_dates) > 0 else None,
    }


def validate_coordinate_range(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> Dict[str, Any]:
    """Validate that latitude and longitude values are within valid ranges.

    Latitude must be in [-90, 90] and longitude in [-180, 180].

    Args:
        df: Input DataFrame.
        lat_col: Name of the latitude column.
        lon_col: Name of the longitude column.

    Returns:
        Dictionary with ``passed``, ``invalid_lat_count``, ``invalid_lon_count``.
    """
    result: Dict[str, Any] = {
        "check": "coordinate_range",
        "lat_col": lat_col,
        "lon_col": lon_col,
        "passed": True,
        "invalid_lat_count": 0,
        "invalid_lon_count": 0,
    }

    for col, label, lo, hi in [
        (lat_col, "invalid_lat_count", -90.0, 90.0),
        (lon_col, "invalid_lon_count", -180.0, 180.0),
    ]:
        if col not in df.columns:
            logger.warning("Coordinate column '%s' not found.", col)
            result[label] = len(df)
            result["passed"] = False
            continue

        numeric = pd.to_numeric(df[col], errors="coerce")
        out = int(((numeric < lo) | (numeric > hi)).sum())
        nan_introduced = int(numeric.isna().sum() - df[col].isna().sum())
        total_invalid = out + nan_introduced
        result[label] = total_invalid
        if total_invalid > 0:
            result["passed"] = False

    if result["passed"]:
        logger.info("Coordinate-range check PASSED.")
    else:
        logger.warning(
            "Coordinate-range check FAILED — %d invalid lat, %d invalid lon.",
            result["invalid_lat_count"],
            result["invalid_lon_count"],
        )

    return result


def validate_numeric_range(
    df: pd.DataFrame,
    col: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    col_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate that a numeric column falls within specified bounds.

    Args:
        df: Input DataFrame.
        col: Column name to validate.
        min_val: Minimum acceptable value (inclusive).
        max_val: Maximum acceptable value (inclusive).
        col_name: Human-readable label for logs (defaults to *col*).

    Returns:
        Dictionary with ``passed`` and ``out_of_range_count``.
    """
    label = col_name or col

    if col not in df.columns:
        logger.warning("Column '%s' not found for numeric-range check.", col)
        return {
            "check": "numeric_range",
            "column": label,
            "passed": False,
            "error": f"Column '{col}' not found",
            "out_of_range_count": len(df),
        }

    numeric = pd.to_numeric(df[col], errors="coerce")
    out_count = 0
    if min_val is not None:
        out_count += int((numeric < min_val).sum())
    if max_val is not None:
        out_count += int((numeric > max_val).sum())

    passed = out_count == 0

    if passed:
        logger.info("Numeric-range check on '%s' PASSED.", label)
    else:
        logger.warning(
            "Numeric-range check on '%s' FAILED — %d value(s) out of [%s, %s].",
            label,
            out_count,
            min_val,
            max_val,
        )

    return {
        "check": "numeric_range",
        "column": label,
        "passed": passed,
        "out_of_range_count": out_count,
        "min_val": min_val,
        "max_val": max_val,
    }


def validate_no_duplicates(
    df: pd.DataFrame,
    subset_cols: Optional[List[str]] = None,
    dataset_name: str = "dataset",
) -> Dict[str, Any]:
    """Validate that the DataFrame has no duplicate rows.

    Args:
        df: Input DataFrame.
        subset_cols: Columns to consider when identifying duplicates.
            If ``None``, all columns are used.
        dataset_name: Human-readable name for log messages.

    Returns:
        Dictionary with ``passed`` and ``duplicate_count``.
    """
    # Filter to only existing columns to avoid KeyError
    if subset_cols is not None:
        existing = [c for c in subset_cols if c in df.columns]
        if not existing:
            logger.warning(
                "[%s] None of the subset columns %s exist — skipping duplicate check.",
                dataset_name,
                subset_cols,
            )
            return {
                "check": "no_duplicates",
                "dataset": dataset_name,
                "passed": True,
                "duplicate_count": 0,
                "note": "No subset columns found; check skipped.",
            }
        subset_cols = existing

    dup_count = int(df.duplicated(subset=subset_cols).sum())
    passed = dup_count == 0

    if passed:
        logger.info("[%s] Duplicate check PASSED — 0 duplicates.", dataset_name)
    else:
        logger.warning(
            "[%s] Duplicate check FAILED — %d duplicate row(s) found.",
            dataset_name,
            dup_count,
        )

    return {
        "check": "no_duplicates",
        "dataset": dataset_name,
        "passed": passed,
        "duplicate_count": dup_count,
        "subset_columns": subset_cols,
    }


def validate_missingness(
    df: pd.DataFrame,
    threshold_pct: float = 50.0,
    dataset_name: str = "dataset",
) -> Dict[str, Any]:
    """Validate per-column missingness against a threshold.

    Args:
        df: Input DataFrame.
        threshold_pct: Maximum acceptable percentage of missing values per
            column (0–100). Columns exceeding this are flagged.
        dataset_name: Human-readable name for log messages.

    Returns:
        Dictionary with ``passed``, ``total_rows``, and ``columns`` (a dict
        keyed by column name with ``missing_count``, ``missing_pct``,
        ``exceeds_threshold``).
    """
    total_rows = len(df)
    columns_report: Dict[str, Dict[str, Any]] = {}
    any_exceeds = False

    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        missing_pct = round((missing_count / total_rows * 100) if total_rows > 0 else 0.0, 2)
        exceeds = missing_pct > threshold_pct
        if exceeds:
            any_exceeds = True
            logger.warning(
                "[%s] Column '%s' has %.1f%% missing (threshold: %.1f%%).",
                dataset_name,
                col,
                missing_pct,
                threshold_pct,
            )
        columns_report[col] = {
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "exceeds_threshold": exceeds,
        }

    passed = not any_exceeds

    if passed:
        logger.info(
            "[%s] Missingness check PASSED — no column exceeds %.1f%% threshold.",
            dataset_name,
            threshold_pct,
        )
    else:
        flagged = [c for c, v in columns_report.items() if v["exceeds_threshold"]]
        logger.warning(
            "[%s] Missingness check FAILED — %d column(s) exceed threshold: %s",
            dataset_name,
            len(flagged),
            flagged,
        )

    return {
        "check": "missingness",
        "dataset": dataset_name,
        "passed": passed,
        "threshold_pct": threshold_pct,
        "total_rows": total_rows,
        "columns": columns_report,
    }


# ---------------------------------------------------------------------------
# Comprehensive validation suite
# ---------------------------------------------------------------------------

def run_validation_suite(
    df: pd.DataFrame,
    dataset_name: str = "dataset",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run all applicable validation checks on a DataFrame.

    The ``config`` dictionary controls which checks run and their parameters.
    Supported keys (all optional):

    - ``required_columns``: ``List[str]`` — columns that must be present.
    - ``date_col``: ``str`` — name of the date column for range validation.
    - ``min_date`` / ``max_date``: ``str`` — ISO-8601 date boundaries.
    - ``lat_col`` / ``lon_col``: ``str`` — coordinate column names.
    - ``numeric_ranges``: ``Dict[str, Dict]`` — ``{col: {min: float, max: float}}``.
    - ``duplicate_subset``: ``List[str]`` — columns for duplicate detection.
    - ``missing_threshold_pct``: ``float`` — missingness threshold.

    Args:
        df: Input DataFrame.
        dataset_name: Human-readable name for log messages.
        config: Configuration dictionary (see above). If ``None``, sensible
            defaults are applied.

    Returns:
        Comprehensive validation report dictionary.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pd.DataFrame, got {type(df).__name__}")

    config = config or {}
    results: Dict[str, Any] = {
        "dataset": dataset_name,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "checks": [],
        "overall_passed": True,
    }

    logger.info(
        "=== Running validation suite for '%s' (%d rows, %d cols) ===",
        dataset_name,
        len(df),
        len(df.columns),
    )

    # 1. Required columns
    if "required_columns" in config:
        check = validate_required_columns(
            df, config["required_columns"], dataset_name
        )
        results["checks"].append(check)
        if not check["passed"]:
            results["overall_passed"] = False

    # 2. Date range
    if "date_col" in config:
        check = validate_date_range(
            df,
            config["date_col"],
            config.get("min_date"),
            config.get("max_date"),
        )
        results["checks"].append(check)
        if not check["passed"]:
            results["overall_passed"] = False

    # 3. Coordinate range
    lat_col = config.get("lat_col")
    lon_col = config.get("lon_col")
    if lat_col or lon_col:
        check = validate_coordinate_range(
            df,
            lat_col=lat_col or "latitude",
            lon_col=lon_col or "longitude",
        )
        results["checks"].append(check)
        if not check["passed"]:
            results["overall_passed"] = False

    # 4. Numeric ranges
    for col, bounds in config.get("numeric_ranges", {}).items():
        check = validate_numeric_range(
            df,
            col,
            min_val=bounds.get("min"),
            max_val=bounds.get("max"),
            col_name=bounds.get("name", col),
        )
        results["checks"].append(check)
        if not check["passed"]:
            results["overall_passed"] = False

    # 5. Duplicates
    dup_subset = config.get("duplicate_subset")
    check = validate_no_duplicates(df, dup_subset, dataset_name)
    results["checks"].append(check)
    if not check["passed"]:
        results["overall_passed"] = False

    # 6. Missingness
    threshold = config.get("missing_threshold_pct", 50.0)
    check = validate_missingness(df, threshold, dataset_name)
    results["checks"].append(check)
    if not check["passed"]:
        results["overall_passed"] = False

    status = "PASSED" if results["overall_passed"] else "FAILED"
    logger.info(
        "=== Validation suite for '%s' %s (%d checks) ===",
        dataset_name,
        status,
        len(results["checks"]),
    )

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_quality_report(
    validation_results: Dict[str, Any],
    output_path: Union[str, Path],
) -> Path:
    """Save a validation report as a CSV file.

    Each row represents one validation check with its result and details.

    Args:
        validation_results: Output of :func:`run_validation_suite`.
        output_path: File path for the CSV report.

    Returns:
        Resolved ``Path`` of the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    dataset_name = validation_results.get("dataset", "unknown")

    for check in validation_results.get("checks", []):
        row: Dict[str, Any] = {
            "dataset": dataset_name,
            "check": check.get("check", ""),
            "passed": check.get("passed", ""),
        }

        # Flatten relevant details based on check type
        check_type = check.get("check", "")
        if check_type == "required_columns":
            row["detail"] = (
                f"missing={check.get('missing_columns', [])}"
            )
        elif check_type == "date_range":
            row["detail"] = (
                f"invalid={check.get('invalid_count', 0)}, "
                f"out_of_range={check.get('out_of_range_count', 0)}"
            )
        elif check_type == "coordinate_range":
            row["detail"] = (
                f"invalid_lat={check.get('invalid_lat_count', 0)}, "
                f"invalid_lon={check.get('invalid_lon_count', 0)}"
            )
        elif check_type == "numeric_range":
            row["detail"] = (
                f"column={check.get('column', '')}, "
                f"out_of_range={check.get('out_of_range_count', 0)}"
            )
        elif check_type == "no_duplicates":
            row["detail"] = f"duplicates={check.get('duplicate_count', 0)}"
        elif check_type == "missingness":
            cols_info = check.get("columns", {})
            flagged = [
                f"{c}({v['missing_pct']}%)"
                for c, v in cols_info.items()
                if v.get("exceeds_threshold")
            ]
            row["detail"] = (
                f"flagged_columns={flagged}" if flagged else "all_within_threshold"
            )
        else:
            row["detail"] = str(check)

        rows.append(row)

    # Add summary row
    rows.append({
        "dataset": dataset_name,
        "check": "OVERALL",
        "passed": validation_results.get("overall_passed", ""),
        "detail": (
            f"total_rows={validation_results.get('total_rows', 0)}, "
            f"total_columns={validation_results.get('total_columns', 0)}"
        ),
    })

    report_df = pd.DataFrame(rows)
    report_df.to_csv(output_path, index=False)
    logger.info("Quality report saved to %s", output_path)

    return output_path
