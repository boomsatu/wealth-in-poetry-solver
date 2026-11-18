"""
MEGA SOLVER PHASE 2 - More advanced approaches

The article text uses TWO types of encoding demonstrated:
1. Phone number → word positions (direct encoding)  
2. GPS coordinate → word positions (+10 per digit)

For the actual puzzle, the "key" must be WITHIN the article.
Let's try more creative approaches.
"""

import re
import time
import hashlib
from bip_utils import (
    Bip39MnemonicValidator, Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes,
)

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
validator = Bip39MnemonicValidator()

with open('english.txt') as f:
    bip39_set = set(line.strip() for line in f)

with open('text.txt', encoding='utf-8') as f:
    text_txt = f.read()
with open('clean_article.txt', encoding='utf-8') as f:
    clean_text = f.read()

def get_words(text):
    return [re.sub(r'[^a-zA-Z]', '', w).lower() for w in text.split() if re.sub(r'[^a-zA-Z]', '', w)]

def check_phrase(phrase, label=""):
    if not validator.IsValid(phrase):
        return False
    try:
        seed = Bip39SeedGenerator(phrase).Generate()
        mst44 = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
        for acc in range(3):
            for chg in [Bip44Changes.CHAIN_EXT, Bip44Changes.CHAIN_INT]:
                for i in range(5):
                    addr = mst44.Purpose().Coin().Account(acc).Change(chg).AddressIndex(i).PublicKey().ToAddress()
                    if addr == target:
                        print(f"\n{'='*60}")
                        print(f"TARGET FOUND! [{label}]")
                        print(f"Mnemonic: {phrase}")
                        print(f"Address: {addr}")
                        print(f"{'='*60}")
                        return True
    except:
        pass
    return False

all_words = get_words(text_txt)
all_words_clean = get_words(clean_text)
bip39_words_text = [(i, w) for i, w in enumerate(all_words) if w in bip39_set]
bip39_words_clean = [(i, w) for i, w in enumerate(all_words_clean) if w in bip39_set]

t0 = time.time()
tested = 0
valid_count = 0

# ============================================================
# STRATEGY 8: Steganographia Book I rule - every other word
# Then take every other letter of the concatenation
# ============================================================
print("--- STRATEGY 8: Steganographia Book I technique ---")

# The article describes: "ignore first and last word, take every other word,
# then take every other letter"
# Let's try variations on each paragraph

for p_idx, p in enumerate([text_txt]):
    words = get_words(p)
    # Try: every other word (odd positions), then every other word (even positions)
    for start in [0, 1]:
        every_other = words[start::2]
        # Concatenate and take every other letter
        concat = "".join(every_other)
        for letter_start in [0, 1]:
            hidden = concat[letter_start::2]
            # Check if hidden text contains 12 BIP-39 words separated somehow
            hidden_words = re.findall(r'[a-z]+', hidden)
            bip_in_hidden = [w for w in hidden_words if w in bip39_set and len(w) >= 3]
            if len(bip_in_hidden) >= 12:
                phrase = " ".join(bip_in_hidden[:12])
                tested += 1
                if validator.IsValid(phrase):
                    valid_count += 1
                    print(f"  VALID [{start},{letter_start}]: {phrase}")
                    check_phrase(phrase, f"S8-everyother-{start}-{letter_start}")

# ============================================================
# STRATEGY 9: Brainwallet - SHA256 of text sections
# ============================================================
print("\n--- STRATEGY 9: Brainwallet (SHA256 of text) ---")

import codecs
import ecdsa
import base58

def sha256_to_p2pkh(text_input):
    """Convert text to brainwallet P2PKH address."""
    pk_bytes = hashlib.sha256(text_input.encode('utf-8')).digest()
    pk_hex = pk_bytes.hex()
    
    # Get public key (compressed)
    key = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1).verifying_key
    key_bytes = key.to_string()
    if key_bytes[-1] & 1:
        pub_prefix = b'\x03'
    else:
        pub_prefix = b'\x02'
    pub_key = pub_prefix + key_bytes[:32]
    
    # SHA256 + RIPEMD160
    sha = hashlib.sha256(pub_key).digest()
    ripemd = hashlib.new('ripemd160', sha).digest()
    
    # Add network byte and checksum
    versioned = b'\x00' + ripemd
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    address = base58.b58encode(versioned + checksum).decode()
    return address

