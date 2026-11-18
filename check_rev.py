import re

with open('clean_article.txt', encoding='utf-8') as f:
    text = f.read()

# Let's extract the Revolution section
start = text.find('Revolution')
end = text.find('Fiat')
rev_text = text[start:end].strip()

# words in rev_text
words = re.findall(r'[a-zA-Z]+', rev_text)
print("Revolution section words count:", len(words))

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

bip39_in_rev = [(i+1, w.lower()) for i, w in enumerate(words) if w.lower() in bip39]
print(f"Total BIP39 words in Revolution: {len(bip39_in_rev)} out of {len(words)}")
