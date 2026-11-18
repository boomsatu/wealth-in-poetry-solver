import re
from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
validator = Bip39MnemonicValidator()

with open('english.txt') as f:
    bip39_set = set(line.strip() for line in f)

with open('clean_article.txt', encoding='utf-8') as f:
    full_text = f.read()

# Load text sections
with open('text.txt', encoding='utf-8') as f:
    text_txt = f.read()

paragraphs = [p.strip() for p in text_txt.split('\n\n') if p.strip()]

def get_clean_words(text):
    raw = text.split()
    return [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw if re.sub(r'[^a-zA-Z]', '', w)]

def test_digits_on_words(digits, words, label=""):
    if len(digits) != 12:
        return
    indices = [digits[i] + i * 10 for i in range(12)]
    # Check if indices are within bounds
    if any(idx >= len(words) for idx in indices):
        return
    # 0-based vs 1-based
    for base in [0, 1]:
        phrase_words = []
        all_in_bip39 = True
        for idx in indices:
            real_idx = idx if base == 0 else idx - 1
            if real_idx < 0 or real_idx >= len(words):
                all_in_bip39 = False
                break
            w = words[real_idx]
            if w not in bip39_set:
                all_in_bip39 = False
                break
            phrase_words.append(w)
        if all_in_bip39:
            phrase = " ".join(phrase_words)
            is_valid = validator.IsValid(phrase)
            print(f"[{label}] Base={base} All in BIP39! Valid BIP39={is_valid} -> {phrase}")
            if is_valid:
                seed = Bip39SeedGenerator(phrase).Generate()
                mst = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
                for i in range(5):
                    addr = mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
                    if addr == target:
                        print(f"!!! JACKPOT TARGET MATCH: {phrase} !!!")

# Candidates for 12 digits:
candidates = [
    # Mount Vernon: 38.7080 N, 77.0861 W
    ([3,8,7,0,8,0, 7,7,0,8,6,1], "Mount Vernon 1"),
    ([3,8,7,3,5,2, 7,7,0,9,5,2], "Mount Vernon CDP"),
    # Jesus College Oxford: 51.7534 N, 1.2569 W (padded with 0: 01.2569 or 1.25690)
    ([5,1,7,5,3,4, 0,1,2,5,6,9], "Jesus College 1"),
    ([5,1,7,5,3,4, 1,2,5,6,9,0], "Jesus College 2"),
    ([5,1,7,5,3,4, 1,2,5,6,4,0], "Jesus College 3"),
    # Qingdao: 36.0669 N, 120.3827 E
    ([3,6,0,6,6,9, 1,2,0,3,8,2], "Qingdao 1"),
    ([3,6,0,6,7,1, 1,2,0,3,8,2], "Qingdao 2"),
    # Trittenheim (Johannes Trithemius birth): 49.8247 N, 6.8994 E
    ([4,9,8,2,4,7, 0,6,8,9,9,4], "Trittenheim 1"),
    ([4,9,8,2,4,7, 6,8,9,9,4,0], "Trittenheim 2"),
    # Sponheim Abbey: 49.8456 N, 7.7289 E
    ([4,9,8,4,5,6, 0,7,7,2,8,9], "Sponheim 1"),
    # Frankfurt: 50.1109 N, 8.6821 E
    ([5,0,1,1,0,9, 0,8,6,8,2,1], "Frankfurt 1"),
]

# Test on all paragraphs of text.txt with length >= 120
for p_idx, p in enumerate(paragraphs):
    words = get_clean_words(p)
    if len(words) >= 115:
        for digits, name in candidates:
            test_digits_on_words(digits, words, f"P{p_idx}_{name}")

# Also test on Revolution full text
rev_words = get_clean_words(" ".join(paragraphs[5:13]))
print(f"Testing on full Revolution text (len={len(rev_words)})...")
for digits, name in candidates:
    test_digits_on_words(digits, rev_words, f"RevFull_{name}")
