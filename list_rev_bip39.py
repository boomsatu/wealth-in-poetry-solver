import re

with open('clean_article.txt', encoding='utf-8') as f:
    text = f.read()

start = text.find('Revolution')
end = text.find('Fiat')
rev_text = text[start:end].strip()

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

raw_words = rev_text.split()
clean_words = [(i+1, re.sub(r'[^a-zA-Z]', '', w).lower()) for i, w in enumerate(raw_words) if re.sub(r'[^a-zA-Z]', '', w)]

bip_words = [(pos, w) for pos, w in clean_words if w in bip39]
print(f"Total BIP39 words in Revolution: {len(bip_words)}")
for pos, w in bip_words:
    print(f"{pos:3d}: {w}")
