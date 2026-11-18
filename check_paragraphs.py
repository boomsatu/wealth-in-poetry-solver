import re

with open('clean_article.txt', encoding='utf-8') as f:
    full_text = f.read()

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

# Let's split by paragraphs or sections
paragraphs = full_text.split('\n\n')
print(f"Total paragraphs: {len(paragraphs)}")

for p_idx, p in enumerate(paragraphs):
    raw_words = p.split()
    clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_words if re.sub(r'[^a-zA-Z]', '', w)]
    if len(clean_words) >= 114:
        print(f"\n--- Paragraph {p_idx} (len={len(clean_words)}) ---")
        print(" ".join(clean_words[:20]) + "...")
        # Check blocks of 10
        blocks = []
        possible = True
        for b in range(12):
            block_words = [(i, clean_words[i]) for i in range(b*10, min((b+1)*10, len(clean_words))) if clean_words[i] in bip39]
            blocks.append(block_words)
            if not block_words:
                possible = False
        print(f"Has BIP39 in all 12 blocks of 10? {possible}")
        if possible:
            for b in range(12):
                print(f"  Block {b} ({b*10}-{(b+1)*10-1}): {blocks[b]}")
