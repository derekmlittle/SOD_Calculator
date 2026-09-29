"""
Generic JSON storage helper.

This keeps persistence logic out of the UI.
"""

import json
import os
from typing import Dict, Any


class JsonStore:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self, data: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)