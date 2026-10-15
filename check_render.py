with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Find the _render_character_frame method area
for i, line in enumerate(lines):
    if '_render_character_frame' in line and 'def ' in line:
        print(f'Line {i+1}: {lines[i]!r}')
        break

# Check around line 2000-2010
for i in range(1980, 2020):
    if i < len(lines):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f'{i+1}: indent={indent} | {lines[i]!r}')