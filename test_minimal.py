import ast

with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Test adding back pieces of the character sprite system
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

# Test adding back just the comment + init method
comment_line = lines[start]
method_def = '    def _init_character_sprites(self):'
docstring = '        """Initialize character sprite system with 4-directional animated sprites."""'
init_line = '        self.char_sprites = {}'

# Build test: draw_guy + comment + init method
test_lines = lines[:2700] + [
    lines[start],  # comment
    '    def _init_character_sprites(self):',
    '        """Initialize character sprite system with 4-directional animated sprites."""',
    '        self.char_sprites = {}',
    '        char_defs = {',
    '            "hero": {"colors": [(200, 170, 60), (255, 220, 90), (240, 203, 170)], "scale": 1.0},',
    '            "nym": {"colors": [(170, 120, 235), (200, 150, 245), (240, 203, 170)], "scale": 0.9},',
    '            "kael": {"colors": [(235, 160, 80), (255, 190, 120), (232, 190, 160)], "scale": 1.1},',
    '        }',
    '        for char_id, defn in char_defs.items():',
    '            pass',  # placeholder
    '        self.char_anim_state = {}',
    '',  # empty line
] + lines[2700:]  # rest of file after the section

test_source = '\n'.join(test_lines)
try:
    compile('\n'.join(test_lines), '<test>', 'exec')
    print('SUCCESS with minimal init method')
except SyntaxError as e:
    print(f'FAIL: {e}')
    print(f'Line {e.lineno}: {e.text}')