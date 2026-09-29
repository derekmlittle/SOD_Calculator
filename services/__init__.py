"""
Services package.

This package contains the application logic for:
- importing CSVs
- calculations
- plotting
- report generation
"""

from .calculation_service import (
    ChamberResult,
    compute_chamber_result,
    apply_blank_adjustment_and_convert,
    summarize_site,
    results_to_dataframe,
)
from .csv_importer import read_csv_with_fallback
from .plot_service import plot_site_results
from .report_service import build_word_report