"""Build the SRD narrative vector index with real OpenAI embeddings.
Requires OPENAI_EMBEDDING_API_KEY in .env. Run: uv run python scripts/build_index.py
The index is written to data/vector_index/ (gitignored; rebuildable)."""

from __future__ import annotations

import sys
from pathlib import Path

# 让脚本无论从哪个 cwd 运行都能 import dnd5e_engine（项目未安装进 venv）。
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dnd5e_engine import config, ingest  # config import loads .env  # noqa: E402
from dnd5e_engine.data import SRDData
from dnd5e_engine.embeddings import OpenAIEmbedder
from dnd5e_engine.vectorstore import VectorStore

_DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    if not config.embedding_api_key():
        raise SystemExit("OPENAI_EMBEDDING_API_KEY not set (fill it into .env)")
    srd = SRDData.load(_DATA / "srd_2014")
    store = VectorStore(_DATA / "vector_index")
    n = ingest.build_index(srd, OpenAIEmbedder(), store)
    print(f"indexed {n} narrative records -> {_DATA / 'vector_index'} "
          f"(model: {config.embedding_model()})")


if __name__ == "__main__":
    main()
