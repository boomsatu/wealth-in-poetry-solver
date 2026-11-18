with open('text.txt', encoding='utf-8') as f:
    full_text = f.read()

paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

import re

print(f"Total paragraphs: {len(paragraphs)}\n")
for idx, p in enumerate(paragraphs):
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in p.split() if re.sub(r'[^a-zA-Z]', '', w)]
    bip_words = [w for w in words if w in bip39]
    print(f"P {idx:2d} (words={len(words):3d}, bip39={len(bip_words):2d}): {bip_words[:6]}")
