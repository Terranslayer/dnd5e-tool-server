from pathlib import Path

import pytest

from dnd5e_engine import data

SRD_DIR = Path(__file__).resolve().parent.parent / "data" / "srd_2014"

pytestmark = pytest.mark.skipif(
    not (SRD_DIR / "5e-SRD-Monsters.json").exists(),
    reason="real SRD data not downloaded; run scripts/fetch_srd.py",
)


def test_real_srd_loads_and_has_known_entries():
    srd = data.SRDData.load(SRD_DIR)
    assert srd.get("monsters", "goblin")["name"] == "Goblin"
    assert srd.get("spells", "fireball")["name"] == "Fireball"
    assert srd.get("conditions", "blinded") is not None
    # SRD subset guard: iconic non-SRD monsters must be absent.
    assert srd.get("monsters", "beholder") is None
    assert srd.get("monsters", "mind-flayer") is None
