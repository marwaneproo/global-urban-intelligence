"""
Visualization package for Global Urban Intelligence.

Provides high-resolution, publication-quality visualizations covering:
- Distribution analysis (histograms, KDE, box plots, violin plots, ECDFs)
- Comparison analysis (bar charts, dot plots, heatmaps, small multiples)
- Temporal dynamics (time series, rolling averages, seasonal profiles, calendar heatmaps)
- Correlation & relationship modeling (scatter, regressions, pairplots, bubble charts)
- Geographic intelligence (spatial distribution, comparative mapping)
- Executive dashboards (multi-panel analytical summary overviews)
"""

from src.visualization.distributions import (
    plot_histogram,
    plot_histogram_kde,
    plot_boxplot,
    plot_violin,
    plot_density,
    plot_ecdf,
)
from src.visualization.comparisons import (
    plot_bar_chart,
    plot_grouped_bar,
    plot_horizontal_bar,
    plot_dot_plot,
    plot_heatmap,
    plot_small_multiples,
)
from src.visualization.temporal import (
    plot_timeseries,
    plot_multi_timeseries,
    plot_rolling_average,
    plot_seasonal_comparison,
    plot_calendar_heatmap,
)
from src.visualization.correlations import (
    plot_correlation_heatmap,
    plot_scatter,
    plot_scatter_regression,
    plot_pairplot,
    plot_bubble_chart,
)
from src.visualization.geographic import (
    plot_city_map,
    plot_interactive_map,
    plot_geographic_comparison,
)
from src.visualization.dashboard_charts import (
    create_dashboard_overview,
    create_plotly_dashboard,
)

CITY_COLORS = {
    "Casablanca": "#e74c3c",
    "Rabat": "#3498db",
    "Paris": "#2ecc71",
    "Madrid": "#f39c12",
    "Lisbon": "#9b59b6",
}

__all__ = [
    "CITY_COLORS",
    "plot_histogram",
    "plot_histogram_kde",
    "plot_boxplot",
    "plot_violin",
    "plot_density",
    "plot_ecdf",
    "plot_bar_chart",
    "plot_grouped_bar",
    "plot_horizontal_bar",
    "plot_dot_plot",
    "plot_heatmap",
    "plot_small_multiples",
    "plot_timeseries",
    "plot_multi_timeseries",
    "plot_rolling_average",
    "plot_seasonal_comparison",
    "plot_calendar_heatmap",
    "plot_correlation_heatmap",
    "plot_scatter",
    "plot_scatter_regression",
    "plot_pairplot",
    "plot_bubble_chart",
    "plot_city_map",
    "plot_interactive_map",
    "plot_geographic_comparison",
    "create_dashboard_overview",
    "create_plotly_dashboard",
]
