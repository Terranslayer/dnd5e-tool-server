from dnd5e_engine import spellcasting


def test_spell_save_dc():
    # 8 + proficiency + ability modifier
    assert spellcasting.spell_save_dc(ability_mod=4, proficiency_bonus=3) == 15


def test_spell_attack_bonus():
    assert spellcasting.spell_attack_bonus(ability_mod=4, proficiency_bonus=3) == 7
