with open('text.txt', encoding='utf-8') as f:
    full_text = f.read()

paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

import re

for idx in [46, 47, 48, 49]:
    p = paragraphs[idx]
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in p.split() if re.sub(r'[^a-zA-Z]', '', w)]
    bip_words = [w for w in words if w in bip39]
    print(f"\nParagraph {idx}:")
    print(p)
    print(f"BIP39 words ({len(bip_words)}):", bip_words)
