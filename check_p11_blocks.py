import re

with open('text.txt', encoding='utf-8') as f:
    full_text = f.read()

paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
p11 = paragraphs[11]

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

raw_words = p11.split()
clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_words if re.sub(r'[^a-zA-Z]', '', w)]
print(f"Total clean words in P11: {len(clean_words)}")

for b in range(12):
    block_words = [(i+1, clean_words[i]) for i in range(b*10, min((b+1)*10, len(clean_words))) if clean_words[i] in bip39]
    print(f"Block {b:2d} (words {b*10+1:3d} to {(b+1)*10:3d}): {block_words}")
