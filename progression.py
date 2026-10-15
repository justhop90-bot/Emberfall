"""Sparks & Bonds — progression data and pure logic (no arcade, no Game).

Sparks  = hero talent drafts (levels 2/3/5) + Feat-or-ASI (level 4).
Bonds   = Nym/Kael approval ranks (2/4/5) unlocking Duo Techniques.
Tags    = Ember / Iron / Tide Uni(versal counts toward none) / Lone.
          Ember3 / Iron3 / Tide3 / Lone2 grant set bonuses.
Engine glue lives in EmberfallAct1.py (apply_talent, duo execution, modals).
"""
import random

XP_TABLE = [0, 80, 200, 350, 500]  # Act 1: cap level 5 (pre-boss total ~505)
DRAFT_LEVELS = (2, 3, 5)
FEAT_LEVEL = 4

BOND_RANKS = {2: "Friend", 4: "Confidant", 5: "Sworn"}

# tag -> (threshold, label, desc)
TAG_SETS = {
    "Ember": (3, "Wildfire", "Your burns last +2 rounds."),
    "Iron": (3, "Bulwark", "Guarding also heals you +4."),
    "Tide": (3, "Ebb & Flow", "+2 Agility."),
    "Lone": (2, "Salt Heart", "+2 damage, always."),
}

# tid -> spec. pool: class ids, 'any', or 'origin:<id>'.
# Hooks read by engine: see apply_talent() contract in EmberfallAct1.py.
TALENTS = {
    # --- Blade ---
    "keen_edge": {"label": "Keen Edge", "tag": "Iron", "pool": ["blade"], "mp": 0,
                  "desc": "Your Attacks deal +2 damage."},
    "cleave_master": {"label": "Reaper's Arc", "tag": "Iron", "pool": ["blade"], "mp": 0,
                      "desc": "Cleave hits harder (0.9x -> 1.15x)."},
    "ember_edge": {"label": "Ember Edge", "tag": "Ember", "pool": ["blade"], "mp": 0,
                   "desc": "Your Attacks set foes burning."},
    "bulwark": {"label": "Bulwark", "tag": "Iron", "pool": ["blade"], "mp": 0,
                "desc": "Guarding also raises your defense."},
    # --- Channeler ---
    "deep_well": {"label": "Deep Well", "tag": "Tide", "pool": ["channeler"], "mp": 0,
                  "desc": "+8 max MP, refill now."},
    "bright_mind": {"label": "Bright Mind", "tag": "Ember", "pool": ["channeler"], "mp": 0,
                    "desc": "Starbolt hits harder and burns."},
    "mend_circle": {"label": "Mend Circle", "tag": "Tide", "pool": ["channeler"], "mp": 0,
                    "desc": "Mend heals +6 and soothes you +4."},
    "ember_soul": {"label": "Ember Soul", "tag": "Ember", "pool": ["channeler"], "mp": 0,
                   "desc": "Foes you burn, burn longer (+2 rounds)."},
    # --- Wayknife ---
    "first_cut": {"label": "First Cut", "tag": "Tide", "pool": ["wayknife"], "mp": 0,
                  "desc": "Your first strike each battle always crits."},
    "snipe_master": {"label": "Dead Eye", "tag": "Tide", "pool": ["wayknife"], "mp": 0,
                     "desc": "Snipe deals +3 damage."},
    "tideborn": {"label": "Tideborn", "tag": "Tide", "pool": ["wayknife"], "mp": 0,
                 "desc": "+2 Agility, forever."},
    "smoke_master": {"label": "Low Tide", "tag": "Tide", "pool": ["wayknife"], "mp": 0,
                     "desc": "Smoke Veil also cures the party."},
    # --- Universal ---
    "apothecary": {"label": "Apothecary", "tag": "Tide", "pool": "any", "mp": 0,
                   "desc": "Your healing (spells + items) +6."},
    "tough": {"label": "Tough", "tag": "Iron", "pool": "any", "mp": 0,
              "desc": "+10 max HP, heal 10 now."},
    "swift": {"label": "Swift", "tag": "Tide", "pool": "any", "mp": 0,
              "desc": "+2 Agility, forever."},
    "lone_wolf": {"label": "Lone Wolf", "tag": "Lone", "pool": "any", "mp": 0,
                  "desc": "+4 damage while outnumbered."},
    "salt_heart": {"label": "Salt Heart", "tag": "Lone", "pool": "any", "mp": 0,
                   "desc": "+3 damage while above half health."},
    # --- Origin ---
    "rift_scarred": {"label": "Rift-Scarred", "tag": "Tide", "pool": "origin:survivor", "mp": 0,
                     "desc": "Dots wound you half as deep."},
    "drill_sergeant": {"label": "Drill Sergeant", "tag": "Iron", "pool": "origin:warden", "mp": 0,
                       "desc": "War Cry also raises party defense."},
    "scrounge": {"label": "Scrounge", "tag": "Tide", "pool": "origin:stowaway", "mp": 0,
                 "desc": "+10 gold after every victory."},
}

FALLBACK_TALENT = {"label": "Second Wind", "tag": None, "pool": "any", "mp": 0,
                   "desc": "+4 max HP. The Star provides."}

FEATS = {
    "asi_might": {"label": "Mighty Thews (+2 MIGHT)", "desc": "Hit harder, intimidate better."},
    "asi_wit": {"label": "Keen Mind (+2 WIT)", "desc": "Stronger magic, sharper checks."},
    "asi_cunning": {"label": "Quick Fingers (+2 CUNNING)", "desc": "Act sooner, sneak better."},
    "feat_tough": {"label": "Tough", "desc": "+12 max HP, heal 12 now."},
    "feat_startouched": {"label": "Star-Touched", "desc": "Starbolt/Immolate/Spark +0.3 power."},
    "feat_tactician": {"label": "Tactician", "desc": "+2 Agility, escape easier."},
}

DUOS = {
    "nym": {"label": "Starfall Duet", "mp": 6, "with": "Nym",
            "desc": "Starfire falls on ALL foes. Stronger with rank."},
    "kael": {"label": "Phalanx Oath", "mp": 6, "with": "Kael",
             "desc": "The whole party Guards and mends 6."},
}


def tag_counts(talent_ids):
    counts = {}
    for tid in talent_ids:
        spec = TALENTS.get(tid)
        tag = spec.get("tag") if spec else None
        if tag:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def active_sets(talent_ids):
    out = []
    counts = tag_counts(talent_ids)
    for tag, (need, label, _desc) in TAG_SETS.items():
        if counts.get(tag, 0) >= need:
            out.append((tag, label))
    return out


def bond_rank(approval, peacemaker=False):
    eff = approval + (1 if peacemaker else 0)
    rank = 0
    for need in sorted(BOND_RANKS):
        if eff >= need:
            rank = need
    return rank


def draft_pool(class_id, origin_id, taken):
    pool = []
    for tid, spec in TALENTS.items():
        if tid in taken:
            continue
        p = spec["pool"]
        if p == "any" or class_id in p or p == f"origin:{origin_id}":
            pool.append(tid)
    return pool


def draft_offer(class_id, origin_id, taken, k=3, rng=None):
    rng = rng or random
    pool = draft_pool(class_id, origin_id, taken)
    rng.shuffle(pool)
    return pool[:k]


def duo_power(companion, rank):
    if companion == "nym":
        return 1.2 + 0.15 * rank
    return 0.0  # kael duo heals/guards instead of damage
