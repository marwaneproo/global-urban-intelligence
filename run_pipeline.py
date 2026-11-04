#!/usr/bin/env python3
"""
Global Urban Intelligence — Master Analytical Pipeline

Executes the complete end-to-end data engineering, statistical profiling,
analytical modeling, and visualization workflow across European and Mediterranean cities.

Usage:
    python run_pipeline.py --demo      # Run with reproducible demonstration data (offline)
    python run_pipeline.py --live      # Run with real API data ingestion and fallback
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict

import numpy as np
import pandas as pd
import yaml

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set writable Matplotlib cache directory to avoid permissions hang
os.environ["MPLCONFIGDIR"] = os.path.join(PROJECT_ROOT, "outputs", ".mpl_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

from src.data_collection.collect_all import run_collection
from src.preprocessing.validation import run_validation_suite, generate_quality_report
from src.preprocessing.cleaning import (
    clean_air_quality,
    clean_weather,
    clean_demographics,
    generate_cleaning_report,
)
from src.preprocessing.transformation import (
    transform_air_quality,
    transform_weather,
    transform_demographics,
    compute_city_summaries,
)
from src.preprocessing.integration import (
    create_analytical_dataset,
    generate_integration_report,
)
from src.analysis.descriptive import (
    compute_descriptive_stats,
    compute_group_stats,
    summarize_dataset,
)
from src.analysis.statistical import (
    compute_correlation_matrix,
    compute_pairwise_correlations,
    test_normality,
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
import src.visualization as viz

CITY_COLORS = {
    "Casablanca": "#e74c3c",
    "Rabat": "#3498db",
    "Paris": "#2ecc71",
    "Madrid": "#f39c12",
    "Lisbon": "#9b59b6",
}

# Ensure matplotlib runs in headless mode
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


def setup_pipeline_logging(log_file: str) -> logging.Logger:
    """Configure console and file logging."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    while logger.handlers:
        logger.handlers.pop()

    formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s: %(message)s")

    import io
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def load_configurations() -> tuple:
    """Load configuration files."""
    cities_path = os.path.join(PROJECT_ROOT, "config", "cities.json")
    settings_path = os.path.join(PROJECT_ROOT, "config", "settings.yaml")

    with open(cities_path, "r", encoding="utf-8") as f:
        cities_cfg = json.load(f)

    with open(settings_path, "r", encoding="utf-8") as f:
        settings_cfg = yaml.safe_load(f)

    return cities_cfg, settings_cfg


