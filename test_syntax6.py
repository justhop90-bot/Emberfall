import ast

with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Find the character sprite system section
start = None
for i, line in enumerate(lines):
    if '# ===== CHARACTER SPRITE SYSTEM =====' in line:
        start = i
        break

# Find the end - next top-level class method (not indented)
end = None
if start is not None:
    for i in range(start + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()
        if stripped and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#') and not line.strip().startswith('"""'):
            end = i
            break

print('Section: lines', start, 'to', end)

# Test: remove the entire section
if start is not None and end is not None:
    new_lines = lines[:start] + lines[end:]
    new_source = '\n'.join(new_lines)
    try:
        ast.parse('\n'.join(new_lines))
        print('SUCCESS: File parses without character sprite system')
    except SyntaxError as e:
        print('FAIL:', e)

# Now test adding back just the first method
method_lines = []
in_method = False
for i in range(start, min(start + 100, len(lines))):
    line = lines[i]
    if 'def _init_character_sprites' in line:
        in_method = True
    if in_method:
        method_lines.append(line)
    if in_method and line.strip() and not line.startswith(' ') and not line.startswith('\t') and i > start + 1:
        break

print(f'_init_character_sprites method lines: {len(method_lines)}')
for j, ml in enumerate(method_lines[:10]):
    print('  ', repr(ml))

# Test with just the init method
new_lines2 = lines[:start] + method_lines + lines[end:]
try:
    ast.parse('\n'.join(new_lines2))
    print('SUCCESS with just _init_character_sprites')
except SyntaxError as e:
    print(f'FAIL with just init: {e}')