"""Deterministic dice engine. All randomness is injected via `rng` (anything
with a .randint(a, b) method) so behavior is fully testable."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

_NOTATION = re.compile(r"^\s*(\d*)\s*[dD]\s*(\d+)\s*([+-]\s*\d+)?\s*$")


@dataclass
class Roll:
    rolls: list[int]
    modifier: int
    total: int


def parse(notation: str) -> tuple[int, int, int]:
    """Parse 'NdM+K' into (count, sides, modifier). Count defaults to 1."""
    m = _NOTATION.match(notation)
    if not m:
        raise ValueError(f"invalid dice notation: {notation!r}")
    count = int(m.group(1)) if m.group(1) else 1
    sides = int(m.group(2))
    modifier = int(m.group(3).replace(" ", "")) if m.group(3) else 0
    if count < 1 or sides < 1:
        raise ValueError(f"dice count/sides must be >= 1: {notation!r}")
    return count, sides, modifier


def _roll_many(count: int, sides: int, rng) -> list[int]:
    return [rng.randint(1, sides) for _ in range(count)]


def roll_notation(notation: str, rng=None, crit: bool = False) -> Roll:
    """Roll an 'NdM+K' expression. On crit the number of dice is doubled
    (5e critical hit rule), the modifier is added once."""
    rng = rng or random.Random()
    count, sides, modifier = parse(notation)
    if crit:
        count *= 2
    rolls = _roll_many(count, sides, rng)
    return Roll(rolls=rolls, modifier=modifier, total=sum(rolls) + modifier)


def roll_d20(modifier: int = 0, advantage: bool = False, disadvantage: bool = False, rng=None):
    """Roll a single d20 check. Advantage and disadvantage cancel out.
    Returns (natural_d20, rolls_list, total)."""
    rng = rng or random.Random()
    if advantage and disadvantage:
        advantage = disadvantage = False
    if advantage or disadvantage:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
        nat = max(a, b) if advantage else min(a, b)
        rolls = [a, b]
    else:
        nat = rng.randint(1, 20)
        rolls = [nat]
    return nat, rolls, nat + modifier
