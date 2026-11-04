"""
Distribution visualization module for Global Urban Intelligence.
"""

import logging
import os
from typing import Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

# Default project styling
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except Exception:
    plt.style.use("ggplot")

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


def plot_histogram(
    df: pd.DataFrame,
    col: str,
    city_col: str = "city",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    bins: int = 30,
) -> plt.Figure:
    """Plot histogram of values per city using faceted subplots."""
    cities = df[city_col].unique() if city_col in df.columns else ["All"]
    n_cities = len(cities)
    fig, axes = plt.subplots(1, n_cities, figsize=(4 * n_cities, 4), sharey=True)
    if n_cities == 1:
        axes = [axes]

    for ax, city in zip(axes, cities):
        subset = df[df[city_col] == city][col].dropna() if city_col in df.columns else df[col].dropna()
        color = CITY_COLORS.get(city, "#34495e")
        ax.hist(subset, bins=bins, color=color, alpha=0.75, edgecolor="white")
        ax.set_title(f"{city}", fontsize=12, fontweight="bold")
        ax.set_xlabel(f"{col}")
        if ax == axes[0]:
            ax.set_ylabel("Frequency")

    fig.suptitle(title or f"Distribution of {col} Across Cities", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved histogram to {save_path}")
        plt.close(fig)
    return fig


def plot_histogram_kde(
    df: pd.DataFrame,
    col: str,
    city_col: str = "city",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot combined Histogram and KDE overlay for each city."""
    fig, ax = plt.subplots(figsize=(10, 6))

    if city_col in df.columns:
        for city, color in CITY_COLORS.items():
            sub = df[df[city_col] == city][col].dropna()
            if not sub.empty:
                sns.histplot(sub, kde=True, ax=ax, label=city, color=color, stat="density", alpha=0.3, element="step")
    else:
        sns.histplot(df[col].dropna(), kde=True, ax=ax, color="#2980b9", stat="density", alpha=0.5)

    ax.set_title(title or f"Density Distribution & KDE of {col}", fontsize=14, fontweight="bold")
    ax.set_xlabel(col, fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.legend(title="City", frameon=True)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved histogram KDE to {save_path}")
        plt.close(fig)
    return fig


def plot_boxplot(
    df: pd.DataFrame,
    col: str,
    group_col: str = "city",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot box plot comparing distribution across groups with outliers highlighted."""
    fig, ax = plt.subplots(figsize=(10, 6))
    palette = [CITY_COLORS.get(c, "#7f8c8d") for c in df[group_col].unique()] if group_col in df.columns else None

    sns.boxplot(data=df, x=group_col, y=col, ax=ax, palette=palette, flierprops=dict(marker="o", markersize=4, alpha=0.5))
    ax.set_title(title or f"Box Plot of {col} by {group_col.title()}", fontsize=14, fontweight="bold")
    ax.set_xlabel(group_col.title(), fontsize=12)
    ax.set_ylabel(col, fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved box plot to {save_path}")
        plt.close(fig)
    return fig


def plot_violin(
    df: pd.DataFrame,
    col: str,
    group_col: str = "city",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot violin plot demonstrating probability density and quartiles."""
    fig, ax = plt.subplots(figsize=(10, 6))
    palette = [CITY_COLORS.get(c, "#7f8c8d") for c in df[group_col].unique()] if group_col in df.columns else None

    sns.violinplot(data=df, x=group_col, y=col, ax=ax, palette=palette, inner="quartile", cut=0)
    ax.set_title(title or f"Violin Plot of {col} by {group_col.title()}", fontsize=14, fontweight="bold")
    ax.set_xlabel(group_col.title(), fontsize=12)
    ax.set_ylabel(col, fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved violin plot to {save_path}")
        plt.close(fig)
    return fig


def plot_density(
    df: pd.DataFrame,
    col: str,
    group_col: str = "city",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot kernel density estimates comparing across groups."""
    fig, ax = plt.subplots(figsize=(10, 6))
    if group_col in df.columns:
        for val, color in CITY_COLORS.items():
            sub = df[df[group_col] == val][col].dropna()
            if not sub.empty:
                sns.kdeplot(sub, ax=ax, label=val, color=color, linewidth=2, fill=True, alpha=0.15)
    else:
        sns.kdeplot(df[col].dropna(), ax=ax, color="#2980b9", linewidth=2, fill=True, alpha=0.2)

    ax.set_title(title or f"Density Curves for {col}", fontsize=14, fontweight="bold")
    ax.set_xlabel(col, fontsize=12)
    ax.set_ylabel("Kernel Density", fontsize=12)
    ax.legend(title=group_col.title(), frameon=True)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved density plot to {save_path}")
        plt.close(fig)
    return fig


def plot_ecdf(
    df: pd.DataFrame,
    col: str,
    group_col: str = "city",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot Empirical Cumulative Distribution Function (ECDF)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    if group_col in df.columns:
        for val in df[group_col].unique():
            sub = df[df[group_col] == val][col].dropna().sort_values()
            if not sub.empty:
                y = np.linspace(0, 1, len(sub))
                color = CITY_COLORS.get(val, None)
                ax.plot(sub, y, label=val, color=color, linewidth=2)
    else:
        sub = df[col].dropna().sort_values()
        y = np.linspace(0, 1, len(sub))
        ax.plot(sub, y, label=col, color="#2980b9", linewidth=2)

    ax.set_title(title or f"Empirical Cumulative Distribution Function (ECDF) — {col}", fontsize=14, fontweight="bold")
    ax.set_xlabel(col, fontsize=12)
    ax.set_ylabel("Cumulative Probability P(X <= x)", fontsize=12)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.6, label="Median (P=0.50)")
    ax.legend(frameon=True)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved ECDF to {save_path}")
        plt.close(fig)
    return fig
