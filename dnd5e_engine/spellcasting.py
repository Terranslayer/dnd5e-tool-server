"""Spellcasting derived numbers (SRD: 8 + prof + mod / prof + mod)."""

from __future__ import annotations


def spell_save_dc(ability_mod: int, proficiency_bonus: int) -> int:
    return 8 + proficiency_bonus + ability_mod


def spell_attack_bonus(ability_mod: int, proficiency_bonus: int) -> int:
    return proficiency_bonus + ability_mod
