"""
Advanced solver approaches:
1. Line 118 BIP-39 words with different derivation paths (BIP-49, BIP-84, BIP-32)
2. Permutations of line 118 words (it has exactly 12 BIP-39 words!)
3. The GPS method applied to the FULL article using all coordinate candidates  
4. Try extracting words at positions derived from the Bitcoin address itself
5. Try the article text as seed phrase directly (brainwallet variants)
6. Null cipher: every Nth letter forming BIP-39 words
7. Word-position extraction from the last paragraph (the actual puzzle)
"""
import re
import hashlib
import struct

# Load BIP-39 wordlist
with open('english.txt', 'r') as f:
    bip39_list = f.read().strip().split('\n')
    bip39_set = set(bip39_list)
    bip39_index = {w: i for i, w in enumerate(bip39_list)}

# Load article
with open('text.txt', 'r') as f:
    lines = [l.strip() for l in f.readlines()]

full_text = ' '.join(lines)
all_words_raw = full_text.split()
all_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in all_words_raw]

# Body words (skip header)
body_lines = [l for l in lines[18:] if l.strip()]
body_text = ' '.join(body_lines)
body_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in body_text.split()]

from bip_utils import (
    Bip39MnemonicValidator, Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes,
    Bip49, Bip49Coins,
    Bip84, Bip84Coins,
    Bip32Slip10Secp256k1
)
import base58

TARGET = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
TARGET_HASH160 = "c6233aeb3a50a70b82fcd88d69b5f1a3ec6e355a"

found = False

def check_all_paths(phrase, label=""):
    """Check mnemonic with ALL derivation paths"""
    global found
    try:
        Bip39MnemonicValidator(phrase).Validate()
    except:
        return False
    
    passphrases = ["", "trithemius", "Trithemius", "steganography", "Steganographia",
                   "poetry", "wealth", "bitcoin", "Bitcoin", "ye-ye", "yuanbao",
                   "revolution", "M.7.7"]
    
    for pp in passphrases:
        try:
            seed = Bip39SeedGenerator(phrase).Generate(pp)
            
            # BIP-44 (P2PKH - starts with 1)
            bip44 = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            for acct in range(3):
                for change in [Bip44Changes.CHAIN_EXT, Bip44Changes.CHAIN_INT]:
                    for idx in range(5):
                        try:
                            addr = bip44.Purpose().Coin().Account(acct).Change(change).AddressIndex(idx).PublicKey().ToAddress()
                            if addr == TARGET:
                                print(f"\n!!! BIP-44 MATCH !!! [{label}] pp='{pp}' acct={acct} change={change} idx={idx}")
                                print(f"Phrase: {phrase}")
                                found = True
                                return True
                        except:
                            pass
            
            # BIP-49 (P2SH-P2WPKH - starts with 3) - unlikely but try
            # BIP-84 (P2WPKH - starts with bc1) - unlikely but try
            
            # BIP-32 direct paths
            bip32 = Bip32Slip10Secp256k1.FromSeed(seed)
            # Try m/0/0
            try:
                child = bip32.ChildKey(0).ChildKey(0)
                # Derive P2PKH address from public key
                from bip_utils import P2PKHAddrEncoder, CoinsConf, Bip44Coins as BC
                pubkey = child.PublicKey()
                addr = P2PKHAddrEncoder.EncodeKey(pubkey.KeyObject(), ver=b'\x00')
                if addr == TARGET:
                    print(f"\n!!! BIP-32 m/0/0 MATCH !!! [{label}] pp='{pp}'")
                    print(f"Phrase: {phrase}")
                    found = True
                    return True
            except Exception as e:
                pass
            
            # Try root key directly
            try:
                from bip_utils import P2PKHAddrEncoder
                pubkey = bip32.PublicKey()
                addr = P2PKHAddrEncoder.EncodeKey(pubkey.KeyObject(), ver=b'\x00')
                if addr == TARGET:
                    print(f"\n!!! BIP-32 root MATCH !!! [{label}] pp='{pp}'")
                    print(f"Phrase: {phrase}")
                    found = True
                    return True
            except:
                pass
                
        except Exception as e:
            pass
    
    return False

