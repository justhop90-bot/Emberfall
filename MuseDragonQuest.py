import arcade
import random
import math

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640

STATE_OVERWORLD = 0
STATE_BATTLE = 1

class Enemy:
    def __init__(self, x, y, kind="slime"):
        self.x = x
        self.y = y
        self.kind = kind
        if kind == "slime":
            self.name = "Slime"
            self.max_hp = 18
            self.atk = 7
            self.exp = 25
        else:
            self.name = "Dracky"
            self.max_hp = 24
            self.atk = 9
            self.exp = 35
        self.hp = self.max_hp
        self.angle = random.uniform(0, math.pi*2)
        self.timer = 0

    def update(self, walls, delta_time):
        self.timer -= delta_time
        if self.timer <= 0:
            self.angle = random.uniform(0, math.pi*2)
            self.timer = random.uniform(1.0, 3.0)
        
        speed = 40
        new_x = self.x + math.cos(self.angle) * speed * delta_time
        new_y = self.y + math.sin(self.angle) * speed * delta_time

        if new_x < 32 or new_x > SCREEN_WIDTH - 32 or self.collides(new_x, self.y, walls):
            self.angle = math.pi - self.angle
        elif new_y < 100 or new_y > SCREEN_HEIGHT - 32 or self.collides(self.x, new_y, walls):
            self.angle = -self.angle
        else:
            self.x = new_x
            self.y = new_y

    def collides(self, x, y, walls):
        for wx, wy, ww, wh in walls:
            if wx < x < wx + ww and wy < y < wy + wh:
                return True
        return False

class DragonQuestGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Muse RPG - DQ8 Inspired")
        self.state = STATE_OVERWORLD
        
        self.player_x = 480
        self.player_y = 320
        self.player_speed = 180
        self.keys = set()
        
        self.level = 1
        self.max_hp = 35
        self.hp = 35
        self.max_mp = 12
        self.mp = 12
        self.atk = 10
        self.exp = 0
        self.exp_to_level = 50

        self.walls = [
            (0, 0, SCREEN_WIDTH, 24),
            (0, 0, 24, SCREEN_HEIGHT),
            (SCREEN_WIDTH-24, 0, 24, SCREEN_HEIGHT),
            (0, SCREEN_HEIGHT-24, SCREEN_WIDTH, 24),
            (200, 200, 96, 32),
            (600, 450, 32, 96),
            (350, 380, 128, 32),
            (150, 450, 64, 64),
            (700, 200, 96, 96),
        ]

        self.enemies = [
            Enemy(200, 300, "slime"),
            Enemy(700, 400, "slime"),
            Enemy(500, 150, "dracky"),
            Enemy(300, 500, "slime"),
        ]

        self.battle_enemy = None
        self.battle_menu = ["Attack", "Heal", "Run"]
        self.battle_select = 0
        self.battle_log = []
        self.battle_turn = "player"
        self.battle_timer = 0
        self.current_overworld_enemy = None

        arcade.set_background_color((110, 180, 90))

    def on_draw(self):
        self.clear()
        if self.state == STATE_OVERWORLD:
            self.draw_overworld()
        else:
            self.draw_battle()

    def draw_slime(self, x, y, kind, size):
        if kind == "slime":
            arcade.draw_circle_filled(x, y, size, (0, 180, 220))
            arcade.draw_circle_filled(x, y+size*0.6, size*0.7, (0, 180, 220))
            arcade.draw_circle_filled(x-5, y+2, 3, arcade.color.BLACK)
            arcade.draw_circle_filled(x+5, y+2, 3, arcade.color.BLACK)
        else:
            arcade.draw_circle_filled(x, y, size, (80, 80, 255))
            arcade.draw_circle_filled(x, y+12, 8, (80, 80, 255))
            arcade.draw_circle_filled(x-12, y+8, 6, (60, 60, 180))
            arcade.draw_circle_filled(x+12, y+8, 6, (60, 60, 180))

    def draw_overworld(self):
        # grass
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (125, 190, 100))
        
        # walls / trees
        for wx, wy, ww, wh in self.walls:
            arcade.draw_lbwh_rectangle_filled(wx, wy, ww, wh, (90, 60, 30))
            arcade.draw_lbwh_rectangle_filled(wx+4, wy+4, ww-8, wh-8, (60, 130, 60))

        for e in self.enemies:
            self.draw_slime(e.x, e.y, e.kind, 18)

        # player
        arcade.draw_circle_filled(self.player_x, self.player_y, 16, (255, 220, 80))
        arcade.draw_circle_filled(self.player_x, self.player_y+14, 10, (240, 200, 170))
        arcade.draw_circle_filled(self.player_x, self.player_y+18, 12, (60, 120, 200))

        # UI
        arcade.draw_lbwh_rectangle_filled(8, SCREEN_HEIGHT-40, SCREEN_WIDTH-16, 36, (0, 0, 0))
        arcade.draw_text(f"Lv:{self.level}  HP:{self.hp}/{self.max_hp}  MP:{self.mp}/{self.max_mp}  EXP:{self.exp}/{self.exp_to_level}", 20, SCREEN_HEIGHT-30, arcade.color.WHITE, 14)
        arcade.draw_text("Touch a monster to battle! | DQ8 Inspired", 520, SCREEN_HEIGHT-28, arcade.color.WHITE, 11)

    def draw_battle(self):
        arcade.draw_lbwh_rectangle_filled(0, 240, SCREEN_WIDTH, SCREEN_HEIGHT-240, (135, 206, 235))
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, 240, (180, 220, 120))

        if self.battle_enemy:
            bx = SCREEN_WIDTH/2
            by = SCREEN_HEIGHT/2 + 40
            self.draw_slime(bx, by, self.battle_enemy.kind, 50)
            arcade.draw_lbwh_rectangle_filled(bx-60, by+90, 120, 12, arcade.color.BLACK)
            pct = self.battle_enemy.hp / self.battle_enemy.max_hp
            arcade.draw_lbwh_rectangle_filled(bx-60, by+90, 120*pct, 10, arcade.color.RED)
            arcade.draw_text(f"{self.battle_enemy.name}", bx-40, by+110, arcade.color.BLACK, 16, bold=True)

        # menu window
        arcade.draw_lbwh_rectangle_filled(20, 20, 260, 130, (10, 10, 80))
        arcade.draw_lbwh_rectangle_outline(20, 20, 260, 130, arcade.color.WHITE, 3)
        
        for i, option in enumerate(self.battle_menu):
            color = arcade.color.YELLOW if i == self.battle_select else arcade.color.WHITE
            prefix = ">" if i == self.battle_select else " "
            arcade.draw_text(f"{prefix} {option}", 40, 115 - i*30, color, 18)

        # log window
        arcade.draw_lbwh_rectangle_filled(300, 20, 640, 130, (0, 0, 0))
        arcade.draw_lbwh_rectangle_outline(300, 20, 640, 130, arcade.color.WHITE, 3)
        
        for i, line in enumerate(self.battle_log[-4:]):
            arcade.draw_text(line, 320, 110 - i*24, arcade.color.WHITE, 13)

        arcade.draw_text(f"HERO Lv{self.level} HP:{self.hp}/{self.max_hp} MP:{self.mp}/{self.max_mp}", 320, 25, arcade.color.WHITE, 12)

    def on_update(self, delta_time):
        if self.state == STATE_OVERWORLD:
            dx = dy = 0
            if arcade.key.W in self.keys or arcade.key.UP in self.keys:
                dy += 1
            if arcade.key.S in self.keys or arcade.key.DOWN in self.keys:
                dy -= 1
            if arcade.key.A in self.keys or arcade.key.LEFT in self.keys:
                dx -= 1
            if arcade.key.D in self.keys or arcade.key.RIGHT in self.keys:
                dx += 1
            
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071

            new_x = self.player_x + dx * self.player_speed * delta_time
            new_y = self.player_y + dy * self.player_speed * delta_time

            blocked = False
            for wx, wy, ww, wh in self.walls:
                if wx-14 < new_x < wx+ww+14 and wy-14 < new_y < wy+wh+14:
                    blocked = True
            if not blocked:
                if 32 < new_x < SCREEN_WIDTH-32:
                    self.player_x = new_x
                if 100 < new_y < SCREEN_HEIGHT-32:
                    self.player_y = new_y

            for e in self.enemies:
                e.update(self.walls, delta_time)
                dist = math.hypot(self.player_x - e.x, self.player_y - e.y)
                if dist < 28:
                    self.start_battle(e)
                    break
        else:
            self.battle_timer -= delta_time
            if self.battle_turn == "enemy" and self.battle_timer <= 0:
                self.enemy_turn()

    def start_battle(self, enemy):
        self.state = STATE_BATTLE
        self.battle_enemy = Enemy(0,0, enemy.kind)
        self.battle_enemy.name = enemy.name
        self.battle_enemy.max_hp = enemy.max_hp
        self.battle_enemy.hp = enemy.max_hp
        self.battle_enemy.atk = enemy.atk
        self.battle_enemy.exp = enemy.exp
        self.current_overworld_enemy = enemy
        
        self.battle_log = [f"A wild {enemy.name} appears!", "What will you do?"]
        self.battle_select = 0
        self.battle_turn = "player"

    def end_battle(self, won):
        if won:
            self.battle_log.append(f"You defeated the {self.battle_enemy.name}!")
            self.battle_log.append(f"Gained {self.battle_enemy.exp} EXP!")
            self.exp += self.battle_enemy.exp
            if self.exp >= self.exp_to_level:
                self.level_up()
            if self.current_overworld_enemy in self.enemies:
                self.enemies.remove(self.current_overworld_enemy)
            if len(self.enemies) < 3:
                self.enemies.append(Enemy(random.randint(100, 860), random.randint(120, 500), random.choice(["slime","slime","dracky"])))
            self.state = STATE_OVERWORLD
        else:
            self.battle_log.append("You were defeated...")
            self.hp = self.max_hp
            self.mp = self.max_mp
            self.player_x = 480
            self.player_y = 320
            self.state = STATE_OVERWORLD

    def level_up(self):
        self.exp -= self.exp_to_level
        self.level += 1
        self.exp_to_level = int(self.exp_to_level * 1.4)
        self.max_hp += 8
        self.max_mp += 4
        self.atk += 3
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.battle_log.append(f"LEVEL UP! Now Lv {self.level}!")

    def on_key_press(self, key, modifiers):
        self.keys.add(key)
        if self.state == STATE_BATTLE and self.battle_turn == "player":
            if key in (arcade.key.UP, arcade.key.W):
                self.battle_select = (self.battle_select - 1) % len(self.battle_menu)
            elif key in (arcade.key.DOWN, arcade.key.S):
                self.battle_select = (self.battle_select + 1) % len(self.battle_menu)
            elif key in (arcade.key.ENTER, arcade.key.SPACE):
                choice = self.battle_menu[self.battle_select]
                if choice == "Attack":
                    dmg = random.randint(self.atk-2, self.atk+4)
                    self.battle_enemy.hp -= dmg
                    self.battle_log.append(f"You attack for {dmg} damage!")
                    if self.battle_enemy.hp <= 0:
                        self.end_battle(True)
                    else:
                        self.battle_turn = "enemy"
                        self.battle_timer = 1.0
                elif choice == "Heal":
                    if self.mp >= 4:
                        self.mp -= 4
                        heal = 20
                        self.hp = min(self.max_hp, self.hp + heal)
                        self.battle_log.append(f"You cast Heal! +{heal} HP!")
                        self.battle_turn = "enemy"
                        self.battle_timer = 1.0
                    else:
                        self.battle_log.append("Not enough MP!")
                elif choice == "Run":
                    if random.random() < 0.5:
                        self.battle_log.append("You ran away!")
                        self.state = STATE_OVERWORLD
                    else:
                        self.battle_log.append("Couldn't escape!")
                        self.battle_turn = "enemy"
                        self.battle_timer = 1.0

    def on_key_release(self, key, modifiers):
        if key in self.keys:
            self.keys.remove(key)

    def enemy_turn(self):
        if self.battle_enemy.hp <= 0:
            return
        dmg = random.randint(self.battle_enemy.atk-2, self.battle_enemy.atk+2)
        self.hp -= dmg
        self.battle_log.append(f"{self.battle_enemy.name} attacks for {dmg}!")
        if self.hp <= 0:
            self.hp = 0
            self.battle_log.append("You fell...")
            arcade.schedule(lambda dt: self.end_battle(False), 1.0)
        else:
            self.battle_turn = "player"

game = DragonQuestGame()
arcade.run()