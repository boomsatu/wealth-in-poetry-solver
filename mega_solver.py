"""
MEGA SOLVER for Wealth in Poetry puzzle.

Strategy:
1. Apply Example 1 indices (2,6,9,18,22,25,45,70,86,100,113,116) to every paragraph
2. Apply Example 2 indices (3,18,28,39,40,56,67,77,80,90,104,114) to every paragraph  
3. Apply various GPS coordinates with +10/digit rule to the FULL article text
4. Try every Nth BIP-39 word from the full article
5. Try first BIP-39 word per section/paragraph
6. Try applying indices to ONLY the BIP-39 words (filtered list)
"""

import re
import time
from bip_utils import (
    Bip39MnemonicValidator, Bip39SeedGenerator, 
    Bip44, Bip44Coins, Bip44Changes,
    Bip49, Bip49Coins,  # P2SH-P2WPKH (3xxx addresses)
    Bip84, Bip84Coins,  # Bech32 (bc1 addresses)
)

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
validator = Bip39MnemonicValidator()

with open('english.txt') as f:
    bip39_set = set(line.strip() for line in f)

with open('text.txt', encoding='utf-8') as f:
    text_txt = f.read()

# Full article from clean_article.txt
with open('clean_article.txt', encoding='utf-8') as f:
    clean_text = f.read()

def get_words(text):
    return [re.sub(r'[^a-zA-Z]', '', w).lower() for w in text.split() if re.sub(r'[^a-zA-Z]', '', w)]

def check_phrase(phrase, label=""):
    """Check if phrase is valid BIP-39 and derives to target address."""
    if not validator.IsValid(phrase):
        return False
    try:
        seed = Bip39SeedGenerator(phrase).Generate()
        # BIP-44 (P2PKH - 1xxx addresses)
        mst44 = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
        for acc in range(3):
            for i in range(5):
                addr = mst44.Purpose().Coin().Account(acc).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
                if addr == target:
                    print(f"\n{'='*60}")
                    print(f"🎯🎯🎯 TARGET FOUND! [{label}] 🎯🎯🎯")
                    print(f"Mnemonic: {phrase}")
                    print(f"Path: m/44'/0'/{acc}'/0/{i}")
                    print(f"Address: {addr}")
                    print(f"{'='*60}")
                    return True
        # Also try BIP-44 account 0, change addresses
        for i in range(5):
            addr = mst44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_INT).AddressIndex(i).PublicKey().ToAddress()
            if addr == target:
                print(f"\n🎯 TARGET FOUND (change addr)! [{label}]: {phrase}")
                return True
    except Exception:
        pass
    return False

def gps_indices(digits):
    """Convert 12 GPS digits to word positions using +10/digit rule."""
    return [digits[i] + i * 10 for i in range(12)]

paragraphs = [p.strip() for p in text_txt.split('\n\n') if p.strip()]
all_words_text = get_words(text_txt)
all_words_clean = get_words(clean_text)

print(f"Total words in text.txt: {len(all_words_text)}")
print(f"Total words in clean_article.txt: {len(all_words_clean)}")
print(f"Total paragraphs: {len(paragraphs)}")

t0 = time.time()
tested = 0
valid_count = 0

# ============================================================
# STRATEGY 1: Apply Example indices to every paragraph
# ============================================================
print("\n--- STRATEGY 1: Example indices on each paragraph ---")
ex1_indices = [2, 6, 9, 18, 22, 25, 45, 70, 86, 100, 113, 116]
ex2_indices = [3, 18, 28, 39, 40, 56, 67, 77, 80, 90, 104, 114]

for p_idx, p in enumerate(paragraphs):
    words = get_words(p)
    for name, indices in [("Ex1", ex1_indices), ("Ex2", ex2_indices)]:
        max_idx = max(indices)
        if len(words) >= max_idx:
            # 1-based
            phrase_words = [words[i-1] for i in indices]
            if all(w in bip39_set for w in phrase_words):
                phrase = " ".join(phrase_words)
                tested += 1
                if validator.IsValid(phrase):
                    valid_count += 1
                    if check_phrase(phrase, f"S1-{name}-P{p_idx}"):
                        exit()

# ============================================================
# STRATEGY 2: GPS coordinates on FULL article text
# ============================================================
print("\n--- STRATEGY 2: GPS coordinates on full article ---")