tested = 0
valid_checksums = 0

# ============================================================
# METHOD 1: Line 118 has exactly 12 BIP-39 words - try reordering
# ============================================================
print("=== METHOD 1: Line 118 BIP-39 words with all paths ===")

line118_bip = ['can', 'easy', 'point', 'country', 'where', 'people', 'trust', 'what', 'what', 'truly', 'unaware', 'trust']
# Original order
phrase = ' '.join(line118_bip)
tested += 1
check_all_paths(phrase, "line118_original")

# Remove duplicates and try
unique_118 = list(dict.fromkeys(line118_bip))  # preserves order
print(f"  Unique words from line 118: {unique_118}")

# Try with the exact 12 unique BIP-39 words from lines 118-120
# Lines 118-122 together
last_section = ' '.join(lines[117:])
last_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in last_section.split()]
last_bip = [w for w in last_words if w in bip39_set]
print(f"  BIP-39 in lines 118-122: {last_bip}")

# Sliding windows from last section
for i in range(len(last_bip) - 11):
    window = last_bip[i:i+12]
    tested += 1
    try:
        Bip39MnemonicValidator(' '.join(window)).Validate()
        valid_checksums += 1
        check_all_paths(' '.join(window), f"last_section_w{i}")
    except:
        pass

# ============================================================
# METHOD 2: GPS coordinates with the FULL article
# Try coordinates that relate to the author/article
# ============================================================
print("\n=== METHOD 2: Extended GPS coordinate search ===")

# Key coordinates from the article plus extras
coordinates = {
    # From the article
    "US_Supreme_Court": (38.8906, 77.0044),
    "Qingdao": (36.0669, 120.3827),
    "Qingdao_v2": (36.0671, 120.3826),
    # Historical/Trithemius related
    "Trittenheim": (49.8247, 6.8994),
    "Sponheim_Abbey": (49.8900, 7.6350),
    "Wurzburg": (49.7913, 9.9534),
    # Article mentions
    "Taiwan": (25.0330, 121.5654),
    "Mount_Vernon": (38.7080, 77.0861),
    "Zimbabwe_Harare": (17.8252, 31.0335),
    "Venezuela_Caracas": (10.4806, 66.9036),
    "Canada_Toronto": (43.6532, 79.3832),
    # Jesus College Oxford (M.7.7 ref)
    "Jesus_College_Oxford": (51.7534, 1.2569),
    "Bodleian_Library": (51.7540, 1.2545),
    # Vatican (banned book)
    "Vatican": (41.9029, 12.4534),
    # Beijing
    "Beijing": (39.9042, 116.4074),
    # Shanghai
    "Shanghai": (31.2304, 121.4737),
    # China general
    "China_center": (35.8617, 104.1954),
    # Frankfurt (financial ref)
    "Frankfurt": (50.1109, 8.6821),
    # London
    "London": (51.5074, 0.1278),
    # New York
    "New_York": (40.7128, 74.0060),
}

def gps_to_positions(lat, lon, variant="standard"):
    """Convert GPS coordinates to word positions using article's method"""
    # Get digit string from lat and lon  
    lat_str = f"{abs(lat):.4f}".replace('.', '')
    lon_str = f"{abs(lon):.4f}".replace('.', '')
    
    if variant == "standard":
        # Combine lat+lon digits, take first 12
        all_digits = [int(d) for d in lat_str + lon_str][:12]
        positions = [d + 10*i + 1 for i, d in enumerate(all_digits)]
    elif variant == "no_plus1":
        all_digits = [int(d) for d in lat_str + lon_str][:12]
        positions = [d + 10*i for i, d in enumerate(all_digits)]
    elif variant == "lat_then_lon_separate":
        lat_digits = [int(d) for d in lat_str][:6]
        lon_digits = [int(d) for d in lon_str][:6]
        positions = [d + 10*i + 1 for i, d in enumerate(lat_digits + lon_digits)]
    elif variant == "reverse":
        all_digits = [int(d) for d in (lon_str + lat_str)][:12]
        positions = [d + 10*i + 1 for i, d in enumerate(all_digits)]
    elif variant == "just_digits":
        # Use digits as direct 1-indexed positions
        all_digits = [int(d) for d in lat_str + lon_str][:12]
        positions = [d + 1 for d in all_digits]  # small positions
    return positions

