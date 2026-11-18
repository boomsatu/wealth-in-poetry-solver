"""
Test all Trithemius-style letter extraction rules across:
- Each paragraph
- The Revolution story
- The whole article
- The concluding paragraphs
"""
import re

with open('text.txt', encoding='utf-8') as f:
    text_lines = [l.strip() for l in f if l.strip()]

with open('english.txt') as f:
    bip39_list = [line.strip() for line in f]
    bip39_set = set(bip39_list)

# Split text into paragraphs
with open('text.txt', encoding='utf-8') as f:
    full_raw = f.read()
paragraphs = [p.strip() for p in full_raw.split('\n\n') if p.strip()]

def clean_words(text):
    return [re.sub(r'[^a-zA-Z]', '', w).lower() for w in text.split() if re.sub(r'[^a-zA-Z]', '', w)]

print(f"Total paragraphs: {len(paragraphs)}")

# Test letter extraction rules on each paragraph:
# Rule 1: 1st letter of every word
# Rule 2: 2nd letter of every word
# Rule 3: 3rd letter of every word
# Rule 4: Last letter of every word
# Rule 5: 1st letter of every 2nd word (odd: 1, 3, 5...)
# Rule 6: 1st letter of every 2nd word (even: 2, 4, 6...)
# Rule 7: 2nd letter of every 2nd word
# Rule 8: 1st letter, skip 1st and last word

def extract_letters(words, rule):
    letters = []
    if rule == '1st_all':
        letters = [w[0] for w in words]
    elif rule == '2nd_all':
        letters = [w[1] for w in words if len(w) >= 2]
    elif rule == '3rd_all':
        letters = [w[2] for w in words if len(w) >= 3]
    elif rule == 'last_all':
        letters = [w[-1] for w in words]
    elif rule == '1st_odd':
        letters = [words[i][0] for i in range(0, len(words), 2)]
    elif rule == '1st_even':
        letters = [words[i][0] for i in range(1, len(words), 2)]
    elif rule == '2nd_odd':
        letters = [words[i][1] for i in range(0, len(words), 2) if len(words[i]) >= 2]
    elif rule == '2nd_even':
        letters = [words[i][1] for i in range(1, len(words), 2) if len(words[i]) >= 2]
    elif rule == '3rd_odd':
        letters = [words[i][2] for i in range(0, len(words), 2) if len(words[i]) >= 3]
    elif rule == '3rd_even':
        letters = [words[i][2] for i in range(1, len(words), 2) if len(words[i]) >= 3]
    return "".join(letters)

# Function to search for BIP-39 words in a string of letters
def find_bip_words_in_string(s):
    # Greedily or dynamically find BIP-39 words
    found = []
    i = 0
    while i < len(s):
        matched = None
        # Try words from len 8 down to 3
        for l in range(8, 2, -1):
            sub = s[i:i+l]
            if sub in bip39_set:
                matched = sub
                break
        if matched:
            found.append(matched)
            i += len(matched)
        else:
            i += 1
    return found

print("\n--- Testing letter extraction on paragraphs ---")
for p_idx, p in enumerate(paragraphs):
    words = clean_words(p)
    if len(words) < 10:
        continue
    for rule in ['1st_all', '2nd_all', '3rd_all', 'last_all', '1st_odd', '1st_even', '2nd_odd', '2nd_even']:
        s = extract_letters(words, rule)
        bip = find_bip_words_in_string(s)
        if len(bip) >= 5:
            print(f"P{p_idx} [{rule}] (len {len(s)}): {s[:50]}... -> found {len(bip)} BIP words: {bip[:8]}")

# Also test on Revolution full text (paragraphs 5 to 13)
rev_text = " ".join(paragraphs[5:14])
rev_words = clean_words(rev_text)
print(f"\n--- Revolution text ({len(rev_words)} words) ---")
for rule in ['1st_all', '2nd_all', '3rd_all', 'last_all', '1st_odd', '1st_even', '2nd_odd', '2nd_even']:
    s = extract_letters(rev_words, rule)
    bip = find_bip_words_in_string(s)
    print(f"Rev [{rule}] (len {len(s)}): {s[:40]}... -> found {len(bip)} BIP words: {bip[:12]}")
