"""
Correlation and relationship visualization module for Global Urban Intelligence.
"""

import logging
import os
from typing import List, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
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


def plot_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot Pearson/Spearman correlation heatmap with diverging palette and mask."""
    fig, ax = plt.subplots(figsize=(10, 8))

    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    cmap = sns.diverging_palette(230, 20, as_cmap=True)

    sns.heatmap(
        corr_matrix,
        mask=mask,
        cmap=cmap,
        vmax=1.0,
        vmin=-1.0,
        center=0,
        square=True,
        linewidths=0.5,
        annot=True,
        fmt=".2f",
        cbar_kws={"shrink": 0.8, "label": "Correlation Coefficient (r)"},
        ax=ax,
    )

    ax.set_title(title or "Cross-Indicator Correlation Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved correlation heatmap to {save_path}")
        plt.close(fig)
    return fig


def plot_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot bivariate scatter plot with city color mapping."""
    fig, ax = plt.subplots(figsize=(10, 6))

    if hue and hue in df.columns:
        for group in df[hue].unique():
            sub = df[df[hue] == group]
            color = CITY_COLORS.get(group, None)
            ax.scatter(sub[x], sub[y], label=group, color=color, alpha=0.6, edgecolors="none", s=35)
        ax.legend(title=hue.title(), frameon=True)
    else:
        ax.scatter(df[x], df[y], color="#2980b9", alpha=0.6, edgecolors="none", s=35)

    ax.set_title(title or f"Relationship: {y} vs {x}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x, fontsize=12)
    ax.set_ylabel(y, fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved scatter to {save_path}")
        plt.close(fig)
    return fig


def plot_scatter_regression(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot scatter with linear OLS regression fit line and R² annotation."""
    fig, ax = plt.subplots(figsize=(10, 6))

    clean = df[[x, y]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(clean[x], clean[y])

    if hue and hue in df.columns:
        for group in df[hue].unique():
            sub = df[df[hue] == group]
            color = CITY_COLORS.get(group, None)
            ax.scatter(sub[x], sub[y], label=group, color=color, alpha=0.5, s=30)
        ax.legend(title=hue.title(), frameon=True)
    else:
        ax.scatter(clean[x], clean[y], color="#34495e", alpha=0.4, s=30)

    x_vals = np.linspace(clean[x].min(), clean[x].max(), 100)
    y_vals = slope * x_vals + intercept
    ax.plot(x_vals, y_vals, color="#e74c3c", linewidth=2.5, label=f"OLS: y={slope:.2f}x+{intercept:.1f}")

    r2_text = f"R² = {r_value**2:.3f}\nr = {r_value:.3f}\np = {p_value:.3e}"
    ax.annotate(
        r2_text,
        xy=(0.05, 0.92),
        xycoords="axes fraction",
        fontsize=11,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.9),
    )

    ax.set_title(title or f"Linear Fit: {y} vs {x}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x, fontsize=12)
    ax.set_ylabel(y, fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved scatter regression to {save_path}")
        plt.close(fig)
    return fig


def plot_pairplot(
    df: pd.DataFrame,
    cols: List[str],
    hue: Optional[str] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Optional[plt.Figure]:
    """Plot pairwise joint relationships and univariate marginal distributions."""
    sub_df = df[cols + ([hue] if hue and hue in df.columns else [])].dropna()
    palette = CITY_COLORS if hue == "city" else None

    g = sns.pairplot(
        sub_df,
        vars=cols,
        hue=hue,
        palette=palette,
        diag_kind="kde",
        plot_kws={"alpha": 0.6, "s": 25},
        corner=False,
    )

    if title:
        g.fig.suptitle(title, y=1.02, fontsize=14, fontweight="bold")

    if save_path:
        _ensure_dir(save_path)
        g.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved pairplot to {save_path}")
        plt.close(g.fig)
    return g.fig


def plot_bubble_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: str,
    hue: Optional[str] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot 3D multivariate relationship via 2D bubble chart with size dimension."""
    fig, ax = plt.subplots(figsize=(10, 6))

    clean = df.dropna(subset=[x, y, size])
    # Normalize size for display
    size_norm = ((clean[size] - clean[size].min()) / max(clean[size].max() - clean[size].min(), 1e-4) * 300) + 30

    if hue and hue in clean.columns:
        for group in clean[hue].unique():
            idx = clean[hue] == group
            color = CITY_COLORS.get(group, None)
            ax.scatter(
                clean.loc[idx, x],
                clean.loc[idx, y],
                s=size_norm[idx],
                label=group,
                color=color,
                alpha=0.6,
                edgecolors="black",
                linewidth=0.5,
            )
        ax.legend(title=hue.title(), frameon=True)
    else:
        ax.scatter(clean[x], clean[y], s=size_norm, color="#2980b9", alpha=0.6, edgecolors="black", linewidth=0.5)

    ax.set_title(title or f"Bubble Chart: {y} vs {x} (Size: {size})", fontsize=14, fontweight="bold")
    ax.set_xlabel(x, fontsize=12)
    ax.set_ylabel(y, fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved bubble chart to {save_path}")
        plt.close(fig)
    return fig
