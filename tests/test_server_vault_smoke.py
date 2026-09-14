import asyncio

from dnd5e_engine import server


def test_vault_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    assert {"create_note", "read_note", "list_notes"} <= names


def test_create_read_list_note_via_server(tmp_path, monkeypatch):
    monkeypatch.setenv("DND5E_VAULT", str(tmp_path))
    created = server.create_note("npc", "守卫队长", frontmatter={"role": "城卫"},
                                 body="忠诚而严厉。")
    assert created["path"] == "03_NPCs_角色/守卫队长.md"
    read = server.read_note(created["path"])
    assert read["frontmatter"]["name"] == "守卫队长"
    assert read["frontmatter"]["role"] == "城卫"
    assert read["frontmatter"]["type"] == "npc"
    assert "忠诚" in read["body"]
    listed = server.list_notes("npc")["notes"]
    assert any(n["name"] == "守卫队长" for n in listed)
