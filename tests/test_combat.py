"""Validator: menu-battle tables + headless auto-battle. Run: pytest tests/"""
import random

import EmberfallAct1 as E


def make_game(cls="blade", key="e1"):
    g = E.Game.__new__(E.Game)
    g.class_id = cls
    g.abilities = {"MIGHT": 12, "WIT": 12, "CUNNING": 10}
    g.ac, g.atk = 13, 5
    g.max_hp, g.hp, g.max_mp, g.mp = 34, 34, 16, 16
    g.hero_name = "T"
    g.equip_atk, g.equip_ac = 0, 0
    g.comps = [
        {"name": "Nym", "hp": 18, "max": 18, "mp": 14, "mpmax": 14, "on": True},
        {"name": "Kael", "hp": 26, "max": 26, "mp": 6, "mpmax": 6, "on": True},
    ]
    g.flags, g.quests = {}, {"q1": 2, "q2": 0, "q3": 0, "q4": 0, "q5": 0}
    g.approval = {"Nym": 0, "Kael": 0}
    g.inv = {"bandage": 2, "herb": 1, "oil": 1}
    g.gold, g.xp, g.level = 0, 0, 1
    g.stats = {"kills": 0, "ok": 0, "fail": 0}
    g.map_id, g.return_map, g.state = "shore", "shore", "EXPLORE"
    g.msg, g.msg_t = "", 0
    g.trauma, g.hitstop, g.floaters, g.particles, g.hp_show = 0, 0, [], [], {}
    g.hero_talents, g.pending_drafts, g.pending_feat = [], 0, False
    g.feat, g.bond_seen, g.tut_spark, g.draft_offer = None, set(), True, []
    g.play = lambda n: None
    g.start_music = lambda m: None
    g.origin_id = "warden"
    g.start_combat(key)
    return g


def auto_round(g):
    c = g.combat
    for a in [x for x in c["allies"] if x["alive"]]:
        foes = [i for i, f in enumerate(c["foes"]) if f["alive"]]
        if not foes:
            break
        a["cmd"] = ("attack", None, foes[0])
    g.b_begin_round()
    guard = 0
    while c["stage"] == "resolve" and guard < 40:
        g.b_step()
        guard += 1
        if g.state != "COMBAT":
            break


def test_tables_sane():
    for cls, kit in E.CLASS_KITS.items():
        for ab in kit["skills"] + kit["spells"]:
            assert ab in E.ABILITIES, f"{cls}: unknown ability {ab}"
            d = E.ABILITIES[ab]
            assert d["scope"] in ("foe", "allfoes", "ally", "party", "self"), f"{ab}: bad scope"
            assert d["mp"] >= 0, f"{ab}: negative MP"


def test_menu_lists_match_kits():
    g = make_game("channeler")
    hero = g.combat["allies"][0]
    assert "spell" in [m[0] for m in g.b_menu(hero)]
    g2 = make_game("blade")
    assert "spell" not in [m[0] for m in g2.b_menu(g2.combat["allies"][0])]


def test_auto_battle_winnable():
    random.seed(7)
    g = make_game("blade", "e1")
    for _ in range(12):
        if g.state != "COMBAT":
            break
        auto_round(g)
    assert g.state == "EXPLORE", "e1 basic-attack run should win"
    assert g.xp > 0


def test_spell_mp_deducted_and_heals():
    random.seed(3)
    g = make_game("channeler", "e1")
    hero = g.combat["allies"][0]
    hero["hp"] = 10
    mp0 = hero["mp"]
    hero["cmd"] = ("spell", "mend", 0)
    g.b_begin_round()
    while g.combat["stage"] == "resolve" and g.state == "COMBAT":
        g.b_step()
    assert hero["mp"] < mp0, "mend should cost MP"
    assert hero["hp"] > 10, "mend should heal"


def test_boss_flee_fails_and_fights():
    random.seed(11)
    g = make_game("blade", "boss")
    g.b_flee(g.combat["allies"][0])
    assert not g.combat["fled"], "boss must be inescapable"
    assert g.state == "COMBAT"


def _drive_resolve(g, cap=60):
    c, n = g.combat, 0
    while c["stage"] == "resolve" and n < cap:
        g.b_step()
        n += 1
        if g.state != "COMBAT":
            break


def test_menu_input_two_rounds_deal_damage():
    """Regression: orders locked via b_input must execute as real actions,
    in round 1 AND round 2, for attack / skill / spell / item paths."""
    import arcade

    random.seed(21)
    g = make_game("channeler", "e1")
    K, c = arcade.key, g.combat
    num = {49: 0, 50: 1, 51: 2, 52: 3, 53: 4, 54: 5}
    foe_hp0 = sum(f["hp"] for f in c["foes"])

    def lock_attack():
        g.b_input(49, num)  # menu 1 = Attack -> targeting
        assert c.get("targeting"), "attack must open target select"
        g.b_input(K.ENTER, num)
        assert c.get("targeting") is None

    def lock_first_submenu():
        g.b_input(50, num)  # menu 2 = Skill -> submenu
        assert c["submenu"] == "skill", f"got submenu={c['submenu']}"
        g.b_input(49, num)  # first skill
        if c.get("targeting"):
            g.b_input(K.ENTER, num)

    for rnd in (1, 2):
        assert c["stage"] == "input", f"round {rnd}: not in input"
        while g.b_input_ally() is not None:
            a = g.b_input_ally()
            if a.get("hero"):
                lock_attack()
            elif a["n"] == "Nym":
                # spell menu: attack0 skill1 spell2 -> key '3'
                g.b_input(51, num)
                assert c["submenu"] == "spell", f"Nym submenu={c['submenu']}"
                g.b_input(49, num)  # spark (foe scope)
                if c.get("targeting"):
                    g.b_input(K.ENTER, num)
            else:
                lock_first_submenu()
        for a in c["allies"]:
            act = (a.get("cmd") or (None,))[0]
            assert act in ("attack", "skill", "spell", "item", "guard", "flee"), f"malformed cmd {a.get('cmd')}"
        _drive_resolve(g)
        if g.state != "COMBAT":
            break
    assert sum(f["hp"] for f in c["foes"]) < foe_hp0, "allies dealt no damage across 2 rounds"
    assert g.state in ("COMBAT", "EXPLORE")
