p47 = "It can be easy to overlook the point of bitcoin living in a country where people trust their government. What happens to those who can’t? What has happened to those who couldn’t? It is truly a privilege to be unaware of the importance of trust."

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

import re
raw_words = p47.split()
clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_words if re.sub(r'[^a-zA-Z]', '', w)]

print(f"Total words in P47: {len(clean_words)}")
bip_in_p47 = []
for i, w in enumerate(clean_words, 1):
    is_b = w in bip39
    if is_b:
        bip_in_p47.append((i, w))
    print(f"{i:2d}: {w:15s} -> {is_b}")

print(f"\nTotal BIP39 words in P47: {len(bip_in_p47)}")
print("Words:", [w for _, w in bip_in_p47])
