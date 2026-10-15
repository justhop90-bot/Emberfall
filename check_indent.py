with open('EmberfallAct1.py', 'rb') as f:
    content = f.read()
lines = content.split(b'\n')
for i, line in enumerate(lines[2678:2710], 2679):
    indent = len(line) - len(line.lstrip(b' '))
    if indent <= 4 and line.strip() and not line.strip().startswith(b'#') and not line.strip().startswith(b'"""') and i > 2679:
        print(f'LINE {i+1}: indent={indent} | {line!r}')