for name, (lat, lon) in coordinates.items():
    for variant in ["standard", "no_plus1", "reverse"]:
        try:
            positions = gps_to_positions(lat, lon, variant)
        except:
            continue
        
        for word_list, wl_name in [(body_words, "body"), (all_words, "all")]:
            if any(p >= len(word_list) or p < 0 for p in positions):
                continue
            extracted = [word_list[p] for p in positions]
            if all(w in bip39_set for w in extracted):
                tested += 1
                phrase = ' '.join(extracted)
                try:
                    Bip39MnemonicValidator(phrase).Validate()
                    valid_checksums += 1
                    print(f"  VALID CHECKSUM: {name}_{variant}_{wl_name}: {phrase}")
                    print(f"    Positions: {positions}")
                    check_all_paths(phrase, f"gps_{name}_{variant}_{wl_name}")
                except:
                    pass

# ============================================================
# METHOD 3: Bitcoin address hash as position key
# ============================================================
print("\n=== METHOD 3: Bitcoin address as position key ===")

# Target address: 1K4ezpLybootYF23TM4a8Y4NyP7auysnRo
# Hash160: c6233aeb3a50a70b82fcd88d69b5f1a3ec6e355a
# Try using hash160 digits as GPS-method key
hash_digits = [int(c, 16) for c in TARGET_HASH160]  # hex digits 0-15
# First 12 hex digits: c,6,2,3,3,a,e,b,3,a,5,0 -> 12,6,2,3,3,10,14,11,3,10,5,0
gps_from_hash = [hash_digits[i] + 10*i for i in range(12)]
print(f"  Hash160 GPS positions: {gps_from_hash}")
for word_list, wl_name in [(body_words, "body"), (all_words, "all")]:
    if max(gps_from_hash) < len(word_list):
        extracted = [word_list[p] for p in gps_from_hash]
        if all(w in bip39_set for w in extracted):
            tested += 1
            phrase = ' '.join(extracted)
            print(f"    Hash160 GPS ({wl_name}): {phrase}")
            try:
                Bip39MnemonicValidator(phrase).Validate()
                valid_checksums += 1
                check_all_paths(phrase, f"hash160_gps_{wl_name}")
            except:
                pass

# Base58 decode of address
addr_bytes = base58.b58decode(TARGET)
addr_hex = addr_bytes.hex()
print(f"  Address bytes hex: {addr_hex}")

# ============================================================
# METHOD 4: Try using paragraph numbers as BIP-39 word indices
# ============================================================
print("\n=== METHOD 4: Paragraph-derived BIP-39 indices ===")

# Count paragraphs and use paragraph word counts as indices
para_word_counts = []
for line in lines:
    if line.strip():
        wc = len(line.strip().split())
        para_word_counts.append(wc)

print(f"  Paragraph word counts: {para_word_counts}")

# Use specific number sequences from the article as BIP-39 indices (0-2047)
number_sequences = {
    "article_numbers": [1930, 2000, 1920, 40, 40, 10, 221, 206, 50, 2018, 39, 300],
    "small_article_nums": [40, 40, 10, 50, 39, 7, 7],
    "year_digits": [1,9,3,0,2,0,0,0,1,9,2,0],  # 1930, 2000, 1920 digits
}

