from pathlib import Path

_SKILL = Path(__file__).resolve().parent.parent / "examples/workflows/solo-dm/SKILL.md"


def test_solo_dm_skill_exists_with_frontmatter():
    assert _SKILL.exists()
    text = _SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: solo-dm" in text and "description:" in text


def test_solo_dm_references_core_tools():
    text = _SKILL.read_text(encoding="utf-8")
    for tool in ("load_play_context", "start_encounter", "manage_combat_state",
                 "apply_hp_change", "resolve_check", "resolve_attack",
                 "update_campaign_state", "load_style"):
        assert tool in text, f"skill 应引用 {tool}"


def test_solo_dm_documents_safety_rails():
    text = _SKILL.read_text(encoding="utf-8")
    assert "不替玩家" in text          # 玩家自主
    assert "可审计" in text            # 状态写可审计文件
    assert "走工具" in text or "绝不编" in text  # 数值/规则走工具
