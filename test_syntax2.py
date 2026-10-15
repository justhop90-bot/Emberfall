import ast

with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

# Find the exact boundaries of the character sprite system
lines = source.split('\n')
start = None
for i, line in enumerate(lines):
    if '# ===== CHARACTER SPRITE SYSTEM =====' in line:
        start = i
        break

# Find the end - next class method or end of class
end = None
if start is not None:
    for i in range(start + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()
        if stripped and not line.startswith(' ') and not line.startswith('\t') and not stripped.startswith('#') and not stripped.startswith('"""'):
            end = i
            break

print('Start line:', start)
print('End line:', end)

# Remove the character sprite system section
if start is not None and end is not None:
    new_lines = lines[:start] + lines[end:]
    new_source = '\n'.join(new_lines)
    try:
        ast.parse(new_source)
        print('Syntax OK without character sprite system')
    except SyntaxError as e:
        print('Still has error:', e)
else:
    print('Could not find section boundaries')

# Also test: just remove the _init_character_sprites method
lines2 = source.split('\n')
method_start = None
method_end = None
for i, line in enumerate(lines):
    if 'def _init_character_sprites' in line:
        method_start = i
    elif method_start is not None and method_end is None:
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#') and not line.strip().startswith('"""'):
            method_end = i
            break

if method_start is not None and method_end is not None:
    print('Method start:', method_start, 'end:', method_end)
    new_lines2 = lines[:method_start] + lines[method_end:]
    source2 = '\n'.join(new_lines2)
    try:
        ast.parse(source2)
        print('Syntax OK without _init_character_sprites method')
    except SyntaxError as e:
        print('Still has error without method:', e)