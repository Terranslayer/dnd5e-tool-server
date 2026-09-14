import pytest

from dnd5e_engine import dice


def test_parse_basic():
    assert dice.parse("2d6+3") == (2, 6, 3)
    assert dice.parse("d20") == (1, 20, 0)
    assert dice.parse("1d8 - 1") == (1, 8, -1)


def test_parse_invalid():
    with pytest.raises(ValueError):
        dice.parse("banana")


def test_roll_notation_uses_rng(fake_rng):
    r = dice.roll_notation("2d6+3", rng=fake_rng([4, 5]))
    assert r.rolls == [4, 5]
    assert r.modifier == 3
    assert r.total == 12


def test_roll_notation_crit_doubles_dice_only(fake_rng):
    r = dice.roll_notation("1d8+3", rng=fake_rng([8, 8]), crit=True)
    assert r.rolls == [8, 8]
    assert r.total == 19


def test_roll_d20_plain(fake_rng):
    nat, rolls, total = dice.roll_d20(modifier=5, rng=fake_rng([15]))
    assert nat == 15 and rolls == [15] and total == 20


def test_roll_d20_advantage_takes_higher(fake_rng):
    nat, rolls, total = dice.roll_d20(modifier=2, advantage=True, rng=fake_rng([7, 18]))
    assert nat == 18 and rolls == [7, 18] and total == 20


def test_roll_d20_disadvantage_takes_lower(fake_rng):
    nat, rolls, total = dice.roll_d20(modifier=0, disadvantage=True, rng=fake_rng([7, 18]))
    assert nat == 7 and rolls == [7, 18] and total == 7


def test_roll_d20_advantage_and_disadvantage_cancel(fake_rng):
    nat, rolls, total = dice.roll_d20(modifier=0, advantage=True, disadvantage=True, rng=fake_rng([11]))
    assert rolls == [11]  # single d20, they cancel
