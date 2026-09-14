from dnd5e_engine import checks


def test_resolve_check_success(fake_rng):
    r = checks.resolve_check(modifier=3, dc=15, proficiency_bonus=2, rng=fake_rng([12]))
    assert r["d20"] == 12
    assert r["total"] == 17  # 12 + 3 + 2
    assert r["success"] is True


def test_resolve_check_failure(fake_rng):
    r = checks.resolve_check(modifier=0, dc=15, rng=fake_rng([8]))
    assert r["total"] == 8
    assert r["success"] is False


def test_resolve_check_no_auto_success_on_nat20(fake_rng):
    # Ability checks: nat 20 is NOT an automatic success in 5e.
    r = checks.resolve_check(modifier=-5, dc=30, rng=fake_rng([20]))
    assert r["d20"] == 20
    assert r["total"] == 15
    assert r["success"] is False


def test_resolve_attack_nat20_is_crit_hit(fake_rng):
    r = checks.resolve_attack(attack_bonus=0, target_ac=99, rng=fake_rng([20]))
    assert r["hit"] is True
    assert r["crit"] is True


def test_resolve_attack_nat1_is_auto_miss(fake_rng):
    r = checks.resolve_attack(attack_bonus=100, target_ac=1, rng=fake_rng([1]))
    assert r["hit"] is False
    assert r["crit"] is False


def test_resolve_attack_normal_hit(fake_rng):
    r = checks.resolve_attack(attack_bonus=5, target_ac=15, rng=fake_rng([10]))
    assert r["total"] == 15
    assert r["hit"] is True
    assert r["crit"] is False


def test_roll_damage_crit_doubles_dice(fake_rng):
    r = checks.roll_damage(notation="2d6", modifier=3, crit=True, rng=fake_rng([6, 6, 6, 6]))
    assert r["rolls"] == [6, 6, 6, 6]  # 2d6 doubled to 4d6
    assert r["total"] == 27  # 24 + 3


def test_roll_damage_no_crit(fake_rng):
    r = checks.roll_damage("2d6", modifier=3, rng=fake_rng([4, 5]))
    assert r["rolls"] == [4, 5]
    assert r["total"] == 12  # 9 + 3


def test_roll_damage_respects_embedded_modifier(fake_rng):
    r = checks.roll_damage("1d6+2", rng=fake_rng([4]))
    assert r["rolls"] == [4]
    assert r["total"] == 6  # 4 + 2 embedded


def test_roll_damage_embedded_and_separate_modifier(fake_rng):
    r = checks.roll_damage("1d6+2", modifier=1, rng=fake_rng([4]))
    assert r["total"] == 7  # 4 + 2 embedded + 1 separate


def test_resolve_attack_advantage_path(fake_rng):
    r = checks.resolve_attack(attack_bonus=0, target_ac=10, advantage=True, rng=fake_rng([3, 19]))
    assert r["d20_rolls"] == [3, 19]
    assert r["d20"] == 19
    assert r["hit"] is True


def test_resolve_attack_normal_miss(fake_rng):
    r = checks.resolve_attack(attack_bonus=0, target_ac=20, rng=fake_rng([10]))
    assert r["total"] == 10
    assert r["hit"] is False
    assert r["crit"] is False
