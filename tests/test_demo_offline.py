"""The public example must stay repeatable, offline, and away from user files."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

import pytest


ROOT = Path(__file__).resolve().parent.parent


def test_offline_demo_repeats_real_results_without_user_vault_or_network(tmp_path):
    # Catch accidental use of the configured vault, network, or .env while
    # exercising real calculations, bundled reference data, and on-disk state.
    personal_vault = tmp_path / "personal-vault"
    personal_vault.mkdir()
    sentinel = personal_vault / "keep.md"
    sentinel.write_text("Private campaign: leave unchanged.\n", encoding="utf-8")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("OPENAI_")}
    env.update(DND5E_VAULT=str(personal_vault), TMP=str(scratch),
               TEMP=str(scratch), TMPDIR=str(scratch))
    guard = textwrap.dedent("""\
        import os
        from pathlib import Path
        import runpy
        import sys

        def guard(event, args):
            if event.startswith("socket."):
                raise RuntimeError("The offline demo attempted network access")
            if event == "import" and args[0] in {"dnd5e_engine.config", "dotenv", "openai"}:
                raise RuntimeError("The offline demo imported optional configuration or API code")
            if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
                if os.path.basename(os.fsdecode(args[0])) == ".env":
                    raise RuntimeError("The offline demo attempted to load .env")
                write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
                if args[2] & write_flags:
                    if not Path(os.fsdecode(args[0])).resolve().is_relative_to(Path(os.environ["TMP"])):
                        raise RuntimeError("The offline demo wrote outside its temporary folder")

        sys.addaudithook(guard)
        runpy.run_module("scripts.demo_offline", run_name="__main__")
    """)
    guarded = subprocess.run([sys.executable, "-B", "-c", guard], cwd=ROOT,
                             env=env, capture_output=True, text=True, timeout=30)
    assert guarded.returncode == 0, guarded.stderr
    repeated = subprocess.run([sys.executable, "-B", "-m", "scripts.demo_offline"],
                              cwd=ROOT, env=env, capture_output=True,
                              text=True, timeout=30)
    assert repeated.returncode == 0, repeated.stderr
    assert guarded.stdout == repeated.stdout
    result = json.loads(guarded.stdout)

    attack = result["calculations"]["attack"]
    assert attack["d20_rolls"] == [7, 18]
    assert (attack["total"], attack["target_ac"], attack["hit"]) == (23, 15, True)
    assert result["calculations"]["damage"]["total"] == 7
    assert result["calculations"]["spell_save_dc"] == 13
    budget = result["calculations"]["encounter"]
    assert (budget["raw_xp"], budget["multiplier"], budget["adjusted_xp"],
            budget["band"]) == (150, 2, 300, "hard")

    monster = result["lookup"]["monster"]
    assert (monster["name"], monster["cr"], monster["ac"], monster["hp"]) == (
        "Goblin", 0.25, 15, 7)
    assert monster["citation"] == {
        "source": "SRD 5.1", "license": "CC-BY-4.0", "ref": "/api/2014/monsters/goblin"}
    spell = result["lookup"]["spell"]
    assert (spell["name"], spell["level"], spell["range"]) == ("Fireball", 3, "150 feet")
    assert result["lookup"]["missing_monster_found"] is False

    campaign = result["campaign"]
    assert (campaign["round"], campaign["turn_index"]) == (1, 1)
    assert campaign["combatants"] == [
        {"name": "Ranger", "hp": {"value": 10, "max": 12, "temp": 0}, "status": "ok"},
        {"name": "Goblin", "hp": {"value": 0, "max": 7, "temp": 0}, "status": "down"},
    ]
    assert campaign["world_flags"] == {"bridge_open": True, "goblin_defeated": True}
    assert campaign["notes_written"] == 2
    assert campaign["temporary_vault_removed"] is True
    assert list(scratch.iterdir()) == []
    assert list(personal_vault.iterdir()) == [sentinel]
    assert sentinel.read_text(encoding="utf-8") == "Private campaign: leave unchanged.\n"


@pytest.mark.parametrize("missing", ["5e-SRD-Monsters.json", "5e-SRD-Spells.json", "term_map.json"])
def test_missing_demo_data_gives_an_actionable_error_before_campaign_writes(tmp_path, monkeypatch, missing):
    # Catch a missing reference file becoming a KeyError, a misleading
    # found=false result, or a request to an external data service.
    from scripts import demo_offline

    (tmp_path / "srd_2014").mkdir()
    for filename in ("5e-SRD-Monsters.json", "5e-SRD-Spells.json", "term_map.json"):
        relative = Path(filename) if filename == "term_map.json" else Path("srd_2014") / filename
        if filename != missing:
            shutil.copyfile(ROOT / "data" / relative, tmp_path / relative)
    monkeypatch.setattr(demo_offline, "DATA_DIR", tmp_path)
    def unexpected_campaign(*args, **kwargs):
        pytest.fail("Campaign creation attempted before missing data was reported")
    monkeypatch.setattr(demo_offline, "TemporaryDirectory", unexpected_campaign)
    with pytest.raises(FileNotFoundError, match="Restore the tracked data/ files"):
        demo_offline.run_demo()
