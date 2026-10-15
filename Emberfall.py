"""
Emberfall: Chains of the Pale Star — Story-First Prototype (Phase 0/1)
Python-Arcade | 1 Hero + 2 Companions | Story before combat

Professional RPG intro techniques demonstrated here:
 1. COLD OPEN (in medias res) — you wake in wreckage, no lore dump.
 2. IDENTITY THROUGH CHOICE — Origin/Class picked in-fiction as "what do you remember?"
 3. TUTORIAL AS STORY — move/interact taught by companions, not a manual.
 4. COMPANIONS AS LENSES — Kael (duty) vs Nym (curiosity) argue; you break the tie.
 5. MYSTERY QUESTION — "What is the Pale Star, and why did it wake you?" drives Act 1.

Run:  python Emberfall.py
Controls: WASD/Arrows move | E interact | J journal | SPACE/ENTER advance | 1-4 dialogue
"""
import arcade
import random
import math

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
TITLE = "Emberfall: Chains of the Pale Star"

# ---------------------------------------------------------------- data
ORIGINS = {
    "survivor": {
        "label": "Rift-Touched Survivor",
        "desc": "You lived through the Rift once before. +2 WIT. NPCs fear you.",
        "bonus": {"WIT": 2}, "hp": 4,
    },
    "warden": {
        "label": "Exiled Warden",
        "desc": "Trained soldier, stripped of rank. +2 MIGHT. Kael respects you.",
        "bonus": {"MIGHT": 2}, "hp": 8,
    },
    "stowaway": {
        "label": "Stowaway Scholar",
        "desc": "You snuck aboard to study the Star. +2 CUNNING. Nym adores you.",
        "bonus": {"CUNNING": 2}, "hp": 2,
    },
}

CLASSES = {
    "blade": {
        "label": "Blade",
        "desc": "Heavy steel. MIGHT checks easier. HP +10.",
        "bonus": {"MIGHT": 2}, "hp": 10,
    },
    "channeler": {
        "label": "Channeler",
        "desc": "You hear the Star hum. WIT checks easier. HP +4.",
        "bonus": {"WIT": 2}, "hp": 4,
    },
    "wayknife": {
        "label": "Wayknife",
        "desc": "Quiet and quick. CUNNING checks easier. HP +6.",
        "bonus": {"CUNNING": 2}, "hp": 6,
    },
}

CINEMATIC_LINES = [
    "The sky tore open above the Mournsea.",
    "A star fell — pale, humming — and the fleet with it.",
    "You remember cold water. A voice saying your name.",
    "And then... sand in your mouth. Someone shaking you awake.",
    "(Press SPACE to open your eyes...)",
]


def d20_roll(mod=0):
    """Core d20-lite roll used for all skill checks. Returns (natural, total)."""
    nat = random.randint(1, 20)
    return nat, nat + mod


def ability_mod(score):
    return (score - 10) // 2


