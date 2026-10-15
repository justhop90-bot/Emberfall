import ast

with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Check if draw_guy method ends properly
# Find draw_guy method
draw_guy_start = None
for i, line in enumerate(lines):
    if 'def draw_guy' in line and 'def draw_guy' == line.strip()[:14]:
        print(f'draw_guy at line {i+1}: {lines[i].strip()}')

# Find the end of draw_guy method (next method at class level)
for i in range(2679, len(lines)):
    line = lines[i]
    if line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#') and not line.strip().startswith('"""'):
        if i > 2679:
            print(f'Next top-level at line {i+1}: {lines[i].strip()}')
            break

# Check the last few lines of draw_guy method
print('Last 10 lines of draw_guy area:')
for i in range(2690, 2705):
    indent = len(lines[i]) - len(lines[i].lstrip())
    print(f'  {i+1}: indent={indent} | {lines[i]!r}')