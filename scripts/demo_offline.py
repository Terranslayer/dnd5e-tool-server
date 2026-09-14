"""Run a repeatable example with bundled SRD data and a disposable campaign.

From the repository root: python -m scripts.demo_offline
This calls the core implementations behind MCP tools, without importing the
server (which loads .env) or starting an MCP client or model.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from dnd5e_engine import checks, encounter, spellcasting
from dnd5e_engine.data import SRDData
from dnd5e_engine.lookup import LookupService
from dnd5e_engine.state import StateService
from dnd5e_engine.terms import TermMap


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ScriptedRolls:
    """Supply explicit dice faces through the engine's existing RNG interface."""

    def __init__(self, *values: int):
        self.values = iter(values)

    def randint(self, low: int, high: int) -> int:
        value = next(self.values)
        if not low <= value <= high:
            raise ValueError(f"scripted roll {value} outside [{low}, {high}]")
        return value


def run_demo() -> dict:
    required = ("srd_2014/5e-SRD-Monsters.json", "srd_2014/5e-SRD-Spells.json", "term_map.json")
    missing = [name for name in required if not (DATA_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing demo data: {', '.join(missing)}. "
            "Restore the tracked data/ files from this checkout; see docs/offline-demo.md. "
            "The demo does not download data automatically.")
    lookup = LookupService(SRDData.load(DATA_DIR / "srd_2014"),
                           TermMap.load(DATA_DIR / "term_map.json"))
    monster = lookup.lookup_monster("goblin")
    spell = lookup.lookup_spell("fireball")
    goblin = monster["entry"]
    goblin_ac = goblin["armor_class"][0]["value"]

    # Fixed dice faces make the example independent of random seeds and luck.
    attack = checks.resolve_attack(5, goblin_ac, advantage=True,
                                    rng=ScriptedRolls(7, 18))
    damage = checks.roll_damage("1d6+3", crit=attack["crit"], rng=ScriptedRolls(4))
    budget = encounter.evaluate_encounter(
        [1, 1, 1, 1], [{"cr": goblin["challenge_rating"], "count": 3}])

    # Pass the temporary root explicitly; never read DND5E_VAULT or .env.
    # The budget above and the two-combatant state example are separate cases.
    with TemporaryDirectory(prefix="dnd5e-demo-") as temporary_vault:
        state = StateService(temporary_vault)
        campaign, name = "Offline Demo", "Bridge skirmish"
        started = state.start_encounter(campaign, name, [
            {"name": "Goblin", "side": "enemy", "initiative": 10, "ac": goblin_ac,
             "hp": {"value": goblin["hit_points"], "max": goblin["hit_points"]}},
            {"name": "Ranger", "side": "party", "initiative": 18, "ac": 16,
             "hp": {"value": 12, "max": 12, "temp": 3}},
        ])
        combatant_ids = {c["name"]: c["id"] for c in started["combatants"]}
        goblin_after = state.apply_hp_change(
            campaign, name, combatant_ids["Goblin"], -damage["total"] if attack["hit"] else 0)
        # A separate fixed damage event illustrates temporary HP absorption.
        state.apply_hp_change(campaign, name, combatant_ids["Ranger"], -5)
        state.manage_combat_state(campaign, name, advance_turn=True)
        state.update_campaign_state(campaign, patch={"world_flags": {"bridge_open": True}})
        state.update_campaign_state(campaign, patch={
            "world_flags": {"goblin_defeated": goblin_after["status"] == "down"}})

        # A fresh service reads the actual Markdown files back from disk.
        context = StateService(temporary_vault).load_play_context(campaign)
        saved = context["active_encounters"][0]
        campaign_result = {
            "name": campaign,
            "round": saved["round"],
            "turn_index": saved["turn_index"],
            "combatants": [{"name": c["name"], "hp": c["hp"], "status": c["status"]}
                           for c in saved["combatants"]],
            "world_flags": context["state"]["world_flags"],
            "notes_written": len(list(Path(temporary_vault).rglob("*.md"))),
        }
    campaign_result["temporary_vault_removed"] = not Path(temporary_vault).exists()

    # UUIDs and the temporary path are deliberately absent from the report.
    return {
        "lookup": {
            "monster": {"name": monster["name_en"], "cr": goblin["challenge_rating"],
                        "ac": goblin_ac, "hp": goblin["hit_points"],
                        "citation": monster["citation"]},
            "spell": {"name": spell["name_en"], "level": spell["entry"]["level"],
                      "range": spell["entry"]["range"], "citation": spell["citation"]},
            "missing_monster_found": lookup.lookup_monster("beholder")["found"],
        },
        "calculations": {"attack": attack, "damage": damage, "encounter": budget,
                         "spell_save_dc": spellcasting.spell_save_dc(3, 2)},
        "campaign": campaign_result,
    }


def main() -> None:
    print(json.dumps(run_demo(), indent=2))


if __name__ == "__main__":
    main()
