import ast

with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

# Try parsing the whole file
try:
    ast.parse(source)
    print('Syntax OK')
except SyntaxError as e:
    print('SyntaxError:', e)
    print('Line:', e.lineno)
    print('Offset:', e.offset)
    print('Text:', e.text)

# Now test without the character sprite system
lines = source.split('\n')
start = None
end = None
for i, line in enumerate(lines):
    if '# ===== CHARACTER SPRITE SYSTEM =====' in line:
        start = i
    if start is not None and i > start and line.strip() and not line.startswith(' ') and not line.startswith('#') and not line.strip().startswith('"""'):
        end = i
        break

print('Start:', start, 'End:', end)

if start is not None and end is not None:
    new_lines = lines[:start] + lines[end:]
    new_source = '\n'.join(new_lines)
    try:
        ast.parse(new_source)
        print('Syntax OK without character sprite system')
    except SyntaxError as e:
        print('Still has error:', e)
    except Exception as e:
        print('Other error:', e)
else:
    print('Could not find section boundaries')