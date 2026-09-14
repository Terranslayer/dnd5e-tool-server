from pathlib import Path

_SKILL = Path(__file__).resolve().parent.parent / "examples/workflows/parse-module/SKILL.md"


def test_skill_file_exists_with_frontmatter():
    assert _SKILL.exists()
    text = _SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: parse-module" in text
    assert "description:" in text


def test_skill_references_engine_tools():
    text = _SKILL.read_text(encoding="utf-8")
    for tool in ("create_note", "index_module", "validate_module_graph"):
        assert tool in text


def test_prep_skill_drops_srd_boolean():
    prep = (Path(__file__).resolve().parent.parent
            / "examples/workflows/dnd5e-prep/SKILL.md").read_text(encoding="utf-8")
    assert "srd: false" not in prep and "srd: true" not in prep
