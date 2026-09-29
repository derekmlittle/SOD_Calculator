"""
Application constants.

This keeps shared lists and settings in one place so the UI and services
all use the same definitions.
"""

TARGET_FIELDS = [
    "TIME (HH:MM:SS)",
    "DATE (MM/DD/YYYY)",
    "FILE NAME",
    "SITE NAME",
    "ODO % SAT",
    "ODO MG/L",
    "TEMP C",
    "TURBIDITY FNU",
]

CHAMBER_TYPES = ["contact chamber", "blank chamber", "ambient"]

CHAMBER_IDS = ["00", "0", "1", "2", "3","4", "AMB"]

ENCODINGS = ["utf-8-sig", "utf-16", "cp1252", "latin1"]