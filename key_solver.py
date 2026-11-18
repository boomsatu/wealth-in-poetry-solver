"""
Try various key-based extraction methods:
1. Author ID as GPS key: 89cc82722605
2. URL hash as GPS key: d8eb43a02254
3. Numbers found in article as word positions
4. Acrostic methods (first letter of sentences/paragraphs)
5. First BIP-39 word of each paragraph
6. Last BIP-39 word of each paragraph
"""
import re
import hashlib
from itertools import combinations

# Load BIP-39 wordlist
with open('english.txt', 'r') as f:
    bip39_words = set(f.read().strip().split('\n'))

# Load article text
with open('text.txt', 'r') as f:
    lines = [l.strip() for l in f.readlines()]

# Build full text (all words, 1-indexed)
full_text = ' '.join(lines)
all_words_raw = full_text.split()
all_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in all_words_raw]

print(f"Total words in article: {len(all_words)}")

# Also build from just the article body (skip header lines 1-18)
body_lines = [l for l in lines[18:] if l.strip()]
body_text = ' '.join(body_lines)
body_words_raw = body_text.split()
body_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in body_words_raw]
print(f"Total body words: {len(body_words)}")

# BIP-39 validation
try:
    from bip_utils import (
        Bip39MnemonicValidator, Bip39SeedGenerator, Bip39MnemonicGenerator,
        Bip44, Bip44Coins, Bip44Changes
    )
    HAS_BIP = True
except ImportError:
    HAS_BIP = False
    print("WARNING: bip_utils not available")

TARGET = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"

def check_mnemonic(words_list, label=""):
    """Check if 12 words form a valid mnemonic and derive address"""
    phrase = ' '.join(words_list)
    # Check all words are BIP-39
    for w in words_list:
        if w not in bip39_words:
            return False
    if not HAS_BIP:
        return False
    try:
        Bip39MnemonicValidator(phrase).Validate()
    except:
        return False
    
    # Valid checksum! Try to derive address
    try:
        seed = Bip39SeedGenerator(phrase).Generate()
        # BIP44 m/44'/0'/0'/0/0
        bip44 = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
        addr = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
        if addr == TARGET:
            print(f"\n!!! MATCH FOUND !!! [{label}]")
            print(f"Phrase: {phrase}")
            print(f"Address: {addr}")
            return True
        # Also try account 0, no change
        for acct in range(3):
            for idx in range(5):
                for change in [Bip44Changes.CHAIN_EXT, Bip44Changes.CHAIN_INT]:
                    addr2 = bip44.Purpose().Coin().Account(acct).Change(change).AddressIndex(idx).PublicKey().ToAddress()
                    if addr2 == TARGET:
                        print(f"\n!!! MATCH FOUND !!! [{label}] acct={acct} change={change} idx={idx}")
                        print(f"Phrase: {phrase}")
                        return True
    except Exception as e:
        pass
    return False

# Also try with passphrase
def check_with_passphrases(words_list, label=""):
    phrase = ' '.join(words_list)
    for w in words_list:
        if w not in bip39_words:
            return False
    try:
        Bip39MnemonicValidator(phrase).Validate()
    except:
        return False
    
    passphrases = ["", "trithemius", "Trithemius", "bitcoin", "Bitcoin", "steganography", 
                   "poetry", "wealth", "revolution", "yuanbao", "yeye", "ye-ye",
                   "steganographia", "Steganographia", "M.7.7", "trithemian",
                   "Trithemian", "seed", "seeds", "null", "cipher"]
    
    for pp in passphrases:
        try:
            seed = Bip39SeedGenerator(phrase).Generate(pp)
            bip44 = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            addr = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
            if addr == TARGET:
                print(f"\n!!! MATCH FOUND !!! [{label}] passphrase='{pp}'")
                print(f"Phrase: {phrase}")
                return True
        except:
            pass
    return False

tested = 0
valid = 0

# ============================================================
# METHOD 1: GPS method with author ID digits: 89cc82722605
# Hex digits only: 8,9,8,2,7,2,2,6,0,5 -> only 10, need 12
# All chars: 8,9,c,c,8,2,7,2,2,6,0,5 -> c is not a digit
# Just the numeric digits: 8,9,8,2,7,2,2,6,0,5
# ============================================================
print("\n=== METHOD 1: Author ID / URL hash as GPS keys ===")

