import json

from dnd5e_engine import data, ingest
from dnd5e_engine.embeddings import FakeEmbedder
from dnd5e_engine.retrieval import SemanticSearch
from dnd5e_engine.vectorstore import VectorStore


def _service(tmp_path):
    d = tmp_path / "srd"
    d.mkdir()
    (d / "5e-SRD-Spells.json").write_text(json.dumps([
        {"index": "fireball", "name": "Fireball", "desc": ["A bright streak..."],
         "url": "/api/2014/spells/fireball"},
        {"index": "cure-wounds", "name": "Cure Wounds", "desc": ["A creature you touch regains..."],
         "url": "/api/2014/spells/cure-wounds"},
    ]), encoding="utf-8")
    srd = data.SRDData.load(d)
    store = VectorStore(tmp_path / "idx")
    emb = FakeEmbedder(dim=8)
    ingest.build_index(srd, emb, store)
    return SemanticSearch(emb, store)


def test_semantic_search_returns_results_with_citation(tmp_path):
    svc = _service(tmp_path)
    out = svc.search("Fireball", k=2)
    assert out["count"] >= 1
    top = out["results"][0]
    assert top["index"] in {"fireball", "cure-wounds"}
    assert top["citation"]["source"] == "SRD 5.1"
    assert top["citation"]["license"] == "CC-BY-4.0"
    assert "ref" in top["citation"]
    assert "score" in top


def test_semantic_search_respects_k(tmp_path):
    svc = _service(tmp_path)
    out = svc.search("anything", k=1)
    assert out["count"] == 1


def test_index_text_recalled_under_its_campaign(tmp_path):
    svc = _service(tmp_path)  # SRD baseline，campaign=""
    svc.index_text("地窖里弥漫着腐臭，一只巨鼠从阴影中窜出。",
                   campaign="孤山矿坑", source="测试模组",
                   license="user-provided", note_id="scene-1")
    hit = svc.search("巨鼠 腐臭 地窖", k=5, campaign="孤山矿坑")
    assert "测试模组" in {r["citation"]["source"] for r in hit["results"]}


def test_other_campaign_excluded(tmp_path):
    svc = _service(tmp_path)
    svc.index_text("地窖里弥漫着腐臭，一只巨鼠从阴影中窜出。",
                   campaign="孤山矿坑", source="测试模组",
                   license="user-provided", note_id="scene-1")
    other = svc.search("巨鼠 腐臭 地窖", k=5, campaign="别的战役")
    assert "测试模组" not in {r["citation"]["source"] for r in other["results"]}