# Dialogue nodes: data-driven so writers can edit without touching code.
# option = {text, next, check:(ability,dc)|None, success:node, fail:node, approval:{k:v}, flag:str}
DIALOGUES = {
    "wake": {
        "speaker": "Nym",
        "text": "Hey — hey! Breathe. You're bleeding sand. Do you remember your name?",
        "options": [
            {"text": "\"...I remember. I'm alive. That's enough.\" (Kind)", "next": "wake2",
             "approval": {"Nym": 1}, "flag": "tone_kind"},
            {"text": "\"Get your hands off me.\" (Cold)", "next": "wake2",
             "approval": {"Nym": -1, "Kael": 1}, "flag": "tone_cold"},
            {"text": "[CUNNING] Study her first before answering.", "next": None,
             "check": ("CUNNING", 9), "success": "wake_cunning_ok", "fail": "wake_cunning_fail"},
        ],
    },
    "wake_cunning_ok": {
        "speaker": "You (insight)",
        "text": "(Success) Ink-stained fingers. Scholar's satchel. She's more scared for you than of you. She can be trusted — for now.",
        "options": [{"text": "\"...Thank you for pulling me out.\"", "next": "wake2", "approval": {"Nym": 2}}],
    },
    "wake_cunning_fail": {
        "speaker": "You (insight)",
        "text": "(Failed) Your head pounds. Details blur. Best to just answer.",
        "options": [{"text": "\"...I'm... awake.\"", "next": "wake2"}],
    },
    "wake2": {
        "speaker": "Kael",
        "text": "Enough. The tide takes the wreck by dusk, and that thing in the sky is still humming. Scholar — we leave the wounded and light the signal, or we die curious.",
        "options": [
            {"text": "\"Nobody gets left behind.\" (Side with Nym)", "next": "conflict_nym",
             "approval": {"Nym": 2, "Kael": -1}, "flag": "sided_nym"},
            {"text": "\"He's right. Signal first, grief later.\" (Side with Kael)", "next": "conflict_kael",
             "approval": {"Kael": 2, "Nym": -1}, "flag": "sided_kael"},
            {"text": "[WIT] \"We do both: splint, signal, move. Together.\"", "next": None,
             "check": ("WIT", 10), "success": "conflict_peace_ok", "fail": "conflict_peace_fail"},
        ],
    },
    "conflict_nym": {
        "speaker": "Nym",
        "text": "See? Decency! Kael, help me splint the sailor by the rocks — then we ALL light the fire. The Star chose them for a reason.",
        "options": [{"text": "\"Let's move. Show me the signal fire.\"", "next": None, "end": "shore", "flag": "quest_signal"}],
    },
    "conflict_kael": {
        "speaker": "Kael",
        "text": "Hm. A soldier's answer. Good. Help me gather oil at the wreck — the scholar will pout, but she'll live longer.",
        "options": [{"text": "\"Lead on. Then we light it together.\"", "next": None, "end": "shore", "flag": "quest_signal"}],
    },
    "conflict_peace_ok": {
        "speaker": "Both",
        "text": "(Success) They stare — then nod. Kael: \"...A leader's answer.\" Nym grins: \"Oh, I LIKE you.\" Both companions commit to you.",
        "options": [{"text": "\"Splint, oil, fire. Now.\"", "next": None, "end": "shore",
                      "approval": {"Nym": 1, "Kael": 1}, "flag": "peacemaker"}],
    },
    "conflict_peace_fail": {
        "speaker": "Kael",
        "text": "(Failed) Pretty words, no plan. Kael shakes his head; Nym bites her lip. You'll have to pick a side after all.",
        "options": [
            {"text": "Back Nym — save the sailor.", "next": "conflict_nym", "approval": {"Nym": 1}},
            {"text": "Back Kael — signal first.", "next": "conflict_kael", "approval": {"Kael": 1}},
        ],
    },
}


class EmberfallGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
        arcade.set_background_color((12, 14, 24))

        self.state = "TITLE"
        self.keys = set()

        # --- character being forged ---
        self.origin_id = "survivor"
        self.class_id = "blade"
        self.hero_name = ""
        self.abilities = {"MIGHT": 10, "WIT": 10, "CUNNING": 10}
        self.max_hp = 20
        self.hp = 20

        # --- story state ---
        self.flags = {}
        self.approval = {"Kael": 0, "Nym": 0}
        self.quest_stage = 0  # 0 wake, 1 meet conflict, 2 light fire, 3 done
        self.journal_open = False
        self.roll_banner = ""  # last d20 result shown in dialogue
        self.roll_timer = 0.0

        # --- cinematic ---
        self.cine_index = 0
        self.cine_chars = 0
        self.cine_timer = 0.0

        # --- explore ---
        self.player_x, self.player_y = 480, 200
        self.speed = 200
        self.walls = [
            (0, 0, SCREEN_WIDTH, 20),
            (0, 0, 20, SCREEN_HEIGHT),
            (SCREEN_WIDTH - 20, 0, 20, SCREEN_HEIGHT),
            (0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20),
            (180, 320, 220, 40),   # wreck hull
            (620, 300, 160, 50),   # rocks
        ]
        # companions follow; recruited flags gate them
        self.companions = [
            {"name": "Nym", "x": 540, "y": 230, "color": (190, 130, 240), "recruited": False},
            {"name": "Kael", "x": 420, "y": 420, "color": (240, 170, 90), "recruited": False},
        ]
        self.interactables = [
            {"id": "nym", "x": 540, "y": 260, "label": "Talk to Nym (E)", "when": lambda: self.quest_stage == 0},
            {"id": "kael", "x": 480, "y": 430, "label": "Approach Kael & Nym (E)", "when": lambda: self.quest_stage == 1},
            {"id": "fire", "x": 830, "y": 480, "label": "Light the Signal Fire (E)", "when": lambda: self.quest_stage == 2},
        ]

        # --- dialogue runtime ---
        self.node_id = None
        self.reveal = 0.0
        self.dialog_select = 0

        # creator cursor
        self.creator_options = list(ORIGINS.keys())

    # ============================ helpers
    def finalize_character(self):
        self.abilities = {"MIGHT": 10, "WIT": 10, "CUNNING": 10}
        for k, v in ORIGINS[self.origin_id]["bonus"].items():
            self.abilities[k] += v
        for k, v in CLASSES[self.class_id]["bonus"].items():
            self.abilities[k] += v
        self.max_hp = 20 + ORIGINS[self.origin_id]["hp"] + CLASSES[self.class_id]["hp"]
        self.hp = self.max_hp
        if not self.hero_name.strip():
            self.hero_name = "Ash"

    def start_cinematic(self):
        self.finalize_character()
        self.state = "CINEMATIC"
        self.cine_index = 0
        self.cine_chars = 0

    def start_dialogue(self, node_id):
        self.state = "DIALOGUE"
        self.node_id = node_id
        self.reveal = 0.0
        self.dialog_select = 0
        self.roll_banner = ""

    def current_node(self):
        return DIALOGUES[self.node_id]

    def apply_option(self, opt):
        # skill check?
        if opt.get("check"):
            ability, dc = opt["check"]
            score = self.abilities[ability]
            nat, total = d20_roll(ability_mod(score))
            ok = (nat == 20) or (total >= dc and nat != 1)
            self.roll_banner = f"d20: {nat} + {ability_mod(score)} ({ability}) vs DC {dc} — {'SUCCESS' if ok else 'FAIL'}"
            self.roll_timer = 3.0
            for k, v in opt.get("approval", {}).items():
                self.approval[k] = self.approval.get(k, 0) + v
            if opt.get("flag"):
                self.flags[opt["flag"]] = True
            self.start_dialogue(opt["success"] if ok else opt["fail"])
            return
        for k, v in opt.get("approval", {}).items():
            self.approval[k] = self.approval.get(k, 0) + v
        if opt.get("flag"):
            self.flags[opt["flag"]] = True
        if opt.get("end") == "shore":
            # leaving the argument recruits both, quest advances
            for c in self.companions:
                c["recruited"] = True
            self.quest_stage = 2
            self.state = "EXPLORE"
            return
        if opt.get("next"):
            self.start_dialogue(opt["next"])

    def nearest_interact(self):
        best, best_d = None, 1e9
        for it in self.interactables:
            if not it["when"]():
                continue
            d = math.hypot(self.player_x - it["x"], self.player_y - it["y"])
            if d < 70 and d < best_d:
                best, best_d = it, d
        return best

    # ============================ input
    def on_key_press(self, key, modifiers):
        self.keys.add(key)

        if self.state == "TITLE":
            if key in (arcade.key.ENTER, arcade.key.SPACE):
                self.state = "CREATOR_ORIGIN"
                self.creator_options = list(ORIGINS.keys())
            return

        if self.state in ("CREATOR_ORIGIN", "CREATOR_CLASS"):
            opts = list(ORIGINS.keys()) if self.state == "CREATOR_ORIGIN" else list(CLASSES.keys())
            idx = self.creator_options.index(self.origin_id if self.state == "CREATOR_ORIGIN" else self.class_id) \
                if (self.origin_id in self.creator_options or self.class_id in self.creator_options) else 0
            if key in (arcade.key.UP, arcade.key.W):
                idx = (idx - 1) % len(opts)
            elif key in (arcade.key.DOWN, arcade.key.S):
                idx = (idx + 1) % len(opts)
            elif key in (arcade.key.ENTER, arcade.key.SPACE):
                if self.state == "CREATOR_ORIGIN":
                    self.state = "CREATOR_CLASS"
                    self.creator_options = list(CLASSES.keys())
                else:
                    self.state = "CREATOR_NAME"
                    self.hero_name = ""
                return
            elif key in (arcade.key._1, arcade.key._2, arcade.key._3,
                         arcade.key.NUM_1, arcade.key.NUM_2, arcade.key.NUM_3):
                num = {arcade.key._1: 0, arcade.key._2: 1, arcade.key._3: 2,
                       arcade.key.NUM_1: 0, arcade.key.NUM_2: 1, arcade.key.NUM_3: 2}[key]
                if num < len(opts):
                    if self.state == "CREATOR_ORIGIN":
                        self.origin_id = opts[num]
                        self.state = "CREATOR_CLASS"
                        self.creator_options = list(CLASSES.keys())
                    else:
                        self.class_id = opts[num]
                        self.state = "CREATOR_NAME"
                        self.hero_name = ""
                return
            if self.state == "CREATOR_ORIGIN":
                self.origin_id = opts[idx]
            else:
                self.class_id = opts[idx]
            self.creator_options = opts
            return

        if self.state == "CREATOR_NAME":
            if key == arcade.key.ENTER:
                self.start_cinematic()
            elif key == arcade.key.BACKSPACE:
                self.hero_name = self.hero_name[:-1]
            elif key == arcade.key.ESCAPE:
                self.state = "CREATOR_CLASS"
            return

        if self.state == "CINEMATIC":
            if key in (arcade.key.SPACE, arcade.key.ENTER):
                # advance fast: finish line or next
                full = CINEMATIC_LINES[self.cine_index]
                if self.cine_chars < len(full):
                    self.cine_chars = len(full)
                else:
                    self.cine_index += 1
                    self.cine_chars = 0
                    if self.cine_index >= len(CINEMATIC_LINES):
                        self.state = "EXPLORE"
                        self.quest_stage = 0
            return

        if self.state == "EXPLORE":
            if key == arcade.key.E:
                it = self.nearest_interact()
                if it:
                    if it["id"] == "nym":
                        for c in self.companions:
                            if c["name"] == "Nym":
                                c["recruited"] = True
                        self.start_dialogue("wake")
                    elif it["id"] == "kael":
                        self.start_dialogue("wake2")
                    elif it["id"] == "fire":
                        self.quest_stage = 3
                        self.state = "ENDING"
            elif key == arcade.key.J:
                self.journal_open = not self.journal_open
            return

        if self.state == "DIALOGUE":
            node = self.current_node()
            n = len(node["options"])
            if key in (arcade.key.UP, arcade.key.W):
                self.dialog_select = (self.dialog_select - 1) % n
            elif key in (arcade.key.DOWN, arcade.key.S):
                self.dialog_select = (self.dialog_select + 1) % n
            elif key in (arcade.key.ENTER, arcade.key.SPACE):
                # finish typewriter first
                if self.reveal < len(node["text"]):
                    self.reveal = len(node["text"])
                else:
                    self.dialog_select = 0 if self.dialog_select >= n else self.dialog_select
                    self.apply_option(node["options"][self.dialog_select])
            elif key in (arcade.key._1, arcade.key._2, arcade.key._3, arcade.key._4,
                         arcade.key.NUM_1, arcade.key.NUM_2, arcade.key.NUM_3):
                nums = [arcade.key._1, arcade.key._2, arcade.key._3, arcade.key._4]
                nums += [arcade.key.NUM_1, arcade.key.NUM_2, arcade.key.NUM_3]
                try:
                    i = nums.index(key) % 4
                except ValueError:
                    return
                if i < n:
                    self.dialog_select = i
                    self.apply_option(node["options"][i])
            return

        if self.state == "ENDING":
            if key in (arcade.key.ENTER, arcade.key.SPACE, arcade.key.ESCAPE):
                self.state = "TITLE"
                self.__init__()  # clean restart for prototype

    def on_text(self, text):
        # name typing (letters, spaces, hyphen only, max 14)
        if self.state == "CREATOR_NAME":
            if text.isalpha() or text in (" ", "-", "'"):
                if len(self.hero_name) < 14:
                    self.hero_name += text

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)

    # ============================ update
    def on_update(self, dt):
        if self.state == "CINEMATIC":
            self.cine_timer += dt
            full = CINEMATIC_LINES[self.cine_index] if self.cine_index < len(CINEMATIC_LINES) else ""
            if self.cine_chars < len(full) and self.cine_timer > 0.03:
                self.cine_timer = 0
                self.cine_chars += 1
        if self.state == "DIALOGUE":
            node = self.current_node()
            if self.reveal < len(node["text"]):
                self.reveal = min(len(node["text"]), self.reveal + dt * 60)
            if self.roll_timer > 0:
                self.roll_timer -= dt
        if self.state == "EXPLORE":
            dx = dy = 0
            if arcade.key.W in self.keys or arcade.key.UP in self.keys:
                dy += 1
            if arcade.key.S in self.keys or arcade.key.DOWN in self.keys:
                dy -= 1
            if arcade.key.A in self.keys or arcade.key.LEFT in self.keys:
                dx -= 1
            if arcade.key.D in self.keys or arcade.key.RIGHT in self.keys:
                dx += 1
            if dx and dy:
                dx *= 0.7071
                dy *= 0.7071
            nx = self.player_x + dx * self.speed * dt
            ny = self.player_y + dy * self.speed * dt
            # wall collide (circle radius 14)
            def blocked(x, y):
                for wx, wy, ww, wh in self.walls:
                    if wx - 12 < x < wx + ww + 12 and wy - 12 < y < wy + wh + 12:
                        return True
                return False
            if not blocked(nx, self.player_y) and 30 < nx < SCREEN_WIDTH - 30:
                self.player_x = nx
            if not blocked(self.player_x, ny) and 30 < ny < SCREEN_HEIGHT - 30:
                self.player_y = ny
            # companions trail behind
            tx, ty = self.player_x, self.player_y
            for c in self.companions:
                if not c["recruited"]:
                    continue
                d = math.hypot(tx - c["x"], ty - c["y"])
                if d > 55:
                    ang = math.atan2(ty - c["y"], tx - c["x"])
                    c["x"] += math.cos(ang) * 160 * dt
                    c["y"] += math.sin(ang) * 160 * dt
                tx, ty = c["x"] - 20, c["y"] - 10

    # ============================ draw
    def on_draw(self):
        self.clear()
        if self.state == "TITLE":
            self.draw_title()
        elif self.state.startswith("CREATOR"):
            self.draw_creator()
        elif self.state == "CINEMATIC":
            self.draw_cinematic()
        elif self.state == "EXPLORE":
            self.draw_explore()
        elif self.state == "DIALOGUE":
            self.draw_explore(dim=True)
            self.draw_dialogue()
        elif self.state == "ENDING":
            self.draw_ending()

    def draw_title(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (12, 14, 24))
        # pale star
        arcade.draw_circle_filled(480, 440, 34, (235, 230, 255))
        arcade.draw_circle_filled(480, 440, 52, (120, 120, 200, 60))
        arcade.draw_text(TITLE, 480, 330, arcade.color.WHITE, 30, anchor_x="center", bold=True)
        arcade.draw_text("A party-based tale of wreckage and will — inspired by Baldur's Gate, our own world.",
                        480, 295, (160, 165, 190), 13, anchor_x="center")
        arcade.draw_text("1 Hero + 2 Companions  •  Choices matter  •  d20 story checks",
                        480, 270, (130, 200, 170), 13, anchor_x="center")
        arcade.draw_text("Press ENTER to forge your hero", 480, 200, arcade.color.YELLOW, 16, anchor_x="center")
        arcade.draw_text("WASD move • E talk • J journal • 1-4 choose", 480, 60, (120, 120, 140), 12, anchor_x="center")

    def draw_creator(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (18, 20, 34))
        arcade.draw_text("FORGE YOUR HERO — what do you remember?", 480, 580, arcade.color.GOLD, 20, anchor_x="center", bold=True)
        if self.state == "CREATOR_ORIGIN":
            arcade.draw_text("STEP 1/3 — ORIGIN (who were you?)  [1/2/3 or Up/Down + Enter]",
                             480, 545, (170, 175, 200), 13, anchor_x="center")
            for i, oid in enumerate(ORIGINS):
                o = ORIGINS[oid]
                sel = oid == self.origin_id
                y = 460 - i * 90
                arcade.draw_lbwh_rectangle_filled(180, y - 14, 600, 70, (40, 44, 70) if sel else (26, 28, 46))
                if sel:
                    arcade.draw_lbwh_rectangle_outline(180, y - 14, 600, 70, arcade.color.GOLD, 2)
                arcade.draw_text(f"{i+1}. {o['label']}", 200, y + 28, arcade.color.YELLOW if sel else arcade.color.WHITE, 16, bold=sel)
                arcade.draw_text(o["desc"], 200, y + 6, (180, 185, 210), 12)
        elif self.state == "CREATOR_CLASS":
            arcade.draw_text(f"STEP 2/3 — CLASS (how do you fight?)  Origin: {ORIGINS[self.origin_id]['label']}",
                             480, 545, (170, 175, 200), 13, anchor_x="center")
            for i, cid in enumerate(CLASSES):
                c = CLASSES[cid]
                sel = cid == self.class_id
                y = 460 - i * 90
                arcade.draw_lbwh_rectangle_filled(180, y - 14, 600, 70, (40, 44, 70) if sel else (26, 28, 46))
                if sel:
                    arcade.draw_lbwh_rectangle_outline(180, y - 14, 600, 70, arcade.color.GOLD, 2)
                arcade.draw_text(f"{i+1}. {c['label']}", 200, y + 28, arcade.color.YELLOW if sel else arcade.color.WHITE, 16, bold=sel)
                arcade.draw_text(c["desc"], 200, y + 6, (180, 185, 210), 12)
        else:
            arcade.draw_text(f"STEP 3/3 — NAME  ({ORIGINS[self.origin_id]['label']} • {CLASSES[self.class_id]['label']})",
                             480, 545, (170, 175, 200), 13, anchor_x="center")
            arcade.draw_text("Type your name, then ENTER. Backspace to edit, Esc to go back.",
                             480, 500, (150, 155, 180), 12, anchor_x="center")
            arcade.draw_lbwh_rectangle_filled(280, 380, 400, 60, (26, 28, 46))
            arcade.draw_lbwh_rectangle_outline(280, 380, 400, 60, arcade.color.GOLD, 2)
            shown = self.hero_name if self.hero_name else "___"
            arcade.draw_text(shown, 480, 398, arcade.color.WHITE, 22, anchor_x="center")
            # preview stats — teaches that origin/class = mechanics
            self.finalize_preview()
            ab = self.abilities_preview
            arcade.draw_text(f"MIGHT {ab['MIGHT']} ({ability_mod(ab['MIGHT']):+})   WIT {ab['WIT']} ({ability_mod(ab['WIT']):+})   CUNNING {ab['CUNNING']} ({ability_mod(ab['CUNNING']):+})   HP {self.hp_preview}",
                             480, 330, (150, 220, 170), 14, anchor_x="center")

    def finalize_preview(self):
        ab = {"MIGHT": 10, "WIT": 10, "CUNNING": 10}
        for k, v in ORIGINS[self.origin_id]["bonus"].items():
            ab[k] += v
        for k, v in CLASSES[self.class_id]["bonus"].items():
            ab[k] += v
        self.abilities_preview = ab
        self.hp_preview = 20 + ORIGINS[self.origin_id]["hp"] + CLASSES[self.class_id]["hp"]

    def draw_cinematic(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (5, 6, 12))
        # letterbox
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, 70, arcade.color.BLACK)
        arcade.draw_lbwh_rectangle_filled(0, SCREEN_HEIGHT - 70, SCREEN_WIDTH, 70, arcade.color.BLACK)
        line = CINEMATIC_LINES[self.cine_index] if self.cine_index < len(CINEMATIC_LINES) else ""
        arcade.draw_text(line[:int(self.cine_chars)], 480, 320, (225, 225, 240), 20,
                         anchor_x="center", anchor_y="center", width=700, align="center")
        arcade.draw_text(f"Memory {min(self.cine_index+1, len(CINEMATIC_LINES))}/{len(CINEMATIC_LINES)} — SPACE to continue",
                         480, 90, (130, 130, 150), 12, anchor_x="center")
        # faint star grows as cinematic advances
        r = 12 + self.cine_index * 8
        arcade.draw_circle_filled(480, 470, r, (200, 200, 255))

    def draw_explore(self, dim=False):
        # sand + sea
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (178, 168, 130))
        arcade.draw_lbwh_rectangle_filled(0, 500, SCREEN_WIDTH, 140, (70, 120, 170))
        for wx, wy, ww, wh in self.walls:
            if wy > 500:
                continue
            arcade.draw_lbwh_rectangle_filled(wx, wy, ww, wh, (90, 70, 50))
        # wreck + rocks labels
        arcade.draw_text("WRECK", 260, 336, (60, 40, 25), 11, bold=True)
        arcade.draw_text("ROCKS", 680, 316, (60, 60, 70), 11, bold=True)
        # signal fire (unlit/lit)
        fx, fy = 830, 480
        arcade.draw_lbwh_rectangle_filled(fx - 18, fy - 30, 36, 30, (80, 60, 40))
        if self.quest_stage >= 3:
            arcade.draw_circle_filled(fx, fy + 10, 22, (255, 140, 40))
            arcade.draw_circle_filled(fx, fy + 10, 12, (255, 230, 120))
        else:
            arcade.draw_text("UNLIT\nSIGNAL", fx, fy - 8, (50, 40, 30), 10, anchor_x="center", align="center")
        # sailor to save (flavor of Nym's ask)
        arcade.draw_circle_filled(700, 260, 12, (200, 120, 120))
        # companions not yet recruited stand at spots; recruited follow
        for c in self.companions:
            if not c["recruited"] and self.quest_stage > 1:
                continue
            arcade.draw_circle_filled(c["x"], c["y"], 14, c["color"])
            arcade.draw_text(c["name"][0], c["x"], c["y"] - 7, arcade.color.BLACK, 13, anchor_x="center", bold=True)
            arcade.draw_text(c["name"], c["x"], c["y"] + 18, arcade.color.BLACK, 11, anchor_x="center", bold=True)
        # hero
        arcade.draw_circle_filled(self.player_x, self.player_y, 15, (250, 220, 90))
        arcade.draw_circle_filled(self.player_x, self.player_y + 14, 9, (240, 200, 170))
        arcade.draw_text(self.hero_name or "Hero", self.player_x, self.player_y + 26, arcade.color.BLACK, 11, anchor_x="center", bold=True)

        if dim:
            arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 130))

        if not dim:
            # HUD
            arcade.draw_lbwh_rectangle_filled(8, SCREEN_HEIGHT - 46, 460, 38, (0, 0, 0, 200))
            arcade.draw_text(f"{self.hero_name}  {CLASSES[self.class_id]['label']}  HP {self.hp}/{self.max_hp}   "
                             f"M{self.abilities['MIGHT']} W{self.abilities['WIT']} C{self.abilities['CUNNING']}",
                             16, SCREEN_HEIGHT - 32, arcade.color.WHITE, 12)
            # quest tracker (always visible — pro RPGs never let you feel lost)
            quests = ["Wake up on the shore (find Nym [!])",
                      "Hear both sides (go to Kael [!])",
                      "Light the Signal Fire (east, [!])",
                      "Done — see recap"]
            arcade.draw_lbwh_rectangle_filled(SCREEN_WIDTH - 332, SCREEN_HEIGHT - 46, 324, 38, (0, 0, 0, 200))
            arcade.draw_text(f"◆ {quests[min(self.quest_stage, 3)]}", SCREEN_WIDTH - 322, SCREEN_HEIGHT - 32, arcade.color.YELLOW, 11)
            # approval
            arcade.draw_text(f"Nym {self.approval['Nym']:+}   Kael {self.approval['Kael']:+}",
                             SCREEN_WIDTH - 160, SCREEN_HEIGHT - 66, arcade.color.WHITE, 11)
            it = self.nearest_interact()
            if it:
                arcade.draw_text(f"[!] {it['label']}", 480, 44, arcade.color.YELLOW, 14, anchor_x="center", bold=True)
            else:
                arcade.draw_text("WASD move • E interact • J journal", 480, 30, (60, 55, 45), 12, anchor_x="center")
            if self.journal_open:
                self.draw_journal()
            # advance quest_stage when first dialogue done
            if self.quest_stage == 0 and self.companions[0]["recruited"]:
                pass  # stays 0 until wake dialogue ends? handled by end flag; force:
                if self.state == "EXPLORE" and "tone_kind" in self.flags or "tone_cold" in self.flags:
                    self.quest_stage = 1

    def draw_journal(self):
        arcade.draw_lbwh_rectangle_filled(230, 150, 500, 340, (14, 14, 26))
        arcade.draw_lbwh_rectangle_outline(230, 150, 500, 340, arcade.color.GOLD, 2)
        arcade.draw_text("JOURNAL (J to close)", 480, 455, arcade.color.GOLD, 16, anchor_x="center", bold=True)
        lines = [
            "THE PALE STAR fell. The fleet broke.",
            f"You are {self.hero_name}, {ORIGINS[self.origin_id]['label']},",
            f"trained as a {CLASSES[self.class_id]['label']}.",
            "",
            "Mystery: why did the Star hum YOUR name?",
            f"Flags: {', '.join(self.flags.keys()) or 'none yet'}",
            f"Nym approves {self.approval['Nym']:+} | Kael approves {self.approval['Kael']:+}",
        ]
        for i, ln in enumerate(lines):
            arcade.draw_text(ln, 260, 420 - i * 24, arcade.color.WHITE, 12)

    def draw_dialogue(self):
        node = self.current_node()
        # panel
        arcade.draw_lbwh_rectangle_filled(60, 30, 840, 220, (12, 12, 24))
        arcade.draw_lbwh_rectangle_outline(60, 30, 840, 220, arcade.color.GOLD, 2)
        arcade.draw_text(f"{node['speaker']}", 90, 215, arcade.color.GOLD, 15, bold=True)
        arcade.draw_text(node["text"][:int(self.reveal)], 90, 150, arcade.color.WHITE, 14, width=780, align="left")
        if self.roll_banner and self.roll_timer > 0:
            arcade.draw_text(self.roll_banner, 90, 120, arcade.color.YELLOW, 12, bold=True)
        if self.reveal >= len(node["text"]):
            for i, opt in enumerate(node["options"]):
                sel = i == self.dialog_select
                arcade.draw_text(f"{'▶' if sel else ' '} {i+1}. {opt['text']}", 90, 92 - i * 22,
                                 arcade.color.YELLOW if sel else (200, 200, 210), 12, bold=sel)

    def draw_ending(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (10, 12, 22))
        arcade.draw_text("THE FIRE IS LIT", 480, 480, arcade.color.GOLD, 30, anchor_x="center", bold=True)
        arcade.draw_text("Act 1 demo complete — this is how pro RPGs close an intro:", 480, 440, (180, 185, 210), 13, anchor_x="center")
        arcade.draw_text("recap your choices, tease the consequence, pose the next mystery.",
                         480, 420, (180, 185, 210), 13, anchor_x="center")
        side = "Peacemaker" if "peacemaker" in self.flags else ("Sided with Nym" if "sided_nym" in self.flags else "Sided with Kael")
        arcade.draw_text(f"{self.hero_name} the {CLASSES[self.class_id]['label']} — {side}",
                         480, 360, arcade.color.WHITE, 15, anchor_x="center")
        arcade.draw_text(f"Nym {self.approval['Nym']:+}   Kael {self.approval['Kael']:+}   Tone: {'kind' if 'tone_kind' in self.flags else 'cold' if 'tone_cold' in self.flags else 'guarded'}",
                         480, 330, arcade.color.YELLOW, 13, anchor_x="center")
        arcade.draw_text("Next: combat prototype (turn-based tactics) OR expand this shore with 2 more quests.",
                         480, 290, (150, 200, 170), 13, anchor_x="center")
        arcade.draw_text("Press ENTER to return to title", 480, 220, arcade.color.WHITE, 14, anchor_x="center")


def main():
    game = EmberfallGame()
    arcade.run()


if __name__ == "__main__":
    main()
