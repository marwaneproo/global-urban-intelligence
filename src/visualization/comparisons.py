"""
Comparison visualization module for Global Urban Intelligence.
"""

import logging
import os
from typing import Optional
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


def plot_bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot standard vertical bar chart with value annotations."""
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [CITY_COLORS.get(val, "#34495e") for val in data[x]]

    bars = ax.bar(data[x], data[y], color=colors, edgecolor="black", alpha=0.85)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    ax.set_title(title or f"Comparison of {y} across {x}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x.title(), fontsize=12)
    ax.set_ylabel(y.title(), fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved bar chart to {save_path}")
        plt.close(fig)
    return fig


def plot_grouped_bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: str,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot grouped bar chart comparing multiple series per category."""
    fig, ax = plt.subplots(figsize=(12, 6))

    sns.barplot(data=data, x=x, y=y, hue=hue, ax=ax, palette="deep")

    ax.set_title(title or f"Grouped Comparison: {y} by {x} and {hue}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x.title(), fontsize=12)
    ax.set_ylabel(y.title(), fontsize=12)
    ax.legend(title=hue.title(), frameon=True)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved grouped bar to {save_path}")
        plt.close(fig)
    return fig


def plot_horizontal_bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot horizontal bar chart, ideal for ranking categories."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sorted_df = data.sort_values(by=y, ascending=True)

    colors = [CITY_COLORS.get(val, "#34495e") for val in sorted_df[x]]
    bars = ax.barh(sorted_df[x], sorted_df[y], color=colors, edgecolor="black", alpha=0.85)

    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            f"{width:.1f}",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(6, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontweight="bold",
        )

    ax.set_title(title or f"Ranked {y} across {x}", fontsize=14, fontweight="bold")
    ax.set_xlabel(y.title(), fontsize=12)
    ax.set_ylabel(x.title(), fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved horizontal bar to {save_path}")
        plt.close(fig)
    return fig


def plot_dot_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot Cleveland dot plot for clean, low-ink comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sorted_df = data.sort_values(by=y, ascending=True)

    ax.hlines(y=sorted_df[x], xmin=0, xmax=sorted_df[y], color="gray", alpha=0.5, linewidth=1.5)
    colors = [CITY_COLORS.get(val, "#e74c3c") for val in sorted_df[x]]
    ax.scatter(sorted_df[y], sorted_df[x], color=colors, s=120, zorder=3, edgecolor="black")

    for i, (_, row) in enumerate(sorted_df.iterrows()):
        ax.annotate(f" {row[y]:.1f}", (row[y], i), va="center", fontsize=10, fontweight="bold")

    ax.set_title(title or f"Cleveland Dot Plot: {y} by {x}", fontsize=14, fontweight="bold")
    ax.set_xlabel(y.title(), fontsize=12)
    ax.set_ylabel(x.title(), fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved dot plot to {save_path}")
        plt.close(fig)
    return fig


def plot_heatmap(
    data: pd.DataFrame,
    title: Optional[str] = None,
    annot: bool = True,
    save_path: Optional[str] = None,
    cmap: str = "YlOrRd",
) -> plt.Figure:
    """Plot 2D matrix heatmap with value annotations."""
    fig, ax = plt.subplots(figsize=(10, 6))

    sns.heatmap(data, annot=annot, fmt=".1f" if annot else "", cmap=cmap, ax=ax, cbar_kws={"label": "Magnitude"})
    ax.set_title(title or "Comparative Matrix Heatmap", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved heatmap to {save_path}")
        plt.close(fig)
    return fig


def plot_small_multiples(
    df: pd.DataFrame,
    col: str,
    group_col: str = "city",
    plot_type: str = "hist",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot small multiples grid across categorical groups."""
    groups = df[group_col].unique()
    n_groups = len(groups)
    cols_grid = min(3, n_groups)
    rows_grid = (n_groups + cols_grid - 1) // cols_grid

    fig, axes = plt.subplots(rows_grid, cols_grid, figsize=(5 * cols_grid, 4 * rows_grid), squeeze=False)
    axes_flat = axes.flatten()

    for i, group in enumerate(groups):
        ax = axes_flat[i]
        sub = df[df[group_col] == group][col].dropna()
        color = CITY_COLORS.get(group, "#34495e")

        if plot_type == "hist":
            ax.hist(sub, bins=25, color=color, alpha=0.7, edgecolor="white")
        else:
            sns.kdeplot(sub, ax=ax, color=color, fill=True)

        ax.set_title(f"{group}", fontweight="bold")
        ax.set_xlabel(col)

    # Turn off unused subplots
    for j in range(n_groups, len(axes_flat)):
        axes_flat[j].axis("off")

    fig.suptitle(title or f"Small Multiples: {col} Across {group_col.title()}", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved small multiples to {save_path}")
        plt.close(fig)
    return fig
