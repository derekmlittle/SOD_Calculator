"""
Date helpers.
"""

from typing import Optional
import pandas as pd


def parse_time_text(text: str) -> Optional[pd.Timestamp]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        dt = pd.to_datetime(text, errors="coerce")
        return None if pd.isna(dt) else dt
    except Exception:
        return None