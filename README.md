# Emberfall — Act 1: The Light Below

A party-based tactical CRPG in the spirit of Baldur's Gate, built with Python + Arcade. Original world, original rules.

- 1 hero (forged: origin + class + name) + 2 companions (Nym, Kael)
- 5 quests, 4 turn-based menu battles (Attack / Skill / Spell / Item / Guard / Flee / Duo), levels 1–5
- Sparks & Bonds progression: talent drafts, feats, tag sets, companion duos sealed at campfires
- d20 skill checks, branching dialogue, approval that remembers

## Run

```
pip install arcade pygame pillow numpy pytest
python EmberfallAct1.py
```

| Keys | Action |
|---|---|
| WASD / Arrows | Move |
| E | Interact |
| J / K | Journal / Character sheet |
| B | Bandage |
| M / N / P | Sound / Music / Sound test |
| F5 / F9 | Save / Load |
| Battle | Up-Down + Enter, 1-6 shortcuts, Esc backs out |

## Test

```
python -m pytest tests/ -q
```

## Assets

All CC0: [Kenney](https://kenney.nl) RPG Base + Input Prompts, Google Fonts (Cinzel, Alegreya, OFL). Music/SFX synthesized in-repo.
