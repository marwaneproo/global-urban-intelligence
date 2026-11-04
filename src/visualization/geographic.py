"""
Geographic visualization module for Global Urban Intelligence.
"""

import logging
import os
from typing import Any, Dict, Optional
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)

CITY_COORDINATES = {
    "Casablanca": (33.5731, -7.5898),
    "Rabat": (34.0209, -6.8416),
    "Paris": (48.8566, 2.3522),
    "Madrid": (40.4168, -3.7038),
    "Lisbon": (38.7223, -9.1393),
}

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


def plot_city_map(
    cities_config: Dict[str, Any],
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot static spatial map of target cities across Western Europe & North Africa."""
    fig, ax = plt.subplots(figsize=(10, 8))

    cities = cities_config.get("cities", [])
    if not cities:
        # Fallback to predefined
        cities = [{"name": k, "latitude": v[0], "longitude": v[1]} for k, v in CITY_COORDINATES.items()]

    lons = [c["longitude"] for c in cities]
    lats = [c["latitude"] for c in cities]
    names = [c["name"] for c in cities]

    # Geographic boundary box
    ax.set_xlim(-15, 10)
    ax.set_ylim(28, 55)

    # Simple background grid representation
    ax.axhline(0, color="lightgray", linestyle="--")
    ax.axvline(0, color="lightgray", linestyle="--")

    for c in cities:
        name = c["name"]
        color = CITY_COLORS.get(name, "#2c3e50")
        ax.scatter(c["longitude"], c["latitude"], color=color, s=200, edgecolors="black", linewidth=1.5, zorder=5)
        ax.annotate(
            f"  {name}",
            (c["longitude"], c["latitude"]),
            fontsize=12,
            fontweight="bold",
            va="center",
            ha="left",
            zorder=6,
        )

    ax.set_title(title or "Geographic Monitoring Network — Target Urban Centers", fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude (°E)", fontsize=12)
    ax.set_ylabel("Latitude (°N)", fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved city map to {save_path}")
        plt.close(fig)
    return fig


def plot_interactive_map(
    cities_config: Dict[str, Any],
    values_dict: Optional[Dict[str, float]] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> None:
    """Generate an interactive HTML geographic visualization using Plotly."""
    try:
        import plotly.graph_objects as go

        cities = cities_config.get("cities", [])
        if not cities:
            cities = [{"name": k, "latitude": v[0], "longitude": v[1]} for k, v in CITY_COORDINATES.items()]

        names = [c["name"] for c in cities]
        lats = [c["latitude"] for c in cities]
        lons = [c["longitude"] for c in cities]

        if values_dict:
            vals = [values_dict.get(n, 20.0) for n in names]
            sizes = [max(15, min(v * 1.5, 60)) for v in vals]
            text = [f"<b>{n}</b><br>Observed Level: {v:.1f} µg/m³" for n, v in zip(names, vals)]
        else:
            vals = [30] * len(names)
            sizes = [20] * len(names)
            text = [f"<b>{n}</b>" for n in names]

        fig = go.Figure(
            data=go.Scattergeo(
                lon=lons,
                lat=lats,
                text=text,
                mode="markers+text",
                textposition="top center",
                marker=dict(
                    size=sizes,
                    color=vals,
                    colorscale="Viridis",
                    showscale=True,
                    colorbar_title="µg/m³",
                    line_color="black",
                    line_width=1.5,
                ),
            )
        )

        fig.update_layout(
            title_text=title or "Global Urban Intelligence — Geographic Air Quality Network",
            geo=dict(
                scope="europe",
                resolution=50,
                showland=True,
                landcolor="rgb(243, 243, 243)",
                countrycolor="rgb(204, 204, 204)",
                lataxis=dict(range=[28, 55]),
                lonaxis=dict(range=[-15, 10]),
            ),
            margin=dict(l=0, r=0, t=50, b=0),
        )

        if save_path:
            _ensure_dir(save_path)
            fig.write_html(save_path)
            logger.info(f"Saved interactive map HTML to {save_path}")
    except Exception as e:
        logger.warning(f"Could not render interactive map: {e}")


def plot_geographic_comparison(
    city_summaries: pd.DataFrame,
    indicator: str = "mean",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot horizontal comparative bar with geographic coordinates annotated."""
    fig, ax = plt.subplots(figsize=(10, 6))

    sorted_df = city_summaries.sort_values(by=indicator, ascending=True)
    colors = [CITY_COLORS.get(c, "#34495e") for c in sorted_df["city"]]

    bars = ax.barh(sorted_df["city"], sorted_df[indicator], color=colors, edgecolor="black", alpha=0.85)

    for bar, city in zip(bars, sorted_df["city"]):
        coords = CITY_COORDINATES.get(city, (0, 0))
        w = bar.get_width()
        ax.annotate(
            f" {w:.1f} µg/m³ ({coords[0]:.1f}°N, {abs(coords[1]):.1f}°W)",
            xy=(w, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontweight="bold",
        )

    ax.set_title(title or f"Geographic Comparison of {indicator.title()} Particulate Levels", fontsize=14, fontweight="bold")
    ax.set_xlabel(f"{indicator.title()} Concentration (µg/m³)", fontsize=12)
    ax.set_ylabel("City", fontsize=12)
    plt.tight_layout()

    if save_path:
        _ensure_dir(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved geographic comparison to {save_path}")
        plt.close(fig)
    return fig
