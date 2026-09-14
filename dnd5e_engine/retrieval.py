"""Semantic search over SRD + module narrative. Composes an Embedder + a
VectorStore（注入，故无 key 也可测）。检索支持按 campaign/ruleset 过滤，出处按记录返回。"""

from __future__ import annotations


def _esc(s: str) -> str:
    return s.replace("'", "''")


class SemanticSearch:
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def search(self, query: str, k: int = 5, campaign: str | None = None,
               ruleset: str | None = None) -> dict:
        vector = self.embedder.embed([query])[0]
        clauses = []
        if campaign:
            clauses.append(f"(campaign = '{_esc(campaign)}' OR campaign = '')")
        # SRD 记录 ruleset="dnd5e-2014"；传 ruleset 时按"该值 OR 空"过滤。
        # 注：家规变种跨规则集访问 SRD 的语义留待 Phase 2 明确（M1-4 仅 dnd5e-2014）。
        if ruleset:
            clauses.append(f"(ruleset = '{_esc(ruleset)}' OR ruleset = '')")
        where = " AND ".join(clauses) if clauses else None
        rows = self.store.search(vector, k=k, where=where)
        results = []
        for r in rows:
            results.append({
                "text": r.get("text"),
                "category": r.get("category"),
                "name": r.get("name"),
                "index": r.get("index"),
                "campaign": r.get("campaign"),
                "score": r.get("_distance"),
                "citation": {
                    "source": r.get("source"),
                    "license": r.get("license"),
                    "ref": r.get("url") or r.get("note_id"),
                    "note_id": r.get("note_id"),
                },
            })
        return {"count": len(results), "results": results}

    def index_text(self, text: str, campaign: str, source: str, license: str,
                   note_id: str = "", ruleset: str = "dnd5e-2014") -> dict:
        """把一段模组散文切块、嵌入、追加进库。返回 {count}。"""
        from dnd5e_engine import ingest
        records = ingest.records_from_module_text(
            text, campaign=campaign, source=source, license=license,
            note_id=note_id, ruleset=ruleset)
        vectors = self.embedder.embed([r["text"] for r in records])
        for r, v in zip(records, vectors):
            r["vector"] = v
        self.store.add(records)
        return {"count": len(records)}
