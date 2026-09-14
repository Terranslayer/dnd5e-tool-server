"""Lookup tools over SRDData + TermMap, always returning a source citation.
Anti-hallucination rule: if nothing is found, say so explicitly — never invent."""

from __future__ import annotations

from dnd5e_engine import encounter
from dnd5e_engine.data import SRDData
from dnd5e_engine.terms import TermMap

_CITATION = {"source": "SRD 5.1", "license": "CC-BY-4.0"}


class LookupService:
    def __init__(self, srd: SRDData, term_map: TermMap):
        self.srd = srd
        self.terms = term_map

    def _citation(self, entry: dict) -> dict:
        return {**_CITATION, "ref": entry.get("url")}

    def _resolve_index(self, category: str, query: str) -> str | None:
        """Resolve a query to an english index: direct slug, english name, or
        Chinese name via the term map."""
        if self.srd.get(category, query):
            return query
        q = query.lower()
        for entry in self.srd.all(category):
            if entry.get("name", "").lower() == q:
                return entry["index"]
        en = self.terms.translate(query, direction="zh2en")
        if en and self.srd.get(category, en):
            return en
        return None

    def _lookup(self, category: str, query: str, zh_label: str) -> dict:
        index = self._resolve_index(category, query)
        if index is None:
            return {"found": False,
                    "message": f"'{query}' 不在 SRD 5.1 的{zh_label}数据中（not in SRD）。"
                               f"需要我帮你生成一个原创版本或裁定吗？"}
        entry = self.srd.get(category, index)
        return {
            "found": True,
            "entry": entry,
            "name_en": entry.get("name"),
            "name_zh": self.terms.zh_for(category, index),
            "citation": self._citation(entry),
        }

    def lookup_monster(self, query: str) -> dict:
        return self._lookup("monsters", query, "怪物")

    def lookup_spell(self, query: str) -> dict:
        return self._lookup("spells", query, "法术")

    def lookup_condition(self, query: str) -> dict:
        return self._lookup("conditions", query, "状态")

    def lookup_rule(self, query: str) -> dict:
        """Keyword search over rules + rule-sections desc/name."""
        needle = query.lower()
        matches = []
        for category in ("rule-sections", "rules"):
            for entry in self.srd.all(category):
                desc = entry.get("desc", "")
                if isinstance(desc, list):
                    desc = " ".join(desc)
                if needle in entry.get("name", "").lower() or needle in str(desc).lower():
                    matches.append({"name": entry.get("name"), "index": entry.get("index"),
                                    "category": category, "citation": self._citation(entry)})
        if not matches:
            return {"found": False,
                    "message": f"SRD 5.1 中未检索到与 '{query}' 相关的规则条目。"}
        return {"found": True, "matches": matches[:10]}

    def translate_term(self, term: str, direction: str = "en2zh") -> dict:
        result = self.terms.translate(term, direction=direction)
        return {"found": result is not None, "term": term,
                "direction": direction, "translation": result}

    def monsters_by_cr(self, min_cr, max_cr=None) -> dict:
        """List SRD monsters whose challenge_rating falls in [min_cr, max_cr]
        (max_cr=None means exact min_cr). For picking budget-legal monsters."""
        lo = encounter.cr_to_float(min_cr)
        hi = lo if max_cr is None else encounter.cr_to_float(max_cr)
        if hi < lo:
            lo, hi = hi, lo
        results = []
        for entry in self.srd.all("monsters"):
            cr = entry.get("challenge_rating")
            if cr is None:
                continue
            if lo <= float(cr) <= hi:
                results.append({
                    "index": entry["index"],
                    "name_en": entry.get("name"),
                    "name_zh": self.terms.zh_for("monsters", entry["index"]),
                    "cr": cr,
                })
        results.sort(key=lambda m: (float(m["cr"]), m["index"]))
        return {"count": len(results), "min_cr": lo, "max_cr": hi,
                "monsters": results, "citation": dict(_CITATION)}