# GPS method: each digit d at position i (0-based) -> position = d + 10*i + 1
def gps_to_positions(digits):
    return [d + 10*i + 1 for i, d in enumerate(digits)]

# Try various digit sequences
digit_sequences = {
    "author_id_numeric": [8,9,8,2,7,2,2,6,0,5],  # only 10 digits
    "url_hash_d8eb43a02254": [8,4,3,0,2,2,5,4],  # only 8 hex digits
    "url_hash_numeric": [8,4,3,0,2,2,5,4],
    "pub_date_02112019": [0,2,1,1,2,0,1,9],
    "pub_date_11022019": [1,1,0,2,2,0,1,9],
    "pub_date_20190211": [2,0,1,9,0,2,1,1],
    # Full 12-digit sequences
    "author_full_hex": [8,9,12,12,8,2,7,2,2,6,0,5],  # c=12, treating as number
    "url_full_hex_d8eb43a02254": [13,8,14,11,4,3,10,0,2,2,5,4],  # d=13,e=14,b=11,a=10
    # What if we use ALL hex chars as their values?
    "author_hex_values": [8,9,0xc,0xc,8,2,7,2,2,6,0,5],
    "url_hex_values": [0xd,8,0xe,0xb,4,3,0xa,0,2,2,5,4],
}

# Also try: treat the hex string as pairs
# 89 cc 82 72 26 05 -> 89,204,130,114,38,5 (nah too big)
# d8 eb 43 a0 22 54 -> ...

# Also pure digit strings that are 12 digits
twelve_digit_keys = {
    "890882722605": [8,9,0,8,8,2,7,2,2,6,0,5],  # author removing c's
    "d8eb43a02254_digits_only": [8,4,3,0,2,2,5,4],  # only 8
    "publication_021120190211": [0,2,1,1,2,0,1,9,0,2,1,1],  # repeat
    "feb_11_2019_full": [0,2,1,1,2,0,1,9],
}

for name, digits in {**digit_sequences, **twelve_digit_keys}.items():
    if len(digits) < 12:
        # Can't get 12 positions, try with what we have
        positions = gps_to_positions(digits)
        # Also try without the +1
        positions_zero = [d + 10*i for i, d in enumerate(digits)]
    else:
        positions = gps_to_positions(digits[:12])
        positions_zero = [d + 10*i for i, d in enumerate(digits[:12])]
    
    for word_list, wl_name in [(all_words, "all"), (body_words, "body")]:
        for pos_list, pname in [(positions, "gps+1"), (positions_zero, "gps+0")]:
            if max(pos_list) >= len(word_list) or min(pos_list) < 0:
                continue
            extracted = [word_list[p] for p in pos_list]
            if all(w in bip39_words for w in extracted):
                tested += 1
                if check_mnemonic(extracted, f"{name}_{wl_name}_{pname}"):
                    print("SOLVED!")
                    exit()
                if check_with_passphrases(extracted, f"{name}_{wl_name}_{pname}_pp"):
                    print("SOLVED!")
                    exit()

print(f"  Tested: {tested} GPS key combinations")

# ============================================================
# METHOD 2: Acrostic - first letter of each sentence
# ============================================================
print("\n=== METHOD 2: Acrostic approaches ===")

# Split into sentences
sentences = re.split(r'[.!?]+', full_text)
sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

print(f"  Total sentences: {len(sentences)}")

# First letters of sentences
first_letters = ''.join(s[0].lower() for s in sentences if s)
print(f"  First letters: {first_letters}")

# Check if first letters spell out BIP-39 words
# Try grouping letters into words
# This is complex, skip for now

# First WORD of each sentence
first_words = []
for s in sentences:
    words = s.split()
    if words:
        w = re.sub(r'[^a-zA-Z]', '', words[0]).lower()
        if w:
            first_words.append(w)

print(f"  First words of sentences (BIP-39): {[w for w in first_words if w in bip39_words]}")

