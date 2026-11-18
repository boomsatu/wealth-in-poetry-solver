import re
import itertools
from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"

with open('text.txt', encoding='utf-8') as f:
    full_text = f.read()

paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
p11 = paragraphs[11]

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

raw_words = p11.split()
clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_words if re.sub(r'[^a-zA-Z]', '', w)]

blocks = []
for b in range(12):
    block_words = [clean_words[i] for i in range(b*10, min((b+1)*10, len(clean_words))) if clean_words[i] in bip39]
    blocks.append(block_words)

validator = Bip39MnemonicValidator()

valid_checksum_count = 0
tested = 0
found = False

for combo in itertools.product(*blocks):
    phrase = " ".join(combo)
    tested += 1
    if validator.IsValid(phrase):
        valid_checksum_count += 1
        seed_bytes = Bip39SeedGenerator(phrase).Generate()
        bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        # test both address 0, and uncompressed/compressed, or account 0
        for addr_idx in range(5):
            addr = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(addr_idx).PublicKey().ToAddress()
            if addr == target:
                print(f"FOUND MATCH in P11 with BIP44: {phrase}")
                found = True
                break

print(f"P11 test complete. Tested: {tested}, Valid checksums: {valid_checksum_count}, Found: {found}")
