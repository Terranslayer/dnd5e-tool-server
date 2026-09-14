"""English<->Chinese term map. Keyed by category -> english `index` slug -> 中文.
The English slug is the stable join key (never the display name)."""

from __future__ import annotations

import json
from pathlib import Path


class TermMap:
    def __init__(self, by_category: dict[str, dict[str, str]]):
        self._by_category = by_category
        # build reverse index: zh -> (category, en_index)
        self._reverse: dict[str, tuple[str, str]] = {}
        for category, mapping in by_category.items():
            for en_index, zh in mapping.items():
                self._reverse[zh] = (category, en_index)

    @classmethod
    def load(cls, path) -> "TermMap":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data)

    def zh_for(self, category: str, en_index: str) -> str | None:
        return self._by_category.get(category, {}).get(en_index)

    def translate(self, term: str, direction: str = "en2zh") -> str | None:
        if direction == "en2zh":
            for mapping in self._by_category.values():
                if term in mapping:
                    return mapping[term]
            return None
        if direction == "zh2en":
            hit = self._reverse.get(term)
            return hit[1] if hit else None
        raise ValueError("direction must be 'en2zh' or 'zh2en'")
