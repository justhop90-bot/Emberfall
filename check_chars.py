with open('EmberfallAct1.py', 'rb') as f:
    content = f.read()

# Check for BOM
if content.startswith(b'\xef\xbb\xbf'):
    print('HAS UTF-8 BOM')
elif content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
    print('HAS UTF-16 BOM')

# Check line endings
cr_count = content.count(b'\r')
lf_count = content.count(b'\n')
crlf_count = content.count(b'\r\n')
print('CR:', cr_count, 'LF:', lf_count, 'CRLF:', crlf_count)

# Check for any non-ASCII in the problematic area
idx = content.find(b'def _init_character_sprites')
if idx >= 0:
    context = content[max(0, idx-50):idx+100]
    for i, b in enumerate(context):
        if b >= 128:
            print('Non-ASCII at offset', idx+i, ':', b, chr(b) if b < 256 else '?')

# Also check for any zero-width characters or other invisible chars
for i, b in enumerate(content):
    if b in (0x200b, 0x200c, 0x200d, 0xfeff, 0xfffe):
        print('Invisible char at offset', i, ':', hex(b))
print('Done')