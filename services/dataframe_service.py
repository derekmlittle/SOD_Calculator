"""
DataFrame preparation helpers.

Builds a normalized dataframe with a _datetime column.
"""

from __future__ import annotations

import pandas as pd

NUMERIC_COLUMNS = ["ODO MG/L", "TEMP C", "ODO % SAT", "TURBIDITY FNU"]


def _find_column(df: pd.DataFrame, word: str, startswith: bool = False):
    word = word.lower().strip()
    for col in df.columns:
        name = str(col).strip().lower()
        if (name.startswith(word) if startswith else word in name):
            return col
    return None


def _resolve_time_or_date_column(df: pd.DataFrame, column_mapping: dict, key_word: str):
    key_word = key_word.lower().strip()

    for target, src in column_mapping.items():
        if src and src in df.columns and key_word in str(target).lower():
            return src

    return _find_column(df, key_word, startswith=True) or _find_column(df, key_word)


def prepare_dataframe(raw_df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
    """
    Return a normalized dataframe with:
    - mapped column names
    - numeric conversion for known measurement columns
    - a _datetime column for later filtering/plotting
    """
    if raw_df is None or raw_df.empty:
        return pd.DataFrame()

    df = raw_df.copy()

    rename_map = {
        src: target
        for target, src in column_mapping.items()
        if src and src in df.columns
    }
    if rename_map:
        df = df.rename(columns=rename_map)

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    time_col = _resolve_time_or_date_column(df, column_mapping, "time")
    date_col = _resolve_time_or_date_column(df, column_mapping, "date")

    if time_col and date_col and time_col == date_col:
        df["_datetime"] = pd.to_datetime(df[time_col], errors="coerce")

    elif time_col and date_col:
        df["_datetime"] = pd.to_datetime(
            df[date_col].astype(str).str.strip() + " " + df[time_col].astype(str).str.strip(),
            errors="coerce",
        )

    else:
        datetime_col = next(
            (
                col
                for col in df.columns
                if any(
                    key in str(col).strip().lower()
                    for key in ("datetime", "timestamp")
                )
                or ("date" in str(col).lower() and "time" in str(col).lower())
            ),
            None,
        )

        df["_datetime"] = (
            pd.to_datetime(df[datetime_col], errors="coerce")
            if datetime_col
            else pd.NaT
        )

    return df