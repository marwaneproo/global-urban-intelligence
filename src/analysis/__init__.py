"""
Analysis package for Global Urban Intelligence.

Provides descriptive statistics, statistical tests, and insight generation
for urban environmental data analysis.
"""

from src.analysis.descriptive import (
    compute_descriptive_stats,
    compute_percentiles,
    compute_group_stats,
    summarize_dataset,
)
from src.analysis.statistical import (
    test_normality,
    compute_correlation_matrix,
    compute_pairwise_correlations,
    test_group_differences,
    compute_confidence_interval,
    detect_outliers_iqr,
    detect_outliers_zscore,
    run_regression,
    run_pca,
    run_clustering,
)
from src.analysis.insights import (
    generate_key_findings,
    generate_recommendations,
    compile_analysis_summary,
    save_analysis_summary,
)

__all__ = [
    # Descriptive
    "compute_descriptive_stats",
    "compute_percentiles",
    "compute_group_stats",
    "summarize_dataset",
    # Statistical
    "test_normality",
    "compute_correlation_matrix",
    "compute_pairwise_correlations",
    "test_group_differences",
    "compute_confidence_interval",
    "detect_outliers_iqr",
    "detect_outliers_zscore",
    "run_regression",
    "run_pca",
    "run_clustering",
    # Insights
    "generate_key_findings",
    "generate_recommendations",
    "compile_analysis_summary",
    "save_analysis_summary",
]
