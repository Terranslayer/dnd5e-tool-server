# Offline demo: from tool inputs to saved campaign state

This example runs real rule calculations, SRD lookup, and campaign persistence with fixed inputs. It needs no model or API key and does not read `.env` or `DND5E_VAULT`. The entry point is [`scripts/demo_offline.py`](../scripts/demo_offline.py).

## Run it

From the repository root, with Python 3.12+ and `uv` installed:

```bash
uv sync --frozen
uv run --offline --no-sync python -B -m scripts.demo_offline
```

Dependency setup may use the internet. After setup, the second command disables `uv` network access and avoids dependency synchronization; the demo itself makes no network requests. If the project environment is already active, the equivalent command is:

```bash
python -B -m scripts.demo_offline
```

The checkout includes `data/srd_2014/` and `data/term_map.json`. No fetch or index build is needed. If files are missing, restore those tracked files from the same revision. The optional `scripts/fetch_srd.py` downloads a newer snapshot from upstream `main` and can change the reference data. The demo never fetches automatically.

The SRD content retains its attribution in [`data/srd_2014/ATTRIBUTION.txt`](../data/srd_2014/ATTRIBUTION.txt). Lookup results carry the source, license, and an API-relative reference such as `/api/2014/monsters/goblin`; that reference is returned as provenance, not requested over the network.

## Expected results

The command prints one JSON report and exits. Repeated runs on the included data print the same report. Dice faces are supplied explicitly; generated note IDs and temporary directory names are omitted from the report.

| Case | Fixed input | Result |
|---|---|---|
| Monster lookup | `goblin` | Goblin, CR 1/4, AC 15, HP 7, SRD 5.1 citation |
| Spell lookup | `fireball` | Level 3, range 150 feet, SRD 5.1 citation |
| Missing lookup | `beholder` | `missing_monster_found: false` |
| Attack with advantage | d20 faces 7 and 18; attack bonus 5; AC from Goblin lookup | Keep 18; total 23; hit; no critical hit |
| Damage | `1d6+3`; die face 4 | 7 damage |
| Spell save DC | Ability modifier 3; proficiency bonus 2 | 8 + 3 + 2 = 13 |
| Encounter budget | Four level-1 characters; three CR 1/4 goblins | 150 raw XP; multiplier 2; 300 adjusted XP; hard |
| Temporary HP | Ranger starts at 12/12 HP plus 3 temporary HP; takes 5 damage | 10/12 HP; 0 temporary HP |
| Goblin HP | Starts at 7/7; takes the calculated 7 damage | 0/7 HP; `status: down` |
| Persistence | Save an encounter and two successive campaign flag patches; reload files | Both flags retained; round 1; turn index 1; two Markdown files |
| Cleanup | Leave the temporary directory context | `temporary_vault_removed: true` |

The budget example and the saved two-combatant example are separate demonstrations. This is not a full battle simulation. Advancing the turn moves the stored cursor; this example does not automatically skip a downed combatant.

## Follow the data through the code

The flow is **inputs → rule functions or lookup service → structured result → optional state write → readback**.

1. **Choose the action.** In a live MCP session, [`server.py`](../dnd5e_engine/server.py) exposes named tools such as `resolve_attack`, `lookup_monster`, and `apply_hp_change`. Most wrappers delegate to another module. This demo calls those underlying implementations directly so it can inject dice faces and an isolated vault path without loading server configuration. It does not test the MCP transport or a model choosing tools.
2. **Validate the relevant input.** [`dice.py`](../dnd5e_engine/dice.py) parses notation and rejects malformed expressions or non-positive dice counts/sides. The demo's `ScriptedRolls.randint` checks that each supplied face is within the requested die range. [`encounter.py`](../dnd5e_engine/encounter.py) rejects unsupported rulesets. These are specific checks, not comprehensive validation of every possible tool argument.
3. **Calculate or retrieve.** [`checks.py`](../dnd5e_engine/checks.py) keeps the higher d20 for advantage, adds the bonus, and compares with AC. [`spellcasting.py`](../dnd5e_engine/spellcasting.py) computes the spell DC; [`encounter.py`](../dnd5e_engine/encounter.py) applies the 2014 XP tables. [`data.py`](../dnd5e_engine/data.py) loads local JSON, and [`lookup.py`](../dnd5e_engine/lookup.py) returns an entry plus citation or `found: false`. A citation identifies the stored source; it is not a live verification of that source.
4. **Write within the chosen vault.** [`state.py`](../dnd5e_engine/state.py) sorts combatants, applies damage to temporary HP first, and writes YAML frontmatter through [`notes.py`](../dnd5e_engine/notes.py). Names are sanitized for filenames; `StateService._write` resolves its destination and checks that it stays inside the configured root. In this demo that root is a newly created `TemporaryDirectory`, passed explicitly rather than obtained from personal settings.
5. **Read back and clean up.** A new `StateService` loads the saved Markdown, demonstrating persistence beyond one service object. Campaign `world_flags` merge across updates. The report is built from the reloaded state, and the temporary folder is removed when the context exits. Only the JSON printed to the terminal remains.

Normal dice calls use randomness when no RNG is supplied. Repeatability here comes from the explicit dice faces, fixed inputs, and tracked data; it is not a claim that ordinary game rolls always return the same number.

## Three small exercises

Make one change at a time in `scripts/demo_offline.py`, predict the result, then rerun the demo. Restore the edited line before the next exercise. The regression test deliberately checks the original example and will fail while these example inputs are changed.

1. Change `advantage=True` to `advantage=False`. The attack uses the first scripted face, 7: 7 + 5 = 12, which misses AC 15. The Goblin stays at 7 HP and `goblin_defeated` becomes false. The damage calculation still prints 7, but the state update applies zero damage because the attack missed.
2. Change the party in `evaluate_encounter` from `[1, 1, 1, 1]` to `[1, 1]`. Raw XP remains 150; the small-party multiplier rises to 2.5, giving 375 adjusted XP and a deadly classification. The saved Ranger/Goblin example stays the same because it is a separate case.
3. Change the Ranger's fixed damage event from `-5` to `-20`. The 3 temporary HP absorb the first 3 damage, regular HP falls to zero rather than becoming negative, and the Ranger is marked down.

## What the checks establish

```bash
uv run --offline --no-sync pytest tests/test_demo_offline.py
uv run --offline --no-sync pytest
```

[`tests/test_demo_offline.py`](../tests/test_demo_offline.py) runs the actual example in a subprocess, compares repeated reports, and checks hand-derived results from the bundled data. A guarded run rejects Python socket operations, optional configuration/API imports, `.env` reads, and file writes outside the test's temporary folder. A sentinel personal-vault file remains unchanged, and temporary campaign files are gone after the run. Missing required data produces an actionable error before campaign creation.

These are regression checks for this fixed workflow. They do not establish resistance to arbitrary prompt injection, comprehensive filesystem security, concurrent campaign editing, or improved model performance. No live LLM evaluation or model-only baseline comparison has been run for this demo.
