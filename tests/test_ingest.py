import json

from dnd5e_engine import data, ingest
from dnd5e_engine.embeddings import FakeEmbedder
from dnd5e_engine.vectorstore import VectorStore


def _srd(tmp_path):
    d = tmp_path / "srd"
    d.mkdir()
    (d / "5e-SRD-Spells.json").write_text(json.dumps([
        {"index": "fireball", "name": "Fireball",
         "desc": ["A bright streak flashes...", "Each creature in a 20-foot radius..."],
         "url": "/api/2014/spells/fireball"},
    ]), encoding="utf-8")
    (d / "5e-SRD-Conditions.json").write_text(json.dumps([
        {"index": "prone", "name": "Prone", "desc": ["A prone creature's only movement..."],
         "url": "/api/2014/conditions/prone"},
    ]), encoding="utf-8")
    (d / "5e-SRD-Monsters.json").write_text(json.dumps([
        {"index": "goblin", "name": "Goblin", "url": "/api/2014/monsters/goblin"},
    ]), encoding="utf-8")
    return data.SRDData.load(d)


def test_build_records_covers_narrative_categories(tmp_path):
    recs = ingest.build_records(_srd(tmp_path))
    cats = {r["category"] for r in recs}
    assert "spells" in cats and "conditions" in cats
    assert "monsters" not in cats  # monsters have no desc -> skipped
    fb = next(r for r in recs if r["index"] == "fireball")
    assert fb["id"] == "spells:fireball"
    assert "Fireball" in fb["text"] and "bright streak" in fb["text"]
    assert fb["source"] == "SRD 5.1" and fb["license"] == "CC-BY-4.0"
    assert fb["campaign"] == "" and fb["url"] == "/api/2014/spells/fireball"
    assert "srd" not in fb  # srd 布尔已移除，改由 source/license 派生
    assert "vector" not in fb  # records are pre-embedding


def test_build_index_embeds_and_stores(tmp_path):
    srd = _srd(tmp_path)
    store = VectorStore(tmp_path / "idx")
    n = ingest.build_index(srd, FakeEmbedder(dim=8), store)
    assert n >= 2
    rows = store.search(FakeEmbedder(dim=8).embed(["Fireball"])[0], k=1)
    assert rows[0]["category"] in {"spells", "conditions"}
    assert "_distance" in rows[0]


def test_chunk_text_packs_paragraphs():
    text = "段落一。\n\n段落二，稍长一些的内容。\n\n段落三。"
    chunks = ingest.chunk_text(text, max_chars=20)
    assert len(chunks) >= 2
    assert all(c.strip() for c in chunks)
    joined = "\n\n".join(chunks)
    for p in ("段落一", "段落二", "段落三"):
        assert p in joined


def test_records_from_module_text_metadata():
    recs = ingest.records_from_module_text(
        "地窖弥漫腐臭。\n\n一只巨鼠窜出。",
        campaign="孤山矿坑", source="测试模组", license="user-provided",
        note_id="scene-1", max_chars=20)
    assert len(recs) >= 2
    r = recs[0]
    assert r["campaign"] == "孤山矿坑" and r["source"] == "测试模组"
    assert r["license"] == "user-provided" and r["note_id"] == "scene-1"
    assert r["ruleset"] == "dnd5e-2014" and r["category"] == "module"
    assert set(["id", "text", "category", "name", "index", "url",
                "source", "license", "ruleset", "campaign", "note_id"]) <= set(r)
    assert "vector" not in r
