with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Find where to insert the sprite system (after the _draw_lighting method, before # ---------- input ----------)
insert_idx = None
for i, line in enumerate(lines):
    if '# ---------- input ----------' in line:
        insert_idx = i
        break

if insert_idx is None:
    print('Could not find insertion point')
else:
    print(f'Inserting at line {insert_idx}')

# Read the sprite system code
with open('sprite_system.py', 'r', encoding='utf-8') as f:
    sprite_code = f.read()

# Split into lines
sprite_lines = sprite_code.split('\n')

# Indent the sprite code to class level (4 spaces)
indented_sprite_lines = ['    ' + line if line.strip() else '' for line in sprite_code.split('\n')]

# Build new source
new_lines = lines[:insert_idx] + ['', ''] + indented_sprite_lines + ['', ''] + lines[insert_idx:]

with open('EmberfallAct1.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('Inserted character sprite system')