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

print(f'Section: lines {start} to {end}')

# Fix indentation: remove 4 spaces from each line in the section
new_lines = lines[:start]
for i in range(start, end):
    line = lines[i]
    if line.startswith('        '):  # 8 spaces
        new_lines.append(line[4:])  # Remove 4 spaces
    elif line.startswith('    '):  # 4 spaces
        new_lines.append(line)  # Keep as is
    else:
        new_lines.append(line)

new_lines.extend(lines[end:])

with open('EmberfallAct1.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('Fixed indentation')