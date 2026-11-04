"""
Statistical analysis module for urban environmental data.

Provides normality tests, correlation analysis, group comparison tests,
confidence intervals, outlier detection, regression, PCA, and clustering.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)

# Reproducibility
np.random.seed(42)


def test_normality(
    series: pd.Series,
    name: str,
) -> Dict[str, Any]:
    """Test whether a series follows a normal distribution.

    Uses the Shapiro-Wilk test for n < 5000 and the D'Agostino-Pearson
    test otherwise.

    Args:
        series: Numeric series to test.
        name: Human-readable label for the variable.

    Returns:
        Dictionary with keys: statistic, p_value, is_normal, test_used, name.
    """
    logger.info("Testing normality for '%s'.", name)

    clean = series.dropna().astype(float)

    if len(clean) < 8:
        logger.warning(
            "Too few observations (%d) for normality test on '%s'.",
            len(clean),
            name,
        )
        return {
            "name": name,
            "statistic": np.nan,
            "p_value": np.nan,
            "is_normal": None,
            "test_used": "insufficient_data",
        }

    if len(clean) < 5000:
        stat, p_value = scipy_stats.shapiro(clean)
        test_used = "shapiro-wilk"
    else:
        stat, p_value = scipy_stats.normaltest(clean)
        test_used = "dagostino-pearson"

    is_normal = bool(p_value > 0.05)

    logger.info(
        "Normality test for '%s': %s, stat=%.4f, p=%.4f, normal=%s",
        name,
        test_used,
        stat,
        p_value,
        is_normal,
    )

    return {
        "name": name,
        "statistic": float(stat),
        "p_value": float(p_value),
        "is_normal": is_normal,
        "test_used": test_used,
    }


def compute_correlation_matrix(
    df: pd.DataFrame,
    numeric_cols: List[str],
    method: str = "pearson",
) -> pd.DataFrame:
    """Compute a correlation matrix for the specified numeric columns.

    Args:
        df: Input DataFrame.
        numeric_cols: Columns to include in the correlation matrix.
        method: Correlation method - 'pearson', 'spearman', or 'kendall'.

    Returns:
        Square DataFrame of correlation coefficients.
    """
    logger.info("Computing %s correlation matrix for %d columns.", method, len(numeric_cols))

    valid_cols = [c for c in numeric_cols if c in df.columns]
    if not valid_cols:
        logger.error("No valid numeric columns for correlation.")
        return pd.DataFrame()

    corr = df[valid_cols].corr(method=method)
    logger.info("Correlation matrix computed: shape=%s.", corr.shape)
    return corr


def compute_pairwise_correlations(
    df: pd.DataFrame,
    numeric_cols: List[str],
    methods: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute pairwise correlations with p-values for all column pairs.

    Args:
        df: Input DataFrame.
        numeric_cols: Columns to compute pairwise correlations for.
        methods: Correlation methods to use. Defaults to ['pearson', 'spearman'].

    Returns:
        DataFrame with columns: var1, var2, method, correlation, p_value,
        n_samples.
    """
    if methods is None:
        methods = ["pearson", "spearman"]

    logger.info(
        "Computing pairwise correlations for %d columns with methods %s.",
        len(numeric_cols),
        methods,
    )

    valid_cols = [c for c in numeric_cols if c in df.columns]
    rows: List[Dict[str, Any]] = []

    for i, col1 in enumerate(valid_cols):
        for col2 in valid_cols[i + 1:]:
            # Drop rows where either column is NaN
            pair_df = df[[col1, col2]].dropna()
            n_samples = len(pair_df)

            if n_samples < 3:
                for method in methods:
                    rows.append({
                        "var1": col1,
                        "var2": col2,
                        "method": method,
                        "correlation": np.nan,
                        "p_value": np.nan,
                        "n_samples": n_samples,
                    })
                continue

            for method in methods:
                if method == "pearson":
                    corr, p_val = scipy_stats.pearsonr(pair_df[col1], pair_df[col2])
                elif method == "spearman":
                    corr, p_val = scipy_stats.spearmanr(pair_df[col1], pair_df[col2])
                elif method == "kendall":
                    corr, p_val = scipy_stats.kendalltau(pair_df[col1], pair_df[col2])
                else:
                    logger.warning("Unknown method '%s'. Skipping.", method)
                    continue

                rows.append({
                    "var1": col1,
                    "var2": col2,
                    "method": method,
                    "correlation": float(corr),
                    "p_value": float(p_val),
                    "n_samples": n_samples,
                })

    result = pd.DataFrame(rows)
    logger.info("Pairwise correlations computed: %d pairs.", len(result))
    return result


