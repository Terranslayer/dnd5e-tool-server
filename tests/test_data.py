import json

from dnd5e_engine import data


def _write_srd_dir(tmp_path):
    d = tmp_path / "srd"
    d.mkdir()
    (d / "5e-SRD-Monsters.json").write_text(json.dumps([
        {"index": "goblin", "name": "Goblin", "url": "/api/2014/monsters/goblin"},
    ]), encoding="utf-8")
    (d / "5e-SRD-Conditions.json").write_text(json.dumps([
        {"index": "blinded", "name": "Blinded", "desc": ["A blinded creature..."],
         "url": "/api/2014/conditions/blinded"},
    ]), encoding="utf-8")
    return d


def test_category_from_filename():
    assert data.category_from_filename("5e-SRD-Monsters.json") == "monsters"
    assert data.category_from_filename("5e-SRD-Rule-Sections.json") == "rule-sections"


def test_load_and_index(tmp_path):
    srd = data.SRDData.load(_write_srd_dir(tmp_path))
    assert srd.get("monsters", "goblin")["name"] == "Goblin"
    assert srd.get("conditions", "blinded")["desc"][0].startswith("A blinded")
    assert srd.get("monsters", "nonexistent") is None


def test_search_by_name_substring(tmp_path):
    srd = data.SRDData.load(_write_srd_dir(tmp_path))
    hits = srd.search("monsters", "gob")
    assert len(hits) == 1 and hits[0]["index"] == "goblin"


def test_categories(tmp_path):
    srd = data.SRDData.load(_write_srd_dir(tmp_path))
    assert set(srd.categories()) == {"monsters", "conditions"}
