import ast

with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Find section boundaries
start = None
for i, line in enumerate(lines):
    if '# ===== CHARACTER SPRITE SYSTEM =====' in line:
        start = i
        break

end = None
for i in range(start + 1, len(lines)):
    line = lines[i]
    if line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#') and not line.strip().startswith('"""'):
        end = i
        break

print(f'Section: {start} to {end}')

# Test with full init method
test_lines = lines[:start] + [
    '# ===== CHARACTER SPRITE SYSTEM =====',
    '    def _init_character_sprites(self):',
    '        """Initialize character sprite system with 4-directional animated sprites."""',
    '        self.char_sprites = {}',
    '        ',
    '        # Character definitions with their color schemes',
    '        char_defs = {',
    '            "hero": {"colors": [(200, 170, 60), (255, 220, 90), (240, 203, 170)], "scale": 1.0},',
    '            "nym": {"colors": [(170, 120, 235), (200, 150, 245), (240, 203, 170)], "scale": 0.9},',
    '            "kael": {"colors": [(235, 160, 80), (255, 190, 120), (232, 190, 160)], "scale": 1.1},',
    '            "maren": {"colors": [(150, 200, 140), (180, 220, 170), (220, 210, 190)], "scale": 0.95},',
    '            "per": {"colors": [(90, 170, 220), (120, 190, 240), (220, 210, 190)], "scale": 0.95},',
    '            "joss": {"colors": [(120, 130, 150), (150, 160, 180), (200, 190, 180)], "scale": 1.0},',
    '            "tess": {"colors": [(220, 210, 230), (200, 190, 210), (240, 230, 240)], "scale": 0.95},',
    '            "pilgrim": {"colors": [(160, 140, 170), (140, 120, 150), (200, 190, 180)], "scale": 0.9},',
    '            "mourn_crab": {"colors": [(200, 90, 80), (220, 110, 100), (180, 70, 60)], "scale": 0.8},',
    '            "wreckghast": {"colors": [(150, 160, 220), (180, 190, 240), (130, 140, 200)], "scale": 0.9},',
    '            "tidecaller": {"colors": [(90, 200, 170), (120, 220, 190), (70, 180, 150)], "scale": 1.0},',
    '            "star_warden": {"colors": [(220, 200, 90), (240, 220, 120), (200, 180, 70)], "scale": 1.2},',
    '            "deepmaw": {"colors": [(120, 40, 60), (160, 80, 100), (90, 30, 50)], "scale": 1.1},',
    '        }',
    '        ',
    '        for char_id, defn in char_defs.items():',
    '            self.char_sprites[char_id] = self._generate_character_sprites(defn)',
    '        ',
    '        self.char_anim_state = {}',
    '',
] + lines[3319:]

try:
    compile('\n'.join(test_lines), '<test>', 'exec')
    print('SUCCESS with full init method')
except SyntaxError as e:
    print(f'FAIL: {e}')
    print(f'Line {e.lineno}: {e.text}')