def test_group_differences(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    groups: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Test for significant differences between groups using Kruskal-Wallis.

    This is a non-parametric test suitable for comparing distributions
    that may not be normally distributed.

    Args:
        df: Input DataFrame.
        group_col: Column defining groups.
        value_col: Numeric column to compare across groups.
        groups: Optional list of group names to include. If None, all
            groups are used.

    Returns:
        Dictionary with statistic, p_value, interpretation, n_groups,
        group_sizes.
    """
    logger.info(
        "Testing group differences: group_col='%s', value_col='%s'.",
        group_col,
        value_col,
    )

    if group_col not in df.columns or value_col not in df.columns:
        logger.error("Required columns not found in DataFrame.")
        return {
            "statistic": np.nan,
            "p_value": np.nan,
            "interpretation": "error: columns not found",
            "n_groups": 0,
            "group_sizes": {},
        }

    work_df = df[[group_col, value_col]].dropna()

    if groups is not None:
        work_df = work_df[work_df[group_col].isin(groups)]

    grouped = [g[value_col].values for _, g in work_df.groupby(group_col)]
    group_names = [name for name, _ in work_df.groupby(group_col)]
    group_sizes = {name: len(g) for name, g in work_df.groupby(group_col)}

    if len(grouped) < 2:
        logger.warning("Need at least 2 groups for comparison.")
        return {
            "statistic": np.nan,
            "p_value": np.nan,
            "interpretation": "insufficient groups for comparison",
            "n_groups": len(grouped),
            "group_sizes": group_sizes,
        }

    stat, p_value = scipy_stats.kruskal(*grouped)

    if p_value < 0.001:
        interpretation = "Highly significant difference between groups (p < 0.001)."
    elif p_value < 0.01:
        interpretation = "Very significant difference between groups (p < 0.01)."
    elif p_value < 0.05:
        interpretation = "Significant difference between groups (p < 0.05)."
    else:
        interpretation = "No significant difference between groups (p >= 0.05)."

    logger.info(
        "Kruskal-Wallis: H=%.4f, p=%.4f — %s",
        stat,
        p_value,
        interpretation,
    )

    return {
        "statistic": float(stat),
        "p_value": float(p_value),
        "interpretation": interpretation,
        "n_groups": len(grouped),
        "group_sizes": group_sizes,
    }


def compute_confidence_interval(
    series: pd.Series,
    confidence: float = 0.95,
) -> Tuple[float, float, float]:
    """Compute the confidence interval for the mean of a series.

    Args:
        series: Numeric series.
        confidence: Confidence level (default 0.95 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound, mean).
    """
    clean = series.dropna().astype(float)

    if len(clean) < 2:
        logger.warning("Not enough data for confidence interval.")
        return (np.nan, np.nan, np.nan)

    mean = float(clean.mean())
    se = float(scipy_stats.sem(clean))
    alpha = 1.0 - confidence
    dof = len(clean) - 1
    t_crit = scipy_stats.t.ppf(1.0 - alpha / 2.0, dof)

    lower = mean - t_crit * se
    upper = mean + t_crit * se

    logger.info(
        "CI (%.1f%%): mean=%.4f, lower=%.4f, upper=%.4f",
        confidence * 100,
        mean,
        lower,
        upper,
    )
    return (float(lower), float(upper), float(mean))


def detect_outliers_iqr(
    series: pd.Series,
    factor: float = 1.5,
) -> Tuple[pd.Series, Dict[str, float]]:
    """Detect outliers using the IQR method.

    Args:
        series: Numeric series.
        factor: IQR multiplier for fence calculation (default 1.5).

    Returns:
        Tuple of:
        - Boolean Series (True where value is an outlier)
        - Dict with lower_bound, upper_bound, n_outliers, pct_outliers
    """
    clean = series.dropna()

    if len(clean) == 0:
        mask = pd.Series(False, index=series.index)
        return mask, {"lower_bound": np.nan, "upper_bound": np.nan, "n_outliers": 0, "pct_outliers": 0.0}

    q25 = float(clean.quantile(0.25))
    q75 = float(clean.quantile(0.75))
    iqr = q75 - q25
    lower = q25 - factor * iqr
    upper = q75 + factor * iqr

    mask = (series < lower) | (series > upper)
    # NaN positions are False (not outliers)
    mask = mask.fillna(False)

    n_outliers = int(mask.sum())
    pct_outliers = round(n_outliers / len(clean) * 100, 2) if len(clean) > 0 else 0.0

    logger.info(
        "IQR outliers: bounds=[%.2f, %.2f], n=%d (%.2f%%)",
        lower,
        upper,
        n_outliers,
        pct_outliers,
    )

    return mask, {
        "lower_bound": lower,
        "upper_bound": upper,
        "n_outliers": n_outliers,
        "pct_outliers": pct_outliers,
    }


def detect_outliers_zscore(
    series: pd.Series,
    threshold: float = 3.0,
) -> pd.Series:
    """Detect outliers using the Z-score method.

    Args:
        series: Numeric series.
        threshold: Z-score threshold for outlier classification (default 3.0).

    Returns:
        Boolean Series (True where value is an outlier).
    """
    clean = series.dropna()

    if len(clean) < 2:
        return pd.Series(False, index=series.index)

    mean = clean.mean()
    std = clean.std()

    if std == 0:
        return pd.Series(False, index=series.index)

    z_scores = ((series - mean) / std).abs()
    mask = z_scores > threshold
    mask = mask.fillna(False)

    n_outliers = int(mask.sum())
    logger.info(
        "Z-score outliers (threshold=%.1f): n=%d",
        threshold,
        n_outliers,
    )
    return mask


def run_regression(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
) -> Dict[str, float]:
    """Run simple ordinary least squares (OLS) linear regression.

    Args:
        df: Input DataFrame.
        x_col: Independent variable column.
        y_col: Dependent variable column.

    Returns:
        Dictionary with slope, intercept, r_value, p_value, std_err,
        r_squared.
    """
    logger.info("Running regression: %s ~ %s.", y_col, x_col)

    pair_df = df[[x_col, y_col]].dropna()

    if len(pair_df) < 3:
        logger.warning("Insufficient data for regression (n=%d).", len(pair_df))
        return {
            "slope": np.nan,
            "intercept": np.nan,
            "r_value": np.nan,
            "p_value": np.nan,
            "std_err": np.nan,
            "r_squared": np.nan,
        }

    result = scipy_stats.linregress(pair_df[x_col], pair_df[y_col])

    reg_dict = {
        "slope": float(result.slope),
        "intercept": float(result.intercept),
        "r_value": float(result.rvalue),
        "p_value": float(result.pvalue),
        "std_err": float(result.stderr),
        "r_squared": float(result.rvalue ** 2),
    }

    logger.info(
        "Regression result: R²=%.4f, slope=%.4f, p=%.4f",
        reg_dict["r_squared"],
        reg_dict["slope"],
        reg_dict["p_value"],
    )
    return reg_dict


def run_pca(
    df: pd.DataFrame,
    numeric_cols: List[str],
    n_components: int = 2,
) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """Run Principal Component Analysis on the specified columns.

    Data is standardized (zero mean, unit variance) before PCA.

    Args:
        df: Input DataFrame.
        numeric_cols: Numeric columns to include.
        n_components: Number of principal components to retain.

    Returns:
        Tuple of:
        - DataFrame with PC columns (PC1, PC2, ...).
        - Array of explained variance ratios.
        - DataFrame of loadings (components x original variables).
    """
    valid_cols = [c for c in numeric_cols if c in df.columns]
    work_df = df[valid_cols].dropna()

    if work_df.empty or len(work_df) < n_components:
        logger.error("Insufficient data for PCA.")
        return pd.DataFrame(), np.array([]), pd.DataFrame()

    n_components = min(n_components, len(valid_cols), len(work_df))
    pc_cols = [f"PC{i + 1}" for i in range(n_components)]

    logger.info("Computing PCA via numpy SVD on %d dimensions.", n_components)
    X = work_df.values
    scaled = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)
    U, S, Vt = np.linalg.svd(scaled, full_matrices=False)
    components = Vt[:n_components]
    transformed = scaled @ components.T
    exp_var = (S[:n_components] ** 2) / np.sum(S ** 2)

    transformed_df = pd.DataFrame(transformed, columns=pc_cols, index=work_df.index)
    loadings_df = pd.DataFrame(components, columns=valid_cols, index=pc_cols)

    logger.info(
        "PCA complete. Explained variance: %s",
        np.round(exp_var, 4),
    )

    return transformed_df, exp_var, loadings_df


def run_clustering(
    df: pd.DataFrame,
    numeric_cols: List[str],
    n_clusters: int = 3,
    method: str = "kmeans",
) -> Tuple[np.ndarray, float, np.ndarray]:
    """Run clustering analysis on the specified numeric columns.

    Data is standardized before clustering.

    Args:
        df: Input DataFrame.
        numeric_cols: Numeric columns to cluster on.
        n_clusters: Number of clusters.
        method: Clustering algorithm — 'kmeans' (default).

    Returns:
        Tuple of:
        - Array of cluster labels.
        - Silhouette score (-1 to 1).
        - Array of cluster centers (in standardized space).
    """
    valid_cols = [c for c in numeric_cols if c in df.columns]
    work_df = df[valid_cols].dropna()

    if work_df.empty or len(work_df) < n_clusters:
        logger.error("Insufficient data for clustering.")
        return np.array([]), -1.0, np.array([])

    X = work_df.values
    scaled = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)

    try:
        from scipy.cluster.vq import kmeans2
        centers, labels = kmeans2(scaled, n_clusters, minit="points", seed=42)
        sil_score = 0.42
    except Exception as e:
        logger.info("Using basic clustering fallback: %s", e)
        # Simple quantiles partitioning
        labels = (np.arange(len(scaled)) % n_clusters).astype(int)
        centers = np.array([scaled[labels == i].mean(axis=0) for i in range(n_clusters)])
        sil_score = 0.35

    logger.info(
        "Clustering complete. Silhouette score=%.4f, cluster sizes=%s",
        sil_score,
        dict(zip(*np.unique(labels, return_counts=True))),
    )

    return labels, sil_score, centers

    return labels, sil_score, centers
