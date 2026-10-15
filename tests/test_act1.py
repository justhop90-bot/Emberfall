"""Validator: Act 1 density — maps, NPCs, puzzle, pressure, overflow. Run: pytest tests/"""
import EmberfallAct1 as E
import tests.test_combat as T


def _explore_stub(map_id="shore"):
    g = T.make_game("blade", "e1")
    g.state = "EXPLORE"
    g.map_id = map_id
    g.rations = 3
    g.banter_n = 0
    g.tut_spark = True
    g.msg, g.msg_t = "", 0
    return g


def test_five_maps_with_spawns_and_npcs():
    assert set(E.MAPS) >= {"shore", "camp", "chapel", "hold", "cove"}
    for mid, m in E.MAPS.items():
        assert {"hero", "nym", "kael"} <= set(m["spawns"]), mid
        assert m["walls"], mid
    for mid, npcs in E.NPCS.items():
        assert mid in E.MAPS, mid
        for key, _n, _x, _y, _c in npcs:
            assert 0 < _x < E.MAPS[mid]["w"] and 0 < _y < E.MAPS[mid]["h"], (mid, key)


def test_brazier_order_opens_wrong_resets():
    g = _explore_stub("chapel")
    g.flags["e3_done"] = True
    g.brazier("star")
    g.brazier("sun")
    assert "font_open" not in g.flags
    # After wrong 'star', 'sun' restarts sequence correctly
    assert g.braz_order == ["sun"]
    g.brazier("tide")
    g.brazier("star")
    assert "font_open" in g.flags


def test_sailor_dies_on_second_rest():
    g = _explore_stub("camp")
    g.quests["q2"] = 1
    g.camp_rest()
    assert "q2_dead" not in g.flags
    g.camp_rest()
    assert "q2_dead" in g.flags
    assert g.approval["Nym"] < 0


def test_xp_overflow_becomes_gold():
    g = _explore_stub()
    g.level = 5
    g.xp = 500
    g0 = g.gold
    assert g.gain_xp(60) is False
    assert g.gold == g0 + 12


def test_deepmaw_and_new_fights_run():
    for key in ("e4", "maw"):
        g = T.make_game("blade", key)
        assert g.state == "COMBAT"
        assert any(f["alive"] for f in g.combat["foes"])


def test_tess_blessing_weakens_boss():
    g = T.make_game("blade", "boss")
    w0 = [f for f in g.combat["foes"] if f["key"] == "warden_boss"][0]["hp"]
    g2 = T.make_game("blade", "boss")
    g2.flags["tess_bless"] = True
    # rebuild with blessing (flag read at spawn)
    g2b = T.make_game("blade", "boss")
    g2b.flags["tess_bless"] = True
    E.Game.start_combat(g2b, "boss")
    w1 = [f for f in g2b.combat["foes"] if f["key"] == "warden_boss"][0]["hp"]
    assert w0 == 46 and w1 == 36
