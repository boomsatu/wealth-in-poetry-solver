import re

with open('text.txt', encoding='utf-8') as f:
    full_text = f.read()

paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
print(f"Total paragraphs in text.txt: {len(paragraphs)}")

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

for p_idx, p in enumerate(paragraphs):
    raw_words = p.split()
    clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_words if re.sub(r'[^a-zA-Z]', '', w)]
    print(f"P {p_idx:2d} (len={len(clean_words):3d}): {' '.join(clean_words[:8])}...")
