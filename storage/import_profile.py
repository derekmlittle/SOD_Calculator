"""
Import profile storage.

This is where skip-row and import setting profiles live.
"""

from typing import Dict, Any
from storage.profile_store import JsonStore


class ImportProfileStore:
    def __init__(self, storage_path: str = "import_profiles.json"):
        self.store = JsonStore(storage_path)
        self.profiles = self.store.load()

    def list_profiles(self):
        return sorted(self.profiles.keys())

    def load_profile(self, name: str) -> Dict[str, Any]:
        return self.profiles.get(name, {})

    def save_profile(self, name: str, data: Dict[str, Any]) -> None:
        self.profiles[name] = data
        self.store.save(self.profiles)