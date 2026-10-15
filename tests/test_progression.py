"""Validator: Sparks & Bonds tables + progression logic. Run: pytest tests/"""
import random

import progression as P
import EmberfallAct1 as E


def test_tables_sane():
    for tid, spec in P.TALENTS.items():
        assert spec["tag"] in ("Ember", "Iron", "Tide", "Lone", None), tid
        p = spec["pool"]
        assert p == "any" or isinstance(p, list) or p.startswith("origin:"), tid
    for tag, (need, _label, _desc) in P.TAG_SETS.items():
        assert need >= 2, tag
    assert set(P.BOND_RANKS) == {2, 4, 5}
    assert set(P.DRAFT_LEVELS) == {2, 3, 5} and P.FEAT_LEVEL == 4
    assert E.XP_TABLE == P.XP_TABLE


def test_draft_pools():
    rng = random.Random(9)
    for cls in ("blade", "channeler", "wayknife"):
        offer = P.draft_offer(cls, "warden", [], rng=rng)
        assert len(offer) == 3 and len(set(offer)) == 3
        for tid in offer:
            p = P.TALENTS[tid]["pool"]
            assert p == "any" or cls in p or p == "origin:warden", tid
    # taken talents never re-offered
    taken = P.draft_offer("blade", "warden", [], rng=random.Random(2))
    again = P.draft_offer("blade", "warden", taken, rng=random.Random(2))
    assert not set(taken) & set(again)


def test_tag_sets_and_bonds():
    assert P.tag_counts(["keen_edge", "cleave_master", "bulwark"]) == {"Iron": 3}
    assert ("Iron", "Bulwark") in P.active_sets(["keen_edge", "cleave_master", "bulwark"])
    assert ("Ember", "Wildfire") not in P.active_sets(["keen_edge", "ember_edge"])
    assert P.bond_rank(1) == 0 and P.bond_rank(2) == 2 and P.bond_rank(4) == 4 and P.bond_rank(6) == 5
    assert P.bond_rank(4, peacemaker=True) == 5
    assert P.bond_rank(1, peacemaker=True) == 2


def _game():
    import tests.test_combat as T
    return T.make_game("blade", "e1")


def test_talent_apply_and_sets():
    g = _game()
    g.apply_talent("keen_edge")
    g.apply_talent("cleave_master")
    g.apply_talent("bulwark")
    assert ("Iron", "Bulwark") in P.active_sets(["keen_edge", "cleave_master", "bulwark"])
    assert "Iron" in g.tag_sets()
    assert E.ABILITIES["cleave"]["power"] == 1.15
    E.ABILITIES["cleave"]["power"] = 0.9  # restore global for other tests


def test_duo_gating():
    g = _game()
    assert g.duo_available() == []
    g.approval["Nym"] = 4
    assert g.bond_rank("Nym") == 4, "standing is still approval-based"
    assert g.duo_available() == [], "but duos need the sealed scene"
    assert "duo" not in [m[0] for m in g.b_menu(g.combat["allies"][0])]


def test_level_queues_draft_not_instant_power():
    g = _game()
    assert g.pending_drafts == 0 and g.hero_talents == []
    g.gain_xp(200)  # crosses 80 (L2 draft) — table [0,80,200,350,500]
    assert g.level == 3, f"level={g.level}"
    assert g.pending_drafts == 2, f"pending={g.pending_drafts}"
    assert g.hero_talents == [], "drafts must wait for campfire, never auto-grant"


def _camp_stub():
    g = _game()
    g.state = "EXPLORE"
    g.rations = 2
    g.banter_n = 0
    g.tut_spark = False
    g.pending_drafts = 1
    g.pending_feat = False
    return g


def test_duo_locked_until_scene_sealed():
    g = _game()
    g.approval = {"Nym": 6, "Kael": 4}  # devoted Q1 — max before first rest
    assert g.bond_rank("Nym") == 5
    assert g.duo_available() == [], "approval alone must never unlock duos"
    g.bond_seen.add("nym:2")
    assert g.duo_available() == ["nym"]
    g.bond_seen.add("kael:4")
    assert set(g.duo_available()) == {"nym", "kael"}
    assert g.duo_rank("Nym") == 2 and g.duo_rank("Kael") == 4


def test_tutorial_plays_before_bond_scene():
    g = _camp_stub()
    g.approval = {"Nym": 4, "Kael": 0}  # rank 4 scene waiting + draft pending
    g.camp_rest()
    assert g.node == "draft_tut", f"tutorial first, got {g.node}"
    assert "nym:4" not in g.bond_seen, "scene must wait for the next rest"
    g.state = "EXPLORE"  # next rest, after the modal closes
    g.pending_drafts = 0
    g.camp_rest()
    assert g.node == "nym_bond2", f"then scenes play lowest-first, got {g.node}"


def test_flawless_victory_earns_bonds():
    g = _game()
    g.state = "COMBAT"
    g.return_map = "shore"
    g.map_id = "shore"
    g.start_combat("e2")
    for f in g.combat["foes"]:
        f["hp"] = 0
        f["alive"] = False
    n0, k0 = g.approval["Nym"], g.approval["Kael"]
    g.b_finish()
    assert g.approval["Nym"] == n0 + 1 and g.approval["Kael"] == k0 + 1
    # ...but not if someone fell
    g2 = _game()
    g2.state = "COMBAT"
    g2.return_map = "shore"
    g2.map_id = "shore"
    g2.start_combat("e2")
    g2.combat["ally_down"] = True
    for f in g2.combat["foes"]:
        f["hp"] = 0
        f["alive"] = False
    n0, k0 = g2.approval["Nym"], g2.approval["Kael"]
    g2.b_finish()
    assert (g2.approval["Nym"], g2.approval["Kael"]) == (n0, k0)