# All candidate GPS coordinate digit sequences (12 digits each)
gps_candidates = {
    # Qingdao: 36.0669 N, 120.3827 E
    "Qingdao_1": [3,6,0,6,6,9,1,2,0,3,8,2],
    "Qingdao_2": [3,6,0,6,7,0,1,2,0,3,8,3],
    # Jesus College Oxford: 51.7534 N, 1.2569 W
    "JesusCollege_1": [5,1,7,5,3,4,0,1,2,5,6,9],
    "JesusCollege_2": [5,1,7,5,3,4,1,2,5,6,9,0],
    # Mount Vernon: 38.7080 N, 77.0861 W
    "MtVernon_1": [3,8,7,0,8,0,7,7,0,8,6,1],
    "MtVernon_2": [3,8,7,3,5,3,7,7,0,9,5,3],
    # Frankfurt: 50.1109 N, 8.6821 E
    "Frankfurt_1": [5,0,1,1,0,9,0,8,6,8,2,1],
    "Frankfurt_2": [5,0,1,1,0,9,8,6,8,2,1,0],
    # Trittenheim: 49.8247 N, 6.8994 E
    "Trittenheim_1": [4,9,8,2,4,7,0,6,8,9,9,4],
    "Trittenheim_2": [4,9,8,2,4,7,6,8,9,9,4,0],
    # Sponheim Abbey: 49.8456 N, 7.7289 E
    "Sponheim_1": [4,9,8,4,5,6,0,7,7,2,8,9],
    "Sponheim_2": [4,9,8,4,5,6,7,7,2,8,9,0],
    # Würzburg (Trithemius died): 49.7913 N, 9.9534 E
    "Wurzburg_1": [4,9,7,9,1,3,0,9,9,5,3,4],
    "Wurzburg_2": [4,9,7,9,1,3,9,9,5,3,4,0],
    # Taiwan (mentioned in story): 25.0330 N, 121.5654 E
    "Taiwan_1": [2,5,0,3,3,0,1,2,1,5,6,5],
    # Beijing: 39.9042 N, 116.4074 E
    "Beijing_1": [3,9,9,0,4,2,1,1,6,4,0,7],
    # Unsplash photo: 5_bAKRGvkq8 → not GPS
    # Medium article hash: d8eb43a02254
    "MediumHash": [8,8,4,3,0,2,2,5,4,0,0,0],  # d=13→? just digits
    # U.S. Supreme Court (from example): 38.8906 N, 77.0044 W
    "USSupreme": [3,8,8,9,0,6,7,7,0,0,4,4],
    # Barth Bailey photo coordinates? Let's try flock of birds coordinates
    # Vatican: 41.9029 N, 12.4534 E
    "Vatican_1": [4,1,9,0,2,9,1,2,4,5,3,4],
    # Let's also try reversed coordinate order (lon, lat)
    "Qingdao_rev": [1,2,0,3,8,2,3,6,0,6,6,9],
    "JesusCollege_rev": [0,1,2,5,6,9,5,1,7,5,3,4],
    "MtVernon_rev": [7,7,0,8,6,1,3,8,7,0,8,0],
    # Historical: 1606 Steganographia → 1,6,0,6,...?
    # M.7.7 Gall → 7,7?
    # 1930s, 2000, 1920s → article numbers
    # 221 to 206 BC: 2,2,1,2,0,6
    "Steganographia_1606": [1,6,0,6,0,0,0,0,0,0,0,0],
    # Feb 11, 2019 → 02112019 or 11022019
    "PubDate_1": [0,2,1,1,2,0,1,9,0,0,0,0],
    "PubDate_2": [1,1,0,2,2,0,1,9,0,0,0,0],
}

for text_name, word_list in [("text_txt", all_words_text), ("clean_article", all_words_clean)]:
    for gps_name, digits in gps_candidates.items():
        indices = gps_indices(digits)
        # Both 0-based and 1-based
        for base_name, offset in [("0base", 0), ("1base", -1)]:
            real_indices = [idx + offset for idx in indices]
            if any(ri < 0 or ri >= len(word_list) for ri in real_indices):
                continue
            phrase_words = [word_list[ri] for ri in real_indices]
            if all(w in bip39_set for w in phrase_words):
                phrase = " ".join(phrase_words)
                tested += 1
                label = f"S2-{text_name}-{gps_name}-{base_name}"
                if validator.IsValid(phrase):
                    valid_count += 1
                    print(f"  VALID CHECKSUM [{label}]: {phrase}")
                    if check_phrase(phrase, label):
                        exit()

# Also try GPS on each paragraph
for p_idx, p in enumerate(paragraphs):
    words = get_words(p)
    if len(words) < 115:
        continue
    for gps_name, digits in gps_candidates.items():
        indices = gps_indices(digits)
        for base_name, offset in [("0base", 0), ("1base", -1)]:
            real_indices = [idx + offset for idx in indices]
            if any(ri < 0 or ri >= len(words) for ri in real_indices):
                continue
            phrase_words = [words[ri] for ri in real_indices]
            if all(w in bip39_set for w in phrase_words):
                phrase = " ".join(phrase_words)
                tested += 1
                label = f"S2-P{p_idx}-{gps_name}-{base_name}"
                if validator.IsValid(phrase):
                    valid_count += 1
                    print(f"  VALID CHECKSUM [{label}]: {phrase}")
                    if check_phrase(phrase, label):
                        exit()

# ============================================================
# STRATEGY 3: Every Nth BIP-39 word from the full text
# ============================================================
print("\n--- STRATEGY 3: Every Nth BIP-39 word ---")

