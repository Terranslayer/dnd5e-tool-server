"""Download the 25 SRD 5.1 (2014) JSON files from 5e-bits/5e-database into
data/srd_2014/. Run once: `uv run python scripts/fetch_srd.py`.

Content: SRD 5.1 by Wizards of the Coast, licensed under CC-BY-4.0.
See data/srd_2014/ATTRIBUTION.txt."""

from __future__ import annotations

import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/5e-bits/5e-database/main/src/2014/en"
FILES = [
    "5e-SRD-Ability-Scores.json", "5e-SRD-Alignments.json", "5e-SRD-Backgrounds.json",
    "5e-SRD-Classes.json", "5e-SRD-Conditions.json", "5e-SRD-Damage-Types.json",
    "5e-SRD-Equipment-Categories.json", "5e-SRD-Equipment.json", "5e-SRD-Feats.json",
    "5e-SRD-Features.json", "5e-SRD-Languages.json", "5e-SRD-Levels.json",
    "5e-SRD-Magic-Items.json", "5e-SRD-Magic-Schools.json", "5e-SRD-Monsters.json",
    "5e-SRD-Proficiencies.json", "5e-SRD-Races.json", "5e-SRD-Rule-Sections.json",
    "5e-SRD-Rules.json", "5e-SRD-Skills.json", "5e-SRD-Spells.json",
    "5e-SRD-Subclasses.json", "5e-SRD-Subraces.json", "5e-SRD-Traits.json",
    "5e-SRD-Weapon-Properties.json",
]

ATTRIBUTION = (
    'This work includes material taken from the System Reference Document 5.1 '
    '("SRD 5.1") by Wizards of the Coast LLC and available at '
    "https://dnd.wizards.com/resources/systems-reference-document. The SRD 5.1 is "
    "licensed under the Creative Commons Attribution 4.0 International License available at "
    "https://creativecommons.org/licenses/by/4.0/legalcode.\n"
)


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "data" / "srd_2014"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ATTRIBUTION.txt").write_text(ATTRIBUTION, encoding="utf-8")
    for name in FILES:
        url = f"{BASE}/{name}"
        dest = out / name
        print(f"downloading {name} ...")
        with urllib.request.urlopen(url) as resp:
            dest.write_bytes(resp.read())
    print(f"done: {len(FILES)} files -> {out}")


if __name__ == "__main__":
    main()
