from dnd5e_engine import modulegraph
from dnd5e_engine.vault import VaultService


def _vault(tmp_path):
    v = VaultService(tmp_path)
    C = "孤山矿坑"
    v.create_note("campaign", C, campaign=C,
                  frontmatter={"source": "测试模组", "exits": ["[[矿口]]"]})
    v.create_note("scene", "矿口", campaign=C,
                  frontmatter={"exits": ["[[竖井]]"], "clues": ["[[血迹]]"]})
    v.create_note("scene", "竖井", campaign=C, frontmatter={})         # 可达（矿口→竖井）
    v.create_note("scene", "密室", campaign=C, frontmatter={})         # 孤立：无入边
    v.create_note("clue", "血迹", campaign=C,
                  frontmatter={"revealed_by": ["[[矿口]]"]})
    v.create_note("clue", "暗号", campaign=C, frontmatter={})          # 无来源
    v.create_note("scene", "断桥", campaign=C,
                  frontmatter={"exits": ["[[不存在的场景]]"]})          # 悬空链接
    return v, C


def test_validate_flags_issues(tmp_path):
    v, C = _vault(tmp_path)
    rep = modulegraph.validate(v, C)
    kinds = {(i["type"], i.get("note"), i.get("target")) for i in rep["issues"]}
    assert ("unreachable_scene", "密室", None) in kinds
    assert ("clue_without_source", "暗号", None) in kinds
    assert ("dangling_link", "断桥", "不存在的场景") in kinds
    assert not any(i["note"] == "竖井" for i in rep["issues"])
    assert rep["counts"]["scene"] == 4


def test_validate_clean_graph_has_no_issues(tmp_path):
    v = VaultService(tmp_path)
    C = "净土"
    v.create_note("campaign", C, campaign=C, frontmatter={"exits": ["[[入口]]"]})
    v.create_note("scene", "入口", campaign=C, frontmatter={"clues": ["[[脚印]]"]})
    v.create_note("clue", "脚印", campaign=C, frontmatter={"revealed_by": ["[[入口]]"]})
    rep = modulegraph.validate(v, C)
    assert rep["issues"] == []


def test_start_scene_linked_only_from_campaign_is_reachable(tmp_path):
    from dnd5e_engine.vault import VaultService
    v = VaultService(tmp_path)
    C = "晨曦"
    # 概览笔记把"前厅"列为入口；前厅没有任何其它入边
    v.create_note("campaign", C, campaign=C, frontmatter={"scenes": ["[[前厅]]"]})
    v.create_note("scene", "前厅", campaign=C, frontmatter={})
    rep = modulegraph.validate(v, C)
    assert not any(i["type"] == "unreachable_scene" and i["note"] == "前厅"
                   for i in rep["issues"]), rep["issues"]
