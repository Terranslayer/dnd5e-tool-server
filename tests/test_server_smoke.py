import asyncio

import pytest

from dnd5e_engine import server


def test_server_object_exists():
    assert server.mcp.name == "dnd5e-engine"


def test_roll_dice_tool_callable():
    # The tool functions are plain functions registered on the server; call directly.
    out = server.roll_dice("1d1+2")  # 1d1 always rolls 1
    assert out["total"] == 3


def test_encounter_tool_branches_on_ruleset():
    out = server.evaluate_encounter([3, 3, 3, 3], [{"cr": "1/4", "count": 4}], "2014")
    assert out["band"] == "easy"


def test_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    for expected in {"roll_dice", "resolve_check", "lookup_monster", "evaluate_encounter",
                     "lookup_rule", "translate_term"}:
        assert expected in names


def test_roll_dice_unified_schema_both_branches():
    # Both branches must expose the same keys.
    expected_keys = {"notation", "rolls", "natural", "modifier",
                     "advantage", "disadvantage", "crit", "total"}
    normal = server.roll_dice("2d6+3")
    adv = server.roll_dice("1d20+5", advantage=True)
    assert set(normal.keys()) == expected_keys
    assert set(adv.keys()) == expected_keys


def test_roll_dice_normal_branch_natural_none_for_multidice():
    out = server.roll_dice("2d6")
    assert out["natural"] is None  # multiple dice -> no single natural


def test_roll_dice_advantage_only_on_d20():
    with pytest.raises(ValueError):
        server.roll_dice("2d6", advantage=True)


def test_monsters_by_cr_tool_registered_and_works():
    tools = asyncio.run(server.mcp.list_tools())
    assert "monsters_by_cr" in {t.name for t in tools}
    # real SRD data: goblin is CR 1/4
    out = server.monsters_by_cr("1/4")
    assert out["count"] >= 1
    assert any(m["index"] == "goblin" for m in out["monsters"])
    assert out["citation"]["source"] == "SRD 5.1"


def test_tool_count_is_27():
    tools = asyncio.run(server.mcp.list_tools())
    assert len(tools) == 27
