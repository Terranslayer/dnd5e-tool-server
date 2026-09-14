"""Load the bundled 5e-database SRD JSON files and index them by `index` slug."""

from __future__ import annotations

import json
from pathlib import Path


def category_from_filename(filename: str) -> str:
    """'5e-SRD-Monsters.json' -> 'monsters'; '5e-SRD-Rule-Sections.json' -> 'rule-sections'."""
    stem = filename[: -len(".json")] if filename.endswith(".json") else filename
    if stem.startswith("5e-SRD-"):
        stem = stem[len("5e-SRD-"):]
    return stem.lower()


class SRDData:
    """In-memory SRD index: {category: {index_slug: entry}}."""

    def __init__(self, by_category: dict[str, dict[str, dict]]):
        self._by_category = by_category

    @classmethod
    def load(cls, directory) -> "SRDData":
        directory = Path(directory)
        by_category: dict[str, dict[str, dict]] = {}
        for path in sorted(directory.glob("5e-SRD-*.json")):
            category = category_from_filename(path.name)
            entries = json.loads(path.read_text(encoding="utf-8"))
            indexed: dict[str, dict] = {}
            for entry in entries:
                key = entry.get("index")
                if key:
                    indexed[key] = entry
            by_category[category] = indexed
        return cls(by_category)

    def categories(self) -> list[str]:
        return list(self._by_category.keys())

    def get(self, category: str, index: str) -> dict | None:
        return self._by_category.get(category, {}).get(index)

    def all(self, category: str) -> list[dict]:
        return list(self._by_category.get(category, {}).values())

    def search(self, category: str, name_substring: str) -> list[dict]:
        needle = name_substring.lower()
        return [e for e in self.all(category) if needle in e.get("name", "").lower()]
