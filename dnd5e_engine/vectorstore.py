"""Local LanceDB vector store. Records are plain dicts that MUST include a
'vector' key (list[float]); other keys are metadata stored alongside."""

from __future__ import annotations

from pathlib import Path

import lancedb


class VectorStore:
    def __init__(self, path, table: str = "srd"):
        self.path = str(path)
        self.table = table

    def build(self, records: list[dict]) -> int:
        db = lancedb.connect(self.path)
        db.create_table(self.table, data=records, mode="overwrite")
        return len(records)

    def search(self, query_vector: list[float], k: int = 5,
               where: str | None = None) -> list[dict]:
        db = lancedb.connect(self.path)
        tbl = db.open_table(self.table)
        q = tbl.search(query_vector)
        if where:
            q = q.where(where, prefilter=True)
        return q.limit(k).to_list()

    def add(self, records: list[dict]) -> int:
        """追加记录；表不存在则创建。记录键须与既有表 schema 一致。"""
        db = lancedb.connect(self.path)
        if self.exists():
            db.open_table(self.table).add(records)
        else:
            db.create_table(self.table, data=records, mode="overwrite")
        return len(records)

    def exists(self) -> bool:
        try:
            lancedb.connect(self.path).open_table(self.table)
            return True
        except Exception:
            return False
