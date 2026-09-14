from pathlib import Path

_SKILLS = Path(__file__).resolve().parent.parent / "examples/workflows"


def test_prep_and_parse_skills_load_style():
    for name in ("dnd5e-prep", "parse-module"):
        text = (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert "load_style" in text, f"{name} 应在生成前加载风格档案"


def test_prep_skill_documents_creating_style():
    prep = (_SKILLS / "dnd5e-prep" / "SKILL.md").read_text(encoding="utf-8")
    assert 'create_note("style"' in prep or "create_note(\"style\"" in prep
