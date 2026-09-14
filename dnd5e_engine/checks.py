"""Ability/skill/save checks, attack resolution, and damage rolls."""

from __future__ import annotations

from dnd5e_engine import dice


def resolve_check(modifier: int, dc: int, proficiency_bonus: int = 0,
                  advantage: bool = False, disadvantage: bool = False, rng=None) -> dict:
    """Resolve a d20 ability/skill/save check vs a DC. Natural 20/1 do NOT
    auto-succeed/fail on checks (only on attacks)."""
    nat, rolls, _ = dice.roll_d20(modifier=0, advantage=advantage, disadvantage=disadvantage, rng=rng)
    total = nat + modifier + proficiency_bonus
    return {
        "d20": nat,
        "d20_rolls": rolls,
        "modifier": modifier,
        "proficiency_bonus": proficiency_bonus,
        "total": total,
        "dc": dc,
        "success": total >= dc,
        "breakdown": f"d20({nat}) + mod({modifier}) + prof({proficiency_bonus}) = {total} vs DC {dc}",
    }


def resolve_attack(attack_bonus: int, target_ac: int,
                   advantage: bool = False, disadvantage: bool = False, rng=None) -> dict:
    """Resolve an attack roll. Nat 20 = automatic hit + critical; nat 1 =
    automatic miss."""
    nat, rolls, _ = dice.roll_d20(modifier=0, advantage=advantage, disadvantage=disadvantage, rng=rng)
    total = nat + attack_bonus
    if nat == 20:
        hit, crit = True, True
    elif nat == 1:
        hit, crit = False, False
    else:
        hit, crit = total >= target_ac, False
    return {
        "d20": nat,
        "d20_rolls": rolls,
        "attack_bonus": attack_bonus,
        "total": total,
        "target_ac": target_ac,
        "hit": hit,
        "crit": crit,
        "breakdown": f"d20({nat}) + atk({attack_bonus}) = {total} vs AC {target_ac}",
    }


def roll_damage(notation: str, modifier: int = 0, crit: bool = False, rng=None) -> dict:
    """Roll damage. On a critical hit the dice are doubled; flat modifiers are
    added once. Respects BOTH a modifier embedded in `notation` (e.g. '1d8+5')
    and the separate `modifier` argument. Delegates dice math to
    dice.roll_notation so the crit rule lives in one place."""
    roll = dice.roll_notation(notation, rng=rng, crit=crit)
    total = roll.total + modifier
    return {
        "notation": notation,
        "rolls": roll.rolls,
        "modifier": modifier,
        "notation_modifier": roll.modifier,
        "crit": crit,
        "total": total,
        "breakdown": f"{'+'.join(map(str, roll.rolls))} + notation_mod({roll.modifier}) + mod({modifier}) = {total}",
    }
