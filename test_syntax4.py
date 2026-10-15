import ast

with open('EmberfallAct1.py', 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

# Test each method individually
methods = [
    ('_init_character_sprites', 2701, 2728),
    ('_generate_character_sprites', 2729, 2795),
    ('_draw_character_sprite', 2796, 2820),
    ('_render_character_frame', 2821, 2870),
]

for name, start, end in methods:
    # Find actual boundaries
    method_start = None
    method_end = None
    for i in range(start-1, min(end+1, len(lines))):
        if f'def {name}' in lines[i]:
            method_start = i
        elif method_start is not None and i > start:
            if lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t') and not lines[i].startswith('#') and not lines[i].strip().startswith('"""'):
                method_end = i
                break
    
    if method_start is not None and method_end is not None:
        # Test without this method
        new_lines = lines[:method_start] + lines[method_end:]
        new_source = '\n'.join(new_lines)
        try:
            ast.parse('\n'.join(new_lines))
            print(f'{name}: OK when removed')
        except SyntaxError as e:
            print(f'{name}: STILL BROKEN - {e}')
        except Exception as e:
            print(f'{name}: OTHER ERROR - {e}')
    else:
        print(f'{name}: Could not find boundaries (start={method_start}, end={method_end})')