# First BIP-39 word of each sentence
first_bip_per_sentence = []
for s in sentences:
    words = s.split()
    for w in words:
        clean = re.sub(r'[^a-zA-Z]', '', w).lower()
        if clean in bip39_words:
            first_bip_per_sentence.append(clean)
            break

print(f"  First BIP-39 per sentence ({len(first_bip_per_sentence)}): {first_bip_per_sentence[:20]}...")

# Try sliding windows of 12 from first_bip_per_sentence
for i in range(len(first_bip_per_sentence) - 11):
    window = first_bip_per_sentence[i:i+12]
    tested += 1
    if check_mnemonic(window, f"first_bip_sentence_w{i}"):
        print("SOLVED!")
        exit()

# ============================================================
# METHOD 3: Numbers in the article as word positions
# ============================================================
print("\n=== METHOD 3: Numbers in article as positions ===")

# Find all numbers in the text
numbers = re.findall(r'\b\d+\b', full_text)
print(f"  Numbers found: {numbers}")

# Try using specific number sequences as positions
# Key numbers: 2000, 1920, 1930, 40, 40, 10, 18, 5, 50, 300, 03
# Article mentions: 2000, 1920s, 1930s, 40, 40, 10, 18, 5, 50, 221, 206, 300
# Small numbers that could be positions: 40, 40, 10, 18, 5, 50
small_nums = [int(n) for n in numbers if 1 <= int(n) <= 2500]
print(f"  Small numbers (1-2500): {small_nums}")

# ============================================================  
# METHOD 4: First/Last BIP-39 word per SECTION
# ============================================================
print("\n=== METHOD 4: Section-based extraction ===")

# Define sections by their headers in text.txt
section_headers = ["Revolution", "Fiat", "Bitcoin", "Touchpoints", "Steganography", "Trithemian Seeds"]
section_texts = []
current_section = ""
current_text = []

for line in lines:
    if line.strip() in section_headers:
        if current_text:
            section_texts.append((current_section, ' '.join(current_text)))
        current_section = line.strip()
        current_text = []
    else:
        current_text.append(line)
if current_text:
    section_texts.append((current_section, ' '.join(current_text)))

for name, text in section_texts:
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in text.split()]
    bip = [w for w in words if w in bip39_words]
    print(f"  {name}: {len(bip)} BIP-39 words, first={bip[:3] if bip else 'none'}, last={bip[-3:] if bip else 'none'}")

# Try: 2 BIP-39 words per section (first 2)
method_results = {}
for n_per_section in [1, 2, 3]:
    combo = []
    for name, text in section_texts:
        if not name:
            continue
        words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in text.split()]
        bip = list(dict.fromkeys(w for w in words if w in bip39_words))  # unique, ordered
        combo.extend(bip[:n_per_section])
    
    if len(combo) >= 12:
        tested += 1
        if check_mnemonic(combo[:12], f"first_{n_per_section}_per_section"):
            print("SOLVED!")
            exit()
        # Also try last N per section
    
    combo_last = []
    for name, text in section_texts:
        if not name:
            continue
        words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in text.split()]
        bip = list(dict.fromkeys(w for w in words if w in bip39_words))
        combo_last.extend(bip[-n_per_section:])
    
    if len(combo_last) >= 12:
        tested += 1
        if check_mnemonic(combo_last[:12], f"last_{n_per_section}_per_section"):
            print("SOLVED!")
            exit()

# ============================================================
# METHOD 5: Paragraph-based extraction with line numbers
# ============================================================
print("\n=== METHOD 5: Paragraph-level extractions ===")

# Non-empty lines (paragraphs)
paragraphs = [l for l in lines if l.strip() and len(l.strip()) > 20]
print(f"  Paragraphs with >20 chars: {len(paragraphs)}")

# First BIP-39 word of each paragraph
first_bip_para = []
for p in paragraphs:
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in p.split()]
    for w in words:
        if w in bip39_words:
            first_bip_para.append(w)
            break

print(f"  First BIP-39 per paragraph ({len(first_bip_para)}): {first_bip_para}")

