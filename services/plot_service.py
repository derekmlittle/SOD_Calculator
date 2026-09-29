"""
Plotting service.

This generates the regression plot for display and export.
"""

from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from services.dataframe_service import prepare_dataframe


def plot_site_results(
    results: List[object],
    project_number: str,
    project_name: str,
    site_summary: Optional[Dict] = None,
    blank_mean: float = np.nan,
):
    fig, ax = plt.subplots(figsize=(11, 7))

    # Base styles by chamber type
    type_colors = {
        "contact chamber": "#1f77b4",
        "blank chamber": "#ff7f0e",
        "ambient": "#2ca02c",
        "other": "#666666",
    }

    # Marker cycle by chamber ID
    chamber_markers = ["o", "s", "^", "D", "v", "P", "X", "*", "<", ">"]

    # Consistent per-chamber-id styling
    chamber_style_map = {}
    style_idx = 0

    for r in results:
        df = getattr(r.record, "dataframe", None)
        if df is None or df.empty:
            continue

        work = prepare_dataframe(df, r.record.column_mapping)
        if "_datetime" not in work.columns:
            continue

        odo_col = "ODO MG/L"
        if odo_col not in work.columns:
            continue

        d = work.dropna(subset=["_datetime", odo_col]).copy()
        d = d.sort_values("_datetime")

        if r.start_time is not None:
            d = d[d["_datetime"] >= r.start_time]
        if r.end_time is not None:
            d = d[d["_datetime"] <= r.end_time]

        if len(d) < 2:
            continue

        t0 = r.start_time if r.start_time is not None else d["_datetime"].iloc[0]
        x = (d["_datetime"] - t0).dt.total_seconds() / 60.0
        y = pd.to_numeric(d[odo_col], errors="coerce")

        mask = np.isfinite(x) & np.isfinite(y)
        x = x[mask]
        y = y[mask]

        if len(x) < 2:
            continue

        ctype = (r.record.chamber_type or "").strip().lower()
        chamber_id = (r.record.chamber_id or "").strip() or "UNKNOWN"

        if chamber_id not in chamber_style_map:
            marker = chamber_markers[style_idx % len(chamber_markers)]
            # Slightly vary shade by chamber ID while keeping type color family
            base_color = type_colors.get(ctype, type_colors["other"])
            chamber_style_map[chamber_id] = {
                "color": base_color,
                "marker": marker,
            }
            style_idx += 1

        style = chamber_style_map[chamber_id]
        color = style["color"]
        marker = style["marker"]

        # Scatter points for the selected regression window
        ax.scatter(
            x, y,
            s=28,
            alpha=0.80,
            color=color,
            marker=marker,
            edgecolors="black",
            linewidths=0.3,
            label=f"ID {chamber_id} | Slope={r.slope:.6f} | R²={r.r2:.3f}"
        )

        xx = np.linspace(np.min(x), np.max(x), 100)
        yy = r.intercept + r.slope * xx
        ax.plot(xx, yy, linewidth=1.5, color=color)

    ax.set_title(f"Raw SOD Regression Plot - Project {project_number} {project_name}".strip())
    ax.set_xlabel("Minutes from selected start")
    ax.set_ylabel("ODO MG/L")
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.legend(fontsize=8, loc="best")

    summary_lines = []
    if not np.isnan(blank_mean):
        summary_lines.append(f"Blank mean slope: {blank_mean:.6f} mg/L/min")
    if site_summary:
        summary_lines.append(f"Mean SOD: {site_summary.get('mean_sod_g_m2_day', np.nan):.6f} g/m²/day")
        summary_lines.append(f"Mean R²: {site_summary.get('mean_r2', np.nan):.6f}")

    if summary_lines:
        fig.text(
            0.01,
            0.01,
            "\n".join(summary_lines),
            ha="left",
            va="bottom",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.88),
        )

    fig.tight_layout(rect=[0, 0.08, 1, 1])
    return fig