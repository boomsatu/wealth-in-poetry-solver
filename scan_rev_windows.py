import re
import itertools
from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
validator = Bip39MnemonicValidator()

with open('english.txt') as f:
    bip39_set = set(line.strip() for line in f)

with open('clean_article.txt', encoding='utf-8') as f:
    text = f.read()

start = text.find('Revolution')
end = text.find('Fiat')
rev_text = text[start:end].strip()

raw_words = rev_text.split()
words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_words if re.sub(r'[^a-zA-Z]', '', w)]
print(f"Total words in Revolution: {len(words)}")

valid_windows = []
for start_idx in range(len(words) - 120 + 1):
    window = words[start_idx : start_idx + 120]
    blocks = []
    possible = True
    for b in range(12):
        block_bip = [window[b*10 + j] for j in range(10) if window[b*10 + j] in bip39_set]
        if not block_bip:
            possible = False
            break
        blocks.append(block_bip)
    if possible:
        combos = 1
        for b in blocks:
            combos *= len(b)
        valid_windows.append((start_idx, combos, blocks))

print(f"Number of 120-word windows with at least one BIP39 word in EVERY block: {len(valid_windows)}")
total_combos = sum(c for _, c, _ in valid_windows)
print(f"Total combinations across all valid windows: {total_combos}")
