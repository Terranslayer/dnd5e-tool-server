import json

from dnd5e_engine import terms


def _write_term_map(tmp_path):
    p = tmp_path / "term_map.json"
    p.write_text(json.dumps({
        "monsters": {"goblin": "地精"},
        "spells": {"fireball": "火球术"},
    }, ensure_ascii=False), encoding="utf-8")
    return p


def test_load_and_zh_for(tmp_path):
    tm = terms.TermMap.load(_write_term_map(tmp_path))
    assert tm.zh_for("monsters", "goblin") == "地精"
    assert tm.zh_for("monsters", "unknown") is None


def test_translate_en_to_zh(tmp_path):
    tm = terms.TermMap.load(_write_term_map(tmp_path))
    assert tm.translate("fireball", direction="en2zh") == "火球术"


def test_translate_zh_to_en(tmp_path):
    tm = terms.TermMap.load(_write_term_map(tmp_path))
    assert tm.translate("地精", direction="zh2en") == "goblin"


def test_translate_missing_returns_none(tmp_path):
    tm = terms.TermMap.load(_write_term_map(tmp_path))
    assert tm.translate("nonexistent", direction="en2zh") is None
