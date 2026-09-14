import pytest

from dnd5e_engine import encounter


def test_cr_to_xp_known_values():
    assert encounter.cr_to_xp("1/4") == 50
    assert encounter.cr_to_xp(1) == 200
    assert encounter.cr_to_xp("5") == 1800
    assert encounter.cr_to_xp(0.5) == 100  # 0.5 normalizes to "1/2"


def test_cr_to_xp_unknown_raises():
    with pytest.raises(ValueError):
        encounter.cr_to_xp("99")


def test_xp_to_cr_exact():
    assert encounter.xp_to_cr(1800) == "5"
    assert encounter.xp_to_cr(50) == "1/4"


def test_encounter_budget_sums_per_character():
    b = encounter.encounter_budget(party_levels=[1, 1], difficulty="medium")
    assert b["budget"] == 100
    assert b["per_character"] == [50, 50]


def test_encounter_multiplier_by_count_and_party_size():
    assert encounter.encounter_multiplier(monster_count=4, party_size=4) == 2
    assert encounter.encounter_multiplier(monster_count=4, party_size=2) == 2.5
    assert encounter.encounter_multiplier(monster_count=4, party_size=6) == 1.5


def test_evaluate_encounter_2014_band():
    # 4 level-3 PCs vs 4 goblins (CR 1/4 = 50 XP each = 200 raw), x2 multiplier
    # (4 monsters) -> 400 adjusted XP. Level-3 party thresholds:
    # easy 300, medium 600, hard 900, deadly 1600.
    # 400 meets easy(300) but not medium(600) -> an "easy" encounter.
    result = encounter.evaluate_encounter(
        party_levels=[3, 3, 3, 3],
        monsters=[{"cr": "1/4", "count": 4}],
        ruleset="2014",
    )
    assert result["raw_xp"] == 200
    assert result["multiplier"] == 2
    assert result["adjusted_xp"] == 400
    assert result["thresholds"] == {"easy": 300, "medium": 600, "hard": 900, "deadly": 1600}
    assert result["band"] == "easy"


def test_evaluate_encounter_2014_deadly_band():
    # 4 level-1 PCs vs 3 CR-1 monsters: raw 600, x2 (3 monsters) -> 1200 adjusted.
    # Level-1 party thresholds: easy 100, medium 200, hard 300, deadly 400.
    # 1200 >= deadly(400) -> deadly.
    result = encounter.evaluate_encounter([1, 1, 1, 1], [{"cr": 1, "count": 3}], "2014")
    assert result["multiplier"] == 2
    assert result["raw_xp"] == 600
    assert result["adjusted_xp"] == 1200
    assert result["band"] == "deadly"


def test_evaluate_encounter_2014_trivial_band():
    # 4 level-5 PCs (easy threshold 4x250=1000) vs 1 CR-1/8 monster (25 XP), x1.
    # 25 < easy(1000) -> trivial.
    result = encounter.evaluate_encounter([5, 5, 5, 5], [{"cr": "1/8", "count": 1}], "2014")
    assert result["adjusted_xp"] == 25
    assert result["band"] == "trivial"


def test_evaluate_encounter_2024_not_implemented():
    with pytest.raises(NotImplementedError):
        encounter.evaluate_encounter(party_levels=[1], monsters=[{"cr": 1, "count": 1}], ruleset="2024")


def test_cr_to_float():
    assert encounter.cr_to_float("1/4") == 0.25
    assert encounter.cr_to_float("1/8") == 0.125
    assert encounter.cr_to_float("1/2") == 0.5
    assert encounter.cr_to_float(5) == 5.0
    assert encounter.cr_to_float("0.5") == 0.5
    assert encounter.cr_to_float("10") == 10.0


def test_cr_to_float_invalid_raises():
    with pytest.raises(ValueError):
        encounter.cr_to_float("banana")
