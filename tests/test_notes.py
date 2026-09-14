import pytest

from dnd5e_engine import notes


def test_note_path_non_campaign():
    assert notes.note_path("npc", "酒馆老板") == "03_NPCs_角色/酒馆老板.md"
    assert notes.note_path("location", "月溪镇") == "02_World_世界/Locations_地点/月溪镇.md"


def test_note_path_campaign_scoped():
    assert notes.note_path("encounter", "哥布林伏击", campaign="失落矿坑") == \
        "04_Campaign_战役/失落矿坑/Encounters_遭遇/哥布林伏击.md"


def test_note_path_campaign_state_at_campaign_root():
    assert notes.note_path("campaign_state", "state", campaign="失落矿坑") == \
        "04_Campaign_战役/失落矿坑/state.md"


def test_note_path_unknown_type_raises():
    with pytest.raises(ValueError):
        notes.note_path("dragon_hoard", "x")


def test_note_path_campaign_required_raises():
    with pytest.raises(ValueError):
        notes.note_path("encounter", "哥布林伏击")  # campaign missing


def test_sanitize_filename():
    assert notes.sanitize_filename("a/b:c?") == "a-b-c"
    assert notes.sanitize_filename("守卫队长") == "守卫队长"
    with pytest.raises(ValueError):
        notes.sanitize_filename("///")


def test_new_id_is_hex_uuid():
    i = notes.new_id()
    assert len(i) == 32 and all(c in "0123456789abcdef" for c in i)


def test_render_and_parse_roundtrip():
    fm = {"id": "abc", "type": "npc", "name": "酒馆老板"}
    text = notes.render_note(fm, "一个圆脸的中年男人。")
    assert text.startswith("---\n") and "酒馆老板" in text
    parsed_fm, body = notes.parse_note(text)
    assert parsed_fm == fm
    assert body == "一个圆脸的中年男人。"


def test_parse_note_without_frontmatter():
    fm, body = notes.parse_note("just some text")
    assert fm == {} and body == "just some text"


def test_sanitize_filename_strips_trailing_punct():
    assert notes.sanitize_filename("精灵-德鲁伊") == "精灵-德鲁伊"  # internal hyphen kept
    assert notes.sanitize_filename(".hidden") == "hidden"
    assert notes.sanitize_filename("a.b.c") == "a.b.c"  # internal dots kept


def test_sanitize_filename_pure_punctuation_raises():
    for bad in ["-.-", "...", "- . -", "*?|"]:
        with pytest.raises(ValueError):
            notes.sanitize_filename(bad)


def test_new_module_note_paths():
    assert notes.note_path("scene", "矿口", campaign="孤山矿坑") == \
        "04_Campaign_战役/孤山矿坑/Scenes_场景/矿口.md"
    assert notes.note_path("clue", "血迹", campaign="孤山矿坑") == \
        "04_Campaign_战役/孤山矿坑/Clues_线索/血迹.md"
    assert notes.note_path("map", "矿坑全图", campaign="孤山矿坑") == \
        "04_Campaign_战役/孤山矿坑/Maps_地图/矿坑全图.md"
    assert notes.note_path("campaign", "孤山矿坑", campaign="孤山矿坑") == \
        "04_Campaign_战役/孤山矿坑/孤山矿坑.md"


def test_relation_fields_registry():
    assert "exits" in notes.RELATION_FIELDS["scene"]
    assert "revealed_by" in notes.RELATION_FIELDS["clue"]


def test_parse_links_extracts_wikilinks():
    assert notes.parse_links("[[矿口]]") == ["矿口"]
    assert notes.parse_links(["[[矿口]]", "[[竖井|深井]]"]) == ["矿口", "竖井"]
    assert notes.parse_links("矿口") == ["矿口"]          # 裸名也算
    assert notes.parse_links(None) == []
    assert notes.parse_links([]) == []


def test_style_note_path():
    assert notes.note_path("style", "style", campaign="孤山矿坑") == \
        "04_Campaign_战役/孤山矿坑/style.md"


def test_parse_note_preserves_dashes_in_body():
    # 正文里含 markdown 分隔线 --- 时，frontmatter 解析不应被它截断
    fm = {"id": "x", "type": "npc", "name": "测试"}
    body = "第一段。\n\n---\n\n第二段（含分隔线）。"
    text = notes.render_note(fm, body)
    pfm, pbody = notes.parse_note(text)
    assert pfm == fm
    assert pbody == body
