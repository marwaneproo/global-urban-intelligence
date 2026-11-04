"""
Preprocessing subpackage for Global Urban Intelligence.

Provides modules for data validation, cleaning, transformation, and integration
of air quality, weather, and demographic datasets.
"""

from src.preprocessing.validation import (
    validate_required_columns,
    validate_date_range,
    validate_coordinate_range,
    validate_numeric_range,
    validate_no_duplicates,
    validate_missingness,
    run_validation_suite,
    generate_quality_report,
)
from src.preprocessing.cleaning import (
    standardize_columns,
    remove_exact_duplicates,
    parse_dates,
    convert_numeric,
    validate_units,
    handle_missing_values,
    flag_suspicious_values,
    clean_air_quality,
    clean_weather,
    clean_demographics,
    generate_cleaning_report,
)
from src.preprocessing.transformation import (
    add_date_features,
    add_season,
    compute_monthly_aggregates,
    compute_daily_aggregates,
    compute_city_summaries,
    compute_rolling_averages,
    create_air_quality_index_category,
    transform_air_quality,
    transform_weather,
    transform_demographics,
)
from src.preprocessing.integration import (
    integrate_air_quality_weather,
    add_demographics_context,
    create_analytical_dataset,
    generate_integration_report,
)

__all__ = [
    # Validation
    "validate_required_columns",
    "validate_date_range",
    "validate_coordinate_range",
    "validate_numeric_range",
    "validate_no_duplicates",
    "validate_missingness",
    "run_validation_suite",
    "generate_quality_report",
    # Cleaning
    "standardize_columns",
    "remove_exact_duplicates",
    "parse_dates",
    "convert_numeric",
    "validate_units",
    "handle_missing_values",
    "flag_suspicious_values",
    "clean_air_quality",
    "clean_weather",
    "clean_demographics",
    "generate_cleaning_report",
    # Transformation
    "add_date_features",
    "add_season",
    "compute_monthly_aggregates",
    "compute_daily_aggregates",
    "compute_city_summaries",
    "compute_rolling_averages",
    "create_air_quality_index_category",
    "transform_air_quality",
    "transform_weather",
    "transform_demographics",
    # Integration
    "integrate_air_quality_weather",
    "add_demographics_context",
    "create_analytical_dataset",
    "generate_integration_report",
]