for name, nums in number_sequences.items():
    if len(nums) >= 12:
        indices = nums[:12]
        if all(0 <= i < 2048 for i in indices):
            words = [bip39_list[i] for i in indices]
            tested += 1
            phrase = ' '.join(words)
            try:
                Bip39MnemonicValidator(phrase).Validate()
                valid_checksums += 1
                print(f"  VALID: {name}: {phrase}")
                check_all_paths(phrase, f"indices_{name}")
            except:
                pass

# ============================================================
# METHOD 5: Extract words where POSITION in article = BIP-39 index
# i.e., word at position N is used if N mod 2048 is a valid selection
# ============================================================
print("\n=== METHOD 5: Position-based filtering ===")

# Words whose position (1-indexed) has specific properties
# Try: words at prime positions
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5)+1):
        if n % i == 0: return False
    return True

prime_bip = [body_words[i] for i in range(len(body_words)) if is_prime(i+1) and body_words[i] in bip39_set]
print(f"  BIP-39 at prime positions ({len(prime_bip)}): {prime_bip[:20]}...")
for i in range(len(prime_bip) - 11):
    window = prime_bip[i:i+12]
    tested += 1
    try:
        Bip39MnemonicValidator(' '.join(window)).Validate()
        valid_checksums += 1
        check_all_paths(' '.join(window), f"prime_pos_w{i}")
    except:
        pass

# ============================================================
# METHOD 6: Brainwallet - SHA256 of article text -> private key
# ============================================================
print("\n=== METHOD 6: Brainwallet SHA256 ===")

import ecdsa

brainwallet_inputs = [
    "Securing Wealth in Poetry",
    "securing wealth in poetry",
    "wealth in poetry",
    "Wealth in Poetry",
    "trithemian seeds",
    "Trithemian Seeds",
    "The beauty of trithemian seeds is that they hide in plain sight.",
    "If you've read this far, you've read every word required to access a wallet with .03 BTC. Good luck!",
    full_text,
    body_text,
    "Trithemius",
    "steganographia",
    "Steganographia",
    "ye-ye",
    "revolution",
    "d8eb43a02254",
    "89cc82722605",
    "M.7.7",
]

for inp in brainwallet_inputs:
    h = hashlib.sha256(inp.encode('utf-8')).digest()
    # Derive bitcoin address from private key
    try:
        sk = ecdsa.SigningKey.from_string(h, curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        # Compressed public key
        x = vk.to_string()[:32]
        y = vk.to_string()[32:]
        prefix = b'\x02' if y[-1] % 2 == 0 else b'\x03'
        compressed_pub = prefix + x
        # Hash160
        sha = hashlib.sha256(compressed_pub).digest()
        import hashlib as hl
        ripemd = hl.new('ripemd160', sha).digest()
        # Base58Check
        addr_bytes = b'\x00' + ripemd
        checksum = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
        addr = base58.b58encode(addr_bytes + checksum).decode()
        if addr == TARGET:
            print(f"  !!! BRAINWALLET MATCH !!!: '{inp[:50]}...'")
            found = True
            break
    except Exception as e:
        pass

if not found:
    print("  No brainwallet match")

# ============================================================
# METHOD 7: Try Electrum-style derivation (m/0/i)
# ============================================================
print("\n=== METHOD 7: BIP-39 words from clean_article.txt ===")

with open('clean_article.txt', 'r', encoding='utf-8', errors='ignore') as f:
    clean_text = f.read()

clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in clean_text.split()]
clean_bip = [w for w in clean_words if w in bip39_set]
print(f"  Clean article BIP-39 words: {len(clean_bip)}")

# Sliding windows from clean article
for i in range(len(clean_bip) - 11):
    window = clean_bip[i:i+12]
    tested += 1
    try:
        Bip39MnemonicValidator(' '.join(window)).Validate()
        valid_checksums += 1
        check_all_paths(' '.join(window), f"clean_w{i}")
    except:
        pass

print(f"\n=== TOTAL: tested={tested}, valid_checksums={valid_checksums}, found={found} ===")
