"""
Descriptive statistics module for urban environmental data analysis.

Provides functions to compute comprehensive descriptive statistics,
percentiles, grouped statistics, and dataset summaries.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Reproducibility
np.random.seed(42)


def compute_descriptive_stats(
    df: pd.DataFrame,
    numeric_cols: List[str],
) -> pd.DataFrame:
    """Compute comprehensive descriptive statistics for numeric columns.

    Args:
        df: Input DataFrame.
        numeric_cols: List of numeric column names to analyze.

    Returns:
        DataFrame indexed by column name with statistics as columns:
        mean, median, mode, min, max, range, variance, std, q25, q50,
        q75, iqr, skewness, kurtosis, count, missing_count, missing_pct.
    """
    logger.info("Computing descriptive statistics for %d columns.", len(numeric_cols))

    results: Dict[str, Dict[str, float]] = {}

    for col in numeric_cols:
        if col not in df.columns:
            logger.warning("Column '%s' not found in DataFrame. Skipping.", col)
            continue

        series = df[col].dropna()
        total = len(df[col])
        missing = df[col].isna().sum()

        if len(series) == 0:
            logger.warning("Column '%s' has no non-null values.", col)
            results[col] = {
                "mean": np.nan,
                "median": np.nan,
                "mode": np.nan,
                "min": np.nan,
                "max": np.nan,
                "range": np.nan,
                "variance": np.nan,
                "std": np.nan,
                "q25": np.nan,
                "q50": np.nan,
                "q75": np.nan,
                "iqr": np.nan,
                "skewness": np.nan,
                "kurtosis": np.nan,
                "count": 0,
                "missing_count": int(missing),
                "missing_pct": 100.0 if total > 0 else 0.0,
            }
            continue

        q25 = float(series.quantile(0.25))
        q50 = float(series.quantile(0.50))
        q75 = float(series.quantile(0.75))

        # Mode: take the first mode value
        mode_values = series.mode()
        mode_val = float(mode_values.iloc[0]) if len(mode_values) > 0 else np.nan

        results[col] = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "mode": mode_val,
            "min": float(series.min()),
            "max": float(series.max()),
            "range": float(series.max() - series.min()),
            "variance": float(series.var()),
            "std": float(series.std()),
            "q25": q25,
            "q50": q50,
            "q75": q75,
            "iqr": q75 - q25,
            "skewness": float(series.skew()),
            "kurtosis": float(series.kurtosis()),
            "count": int(len(series)),
            "missing_count": int(missing),
            "missing_pct": round(float(missing / total * 100), 2) if total > 0 else 0.0,
        }

    stats_df = pd.DataFrame(results).T
    stats_df.index.name = "column"
    logger.info("Descriptive statistics computed successfully.")
    return stats_df


def compute_percentiles(
    df: pd.DataFrame,
    col: str,
    percentiles: Optional[List[int]] = None,
) -> Dict[str, float]:
    """Compute specific percentile values for a column.

    Args:
        df: Input DataFrame.
        col: Column name to compute percentiles for.
        percentiles: List of percentile values (0-100).
            Defaults to [5, 10, 25, 50, 75, 90, 95].

    Returns:
        Dictionary mapping percentile labels (e.g. "p5") to their values.
    """
    if percentiles is None:
        percentiles = [5, 10, 25, 50, 75, 90, 95]

    logger.info("Computing percentiles for column '%s': %s", col, percentiles)

    if col not in df.columns:
        logger.error("Column '%s' not found in DataFrame.", col)
        return {}

    series = df[col].dropna()
    if len(series) == 0:
        logger.warning("Column '%s' has no non-null values.", col)
        return {f"p{p}": np.nan for p in percentiles}

    result: Dict[str, float] = {}
    for p in percentiles:
        result[f"p{p}"] = float(np.percentile(series, p))

    logger.info("Percentiles computed for '%s'.", col)
    return result


def compute_group_stats(
    df: pd.DataFrame,
    group_col: str,
    value_cols: List[str],
) -> pd.DataFrame:
    """Compute descriptive statistics grouped by a categorical column.

    Args:
        df: Input DataFrame.
        group_col: Column to group by (e.g. 'city').
        value_cols: Numeric columns to compute stats for.

    Returns:
        DataFrame with multi-level index (group, column) and statistics
        as columns.
    """
    logger.info(
        "Computing group stats: group_col='%s', value_cols=%s",
        group_col,
        value_cols,
    )

    if group_col not in df.columns:
        logger.error("Group column '%s' not found in DataFrame.", group_col)
        return pd.DataFrame()

    valid_cols = [c for c in value_cols if c in df.columns]
    if not valid_cols:
        logger.error("No valid value columns found in DataFrame.")
        return pd.DataFrame()

    all_results: List[pd.DataFrame] = []

    for group_name, group_df in df.groupby(group_col):
        group_stats = compute_descriptive_stats(group_df, valid_cols)
        group_stats.insert(0, "group", group_name)
        all_results.append(group_stats)

    if not all_results:
        return pd.DataFrame()

    combined = pd.concat(all_results, ignore_index=False)
    combined = combined.reset_index().rename(columns={"column": "variable"})
    combined = combined.set_index(["group", "variable"])

    logger.info("Group statistics computed for %d groups.", combined.index.get_level_values("group").nunique())
    return combined


def summarize_dataset(
    df: pd.DataFrame,
    name: str,
) -> Dict[str, Any]:
    """Create a comprehensive summary of a dataset.

    Args:
        df: Input DataFrame.
        name: Human-readable name for the dataset.

    Returns:
        Dictionary containing:
        - name, shape, n_rows, n_cols
        - dtypes: dict of column -> dtype string
        - numeric_stats: descriptive stats DataFrame for numeric columns
        - categorical_stats: dict per categorical column with value_counts,
          n_unique, top_value, top_freq
        - memory_usage_mb: approximate memory usage
        - missing_summary: dict per column with count and percentage
    """
    logger.info("Summarizing dataset '%s' with shape %s.", name, df.shape)

    summary: Dict[str, Any] = {
        "name": name,
        "shape": df.shape,
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 4),
    }

    # Numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        summary["numeric_stats"] = compute_descriptive_stats(df, numeric_cols)
    else:
        summary["numeric_stats"] = pd.DataFrame()

    # Categorical columns
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    cat_summary: Dict[str, Dict[str, Any]] = {}
    for col in cat_cols:
        vc = df[col].value_counts()
        cat_summary[col] = {
            "n_unique": int(df[col].nunique()),
            "top_value": str(vc.index[0]) if len(vc) > 0 else None,
            "top_freq": int(vc.iloc[0]) if len(vc) > 0 else 0,
            "value_counts": vc.head(10).to_dict(),
        }
    summary["categorical_stats"] = cat_summary

    # Missing data summary
    missing_summary: Dict[str, Dict[str, Union[int, float]]] = {}
    for col in df.columns:
        miss_count = int(df[col].isna().sum())
        miss_pct = round(miss_count / len(df) * 100, 2) if len(df) > 0 else 0.0
        missing_summary[col] = {"count": miss_count, "pct": miss_pct}
    summary["missing_summary"] = missing_summary

    logger.info("Dataset summary for '%s' complete.", name)
    return summary
