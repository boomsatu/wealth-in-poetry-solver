"""
MEGA SOLVER PHASE 3 - Exhaustive BIP-39 sliding window on FULL article
with multiple derivation paths and passphrases.

The HomelessPhD script only tested:
- BIP-44 m/44'/0'/0'/0/0 (standard)
- No passphrase

We need to also test:
- BIP-44 with passphrase variations
- Direct key derivation (non-BIP-44)
- BIP-32 root key
- Simple SHA256(mnemonic) brainwallet
"""

import re
import time
import hashlib
import codecs
import ecdsa
import base58
from bip_utils import (
    Bip39MnemonicValidator, Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes,
)

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
target_hash160 = "c6233aeb3a50a70b82fcd88d69b5f1a3ec6e355a"
validator = Bip39MnemonicValidator()

with open('english.txt') as f:
    bip39_set = set(line.strip() for line in f)

with open('text.txt', encoding='utf-8') as f:
    text_txt = f.read()

def get_words(text):
    return [re.sub(r'[^a-zA-Z]', '', w).lower() for w in text.split() if re.sub(r'[^a-zA-Z]', '', w)]

def privkey_to_p2pkh_compressed(priv_hex):
    """Private key hex -> compressed P2PKH address."""
    pk_bytes = bytes.fromhex(priv_hex)
    key = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1).verifying_key
    kb = key.to_string()
    prefix = b'\x03' if kb[-1] & 1 else b'\x02'
    pub = prefix + kb[:32]
    sha = hashlib.sha256(pub).digest()
    rip = hashlib.new('ripemd160', sha).digest()
    ver = b'\x00' + rip
    cs = hashlib.sha256(hashlib.sha256(ver).digest()).digest()[:4]
    return base58.b58encode(ver + cs).decode()

def privkey_to_p2pkh_uncompressed(priv_hex):
    """Private key hex -> uncompressed P2PKH address."""
    pk_bytes = bytes.fromhex(priv_hex)
    key = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1).verifying_key
    kb = key.to_string()
    pub = b'\x04' + kb
    sha = hashlib.sha256(pub).digest()
    rip = hashlib.new('ripemd160', sha).digest()
    ver = b'\x00' + rip
    cs = hashlib.sha256(hashlib.sha256(ver).digest()).digest()[:4]
    return base58.b58encode(ver + cs).decode()

all_words = get_words(text_txt)
bip39_filtered = [w for w in all_words if w in bip39_set]

t0 = time.time()
tested = 0
found = False

print(f"BIP-39 words in text: {len(bip39_filtered)}")
print(f"Testing sliding window with extended derivation...")

passphrases = ["", "Trithemius", "trithemius", "Revolution", "revolution",
               "Steganographia", "steganographia", "poetry", "wealth"]

for i in range(len(bip39_filtered) - 11):
    phrase = " ".join(bip39_filtered[i:i+12])
    if not validator.IsValid(phrase):
        continue
    
    tested += 1
    
    for pp in passphrases:
        try:
            seed = Bip39SeedGenerator(phrase).Generate(pp)
            mst = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            
            # Test multiple accounts and address indices
            for acc in range(2):
                for chg in [Bip44Changes.CHAIN_EXT, Bip44Changes.CHAIN_INT]:
                    for idx in range(5):
                        addr = mst.Purpose().Coin().Account(acc).Change(chg).AddressIndex(idx).PublicKey().ToAddress()
                        if addr == target:
                            print(f"\nFOUND! pp='{pp}' path=m/44'/0'/{acc}'/{chg.value}/{idx}")
                            print(f"Mnemonic: {phrase}")
                            found = True
                            break
                    if found: break
                if found: break
            if found: break
            
            # Also try direct SHA256 of the mnemonic as private key
            pk = hashlib.sha256(phrase.encode()).hexdigest()
            addr_c = privkey_to_p2pkh_compressed(pk)
            addr_u = privkey_to_p2pkh_uncompressed(pk)
            if addr_c == target or addr_u == target:
                print(f"\nFOUND via SHA256 brainwallet! Mnemonic: {phrase}")
                found = True
                break
                
        except Exception:
            pass
    
    if found:
        break
    
    if tested % 500 == 0:
        print(f"  Progress: {tested} valid phrases tested, window pos {i}/{len(bip39_filtered)-11}...")

t1 = time.time()
print(f"\nCompleted in {t1-t0:.2f}s. Valid phrases tested: {tested}. Found: {found}")

# ============================================================
# STRATEGY 16: Full article word positions with ALL possible 
# 12-digit number sequences from text numbers
# ============================================================
print("\n--- STRATEGY 16: Number sequences from article ---")

# Key numbers in the article:
# 1930, 2000, 1920, 6, 40, 40, 10, 221, 206, 50, 300, 7.7, 1606
# Try using these as direct word positions (1-indexed)

num_combos = [
    # 6 siblings, 40 bags, 40 lbs, 10 taels, 5 taels, 2 sides, 50 years
    [6, 40, 10, 5, 2, 50, 18, 221, 206, 300, 39, 1],
    # Story-relevant small numbers only
    [6, 5, 10, 18, 2, 40, 50, 221, 206, 300, 39, 1],
    # M.7.7 → take word 7, then word 7 again?
]

# Try these as 1-indexed positions
for nums in num_combos:
    if all(0 < n <= len(all_words) for n in nums):
        ws = [all_words[n-1] for n in nums]
        if all(w in bip39_set for w in ws):
            phrase = " ".join(ws)
            print(f"  All BIP39! {nums} -> {phrase}")
            if validator.IsValid(phrase):
                print(f"  VALID CHECKSUM!")