brainwallet_inputs = [
    "Securing Wealth in Poetry",
    "securing wealth in poetry",
    "Revolution",
    "revolution",
    "Trithemius",
    "trithemius",
    "Steganographia",
    "steganographia",
    "trithemian seed",
    "Trithemian Seed",
    "wealth in poetry",
    "Wealth in Poetry",
    "The beauty of trithemian seeds is that they hide in plain sight.",
    "ye-ye",
    "yeye",
    "yuanbao",
    "Qingdao",
    "qingdao",
    text_txt.strip(),
    "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo",
]

for inp in brainwallet_inputs:
    addr = sha256_to_p2pkh(inp)
    if addr == target:
        print(f"  BRAINWALLET MATCH: '{inp[:50]}...'")
    tested += 1

# ============================================================
# STRATEGY 10: Article section headers as keys
# The article has sections: Revolution, Fiat, Bitcoin, Touchpoints,
# Steganography, Trithemian Seeds
# ============================================================
print("\n--- STRATEGY 10: Section-based extraction ---")

sections = {
    "Revolution": (text_txt.find("Revolution"), text_txt.find("Fiat")),
    "Fiat": (text_txt.find("Fiat"), text_txt.find("Bitcoin")),
    "Bitcoin": (text_txt.find("Bitcoin\n"), text_txt.find("Touchpoints")),
    "Touchpoints": (text_txt.find("Touchpoints"), text_txt.find("Steganography")),
    "Steganography": (text_txt.find("Steganography\n"), text_txt.find("Trithemian Seeds")),
    "TrithemianSeeds": (text_txt.find("Trithemian Seeds"), len(text_txt)),
}

for sec_name, (s, e) in sections.items():
    if s < 0:
        continue
    sec_text = text_txt[s:e]
    sec_words = get_words(sec_text)
    sec_bip = [w for w in sec_words if w in bip39_set]
    
    # Try: first 12 BIP-39 words of each section
    if len(sec_bip) >= 12:
        phrase = " ".join(sec_bip[:12])
        tested += 1
        if validator.IsValid(phrase):
            valid_count += 1
            print(f"  VALID first12 [{sec_name}]: {phrase}")
            check_phrase(phrase, f"S10-first12-{sec_name}")
        
        # Last 12
        phrase = " ".join(sec_bip[-12:])
        tested += 1
        if validator.IsValid(phrase):
            valid_count += 1
            print(f"  VALID last12 [{sec_name}]: {phrase}")
            check_phrase(phrase, f"S10-last12-{sec_name}")

# ============================================================
# STRATEGY 11: ALL BIP-39 words sliding window (HomelessPhD approach)
# but check MORE derivation paths + passphrase variations
# ============================================================
print("\n--- STRATEGY 11: Sliding window on BIP-39 list with extended path check ---")

bip_only = [w for _, w in bip39_words_text]
# This was already done by HomelessPhD. Skip if too slow.
# But let's try with passphrase "Trithemius" or other passphrases
passphrases = ["", "Trithemius", "trithemius", "Revolution", "revolution", 
               "Steganographia", "steganographia", "ye-ye", "yuanbao",
               "wealth", "poetry"]

for pp in passphrases[1:]:  # Skip "" as it was already tested
    for i in range(min(50, len(bip_only) - 11)):  # Test first 50 windows as sample
        phrase = " ".join(bip_only[i:i+12])
        tested += 1
        if validator.IsValid(phrase):
            try:
                seed = Bip39SeedGenerator(phrase).Generate(pp)
                mst = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
                for ai in range(3):
                    addr = mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(ai).PublicKey().ToAddress()
                    if addr == target:
                        print(f"  MATCH with passphrase '{pp}': {phrase}")
            except:
                pass

