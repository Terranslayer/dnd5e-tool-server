"""Chunk SRD narrative text into records and (optionally) embed + store them.
Only narrative categories are ingested; rules numbers stay in the structured
lookup layer (anti-hallucination boundary)."""

from __future__ import annotations

from dnd5e_engine.data import SRDData

# Categories whose `desc` is narrative prose worth semantic search.
NARRATIVE_CATEGORIES = ("spells", "conditions", "rules", "rule-sections")


def _desc_text(entry: dict) -> str:
    desc = entry.get("desc", "")
    if isinstance(desc, list):
        desc = " ".join(str(d) for d in desc)
    return str(desc).strip()


def build_records(srd: SRDData) -> list[dict]:
    """One record per narrative entry with desc. No vectors yet.
    统一 schema：source/license/ruleset/campaign/note_id（不再用 srd 布尔）。"""
    records: list[dict] = []
    for category in NARRATIVE_CATEGORIES:
        for entry in srd.all(category):
            text = _desc_text(entry)
            if not text:
                continue
            name = entry.get("name", "")
            records.append({
                "id": f"{category}:{entry.get('index')}",
                "text": f"{name}: {text}" if name else text,
                "category": category,
                "name": name,
                "index": entry.get("index") or "",
                "url": entry.get("url") or "",
                "source": "SRD 5.1",
                "license": "CC-BY-4.0",
                "ruleset": "dnd5e-2014",
                "campaign": "",
                "note_id": "",
            })
    return records


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """按空行分段，把段落打包成不超过 max_chars 字节的块（不切碎单个段落）。
    用 UTF-8 字节数计量，以正确处理多字节中文字符。
    单个段落本身超过 max_chars 时不再切碎、原样成一块（Phase 2 再做字节级次级切分）。"""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if buf and len(buf.encode()) + len(p.encode()) + 2 > max_chars:
            chunks.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        chunks.append(buf)
    return chunks


def records_from_module_text(text: str, campaign: str, source: str, license: str,
                             note_id: str = "", ruleset: str = "dnd5e-2014",
                             category: str = "module", name: str = "",
                             max_chars: int = 800) -> list[dict]:
    """把模组散文切块成与 SRD 同 schema 的向量记录（无 vector）。"""
    records: list[dict] = []
    for i, chunk in enumerate(chunk_text(text, max_chars=max_chars)):
        records.append({
            "id": f"{campaign}:{note_id or source}:{i}",
            "text": chunk,
            "category": category,
            "name": name,
            "index": "",
            "url": "",
            "source": source,
            "license": license,
            "ruleset": ruleset,
            "campaign": campaign,
            "note_id": note_id,
        })
    return records


def build_index(srd: SRDData, embedder, store) -> int:
    """Embed all narrative records and (re)build the vector store."""
    records = build_records(srd)
    vectors = embedder.embed([r["text"] for r in records])
    for r, v in zip(records, vectors):
        r["vector"] = v
    store.build(records)
    return len(records)
