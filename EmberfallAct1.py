"""
Emberfall Act 1 — "The Light Below" (Professional build v0.5)
How CRPG/BG3 fans would make it:
 - Choices persist via flags; companions remember and gate options.
 - d20 with Advantage from height/flank/hide, DCs shown honestly.
 - Tactics: initiative, Move/Action/Bonus, shove/dash/hide, oil>fire, downed saves.
 - Hub (camp) + dungeon (chapel) + tutorial shore. Campfire = rest + banters.
 - No filler: 5 quests, 4 fights, 2 companions, levels 1-4, 25-35 min.

Controls:
 Explore: WASD/Arrows move | E interact | J journal | K sheet | F5 save F9 load | Esc pause
 Dialogue: Up/Down + Enter, or 1-4 | Combat: WASD move tile | TAB target | ENTER attack |
           Q dash | F shove | H hide | SPACE end turn
Run: python EmberfallAct1.py
"""
import arcade
import random
import math
import json
import os
import time

SCREEN_W = 960
SCREEN_H = 640
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emberfall_save.json")

ORIGINS = {
    "survivor": {"label": "Rift-Touched Survivor", "desc": "Survived the Rift once. +2 WIT, +4 HP. Feared.", "bonus": {"WIT": 2}, "hp": 4},
    "warden": {"label": "Exiled Warden", "desc": "Disgraced soldier. +2 MIGHT, +8 HP. Kael respects you.", "bonus": {"MIGHT": 2}, "hp": 8},
    "stowaway": {"label": "Stowaway Scholar", "desc": "Snuck aboard for truth. +2 CUNNING, +2 HP. Nym trusts you.", "bonus": {"CUNNING": 2}, "hp": 2},
}
CLASSES = {
    "blade": {"label": "Blade", "desc": "Steel. Cleave + Shieldwall. +2 MIGHT, +10 HP.", "bonus": {"MIGHT": 2}, "hp": 10, "ac": 15, "atk": 5, "dmg": (1, 8)},
    "channeler": {"label": "Channeler", "desc": "Starbolt ignites oil. Mend heals. +2 WIT, +4 HP.", "bonus": {"WIT": 2}, "hp": 4, "ac": 12, "atk": 5, "dmg": (1, 8)},
    "wayknife": {"label": "Wayknife", "desc": "Snipe far, Trip prone. +2 CUNNING, +6 HP.", "bonus": {"CUNNING": 2}, "hp": 6, "ac": 14, "atk": 6, "dmg": (1, 6)},
}
XP_TABLE = [0, 100, 250, 450, 750]
try:
    import progression as _PROG
    XP_TABLE = list(_PROG.XP_TABLE)
except Exception:
    _PROG = None

ITEMS = {
    "bandage": {"label": "Bandage", "price": 8, "desc": "Heal 12 (E in explore on self: press B)."},
    "oil": {"label": "Oil Flask", "price": 10, "desc": "Combat: press O to throw, creates oil."},
    "herb": {"label": "Bitter Herb", "price": 6, "desc": "Quest + heals 6."},
    "sword1": {"label": "Tide-Sergeant Blade", "price": 60, "desc": "+2 attack.", "atk": 2},
    "charm1": {"label": "Star Shard Charm", "price": 50, "desc": "+1 AC, +1 WIT checks.", "ac": 1},
}

ENEMIES = {
    "crab": {"label": "Mourn Crab", "hp": 14, "ac": 12, "atk": 3, "dmg": (1, 6), "xp": 35, "rng": 1, "color": (200, 90, 80), "dfn": 2, "agi": 2},
    "ghast": {"label": "Wreckghast", "hp": 18, "ac": 12, "atk": 4, "dmg": (1, 8), "xp": 50, "rng": 4, "color": (150, 160, 220), "dfn": 2, "agi": 4},
    "caller": {"label": "Tidecaller", "hp": 22, "ac": 13, "atk": 4, "dmg": (1, 6), "xp": 70, "rng": 4, "color": (90, 200, 170), "dfn": 3, "agi": 5},
    "warden_boss": {"label": "Star Warden", "hp": 46, "ac": 14, "atk": 6, "dmg": (1, 10), "xp": 180, "rng": 1, "color": (220, 200, 90), "dfn": 4, "agi": 4},
    "deepmaw": {"label": "Deepmaw", "hp": 40, "ac": 13, "atk": 6, "dmg": (1, 8), "xp": 120, "rng": 1, "color": (120, 40, 60), "dfn": 4, "agi": 3},
}

# Traditional menu-battle abilities (DQ-style rounds: input all, resolve in Agility order).
# scope: foe | allfoes | ally | party | self
ABILITIES = {
    "power_slash": {"label": "Power Slash", "kind": "skill", "mp": 4, "scope": "foe", "power": 1.7, "desc": "1.7x strike, one foe."},
    "cleave": {"label": "Cleave", "kind": "skill", "mp": 5, "scope": "allfoes", "power": 0.9, "desc": "Sweep ALL foes."},
    "war_cry": {"label": "War Cry", "kind": "skill", "mp": 3, "scope": "party", "buff": ("atk", 1), "desc": "Party attack UP."},
    "guard_stance": {"label": "Guard Stance", "kind": "skill", "mp": 2, "scope": "self", "buff": ("dfn", 2), "desc": "Your defense UP big."},
    "focus": {"label": "Focus", "kind": "skill", "mp": 0, "scope": "self", "focus": True, "desc": "Breathe: +6 MP, attack UP."},
    "ember_ward": {"label": "Ember Ward", "kind": "skill", "mp": 3, "scope": "party", "buff": ("dfn", 1), "desc": "Party defense UP."},
    "snipe": {"label": "Snipe", "kind": "skill", "mp": 3, "scope": "foe", "power": 1.5, "nevermiss": True, "desc": "1.5x, never misses."},
    "trip": {"label": "Trip", "kind": "skill", "mp": 3, "scope": "foe", "power": 1.1, "debuff": ("atk", 1), "desc": "1.1x + foe attack DOWN."},
    "smoke": {"label": "Smoke Veil", "kind": "skill", "mp": 2, "scope": "party", "buff": ("dfn", 1), "desc": "Party defense UP."},
    "starbolt": {"label": "Starbolt", "kind": "spell", "mp": 3, "scope": "foe", "power": 1.6, "desc": "Starfire bolt, one foe."},
    "spark": {"label": "Spark", "kind": "spell", "mp": 2, "scope": "foe", "power": 1.3, "desc": "Quick spark, one foe."},
    "mend": {"label": "Mend", "kind": "spell", "mp": 4, "scope": "ally", "heal": 14, "desc": "Heal one ally ~14."},
    "immolate": {"label": "Immolate", "kind": "spell", "mp": 6, "scope": "allfoes", "power": 1.2, "burn": True, "desc": "Burn ALL foes."},
    "ward": {"label": "Ward", "kind": "spell", "mp": 3, "scope": "party", "buff": ("dfn", 1), "desc": "Party defense UP."},
}
CLASS_KITS = {
    "blade": {"skills": ["power_slash", "cleave", "war_cry"], "spells": []},
    "channeler": {"skills": ["focus", "ember_ward"], "spells": ["starbolt", "mend", "immolate"]},
    "wayknife": {"skills": ["snipe", "trip", "smoke"], "spells": []},
    "nym": {"skills": ["focus", "trip"], "spells": ["spark", "mend", "ward"]},
    "kael": {"skills": ["power_slash", "war_cry", "guard_stance"], "spells": []},
}

DIALOGUES = {
    "wake": {"speaker": "Nym", "text": "Hey — breathe! The wreck is sinking and you're bleeding sand. Do you remember your name?",
        "options": [
            {"text": "\"Alive. That's enough for now.\" (Kind)", "next": "wake2", "approval": {"Nym": 1}, "flag": "tone_kind"},
            {"text": "\"Hands off me.\" (Cold)", "next": "wake2", "approval": {"Kael": 1, "Nym": -1}, "flag": "tone_cold"},
            {"text": "[CUNNING DC9] Read her before answering.", "check": ("CUNNING", 9), "success": "wake_ok", "fail": "wake_fail"}]},
    "wake_ok": {"speaker": "Insight", "text": "(SUCCESS) Ink fingers, scholar satchel, shaking hands. Scared FOR you. Trust her — for now.",
        "options": [{"text": "\"Thank you for pulling me out.\"", "next": "wake2", "approval": {"Nym": 2}}]},
    "wake_fail": {"speaker": "Insight", "text": "(FAIL) Head pounds. Details blur. Just answer.",
        "options": [{"text": "\"...Awake. I'm awake.\"", "next": "wake2"}]},
    "wake2": {"speaker": "Kael", "text": "Enough. Tide takes the wreck by dusk and that Star still hums. Scholar — we leave the wounded and light the signal, or die curious.",
        "options": [
            {"text": "\"Nobody gets left behind.\" (Nym)", "next": "c_nym", "approval": {"Nym": 2, "Kael": -1}, "flag": "sided_nym"},
            {"text": "\"Signal first, grief later.\" (Kael)", "next": "c_kael", "approval": {"Kael": 2, "Nym": -1}, "flag": "sided_kael"},
            {"text": "[WIT DC10] \"Both: splint, oil, fire. Together.\"", "check": ("WIT", 10), "success": "c_peace_ok", "fail": "c_peace_fail"}]},
    "c_nym": {"speaker": "Nym", "text": "Decency! Help me: bitter herbs for the sailor (east rocks), oil for the fire. Kael will pout. He'll live.",
        "options": [{"text": "\"Show me. Act 1 begins.\"", "end": "recruit", "flag": "q1_done"}]},
    "c_kael": {"speaker": "Kael", "text": "Soldier's answer. Bring oil from the wreck to the eastern pyre. The scholar's sailor may not last — war rarely asks.",
        "options": [{"text": "\"Then we light it together.\"", "end": "recruit", "flag": "q1_done"}]},
    "c_peace_ok": {"speaker": "Both", "text": "(SUCCESS) Stare... then nods. Kael: \"A leader's answer.\" Nym: \"Oh, I LIKE you.\"",
        "options": [{"text": "\"Splint, oil, fire. NOW.\"", "end": "recruit", "approval": {"Nym": 1, "Kael": 1}, "flag": "peacemaker"}]},
    "c_peace_fail": {"speaker": "Kael", "text": "(FAIL) Pretty words, no plan. Pick a side, stranger.",
        "options": [{"text": "Back Nym — save the sailor.", "next": "c_nym", "approval": {"Nym": 1}}, {"text": "Back Kael — signal first.", "next": "c_kael", "approval": {"Kael": 1}}]},
    "sailor": {"speaker": "Wounded Sailor", "text": "Cold... the Star sang and the hull answered... Don't let them waste herbs on me — light the fire...",
        "options": [
            {"text": "Give bitter herb (if you carry one).", "need": "herb", "next": "sailor_healed", "flag": "q2_done"},
            {"text": "\"Hold on. Nym — splint him.\"", "next": "sailor_stable", "approval": {"Nym": 1}, "flag": "q2_done"},
            {"text": "\"Kael's right. The fire matters more.\" Leave him.", "next": "sailor_left", "approval": {"Kael": 1, "Nym": -2}, "flag": "q2_dark"}]},
    "sailor_healed": {"speaker": "Nym", "text": "Breathing steadies. You did that. The camp will hear of it — kindness is a kind of signal too.",
        "options": [{"text": "\"Rest now. We carry the light.\"", "end": "close", "approval": {"Nym": 2}}]},
    "sailor_stable": {"speaker": "Kael", "text": "Splinted. He'll live to the camp if the tide allows. Not every mercy costs the mission. Remember that.",
        "options": [{"text": "\"Noted. Move to the pyre.\"", "end": "close", "approval": {"Kael": 1, "Nym": 1}}]},
    "sailor_left": {"speaker": "Nym", "text": "...I will remember you chose the fire over a man. So will he, if he wakes.",
        "options": [{"text": "(Say nothing and go.)", "end": "close"}]},
    "serren": {"speaker": "Serren (Trader)", "text": "Wreck-rats and wardens, my favorite customers. Gold for salvage, steel for sense. What'll it be?",
        "options": [
            {"text": "Trade (open shop).", "shop": True},
            {"text": "[CUNNING DC10] \"Warden prices for a warden's friend?\"", "check": ("CUNNING", 10), "success": "serren_ok", "fail": "serren_fail"},
            {"text": "Leave.", "end": "close"}]},
    "serren_ok": {"speaker": "Serren", "text": "(SUCCESS) Ha! Fine — 20 gold off your next kindness. Take it.",
        "options": [{"text": "Trade.", "shop": True, "gold": 20}, {"text": "Thanks. Another time.", "end": "close", "gold": 20}]},
    "serren_fail": {"speaker": "Serren", "text": "(FAIL) Nice try. Salt prices for salt tongues.",
        "options": [{"text": "Trade anyway.", "shop": True}, {"text": "Leave.", "end": "close"}]},
    "altar": {"speaker": "The Pale Star", "text": "*it hums your name* The chapel drowned praying to it. Light the great fire and call the fleet — or shatter the shard and silence it forever. Both have a price.",
        "options": [
            {"text": "LIGHT IT — call the fleet home. (Kael's way)", "end": "ending_light", "flag": "ending_light"},
            {"text": "SHATTER IT — no more songs, no more wrecks. (Nym fears this)", "end": "ending_dark", "flag": "ending_dark"},
            {"text": "[WIT DC12] BIND IT — carry the hum, answer later. (Needs Peacemaker OR Nym+3)", "check": ("WIT", 12), "success": "altar_bind", "fail": "altar_bind_fail"}]},
    "altar_bind": {"speaker": "The Pale Star", "text": "(SUCCESS) The shard cools into your palm. It chose. The fleet will wait — and so will the deep.",
        "options": [{"text": "Take it. End Act 1.", "end": "ending_bind", "flag": "ending_bind"}]},
    "altar_bind_fail": {"speaker": "The Pale Star", "text": "(FAIL) It burns. Choose, bearer — light or shatter, but choose.",
        "options": [{"text": "Light it.", "end": "ending_light", "flag": "ending_light"}, {"text": "Shatter it.", "end": "ending_dark", "flag": "ending_dark"}]},
    "banter_nym": {"speaker": "Nym (campfire)", "text": "Do you think the Star sings, or only remembers singing? ...Thank you. For choosing people, back there.",
        "options": [{"text": "\"Sleep. I'll keep the hum away.\"", "end": "close", "approval": {"Nym": 1}}]},
    "banter_kael": {"speaker": "Kael (campfire)", "text": "You held the line today. Exile or not — you drill like a warden. Tomorrow the chapel. Stay close.",
        "options": [{"text": "\"Tomorrow we finish it.\"", "end": "close", "approval": {"Kael": 1}}]},
}

# story/ is the source of truth — writers edit JSON, game hot-loads it.
# Inline DIALOGUES above is the fallback if the file is missing/corrupt.
def _load_dialogues():
    try:
        import json as _j
        _base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "story", "dialogues.json")
        with open(_base) as _f:
            _d = _j.load(_f)
        for _n in _d.values():  # JSON lists -> tuples the engine expects
            for _o in _n.get("options", []):
                if isinstance(_o.get("check"), list):
                    _o["check"] = tuple(_o["check"])
        return _d
    except Exception:
        return None
_loaded = _load_dialogues()
if _loaded:
    DIALOGUES = _loaded

CINEMA = ["The sky tore above the Mournsea.", "A pale star fell — humming — and the fleet with it.",
          "Cold water. A voice saying your name.", "Sand in your mouth. Someone shaking you awake.", "(SPACE — open your eyes)"]


def mod(score):
    return (score - 10) // 2


def roll_d20(m=0):
    n = random.randint(1, 20)
    return n, n + m


def roll(d, s):
    return sum(random.randint(1, s) for _ in range(d))


MAPS = {
    "shore": {"w": 1400, "h": 900, "sea": 640,
        "walls": [(0, 0, 1400, 24), (0, 0, 24, 900), (1376, 0, 24, 900), (0, 876, 1400, 24), (260, 380, 260, 46), (900, 360, 200, 56)],
        "props": [("WRECK", 330, 400), ("ROCKS", 960, 380), ("PYRE (east)", 1220, 560)],
        "spawns": {"hero": (480, 220), "nym": (540, 260), "kael": (480, 520)}},
    "camp": {"w": 1400, "h": 900, "sea": 900,
        "walls": [(0, 0, 1400, 24), (0, 0, 24, 900), (1376, 0, 24, 900), (0, 876, 1400, 24), (500, 420, 300, 50), (150, 550, 180, 120)],
        "props": [("TENTS", 620, 440), ("STORE", 220, 600), ("CAMPFIRE", 700, 300)],
        "spawns": {"hero": (200, 200), "nym": (260, 220), "kael": (180, 260)}},
    "chapel": {"w": 1400, "h": 900, "sea": 950,
        "walls": [(0, 0, 1400, 24), (0, 0, 24, 900), (1376, 0, 24, 900), (0, 876, 1400, 24), (400, 300, 120, 300), (880, 300, 120, 300), (500, 600, 400, 46)],
        "props": [("ALTAR", 700, 700), ("PEWS", 620, 480), ("FONT", 780, 420), ("SUN BRAZIER", 480, 640), ("TIDE BRAZIER", 700, 660), ("STAR BRAZIER", 920, 640)],
        "spawns": {"hero": (700, 150), "nym": (750, 170), "kael": (650, 170)}},
    "hold": {"w": 1200, "h": 800, "sea": 900,
        "walls": [(0, 0, 1200, 24), (0, 0, 24, 800), (1176, 0, 24, 800), (0, 776, 1200, 24), (300, 300, 200, 40), (700, 450, 200, 40), (450, 600, 300, 40)],
        "props": [("SPLIT HULL", 400, 400), ("PAY CHEST", 800, 500), ("LEDGER DESK", 550, 650), ("NEST", 950, 250)],
        "spawns": {"hero": (150, 150), "nym": (200, 170), "kael": (130, 200)}},
    "cove": {"w": 1400, "h": 900, "sea": 700,
        "walls": [(0, 0, 1400, 24), (0, 0, 24, 900), (1376, 0, 24, 900), (0, 876, 1400, 24), (500, 200, 300, 46), (900, 500, 200, 60)],
        "props": [("SMUGGLER FIRE", 700, 400), ("TIDE POOL", 1050, 620), ("DARK WATER", 300, 700)],
        "spawns": {"hero": (200, 200), "nym": (260, 220), "kael": (180, 260)}},
}

# ambient NPCs per map: (key, name, x, y, cloak) — drawn + talked via interact
NPCS = {
    "shore": [("per", "Per", 1150, 250, (90, 160, 200))],
    "camp": [("maren", "Maren", 550, 480, (150, 200, 140))],
    "chapel": [("tess", "Tess", 700, 250, (220, 220, 240)), ("pilgrim", "Vess", 850, 380, (160, 140, 160))],
    "hold": [],
    "cove": [("joss", "Joss", 700, 430, (120, 120, 140))],
}


