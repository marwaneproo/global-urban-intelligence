"""
Temporal visualization module for Global Urban Intelligence.
"""

import logging
import os
from typing import List, Optional
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

CITY_COLORS = {
    "Casablanca": "#e74c3c",
    "Rabat": "#3498db",
    "Paris": "#2ecc71",
    "Madrid": "#f39c12",
    "Lisbon": "#9b59b6",
}


def _ensure_dir(path: Optional[str]) -> None:
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)


def plot_timeseries(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    group_col: Optional[str] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot multi-group time series trend lines."""
    fig, ax = plt.subplots(figsize=(14, 6))
    df_sorted = df.copy()
    df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
    df_sorted = df_sorted.sort_values(by=date_col)

    if group_col and group_col in df_sorted.columns:
        for group in df_sorted[group_col].unique():
            sub = df_sorted[df_sorted[group_col] == group]
            color = CITY_COLORS.get(group, None)
            ax.plot(sub[date_col], sub[value_col], label=group, color=color, alpha=0.8, linewidth=1.5)
        ax.legend(title=group_col.title(), frameon=True)
    else:
        ax.plot(df_sorted[date_col], df_sorted[value_col], color="#2980b9", linewidth=1.5)

    ax.set_title(title or f"Time Series of {value_col}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(value_col, fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved timeseries to {save_path}")
        plt.close(fig)
    return fig


def plot_multi_timeseries(
    df: pd.DataFrame,
    date_col: str,
    value_cols: List[str],
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot multiple normalized or dual-axis variables over time."""
    fig, ax = plt.subplots(figsize=(14, 6))
    df_sorted = df.copy()
    df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
    df_daily = df_sorted.groupby(date_col)[value_cols].mean().reset_index()

    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12"]
    for i, col in enumerate(value_cols):
        ax.plot(df_daily[date_col], df_daily[col], label=col, color=colors[i % len(colors)], linewidth=1.8)

    ax.set_title(title or "Multi-Indicator Temporal Progression", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Daily Average Value", fontsize=12)
    ax.legend(frameon=True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved multi-timeseries to {save_path}")
        plt.close(fig)
    return fig


def plot_rolling_average(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    windows: List[int] = [7, 30],
    group_col: Optional[str] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot daily values with 7-day and 30-day moving averages."""
    fig, ax = plt.subplots(figsize=(14, 6))
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col])

    # If aggregated across cities or single series
    daily_series = df_copy.groupby(date_col)[value_col].mean().sort_index()

    ax.scatter(daily_series.index, daily_series.values, color="lightgray", s=15, alpha=0.6, label="Daily Mean")

    line_styles = ["-", "--"]
    colors = ["#e74c3c", "#2980b9"]
    for i, w in enumerate(windows):
        rolling = daily_series.rolling(window=w, min_periods=max(1, w // 2)).mean()
        ax.plot(rolling.index, rolling.values, label=f"{w}-Day Rolling Average", color=colors[i % len(colors)], linestyle=line_styles[i % len(line_styles)], linewidth=2)

    ax.set_title(title or f"{value_col}: Daily Observations with Rolling Trends", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(value_col, fontsize=12)
    ax.legend(frameon=True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved rolling average to {save_path}")
        plt.close(fig)
    return fig


def plot_seasonal_comparison(
    df: pd.DataFrame,
    month_col: str,
    value_col: str,
    group_col: str = "city",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot seasonal monthly profiles across cities."""
    fig, ax = plt.subplots(figsize=(12, 6))

    if group_col in df.columns:
        monthly_avg = df.groupby([group_col, month_col])[value_col].mean().reset_index()
        for group in monthly_avg[group_col].unique():
            sub = monthly_avg[monthly_avg[group_col] == group]
            color = CITY_COLORS.get(group, None)
            ax.plot(sub[month_col], sub[value_col], marker="o", label=group, color=color, linewidth=2)
        ax.legend(title=group_col.title(), frameon=True)
    else:
        monthly_avg = df.groupby(month_col)[value_col].mean()
        ax.plot(monthly_avg.index, monthly_avg.values, marker="o", color="#2980b9", linewidth=2)

    ax.set_title(title or f"Monthly Seasonality of {value_col}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month of Year", fontsize=12)
    ax.set_ylabel(f"Mean {value_col}", fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved seasonal comparison to {save_path}")
        plt.close(fig)
    return fig


def plot_calendar_heatmap(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    year: int = 2024,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot calendar heatmap showing daily variations across the 52 weeks of the year."""
    fig, ax = plt.subplots(figsize=(16, 4))
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col])
    daily = df_copy.groupby(date_col)[value_col].mean().reset_index()

    # Filter to year
    daily = daily[daily[date_col].dt.year == year].copy()
    if daily.empty:
        daily = df_copy.groupby(date_col)[value_col].mean().reset_index()

    daily["week"] = daily[date_col].dt.isocalendar().week
    daily["day_of_week"] = daily[date_col].dt.dayofweek  # 0=Mon, 6=Sun

    pivot = daily.pivot_table(index="day_of_week", columns="week", values=value_col, aggfunc="mean")

    sns.heatmap(pivot, cmap="YlOrRd", ax=ax, cbar_kws={"label": value_col, "shrink": 0.8}, linewidths=0.5, linecolor="white")

    ax.set_title(title or f"Calendar Heatmap: Daily {value_col} ({year})", fontsize=14, fontweight="bold")
    ax.set_xlabel("ISO Week Number", fontsize=12)
    ax.set_ylabel("Day of Week", fontsize=12)
    ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], rotation=0)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved calendar heatmap to {save_path}")
        plt.close(fig)
    return fig
