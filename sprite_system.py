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