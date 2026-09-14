"""StateService：在跑实例层（variants/<变种>/）的状态写入。读-改-写 frontmatter，
权威状态在 frontmatter；不触碰模板层。HP/先攻数学硬编码、不靠模型推断。"""

from __future__ import annotations

from pathlib import Path

from dnd5e_engine import notes


class StateService:
    def __init__(self, root):
        self.root = Path(root)

    # ---- 实例路径 ----
    def _variant_dir(self, campaign: str, variant: str) -> Path:
        return (self.root / notes.CAMPAIGN_ROOT / notes.sanitize_filename(campaign)
                / "variants" / notes.sanitize_filename(variant))

    def _encounter_path(self, campaign: str, name: str, variant: str) -> Path:
        return self._variant_dir(campaign, variant) / "Encounters_遭遇" / (
            notes.sanitize_filename(name) + ".md")

    def _state_path(self, campaign: str, variant: str) -> Path:
        return self._variant_dir(campaign, variant) / "state.md"

    # ---- 读写（带路径穿越防护）----
    def _write(self, dest: Path, fm: dict, body: str = "") -> None:
        if not dest.resolve().is_relative_to(self.root.resolve()):
            raise ValueError(f"path escapes vault root: {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(notes.render_note(fm, body), encoding="utf-8")

    def _read(self, dest: Path) -> tuple[dict, str]:
        if not dest.exists():
            raise FileNotFoundError(str(dest))
        return notes.parse_note(dest.read_text(encoding="utf-8"))

    # ---- 战斗 ----
    def start_encounter(self, campaign, name, combatants, variant="main",
                        terrain="", summary=""):
        if not combatants:
            raise ValueError("combatants list must not be empty")
        cs = []
        for c in combatants:
            hp = dict(c.get("hp", {}))
            cs.append({
                "id": notes.new_id(),
                "ref": c.get("ref", ""),
                "name": c.get("name", ""),
                "side": c.get("side", ""),
                "initiative": c.get("initiative", 0),
                "ac": c.get("ac", 0),
                "hp": {"value": hp.get("value", 0),
                       "max": hp.get("max", hp.get("value", 0)),
                       "temp": hp.get("temp", 0)},
                "conditions": list(c.get("conditions", [])),
                "status": "ok",
            })
        cs.sort(key=lambda x: x["initiative"], reverse=True)
        fm = {"id": notes.new_id(), "type": "encounter", "name": name,
              "campaign": campaign, "variant": variant, "layer": "instance",
              "summary": summary, "terrain": terrain,
              "round": 1, "turn_index": 0, "combatants": cs}
        dest = self._encounter_path(campaign, name, variant)
        self._write(dest, fm)
        return {"path": str(dest.relative_to(self.root)).replace("\\", "/"),
                "round": 1, "turn_index": 0,
                "combatants": [{"id": c["id"], "name": c["name"], "side": c["side"],
                                "initiative": c["initiative"], "hp": c["hp"],
                                "status": c["status"]} for c in cs]}

    def apply_hp_change(self, campaign, encounter, combatant_id, delta, variant="main"):
        dest = self._encounter_path(campaign, encounter, variant)
        fm, body = self._read(dest)
        c = next((x for x in fm["combatants"] if x["id"] == combatant_id), None)
        if c is None:
            raise ValueError(f"combatant not found: {combatant_id}")
        hp = c["hp"]
        if delta < 0:
            dmg = -delta
            from_temp = min(hp.get("temp", 0), dmg)
            hp["temp"] = hp.get("temp", 0) - from_temp
            hp["value"] = max(0, hp["value"] - (dmg - from_temp))
        else:
            hp["value"] = min(hp["max"], hp["value"] + delta)
        c["status"] = "down" if hp["value"] == 0 else "ok"
        self._write(dest, fm, body)
        return {"combatant_id": combatant_id, "name": c["name"], "hp": hp,
                "status": c["status"], "applied": delta}

    def manage_combat_state(self, campaign, encounter, variant="main", advance_turn=False,
                            combatant_id="", set_conditions=None, clear_conditions=None,
                            spell_slots=None):
        dest = self._encounter_path(campaign, encounter, variant)
        fm, body = self._read(dest)
        combs = fm["combatants"]
        if advance_turn:
            ti = fm.get("turn_index", 0) + 1
            if ti >= len(combs):
                ti = 0
                fm["round"] = fm.get("round", 1) + 1
            fm["turn_index"] = ti
        changed = None
        if combatant_id:
            c = next((x for x in combs if x["id"] == combatant_id), None)
            if c is None:
                raise ValueError(f"combatant not found: {combatant_id}")
            if set_conditions:
                for cond in set_conditions:
                    if cond not in c["conditions"]:
                        c["conditions"].append(cond)
            if clear_conditions:
                c["conditions"] = [x for x in c["conditions"] if x not in clear_conditions]
            if spell_slots is not None:
                c["spell_slots"] = spell_slots
            changed = {"id": c["id"], "name": c["name"], "conditions": c["conditions"],
                       "spell_slots": c.get("spell_slots")}
        self._write(dest, fm, body)
        active_idx = fm.get("turn_index", 0)
        active = combs[active_idx] if combs and active_idx < len(combs) else None
        return {"round": fm.get("round", 1), "turn_index": fm.get("turn_index", 0),
                "active_combatant": ({"id": active["id"], "name": active["name"]}
                                     if active else None),
                "changed": changed}

    def load_play_context(self, campaign, variant="main"):
        """开局/续团一次性载入：实例状态(state.md) + 风格档案 + 活动遭遇概要。"""
        from dnd5e_engine.vault import VaultService
        state = {}
        sp = self._state_path(campaign, variant)
        if sp.exists():
            state, _ = self._read(sp)
        active = []
        enc_dir = self._variant_dir(campaign, variant) / "Encounters_遭遇"
        if enc_dir.exists():
            for p in sorted(enc_dir.glob("*.md")):
                fm, _ = notes.parse_note(p.read_text(encoding="utf-8"))
                active.append({
                    "name": fm.get("name"),
                    "round": fm.get("round"),
                    "turn_index": fm.get("turn_index"),
                    "combatants": [{"id": c.get("id"), "name": c.get("name"),
                                    "side": c.get("side"), "status": c.get("status"),
                                    "hp": c.get("hp")} for c in fm.get("combatants", [])],
                })
        style = VaultService(self.root).load_style(campaign)
        return {"campaign": campaign, "variant": variant, "state": state,
                "style": style, "active_encounters": active}

    def update_campaign_state(self, campaign, variant="main", patch=None):
        patch = patch or {}
        dest = self._state_path(campaign, variant)
        if dest.exists():
            fm, body = self._read(dest)
        else:
            fm = {"id": notes.new_id(), "type": "campaign_state", "name": "state",
                  "campaign": campaign, "variant": variant, "layer": "instance"}
            body = ""
        for k, v in patch.items():
            if k == "world_flags":
                if not isinstance(v, dict):
                    raise TypeError(f"world_flags must be a dict, got {type(v).__name__}")
                fm.setdefault("world_flags", {}).update(v)
            else:
                fm[k] = v
        self._write(dest, fm, body)
        return fm
