"""
Filename helpers.
"""

import os
import re


def make_safe_filename(name: str) -> str:
    return name.replace(os.sep, "_").replace("/", "_").replace("\\", "_").strip()


def infer_chamber_id_from_filename(filename: str) -> str:
    """
    Try to infer chamber ID from the filename.
    This matches the current app's general behavior, but keeps it isolated.
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    m = re.search(r"(\d+|AMB)$", base, re.IGNORECASE)
    if not m:
        return ""
    candidate = m.group(1).upper()
    return candidate if candidate in ["00", "0", "1", "2", "3", "4", "AMB"] else ""