"""DnD 5e (2014 / SRD 5.1) encounter math: CR<->XP, XP thresholds, and the
encounter difficulty multiplier. All tables are hard-coded from the 2014 DMG
so the model never has to compute them."""

from __future__ import annotations

# CR -> XP (2014 DMG). CR 0 is treated as 10 XP (a no-attack CR 0 is 0, handled
# by callers if needed).
CR_TO_XP: dict[str, int] = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800, "6": 2300, "7": 2900,
    "8": 3900, "9": 5000, "10": 5900, "11": 7200, "12": 8400, "13": 10000,
    "14": 11500, "15": 13000, "16": 15000, "17": 18000, "18": 20000,
    "19": 22000, "20": 25000, "21": 33000, "22": 41000, "23": 50000,
    "24": 62000, "25": 75000, "26": 90000, "27": 105000, "28": 120000,
    "29": 135000, "30": 155000,
}

# XP thresholds per CHARACTER level (2014 DMG): level -> (easy, medium, hard, deadly)
XP_THRESHOLDS: dict[int, tuple[int, int, int, int]] = {
    1: (25, 50, 75, 100), 2: (50, 100, 150, 200), 3: (75, 150, 225, 400),
    4: (125, 250, 375, 500), 5: (250, 500, 750, 1100), 6: (300, 600, 900, 1400),
    7: (350, 750, 1100, 1700), 8: (450, 900, 1400, 2100), 9: (550, 1100, 1600, 2400),
    10: (600, 1200, 1900, 2800), 11: (800, 1600, 2400, 3600), 12: (1000, 2000, 3000, 4500),
    13: (1100, 2200, 3400, 5100), 14: (1250, 2500, 3800, 5700), 15: (1400, 2800, 4300, 6400),
    16: (1600, 3200, 4800, 7200), 17: (2000, 3900, 5900, 8800), 18: (2100, 4200, 6300, 9500),
    19: (2400, 4900, 7300, 10900), 20: (2800, 5700, 8500, 12700),
}

_DIFFICULTY_INDEX = {"easy": 0, "medium": 1, "hard": 2, "deadly": 3}
_MULTIPLIER_SEQUENCE = [1, 1.5, 2, 2.5, 3, 4]


def _normalize_cr(cr) -> str:
    """Accept int/float/str CR and return the canonical string key."""
    if isinstance(cr, str):
        return cr.strip()
    if cr == 0.125:
        return "1/8"
    if cr == 0.25:
        return "1/4"
    if cr == 0.5:
        return "1/2"
    if float(cr).is_integer():
        return str(int(cr))
    raise ValueError(f"unknown CR: {cr!r}")


def cr_to_xp(cr) -> int:
    key = _normalize_cr(cr)
    if key not in CR_TO_XP:
        raise ValueError(f"unknown CR: {cr!r}")
    return CR_TO_XP[key]


def cr_to_float(cr) -> float:
    """Normalize a CR (str/int/float, incl. '1/8','1/4','1/2') to a float for comparison."""
    if isinstance(cr, (int, float)):
        return float(cr)
    s = str(cr).strip()
    fractions = {"1/8": 0.125, "1/4": 0.25, "1/2": 0.5}
    if s in fractions:
        return fractions[s]
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"unknown CR: {cr!r}")


def xp_to_cr(xp: int) -> str:
    for cr, value in CR_TO_XP.items():
        if value == xp:
            return cr
    raise ValueError(f"no CR with exactly {xp} XP")


def encounter_budget(party_levels: list[int], difficulty: str = "medium") -> dict:
    if difficulty not in _DIFFICULTY_INDEX:
        raise ValueError(f"difficulty must be one of {list(_DIFFICULTY_INDEX)}")
    idx = _DIFFICULTY_INDEX[difficulty]
    per_character = [XP_THRESHOLDS[level][idx] for level in party_levels]
    return {
        "difficulty": difficulty,
        "per_character": per_character,
        "budget": sum(per_character),
    }


def _multiplier_index_for_count(monster_count: int) -> int:
    if monster_count <= 1:
        return 0
    if monster_count == 2:
        return 1
    if 3 <= monster_count <= 6:
        return 2
    if 7 <= monster_count <= 10:
        return 3
    if 11 <= monster_count <= 14:
        return 4
    return 5  # 15+


def encounter_multiplier(monster_count: int, party_size: int) -> float:
    idx = _multiplier_index_for_count(monster_count)
    if party_size < 3:
        idx = min(idx + 1, len(_MULTIPLIER_SEQUENCE) - 1)
    elif party_size >= 6:
        idx = max(idx - 1, 0)
    return _MULTIPLIER_SEQUENCE[idx]


def evaluate_encounter(party_levels: list[int], monsters: list[dict], ruleset: str = "2014") -> dict:
    """Evaluate encounter difficulty. monsters: [{"cr": ..., "count": n} or
    {"xp": ..., "count": n}]."""
    if ruleset != "2014":
        raise NotImplementedError(
            f"encounter math for ruleset {ruleset!r} not implemented; only '2014' is supported"
        )
    raw_xp = 0
    monster_count = 0
    for m in monsters:
        count = int(m.get("count", 1))
        xp = int(m["xp"]) if "xp" in m else cr_to_xp(m["cr"])
        raw_xp += xp * count
        monster_count += count

    party_size = len(party_levels)
    multiplier = encounter_multiplier(monster_count, party_size)
    adjusted_xp = int(raw_xp * multiplier)

    thresholds = {d: encounter_budget(party_levels, d)["budget"]
                  for d in ("easy", "medium", "hard", "deadly")}
    if adjusted_xp >= thresholds["deadly"]:
        band = "deadly"
    elif adjusted_xp >= thresholds["hard"]:
        band = "hard"
    elif adjusted_xp >= thresholds["medium"]:
        band = "medium"
    elif adjusted_xp >= thresholds["easy"]:
        band = "easy"
    else:
        band = "trivial"

    return {
        "ruleset": "2014",
        "raw_xp": raw_xp,
        "monster_count": monster_count,
        "party_size": party_size,
        "multiplier": multiplier,
        "adjusted_xp": adjusted_xp,
        "thresholds": thresholds,
        "band": band,
    }