class Game(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_W, SCREEN_H, "Emberfall Act 1 — The Light Below")
        arcade.set_background_color((10, 12, 22))
        self.keys = set()
        self.state = "TITLE"
        self.map_id = "shore"
        self.cam = [0, 0]
        self.t = 0.0
        self.play_t0 = time.time()
        self.stats = {"kills": 0, "ok": 0, "fail": 0}

        self.origin_id = "survivor"
        self.class_id = "blade"
        self.creator_opts = list(ORIGINS.keys())
        self.hero_name = ""
        self.abilities = {"MIGHT": 10, "WIT": 10, "CUNNING": 10}
        self.max_hp = 24
        self.hp = 24
        self.max_mp = 12
        self.mp = 12
        self.ac = 13
        self.atk = 5
        self.level = 1
        self.xp = 0
        self.gold = 30
        self.inv = {"bandage": 1, "herb": 0, "oil": 1}
        self.equip_atk = 0
        self.equip_ac = 0
        self.rations = 2

        self.flags = {}
        self.approval = {"Kael": 0, "Nym": 0}
        self.quests = {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0}
        self.px, self.py = 480, 220
        self.face = 1
        self.walk = 0.0
        self.comps = [
            {"name": "Nym", "x": 540, "y": 260, "color": (170, 120, 235), "on": False, "hp": 18, "max": 18, "mp": 14, "mpmax": 14, "ac": 12, "atk": 4},
            {"name": "Kael", "x": 480, "y": 520, "color": (235, 160, 80), "on": False, "hp": 26, "max": 26, "mp": 6, "mpmax": 6, "ac": 15, "atk": 5},
        ]
        self.journal = False
        self.sheet = False
        self.cine_i = 0
        self.cine_c = 0
        self.cine_t = 0.0
        self.node = None
        self.reveal = 0.0
        self.sel = 0
        self.banner = ""
        self.banner_t = 0.0
        self.return_map = "shore"
        self.msg = ""
        self.msg_t = 0.0
        self.banter_n = 0
        self.combat = None
        self.shop_sel = 0
        self.paused_from = "EXPLORE"
        # --- pro assets (fonts, Kenney CC0 tiles, key glyphs, portraits) ---
        self.font_title = "Arial"
        self.font_body = "Arial"
        try:
            arcade.load_font("assets/fonts/Cinzel.ttf")
            self.font_title = "Cinzel"
        except Exception:
            pass
        try:
            arcade.load_font("assets/fonts/Alegreya.ttf")
            self.font_body = "Alegreya"
        except Exception:
            pass
        self.tile_tex = {}
        for _tn, _tp in (("grass", "assets/kenney_rpg/PNG/rpgTile019.png"),
                         ("sand", "assets/kenney_rpg/PNG/rpgTile049.png"),
                         ("water", "assets/kenney_rpg/PNG/rpgTile099.png"),
                         ("stone", "assets/kenney_rpg/PNG/rpgTile033.png"),
                         ("wood", "assets/kenney_rpg/PNG/rpgTile198.png")):
            try:
                self.tile_tex[_tn] = arcade.load_texture(_tp)
            except Exception:
                pass
        self.glyph_tex = {}
        for _g in ("keyboard_e", "keyboard_j", "keyboard_k", "keyboard_b", "keyboard_tab",
                   "keyboard_enter", "keyboard_space", "keyboard_escape"):
            try:
                self.glyph_tex[_g] = arcade.load_texture(f"assets/glyphs/{_g}.png")
            except Exception:
                pass
        self.portrait_tex = {}
        for _pn in ("nym", "kael", "hero"):
            try:
                self.portrait_tex[_pn] = arcade.load_texture(f"assets/portraits/{_pn}.png")
            except Exception:
                pass
        # --- audio: pygame mixer (soft SFX + music loops), winsound fallback ---
        self.sounds = {}
        self.pg_sounds = {}
        self.sound_paths = {}
        self.muted = False
        self.music_muted = False
        self.last_sfx = ""
        self.last_sfx_t = 0.0
        self.audio_backend = "none"
        self.audio_err = ""
        self._players = []
        self._music_mode = ""
        try:
            import winsound as _ws
            self._winsound = _ws
        except Exception:
            self._winsound = None
        self._pg = None
        try:
            import pygame as _pg
            if not _pg.mixer.get_init():
                _pg.mixer.pre_init(22050, -16, 1, 512)
                _pg.mixer.init()
            self._pg = _pg
            _vols = {"hit": 0.5, "miss": 0.35, "dice": 0.45, "ui": 0.4, "fire": 0.45,
                     "levelup": 0.5, "heal": 0.45}
            for _sn, _vv in _vols.items():
                _p = os.path.join("assets", "audio", f"{_sn}.wav")
                self.sound_paths[_sn] = _p
                try:
                    _s = _pg.mixer.Sound(_p)
                    _s.set_volume(_vv)
                    self.pg_sounds[_sn] = _s
                except Exception as _e:
                    self.audio_err = f"sfx {_sn}: {_e}"
                try:
                    self.sounds[_sn] = arcade.load_sound(_p)
                except Exception:
                    pass
            self.audio_backend = "pygame"
            try:
                _pg.mixer.music.set_volume(0.32)
            except Exception:
                pass
        except Exception as _e:
            self.audio_err = f"mixer: {_e}"
            for _sn in ("hit", "miss", "dice", "ui", "fire", "levelup", "heal"):
                _p = os.path.join("assets", "audio", f"{_sn}.wav")
                self.sound_paths[_sn] = _p
                try:
                    self.sounds[_sn] = arcade.load_sound(_p)
                except Exception:
                    pass
            if self._winsound is not None:
                self.audio_backend = "winsound"
        self._music_tick = 0.0
        # title ambience from the first frame — no keypress needed
        try:
            self.start_music("explore")
        except Exception:
            pass
        # --- game feel state ---
        self.trauma = 0.0      # screen shake 0..1 (decays)
        self.hitstop = 0.0     # freeze frames on hits (decays fast)
        self.floaters = []     # {x,y,txt,col,t} combat damage numbers (screen space)
        self.hp_show = {}      # unit id -> displayed hp (lerps to real)
        self.particles = []    # {x,y,vx,vy,t,life,col} world-space sparks
        # --- Sparks & Bonds progression ---
        self.hero_talents = []   # talent ids (hero only)
        self.pending_drafts = 0  # queued talent picks (resolved at campfire)
        self.pending_feat = False
        self.feat = None
        self.bond_seen = set()   # e.g. {"nym:2"} scenes already played
        self.draft_offer = []    # current modal options
        self.tut_spark = False   # first-draft tutorial played
        self.seen_nodes = set()  # dialogue nodes ever visited (Ink-style memory)
        self.seen_opts = set()   # "node:idx" once-options already taken

    # ---------- character ----------
    def finalize(self):
        ab = {"MIGHT": 10, "WIT": 10, "CUNNING": 10}
        for k, v in ORIGINS[self.origin_id]["bonus"].items():
            ab[k] += v
        for k, v in CLASSES[self.class_id]["bonus"].items():
            ab[k] += v
        self.abilities = ab
        cl = CLASSES[self.class_id]
        self.max_hp = 20 + ORIGINS[self.origin_id]["hp"] + cl["hp"]
        self.hp = self.max_hp
        self.ac = cl["ac"]
        self.atk = cl["atk"]
        _mpb = {"blade": 2, "channeler": 8, "wayknife": 4}[self.class_id]
        self.max_mp = 10 + mod(ab["WIT"]) * 2 + _mpb
        self.mp = self.max_mp
        if not self.hero_name.strip():
            self.hero_name = "Ash"

    def hero_agi(self):
        v = 5 + mod(self.abilities["CUNNING"]) * 2 + (2 if self.class_id == "wayknife" else 0)
        if self.has_talent("tideborn") or self.has_talent("swift"):
            v += 2
        if "Tide" in [t for t, _l in self.tag_sets()]:
            v += 2
        if self.feat == "feat_tactician":
            v += 2
        return v

    def apply_talent(self, tid):
        """Learn a talent: immediate rewards now, passive flags checked in battle."""
        if tid in self.hero_talents:
            self.max_hp += 4
            self.hp = min(self.max_hp, self.hp + 4)
            return
        if tid == "__hearty__":
            self.max_hp += 4
            self.hp = min(self.max_hp, self.hp + 4)
            self.hero_talents.append(tid)
            return
        self.hero_talents.append(tid)
        if tid == "deep_well":
            self.max_mp += 8
            self.mp = self.max_mp
        elif tid == "tough":
            self.max_hp += 10
            self.hp = min(self.max_hp, self.hp + 10)
        elif tid == "cleave_master":
            ABILITIES["cleave"]["power"] = 1.15
        elif tid == "bright_mind":
            ABILITIES["starbolt"]["power"] = 2.0
            ABILITIES["starbolt"]["burn"] = True
        self.play("levelup")

    def apply_feat(self, fid):
        self.feat = fid
        if fid == "asi_might":
            self.abilities["MIGHT"] += 2
        elif fid == "asi_wit":
            self.abilities["WIT"] += 2
        elif fid == "asi_cunning":
            self.abilities["CUNNING"] += 2
        elif fid == "feat_tough":
            self.max_hp += 12
            self.hp = min(self.max_hp, self.hp + 12)
        elif fid == "feat_startouched":
            for _k in ("starbolt", "immolate", "spark"):
                if _k in ABILITIES:
                    ABILITIES[_k]["power"] = round(ABILITIES[_k].get("power", 1.0) + 0.3, 2)
        self.play("levelup")

    def burn_rounds(self, base=3):
        n = base
        if self.has_talent("ember_soul"):
            n += 2
        if "Ember" in [t for t, _l in self.tag_sets()]:
            n += 2
        return n

    def hero_dfn(self):
        return max(0, self.eff_ac() - 10)

    def eff_atk(self):
        return self.atk + self.equip_atk

    def eff_ac(self):
        return self.ac + self.equip_ac + (1 if "charm1" in self.inv and self.inv.get("charm1_equipped") else 0)

    def check(self, ability, dc):
        m = mod(self.abilities[ability] + (1 if ability == "WIT" and self.inv.get("charm1_equipped") else 0))
        nat, tot = roll_d20(m)
        ok = (nat == 20) or (tot >= dc and nat != 1)
        if ok:
            self.stats["ok"] += 1
        else:
            self.stats["fail"] += 1
        self.play("dice")
        return ok, f"d20:{nat}+{m} {ability} vs DC{dc} — {'SUCCESS' if ok else 'FAIL'}"

    def gain_xp(self, n):
        if self.level >= len(XP_TABLE):
            _g = max(1, n // 5)
            self.gold += _g
            self.msg, self.msg_t = f"+{n} XP (capped) → +{_g}g salt-money.", 3
            return False
        self.msg = f"+{n} XP"
        self.msg_t = 3
        self.xp += n
        leveled = False
        while self.level < len(XP_TABLE) and self.xp >= XP_TABLE[self.level]:
            self.level += 1
            leveled = True
            self.max_hp += 8
            self.hp = self.max_hp
            self.atk += 1
            self.max_mp += 2
            self.mp = self.max_mp
            for c in self.comps:
                c["max"] += 6
                c["hp"] = c["max"]
                c["mpmax"] = c.get("mpmax", 6) + 2
                c["mp"] = c["mpmax"]
            if _PROG is not None and self.level in _PROG.DRAFT_LEVELS:
                self.pending_drafts += 1
                self.msg = f"LEVEL {self.level}! A Spark stirs — rest at a campfire."
            elif _PROG is not None and self.level == _PROG.FEAT_LEVEL:
                self.pending_feat = True
                self.msg = f"LEVEL {self.level}! A turning point — rest at a campfire."
            else:
                self.msg = f"LEVEL {self.level}! HP+8 MP+2 ATK+1 (K for sheet)"
            self.msg_t = 4
            self.play("levelup")
        return leveled

    def has_talent(self, tid):
        return tid in getattr(self, "hero_talents", [])

    def tag_sets(self):
        if _PROG is None:
            return []
        return [t for t, _l in _PROG.active_sets(self.hero_talents)]

    def bond_rank(self, who):
        if _PROG is None:
            return 0
        return _PROG.bond_rank(self.approval.get(who, 0), "peacemaker" in self.flags)

    def duo_rank(self, who):
        """Highest Bond rank actually SEALED at a campfire (scene played).
        Approval alone never unlocks duos — the scene does."""
        node = "nym" if who == "Nym" else "kael"
        best = 0
        for need in sorted((_PROG.BOND_RANKS if _PROG else {})):
            if f"{node}:{need}" in getattr(self, "bond_seen", set()):
                best = need
        return best

    def duo_available(self):
        out = []
        if _PROG is None or self.state not in ("COMBAT",):
            pass
        else:
            c = self.combat
            pals = {a["n"] for a in c["allies"] if a["alive"]}
            if "Nym" in pals and self.duo_rank("Nym") >= 2:
                out.append("nym")
            if "Kael" in pals and self.duo_rank("Kael") >= 2:
                out.append("kael")
        return out

    # ---------- map / save ----------
    def goto_map(self, mid, x=None, y=None):
        self.map_id = mid
        sp = MAPS[mid]["spawns"]
        if x is None:
            self.px, self.py = sp["hero"]
            self.comps[0]["x"], self.comps[0]["y"] = sp["nym"]
            self.comps[1]["x"], self.comps[1]["y"] = sp["kael"]
        else:
            self.px, self.py = x, y
        self.cam = [0, 0]

    def save(self):
        try:
            data = {"name": self.hero_name, "o": self.origin_id, "c": self.class_id, "ab": self.abilities,
                    "hp": self.hp, "max": self.max_hp, "mp": self.mp, "mpmax": self.max_mp,
                    "ac": self.ac, "atk": self.atk, "lv": self.level, "xp": self.xp,
                    "gold": self.gold, "inv": self.inv, "rat": self.rations, "map": self.map_id, "pos": [self.px, self.py],
                    "flags": self.flags, "appr": self.approval, "quests": self.quests,
                    "eat": self.equip_atk, "eac": self.equip_ac,
                    "tal": self.hero_talents, "pd": self.pending_drafts, "pf": self.pending_feat,
                    "feat": self.feat, "bs": sorted(self.bond_seen), "tut": self.tut_spark,
                    "q2r": getattr(self, "q2_rests", 0), "braz": getattr(self, "braz_order", []),
                    "seen": sorted(getattr(self, "seen_nodes", set())),
                    "seen_opts": sorted(getattr(self, "seen_opts", set())),
                    "cmp": [{"hp": c["hp"], "max": c["max"], "mp": c.get("mp", 6), "mpmax": c.get("mpmax", 6)} for c in self.comps]}
            json.dump(data, open(SAVE_PATH, "w"))
            self.msg, self.msg_t = "Saved (F9 to load).", 2
        except Exception as e:
            self.msg, self.msg_t = f"Save failed: {e}", 3

    def load(self):
        try:
            d = json.load(open(SAVE_PATH))
            self.hero_name = d["name"]
            self.origin_id, self.class_id = d["o"], d["c"]
            self.abilities, self.hp, self.max_hp = d["ab"], d["hp"], d["max"]
            self.mp, self.max_mp = d.get("mp", 12), d.get("mpmax", 12)
            self.ac, self.atk, self.level, self.xp = d["ac"], d["atk"], d["lv"], d["xp"]
            self.gold, self.inv, self.rations = d["gold"], d["inv"], d["rat"]
            self.flags, self.approval, self.quests = d["flags"], d["appr"], d["quests"]
            self.equip_atk, self.equip_ac = d.get("eat", 0), d.get("eac", 0)
            self.hero_talents = d.get("tal", [])
            self.pending_drafts = d.get("pd", 0)
            self.pending_feat = d.get("pf", False)
            self.feat = d.get("feat", None)
            self.bond_seen = set(d.get("bs", []))
            self.tut_spark = d.get("tut", True)
            self.q2_rests = d.get("q2r", 0)
            self.braz_order = d.get("braz", [])
            self.seen_nodes = set(d.get("seen", []))
            self.seen_opts = set(d.get("seen_opts", []))
            # table mutations don't survive a reboot — re-apply from the loaded build
            self.revert_abilities()
            for _t in self.hero_talents:
                if _t == "cleave_master":
                    ABILITIES["cleave"]["power"] = 1.15
                elif _t == "bright_mind":
                    ABILITIES["starbolt"]["power"] = 2.0
                    ABILITIES["starbolt"]["burn"] = True
            for _c, _s in zip(self.comps, d.get("cmp", [])):
                _c["hp"], _c["max"] = _s.get("hp", _c["max"]), _s.get("max", _c["max"])
                _c["mp"], _c["mpmax"] = _s.get("mp", 6), _s.get("mpmax", 6)
            self.goto_map(d["map"], d["pos"][0], d["pos"][1])
            for c in self.comps:
                c["on"] = ("q1_done" in self.flags)
            self.state = "EXPLORE"
            self.msg, self.msg_t = "Loaded.", 2
            self.start_music("explore")
        except Exception as e:
            self.msg, self.msg_t = f"No save yet ({e}).", 3

    # ---------- dialogue ----------
    def talk(self, nid):
        self.state = "DIALOGUE"
        self.play("ui")
        self.node = nid
        self.reveal = 0.0
        self.sel = 0
        self.banner = ""
        self.seen_nodes.add(nid)

    def cur(self):
        return DIALOGUES[self.node]

    def opt_ok(self, opt, idx):
        """Ink-style choice gating: unmet requires hide the option entirely."""
        if f"{self.node}:{idx}" in getattr(self, "seen_opts", set()) and opt.get("once"):
            return False
        rq = opt.get("requires") or {}
        if "flag" in rq and rq["flag"] not in self.flags:
            return False
        if "noflag" in rq and rq["noflag"] in self.flags:
            return False
        for _w, _need in (rq.get("approval") or {}).items():
            if self.approval.get(_w, 0) < _need:
                return False
        for _w, _need in (rq.get("rank") or {}).items():
            if self.bond_rank(_w) < _need:
                return False
        for _item, _n in (rq.get("items") or {}).items():
            if self.inv.get(_item, 0) < _n:
                return False
        if "level" in rq and self.level < rq["level"]:
            return False
        if "talents" in rq and len(getattr(self, "hero_talents", [])) < rq["talents"]:
            return False
        return True

    def visible_opts(self):
        return [(i, o) for i, o in enumerate(self.cur()["options"]) if self.opt_ok(o, i)]

    def do_exec(self, cmds):
        """Yarn-style effect commands on options: flag/gold/give/take/heal/approval/xp."""
        for _c in cmds or []:
            _p = str(_c).split()
            if not _p:
                continue
            _verb = _p[0]
            try:
                if _verb == "flag" and len(_p) > 1:
                    self.flags[_p[1]] = True
                elif _verb == "unflag" and len(_p) > 1:
                    self.flags.pop(_p[1], None)
                elif _verb == "gold" and len(_p) > 1:
                    self.gold += int(_p[1])
                elif _verb == "give":
                    self.inv[_p[1]] = self.inv.get(_p[1], 0) + (int(_p[2]) if len(_p) > 2 else 1)
                elif _verb == "take":
                    self.inv[_p[1]] = max(0, self.inv.get(_p[1], 0) - (int(_p[2]) if len(_p) > 2 else 1))
                elif _verb == "heal":
                    _n = int(_p[1]) if len(_p) > 1 else 10
                    self.hp = min(self.max_hp, self.hp + _n)
                elif _verb == "approval" and len(_p) > 2:
                    self.approval[_p[1]] = self.approval.get(_p[1], 0) + int(_p[2])
                elif _verb == "xp" and len(_p) > 1:
                    self.gain_xp(int(_p[1]))
            except (ValueError, IndexError):
                continue

    def choose(self, opt, idx=None):
        if opt.get("need") and self.inv.get(opt["need"], 0) <= 0:
            self.banner = f"Need: {opt['need']} — not in pack."
            self.banner_t = 2.5
            return
        if opt.get("need"):
            self.inv[opt["need"]] -= 1
        if idx is not None and opt.get("once"):
            self.seen_opts.add(f"{self.node}:{idx}")
        self.do_exec(opt.get("do"))
        if opt.get("gold"):
            self.gold += opt["gold"]
        for k, v in opt.get("approval", {}).items():
            self.approval[k] = self.approval.get(k, 0) + v
        if opt.get("flag"):
            self.flags[opt["flag"]] = True
            if opt["flag"] == "q1_done":
                self.quests["q1"] = 2
                for c in self.comps:
                    c["on"] = True
            if opt["flag"] in ("q2_done", "q2_dark"):
                self.quests["q2"] = 2
                self.gain_xp(40)
            if opt["flag"] in ("ending_light", "ending_dark", "ending_bind"):
                self.quests["q5"] = 2
                self.state = "ACTDONE"
                return
        if opt.get("shop"):
            self.state = "TRADER"
            return
        if opt.get("check"):
            ab, dc = opt["check"]
            ok, txt = self.check(ab, dc)
            self.banner, self.banner_t = txt, 3.0
            self.talk(opt["success"] if ok else opt["fail"])
            return
        if opt.get("next"):
            self.talk(opt["next"])
            return
        if opt.get("end"):
            if opt["end"] == "recruit":
                for c in self.comps:
                    c["on"] = True
                self.quests["q1"] = 2
                self.gain_xp(40)
            if opt["end"] == "rest":
                self.camp_rest()
                return
            if opt["end"] == "draft":
                self.open_draft()
                return
            if opt["end"] == "respec":
                self.camp_respec()
                return
            self.state = "EXPLORE"

    # ---------- Sparks & Bonds: campfire, drafts, feats, respec ----------
    def camp_rest(self):
        if self.rations <= 0:
            self.msg, self.msg_t = "No rations. Serren sells food.", 3
            self.state = "EXPLORE"
            return
        self.rations -= 1
        self.hp = self.max_hp
        self.mp = self.max_mp
        for c in self.comps:
            c["hp"] = c["max"]
            c["mp"] = c.get("mpmax", 6)
        self.play("heal")
        # time pressure: the untended sailor fades on the second rest
        if self.quests.get("q2") == 1 and "q2_done" not in self.flags and "q2_dark" not in self.flags:
            self.q2_rests = getattr(self, "q2_rests", 0) + 1
            if self.q2_rests == 1:
                self.msg, self.msg_t = "Rested. Somewhere east, the sailor coughs blood.", 4
            elif self.q2_rests >= 2:
                self.flags["q2_dead"] = True
                self.approval["Nym"] = self.approval.get("Nym", 0) - 2
                self.msg, self.msg_t = "You slept. The sailor didn't wake. Nym won't forget.", 5
        # tutorial first: Nym's Spark intro must never be skipped by a scene
        if self.pending_drafts > 0 and not self.tut_spark:
            self.tut_spark = True
            self.talk("draft_tut")
            return
        scene = self.check_bond_ups()
        if scene:
            self.talk(scene)
            return
        if self.pending_drafts > 0 or self.pending_feat:
            self.open_draft()
            return
        self.banter_n += 1
        self.talk("banter_nym" if self.banter_n % 2 == 1 else "banter_kael")

    def check_bond_ups(self):
        if _PROG is None:
            return None
        for who, node in (("Nym", "nym"), ("Kael", "kael")):
            r = self.bond_rank(who)
            for need in sorted(_PROG.BOND_RANKS):
                key = f"{node}:{need}"
                if r >= need and key not in self.bond_seen:
                    self.bond_seen.add(key)
                    self.play("levelup")
                    return f"{node}_bond{need}"
        return None

    def open_draft(self):
        if _PROG is None or self.pending_drafts <= 0:
            if self.pending_feat:
                self.open_feat()
                return
            self.msg, self.msg_t = "The sparks are quiet. (Level up, then rest.)", 3
            self.state = "EXPLORE"
            return
        offer = _PROG.draft_offer(self.class_id, self.origin_id, self.hero_talents)
        while len(offer) < 3:
            offer.append("__hearty__")
        self.draft_offer = offer[:3]
        self.draft_sel = 0
        self.state = "DRAFT"
        self.play("ui")

    def take_draft(self, tid):
        if tid == "__hearty__":
            self.max_hp += 4
            self.hp = min(self.max_hp, self.hp + 4)
            self.hero_talents.append(tid)
        else:
            self.apply_talent(tid)
        self.pending_drafts -= 1
        if self.pending_drafts > 0:
            self.open_draft()
        elif self.pending_feat:
            self.open_feat()
        else:
            _sets = ", ".join(l for _t, l in self.tag_sets())
            self.msg = f"Spark shaped! {('Set: ' + _sets) if _sets else 'The Star hums approval.'}"
            self.msg_t = 4
            self.state = "EXPLORE"

    def open_feat(self):
        if not self.pending_feat:
            self.state = "EXPLORE"
            return
        self.feat_offer = ["asi_might", "asi_wit", "asi_cunning", "feat_tough", "feat_startouched", "feat_tactician"]
        self.feat_sel = 0
        self.state = "FEAT"
        self.play("ui")

    def take_feat(self, fid):
        self.apply_feat(fid)
        self.pending_feat = False
        self.msg, self.msg_t = "A turning point sealed. (K for sheet)", 4
        self.state = "EXPLORE"

    def camp_respec(self):
        real = [t for t in self.hero_talents if t != "__hearty__"]
        if not real:
            self.msg, self.msg_t = "No path yet to retread. (Earn Sparks first.)", 3
            self.state = "EXPLORE"
            return
        if self.rations <= 0:
            self.msg, self.msg_t = "Retreading costs 1 ration.", 3
            self.state = "EXPLORE"
            return
        self.rations -= 1
        self.hero_talents = []
        self.revert_abilities()
        self.finalize()  # rebuild base stats from origin/class/level
        self.max_hp += 8 * (self.level - 1)
        self.hp = self.max_hp
        self.atk += (self.level - 1)
        self.max_mp += 2 * (self.level - 1)
        self.mp = self.max_mp
        if self.feat == "asi_might":
            self.abilities["MIGHT"] += 2
        elif self.feat == "asi_wit":
            self.abilities["WIT"] += 2
        elif self.feat == "asi_cunning":
            self.abilities["CUNNING"] += 2
        elif self.feat == "feat_tough":
            self.max_hp += 12
            self.hp = self.max_hp
        earned = sum(1 for lv in _PROG.DRAFT_LEVELS if lv <= self.level) if _PROG else 0
        self.pending_drafts = earned
        self.msg, self.msg_t = "The path unwinds. Reflect anew.", 3
        self.open_draft()

    def revert_abilities(self):
        ABILITIES["cleave"]["power"] = 0.9
        ABILITIES["starbolt"]["power"] = 1.6
        ABILITIES["starbolt"].pop("burn", None)
        ABILITIES["immolate"]["power"] = 1.2
        ABILITIES["spark"]["power"] = 1.3
        if self.feat == "feat_startouched":
            for _k in ("starbolt", "immolate", "spark"):
                ABILITIES[_k]["power"] = round(ABILITIES[_k]["power"] + 0.3, 2)

    # ---------- combat: traditional menu battle (DQ-style rounds) ----------
    # Each round: input commands for every ally (Attack/Skill/Spell/Item/Guard/Flee),
    # then resolve all combatants in Agility order. No grid, no ranges — positioning
    # is replaced by Guard, buffs/debuffs, dots, MP management and target priority.
    def b_ally_xy(self, i, n=None):
        n = len(self.combat["allies"]) if n is None else n
        xs = {1: [480], 2: [390, 570], 3: [300, 480, 660]}[n]
        return xs[i], 210

    def b_foe_xy(self, i, n=None):
        n = len(self.combat["foes"]) if n is None else n
        xs = {1: [480], 2: [395, 565], 3: [310, 480, 650], 4: [240, 400, 560, 720]}[n]
        return xs[i], 450

    def b_kit(self, ally):
        return CLASS_KITS[ally.get("cls", "blade")]

    def b_menu(self, ally):
        m = [("attack", "Attack"), ("skill", "Skill")]
        if self.b_kit(ally)["spells"]:
            m.append(("spell", "Spell"))
        m += [("item", "Item")]
        if bool(ally.get("hero")) and self.duo_available():
            m.append(("duo", "Duo ★"))
        m += [("guard", "Guard"), ("flee", "Flee")]
        return m

    def b_ability_list(self, ally, kind):
        return [a for a in self.b_kit(ally)[kind + "s"]]

    def b_item_list(self):
        out = []
        if self.inv.get("bandage", 0) > 0:
            out.append(("bandage", f"Bandage x{self.inv['bandage']} (heal 12)"))
        if self.inv.get("herb", 0) > 0:
            out.append(("herb", f"Bitter Herb x{self.inv['herb']} (heal 6 + cure)"))
        if self.inv.get("oil", 0) > 0:
            out.append(("oil", f"Oil Flask x{self.inv['oil']} (firebomb 8+burn)"))
        return out

    def start_combat(self, key):
        self.return_map = self.map_id
        presets = {
            "e1": ["crab", "crab"],
            "e2": ["crab", "ghast", "ghast"],
            "e3": ["ghast", "ghast", "caller"],
            "e4": ["ghast", "ghast", "crab"],
            "maw": ["deepmaw"],
            "boss": ["caller", "ghast", "warden_boss"],
        }
        foes = presets.get(key, ["crab"])
        allies = [{"n": self.hero_name, "hero": True, "cls": self.class_id, "hp": self.hp, "max": self.max_hp,
                   "mp": self.mp, "mpmax": self.max_mp, "atk": self.eff_atk(), "dfn": self.hero_dfn(),
                   "agi": self.hero_agi(), "color": (250, 220, 90), "alive": True, "guard": False,
                   "st": {"atk": 0, "dfn": 0}, "dot": {"poison": 0, "burn": 0}, "cmd": None}]
        if self.comps[0]["on"]:
            _c = self.comps[0]
            allies.append({"n": "Nym", "cls": "nym", "hp": _c["hp"], "max": _c["max"], "mp": _c.get("mp", 14),
                           "mpmax": _c.get("mpmax", 14), "atk": 4, "dfn": 2, "agi": 7, "color": (170, 120, 235),
                           "alive": True, "guard": False, "st": {"atk": 0, "dfn": 0}, "dot": {"poison": 0, "burn": 0}, "cmd": None})
        if self.comps[1]["on"]:
            _c = self.comps[1]
            allies.append({"n": "Kael", "cls": "kael", "hp": _c["hp"], "max": _c["max"], "mp": _c.get("mp", 6),
                           "mpmax": _c.get("mpmax", 6), "atk": 5, "dfn": 5, "agi": 3, "color": (235, 160, 80),
                           "alive": True, "guard": False, "st": {"atk": 0, "dfn": 0}, "dot": {"poison": 0, "burn": 0}, "cmd": None})
        _fl = []
        for i, f in enumerate(foes):
            e = ENEMIES[f]
            _hp = e["hp"] - (10 if key == "boss" and "tess_bless" in self.flags and f == "warden_boss" else 0)
            _fl.append({"n": e["label"] + (f" {i+1}" if len(foes) > 1 else ""), "key": f, "hp": _hp, "max": _hp,
                        "atk": e["atk"], "dfn": e["dfn"], "agi": e["agi"], "color": e["color"], "alive": True,
                        "xp": e["xp"], "guard": False, "st": {"atk": 0, "dfn": 0}, "dot": {"poison": 0, "burn": 0}})
        self.combat = {"key": key, "round": 1, "log": [f"A wild party appears! ({len(_fl)} foes) — Round 1: orders!"],
                       "allies": allies, "foes": _fl, "stage": "input", "ii": 0, "mi": 0, "si": 0, "ti": 0,
                       "submenu": None, "targeting": None, "order": [], "oi": 0, "timer": 0.0, "fled": False,
                       "boss_cd": 0, "boss_enraged": False, "hero_first": True}
        self.state = "COMBAT"
        self.start_music("combat")
        self.clog(f"{allies[0]['n']}, give orders! (Up/Down+Enter, 1-6, Esc backs)")

    def clog(self, s):
        self.combat["log"] = (self.combat["log"] + [s])[-5:]

    def b_input_ally(self):
        c = self.combat
        alive = [a for a in c["allies"] if a["alive"]]
        if c["ii"] >= len(alive):
            return None
        return alive[c["ii"]]

    def b_lock(self, ally, action, ab=None, tgt=None):
        ally["cmd"] = (action, ab, tgt)
        c = self.combat
        c["ii"] += 1
        c["mi"] = 0
        c["si"] = 0
        c["ti"] = 0
        c["submenu"] = None
        nxt = self.b_input_ally()
        if nxt is None:
            self.b_begin_round()
        else:
            self.clog(f"{nxt['n']}, your orders!")

    # ----- battle math: damage / healing / buffs (screen-space feel) -----
    def b_xy_of(self, side, idx):
        if side == 0:
            return self.b_ally_xy(idx, len(self.combat["allies"]))
        return self.b_foe_xy(idx, len(self.combat["foes"]))

    def b_atk_mult(self, u):
        return 1 + 0.22 * u["st"]["atk"]

    def b_dfn_mult(self, u):
        return 1 + 0.22 * u["st"]["dfn"]

    def b_deal(self, src, dside, didx, power, nevermiss=False, burn=False, label=None):
        c = self.combat
        dst = (c["allies"] if dside == 0 else c["foes"])[didx]
        if not dst["alive"]:
            return 0
        x, y = self.b_xy_of(dside, didx)
        if not nevermiss and random.random() > 0.95:
            self.clog(f"{src['n']} misses {dst['n']}.")
            self.play("miss")
            self.feel_miss(x, y)
            return 0
        crit = random.random() < 0.12
        _hero_src = bool(src.get("hero")) and src.get("n") == self.hero_name
        if _hero_src and self.combat.get("hero_first"):
            self.combat["hero_first"] = False
            if self.has_talent("first_cut"):
                crit = True
        raw = max(1.0, src["atk"] * self.b_atk_mult(src) * 2.2 * power
                  - dst["dfn"] * self.b_dfn_mult(dst) * 1.4)
        raw *= random.uniform(0.85, 1.15) * (1.7 if crit else 1.0)
        if _hero_src:
            if label == "hits" and self.has_talent("keen_edge"):
                raw += 2
            if label == "Snipe" and self.has_talent("snipe_master"):
                raw += 3
            if self.has_talent("lone_wolf"):
                _af = len([a for a in self.combat["allies"] if a["alive"]])
                _ff = len([f for f in self.combat["foes"] if f["alive"]])
                if _ff > _af:
                    raw += 4
            if self.has_talent("salt_heart") and src["hp"] > src["max"] / 2:
                raw += 3
            if "Lone" in [t for t, _l in self.tag_sets()]:
                raw += 2
        if dst.get("guard"):
            raw /= 2
            dst["guard"] = False
        dmg = max(1, int(raw))
        dst["hp"] -= dmg
        self.clog(f"{src['n']} {'CRITS ' if crit else ''}{label or 'hits'} {dst['n']} for {dmg}.")
        self.play("hit")
        self.feel_hit(x, y, dmg, crit)
        if burn and dst["alive"]:
            _br = self.burn_rounds(3) if bool(src.get("hero")) and src.get("n") == self.hero_name else 3
            dst["dot"]["burn"] = _br
            self.clog(f"{dst['n']} is burning!")
            self.play("fire")
        if dst["hp"] <= 0:
            dst["hp"] = 0
            dst["alive"] = False
            self.clog(f"{dst['n']} falls!")
            if dside == 1:
                self.stats["kills"] += 1
            else:
                self.combat["ally_down"] = True
        return dmg

    def b_heal(self, src, dside, didx, amount, cure=False):
        c = self.combat
        dst = (c["allies"] if dside == 0 else c["foes"])[didx]
        if not dst["alive"]:
            return 0
        _hero_src = bool(src.get("hero")) and src.get("n") == self.hero_name
        if _hero_src and self.has_talent("apothecary"):
            amount += 6
        real = min(dst["max"] - dst["hp"], amount + random.randint(-2, 2))
        real = max(0, real)
        dst["hp"] += real
        if cure:
            dst["dot"]["poison"] = 0
            dst["dot"]["burn"] = 0
        x, y = self.b_xy_of(dside, didx)
        self.floaters.append({"x": x, "y": y + 40, "txt": f"+{real}", "col": (140, 255, 150), "t": 0.0, "big": False})
        self.clog(f"{src['n']} mends {dst['n']} (+{real}).")
        self.play("heal")
        return real

    def b_buff(self, src, targets, stat, stages):
        names = []
        for sside, sidx in targets:
            u = (self.combat["allies"] if sside == 0 else self.combat["foes"])[sidx]
            if not u["alive"]:
                continue
            u["st"][stat] = max(-2, min(2, u["st"][stat] + stages))
            names.append(u["n"])
        arrow = "UP" if stages > 0 else "DOWN"
        self.clog(f"{src['n']}: {stat} {arrow} ({', '.join(names) or 'no one'}).")
        self.play("ui")

    def feel_hit(self, x, y, dmg, crit):
        self.trauma = min(1.0, self.trauma + (0.55 if crit else 0.32))
        self.hitstop = 0.16 if crit else 0.09
        self.floaters.append({"x": x, "y": y, "txt": f"{dmg}",
                              "col": arcade.color.GOLD if crit else arcade.color.WHITE,
                              "t": 0.0, "big": crit})
        for _ in range(10 if crit else 6):
            self.particles.append({"x": x + random.uniform(-14, 14), "y": y + random.uniform(-8, 8),
                                   "vx": random.uniform(-70, 70), "vy": random.uniform(30, 120),
                                   "t": 0.0, "life": random.uniform(0.3, 0.6),
                                   "col": (255, 200, 90) if crit else (230, 230, 240)})

    def feel_miss(self, x, y):
        self.floaters.append({"x": x, "y": y, "txt": "MISS",
                              "col": (170, 170, 190), "t": 0.0, "big": False})

    def b_all_foes(self):
        return [(1, i) for i, f in enumerate(self.combat["foes"]) if f["alive"]]

    def b_all_allies(self):
        return [(0, i) for i, a in enumerate(self.combat["allies"]) if a["alive"]]

    def b_act_ally(self, ally):
        c = self.combat
        cmd = ally.get("cmd") or ("attack", None, 0)
        action, abid, tgt = cmd
        if action == "attack":
            _fl = [i for i, f in enumerate(c["foes"]) if f["alive"]]
            if not _fl:
                return
            _t = tgt if tgt in _fl else _fl[0]
            _burn = bool(ally.get("hero")) and self.has_talent("ember_edge")
            self.b_deal(ally, 1, _t, 1.0, burn=_burn)
        elif action in ("skill", "spell"):
            ab = ABILITIES[abid]
            if ally["mp"] < ab["mp"]:
                self.clog(f"{ally['n']}: not enough MP — strikes instead!")
                _fl = [i for i, f in enumerate(c["foes"]) if f["alive"]]
                if _fl:
                    self.b_deal(ally, 1, _fl[0], 1.0)
                return
            ally["mp"] -= ab["mp"]
            self.b_apply_ability(ally, ab, tgt, 0)
        elif action == "item":
            self.b_use_item(ally, abid, tgt)
        elif action == "duo":
            self.b_duo(ally, abid)
        elif action == "guard":
            ally["guard"] = True
            _heal = 0
            if bool(ally.get("hero")) and "Iron" in [t for t, _l in self.tag_sets()]:
                _heal = 4
                ally["hp"] = min(ally["max"], ally["hp"] + _heal)
            if bool(ally.get("hero")) and self.has_talent("bulwark"):
                ally["st"]["dfn"] = min(2, ally["st"]["dfn"] + 1)
            self.clog(f"{ally['n']} guards." + (f" (+{_heal})" if _heal else ""))
            self.play("ui")
        elif action == "flee":
            self.b_flee(ally)

    def b_apply_ability(self, src, ab, tgt, sside):
        c = self.combat
        scope = ab["scope"]
        if ab.get("focus"):
            src["mp"] = min(src.get("mpmax", src.get("mp", 0)), src.get("mp", 0) + 6)
            self.b_buff(src, [(sside, self.b_idx(sside, src))], "atk", 1)
            self.clog(f"{src['n']} focuses (+6 MP).")
            return
        if ab.get("heal"):
            if scope == "ally":
                _al = [i for i, a in enumerate(c["allies"]) if a["alive"]]
                _t = tgt if tgt in _al else _al[0]
                self.b_heal(src, 0, _t, ab["heal"])
                _hero_src = bool(src.get("hero")) and src.get("n") == self.hero_name
                if _hero_src and self.has_talent("mend_circle") and ab.get("label") == "Mend":
                    _si = self.b_idx(0, src)
                    self.b_heal(src, 0, _si, 4)
            return
        if ab.get("buff"):
            stat, stg = ab["buff"]
            if scope == "party":
                self.b_buff(src, self.b_all_allies(), stat, stg)
                _hero_src = bool(src.get("hero")) and src.get("n") == self.hero_name
                if _hero_src and ab.get("label") == "War Cry" and self.has_talent("drill_sergeant"):
                    self.b_buff(src, self.b_all_allies(), "dfn", 1)
                if _hero_src and ab.get("label") == "Smoke Veil" and self.has_talent("smoke_master"):
                    for _s, _i in self.b_all_allies():
                        _u = c["allies"][_i]
                        _u["dot"]["poison"] = 0
                        _u["dot"]["burn"] = 0
                    self.clog("Smoke clears the party's ailments.")
            elif scope == "self":
                self.b_buff(src, [(sside, self.b_idx(sside, src))], stat, stg)
            return
        targets = []
        if scope == "foe":
            _fl = [i for i, f in enumerate(c["foes"]) if f["alive"]]
            if _fl:
                targets = [(1, tgt if tgt in _fl else _fl[0])]
        elif scope == "allfoes":
            targets = self.b_all_foes()
        for dside, didx in targets:
            self.b_deal(src, dside, didx, ab.get("power", 1.0),
                        nevermiss=ab.get("nevermiss", False), burn=ab.get("burn", False),
                        label=ab["label"])
            if ab.get("debuff"):
                stat, stg = ab["debuff"]
                self.b_buff(src, [(dside, didx)], stat, -stg)
            if self.b_over():
                return

    def b_idx(self, side, unit):
        lst = self.combat["allies"] if side == 0 else self.combat["foes"]
        for i, u in enumerate(lst):
            if u is unit:
                return i
        return 0

    def b_use_item(self, ally, itemid, tgt):
        c = self.combat
        if self.inv.get(itemid, 0) <= 0:
            self.clog(f"No {itemid} left — {ally['n']} strikes instead!")
            _fl = [i for i, f in enumerate(c["foes"]) if f["alive"]]
            if _fl:
                self.b_deal(ally, 1, _fl[0], 1.0)
            return
        self.inv[itemid] -= 1
        if itemid == "bandage":
            _al = [i for i, a in enumerate(c["allies"]) if a["alive"]]
            self.b_heal(ally, 0, tgt if tgt in _al else _al[0], 12)
        elif itemid == "herb":
            _al = [i for i, a in enumerate(c["allies"]) if a["alive"]]
            self.b_heal(ally, 0, tgt if tgt in _al else _al[0], 6, cure=True)
        elif itemid == "oil":
            _fl = [i for i, f in enumerate(c["foes"]) if f["alive"]]
            if _fl:
                self.b_deal(ally, 1, tgt if tgt in _fl else _fl[0], 1.0, burn=True, label="Firebomb")

    def b_flee(self, ally):
        c = self.combat
        if c["key"] == "boss":
            self.clog("No escape from the Star Warden!")
            return
        p_agi = sum(a["agi"] for a in c["allies"] if a["alive"]) / max(1, len([a for a in c["allies"] if a["alive"]]))
        f_agi = sum(f["agi"] for f in c["foes"] if f["alive"]) / max(1, len([f for f in c["foes"] if f["alive"]]))
        _bonus = 0.15 if (bool(ally.get("hero")) and self.feat == "feat_tactician") else 0.0
        if random.random() < 0.55 + 0.08 * (p_agi - f_agi) + _bonus:
            c["fled"] = True
            self.clog(f"{ally['n']} throws dust — the party escapes!")
            self.play("ui")
        else:
            self.clog(f"{ally['n']} can't escape!")

    def b_duo(self, ally, who):
        c = self.combat
        rank = self.duo_rank("Nym" if who == "nym" else "Kael")
        if rank < 2:
            self.clog("The bond isn't sealed yet. (Seal it at a campfire.)")
            return
        cost = 4 if rank >= 5 else 6
        if ally.get("mp", 0) < cost:
            self.clog(f"Not enough MP for the duet ({ally.get('mp',0)}/{cost}).")
            self.play("miss")
            _fl = [i for i, f in enumerate(c["foes"]) if f["alive"]]
            if _fl:
                self.b_deal(ally, 1, _fl[0], 1.0)
            return
        ally["mp"] -= cost
        if who == "nym":
            _pw = 1.2 + 0.15 * rank
            for _i in [i for i, f in enumerate(c["foes"]) if f["alive"]]:
                self.b_deal(ally, 1, _i, _pw, burn=(rank >= 4), label="Starfall Duet")
                if self.b_over():
                    return
        else:
            for _s, _i in self.b_all_allies():
                c["allies"][_i]["guard"] = True
                _u = c["allies"][_i]
                _u["hp"] = min(_u["max"], _u["hp"] + 6)
            if rank >= 4:
                self.b_buff(ally, self.b_all_allies(), "atk", 1)
            self.clog("Kael: \"Shoulder to shoulder!\" Phalanx Oath holds (+6).")
            self.play("heal")

    def b_foe_act(self, foe):
        c = self.combat
        pals = [i for i, a in enumerate(c["allies"]) if a["alive"]]
        if not pals:
            return
        weak = min(pals, key=lambda i: c["allies"][i]["hp"])
        key = foe.get("key", "crab")
        if key == "crab":
            self.b_deal(foe, 0, weak, 1.0)
        elif key == "ghast":
            if random.random() < 0.4 and len(pals) > 1:
                for i in pals:
                    self.b_deal(foe, 0, i, 0.7, label="Wail")
                    if self.b_over():
                        return
            else:
                self.b_deal(foe, 0, weak, 1.2, label="Bolt")
        elif key == "caller":
            hurt = [i for i, f in enumerate(c["foes"]) if f["alive"] and f["hp"] < f["max"] * 0.6]
            if hurt and random.random() < 0.55:
                _t = min(hurt, key=lambda i: c["foes"][i]["hp"])
                self.b_heal(foe, 1, _t, 10)
            elif random.random() < 0.5:
                _fl = [i for i, f in enumerate(c["foes"]) if f["alive"]]
                self.b_buff(foe, [(1, random.choice(_fl))], "atk", 1)
            else:
                self.b_deal(foe, 0, weak, 1.1, label="Bolt")
        elif key == "warden_boss":
            self.b_boss_act(foe, weak)
        elif key == "deepmaw":
            if random.random() < 0.25:
                self.b_deal(foe, 0, weak, 2.0, label="Swallow Whole")
            else:
                self.b_deal(foe, 0, weak, 1.6, label="Rending Maw")

    def b_boss_act(self, foe, weak):
        c = self.combat
        if not c["boss_enraged"] and foe["hp"] < foe["max"] * 0.5:
            c["boss_enraged"] = True
            self.b_buff(foe, [(1, self.b_idx(1, foe))], "atk", 2)
            self.clog("The Star Warden burns brighter — ENRAGED!")
        c["boss_cd"] += 1
        if c["boss_cd"] % 3 == 0:
            for i in [j for j, a in enumerate(c["allies"]) if a["alive"]]:
                self.b_deal(foe, 0, i, 0.9, label="Starfall")
                if self.b_over():
                    return
        elif foe["hp"] < foe["max"] * 0.4 and c["boss_cd"] % 3 == 1 and random.random() < 0.5:
            self.b_heal(foe, 1, self.b_idx(1, foe), 12)
        else:
            self.b_deal(foe, 0, weak, 1.5, label="Star Slash")

    def b_begin_round(self):
        c = self.combat
        order = []
        for i, a in enumerate(c["allies"]):
            if a["alive"]:
                order.append((a["agi"] + random.random(), ("A", i)))
        for i, f in enumerate(c["foes"]):
            if f["alive"]:
                order.append((f["agi"] + random.random(), ("F", i)))
        order.sort(key=lambda t: -t[0])
        c["order"] = [t[1] for t in order]
        c["oi"] = 0
        c["stage"] = "resolve"
        c["timer"] = 0.6
        names = [ (c["allies"][i]["n"] if s == "A" else c["foes"][i]["n"]) for s, i in c["order"]]
        self.clog(f"Order: {' › '.join(names)}")

    def b_step(self):
        c = self.combat
        while c["oi"] < len(c["order"]):
            side, idx = c["order"][c["oi"]]
            c["oi"] += 1
            u = (c["allies"] if side == "A" else c["foes"])[idx]
            if not u["alive"] or self.b_over():
                continue
            if side == "A":
                self.b_act_ally(u)
            else:
                self.b_foe_act(u)
            self.b_sync()
            if self.b_over():
                self.b_finish()
                return
            return
        self.b_end_round()

    def b_end_round(self):
        c = self.combat
        # damage-over-time ticks, then new input round
        for side, lst in ((0, c["allies"]), (1, c["foes"])):
            for i, u in enumerate(lst):
                if not u["alive"]:
                    continue
                for kind in ("poison", "burn"):
                    if u["dot"][kind] > 0:
                        u["dot"][kind] -= 1
                        _d = roll(1, 6)
                        if side == 0 and u.get("hero") and self.has_talent("rift_scarred"):
                            _d = max(1, _d // 2)
                        u["hp"] -= _d
                        x, y = self.b_xy_of(side, i)
                        self.floaters.append({"x": x, "y": y + 20, "txt": f"{_d} {kind}",
                                              "col": (180, 255, 180) if kind == "poison" else (255, 170, 80),
                                              "t": 0.0, "big": False})
                        self.clog(f"{u['n']} suffers {_d} {kind}.")
                        if u["hp"] <= 0:
                            u["hp"] = 0
                            u["alive"] = False
                            self.clog(f"{u['n']} falls!")
                            if side == 1:
                                self.stats["kills"] += 1
                            else:
                                c["ally_down"] = True
        self.b_sync()
        if self.b_over():
            self.b_finish()
            return
        for u in c["allies"] + c["foes"]:
            u["guard"] = False
            u["cmd"] = None
        c["round"] += 1
        c["stage"] = "input"
        c["ii"] = 0
        c["mi"] = c["si"] = c["ti"] = 0
        c["submenu"] = None
        self.clog(f"— Round {c['round']}: orders! —")

    def b_over(self):
        c = self.combat
        if c.get("fled"):
            return True
        return not any(a["alive"] for a in c["allies"]) or not any(f["alive"] for f in c["foes"])

    def b_sync(self):
        c = self.combat
        if c["allies"]:
            self.hp = max(0, c["allies"][0]["hp"])
            self.mp = max(0, c["allies"][0].get("mp", 0))
        for a in c["allies"]:
            if a["n"] == "Nym":
                self.comps[0]["hp"] = max(0, a["hp"])
                self.comps[0]["mp"] = max(0, a.get("mp", 0))
            if a["n"] == "Kael":
                self.comps[1]["hp"] = max(0, a["hp"])
                self.comps[1]["mp"] = max(0, a.get("mp", 0))

    def b_finish(self):
        c = self.combat
        self.b_sync()
        if c.get("fled"):
            self.msg = "Escaped! No spoils."
            self.msg_t = 3
            self.state = "EXPLORE"
            self.map_id = self.return_map
            self.start_music("explore")
            return
        if not any(a["alive"] for a in c["allies"]):
            self.state = "GAMEOVER"
            return
        self.win_combat()

    def win_combat(self):
        c = self.combat
        key = c["key"]
        total = sum(f.get("xp", 0) for f in c["foes"])
        loot_g = {"e1": 15, "e2": 30, "e3": 45, "e4": 40, "maw": 60, "boss": 80}[key]
        self.gold += loot_g
        if self.has_talent("scrounge"):
            self.gold += 10
        self.inv["herb"] = self.inv.get("herb", 0) + (1 if key in ("e2", "e3") else 0)
        # flawless trail/chapel work earns both companions' respect (no one fell)
        if key in ("e2", "e3") and not c.get("ally_down"):
            for _w in ("Nym", "Kael"):
                self.approval[_w] = self.approval.get(_w, 0) + 1
            self.clog("Flawless victory — Nym and Kael approve (+1).")
        # catch breath: small MP back so dungeons don't starve casters
        self.mp = min(self.max_mp, self.mp + 4)
        for cc in self.comps:
            cc["mp"] = min(cc.get("mpmax", 6), cc.get("mp", 0) + 4)
        self.gain_xp(total)
        if key == "e1":
            self.flags["e1_done"] = True
            self.quests["q3"] = max(self.quests["q3"], 1)
        if key == "e2":
            self.flags["e2_done"] = True
        if key == "e3":
            self.flags["e3_done"] = True
            self.quests["q4"] = 2
        if key == "boss":
            self.flags["boss_done"] = True
            self.quests["q5"] = 1
        if key == "e4":
            self.flags["e4_done"] = True
            self.inv["oil"] = self.inv.get("oil", 0) + 1
        if key == "maw":
            self.flags["maw_done"] = True
            self.inv["herb"] = self.inv.get("herb", 0) + 2
        self.msg = f"Victory! +{total} XP +{loot_g}g" + (" +10 scrounged" if self.has_talent("scrounge") else "") + (" Flawless: companions approve." if key in ("e2", "e3") and not c.get("ally_down") else "")
        self.msg_t = 4
        self.play("ui")
        self.state = "EXPLORE"
        self.map_id = self.return_map
        self.start_music("explore")

    # ---------- interact ----------
    def interact_list(self):
        L = []
        # ambient NPCs first (data-driven)
        for _k, _n, _x, _y, _c in NPCS.get(self.map_id, []):
            if _k == "per" and "q8_done" in self.flags:
                continue
            L.append({"id": f"npc_{_k}", "x": _x, "y": _y, "label": f"Talk: {_n}"})
        if self.map_id == "shore":
            if "q1_done" not in self.flags:
                L.append({"id": "nym", "x": 540, "y": 260, "label": "Wake: talk to Nym"})
            else:
                if "e1_done" not in self.flags:
                    L.append({"id": "fight_e1", "x": 1000, "y": 420, "label": "Fight: crabs guarding oil (E)"})
                L.append({"id": "oil", "x": 330, "y": 430, "label": "Take oil flask"})
                if "q2_done" not in self.flags and "q2_dark" not in self.flags and "q2_dead" not in self.flags:
                    L.append({"id": "sailor", "x": 960, "y": 300, "label": "Tend the sailor"})
                if "e1_done" in self.flags:
                    L.append({"id": "pyre", "x": 1220, "y": 560, "label": "Light shore pyre (needs oil)"})
                if "q8" in self.flags and "q8_done" not in self.flags and "e1_done" in self.flags:
                    L.append({"id": "net", "x": 1000, "y": 470, "label": "Per's tangled net"})
                if "cache_shore" not in self.flags and "revealed_shore" in self.flags:
                    L.append({"id": "cache_shore", "x": 200, "y": 700, "label": "Disturbed sand"})
            L.append({"id": "go_hold", "x": 330, "y": 480, "label": "Gangplank: wreck hold →"})
            L.append({"id": "go_camp", "x": 1300, "y": 150, "label": "Travel: Hollow Camp →"})
            L.append({"id": "go_cove", "x": 1350, "y": 700, "label": "Smuggler path → (east)"})
            L.append({"id": "plaque_tide", "x": 1100, "y": 200, "label": "Read: tide plaque"})
        elif self.map_id == "camp":
            L.append({"id": "serren", "x": 220, "y": 600, "label": "Talk: Serren the trader"})
            L.append({"id": "fire_rest", "x": 700, "y": 300, "label": "Campfire: rest, sparks, respec"})
            if "e2_done" not in self.flags:
                L.append({"id": "fight_e2", "x": 1050, "y": 650, "label": "Ambush on the trail! (E)"})
            else:
                L.append({"id": "go_chapel", "x": 1300, "y": 150, "label": "Travel: Star Chapel →"})
            L.append({"id": "go_shore", "x": 100, "y": 150, "label": "← Back: Riftshore"})
            if "cache_camp" not in self.flags and "revealed_camp" in self.flags:
                L.append({"id": "cache_camp", "x": 1200, "y": 750, "label": "Loose cliff stones"})
            L.append({"id": "plaque_sun", "x": 400, "y": 700, "label": "Read: sun plaque"})
        elif self.map_id == "chapel":
            if "e3_done" not in self.flags:
                L.append({"id": "fight_e3", "x": 700, "y": 480, "label": "Chapel guards (E)"})
            else:
                if "boss_done" not in self.flags:
                    if "font_open" in self.flags:
                        L.append({"id": "fight_boss", "x": 700, "y": 640, "label": "FACE the Star Warden (E)"})
                    else:
                        L.append({"id": "seal", "x": 700, "y": 640, "label": "Sealed door (braziers?)"})
                else:
                    L.append({"id": "altar", "x": 700, "y": 720, "label": "Touch the Pale Star"})
            if "e3_done" in self.flags and "font_open" not in self.flags:
                for _bid, _bx, _by in (("braz_sun", 480, 640), ("braz_tide", 700, 660), ("braz_star", 920, 640)):
                    L.append({"id": _bid, "x": _bx, "y": _by, "label": f"Light: {_bid[5:].upper()} brazier"})
            L.append({"id": "go_camp2", "x": 700, "y": 100, "label": "← Back: Camp"})
            if "cache_chapel" not in self.flags and "revealed_chapel" in self.flags:
                L.append({"id": "cache_chapel", "x": 250, "y": 700, "label": "Hollow pew"})
            L.append({"id": "plaque_star", "x": 1050, "y": 250, "label": "Read: star plaque"})
            L.append({"id": "plaque_deep", "x": 250, "y": 250, "label": "Read: drowned plaque"})
        elif self.map_id == "hold":
            if "e4_done" not in self.flags:
                L.append({"id": "fight_e4", "x": 950, "y": 250, "label": "Ghasts nest here (E)"})
            else:
                if "q7" in self.flags and "q7_done" not in self.flags:
                    L.append({"id": "stash", "x": 800, "y": 500, "label": "Joss's pay chest"})
                if "ledger_found" not in self.flags:
                    L.append({"id": "ledger", "x": 550, "y": 650, "label": "Read the ledger"})
            L.append({"id": "go_shore2", "x": 150, "y": 150, "label": "← Gangplank out"})
            L.append({"id": "go_cove2", "x": 1100, "y": 700, "label": "Dark tunnel →"})
        elif self.map_id == "cove":
            if "maw_done" not in self.flags:
                L.append({"id": "fight_maw", "x": 300, "y": 700, "label": "Something moves below (E)"})
            if "cache_cove" not in self.flags and "revealed_cove" in self.flags:
                L.append({"id": "cache_cove", "x": 1050, "y": 620, "label": "Still tide pool"})
            L.append({"id": "go_shore3", "x": 200, "y": 150, "label": "← Climb out"})
        return L

    def nearest(self):
        best, bd = None, 90
        for it in self.interact_list():
            d = math.hypot(self.px - it["x"], self.py - it["y"])
            if d < bd:
                best, bd = it, d
        return best

    def do_interact(self, it):
        i = it["id"]
        if i == "nym":
            self.comps[0]["on"] = True
            self.quests["q1"] = 1
            self.talk("wake")
        elif i == "oil":
            self.inv["oil"] = self.inv.get("oil", 0) + 1
            self.msg, self.msg_t = "Took oil flask. (Q3: fuel for the pyre)", 3
            self.play("ui")
            self.quests["q3"] = 1
        elif i == "sailor":
            self.quests["q2"] = 1
            self.talk("sailor")
        elif i == "fight_e1":
            self.start_combat("e1")
        elif i == "fight_e2":
            self.start_combat("e2")
        elif i == "fight_e3":
            self.start_combat("e3")
        elif i == "fight_e4":
            self.start_combat("e4")
        elif i == "fight_maw":
            self.start_combat("maw")
        elif i == "fight_boss":
            self.start_combat("boss")
        elif i == "pyre":
            if self.inv.get("oil", 0) > 0 and "e1_done" in self.flags:
                self.inv["oil"] -= 1
                self.flags["pyre_lit"] = True
                self.quests["q3"] = 2
                self.gain_xp(50)
                self.msg, self.msg_t = "The pyre catches. The camp will see it. (Q3 done)", 4
                self.play("fire")
            else:
                self.msg, self.msg_t = "Need: clear crabs (oil route) + 1 oil flask.", 3
        elif i == "go_camp":
            if "pyre_lit" not in self.flags:
                self.msg, self.msg_t = "Light the shore pyre first — the camp watches for it.", 3
            else:
                self.goto_map("camp")
        elif i == "go_shore":
            self.goto_map("shore", 1250, 180)
        elif i == "go_chapel":
            self.goto_map("chapel")
        elif i == "go_camp2":
            self.goto_map("camp", 1200, 200)
        elif i == "serren":
            self.talk("serren")
        elif i == "fire_rest":
            self.talk("campfire")
        elif i == "altar":
            self.quests["q5"] = 1
            self.talk("altar")
        elif i.startswith("npc_"):
            _k = i[4:]
            _nodes = {"per": "per", "maren": "maren", "joss": "joss", "tess": "tess", "pilgrim": "pilgrim"}
            if _k == "maren" and "q6_done" in self.flags:
                self.talk("maren_done")
            elif _k == "per" and "q8" in self.flags and "net_found" in self.flags:
                self.talk("per_done")
            elif _k == "per" and "q8" in self.flags:
                self.msg, self.msg_t = "Per's net is still tangled by the west pools.", 3
                self.play("miss")
            else:
                self.talk(_nodes.get(_k, "serren"))
        elif i == "net":
            self.inv["oil"] = self.inv.get("oil", 0)  # no-op guard
            self.msg, self.msg_t = "Slogged and stinking. Haul it to Per.", 3
            self.flags["net_found"] = True
            self.play("ui")
        elif i in ("braz_sun", "braz_tide", "braz_star"):
            self.brazier(i[5:])
        elif i == "seal":
            self.msg, self.msg_t = "Sealed by old prayer. Three braziers watch: sun, tide, star.", 4
            self.play("miss")
        elif i in ("cache_shore", "cache_camp", "cache_chapel", "cache_cove"):
            _loot = {"cache_shore": ("gold", 25), "cache_camp": ("bandage", 2),
                     "cache_chapel": ("oil", 2), "cache_cove": ("herb", 3)}[i]
            _k, _n = _loot
            if _k == "gold":
                self.gold += _n
            else:
                self.inv[_k] = self.inv.get(_k, 0) + _n
            self.flags[i] = True
            self.gain_xp(15)
            self.msg, self.msg_t = f"Cache! +{_n} {_k}.", 3
            self.play("ui")
        elif i in ("plaque_sun", "plaque_tide", "plaque_star", "plaque_deep"):
            self.talk(i)
        elif i == "stash":
            self.gold += 50
            self.flags["q7_done"] = True
            self.quests["q7"] = 2
            self.approval["Kael"] = self.approval.get("Kael", 0) + 1
            self.gain_xp(60)
            self.msg, self.msg_t = "Pay chest (+50g). Kael gets his papers. (Q7 done)", 4
            self.play("ui")
        elif i == "ledger":
            self.flags["ledger_found"] = True
            self.msg, self.msg_t = "Debts, bribes, a bought discharge... Serren should answer for this.", 4
            self.play("ui")
        elif i == "go_hold":
            self.goto_map("hold")
        elif i == "go_shore2":
            self.goto_map("shore", 180, 550)
        elif i == "go_cove2":
            self.goto_map("cove")
        elif i == "go_cove":
            self.goto_map("cove")
        elif i == "go_shore3":
            self.goto_map("shore", 1250, 650)

    def brazier(self, which):
        if "font_open" in self.flags:
            return
        _ord = getattr(self, "braz_order", [])
        _ord = _ord + [which]
        if _ord == ["sun", "tide", "star"][:len(_ord)]:
            self.braz_order = _ord
            self.play("fire")
            if len(_ord) == 3:
                self.flags["font_open"] = True
                self.gain_xp(30)
                self.msg, self.msg_t = "SUN, TIDE, STAR — the seal sighs open.", 4
            else:
                self.msg, self.msg_t = f"The {which} flame catches... ({len(_ord)}/3)", 3
        else:
            self.braz_order = []
            self.msg, self.msg_t = "The flames gutter out. Wrong order.", 3
            self.play("miss")

    # ===== RENDER HELPERS =====
    def _get_tile_type(self, m, tx, ty, base_tile):
        """Determine tile type with transitions at boundaries."""
        # Shore: sand above sea line, water below with sand-water transition
        if self.map_id == "shore":
            sea_ty = m["sea"] // 64
            if ty < sea_ty - 1:
                return base_tile  # sand
            elif ty == sea_ty - 1:
                return "sand_water"  # transition
            elif ty == sea_ty:
                return "water_shore"  # shallow water
            else:
                return "water_deep"  # deep water
        
        # Chapel: stone with cracked variants near altar
        if self.map_id == "chapel":
            if 450 < (tx * 64) < 950 and 450 < (ty * 64) < 750:
                if ((tx + ty) % 4 == 0):
                    return "stone_cracked"
            return base_tile
        
        # Hold: wood planks with variations
        if self.map_id == "hold":
            if ((tx + ty) % 5 == 0):
                return "wood_dark"
            elif ((tx + ty) % 7 == 0):
                return "wood_worn"
            return base_tile
        
        # Cove: sand with tide pools
        if self.map_id == "cove":
            if 500 < (tx * 64) < 1100 and 550 < (ty * 64) < 700:
                return "sand_wet"
            return base_tile
        
        return base_tile

    def _draw_water(self, m, cam_x, cam_y):
        """Animated water with shoreline foam."""
        sea_y = m["sea"]
        tile_size = 64
        time_offset = self.t * 2.0
        
        min_tx = max(0, int(cam_x // 64) - 1)
        max_tx = min(m["w"] // 64, int((cam_x + SCREEN_W) // 64) + 1)
        
        for tx in range(min_tx, max_tx + 1):
            wx = tx * 64
            sx = wx - cam_x
            
            # Shore foam line
            fy = sea_y - cam_y
            wave = math.sin((tx * 0.7) + self.t * 2.0) * 3
            foam_y = fy + wave
            
            # Foam line
            arcade.draw_line(sx, foam_y, sx + 64, foam_y, (255, 255, 255, 120), 2)
            
            # Water tiles below shore
            for ty in range((sea_y // 64) + 1, (m["h"] // 64) + 1):
                wy = ty * 64
                sx = tx * 64 - cam_x
                sy = wy - cam_y
                if -64 < sx < SCREEN_W + 64 and -64 < sy < SCREEN_H + 64:
                    wave_offset = math.sin((tx * 0.5 + ty * 0.3) + self.t * 3) * 2
                    water_type = "water_shore" if ty == (sea_y // 64) + 1 else "water_deep"
                    self.draw_tile(water_type, sx, sy + wave_offset)

    def _draw_wreck_interior(self, cam_x, cam_y):
        """Wrecked ship hull interior with planks, debris, cargo."""
        # Wreck bounds
        wx_start, wy_start = 260, 380
        wx_end, wy_end = 520, 426
        
        # Hull planks
        for tx in range(wx_start // 64, wx_end // 64 + 1):
            for ty in range(wy_start // 64, wy_end // 64 + 1):
                wx, wy = tx * 64, ty * 64
                sx, sy = wx - cam_x, wy - cam_y
                if -64 < sx < SCREEN_W + 64 and -64 < sy < SCREEN_H + 64:
                    if ((tx + ty) % 3 == 0):
                        self.draw_tile("wood_dark", sx, sy)
                    elif ((tx + ty) % 5 == 0):
                        self.draw_tile("wood_worn", sx, sy)
                    else:
                        self.draw_tile("wood_plank", sx, sy)
        
        # Debris piles
        debris = [(340, 400), (400, 410), (460, 390), (300, 395)]
        for dx, dy in debris:
            sx, sy = dx - cam_x, dy - cam_y
            if -64 < sx < SCREEN_W + 64 and -64 < sy < SCREEN_H + 64:
                self.draw_tile("cargo_crate", sx, sy)

    def _draw_hold_interior(self, cam_x, cam_y):
        """Ship hold: wooden planks, support beams, cargo areas."""
        for tx in range(0, 1200 // 64 + 1):
            for ty in range(0, 800 // 64 + 1):
                wx, wy = tx * 64, ty * 64
                sx, sy = wx - cam_x, wy - cam_y
                if -64 < sx < SCREEN_W + 64 and -64 < sy < SCREEN_H + 64:
                    if tx % 8 == 0:
                        self.draw_tile("beam_vertical", wx - cam_x, wy - cam_y)
                    elif ty % 8 == 0:
                        self.draw_tile("beam_horizontal", wx - cam_x, wy - cam_y)
                    elif ((tx + ty) % 6 == 0):
                        self.draw_tile("wood_worn", sx, sy)
                    else:
                        self.draw_tile("wood_plank", sx, sy)

    def _draw_chapel_interior(self, cam_x, cam_y):
        """Chapel: stone floor, cracked near altar, pews, braziers."""
        for tx in range(0, 1400 // 64 + 1):
            for ty in range(0, 900 // 64 + 1):
                wx, wy = tx * 64, ty * 64
                sx, sy = wx - cam_x, wy - cam_y
                if -64 < sx < SCREEN_W + 64 and -64 < sy < SCREEN_H + 64:
                    dist_to_altar = math.hypot(wx - 700, wy - 700)
                    if dist_to_altar < 200 and ((tx + ty) % 3 == 0):
                        self.draw_tile("stone_cracked", sx, sy)
                    elif dist_to_altar < 350 and ((tx + ty) % 5 == 0):
                        self.draw_tile("stone_worn", sx, sy)
                    else:
                        self.draw_tile("stone", sx, sy)
        
        # Pews
        for row in range(5):
            for col in range(2):
                px = 480 + col * 200
                py = 400 + row * 40
                sx, sy = px - cam_x, py - cam_y
                if -64 < sx < SCREEN_W + 64 and -64 < sy < SCREEN_H + 64:
                    self.draw_tile("pew", sx, sy)

    def _draw_wall_trim(self, sx, sy, ww, wh):
        """Draw wood/stone trim along walls."""
        if not self.tile_tex.get("wood"):
            return
        steps_x = max(1, int(ww / 64))
        steps_y = max(1, int(wh / 64))
        
        for i in range(steps_x):
            self.draw_tile("wood", sx + i * 64, sy + wh - 32)
            self.draw_tile("wood", sx + i * 64, sy - 32)
        for i in range(steps_y):
            self.draw_tile("wood", sx - 32, sy + i * 64)
            self.draw_tile("wood", sx + ww - 32, sy + i * 64)

    def _draw_prop(self, label, sx, sy):
        """Draw interactive props with proper sprites."""
        prop_tiles = {
            "PYRE (east)": "pyre_unlit",
            "CAMPFIRE": "campfire",
            "ALTAR": "altar",
            "FONT": "font",
            "PEWS": "pew",
            "TENTS": "tent",
            "STORE": "shop_stall",
            "WRECK": "wreck_hull",
            "ROCKS": "rocks_large",
            "SPLIT HULL": "hull_split",
            "PAY CHEST": "chest",
            "LEDGER DESK": "desk",
            "NEST": "nest",
            "SMUGGLER FIRE": "campfire_small",
            "TIDE POOL": "tide_pool",
            "DARK WATER": "water_dark",
            "SUN BRAZIER": "brazier_sun",
            "TIDE BRAZIER": "brazier_tide",
            "STAR BRAZIER": "brazier_star",
            "UNLIT": "pyre_unlit",
        }
        
        tile = prop_tiles.get(label)
        if tile and self.draw_tile(tile, sx, sy, 64):
            return
        
        # Fallback
        if "PYRE" in label or "CAMPFIRE" in label or "ALTAR" in label:
            lit = self.flags.get("pyre_lit") and "PYRE" in label
            # pyre_base: draw as 2x1 tiles (40x26 approx = 64x32, use 2 tiles)
            self.draw_tile("pyre_base", sx - 20, sy - 26, 32)
            self.draw_tile("pyre_base", sx + 12, sy - 26, 32)
            if lit or "CAMPFIRE" in label or "ALTAR" in label:
                self.draw_tile("fire", sx, sy + 6, 36 if "PYRE" in label else 26)
                self.draw_tile("fire_core", sx, sy + 6, 18 if "PYRE" in label else 9)
            else:
                arcade.draw_text("UNLIT", sx, sy - 12, (45, 35, 25), 10, anchor_x="center", bold=True)
        else:
            arcade.draw_lbwh_rectangle_filled(sx - 30, sy - 10, 60, 20, (0, 0, 0, 40))
        arcade.draw_text(label, sx, sy + 18, (50, 42, 30), 10, anchor_x="center", bold=True)

    def _draw_lighting(self, hx, hy):
        """Atmospheric lighting: vignette, fire glow, ambient."""
        # Vignette
        for r in range(0, 400, 50):
            alpha = max(0, 30 - r // 10)
            arcade.draw_circle_filled(hx, hy, SCREEN_W + r, (0, 0, 0, alpha))
        
        # Fire glow on shore/camp
        if self.map_id in ("shore", "camp") and self.flags.get("pyre_lit"):
            for _ in range(3):
                arcade.draw_circle_filled(hx, hy, 100 + _ * 30, (255, 180, 80, 12 - _ * 4))



# ===== CHARACTER SPRITE SYSTEM =====
    def _init_character_sprites(self):
        """Initialize character sprite system with 4-directional animated sprites."""
        self.char_sprites = {}

        # Character definitions with their color schemes
        char_defs = {
            "hero": {"colors": [(200, 170, 60), (255, 220, 90), (240, 203, 170)], "scale": 1.0},
            "nym": {"colors": [(170, 120, 235), (200, 150, 245), (240, 203, 170)], "scale": 0.9},
            "kael": {"colors": [(235, 160, 80), (255, 190, 120), (232, 190, 160)], "scale": 1.1},
            "maren": {"colors": [(150, 200, 140), (180, 220, 170), (220, 210, 190)], "scale": 0.95},
            "per": {"colors": [(90, 170, 220), (120, 190, 240), (220, 210, 190)], "scale": 0.95},
            "joss": {"colors": [(120, 130, 150), (150, 160, 180), (200, 190, 180)], "scale": 1.0},
            "tess": {"colors": [(220, 210, 230), (200, 190, 210), (240, 230, 240)], "scale": 0.95},
            "pilgrim": {"colors": [(160, 140, 170), (140, 120, 150), (200, 190, 180)], "scale": 0.9},
            "mourn_crab": {"colors": [(200, 90, 80), (220, 110, 100), (180, 70, 60)], "scale": 0.8},
            "wreckghast": {"colors": [(150, 160, 220), (180, 190, 240), (130, 140, 200)], "scale": 0.9},
            "tidecaller": {"colors": [(90, 200, 170), (120, 220, 190), (70, 180, 150)], "scale": 1.0},
            "star_warden": {"colors": [(220, 200, 90), (240, 220, 120), (200, 180, 70)], "scale": 1.2},
            "deepmaw": {"colors": [(120, 40, 60), (160, 80, 100), (90, 30, 50)], "scale": 1.1},
        }

        for char_id, defn in char_defs.items():
            self.char_sprites[char_id] = self._generate_character_sprites(defn)

        self.char_anim_state = {}

    def _generate_character_sprites(self, defn):
        """Generate 4-directional procedural sprites for a character type."""
        colors = defn["colors"]
        main, accent, skin = colors[0], colors[1], colors[2]
        scale = defn.get("scale", 1.0)

        sprites = {"down": [], "up": [], "left": [], "right": []}

        for dir_name in ["down", "up", "left", "right"]:
            frames = []
            for frame in range(7):
                is_idle = frame == 0
                walk_frame = (frame - 1) % 6 if not is_idle else 0

                bob = 0
                leg_offset = 0
                arm_swing = 0
                head_bob = 0

                if not is_idle:
                    cycle = walk_frame / 6.0
                    bob = math.sin(cycle * 2 * math.pi) * 2
                    leg_offset = math.sin(cycle * 2 * math.pi) * 3
                    arm_swing = math.sin(cycle * 2 * math.pi) * 2
                    head_bob = math.sin(cycle * 2 * math.pi) * 1

                frames.append({
                    "main_color": main,
                    "accent_color": accent,
                    "skin_color": skin,
                    "bob": bob,
                    "leg_offset": leg_offset,
                    "arm_swing": arm_swing,
                    "head_bob": head_bob,
                    "direction": dir_name,
                    "is_idle": is_idle,
                })
            sprites[dir_name] = frames

        return sprites

    def _draw_character_sprite(self, sx, sy, char_id, face=1, phase=0.0, big=False, selected=False, name=""):
        if char_id not in self.char_sprites:
            return self.draw_guy(sx, sy, (128, 128, 128), name, face, phase, big, selected)

        dir_map = {1: "right", -1: "left"}
        direction = dir_map.get(face, "down")

        anim_key = f"{char_id}_{id(name)}"
        if anim_key not in self.char_anim_state:
            self.char_anim_state[anim_key] = {"frame": 0, "timer": 0, "dir": direction}

        state = self.char_anim_state[anim_key]
        state["timer"] += 1/60

        if state["timer"] > 0.15:
            state["timer"] = 0
            if not self.char_sprites[char_id][direction][0]["is_idle"]:
                state["frame"] = (state["frame"] + 1) % 6

        frame_idx = state["frame"] if not self.char_sprites[char_id][direction][0]["is_idle"] else 0
        frame_data = self.char_sprites[char_id][direction][frame_idx]

        self._render_character_frame(sx, sy, frame_data, big, selected, name)

    def _render_character_frame(self, sx, sy, frame, big, selected, name):
        scale = 1.5 if big else 1.0
        body_h = int(26 * 1.0)
        body_w = int(22 * 1.0)
        head_r = int(10 * 1.0)

        bob = frame.get("bob", 0)
        leg_off = frame.get("leg_offset", 0)
        arm_sw = frame.get("arm_swing", 0)
        head_bob = frame.get("head_bob", 0)

        main = frame.get("main_color", (128, 128, 128))
        accent = frame.get("accent_color", (200, 200, 200))
        skin = frame.get("skin_color", (240, 203, 170))

        arcade.draw_circle_filled(sx, sy - 14 + bob, 14, (0, 0, 0, 70))
        arcade.draw_lbwh_rectangle_filled(sx - 11, sy - 12 + bob, body_w, body_h, main)
        arcade.draw_lbwh_rectangle_filled(sx - 10, sy + 14 + bob, 20, 7, accent)
        arcade.draw_circle_filled(sx + 2, sy + 12 + bob + head_bob, 10, skin)
        arcade.draw_lbwh_rectangle_filled(sx - 10, sy + 14 + bob + head_bob, 20, 7, (main[0]//2, main[1]//2, main[2]//2))
        arcade.draw_circle_filled(sx + 5, sy + 11 + bob + head_bob, 2, arcade.color.BLACK)
        if selected:
            arcade.draw_circle_outline(sx, sy + bob, 20, arcade.color.GOLD, 2)
        arcade.draw_text(name, sx, sy + 26 + bob, arcade.color.WHITE, 12, anchor_x="center", bold=True)


    # ---------- input ----------
    def on_key_press(self, key, modifiers):
        self.keys.add(key)
        K = arcade.key
        numkeys = {getattr(K, "_1", 49): 0, getattr(K, "_2", 50): 1, getattr(K, "_3", 51): 2, getattr(K, "_4", 52): 3,
                   getattr(K, "NUM_1", 49): 0, getattr(K, "NUM_2", 50): 1, 49: 0, 50: 1, 51: 2, 52: 3}

        # global audio keys — work on EVERY screen incl. TITLE/CREATOR
        if key == K.M:
            self.muted = not self.muted
            self.sync_mute()
            self.msg, self.msg_t = f"Sound {'OFF' if self.muted else 'ON'} (M).", 2
        elif key == K.N:
            self.music_muted = not self.music_muted
            self.sync_mute()
            self.msg, self.msg_t = f"Music {'OFF' if self.music_muted else 'ON'} (N).", 2
        elif key == K.P:
            self.muted = False
            self.music_muted = False
            self.audio_err = ""
            self.sync_mute()
            self.ensure_mixer()
            self._music_mode = ""
            self.start_music("combat" if self.state == "COMBAT" else "explore")
            self.play("levelup")
            self.msg, self.msg_t = f"♪ sfx via {self.audio_backend} | ♫ busy={self.music_busy()} err:{self.audio_err or 'none'}", 4
            if self.state == "COMBAT" and getattr(self, "combat", None):
                self.clog(f"♪ sfx via {self.audio_backend} | ♫ busy={self.music_busy()}.")
            if self.state == "TITLE":
                return

        if self.state == "TITLE":
            if key in (K.ENTER, K.SPACE):
                self.state = "CREATOR_ORIGIN"
                self.creator_opts = list(ORIGINS.keys())
                self.start_music("explore")
            return
        if self.state in ("CREATOR_ORIGIN", "CREATOR_CLASS"):
            opts = list(ORIGINS.keys()) if self.state == "CREATOR_ORIGIN" else list(CLASSES.keys())
            cur = self.origin_id if self.state == "CREATOR_ORIGIN" else self.class_id
            try:
                idx = opts.index(cur)
            except ValueError:
                idx = 0
            if key in (K.UP, K.W):
                idx = (idx - 1) % len(opts)
            elif key in (K.DOWN, K.S):
                idx = (idx + 1) % len(opts)
            elif key in (K.ENTER, K.SPACE):
                if self.state == "CREATOR_ORIGIN":
                    self.state = "CREATOR_CLASS"
                else:
                    self.state = "CREATOR_NAME"
                    self.hero_name = ""
                return
            elif key in numkeys and numkeys[key] < len(opts):
                if self.state == "CREATOR_ORIGIN":
                    self.origin_id = opts[numkeys[key]]
                    self.state = "CREATOR_CLASS"
                else:
                    self.class_id = opts[numkeys[key]]
                    self.state = "CREATOR_NAME"
                    self.hero_name = ""
                return
            if self.state == "CREATOR_ORIGIN":
                self.origin_id = opts[idx]
            else:
                self.class_id = opts[idx]
            return
        if self.state == "CREATOR_NAME":
            if key == K.ENTER:
                self.finalize()
                self.state = "CINEMATIC"
                self.cine_i = 0
                self.cine_c = 0
            elif key == K.BACKSPACE:
                self.hero_name = self.hero_name[:-1]
            elif key == K.ESCAPE:
                self.state = "CREATOR_CLASS"
            return
        if self.state == "CINEMATIC":
            if key in (K.SPACE, K.ENTER):
                full = CINEMA[self.cine_i]
                if self.cine_c < len(full):
                    self.cine_c = len(full)
                else:
                    self.cine_i += 1
                    self.cine_c = 0
                    if self.cine_i >= len(CINEMA):
                        self.state = "EXPLORE"
                        self.play_t0 = time.time()
                        self.start_music("explore")
            return
        if self.state == "EXPLORE":
            if key == K.E:
                it = self.nearest()
                if it:
                    self.do_interact(it)
            elif key == K.J:
                self.journal = not self.journal
            elif key == K.K:
                self.sheet = not self.sheet
            elif key == K.B:
                if self.inv.get("bandage", 0) > 0 and self.hp < self.max_hp:
                    self.inv["bandage"] -= 1
                    self.hp = min(self.max_hp, self.hp + 12)
                    self.msg, self.msg_t = "+12 HP (bandage).", 2
                    self.play("heal")
            elif key == K.F5:
                self.save()
            elif key == K.F9:
                self.load()
            elif key == K.ESCAPE:
                self.paused_from = "EXPLORE"
                self.state = "PAUSE"
            return
        if self.state == "DIALOGUE":
            vis = self.visible_opts()
            n = max(1, len(vis))
            if self.sel >= n:
                self.sel = 0
            if key in (K.UP, K.W):
                self.sel = (self.sel - 1) % n
            elif key in (K.DOWN, K.S):
                self.sel = (self.sel + 1) % n
            elif key in (K.ENTER, K.SPACE):
                if self.reveal < len(self.cur()["text"]):
                    self.reveal = len(self.cur()["text"])
                elif vis:
                    _idx, _opt = vis[self.sel]
                    self.choose(_opt, _idx)
                    self.sel = 0
            elif vis and key in numkeys and numkeys[key] < n:
                self.sel = numkeys[key]
                _idx, _opt = vis[self.sel]
                self.choose(_opt, _idx)
                self.sel = 0
            return
        if self.state == "DRAFT":
            n = len(self.draft_offer)
            if key in (K.UP, K.W):
                self.draft_sel = (self.draft_sel - 1) % n
                self.play("ui")
            elif key in (K.DOWN, K.S):
                self.draft_sel = (self.draft_sel + 1) % n
                self.play("ui")
            elif key in (K.ENTER, K.SPACE):
                self.play("ui")
                self.take_draft(self.draft_offer[self.draft_sel % n])
            elif key in numkeys and numkeys[key] < n:
                self.take_draft(self.draft_offer[numkeys[key]])
            return
        if self.state == "FEAT":
            n = len(self.feat_offer)
            if key in (K.UP, K.W):
                self.feat_sel = (self.feat_sel - 1) % n
                self.play("ui")
            elif key in (K.DOWN, K.S):
                self.feat_sel = (self.feat_sel + 1) % n
                self.play("ui")
            elif key in (K.ENTER, K.SPACE):
                self.take_feat(self.feat_offer[self.feat_sel % n])
            elif key in numkeys and numkeys[key] < n:
                self.take_feat(self.feat_offer[numkeys[key]])
            return
        if self.state == "COMBAT":
            self.b_input(key, numkeys)
            return
        if self.state == "TRADER":
            stock = [("bandage", 8), ("oil", 10), ("herb", 6), ("sword1", 60), ("charm1", 50)]
            if key in (K.UP, K.W):
                self.shop_sel = (self.shop_sel - 1) % len(stock)
            elif key in (K.DOWN, K.S):
                self.shop_sel = (self.shop_sel + 1) % len(stock)
            elif key in (K.ENTER, K.SPACE):
                sid, price = stock[self.shop_sel]
                if self.gold >= price:
                    self.gold -= price
                    if sid in ("sword1",):
                        self.equip_atk += ITEMS[sid].get("atk", 0)
                        self.inv[sid] = 1
                    elif sid == "charm1":
                        self.inv["charm1"] = 1
                        self.inv["charm1_equipped"] = True
                        self.equip_ac += 1
                    else:
                        self.inv[sid] = self.inv.get(sid, 0) + 1
                    self.msg = f"Bought {ITEMS[sid]['label']}."
                else:
                    self.msg = "Not enough gold."
                self.msg_t = 2
            elif key in (K.ESCAPE, K.E):
                self.state = "EXPLORE"
            return
        if self.state == "PAUSE":
            if key == K.ESCAPE or key == K.ENTER:
                self.state = self.paused_from if self.paused_from in ("EXPLORE", "COMBAT") else "EXPLORE"
            elif key == K.F5:
                self.save()
            elif key == K.F9:
                self.load()
            return
        if self.state in ("GAMEOVER", "ACTDONE"):
            if key in (K.ENTER, K.SPACE):
                if self.state == "GAMEOVER":
                    self.hp = self.max_hp // 2
                    self.goto_map("camp")
                    self.state = "EXPLORE"
                    self.msg, self.msg_t = "You wake at camp. The fire kept you.", 4
                    self.start_music("explore")
                else:
                    self.state = "TITLE"
                    self.__init__()
            return

    def b_check_end(self):
        c = self.combat
        self.b_sync()
        if not any(a["alive"] for a in c["allies"]):
            self.state = "GAMEOVER"
        elif not any(f["alive"] for f in c["foes"]):
            self.win_combat()

    # ----- menu input: Up/Down+Enter, 1-6 shortcuts, Esc steps back -----
    def b_sublist(self, ally):
        c = self.combat
        if c["submenu"] in ("skill", "spell"):
            return self.b_ability_list(ally, c["submenu"])
        if c["submenu"] == "item":
            return [i[0] for i in self.b_item_list()]
        if c["submenu"] == "duo":
            return self.duo_available()
        return []

    def b_targets(self, scope):
        c = self.combat
        if scope in ("foe",):
            return [(1, i) for i, f in enumerate(c["foes"]) if f["alive"]]
        if scope in ("ally",):
            return [(0, i) for i, a in enumerate(c["allies"]) if a["alive"]]
        return []

    def b_input(self, key, numkeys):
        import arcade as _ac
        K = _ac.key
        c = self.combat
        if c["stage"] != "input":
            if key == K.ESCAPE:
                self.paused_from = "COMBAT"
                self.state = "PAUSE"
            return
        ally = self.b_input_ally()
        if ally is None:
            return
        menu = self.b_menu(ally)
        # ---- target select stage ----
        if c.get("targeting"):
            scope = c["targeting"][1]
            lst = self.b_targets(scope)
            if not lst:
                c["targeting"] = None
                return
            if key in (K.UP, K.W):
                c["ti"] = (c["ti"] - 1) % len(lst)
                self.play("ui")
            elif key in (K.DOWN, K.S, K.TAB, K.T):
                c["ti"] = (c["ti"] + 1) % len(lst)
                self.play("ui")
            elif key in (K.ENTER, K.SPACE):
                (action, abid), _scope = c["targeting"]
                _s, _i = lst[c["ti"] % len(lst)]
                self.play("ui")
                c["targeting"] = None
                self.b_lock(ally, action, abid, _i)
            elif key == K.ESCAPE:
                c["targeting"] = None
                self.play("ui")
            elif key in numkeys and numkeys[key] < len(lst):
                c["ti"] = numkeys[key]
                (action, abid), _scope = c["targeting"]
                _s, _i = lst[c["ti"] % len(lst)]
                c["targeting"] = None
                self.b_lock(ally, action, abid, _i)
            return
        # ---- submenu stage (skill / spell / item lists) ----
        if c["submenu"]:
            lst = self.b_sublist(ally)
            if key in (K.UP, K.W):
                c["si"] = (c["si"] - 1) % max(1, len(lst))
                self.play("ui")
            elif key in (K.DOWN, K.S):
                c["si"] = (c["si"] + 1) % max(1, len(lst))
                self.play("ui")
            elif key == K.ESCAPE:
                c["submenu"] = None
                self.play("ui")
            elif key in (K.ENTER, K.SPACE) or (key in numkeys and numkeys[key] < len(lst)):
                if key in numkeys:
                    c["si"] = numkeys[key]
                if not lst:
                    c["submenu"] = None
                    return
                pick = lst[c["si"] % len(lst)]
                kind = c["submenu"]
                if kind == "duo":
                    import progression as _pgd
                    _spec = _pgd.DUOS[pick]
                    _who = "Nym" if pick == "nym" else "Kael"
                    _rk = self.duo_rank(_who)
                    if _rk < 2:
                        self.clog("The bond isn't sealed yet. (Seal it at a campfire.)")
                        self.play("miss")
                        return
                    _cost = 4 if _rk >= 5 else 6
                    if ally.get("mp", 0) < _cost:
                        self.clog(f"Not enough MP for {_spec['label']} ({_cost}).")
                        self.play("miss")
                        return
                    self.play("ui")
                    self.b_lock(ally, "duo", pick, None)
                elif kind in ("skill", "spell"):
                    ab = ABILITIES[pick]
                    if ally.get("mp", 0) < ab["mp"]:
                        self.clog(f"Not enough MP ({ally.get('mp',0)}/{ab['mp']}).")
                        self.play("miss")
                        return
                    self.play("ui")
                    if ab["scope"] in ("foe", "ally"):
                        c["targeting"] = ((kind, pick), ab["scope"])
                        c["ti"] = 0
                    else:
                        self.b_lock(ally, kind, pick, None)
                else:
                    _items = self.b_item_list()
                    iid = pick if isinstance(pick, str) else _items[c["si"] % len(_items)][0]
                    self.play("ui")
                    if iid == "bandage" or iid == "herb":
                        c["targeting"] = (("item", iid), "ally")
                        c["ti"] = 0
                    else:
                        c["targeting"] = (("item", iid), "foe")
                        c["ti"] = 0
            return
        # ---- main command menu ----
        if key in (K.UP, K.W):
            c["mi"] = (c["mi"] - 1) % len(menu)
            self.play("ui")
        elif key in (K.DOWN, K.S):
            c["mi"] = (c["mi"] + 1) % len(menu)
            self.play("ui")
        elif key in (K.ENTER, K.SPACE) or (key in numkeys and numkeys[key] < len(menu)):
            if key in numkeys:
                c["mi"] = numkeys[key]
            cmd = menu[c["mi"] % len(menu)][0]
            self.play("ui")
            if cmd == "attack":
                c["targeting"] = (("attack", None), "foe")
                c["ti"] = 0
            elif cmd in ("skill", "spell"):
                if cmd == "spell" and not self.b_kit(ally)["spells"]:
                    self.clog(f"{ally['n']} knows no spells.")
                    return
                c["submenu"] = cmd
                c["si"] = 0
            elif cmd == "duo":
                _du = self.duo_available()
                if not _du:
                    self.clog("No partner ready for a duet.")
                    return
                if len(_du) == 1:
                    self.b_lock(ally, "duo", _du[0], None)
                else:
                    c["submenu"] = "duo"
                    c["si"] = 0
            elif cmd == "item":
                if not self.b_item_list():
                    self.clog("Pack is empty!")
                    self.play("miss")
                    return
                c["submenu"] = "item"
                c["si"] = 0
            elif cmd == "guard":
                self.b_lock(ally, "guard", None, None)
            elif cmd == "flee":
                self.b_lock(ally, "flee", None, None)
        elif key == K.ESCAPE:
            self.paused_from = "COMBAT"
            self.state = "PAUSE"

    def on_text(self, text):
        if self.state == "CREATOR_NAME":
            if (text.isalpha() or text in (" ", "-", "'")) and len(self.hero_name) < 14:
                self.hero_name += text

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)

    # ---------- update ----------
    def on_update(self, dt):
        self.t += dt
        # hit-stop: freeze the world for a beat so hits land
        if self.hitstop > 0:
            self.hitstop -= dt
            return
        if self.trauma > 0:
            self.trauma = max(0.0, self.trauma - dt * 1.6)
        for _f in self.floaters:
            _f["t"] += dt
        self.floaters = [_f for _f in self.floaters if _f["t"] < 0.9]
        for _p in self.particles:
            _p["t"] += dt
            _p["x"] += _p["vx"] * dt
            _p["y"] += _p["vy"] * dt
        self.particles = [_p for _p in self.particles if _p["t"] < _p["life"]]
        # resolve pacing: one combatant acts ~every half second (DQ rhythm)
        if self.state == "COMBAT" and getattr(self, "combat", None) and self.combat.get("stage") == "resolve":
            self.combat["timer"] -= dt
            if self.combat["timer"] <= 0:
                self.combat["timer"] = 0.55
                if self.state == "COMBAT" and self.combat.get("stage") == "resolve":
                    self.b_step()
        if self.banner_t > 0:
            self.banner_t -= dt
        if self.msg_t > 0:
            self.msg_t -= dt
        if getattr(self, "last_sfx_t", 0) > 0:
            self.last_sfx_t -= dt
        try:
            self.music_watch(dt)
        except Exception:
            pass
        if self.state == "CINEMATIC":
            self.cine_t += dt
            if self.cine_i < len(CINEMA) and self.cine_c < len(CINEMA[self.cine_i]) and self.cine_t > 0.028:
                self.cine_t = 0
                self.cine_c += 1
        if self.state == "DIALOGUE":
            if self.reveal < len(self.cur()["text"]):
                self.reveal = min(len(self.cur()["text"]), self.reveal + dt * 70)
        if self.state == "EXPLORE":
            dx = dy = 0
            K = arcade.key
            if K.W in self.keys or K.UP in self.keys:
                dy += 1
            if K.S in self.keys or K.DOWN in self.keys:
                dy -= 1
            if K.A in self.keys or K.LEFT in self.keys:
                dx -= 1
                self.face = -1
            if K.D in self.keys or K.RIGHT in self.keys:
                dx += 1
                self.face = 1
            if dx or dy:
                self.walk += dt * 10
                if dx and dy:
                    dx *= 0.7071
                    dy *= 0.7071
                nx = self.px + dx * 210 * dt
                ny = self.py + dy * 210 * dt
                m = MAPS[self.map_id]
                if 30 < nx < m["w"] - 30 and not self.hit(nx, self.py):
                    self.px = nx
                if 30 < ny < m["h"] - 30 and not self.hit(self.px, ny):
                    self.py = ny
            # followers
            tx, ty = self.px, self.py
            for c in self.comps:
                if not c["on"]:
                    continue
                # keep followers on same map: lerp
                d = math.hypot(tx - c["x"], ty - c["y"])
                if self.map_id != getattr(self, "_fmap", self.map_id):
                    pass
                if d > 60:
                    a = math.atan2(ty - c["y"], tx - c["x"])
                    c["x"] += math.cos(a) * 175 * dt
                    c["y"] += math.sin(a) * 175 * dt
                tx, ty = c["x"] - 22, c["y"] - 12
            self._fmap = self.map_id
            # perception: hidden caches ping when close (WIT DC11, retryable)
            _pc = getattr(self, "_ping_cd", {})
            for _cid, (_cm, _cx, _cy) in (("shore", ("shore", 200, 700)), ("camp", ("camp", 1200, 750)),
                                          ("chapel", ("chapel", 250, 700)), ("cove", ("cove", 1050, 620))):
                if _cm != self.map_id or f"revealed_{_cid}" in self.flags or f"cache_{_cid}" in self.flags:
                    continue
                if math.hypot(self.px - _cx, self.py - _cy) < 110 and self.t - _pc.get(_cid, -9) > 4:
                    _pc[_cid] = self.t
                    _nat, _tot = roll_d20(mod(self.abilities["WIT"]))
                    if _nat == 20 or _tot >= 11:
                        self.flags[f"revealed_{_cid}"] = True
                        self.msg, self.msg_t = "Something glints... disturbed ground. (!)", 3
                        self.play("ui")
            self._ping_cd = _pc
            # camera
            m = MAPS[self.map_id]
            self.cam[0] = max(0, min(m["w"] - SCREEN_W, self.px - SCREEN_W / 2))
            self.cam[1] = max(0, min(m["h"] - SCREEN_H, self.py - SCREEN_H / 2))

    def hit(self, x, y):
        for wx, wy, ww, wh in MAPS[self.map_id]["walls"]:
            if wx - 12 < x < wx + ww + 12 and wy - 12 < y < wy + wh + 12:
                return True
        return False

    # ---------- draw ----------
    def w2s(self, x, y):
        return x - self.cam[0], y - self.cam[1]

    def draw_tile(self, texname, sx, sy, size=64):
        # DEBUG: catch bad calls
        import sys
        if not isinstance(texname, str):
            print(f"DEBUG draw_tile: texname is {type(texname)} = {texname}", file=sys.stderr)
        if len([a for a in [texname, sx, sy, size] if a is not None]) > 4:
            print(f"DEBUG draw_tile: too many args: texname={texname}, sx={sx}, sy={sy}, size={size}", file=sys.stderr)
        t = self.tile_tex.get(texname)
        if t is None:
            return False
        try:
            from arcade.types.rect import LBWH
            arcade.draw_texture_rect(t, LBWH(sx, sy, size, size), pixelated=True)
            return True
        except Exception as e:
            print(f"DEBUG draw_tile error: {e}", file=sys.stderr)
            return False

    def draw_glyph(self, name, x, y, s=28):
        t = self.glyph_tex.get(name)
        if t is None:
            return
        try:
            from arcade.types.rect import LBWH
            arcade.draw_texture_rect(t, LBWH(x - s / 2, y - s / 2, s, s))
        except Exception:
            pass

    def play(self, name):
        self.last_sfx = name
        self.last_sfx_t = 2.0
        if self.muted:
            return
        # Primary: pygame mixer (per-sound volumes, mixes with music)
        if getattr(self, "_pg", None) is not None:
            try:
                _s = self.pg_sounds.get(name)
                if _s is not None:
                    _s.play()
                    self.audio_backend = "pygame"
                    return
            except Exception as _e:
                self.audio_err = f"pygame {name}: {_e}"
        # Fallback: Win32 waveOut
        if getattr(self, "_winsound", None) is not None:
            try:
                import winsound as _ws2
                _p = self.sound_paths.get(name, f"assets/audio/{name}.wav")
                _ws2.PlaySound(_p, _ws2.SND_FILENAME | _ws2.SND_ASYNC | _ws2.SND_NODEFAULT)
                self.audio_backend = "winsound"
                return
            except Exception as _e:
                self.audio_err = f"winsound {name}: {_e}"
        # Last resort: arcade/pyglet with retained player ref
        s = self.sounds.get(name)
        if s is None:
            if not self.audio_err:
                self.audio_err = f"no sound {name}"
            return
        try:
            pl = s.play(volume=0.6)
            self.audio_backend = "arcade"
            if pl is not None:
                self._players.append(pl)
                self._players = self._players[-8:]
        except Exception as _e:
            self.audio_err = f"arcade {name}: {_e}"

    def ensure_mixer(self):
        if getattr(self, "_pg", None) is not None:
            return True
        try:
            import pygame as _pge
            if not _pge.mixer.get_init():
                _pge.mixer.pre_init(22050, -16, 1, 512)
                _pge.mixer.init()
            self._pg = _pge
            for _sn, _vv in (("hit", 0.5), ("miss", 0.35), ("dice", 0.45), ("ui", 0.4),
                             ("fire", 0.45), ("levelup", 0.5), ("heal", 0.45)):
                try:
                    _s = _pge.mixer.Sound(self.sound_paths.get(_sn, f"assets/audio/{_sn}.wav"))
                    _s.set_volume(_vv)
                    self.pg_sounds[_sn] = _s
                except Exception as _e:
                    self.audio_err = f"sfx {_sn}: {_e}"
            self.audio_backend = "pygame"
            return True
        except Exception as _e:
            self.audio_err = f"mixer init: {_e}"
            return False

    def start_music(self, mode):
        if mode == getattr(self, "_music_mode", ""):
            return
        self._music_mode = mode
        if getattr(self, "_pg", None) is None and not self.ensure_mixer():
            self._alog(f"start {mode}: no mixer")
            return
        try:
            import pygame as _pg2
            _f = os.path.join("assets", "audio", f"music_{mode}.wav")
            if not os.path.exists(_f):
                self.audio_err = f"missing {_f}"
                self._alog(f"start {mode}: missing file")
                return
            _pg2.mixer.music.load(_f)
            _pg2.mixer.music.set_volume(0.0 if self.muted or self.music_muted else (0.30 if mode == "explore" else 0.34))
            _pg2.mixer.music.play(-1)
            self._alog(f"start {mode}: playing")
        except Exception as _e:
            self.audio_err = f"music {mode}: {_e}"
            self._alog(f"start {mode} FAILED: {_e}")

    def _alog(self, line):
        try:
            with open("emberfall_audio.log", "a") as _f:
                import time as _t
                _f.write(f"{_t.strftime('%H:%M:%S')} {line}\n")
        except Exception:
            pass

    def sync_mute(self):
        try:
            if getattr(self, "_pg", None) is not None:
                import pygame as _pg3
                _v = 0.0 if self.muted or self.music_muted else (0.30 if self._music_mode == "explore" else 0.34)
                _pg3.mixer.music.set_volume(_v)
        except Exception:
            pass

    def music_busy(self):
        try:
            if getattr(self, "_pg", None) is not None:
                import pygame as _pgm
                return bool(_pgm.mixer.music.get_busy())
        except Exception:
            pass
        return False

    def music_watch(self, dt):
        self._music_tick = getattr(self, "_music_tick", 0.0) + dt
        if self._music_tick < 1.0:
            return
        self._music_tick = 0.0
        if getattr(self, "_pg", None) is None and not self.ensure_mixer():
            return
        if self.muted or self.music_muted:
            return
        if not self._music_mode:
            self.start_music("explore" if self.state != "COMBAT" else "combat")
            return
        try:
            import pygame as _pgw
            if not _pgw.mixer.music.get_busy():
                self.audio_err = ""
                _f = os.path.join("assets", "audio", f"music_{self._music_mode}.wav")
                _pgw.mixer.music.load(_f)
                _pgw.mixer.music.set_volume(0.30 if self._music_mode == "explore" else 0.34)
                _pgw.mixer.music.play(-1)
        except Exception as _e:
            self.audio_err = f"music restart: {_e}"

    def on_draw(self):
        self.clear()
        s = self.state
        if s == "TITLE":
            self.d_title()
        elif s.startswith("CREATOR"):
            self.d_creator()
        elif s == "CINEMATIC":
            self.d_cine()
        elif s in ("EXPLORE", "DIALOGUE", "TRADER"):
            self.d_world()
            if s == "DIALOGUE":
                self.d_dlg()
            elif s == "TRADER":
                self.d_shop()
            elif self.journal:
                self.d_journal()
            elif self.sheet:
                self.d_sheet()
            else:
                self.d_hud()
        elif s in ("DRAFT", "FEAT"):
            self.d_world()
            self.d_draft() if s == "DRAFT" else self.d_feat()
        elif s == "COMBAT":
            self.d_combat()
        elif s == "PAUSE":
            self.d_world()
            self.d_pause()
        elif s == "GAMEOVER":
            self.d_over()
        elif s == "ACTDONE":
            self.d_done()

    def d_title(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (10, 12, 24))
        arcade.draw_circle_filled(480, 450, 30, (235, 232, 255))
        arcade.draw_circle_filled(480, 450, 52, (110, 110, 190, 70))
        arcade.draw_text("EMBERFALL", 480, 340, arcade.color.WHITE, 44, anchor_x="center", bold=True, font_name=self.font_title)
        arcade.draw_text("ACT 1 — THE LIGHT BELOW", 480, 305, arcade.color.GOLD, 18, anchor_x="center", bold=True, font_name=self.font_title)
        arcade.draw_text("A CRPG in the spirit of Baldur's Gate — our world, our rules. Choices stick. Fire spreads.",
                         480, 272, (165, 170, 195), 12, anchor_x="center")
        arcade.draw_text("1 hero (you) + Nym + Kael  •  5 quests  •  4 turn-based battles  •  Levels 1-4",
                         480, 250, (140, 210, 175), 12, anchor_x="center")
        arcade.draw_text("ENTER — New Game      (F9 in-game loads save)", 480, 190, arcade.color.YELLOW, 15, anchor_x="center")
        _tmb = "playing" if self.music_busy() else ("muted (N)" if self.muted or self.music_muted else "starting… press P")
        arcade.draw_text(f"♫ music: {_tmb}   |   M sound • N music • P test", 480, 150, arcade.color.LIGHT_BLUE if self.music_busy() else arcade.color.YELLOW, 12, anchor_x="center")
        if getattr(self, "audio_err", ""):
            arcade.draw_text(f"audio: {self.audio_err}", 480, 128, (255, 150, 150), 10, anchor_x="center")
        arcade.draw_text("WASD move • E interact • J journal • K sheet • B bandage • M sound", 480, 60, (120, 125, 150), 12, anchor_x="center")

    def d_creator(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (16, 18, 32))
        arcade.draw_text("FORGE YOUR HERO — what do you remember?", 480, 585, arcade.color.GOLD, 19, anchor_x="center", bold=True)
        if self.state == "CREATOR_ORIGIN":
            arcade.draw_text("1/3 ORIGIN — 1/2/3 or Up/Down + Enter", 480, 550, (170, 175, 200), 12, anchor_x="center")
            for i, oid in enumerate(ORIGINS):
                o = ORIGINS[oid]
                sel = oid == self.origin_id
                y = 460 - i * 95
                arcade.draw_lbwh_rectangle_filled(180, y - 16, 600, 76, (42, 46, 74) if sel else (24, 26, 44))
                if sel:
                    arcade.draw_lbwh_rectangle_outline(180, y - 16, 600, 76, arcade.color.GOLD, 2)
                arcade.draw_text(f"{i+1}. {o['label']}", 200, y + 30, arcade.color.YELLOW if sel else arcade.color.WHITE, 15, bold=sel)
                arcade.draw_text(o["desc"], 200, y + 8, (180, 186, 212), 11)
        elif self.state == "CREATOR_CLASS":
            arcade.draw_text(f"2/3 CLASS — Origin: {ORIGINS[self.origin_id]['label']}", 480, 550, (170, 175, 200), 12, anchor_x="center")
            for i, cid in enumerate(CLASSES):
                c = CLASSES[cid]
                sel = cid == self.class_id
                y = 460 - i * 95
                arcade.draw_lbwh_rectangle_filled(180, y - 16, 600, 76, (42, 46, 74) if sel else (24, 26, 44))
                if sel:
                    arcade.draw_lbwh_rectangle_outline(180, y - 16, 600, 76, arcade.color.GOLD, 2)
                arcade.draw_text(f"{i+1}. {c['label']}", 200, y + 30, arcade.color.YELLOW if sel else arcade.color.WHITE, 15, bold=sel)
                arcade.draw_text(c["desc"], 200, y + 8, (180, 186, 212), 11)
        else:
            ab = {"MIGHT": 10, "WIT": 10, "CUNNING": 10}
            for k, v in ORIGINS[self.origin_id]["bonus"].items():
                ab[k] += v
            for k, v in CLASSES[self.class_id]["bonus"].items():
                ab[k] += v
            hp = 20 + ORIGINS[self.origin_id]["hp"] + CLASSES[self.class_id]["hp"]
            arcade.draw_text("3/3 NAME — type, ENTER to wake. Esc back.", 480, 550, (170, 175, 200), 12, anchor_x="center")
            arcade.draw_lbwh_rectangle_filled(280, 400, 400, 58, (24, 26, 44))
            arcade.draw_lbwh_rectangle_outline(280, 400, 400, 58, arcade.color.GOLD, 2)
            arcade.draw_text(self.hero_name or "___", 480, 418, arcade.color.WHITE, 21, anchor_x="center")
            arcade.draw_text(f"MIGHT {ab['MIGHT']}  WIT {ab['WIT']}  CUNNING {ab['CUNNING']}  HP {hp}  — {ORIGINS[self.origin_id]['label']} • {CLASSES[self.class_id]['label']}",
                             480, 360, (150, 220, 170), 13, anchor_x="center")

    def d_cine(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (4, 5, 11))
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, 66, arcade.color.BLACK)
        arcade.draw_lbwh_rectangle_filled(0, SCREEN_H - 66, SCREEN_W, 66, arcade.color.BLACK)
        line = CINEMA[self.cine_i] if self.cine_i < len(CINEMA) else ""
        arcade.draw_text(line[:int(self.cine_c)], 480, 320, (228, 228, 245), 20, anchor_x="center", anchor_y="center", width=700, align="center")
        arcade.draw_text(f"Memory {min(self.cine_i+1, len(CINEMA))}/{len(CINEMA)} — SPACE", 480, 88, (130, 130, 150), 12, anchor_x="center")
        arcade.draw_circle_filled(480, 470, 10 + self.cine_i * 7, (200, 200, 255))

    def draw_guy(self, sx, sy, cloak, name, face=1, phase=0.0, big=False, selected=False):
        r = 17 if big else 14
        bob = math.sin(phase) * (2.5 if big else 2)
        arcade.draw_circle_filled(sx, sy - r + 2, r, (0, 0, 0, 70))
        # cloak/body
        arcade.draw_lbwh_rectangle_filled(sx - 11, sy - 12 + bob, 22, 26, cloak)
        # head
        arcade.draw_circle_filled(sx + face * 2, sy + 12 + bob, 10, (240, 203, 170))
        # hood/helm stripe
        arcade.draw_lbwh_rectangle_filled(sx - 10, sy + 14 + bob, 20, 7, (cloak[0] // 2, cloak[1] // 2, cloak[2] // 2))
        # eyes face dir
        arcade.draw_circle_filled(sx + face * 5, sy + 11 + bob, 1.8, arcade.color.BLACK)
        if selected:
            arcade.draw_circle_outline(sx, sy, r + 6, arcade.color.GOLD, 2)
        arcade.draw_text(name, sx, sy + 26 + bob, arcade.color.BLACK if not big else arcade.color.WHITE, 10 if not big else 12, anchor_x="center", bold=True)

    def d_world(self):
        try:
            self._d_world_impl()
        except Exception as e:
            # Fallback rendering on error
            arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (20, 22, 34))
            arcade.draw_text(f"Render error: {e}", 480, 320, arcade.color.RED, 16, anchor_x="center")

    def _d_world_impl(self):
        m = MAPS[self.map_id]
        cam_x, cam_y = self.cam
        
        # ===== TILE RENDERING SYSTEM =====
        base_tile = {"shore": "sand", "camp": "grass", "chapel": "stone", "hold": "wood", "cove": "sand"}[self.map_id]
        
        # Precompute visible tile range
        tile_size = 64
        min_tx = max(0, int(cam_x // tile_size) - 1)
        max_tx = min(m["w"] // tile_size, int((cam_x + SCREEN_W) // tile_size) + 1)
        min_ty = max(0, int(cam_y // tile_size) - 1)
        max_ty = min(m["h"] // tile_size, int((cam_y + SCREEN_H) // tile_size) + 1)
        
        # ===== BASE TILES WITH TRANSITIONS =====
        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                wx, wy = tx * 64, ty * 64
                sx, sy = wx - cam_x, wy - cam_y
                
                # Determine tile type with transitions
                tile_type = self._get_tile_type(m, tx, ty, base_tile)
                self.draw_tile(tile_type, sx, sy)
        
        # ===== WATER ANIMATION (shore only) =====
        if self.map_id == "shore":
            self._draw_water(m, cam_x, cam_y)
        
        # ===== WRECK INTERIOR (shore) =====
        if self.map_id == "shore":
            self._draw_wreck_interior(cam_x, cam_y)
        
        # ===== HOLD INTERIOR =====
        if self.map_id == "hold":
            self._draw_hold_interior(cam_x, cam_y)
        
        # ===== CHAPEL INTERIOR =====
        if self.map_id == "chapel":
            self._draw_chapel_interior(cam_x, cam_y)
        
        # ===== WALL TRIM =====
        for wx, wy, ww, wh in m["walls"]:
            sx, sy = self.w2s(wx, wy)
            if -200 < sx < SCREEN_W + 200 and -200 < sy < SCREEN_H + 200:
                self._draw_wall_trim(sx, sy, ww, wh)
        
        # ===== PROPS =====
        for label, x, y in m["props"]:
            sx, sy = self.w2s(x, y)
            self._draw_prop(label, sx, sy)
        
        # ===== INTERACT MARKERS =====
        for it in self.interact_list():
            sx, sy = self.w2s(it["x"], it["y"])
            pulse = 4 + math.sin(self.t * 4) * 2
            arcade.draw_circle_outline(sx, sy, 14 + pulse, arcade.color.GOLD, 2)
            arcade.draw_text("!", sx, sy - 6, arcade.color.GOLD, 13, anchor_x="center", bold=True)
        
        # ===== SAILOR =====
        if self.map_id == "shore" and "q2_done" not in self.flags and "q2_dark" not in self.flags and "q2_dead" not in self.flags:
            sx, sy = self.w2s(960, 300)
            self.draw_guy(sx, sy, (190, 110, 110), "Sailor", 1, self.t * 2)
        
        # ===== AMBIENT NPCS =====
        for _k, _n, _x, _y, _c in NPCS.get(self.map_id, []):
            if _k == "per" and "q8_done" in self.flags:
                continue
            sx, sy = self.w2s(_x, _y)
            if -60 < sx < SCREEN_W + 60 and -60 < sy < SCREEN_H + 60:
                self.draw_guy(sx, sy, _c, _n, 1, self.t * 2)
        
        # ===== COMPANIONS =====
        for c in self.comps:
            if not c["on"]:
                if self.map_id == "shore" and "q1_done" not in self.flags:
                    sx, sy = self.w2s(c["x"], c["y"])
                    self.draw_guy(sx, sy, c["color"], c["name"], 1, self.t * 3)
                continue
            sx, sy = self.w2s(c["x"], c["y"])
            self.draw_guy(sx, sy, c["color"], c["name"], self.face, self.t * 6)
        
        # ===== HERO =====
        hx, hy = self.w2s(self.px, self.py)
        self.draw_guy(hx, hy, (200, 170, 60), self.hero_name or "Hero", self.face, self.walk, big=True, selected=False)
        
        # ===== LIGHTING / VIGNETTE =====
        self._draw_lighting(hx, hy)

    def quest_text(self):
        q = self.quests
        if self.map_id == "shore":
            if "q1_done" not in self.flags:
                return "◆ Wake: talk to Nym [!]"
            if "e1_done" not in self.flags:
                return "◆ Oil for the Light: clear crabs, take oil"
            if "pyre_lit" not in self.flags:
                return "◆ Light the shore pyre (needs oil)"
            if "q8" in self.flags and "q8_done" not in self.flags:
                return "◆ Per's net: west pools"
            return "◆ Go: Hollow Camp → (east) — or explore hold/cove"
        if self.map_id == "camp":
            if "q6_done" not in self.flags:
                return "◆ Maren needs 3 bitter herbs [!]"
            if "e2_done" not in self.flags:
                return "◆ Ambush on the trail [!] — then Chapel"
            return "◆ Go: Star Chapel →"
        if self.map_id == "hold":
            if "e4_done" not in self.flags:
                return "◆ Clear the ghast nest [!]"
            return "◆ Stash? Ledger? Tunnel to cove →"
        if self.map_id == "cove":
            if "maw_done" not in self.flags:
                return "◆ Something moves in dark water [!]"
            return "◆ Joss? Pools? Climb out ←"
        if "boss_done" not in self.flags:
            if "e3_done" not in self.flags:
                return "◆ Chapel guards [!]"
            if "font_open" not in self.flags:
                return "◆ Unseal the door: sun, tide, star"
            return "◆ FACE the Star Warden [!]"
        return "◆ Touch the Pale Star [!]"

    def d_hud(self):
        arcade.draw_lbwh_rectangle_filled(8, SCREEN_H - 48, 500, 40, (0, 0, 0, 200))
        arcade.draw_text(f"{self.hero_name} Lv{self.level} {CLASSES[self.class_id]['label']} HP {max(0,self.hp)}/{self.max_hp} MP {self.mp}/{self.max_mp} XP {self.xp}  M{self.abilities['MIGHT']} W{self.abilities['WIT']} C{self.abilities['CUNNING']}",
                         16, SCREEN_H - 34, arcade.color.WHITE, 11, font_name=self.font_body)
        arcade.draw_lbwh_rectangle_filled(SCREEN_W - 360, SCREEN_H - 48, 352, 40, (0, 0, 0, 200))
        arcade.draw_text(self.quest_text(), SCREEN_W - 350, SCREEN_H - 34, arcade.color.YELLOW, 11)
        arcade.draw_text(f"{self.map_id.upper()}  Nym {self.approval['Nym']:+} Kael {self.approval['Kael']:+}  {self.gold}g  rations {self.rations}  [B]andage {self.inv.get('bandage',0)}{'  MUTED(M)' if self.muted else '  sound ON(M)'}",
                         SCREEN_W - 350, SCREEN_H - 68, arcade.color.WHITE, 10)
        if getattr(self, "last_sfx_t", 0) > 0 and getattr(self, "last_sfx", ""):
            arcade.draw_text(f"♪ {self.last_sfx} [{self.audio_backend}]", SCREEN_W - 170, SCREEN_H - 90, arcade.color.YELLOW, 10, bold=True)
        _mb = "playing" if self.music_busy() else ("muted" if self.muted or self.music_muted else "STOPPED-press P")
        arcade.draw_text(f"♫ {self._music_mode or 'none'} { _mb}", SCREEN_W - 170, SCREEN_H - 108, arcade.color.LIGHT_BLUE, 9, bold=True)
        if getattr(self, "audio_err", ""):
            arcade.draw_text(f"audio: {self.audio_err}", SCREEN_W - 350, SCREEN_H - 106, (255, 150, 150), 9, width=340, align="right")
        it = self.nearest()
        if it:
            arcade.draw_text(f"[!] {it['label']}", 480, 40, arcade.color.YELLOW, 13, anchor_x="center", bold=True, font_name=self.font_body)
            self.draw_glyph("keyboard_e", 480, 18, 30)
        else:
            arcade.draw_text("WASD move • E interact • J journal • K sheet • Esc pause", 480, 26, (60, 55, 45), 11, anchor_x="center", font_name=self.font_body)
            self.draw_glyph("keyboard_e", 700, 26, 22)
            self.draw_glyph("keyboard_j", 770, 26, 22)
        if self.msg_t > 0:
            arcade.draw_lbwh_rectangle_filled(230, 70, 500, 30, (0, 0, 0, 200))
            arcade.draw_text(self.msg, 480, 78, arcade.color.WHITE, 12, anchor_x="center")
        if self.pending_drafts > 0 or self.pending_feat:
            arcade.draw_text("✦ Sparks stir — touch a campfire", 480, 104, arcade.color.GOLD, 12, anchor_x="center", bold=True)
        if self.journal:
            self.d_journal()
        if self.sheet:
            self.d_sheet()

    def d_journal(self):
        arcade.draw_lbwh_rectangle_filled(200, 80, 560, 450, (13, 13, 26))
        arcade.draw_lbwh_rectangle_outline(200, 80, 560, 450, arcade.color.GOLD, 2)
        arcade.draw_text("JOURNAL — J closes (BG rule: never feel lost)", 480, 502, arcade.color.GOLD, 14, anchor_x="center", bold=True)
        lines = ["Q1 Wake of the Star: " + ("DONE" if "q1_done" in self.flags else "find Nym"),
                 "Q2 Salt and Mercy: " + ("DONE" if self.quests["q2"] == 2 else ("DEAD — too slow" if "q2_dead" in self.flags else "sailor at east rocks (hurry!)")),
                 "Q3 Oil for the Light: " + ("DONE" if "pyre_lit" in self.flags else "oil + clear crabs + pyre"),
                 "Q4 The Star Hums: " + ("DONE" if "e3_done" in self.flags else "take the chapel (braziers: sun,tide,star)"),
                 "Q5 Choose the Light: " + ("DONE" if self.quests["q5"] == 2 else "face Warden, touch Star"),
                 "Q6 Maren's Remedy: " + ("DONE" if "q6_done" in self.flags else "3 bitter herbs"),
                 "Q7 Joss's Papers: " + ("DONE" if "q7_done" in self.flags else ("find the hold stash" if "q7" in self.flags else "a deserter in the cove?")),
                 "Q8 Per's Net: " + ("DONE" if "q8_done" in self.flags else ("find it by the pools" if "q8" in self.flags else "—")),
                 "Q9 Serren's Ledger: " + ("DONE" if "q9_done" in self.flags else ("confront him" if "ledger_found" in self.flags else "—")),
                 "Nest/Deepmaw: " + ("cleared" if "e4_done" in self.flags else "hold") + " / " + ("slain" if "maw_done" in self.flags else "cove"),
                 "", f"Mystery: why did it hum YOUR name?",
                 f"Sparks: {', '.join(self._talent_labels()) or 'none yet'}   Pending: {self.pending_drafts} draft(s){' + FEAT' if self.pending_feat else ''} (campfire)",
                 f"Bonds: Nym {self._bond_label('Nym')}  Kael {self._bond_label('Kael')}",
                 f"Flags: {', '.join(sorted(self.flags.keys())) or 'none'}",
                 f"Nym {self.approval['Nym']:+} | Kael {self.approval['Kael']:+} | {self.gold}g"]
        for i, ln in enumerate(lines):
            arcade.draw_text(ln, 230, 470 - i * 23, arcade.color.WHITE, 12)

    def _talent_labels(self):
        import progression as _pgd
        out = []
        for _t in self.hero_talents:
            if _t == "__hearty__":
                out.append("Second Wind")
            elif _t in _pgd.TALENTS:
                out.append(_pgd.TALENTS[_t]["label"])
        return out

    def _feat_label(self):
        if not self.feat:
            return "— (level 4)"
        import progression as _pgd
        return _pgd.FEATS.get(self.feat, {}).get("label", self.feat)

    def _bond_label(self, who):
        import progression as _pgd
        r = self.bond_rank(who)
        _node = "nym" if who == "Nym" else "kael"
        _sealed = f"{_node}:{r}" in getattr(self, "bond_seen", set()) and r >= 2
        return f"{_pgd.BOND_RANKS.get(r, 'Stranger')}{'*' if _sealed else ''} ({self.approval.get(who,0):+})"

    def d_sheet(self):
        arcade.draw_lbwh_rectangle_filled(220, 140, 520, 360, (13, 13, 26))
        arcade.draw_lbwh_rectangle_outline(220, 140, 520, 360, arcade.color.GOLD, 2)
        arcade.draw_text(f"{self.hero_name} — {ORIGINS[self.origin_id]['label']} • {CLASSES[self.class_id]['label']} (K closes)",
                         480, 468, arcade.color.GOLD, 13, anchor_x="center", bold=True)
        ab = self.abilities
        lines = [f"Level {self.level}  XP {self.xp}/{XP_TABLE[self.level] if self.level < len(XP_TABLE) else 'MAX'}",
                 f"HP {max(0,self.hp)}/{self.max_hp}  MP {self.mp}/{self.max_mp}  AC {self.eff_ac()}  ATK +{self.eff_atk()}",
                 f"MIGHT {ab['MIGHT']} ({mod(ab['MIGHT']):+})  WIT {ab['WIT']} ({mod(ab['WIT']):+})  CUNNING {ab['CUNNING']} ({mod(ab['CUNNING']):+})",
                 f"Sparks: {', '.join(self._talent_labels()) or 'none yet — rest at a campfire'}",
                 f"Sets: {', '.join(l for _t, l in self.tag_sets()) or '—'}   Bonds: Nym {self._bond_label('Nym')}  Kael {self._bond_label('Kael')}",
                 f"Feat: {self._feat_label()}",
                 "", f"Pack: bandage x{self.inv.get('bandage',0)} oil x{self.inv.get('oil',0)} herb x{self.inv.get('herb',0)}",
                 f"Gold {self.gold}g rations {self.rations}  equip ATK+{self.equip_atk} AC+{self.equip_ac}",
                 "Class art: " + ("Cleave hits ALL foes" if self.class_id == "blade" else "Starbolt + Immolate burn" if self.class_id == "channeler" else "Snipe never misses"),
                 "BG rule: sheet explains every roll. No hidden math."]
        for i, ln in enumerate(lines):
            arcade.draw_text(ln, 250, 430 - i * 26, arcade.color.WHITE, 12)

    def d_portrait(self, speaker, x, y):
        key = {"Nym": "nym", "Kael": "kael"}.get(speaker)
        t = self.portrait_tex.get(key) if key else None
        if t is not None:
            try:
                from arcade.types.rect import LBWH
                arcade.draw_texture_rect(t, LBWH(x - 30, y - 34, 60, 68))
                arcade.draw_lbwh_rectangle_outline(x - 30, y - 34, 60, 68, arcade.color.GOLD, 2)
                return
            except Exception:
                pass
        colors = {"Nym": (170, 120, 235), "Kael": (235, 160, 80), "You (insight)": (200, 170, 60),
                  "Insight": (200, 170, 60), "Both": (150, 200, 170), "Serren (Trader)": (120, 200, 130),
                  "The Pale Star": (235, 232, 255), "Wounded Sailor": (190, 110, 110)}
        c = colors.get(speaker, (200, 170, 60))
        arcade.draw_circle_filled(x, y, 30, c)
        arcade.draw_circle_filled(x, y + 8, 16, (240, 203, 170))
        arcade.draw_lbwh_rectangle_filled(x - 26, y - 34, 52, 20, (c[0] // 2, c[1] // 2, c[2] // 2))

    def d_dlg(self):
        n = DIALOGUES[self.node]
        arcade.draw_lbwh_rectangle_filled(50, 24, 860, 230, (11, 11, 23))
        arcade.draw_lbwh_rectangle_outline(50, 24, 860, 230, arcade.color.GOLD, 2)
        self.d_portrait(n["speaker"], 110, 180)
        arcade.draw_text(n["speaker"], 160, 218, arcade.color.GOLD, 14, bold=True, font_name=self.font_title)
        arcade.draw_text(n["text"][:int(self.reveal)], 160, 150, arcade.color.WHITE, 13, width=720, align="left", font_name=self.font_body)
        if self.banner and self.banner_t > 0:
            arcade.draw_text(self.banner, 160, 122, arcade.color.YELLOW, 11, bold=True)
        if self.reveal >= len(n["text"]):
            for i, (_idx, o) in enumerate(self.visible_opts()):
                lock = o.get("need") and self.inv.get(o["need"], 0) <= 0
                pre = "🔒 " if lock else ""
                arcade.draw_text(f"{'▶' if i == self.sel else ' '} {i+1}. {pre}{o['text']}", 160, 96 - i * 21,
                                 arcade.color.YELLOW if i == self.sel else (200, 200, 212), 11, bold=(i == self.sel))

    def d_draft(self):
        import progression as _pgd
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (0, 0, 0, 150))
        arcade.draw_text("A SPARK STIRS", 480, 540, arcade.color.GOLD, 26, anchor_x="center", bold=True, font_name=self.font_title)
        arcade.draw_text("The Star remembers through you. Choose — it will shape you.", 480, 508, (190, 195, 220), 13, anchor_x="center", font_name=self.font_body)
        _counts = _pgd.tag_counts(self.hero_talents)
        _prog = "   ".join(f"{_t} {_counts.get(_t,0)}/{_need}" for _t, (_need, _l, _d) in _pgd.TAG_SETS.items())
        arcade.draw_text(f"Sets — {_prog}", 480, 484, (150, 200, 170), 11, anchor_x="center", font_name=self.font_body)
        for _i, _tid in enumerate(self.draft_offer):
            _y = 400 - _i * 100
            _sel = _i == self.draft_sel % 3
            if _tid == "__hearty__":
                _label, _tag, _desc = "Second Wind", "—", "+4 max HP. The Star provides."
            else:
                _sp = _pgd.TALENTS[_tid]
                _label, _tag, _desc = _sp["label"], _sp.get("tag") or "—", _sp["desc"]
            arcade.draw_lbwh_rectangle_filled(180, _y - 16, 600, 76, (42, 46, 74) if _sel else (24, 26, 44))
            if _sel:
                arcade.draw_lbwh_rectangle_outline(180, _y - 16, 600, 76, arcade.color.GOLD, 2)
            arcade.draw_text(f"{'▶' if _sel else ' '} {_i+1}. {_label}  [{_tag}]", 200, _y + 28,
                             arcade.color.YELLOW if _sel else arcade.color.WHITE, 15, bold=_sel, font_name=self.font_body)
            arcade.draw_text(_desc, 200, _y + 6, (180, 186, 212), 12, font_name=self.font_body)

    def d_feat(self):
        import progression as _pgd
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (0, 0, 0, 150))
        arcade.draw_text("A TURNING POINT", 480, 540, arcade.color.GOLD, 26, anchor_x="center", bold=True, font_name=self.font_title)
        arcade.draw_text("Level 4. Raw power, or a feat that defines you?", 480, 508, (190, 195, 220), 13, anchor_x="center", font_name=self.font_body)
        for _i, _fid in enumerate(self.feat_offer):
            _y = 440 - _i * 62
            _sel = _i == self.feat_sel % len(self.feat_offer)
            _sp = _pgd.FEATS[_fid]
            arcade.draw_lbwh_rectangle_filled(230, _y - 12, 500, 52, (42, 46, 74) if _sel else (24, 26, 44))
            if _sel:
                arcade.draw_lbwh_rectangle_outline(230, _y - 12, 500, 52, arcade.color.GOLD, 2)
            arcade.draw_text(f"{'▶' if _sel else ' '} {_i+1}. {_sp['label']}", 250, _y + 16,
                             arcade.color.YELLOW if _sel else arcade.color.WHITE, 13, bold=_sel, font_name=self.font_body)
            arcade.draw_text(_sp["desc"], 250, _y - 2, (180, 186, 212), 11, font_name=self.font_body)

    def d_shop(self):
        arcade.draw_lbwh_rectangle_filled(220, 120, 520, 380, (13, 13, 26))
        arcade.draw_lbwh_rectangle_outline(220, 120, 520, 380, arcade.color.GOLD, 2)
        arcade.draw_text(f"SERREN'S SALVAGE — {self.gold}g (Esc leaves)", 480, 468, arcade.color.GOLD, 15, anchor_x="center", bold=True)
        stock = [("bandage", 8), ("oil", 10), ("herb", 6), ("sword1", 60), ("charm1", 50)]
        for i, (sid, price) in enumerate(stock):
            sel = i == self.shop_sel
            arcade.draw_text(f"{'▶' if sel else ' '} {ITEMS[sid]['label']} {price}g — {ITEMS[sid]['desc']}", 250, 425 - i * 32,
                             arcade.color.YELLOW if sel else arcade.color.WHITE, 12, bold=sel)
        if self.msg_t > 0:
            arcade.draw_text(self.msg, 480, 150, arcade.color.YELLOW, 12, anchor_x="center")

    # ----- combat draw -----
    def d_combat(self):
        c = self.combat
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (16, 18, 30))
        shx = shy = 0.0
        if self.trauma > 0:
            _s = self.trauma * self.trauma * 14
            shx = random.uniform(-_s, _s)
            shy = random.uniform(-_s, _s)
        # header: round + turn order (Agility, ties broken openly at roll)
        if c["stage"] == "input":
            _hd = f"BATTLE — Round {c['round']} — give orders!"
        else:
            _hd = f"BATTLE — Round {c['round']} — clash!"
        arcade.draw_text(_hd, 480, 610, arcade.color.GOLD, 13, anchor_x="center", bold=True, font_name=self.font_body)
        if c["stage"] == "resolve" and c.get("order"):
            _on = [(c["allies"][i]["n"] if s == "A" else c["foes"][i]["n"]) for s, i in c["order"]]
            arcade.draw_text("Order: " + " › ".join(_on[:6]), 480, 592, (150, 160, 185), 10, anchor_x="center", font_name=self.font_body)
        # foes row
        _nf = len(c["foes"])
        for i, f in enumerate(c["foes"]):
            _fx, _fy = self.b_foe_xy(i, _nf)
            _fx += shx
            _fy += shy
            if not f["alive"]:
                arcade.draw_text("✕", _fx, _fy, (90, 90, 100), 20, anchor_x="center", anchor_y="center")
                arcade.draw_text(f["n"], _fx, _fy - 34, (100, 100, 115), 10, anchor_x="center")
                continue
            _tgt = c.get("targeting") and c["targeting"][1] in ("foe",) and self.b_targets("foe") and self.b_targets("foe")[c["ti"] % len(self.b_targets("foe"))] == (1, i)
            self.draw_guy(_fx, _fy - 6, f["color"], "", 1, self.t * 3, selected=bool(_tgt))
            arcade.draw_text(f["n"], _fx, _fy + 26, arcade.color.YELLOW if _tgt else arcade.color.WHITE, 11, anchor_x="center", bold=bool(_tgt))
            if _tgt:
                arcade.draw_text("▼", _fx, _fy + 44, arcade.color.YELLOW, 13, anchor_x="center", bold=True)
            arcade.draw_lbwh_rectangle_filled(_fx - 34, _fy - 30, 68, 7, arcade.color.BLACK)
            arcade.draw_lbwh_rectangle_filled(_fx - 34, _fy - 30, 68 * max(0, f["hp"] / f["max"]), 7, arcade.color.RED)
            _st = []
            if f["dot"]["burn"]:
                _st.append("burn")
            if f["dot"]["poison"]:
                _st.append("psn")
            if f["st"]["atk"] > 0:
                _st.append("atk+")
            if f["st"]["atk"] < 0:
                _st.append("atk-")
            if _st:
                arcade.draw_text(",".join(_st), _fx, _fy - 44, (255, 170, 120), 9, anchor_x="center")
        # allies row: portraits, HP/MP, guard, locked orders
        _na = len(c["allies"])
        for i, a in enumerate(c["allies"]):
            _ax, _ay = self.b_ally_xy(i, _na)
            _ax += shx
            _ay += shy
            if not a["alive"]:
                arcade.draw_text("✕", _ax, _ay, (90, 90, 100), 20, anchor_x="center", anchor_y="center")
                arcade.draw_text(a["n"], _ax, _ay - 40, (100, 100, 115), 10, anchor_x="center")
                continue
            _is_in = c["stage"] == "input" and self.b_input_ally() is a
            self.draw_guy(_ax, _ay - 6, a["color"], "", 1, self.t * (5 if _is_in else 2), big=True, selected=bool(_is_in))
            arcade.draw_text(a["n"] + (" ✓" if a.get("cmd") else ""), _ax, _ay + 30, arcade.color.GOLD if _is_in else arcade.color.WHITE, 12, anchor_x="center", bold=bool(_is_in))
            arcade.draw_lbwh_rectangle_filled(_ax - 36, _ay - 28, 72, 7, arcade.color.BLACK)
            arcade.draw_lbwh_rectangle_filled(_ax - 36, _ay - 28, 72 * max(0, a["hp"] / a["max"]), 7, arcade.color.GREEN)
            arcade.draw_lbwh_rectangle_filled(_ax - 36, _ay - 37, 72, 5, arcade.color.BLACK)
            arcade.draw_lbwh_rectangle_filled(_ax - 36, _ay - 37, 72 * max(0, a.get("mp", 0) / max(1, a.get("mpmax", 1))), 5, (90, 150, 255))
            arcade.draw_text(f"{max(0,a['hp'])}/{a['max']}  MP {a.get('mp',0)}/{a.get('mpmax',0)}", _ax, _ay - 52, arcade.color.WHITE, 9, anchor_x="center")
            _tags = []
            if a.get("guard"):
                _tags.append("GUARD")
            if a["dot"]["burn"]:
                _tags.append("burn")
            if a["dot"]["poison"]:
                _tags.append("psn")
            if a["st"]["atk"]:
                _tags.append(f"atk{a['st']['atk']:+}")
            if a["st"]["dfn"]:
                _tags.append(f"dfn{a['st']['dfn']:+}")
            if _tags:
                arcade.draw_text(" ".join(_tags), _ax, _ay - 64, arcade.color.YELLOW, 9, anchor_x="center")
            if c.get("targeting") and c["targeting"][1] == "ally" and self.b_targets("ally") and self.b_targets("ally")[c["ti"] % len(self.b_targets("ally"))] == (0, i):
                arcade.draw_text("▼", _ax, _ay + 48, arcade.color.YELLOW, 13, anchor_x="center", bold=True)
        # impact particles + floating numbers (screen space)
        for _p in self.particles:
            _a = max(0, 255 - int(_p["t"] / _p["life"] * 255))
            arcade.draw_circle_filled(_p["x"] + shx, _p["y"] + shy, 3, (*_p["col"], _a))
        for _f in self.floaters:
            arcade.draw_text(_f["txt"], _f["x"] + shx, _f["y"] + _f["t"] * 34, _f["col"], 20 if _f["big"] else 14,
                             anchor_x="center", bold=True)
        # command windows (DQ-style) during input
        if c["stage"] == "input":
            _al = self.b_input_ally()
            if _al is not None and not c.get("targeting") and not c["submenu"]:
                menu = self.b_menu(_al)
                arcade.draw_lbwh_rectangle_filled(40, 30, 250, 40 + 26 * len(menu), (11, 11, 23))
                arcade.draw_lbwh_rectangle_outline(40, 30, 250, 40 + 26 * len(menu), arcade.color.GOLD, 2)
                arcade.draw_text(f"{_al['n']} — command?", 60, 30 + 26 * len(menu), arcade.color.GOLD, 12, bold=True, font_name=self.font_title)
                for _j, (_mid, _ml) in enumerate(menu):
                    _sel = _j == c["mi"] % len(menu)
                    arcade.draw_text(f"{'▶' if _sel else ' '} {_j+1}. {_ml}", 60, 30 + 26 * (len(menu) - 1 - _j),
                                     arcade.color.YELLOW if _sel else (200, 200, 212), 12, bold=_sel, font_name=self.font_body)
            elif _al is not None and c["submenu"]:
                lst = self.b_sublist(_al)
                _h = 66 + 24 * max(1, len(lst))
                arcade.draw_lbwh_rectangle_filled(40, 30, 430, _h, (11, 11, 23))
                arcade.draw_lbwh_rectangle_outline(40, 30, 430, _h, arcade.color.GOLD, 2)
                arcade.draw_text(f"{_al['n']} — {c['submenu']} (Esc back)", 60, 30 + _h - 26, arcade.color.GOLD, 12, bold=True, font_name=self.font_title)
                if not lst:
                    arcade.draw_text("Nothing here.", 60, 30 + _h - 52, (170, 170, 185), 12, font_name=self.font_body)
                for _j in range(len(lst)):
                    _sel = _j == c["si"] % len(lst)
                    if c["submenu"] == "item":
                        _iid = lst[_j]
                        _tx = f"{_j+1}. {dict(self.b_item_list()).get(_iid, _iid)}"
                    elif c["submenu"] == "duo":
                        import progression as _pgd
                        _du = _pgd.DUOS[lst[_j]]
                        _rk = self.duo_rank("Nym" if lst[_j] == "nym" else "Kael")
                        _cost = 4 if _rk >= 5 else 6
                        _cant = _al.get("mp", 0) < _cost
                        _tx = f"{'✕' if _cant else ' '} {_j+1}. {_du['label']} ({_cost}MP, rank {_rk}) — {_du['desc']}"
                    else:
                        _ab = ABILITIES[lst[_j]]
                        _cant = _al.get("mp", 0) < _ab["mp"]
                        _tx = f"{'✕' if _cant else ' '} {_j+1}. {_ab['label']} ({_ab['mp']}MP) — {_ab['desc']}"
                    arcade.draw_text(_tx, 60, 30 + _h - 52 - _j * 24,
                                     arcade.color.YELLOW if _sel else (200, 200, 212), 11, bold=_sel, font_name=self.font_body)
            elif _al is not None and c.get("targeting"):
                arcade.draw_lbwh_rectangle_filled(40, 30, 430, 64, (11, 11, 23))
                arcade.draw_lbwh_rectangle_outline(40, 30, 430, 64, arcade.color.GOLD, 2)
                arcade.draw_text("Choose a target — Up/Down (T tabs), Enter confirms, Esc backs.", 60, 48, arcade.color.YELLOW, 12, bold=True, font_name=self.font_body)
        # right log panel
        arcade.draw_lbwh_rectangle_filled(748, 90, 200, 470, (10, 10, 20))
        arcade.draw_text(f"Round {c['round']}", 758, 540, arcade.color.GOLD, 12, bold=True, font_name=self.font_title)
        arcade.draw_text("Log:", 758, 518, (150, 150, 170), 11, bold=True)
        for i, ln in enumerate(c["log"][-5:]):
            arcade.draw_text(ln, 758, 496 - i * 24, arcade.color.WHITE, 9, width=185, align="left", font_name=self.font_body)

    def d_pause(self):
        arcade.draw_lbwh_rectangle_filled(280, 180, 400, 280, (10, 10, 20))
        arcade.draw_lbwh_rectangle_outline(280, 180, 400, 280, arcade.color.GOLD, 2)
        arcade.draw_text("PAUSED", 480, 410, arcade.color.GOLD, 24, anchor_x="center", bold=True)
        arcade.draw_text("Esc/Enter resume • F5 save • F9 load", 480, 370, arcade.color.WHITE, 12, anchor_x="center")
        arcade.draw_text("BG fans pause. No shame.", 480, 340, (150, 160, 180), 11, anchor_x="center")
        arcade.draw_text(f"{self.hero_name} Lv{self.level} {self.map_id}  {self.gold}g", 480, 300, arcade.color.YELLOW, 12, anchor_x="center")

    def d_over(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (30, 8, 10))
        arcade.draw_text("THE PARTY FALLS", 480, 380, arcade.color.RED, 34, anchor_x="center", bold=True)
        arcade.draw_text("The Star hums on without you... this time.", 480, 340, arcade.color.WHITE, 14, anchor_x="center")
        arcade.draw_text("ENTER — wake at camp (half HP, keep loot & lessons)", 480, 280, arcade.color.YELLOW, 13, anchor_x="center")

    def d_done(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_W, SCREEN_H, (8, 12, 22))
        arcade.draw_text("ACT 1 COMPLETE", 480, 500, arcade.color.GOLD, 34, anchor_x="center", bold=True)
        end = "BOUND the Star" if "ending_bind" in self.flags else "LIT the fleet home" if "ending_light" in self.flags else "SHATTERED the song"
        arcade.draw_text(f"{self.hero_name} {end}.", 480, 460, arcade.color.WHITE, 16, anchor_x="center")
        mins = (time.time() - self.play_t0) / 60
        arcade.draw_text(f"Lv{self.level}  {self.xp} XP  {self.stats['kills']} kills  checks {self.stats['ok']}✓/{self.stats['fail']}✗  {mins:.1f} min",
                         480, 425, (150, 220, 170), 13, anchor_x="center")
        arcade.draw_text(f"Nym {self.approval['Nym']:+}  Kael {self.approval['Kael']:+}  Flags: {', '.join(sorted(self.flags.keys()))}",
                         480, 395, arcade.color.YELLOW, 11, anchor_x="center", width=800, align="center")
        arcade.draw_text("How BG fans end an act: recap choices, tease consequence.", 480, 350, (160, 165, 190), 12, anchor_x="center")
        arcade.draw_text("The fleet turns. The deep answers. Act 2 waits.", 480, 328, (160, 165, 190), 12, anchor_x="center")
        arcade.draw_text("ENTER — title (save stays in emberfall_save.json)", 480, 270, arcade.color.WHITE, 13, anchor_x="center")


def main():
    # anchor to the game folder so VS Code / any launcher CWD still finds assets
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    Game()
    arcade.run()


if __name__ == "__main__":
    main()
