import re

with open('english.txt') as f:
    bip39 = set(line.strip() for line in f)

ex1_text = '''The faint lines across the lonely expanse make scale hard to determine. As I walk towards the gate, I sling my camera over my shoulder and prepare to enter the old palace. The door pushes open easily and I walk into the courtyard - no adult in sight. I place my camera on the table and get to work searching through the waste. As I dust off an ancient board game, something shiny catches my eye. I reach towards the cupboard and pick up a gold medal. Upon closer inspection, I notice an inscription that seems to resemble a foreign language. I pocket the trinket with the hope that this might make for a good enough payment at the border. Any valuable will do.'''

ex2_text = '''Such an asset to be represented by an experienced and mature lawyer particularly when you have a trial in front of the Supreme Court of the USA. Load your argument with logic and do not provide ways to escape. Symbol of cultural diversity should be used as often as possible in order to support the story. Our client clearly did not make that complex and improvised bomb himself. They were on their way to his friend's picnic by the river when he noticed a suspicious person pretending to do aerobic exercises. He immediately pointed it out to his friends. Their whereabouts aren't a mystery, during the attack they were ordering ginger tea with honey to bring to the picnic.'''

print("=== Example 1 ===")
raw1 = ex1_text.split()
clean1 = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw1 if re.sub(r'[^a-zA-Z]', '', w)]
indices1 = [2, 6, 9, 18, 22, 25, 45, 70, 86, 100, 113, 116]
sel1 = []
for idx in indices1:
    w = clean1[idx-1]
    sel1.append(w)
    print(f'{idx}: {w} (BIP39: {w in bip39})')
print("Phrase 1:", ' '.join(sel1))

print("\n=== Example 2 ===")
raw2 = ex2_text.split()
clean2 = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw2 if re.sub(r'[^a-zA-Z]', '', w)]
indices2 = [3, 18, 28, 39, 40, 56, 67, 77, 80, 90, 104, 114]
sel2 = []
for idx in indices2:
    w = clean2[idx-1]
    sel2.append(w)
    print(f'{idx}: {w} (BIP39: {w in bip39})')
print("Phrase 2:", ' '.join(sel2))
