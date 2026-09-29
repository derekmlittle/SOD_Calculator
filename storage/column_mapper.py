"""
Column mapping logic.

This is the replacement for the old ColumnMapperHelper behavior.
"""

from typing import Dict, List, Optional
from storage.profile_store import JsonStore


class ColumnMapper:
    def __init__(self, target_fields: List[str], storage_path: str = "column_mappings.json"):
        self.target_fields = target_fields
        self.store = JsonStore(storage_path)
        self.mappings = self.store.load()

    @staticmethod
    def normalize(text: str) -> str:
        s = str(text).strip().lower()
        for ch in [" ", "_", "-", "%", "/", "°", "(", ")", "."]:
            s = s.replace(ch, "")
        return s

    def auto_detect(self, columns: List[str]) -> Dict[str, Optional[str]]:
        lookup = {self.normalize(c): c for c in columns}
        mapping = {}
        for target in self.target_fields:
            mapping[target] = lookup.get(self.normalize(target))
        return mapping

    def get_best_mapping(self, columns: List[str], profile_name: Optional[str] = None) -> Dict[str, Optional[str]]:
        if profile_name and profile_name in self.mappings:
            saved = self.mappings[profile_name]
            return {target: col if col in columns else None for target, col in saved.items()}
        return self.auto_detect(columns)

    def save_profile(self, profile_name: str, mapping: Dict[str, Optional[str]]) -> None:
        self.mappings[profile_name] = mapping
        self.store.save(self.mappings)

    def load_profile(self, profile_name: str) -> Dict[str, Optional[str]]:
        return self.mappings.get(profile_name, {})