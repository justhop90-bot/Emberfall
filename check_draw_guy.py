with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Check the last few lines of draw_guy method
print('Last 15 lines of draw_guy area:')
for i in range(2690, 2710):
    if i < len(lines):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f'{i+1}: indent={indent} | {lines[i]!r}')