# ============================================================
# STRATEGY 12: Words at positions matching numbers in the text
# Numbers found: 1930, 2000, 1920, 40, 40, 10, 221, 206, 50, 300, etc
# ============================================================
print("\n--- STRATEGY 12: Article numbers as word positions ---")

# Numbers that appear in the narrative (not examples)
article_numbers = [
    # From the narrative
    [1930, 2000, 1920, 40, 40, 10, 221, 206, 50, 2018, 39, 300],
    # Subset of small numbers
    [40, 40, 10, 50, 39, 300, 221, 206, 6, 5, 2, 18],
    # Year digits
    [1, 9, 3, 0, 2, 0, 0, 0, 1, 9, 2, 0],
    # Various small numbers from the story  
    [6, 5, 10, 18, 40, 50, 39, 2, 1, 3, 2, 4],
]

for num_set in article_numbers:
    # Only try if all within bounds
    for word_list in [all_words, all_words_clean]:
        if all(0 < n <= len(word_list) for n in num_set):
            phrase_words = [word_list[n-1] for n in num_set]
            if all(w in bip39_set for w in phrase_words):
                phrase = " ".join(phrase_words)
                tested += 1
                if validator.IsValid(phrase):
                    valid_count += 1
                    print(f"  VALID: {phrase}")
                    check_phrase(phrase, f"S12-numbers")

# ============================================================
# STRATEGY 13: M.7.7 Gall. reference → take every 7th word? 
# Or 7.7 as a key?
# ============================================================
print("\n--- STRATEGY 13: M.7.7 pattern ---")

for word_list_name, word_list in [("text", all_words), ("clean", all_words_clean)]:
    # Every 7th word
    for start in range(7):
        selected = word_list[start::7]
        bip_sel = [w for w in selected if w in bip39_set]
        if len(bip_sel) >= 12:
            for i in range(len(bip_sel) - 11):
                phrase = " ".join(bip_sel[i:i+12])
                tested += 1
                if validator.IsValid(phrase):
                    valid_count += 1
                    print(f"  VALID [every7-{word_list_name}-start{start}-i{i}]: {phrase}")
                    check_phrase(phrase, f"S13-every7-{word_list_name}-{start}-{i}")

# ============================================================
# STRATEGY 14: Combine sections in order
# Take 2 BIP-39 words from each of 6 sections = 12 words
# ============================================================
print("\n--- STRATEGY 14: 2 words per section ---")
import itertools

section_bip_words = {}
for sec_name, (s, e) in sections.items():
    if s < 0:
        continue
    sec_text = text_txt[s:e]
    sec_words = get_words(sec_text)
    sec_bip = list(dict.fromkeys(w for w in sec_words if w in bip39_set))  # unique, ordered
    section_bip_words[sec_name] = sec_bip

sec_names_ordered = ["Revolution", "Fiat", "Bitcoin", "Touchpoints", "Steganography", "TrithemianSeeds"]
sec_names_valid = [s for s in sec_names_ordered if s in section_bip_words]

if len(sec_names_valid) == 6:
    # Take first word from each section
    first_per_sec = [section_bip_words[s][0] for s in sec_names_valid]
    # Take last word from each section
    last_per_sec = [section_bip_words[s][-1] for s in sec_names_valid]
    
    # first+last = 12 words
    combo1 = first_per_sec + last_per_sec
    combo2 = []
    for s in sec_names_valid:
        combo2.append(section_bip_words[s][0])
        combo2.append(section_bip_words[s][-1])
    
    for name, combo in [("first6+last6", combo1), ("interleaved", combo2)]:
        phrase = " ".join(combo)
        tested += 1
        if validator.IsValid(phrase):
            valid_count += 1
            print(f"  VALID [{name}]: {phrase}")
            check_phrase(phrase, f"S14-{name}")
    
    print(f"  First per section: {first_per_sec}")
    print(f"  Last per section: {last_per_sec}")

t1 = time.time()
print(f"\n{'='*60}")
print(f"MEGA SOLVER PHASE 2 completed in {t1-t0:.2f}s")
print(f"Tested: {tested}, Valid checksums: {valid_count}")
print(f"Target NOT found.")
print(f"{'='*60}")