# Windows of 12
for i in range(len(first_bip_para) - 11):
    window = first_bip_para[i:i+12]
    tested += 1
    if check_mnemonic(window, f"first_bip_para_w{i}"):
        print("SOLVED!")
        exit()

# Last BIP-39 word of each paragraph
last_bip_para = []
for p in paragraphs:
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in p.split()]
    bip = [w for w in words if w in bip39_words]
    if bip:
        last_bip_para.append(bip[-1])

print(f"  Last BIP-39 per paragraph ({len(last_bip_para)}): {last_bip_para}")

for i in range(len(last_bip_para) - 11):
    window = last_bip_para[i:i+12]
    tested += 1
    if check_mnemonic(window, f"last_bip_para_w{i}"):
        print("SOLVED!")
        exit()

# ============================================================
# METHOD 6: Every Nth BIP-39 word (broader range)
# ============================================================
print("\n=== METHOD 6: Every Nth BIP-39 word ===")

# Get all BIP-39 words in order from body
body_bip39 = []
for w in body_words:
    if w in bip39_words:
        body_bip39.append(w)

print(f"  Total BIP-39 in body: {len(body_bip39)}")

# Try every Nth (N from 2 to 60), all starting positions
for N in range(2, 61):
    for start in range(N):
        selected = body_bip39[start::N]
        if len(selected) >= 12:
            tested += 1
            if check_mnemonic(selected[:12], f"every_{N}th_start{start}"):
                print("SOLVED!")
                exit()

# ============================================================
# METHOD 7: Word index from line 118 (the puzzle paragraph)
# ============================================================
print("\n=== METHOD 7: Puzzle paragraph analysis ===")

# Line 118: "It can be easy to overlook the point of bitcoin living in a country where people trust their government..."
puzzle_line = lines[117]  # 0-indexed
print(f"  Line 118: {puzzle_line[:100]}...")
p_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in puzzle_line.split()]
p_bip = [(i, w) for i, w in enumerate(p_words) if w in bip39_words]
print(f"  BIP-39 words in line 118: {p_bip}")

# Try the 12 BIP-39 words from this line
bip_only = [w for _, w in p_bip]
if len(bip_only) >= 12:
    tested += 1
    check_mnemonic(bip_only[:12], "line118_bip39")

# ============================================================
# METHOD 8: Specific word positions from key clues
# ============================================================
print("\n=== METHOD 8: Specific position patterns ===")

# The M.7.7 reference - Steganographia book reference
# Every 7th word, every 7th BIP-39 word
for start in range(7):
    selected = body_bip39[start::7]
    if len(selected) >= 12:
        tested += 1
        if check_mnemonic(selected[:12], f"every_7th_bip_start{start}"):
            print("SOLVED!")
            exit()

# 300 years banned - try every 300th character position?
# "Born 1930" - various number combos

# Try Fibonacci positions: 1,1,2,3,5,8,13,21,34,55,89,144
fib = [1,1,2,3,5,8,13,21,34,55,89,144]
for word_list, wl_name in [(body_words, "body"), (all_words, "all"), (body_bip39, "body_bip")]:
    extracted = []
    valid_fib = True
    for pos in fib:
        if pos < len(word_list):
            extracted.append(word_list[pos])
        else:
            valid_fib = False
            break
    if valid_fib and all(w in bip39_words for w in extracted):
        tested += 1
        if check_mnemonic(extracted, f"fibonacci_{wl_name}"):
            print("SOLVED!")
            exit()

# Prime number positions: 2,3,5,7,11,13,17,19,23,29,31,37
primes = [2,3,5,7,11,13,17,19,23,29,31,37]
for word_list, wl_name in [(body_words, "body"), (all_words, "all"), (body_bip39, "body_bip")]:
    extracted = []
    valid_p = True
    for pos in primes:
        if pos < len(word_list):
            extracted.append(word_list[pos])
        else:
            valid_p = False
            break
    if valid_p and all(w in bip39_words for w in extracted):
        tested += 1
        if check_mnemonic(extracted, f"primes_{wl_name}"):
            print("SOLVED!")
            exit()

print(f"\n=== TOTAL TESTED: {tested}, no match found ===")
