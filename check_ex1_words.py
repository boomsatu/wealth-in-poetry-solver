ex1 = """The faint lines across the lonely expanse make scale hard to determine. As I walk towards the gate, I sling my camera over my shoulder and prepare to enter the old palace. The door pushes open easily and I walk into the courtyard - no adult in sight. I place my camera on the table and get to work searching through the waste. As I dust off an ancient board game, something shiny catches my eye. I reach towards the cupboard and pick up a gold medal. Upon closer inspection, I notice an inscription that seems to resemble a foreign language. I pocket the trinket with the hope that this might make for a good enough payment at the border. Any valuable will do."""

import re
# Words without hyphen
words = re.findall(r"[a-zA-Z]+", ex1)
print(f"Total words: {len(words)}")
indices = [2, 6, 9, 18, 22, 25, 45, 70, 86, 100, 113, 116]

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

for idx in indices:
    w = words[idx-1].lower()
    print(f"Word {idx}: {w} (BIP39: {w in bip39})")
