import re
from collections import Counter

with open('text.txt', encoding='utf-8') as f:
    text = f.read()

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

raw_words = text.split()
clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_words if re.sub(r'[^a-zA-Z]', '', w)]
bip39_words = [w for w in clean_words if w in bip39]

print("Total words in text.txt:", len(clean_words))
print("Total BIP-39 occurrences in text.txt:", len(bip39_words))
print("Unique BIP-39 words in text.txt:", len(set(bip39_words)))

counts = Counter(bip39_words)
print("\nMost common BIP-39 words:")
for w, c in counts.most_common(20):
    print(f"  {w}: {c}")

print("\nBIP-39 words appearing only ONCE:")
once = [w for w, c in counts.items() if c == 1]
print(f"Count of words appearing only once: {len(once)}")
print(once)
