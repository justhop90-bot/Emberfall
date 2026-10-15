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

print(f'Removing lines {start} to {end}')
new_lines = lines[:start] + lines[end:]
new_source = '\n'.join(new_lines)

with open('EmberfallAct1.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('Removed character sprite system')