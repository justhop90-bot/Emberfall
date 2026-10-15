with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Find the character sprite system section
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

# Remove the character sprite system
new_lines = lines[:start] + lines[end:]
new_source = '\n'.join(new_lines)

try:
    compile('\n'.join(new_lines), '<test>', 'exec')
    print('SUCCESS: File compiles without character sprite system')
except SyntaxError as e:
    print(f'Still broken: {e}')