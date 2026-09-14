from dnd5e_engine.state import StateService
from dnd5e_engine.vault import VaultService


def test_start_encounter_sorts_and_ids(tmp_path):
    svc = StateService(tmp_path)
    r = svc.start_encounter("矿坑", "矿口伏击", [
        {"name": "地精A", "side": "enemy", "initiative": 12, "ac": 13, "hp": {"value": 7, "max": 7}},
        {"name": "游侠", "side": "party", "initiative": 18, "ac": 16, "hp": {"value": 24, "max": 24}},
    ])
    assert r["round"] == 1 and r["turn_index"] == 0
    assert [c["name"] for c in r["combatants"]] == ["游侠", "地精A"]  # initiative 降序
    assert all(c["id"] for c in r["combatants"])
    assert "variants/main/Encounters_遭遇/矿口伏击.md" in r["path"]


def test_start_encounter_does_not_touch_template(tmp_path):
    v = VaultService(tmp_path)
    v.create_note("encounter", "矿口伏击", campaign="矿坑", body="模板正文")  # 模板层
    StateService(tmp_path).start_encounter(
        "矿坑", "矿口伏击",
        [{"name": "地精", "side": "enemy", "initiative": 10, "ac": 13, "hp": {"value": 7, "max": 7}}])
    tmpl = v.read_note("04_Campaign_战役/矿坑/Encounters_遭遇/矿口伏击.md")
    assert tmpl["body"] == "模板正文"  # 模板未被触碰


def test_apply_hp_damage_uses_temp_then_value(tmp_path):
    svc = StateService(tmp_path)
    r = svc.start_encounter("c", "e", [{"name": "X", "side": "party",
        "initiative": 10, "ac": 12, "hp": {"value": 10, "max": 10, "temp": 3}}])
    cid = r["combatants"][0]["id"]
    out = svc.apply_hp_change("c", "e", cid, -5)
    assert out["hp"]["temp"] == 0 and out["hp"]["value"] == 8 and out["status"] == "ok"


def test_apply_hp_floor_and_down(tmp_path):
    svc = StateService(tmp_path)
    r = svc.start_encounter("c", "e", [{"name": "X", "side": "party",
        "initiative": 10, "ac": 12, "hp": {"value": 4, "max": 10}}])
    cid = r["combatants"][0]["id"]
    out = svc.apply_hp_change("c", "e", cid, -9)
    assert out["hp"]["value"] == 0 and out["status"] == "down"


def test_apply_hp_heal_caps_at_max(tmp_path):
    svc = StateService(tmp_path)
    r = svc.start_encounter("c", "e", [{"name": "X", "side": "party",
        "initiative": 10, "ac": 12, "hp": {"value": 2, "max": 10}}])
    cid = r["combatants"][0]["id"]
    out = svc.apply_hp_change("c", "e", cid, 100)
    assert out["hp"]["value"] == 10 and out["status"] == "ok"


def test_apply_hp_unknown_combatant_raises(tmp_path):
    import pytest
    svc = StateService(tmp_path)
    svc.start_encounter("c", "e", [{"name": "X", "side": "party",
        "initiative": 10, "ac": 12, "hp": {"value": 5, "max": 5}}])
    with pytest.raises(ValueError):
        svc.apply_hp_change("c", "e", "nope", -1)


def test_advance_turn_wraps_and_increments_round(tmp_path):
    svc = StateService(tmp_path)
    svc.start_encounter("c", "e", [
        {"name": "A", "side": "x", "initiative": 20, "ac": 10, "hp": {"value": 5, "max": 5}},
        {"name": "B", "side": "y", "initiative": 10, "ac": 10, "hp": {"value": 5, "max": 5}},
    ])
    s1 = svc.manage_combat_state("c", "e", advance_turn=True)
    assert s1["round"] == 1 and s1["turn_index"] == 1 and s1["active_combatant"]["name"] == "B"
    s2 = svc.manage_combat_state("c", "e", advance_turn=True)
    assert s2["round"] == 2 and s2["turn_index"] == 0 and s2["active_combatant"]["name"] == "A"


