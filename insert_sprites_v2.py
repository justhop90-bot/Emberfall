with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Find where to insert (before "# ---------- input ----------")
insert_idx = None
for i, line in enumerate(lines):
    if '# ---------- input ----------' in line:
        insert_idx = i
        break

if insert_idx is None:
    print('Could not find insertion point')
    exit(1)

print(f'Inserting at line {insert_idx}')

# Read the sprite system code
with open('sprite_system_v3.py', 'r', encoding='utf-8') as f:
    sprite_code = f.read()

# The sprite code already has class-level indentation (4 spaces for def, 8 for body)
# We just need to split into lines and insert
sprite_lines = sprite_code.split('\n')

# Build new source
new_lines = lines[:insert_idx] + ['', ''] + sprite_code.split('\n') + ['', ''] + lines[insert_idx:]

with open('EmberfallAct1.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('Inserted character sprite system at class level')