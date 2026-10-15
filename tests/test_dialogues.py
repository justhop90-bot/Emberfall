"""Validator: story/dialogues.json must be a playable graph. Run: pytest tests/"""
import json
import os


def load():
    base = os.path.join(os.path.dirname(__file__), "..", "story", "dialogues.json")
    with open(os.path.normpath(base)) as f:
        return json.load(f)


def test_graph_links():
    d = load()
    assert len(d) >= 10, "story too small — quests missing?"
    for nid, node in d.items():
        assert node.get("speaker"), f"{nid}: no speaker"
        assert node.get("text"), f"{nid}: no text"
        assert node.get("options"), f"{nid}: no options"
        for o in node["options"]:
            for k in ("next", "success", "fail"):
                if o.get(k):
                    assert o[k] in d, f"{nid}: dangling {k}={o[k]}"
            assert o.get("next") or o.get("end") or o.get("shop") or o.get("check"), \
                f"{nid}: option dead-ends: {o.get('text')}"


def test_checks_sane():
    d = load()
    for nid, node in d.items():
        for o in node["options"]:
            if o.get("check"):
                ab, dc = o["check"]
                assert ab in ("MIGHT", "WIT", "CUNNING"), f"{nid}: bad ability {ab}"
                assert 5 <= dc <= 20, f"{nid}: DC{dc} out of d20 range"
                assert o.get("success") in d and o.get("fail") in d, f"{nid}: check missing branch"


def test_needs_valid():
    d = load()
    known_items = {"bandage", "oil", "herb", "sword1", "charm1"}
    for nid, node in d.items():
        for o in node["options"]:
            if o.get("need"):
                assert o["need"] in known_items, f"{nid}: unknown item {o['need']}"


def test_requires_schema():
    d = load()
    for nid, node in d.items():
        for o in node["options"]:
            rq = o.get("requires") or {}
            assert set(rq) <= {"flag", "noflag", "approval", "rank", "items", "level", "talents"}, f"{nid}: bad requires key"
            if "approval" in rq or "rank" in rq:
                for _w in list((rq.get("approval") or {})) + list((rq.get("rank") or {})):
                    assert _w in ("Nym", "Kael"), f"{nid}: bad companion { _w}"
            if "once" in o:
                assert o["once"] is True, f"{nid}: once must be true"
            for _c in o.get("do") or []:
                assert str(_c).split()[0] in ("flag", "unflag", "gold", "give", "take", "heal", "approval", "xp"), f"{nid}: bad do verb {_c}"