def test_conditions_dedup_clear_and_slots(tmp_path):
    svc = StateService(tmp_path)
    r = svc.start_encounter("c", "e", [{"name": "法师", "side": "party",
        "initiative": 15, "ac": 12, "hp": {"value": 8, "max": 8}}])
    cid = r["combatants"][0]["id"]
    mid = svc.manage_combat_state("c", "e", combatant_id=cid, set_conditions=["prone", "prone"])
    assert mid["changed"]["conditions"] == ["prone"]  # 去重：两个 prone 只落一个
    out = svc.manage_combat_state("c", "e", combatant_id=cid,
                                  set_conditions=["restrained"],
                                  clear_conditions=["prone"], spell_slots={"1": 2})
    assert out["changed"]["conditions"] == ["restrained"]  # prone 去重并被清、restrained 加入
    assert out["changed"]["spell_slots"] == {"1": 2}


def test_update_campaign_state_creates_and_merges_flags(tmp_path):
    svc = StateService(tmp_path)
    s1 = svc.update_campaign_state("c", patch={"current": {"location_name": "矿口"},
                                               "world_flags": {"门已开": True}})
    assert s1["type"] == "campaign_state" and s1["current"]["location_name"] == "矿口"
    assert s1["world_flags"] == {"门已开": True}
    s2 = svc.update_campaign_state("c", patch={"world_flags": {"桥已断": True}})
    assert s2["world_flags"] == {"门已开": True, "桥已断": True}  # world_flags 增量合并
    s3 = svc.update_campaign_state("c", patch={"current": {"location_name": "竖井"}})
    assert s3["current"] == {"location_name": "竖井"}  # 其它 key 整体替换


def test_apply_hp_revive_clears_down_status(tmp_path):
    svc = StateService(tmp_path)
    r = svc.start_encounter("c", "e", [{"name": "X", "side": "party",
        "initiative": 10, "ac": 12, "hp": {"value": 10, "max": 10}}])
    cid = r["combatants"][0]["id"]
    svc.apply_hp_change("c", "e", cid, -10)   # 打到 0 → down
    out = svc.apply_hp_change("c", "e", cid, 5)  # 治疗 → 应恢复 ok
    assert out["status"] == "ok" and out["hp"]["value"] == 5


def test_start_encounter_rejects_empty_combatants(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        StateService(tmp_path).start_encounter("c", "e", [])


def test_update_campaign_state_rejects_non_dict_world_flags(tmp_path):
    import pytest
    with pytest.raises(TypeError):
        StateService(tmp_path).update_campaign_state("c", patch={"world_flags": "oops"})


def test_load_play_context_empty(tmp_path):
    ctx = StateService(tmp_path).load_play_context("空团")
    assert ctx["state"] == {} and ctx["active_encounters"] == []
    assert ctx["style"]["found"] is False and ctx["style"]["body"]  # 中性缺省风格


def test_load_play_context_populated(tmp_path):
    from dnd5e_engine.vault import VaultService
    svc = StateService(tmp_path)
    svc.update_campaign_state("孤山", patch={"current": {"location_name": "矿口"}})
    svc.start_encounter("孤山", "矿口伏击", [{"name": "地精", "side": "enemy",
        "initiative": 11, "ac": 13, "hp": {"value": 7, "max": 7}}])
    VaultService(tmp_path).create_note("style", "style", campaign="孤山",
                                       body="## 系统提示\n冷峻克制。")
    ctx = svc.load_play_context("孤山")
    assert ctx["state"]["current"]["location_name"] == "矿口"
    assert ctx["style"]["found"] is True and "冷峻" in ctx["style"]["body"]
    assert len(ctx["active_encounters"]) == 1
    enc = ctx["active_encounters"][0]
    assert enc["name"] == "矿口伏击" and enc["round"] == 1
    assert enc["combatants"][0]["name"] == "地精" and "hp" in enc["combatants"][0]
