"""Loads and caches the JSON datasets."""

import json
from pathlib import Path


class DataLoader:
    """Loads JSON files from the data folder and caches them in memory."""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"
        self._cache = {}

    def load(self, filename):
        """Return a list of records for the given file."""
        if filename in self._cache:
            return self._cache[filename]
        path = self.data_dir / filename
        try:
            with open(path, encoding="utf-8") as file:
                raw = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Could not load {path}: {error}") from error
        records = self._unwrap(raw)
        self._cache[filename] = records
        return records

    @staticmethod
    def _unwrap(raw):
        if isinstance(raw, list):
            return raw
        for value in raw.values():
            if isinstance(value, list):
                return value
        return [raw]