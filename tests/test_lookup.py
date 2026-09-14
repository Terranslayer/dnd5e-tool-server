import json

from dnd5e_engine import data, lookup, terms


def _fixture(tmp_path):
    d = tmp_path / "srd"
    d.mkdir()
    (d / "5e-SRD-Monsters.json").write_text(json.dumps([
        {"index": "goblin", "name": "Goblin", "armor_class": [{"value": 15}],
         "url": "/api/2014/monsters/goblin"},
    ]), encoding="utf-8")
    (d / "5e-SRD-Conditions.json").write_text(json.dumps([
        {"index": "blinded", "name": "Blinded", "desc": ["A blinded creature can't see."],
         "url": "/api/2014/conditions/blinded"},
    ]), encoding="utf-8")
    (d / "5e-SRD-Rule-Sections.json").write_text(json.dumps([
        {"index": "cover", "name": "Cover", "desc": "Walls, trees... provide cover.",
         "url": "/api/2014/rule-sections/cover"},
    ]), encoding="utf-8")
    tm_path = tmp_path / "term_map.json"
    tm_path.write_text(json.dumps({"monsters": {"goblin": "地精"},
                                   "conditions": {"blinded": "目盲"}}, ensure_ascii=False),
                       encoding="utf-8")
    srd = data.SRDData.load(d)
    tm = terms.TermMap.load(tm_path)
    return lookup.LookupService(srd, tm)


def test_lookup_monster_by_index_with_citation(tmp_path):
    svc = _fixture(tmp_path)
    r = svc.lookup_monster("goblin")
    assert r["found"] is True
    assert r["entry"]["name"] == "Goblin"
    assert r["name_zh"] == "地精"
    assert r["citation"]["source"] == "SRD 5.1"
    assert r["citation"]["license"] == "CC-BY-4.0"
    assert r["citation"]["ref"] == "/api/2014/monsters/goblin"


def test_lookup_monster_by_chinese_name(tmp_path):
    svc = _fixture(tmp_path)
    r = svc.lookup_monster("地精")
    assert r["found"] is True
    assert r["entry"]["index"] == "goblin"


def test_lookup_condition(tmp_path):
    svc = _fixture(tmp_path)
    r = svc.lookup_condition("blinded")
    assert r["found"] is True
    assert r["name_zh"] == "目盲"


def test_lookup_not_found_does_not_fabricate(tmp_path):
    svc = _fixture(tmp_path)
    r = svc.lookup_monster("tarrasque")
    assert r["found"] is False
    assert "entry" not in r
    assert "不在" in r["message"] or "not in" in r["message"].lower()


def test_lookup_rule_keyword(tmp_path):
    svc = _fixture(tmp_path)
    r = svc.lookup_rule("cover")
    assert r["found"] is True
    assert any("cover" in m["name"].lower() for m in r["matches"])


def _bestiary_fixture(tmp_path):
    import json
    from dnd5e_engine import data, terms
    d = tmp_path / "srd"
    d.mkdir()
    (d / "5e-SRD-Monsters.json").write_text(json.dumps([
        {"index": "goblin", "name": "Goblin", "challenge_rating": 0.25,
         "url": "/api/2014/monsters/goblin"},
        {"index": "hobgoblin", "name": "Hobgoblin", "challenge_rating": 0.5,
         "url": "/api/2014/monsters/hobgoblin"},
        {"index": "ogre", "name": "Ogre", "challenge_rating": 2,
         "url": "/api/2014/monsters/ogre"},
        {"index": "commoner", "name": "Commoner", "challenge_rating": 0,
         "url": "/api/2014/monsters/commoner"},
    ]), encoding="utf-8")
    tm_path = tmp_path / "term_map.json"
    tm_path.write_text(json.dumps({"monsters": {"goblin": "地精", "ogre": "食人魔"}},
                                  ensure_ascii=False), encoding="utf-8")
    srd = data.SRDData.load(d)
    tm = terms.TermMap.load(tm_path)
    return lookup.LookupService(srd, tm)


def test_monsters_by_cr_exact(tmp_path):
    svc = _bestiary_fixture(tmp_path)
    out = svc.monsters_by_cr("1/4")
    assert out["count"] == 1
    assert out["monsters"][0]["index"] == "goblin"
    assert out["monsters"][0]["name_zh"] == "地精"
    assert out["monsters"][0]["cr"] == 0.25
    assert out["citation"]["source"] == "SRD 5.1"


def test_monsters_by_cr_range_sorted(tmp_path):
    svc = _bestiary_fixture(tmp_path)
    out = svc.monsters_by_cr("0", "1/2")
    indexes = [m["index"] for m in out["monsters"]]
    assert indexes == ["commoner", "goblin", "hobgoblin"]  # cr 0, 0.25, 0.5 sorted


def test_monsters_by_cr_range_accepts_reversed_bounds(tmp_path):
    svc = _bestiary_fixture(tmp_path)
    out = svc.monsters_by_cr("2", "1")  # reversed; should normalize to [1,2]
    assert [m["index"] for m in out["monsters"]] == ["ogre"]


def test_monsters_by_cr_none_match(tmp_path):
    svc = _bestiary_fixture(tmp_path)
    out = svc.monsters_by_cr("30")
    assert out["count"] == 0 and out["monsters"] == []
