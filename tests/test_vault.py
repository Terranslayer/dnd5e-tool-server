import pytest

from dnd5e_engine.vault import VaultService


def test_create_and_read_note(tmp_path):
    svc = VaultService(tmp_path)
    res = svc.create_note("npc", "酒馆老板", frontmatter={"role": "店主"},
                          body="一个圆脸的中年男人。", id="fixedid")
    assert res["path"] == "03_NPCs_角色/酒馆老板.md"
    assert res["id"] == "fixedid"
    assert res["created"] is True
    read = svc.read_note("03_NPCs_角色/酒馆老板.md")
    assert read["frontmatter"]["id"] == "fixedid"
    assert read["frontmatter"]["type"] == "npc"
    assert read["frontmatter"]["name"] == "酒馆老板"
    assert read["frontmatter"]["role"] == "店主"
    assert "圆脸" in read["body"]


def test_create_campaign_scoped_note(tmp_path):
    svc = VaultService(tmp_path)
    res = svc.create_note("encounter", "哥布林伏击", campaign="失落矿坑",
                          frontmatter={"round": 0}, body="3 只哥布林。", id="e1")
    assert res["path"] == "04_Campaign_战役/失落矿坑/Encounters_遭遇/哥布林伏击.md"
    read = svc.read_note(res["path"])
    assert read["frontmatter"]["campaign"] == "失落矿坑"
    assert read["frontmatter"]["round"] == 0


def test_create_auto_generates_id(tmp_path):
    svc = VaultService(tmp_path)
    res = svc.create_note("location", "月溪镇")
    assert len(res["id"]) == 32


def test_create_refuses_overwrite_unless_forced(tmp_path):
    svc = VaultService(tmp_path)
    svc.create_note("npc", "守卫", id="a")
    with pytest.raises(FileExistsError):
        svc.create_note("npc", "守卫", id="b")
    res = svc.create_note("npc", "守卫", id="c", overwrite=True)
    assert res["id"] == "c"


def test_read_missing_raises(tmp_path):
    svc = VaultService(tmp_path)
    with pytest.raises(FileNotFoundError):
        svc.read_note("03_NPCs_角色/不存在.md")


def test_list_notes_by_type(tmp_path):
    svc = VaultService(tmp_path)
    svc.create_note("npc", "酒馆老板", id="1")
    svc.create_note("npc", "守卫队长", id="2")
    listed = svc.list_notes("npc")
    names = {n["name"] for n in listed}
    assert names == {"酒馆老板", "守卫队长"}
    assert all(n["type"] == "npc" for n in listed)


def test_list_campaign_scoped_requires_campaign(tmp_path):
    svc = VaultService(tmp_path)
    with pytest.raises(ValueError):
        svc.list_notes("encounter")  # campaign missing


def test_load_style_found(tmp_path):
    svc = VaultService(tmp_path)
    svc.create_note("style", "style", campaign="孤山矿坑",
                    body="## 系统提示\n克苏鲁式低语，多用不安的暗示。")
    r = svc.load_style("孤山矿坑")
    assert r["found"] is True
    assert r["campaign"] == "孤山矿坑"
    assert "克苏鲁" in r["body"]
    assert r["frontmatter"]["type"] == "style"


def test_load_style_default_when_absent(tmp_path):
    svc = VaultService(tmp_path)
    r = svc.load_style("无档案战役")
    assert r["found"] is False
    assert r["frontmatter"] == {}
    assert r["body"] and "中性" in r["body"]  # 非空中性缺省


def test_read_note_rejects_path_traversal(tmp_path):
    svc = VaultService(tmp_path)
    # 逃逸 vault 根的相对路径必须被拒（在存在性检查之前），不得读到 vault 外的文件
    with pytest.raises(ValueError):
        svc.read_note("../../outside.md")
    with pytest.raises(ValueError):
        svc.read_note("../secret.md")


def test_list_notes_unfiltered_lists_all_types(tmp_path):
    svc = VaultService(tmp_path)
    svc.create_note("npc", "酒馆老板", id="1")
    svc.create_note("location", "月溪镇", id="2")
    svc.create_note("encounter", "伏击", campaign="矿坑", id="3")
    names = {n["name"] for n in svc.list_notes()}  # 不带 type/campaign
    assert {"酒馆老板", "月溪镇", "伏击"} <= names
