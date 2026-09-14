import asyncio

from dnd5e_engine import server


def test_semantic_search_tool_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert "semantic_search" in {t.name for t in tools}


def test_tool_count_is_27():
    tools = asyncio.run(server.mcp.list_tools())
    assert len(tools) == 27


def test_play_context_tool_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert "load_play_context" in names


def test_state_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"start_encounter", "apply_hp_change",
            "manage_combat_state", "update_campaign_state"} <= names


def test_load_style_tool_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert "load_style" in names


def test_module_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"index_module", "validate_module_graph"} <= names