# Get all BIP-39 words in order from the full text
all_bip39_in_text = [w for w in all_words_text if w in bip39_set]
all_bip39_in_clean = [w for w in all_words_clean if w in bip39_set]

for text_name, bip_list in [("text_txt", all_bip39_in_text), ("clean_article", all_bip39_in_clean)]:
    print(f"  {text_name}: {len(bip_list)} BIP-39 words")
    # Try every Nth word (N=2..50)
    for n in range(2, 51):
        for start in range(n):
            selected = bip_list[start::n]
            if len(selected) >= 12:
                phrase = " ".join(selected[:12])
                tested += 1
                if validator.IsValid(phrase):
                    valid_count += 1
                    label = f"S3-{text_name}-every{n}-start{start}"
                    print(f"  VALID CHECKSUM [{label}]: {phrase}")
                    if check_phrase(phrase, label):
                        exit()

# ============================================================
# STRATEGY 4: First/Last BIP-39 word per paragraph
# ============================================================
print("\n--- STRATEGY 4: First/Last BIP-39 word per paragraph ---")

first_bip_per_p = []
last_bip_per_p = []
for p in paragraphs:
    words = get_words(p)
    bip_in_p = [w for w in words if w in bip39_set]
    if bip_in_p:
        first_bip_per_p.append(bip_in_p[0])
        last_bip_per_p.append(bip_in_p[-1])

print(f"  First BIP-39 per paragraph: {len(first_bip_per_p)} words")
print(f"  Last BIP-39 per paragraph: {len(last_bip_per_p)} words")

# sliding window of 12 on first/last lists
for name, lst in [("first", first_bip_per_p), ("last", last_bip_per_p)]:
    for i in range(len(lst) - 11):
        phrase = " ".join(lst[i:i+12])
        tested += 1
        if validator.IsValid(phrase):
            valid_count += 1
            label = f"S4-{name}-start{i}"
            print(f"  VALID CHECKSUM [{label}]: {phrase}")
            if check_phrase(phrase, label):
                exit()

# ============================================================
# STRATEGY 5: Apply Example indices to FILTERED BIP-39 word list
# ============================================================
print("\n--- STRATEGY 5: Example indices on filtered BIP-39 list ---")

for text_name, bip_list in [("text_txt", all_bip39_in_text), ("clean_article", all_bip39_in_clean)]:
    for name, indices in [("Ex1", ex1_indices), ("Ex2", ex2_indices)]:
        max_idx = max(indices)
        if len(bip_list) >= max_idx:
            # 1-based
            phrase_words = [bip_list[i-1] for i in indices]
            phrase = " ".join(phrase_words)
            tested += 1
            if validator.IsValid(phrase):
                valid_count += 1
                label = f"S5-{text_name}-{name}"
                print(f"  VALID CHECKSUM [{label}]: {phrase}")
                if check_phrase(phrase, label):
                    exit()

# ============================================================
# STRATEGY 6: Use only unique BIP-39 words (appearing once) 
# ============================================================
print("\n--- STRATEGY 6: Unique BIP-39 words sliding window ---")

from collections import Counter
word_counts = Counter(w for w in all_words_text if w in bip39_set)
unique_bip39 = [w for w in all_words_text if w in bip39_set and word_counts[w] == 1]
print(f"  Unique BIP-39 words (appear once): {len(unique_bip39)}")

for i in range(len(unique_bip39) - 11):
    phrase = " ".join(unique_bip39[i:i+12])
    tested += 1
    if validator.IsValid(phrase):
        valid_count += 1
        label = f"S6-unique-start{i}"
        print(f"  VALID CHECKSUM [{label}]: {phrase}")
        if check_phrase(phrase, label):
            exit()

# ============================================================
# STRATEGY 7: Sections with exactly 12 BIP-39 words
# ============================================================
print("\n--- STRATEGY 7: Paragraphs with exactly 12 BIP-39 words ---")

for p_idx, p in enumerate(paragraphs):
    words = get_words(p)
    bip_in_p = [w for w in words if w in bip39_set]
    if len(bip_in_p) == 12:
        phrase = " ".join(bip_in_p)
        tested += 1
        label = f"S7-P{p_idx}-exact12"
        if validator.IsValid(phrase):
            valid_count += 1
            print(f"  VALID CHECKSUM [{label}]: {phrase}")
            if check_phrase(phrase, label):
                exit()
        # Also try reversed
        phrase_r = " ".join(reversed(bip_in_p))
        tested += 1
        if validator.IsValid(phrase_r):
            valid_count += 1
            print(f"  VALID CHECKSUM [{label}-rev]: {phrase_r}")
            if check_phrase(phrase_r, f"{label}-rev"):
                exit()

t1 = time.time()
print(f"\n{'='*60}")
print(f"MEGA SOLVER completed in {t1-t0:.2f}s")
print(f"Tested: {tested}, Valid checksums: {valid_count}")
print(f"Target NOT found.")
print(f"{'='*60}")
