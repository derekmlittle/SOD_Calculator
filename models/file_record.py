"""
Data models.

These are plain containers for imported files and calculated results.
They should not contain UI code.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import pandas as pd


@dataclass
class FileRecord:
    """
    Represents one imported file and the settings chosen for it.
    """
    path: str
    encoding: Optional[str] = None
    skiprows: int = 0
    dataframe: Optional[pd.DataFrame] = None
    column_mapping: Dict[str, str] = field(default_factory=dict)
    chamber_type: str = ""
    chamber_id: str = ""
    site_name: str = ""
    file_name: str = ""


@dataclass
class ChamberResult:
    """
    Result of one analyzed file.
    """
    record: FileRecord
    n_points: int
    slope: float
    intercept: float
    r2: float
    unadjusted_do_rate: float
    adjusted_do_rate: float = float("nan")
    temp_corrected_rate: float = float("nan")
    sod_g_m2_day: float = float("nan")
    mean_temp: float = float("nan")
    start_time: Optional[pd.Timestamp] = None
    end_time: Optional[pd.Timestamp] = None
    regression_df: Optional[pd.DataFrame] = None
    selected_minutes: float = float("nan")