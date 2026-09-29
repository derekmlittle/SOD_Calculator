"""
Calculation service.

Contains regression, blank adjustment, site summary, and export dataframe logic.
"""

from __future__ import annotations

from typing import List, Dict, Optional

import numpy as np
import pandas as pd
from scipy.stats import linregress

from models.file_record import ChamberResult, FileRecord
from services.dataframe_service import prepare_dataframe


def compute_regression_on_window(df: pd.DataFrame, time_col: str, value_col: str):
    """
    Run a linear regression on the selected time window.

    Returns:
        slope, intercept, r_squared, regression_dataframe
    """
    d = df.dropna(subset=[time_col, value_col]).copy().sort_values(time_col)

    if len(d) < 2:
        raise ValueError("Need at least 2 valid numeric points in the selected window.")

    x = (d[time_col] - d[time_col].iloc[0]).dt.total_seconds() / 60.0
    y = pd.to_numeric(d[value_col], errors="coerce")

    mask = np.isfinite(x) & np.isfinite(y)
    d = d.loc[mask].copy()
    x = x[mask]
    y = y[mask]

    if len(d) < 2:
        raise ValueError("Need at least 2 valid numeric points in the selected window.")

    fit = linregress(x, y)
    d["_minutes"] = x
    d["_predicted"] = fit.intercept + fit.slope * x

    return float(fit.slope), float(fit.intercept), float(fit.rvalue ** 2), d


def compute_chamber_result(
    record: FileRecord,
    start_dt=None,
    end_dt=None,
) -> ChamberResult:
    """
    Compute one chamber result from the imported record and selected time window.
    """
    df = prepare_dataframe(record.dataframe, record.column_mapping)
    odo_col = "ODO MG/L"
    temp_col = "TEMP C"

    if odo_col not in df.columns:
        raise ValueError(f"Missing ODO MG/L for {record.file_name}")

    # Build a dataframe representing the selected time window only
    window_df = df.dropna(subset=["_datetime"]).copy().sort_values("_datetime")

    if start_dt is not None:
        window_df = window_df[window_df["_datetime"] >= start_dt]
    if end_dt is not None:
        window_df = window_df[window_df["_datetime"] <= end_dt]

    if window_df.empty:
        raise ValueError(f"No data points in selected window for {record.file_name}")

    # Regression should use only valid ODO points inside the selected window
    regression_df = window_df.dropna(subset=[odo_col]).copy()

    if len(regression_df) < 2:
        raise ValueError(f"Not enough points in selected window for {record.file_name}")

    slope, intercept, r2, reg_df = compute_regression_on_window(
        regression_df, "_datetime", odo_col
    )

    # Mean temperature should use only temperatures from the selected time window
    if temp_col in window_df.columns:
        mean_temp = pd.to_numeric(window_df[temp_col], errors="coerce").mean()
    else:
        mean_temp = np.nan

    start_time = regression_df["_datetime"].iloc[0]
    end_time = regression_df["_datetime"].iloc[-1]
    selected_minutes = (end_time - start_time).total_seconds() / 60.0

    return ChamberResult(
        record=record,
        start_time=start_time,
        end_time=end_time,
        n_points=len(regression_df),
        slope=slope,
        intercept=intercept,
        r2=r2,
        unadjusted_do_rate=slope,
        mean_temp=mean_temp,
        regression_df=reg_df,
        selected_minutes=selected_minutes,
    )


def apply_blank_adjustment_and_convert(
    results: List[ChamberResult],
    theta: float = 1.065,
    v_over_a: float = 240.0,
) -> float:
    """
    Apply blank correction and compute adjusted rates and SOD values.
    """
    blank_slopes = [
        r.unadjusted_do_rate
        for r in results
        if (r.record.chamber_type or "").strip().lower() == "blank chamber"
        and pd.notna(r.unadjusted_do_rate)
    ]
    blank_mean = float(np.mean(blank_slopes)) if blank_slopes else 0.0

    for r in results:
        ctype = (r.record.chamber_type or "").strip().lower()

        if ctype == "ambient":
            r.adjusted_do_rate = np.nan
            #r.temp_corrected_rate = np.nan
            r.sod_g_m2_day = np.nan
            continue

        if ctype == "blank chamber":
            r.adjusted_do_rate = r.unadjusted_do_rate
            #r.temp_corrected_rate = r.unadjusted_do_rate 
            r.sod_g_m2_day = np.nan
            continue

        if ctype == "contact chamber":
            r.adjusted_do_rate = r.unadjusted_do_rate - blank_mean
            #r.temp_corrected_rate = r.adjusted_do_rate * theta #THIS IS INCORRECT
            r.sod_g_m2_day = r.adjusted_do_rate * v_over_a*1.44

    return blank_mean


def summarize_site(results: List[ChamberResult], theta: float = 1.065) -> Dict[str, float]:
    contact = [
        r for r in results
        if (r.record.chamber_type or "").strip().lower() == "contact chamber"
    ]

    mean_sod = float(np.nanmean([r.sod_g_m2_day for r in contact])) if contact else np.nan
    average_temp = float(np.nanmean([r.mean_temp for r in contact])) if contact else np.nan

    if contact and pd.notna(mean_sod) and pd.notna(average_temp):
        corrected_to_20 = mean_sod / (theta ** (average_temp - 20))
    else:
        corrected_to_20 = np.nan

    return {
        "mean_sod_g_m2_day": mean_sod,
        "average_temp_c": average_temp,
        "mean_sod_20c_g_m2_day": corrected_to_20,
        "mean_r2": float(np.nanmean([r.r2 for r in results])) if results else np.nan,
    }


def results_to_dataframe(
    results,
    project_number,
    project_name,
    blank_mean,
    site_summary,
    theta,
    v_over_a,
):
    """
    Convert computed results to a flat dataframe for CSV export.
    """
    rows = []

    for r in results:
        rows.append(
            {
                "Project Number": project_number,
                "Project Name": project_name,
                "File Name": r.record.file_name,
                "Site Name": r.record.site_name,
                "Chamber Type": r.record.chamber_type,
                "Chamber ID": r.record.chamber_id,
                "N Points": r.n_points,
                "Slope": r.slope,
                "Intercept": r.intercept,
                "R2": r.r2,
                "Unadjusted DO Rate": r.unadjusted_do_rate,
                "Adjusted DO Rate": r.adjusted_do_rate,
                "SOD g/m2/day": r.sod_g_m2_day,
                "Blank Mean Slope": blank_mean,
                "Mean Site SOD g/m2/day": site_summary.get("mean_sod_g_m2_day", np.nan), 
                "Mean Site SOD 20C g/m2/day": site_summary.get("mean_sod_20c_g_m2_day", np.nan),               
                "Mean Site R2": site_summary.get("mean_r2", np.nan),
                "Theta": theta,
                "V/A": v_over_a,
            }
        )

    return pd.DataFrame(rows)