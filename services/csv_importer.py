"""
CSV import service.

Reads CSV-like files using a list of fallback encodings and basic delimiter detection.
"""

from __future__ import annotations

import csv
from typing import Tuple

import pandas as pd

from config import ENCODINGS


def detect_delimiter(sample_text: str) -> str:
    """
    Detect a delimiter from sample text.
    Falls back to comma if detection fails.
    """
    try:
        return csv.Sniffer().sniff(sample_text, delimiters=",\t;|").delimiter
    except csv.Error:
        return ","


def read_csv_with_fallback(path: str, skiprows: int = 0) -> Tuple[pd.DataFrame, str, str]:
    """
    Read a CSV using fallback encodings.

    Returns:
        (dataframe, encoding_used, delimiter_used)
    """
    last_error = None

    for encoding in ENCODINGS:
        try:
            with open(path, "r", encoding=encoding, errors="replace") as f:
                sample = f.read(4096)

            sep = detect_delimiter(sample)
            df = pd.read_csv(path, encoding=encoding, sep=sep, skiprows=skiprows)
            return df, encoding, sep
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"Could not read file {path}: {last_error}")