def main(mode: str = "demo") -> None:
    """Execute the end-to-end data pipeline."""
    start_time = time.time()
    log_path = os.path.join(PROJECT_ROOT, "outputs", "reports", "pipeline.log")
    logger = setup_pipeline_logging(log_path)

    logger.info("================================================================================")
    logger.info("  GLOBAL URBAN INTELLIGENCE: END-TO-END ANALYTICAL PIPELINE")
    logger.info("================================================================================")
    logger.info("Mode: %s | Project Root: %s", mode.upper(), PROJECT_ROOT)

    cities_cfg, settings_cfg = load_configurations()

    # -------------------------------------------------------------------------
    # STAGE 1: DATA COLLECTION
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 1: DATA ACQUISITION & RAW STORAGE")
    raw_dfs = run_collection(mode=mode, project_root=PROJECT_ROOT)
    aq_raw = raw_dfs["air_quality"]
    weather_raw = raw_dfs["weather"]
    demo_raw = raw_dfs["demographics"]

    # Write collection report
    coll_report_path = os.path.join(PROJECT_ROOT, "outputs", "reports", "data_collection_report.md")
    with open(coll_report_path, "w", encoding="utf-8") as f:
        f.write("# Data Collection & Provenance Report\n\n")
        f.write(f"- **Execution Timestamp**: {pd.Timestamp.now(tz='UTC').isoformat()}\n")
        f.write(f"- **Collection Mode**: `{mode.upper()}`\n")
        f.write(f"- **Air Quality Records**: {len(aq_raw):,} (Parameters: PM2.5, PM10)\n")
        f.write(f"- **Weather Records**: {len(weather_raw):,} (Variables: Temp, Humidity, Wind, Rain)\n")
        f.write(f"- **Demographics Records**: {len(demo_raw):,} (World Bank Country Indicators)\n")
        f.write(f"- **Data Provenance**: Explicitly tagged with `source` metadata.\n")
    logger.info("Saved data collection report to %s", coll_report_path)

    # -------------------------------------------------------------------------
    # STAGE 2: DATA PROFILING & QUALITY VALIDATION
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 2: DATA QUALITY VALIDATION & PROFILING")
    val_config = {
        "required_columns": ["city", "parameter", "value", "date"],
        "date_col": "date",
        "min_date": "2024-01-01",
        "max_date": "2024-12-31",
        "duplicate_subset": ["city", "parameter", "date", "station_id"],
        "missing_threshold_pct": 50.0,
    }
    val_results = run_validation_suite(aq_raw, "air_quality_raw", val_config)
    quality_report_path = os.path.join(PROJECT_ROOT, "outputs", "reports", "data_quality_report.csv")
    generate_quality_report(val_results, quality_report_path)

    # -------------------------------------------------------------------------
    # STAGE 3: DATA CLEANING
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 3: DATA CLEANING & STANDARDIZATION")
    aq_clean = clean_air_quality(aq_raw, settings_cfg)
    weather_clean = clean_weather(weather_raw, settings_cfg)
    demo_clean = clean_demographics(demo_raw, settings_cfg)

    # Persist cleaned interim datasets
    interim_dir = os.path.join(PROJECT_ROOT, "data", "interim")
    os.makedirs(interim_dir, exist_ok=True)
    aq_clean.to_csv(os.path.join(interim_dir, "air_quality_cleaned.csv"), index=False)
    weather_clean.to_csv(os.path.join(interim_dir, "weather_cleaned.csv"), index=False)
    demo_clean.to_csv(os.path.join(interim_dir, "demographics_cleaned.csv"), index=False)

    cleaning_report_path = os.path.join(PROJECT_ROOT, "outputs", "reports", "cleaning_report.md")
    generate_cleaning_report(aq_raw, aq_clean, "Air Quality", cleaning_report_path)

    # -------------------------------------------------------------------------
    # STAGE 4: FEATURE ENGINEERING & TRANSFORMATION
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 4: FEATURE ENGINEERING & TRANSFORMATION")
    aq_trans = transform_air_quality(aq_clean, settings_cfg)
    weather_trans = transform_weather(weather_clean, settings_cfg)
    demo_trans = transform_demographics(demo_clean, settings_cfg)

    aq_trans.to_csv(os.path.join(interim_dir, "air_quality_transformed.csv"), index=False)
    weather_trans.to_csv(os.path.join(interim_dir, "weather_transformed.csv"), index=False)

    # -------------------------------------------------------------------------
    # STAGE 5: DATA INTEGRATION
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 5: DATA INTEGRATION & ANALYTICAL DATASET CREATION")
    analytical_df = create_analytical_dataset(aq_trans, weather_trans, demo_trans, cities_cfg)

    # Save to primary processed path
    proc_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    os.makedirs(proc_dir, exist_ok=True)
    proc_csv = os.path.join(proc_dir, "urban_analytics.csv")
    analytical_df.to_csv(proc_csv, index=False)
    logger.info("Saved integrated analytical dataset -> %s (%d rows)", proc_csv, len(analytical_df))

    # Also mirror into outputs/datasets
    outputs_dataset_dir = os.path.join(PROJECT_ROOT, "outputs", "datasets")
    os.makedirs(outputs_dataset_dir, exist_ok=True)
    analytical_df.to_csv(os.path.join(outputs_dataset_dir, "urban_analytics.csv"), index=False)

    # Compute city summaries
    pm25_df = analytical_df[analytical_df["parameter"] == "pm25"] if "parameter" in analytical_df.columns else analytical_df
    city_summaries = compute_city_summaries(pm25_df, city_col="city", value_cols=["value", "temperature_mean", "wind_speed_mean"])
    city_summaries.to_csv(os.path.join(outputs_dataset_dir, "city_summaries.csv"), index=False)

    # -------------------------------------------------------------------------
    # STAGE 6: STATISTICAL & ADVANCED ANALYTICS
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 6: STATISTICAL MODELING & ADVANCED ANALYSIS")
    numeric_cols = ["value", "temperature_mean", "humidity_mean", "precipitation_sum", "wind_speed_mean"]
    valid_numeric = [c for c in numeric_cols if c in analytical_df.columns]

    # Descriptive statistics
    desc_stats = compute_descriptive_stats(analytical_df, valid_numeric)
    desc_stats.to_csv(os.path.join(PROJECT_ROOT, "outputs", "reports", "descriptive_statistics.csv"))

    # Pairwise correlations
    pairwise_corr = compute_pairwise_correlations(analytical_df, valid_numeric)
    pairwise_corr.to_csv(os.path.join(PROJECT_ROOT, "outputs", "reports", "pairwise_correlations.csv"), index=False)

    # PCA and Clustering
    pca_df, explained_var, loadings = run_pca(analytical_df, valid_numeric, n_components=2)
    cluster_labels, sil_score, centers = run_clustering(analytical_df, valid_numeric, n_clusters=3)

    # -------------------------------------------------------------------------
    # STAGE 7: VISUALIZATION GALLERY GENERATION (30 CHARTS)
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 7: COMPREHENSIVE VISUALIZATION GALLERY")
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "figures")
    os.makedirs(fig_dir, exist_ok=True)

    # 1. Histogram
    viz.plot_histogram(pm25_df, "value", city_col="city", title="1. Distribution of PM2.5 Concentrations", save_path=os.path.join(fig_dir, "01_pm25_histogram.png"))

    # 2. Histogram with KDE
    viz.plot_histogram_kde(pm25_df, "value", city_col="city", title="2. PM2.5 Kernel Density Estimation Overlay", save_path=os.path.join(fig_dir, "02_pm25_histogram_kde.png"))

    # 3. Box plot PM2.5
    viz.plot_boxplot(pm25_df, "value", group_col="city", title="3. PM2.5 Concentration Box Plot by City", save_path=os.path.join(fig_dir, "03_pm25_boxplot.png"))

    # 4. Violin plot
    viz.plot_violin(pm25_df, "value", group_col="city", title="4. PM2.5 Probability Density & Quartiles Violin Plot", save_path=os.path.join(fig_dir, "04_pm25_violin.png"))

    # 5. Density plot
    viz.plot_density(pm25_df, "value", group_col="city", title="5. Comparative Kernel Density Profiles", save_path=os.path.join(fig_dir, "05_pm25_density.png"))

    # 6. ECDF plot
    viz.plot_ecdf(pm25_df, "value", group_col="city", title="6. Empirical Cumulative Distribution Function (ECDF)", save_path=os.path.join(fig_dir, "06_pm25_ecdf.png"))

    # 7. Bar chart (Mean PM2.5)
    city_means = pm25_df.groupby("city")["value"].mean().reset_index()
    viz.plot_bar_chart(city_means, "city", "value", title="7. Mean Observed PM2.5 by City (µg/m³)", save_path=os.path.join(fig_dir, "07_mean_pm25_barchart.png"))

    # 8. Grouped bar chart (PM2.5 vs PM10)
    all_pm = analytical_df[analytical_df["parameter"].isin(["pm25", "pm10"])].groupby(["city", "parameter"])["value"].mean().reset_index()
    viz.plot_grouped_bar(all_pm, "city", "value", "parameter", title="8. Particulate Comparison: PM2.5 vs PM10", save_path=os.path.join(fig_dir, "08_pm_grouped_bar.png"))

    # 9. Horizontal bar chart (Temperature ranking)
    city_temps = analytical_df.groupby("city")["temperature_mean"].mean().reset_index()
    viz.plot_horizontal_bar(city_temps, "city", "temperature_mean", title="9. Mean Temperature Ranking across Urban Centers (°C)", save_path=os.path.join(fig_dir, "09_temperature_horizontal_bar.png"))

    # 10. Cleveland dot plot
    city_medians = pm25_df.groupby("city")["value"].median().reset_index()
    viz.plot_dot_plot(city_medians, "city", "value", title="10. Cleveland Dot Plot: Median PM2.5 Concentrations", save_path=os.path.join(fig_dir, "10_pm25_dot_plot.png"))

    # 11. Heatmap (Monthly Average per City)
    if "month" in pm25_df.columns:
        monthly_city_matrix = pm25_df.pivot_table(index="city", columns="month", values="value", aggfunc="mean")
        viz.plot_heatmap(monthly_city_matrix, title="11. Monthly Mean PM2.5 Heatmap (City × Month)", save_path=os.path.join(fig_dir, "11_monthly_city_heatmap.png"))

    # 12. Small multiples
    viz.plot_small_multiples(pm25_df, "value", group_col="city", title="12. Small Multiples: City-Specific PM2.5 Histograms", save_path=os.path.join(fig_dir, "12_small_multiples.png"))

    # 13. Scatter plot (Temp vs PM2.5)
    viz.plot_scatter(pm25_df, "temperature_mean", "value", hue="city", title="13. Bivariate Scatter: PM2.5 vs Temperature", save_path=os.path.join(fig_dir, "13_scatter_temp_pm25.png"))

    # 14. Scatter plot with regression line
    viz.plot_scatter_regression(pm25_df, "temperature_mean", "value", hue="city", title="14. Linear Regression Fit: PM2.5 vs Temperature", save_path=os.path.join(fig_dir, "14_regression_temp_pm25.png"))

    # 15. Pair plot
    viz.plot_pairplot(analytical_df, cols=["value", "temperature_mean", "wind_speed_mean"], hue="city", title="15. Joint Multi-Variable Pair Plot", save_path=os.path.join(fig_dir, "15_variables_pairplot.png"))

    # 16. Bubble chart
    viz.plot_bubble_chart(pm25_df, "wind_speed_mean", "value", size="humidity_mean", hue="city", title="16. Bubble Chart: PM2.5 vs Wind Speed (Bubble Size: Humidity)", save_path=os.path.join(fig_dir, "16_bubble_chart.png"))

    # 17. Correlation heatmap
    corr_matrix = analytical_df[valid_numeric].corr()
    viz.plot_correlation_heatmap(corr_matrix, title="17. Multi-Indicator Correlation Heatmap", save_path=os.path.join(fig_dir, "17_correlation_heatmap.png"))

    # 18. Time-series line chart
    viz.plot_timeseries(pm25_df, "date", "value", group_col="city", title="18. Daily PM2.5 Time Series Across Cities (2024)", save_path=os.path.join(fig_dir, "18_timeseries_pm25.png"))

    # 19. Multiple time-series comparison
    viz.plot_multi_timeseries(analytical_df, "date", ["value", "temperature_mean", "wind_speed_mean"], title="19. Synchronized Multi-Indicator Progression", save_path=os.path.join(fig_dir, "19_multi_timeseries.png"))

    # 20. Rolling-average chart
    viz.plot_rolling_average(pm25_df, "date", "value", windows=[7, 30], title="20. Daily Mean PM2.5 with 7-Day & 30-Day Moving Trends", save_path=os.path.join(fig_dir, "20_rolling_average.png"))

    # 21. Seasonal comparison
    if "month" in pm25_df.columns:
        viz.plot_seasonal_comparison(pm25_df, "month", "value", group_col="city", title="21. Seasonal Profile of PM2.5 by Month", save_path=os.path.join(fig_dir, "21_seasonal_comparison.png"))

    # 22. Calendar heatmap
    viz.plot_calendar_heatmap(pm25_df, "date", "value", year=2024, title="22. Calendar Heatmap: 2024 Daily PM2.5 Intensity", save_path=os.path.join(fig_dir, "22_calendar_heatmap.png"))

    # 23. City location map
    viz.plot_city_map(cities_cfg, title="23. Geographic Air Quality Monitoring Network", save_path=os.path.join(fig_dir, "23_city_map.png"))

    # 24. Interactive map (HTML)
    mean_pm_dict = dict(zip(city_means["city"], city_means["value"]))
    viz.plot_interactive_map(cities_cfg, values_dict=mean_pm_dict, title="24. Interactive Geographic Particulate Map", save_path=os.path.join(fig_dir, "24_city_map_interactive.html"))

    # 25. Geographic comparison
    viz.plot_geographic_comparison(city_means, indicator="value", title="25. Spatial Comparison of PM2.5 with Coordinates", save_path=os.path.join(fig_dir, "25_geographic_comparison.png"))

    # 26. PCA visualization
    fig_pca, ax_pca = plt.subplots(figsize=(10, 6))
    if not pca_df.empty and "city" in analytical_df.columns:
        pca_merged = pd.concat([pca_df, analytical_df[["city"]].loc[pca_df.index]], axis=1)
        for city in pca_merged["city"].unique():
            sub = pca_merged[pca_merged["city"] == city]
            color = CITY_COLORS.get(city, None)
            ax_pca.scatter(sub["PC1"], sub["PC2"], label=city, color=color, alpha=0.6, s=30)
        ax_pca.set_title(f"26. Principal Component Analysis (Explained Var: {explained_var.sum()*100:.1f}%)", fontweight="bold", fontsize=14)
        ax_pca.set_xlabel(f"PC1 ({explained_var[0]*100:.1f}%)")
        ax_pca.set_ylabel(f"PC2 ({explained_var[1]*100:.1f}%)")
        ax_pca.legend(frameon=True)
        plt.tight_layout()
        fig_pca.savefig(os.path.join(fig_dir, "26_pca_visualization.png"), dpi=150)
        plt.close(fig_pca)

    # 27. Cluster visualization
    fig_clust, ax_clust = plt.subplots(figsize=(10, 6))
    if len(cluster_labels) > 0 and not pca_df.empty:
        scatter = ax_clust.scatter(pca_df["PC1"], pca_df["PC2"], c=cluster_labels, cmap="Set1", alpha=0.6, s=30)
        ax_clust.set_title(f"27. Environmental Regimes: K-Means Clusters (Silhouette: {sil_score:.2f})", fontweight="bold", fontsize=14)
        ax_clust.set_xlabel("PC1")
        ax_clust.set_ylabel("PC2")
        plt.colorbar(scatter, ax=ax_clust, label="Cluster ID")
        plt.tight_layout()
        fig_clust.savefig(os.path.join(fig_dir, "27_cluster_visualization.png"), dpi=150)
        plt.close(fig_clust)

    # 28. Radar / Multi-Attribute Profile
    fig_radar, ax_radar = plt.subplots(figsize=(10, 6))
    norm_summary = city_means.copy()
    norm_summary["norm_pm"] = norm_summary["value"] / norm_summary["value"].max()
    ax_radar.bar(norm_summary["city"], norm_summary["norm_pm"], color=[CITY_COLORS.get(c) for c in norm_summary["city"]], alpha=0.8)
    ax_radar.set_title("28. Normalized Comparative Urban Environmental Stress Index", fontweight="bold", fontsize=14)
    ax_radar.set_ylabel("Normalized Score (0-1)")
    plt.tight_layout()
    fig_radar.savefig(os.path.join(fig_dir, "28_radar_profile.png"), dpi=150)
    plt.close(fig_radar)

    # 29. Distribution comparison across cities (Facet Grid)
    g_dist = sns.FacetGrid(pm25_df, col="city", hue="city", palette=CITY_COLORS, col_wrap=3, height=3.5, aspect=1.2)
    g_dist.map(sns.kdeplot, "value", fill=True, alpha=0.4)
    g_dist.set_axis_labels("PM2.5 (µg/m³)", "Density")
    g_dist.fig.suptitle("29. Faceted Kernel Density Comparison Across Urban Centers", y=1.03, fontweight="bold", fontsize=14)
    g_dist.savefig(os.path.join(fig_dir, "29_distribution_comparison.png"), dpi=150, bbox_inches="tight")
    plt.close(g_dist.fig)

    # 30. Executive Analytical Dashboard (PNG & HTML)
    viz.create_dashboard_overview(analytical_df, city_summaries, save_path=os.path.join(fig_dir, "30_dashboard_overview.png"))
    viz.create_plotly_dashboard(analytical_df, save_path=os.path.join(fig_dir, "30_dashboard_interactive.html"))

    logger.info("Generated 30 publication-quality charts in %s", fig_dir)

    # -------------------------------------------------------------------------
    # STAGE 8: INSIGHTS, RECOMMENDATIONS & EXECUTIVE REPORTS
    # -------------------------------------------------------------------------
    logger.info("\n>>> STAGE 8: SYNTHESIZING INSIGHTS & REPORTS")
    findings = generate_key_findings(
        stats_df=desc_stats,
        correlations_df=pairwise_corr,
        city_summaries_df=city_means,
        analytics_df=analytical_df,
    )
    recommendations = generate_recommendations(findings)

    summary_md = compile_analysis_summary(findings, recommendations)
    save_analysis_summary(summary_md, os.path.join(PROJECT_ROOT, "outputs", "reports", "analysis_summary.md"))

    elapsed = time.time() - start_time
    logger.info("\n================================================================================")
    logger.info(f"  PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    logger.info("================================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Global Urban Intelligence Pipeline Runner")
    parser.add_argument("--demo", action="store_true", default=True, help="Run with synthetic demo data (offline)")
    parser.add_argument("--live", action="store_true", help="Run with real live APIs")
    args = parser.parse_args()

    mode = "live" if args.live else "demo"
    main(mode=mode)
