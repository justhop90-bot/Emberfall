with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()
lines = source.split('\n')
snippet = '\n'.join(lines[2678:2700])  # draw_guy method body

parens = 0
brackets = 0
braces = 0
for i, ch in enumerate(snippet):
    if ch == '(': parens += 1
    elif ch == ')': parens -= 1
    elif ch == '[': brackets += 1
    elif ch == ']': brackets -= 1
    elif ch == '{': braces += 1
    elif ch == '}': braces -= 1
print(f'Parens: {parens}, Brackets: {brackets}, Braces: {braces}')

single = snippet.count("'")
double = snippet.count('"')
triple_single = snippet.count("'''")
triple_double = snippet.count('"""')
print(f'Single quotes: {single}, Double: {double}, Triple single: {triple_single}, Triple double: {triple_double}')