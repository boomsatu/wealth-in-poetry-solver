import re
import itertools
import time
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

print(f"Scanning Revolution (words={len(words)})...")
t0 = time.time()
tested = 0
valid_checksums = 0
found = False

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
    if not possible:
        continue
    
    for combo in itertools.product(*blocks):
        tested += 1
        phrase = " ".join(combo)
        if validator.IsValid(phrase):
            valid_checksums += 1
            seed = Bip39SeedGenerator(phrase).Generate()
            mst = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            # test standard address 0 and 1
            for addr_idx in range(2):
                addr = mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(addr_idx).PublicKey().ToAddress()
                if addr == target:
                    print(f"\n🎯🎯🎯 TARGET FOUND at window {start_idx} 🎯🎯🎯")
                    print(f"Mnemonic: {phrase}")
                    print(f"Address {addr_idx}: {addr}")
                    found = True
                    break
        if found:
            break
    if found:
        break

t1 = time.time()
print(f"Done in {t1-t0:.2f}s. Tested: {tested}, Valid checksums: {valid_checksums}, Found: {found}")
