from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
import itertools
import re

TARGET = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
v = Bip39MnemonicValidator()

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

bqs = [
    "How can we best enable the safe migration of people and their value?",
    "A trithemian seed is a list of cryptocurrency backup seed phrases stored in an innocuous body of writing, such as a poem, story, or letter.",
    "The beauty of trithemian seeds is that they hide in plain sight. If you've read this far, you've read every word required to access a wallet with .03 BTC. Good luck!"
]

all_bq_bip = []
for i, bq in enumerate(bqs):
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in bq.split()]
    bip = [w for w in words if w in bip39]
    print(f"BQ {i+1} ({len(bip)}): {bip}")
    all_bq_bip.append(bip)

# Test combinations of 12 words from these blockquotes
flat_bq = []
for b in all_bq_bip:
    flat_bq.extend(b)

print(f"Total BIP words across 3 blockquotes: {len(flat_bq)}")
print("Flat list:", flat_bq)

# Test sliding windows of 12
for i in range(len(flat_bq) - 11):
    win = flat_bq[i:i+12]
    phrase = ' '.join(win)
    if v.IsValid(phrase):
        print("VALID sliding window:", phrase)
        seed = Bip39SeedGenerator(phrase).Generate()
        addr = Bip44.FromSeed(seed, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
        print("Addr:", addr)
        if addr == TARGET:
            print("MATCH!")

# Test unique words in order
unique_flat = list(dict.fromkeys(flat_bq))
print(f"Unique BIP words across blockquotes ({len(unique_flat)}): {unique_flat}")
for i in range(len(unique_flat) - 11):
    win = unique_flat[i:i+12]
    phrase = ' '.join(win)
    if v.IsValid(phrase):
        print("VALID unique sliding window:", phrase)
        seed = Bip39SeedGenerator(phrase).Generate()
        addr = Bip44.FromSeed(seed, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
        print("Addr:", addr)
        if addr == TARGET:
            print("MATCH!")
