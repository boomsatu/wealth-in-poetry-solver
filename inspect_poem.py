import re

poem = "Fishing freshwater bends and saltwater coasts rewards anyone feeling stressed. Resourceful anglers usually find masterful leapers fun and admit swordfish rank overwhelming any day."

words = re.findall(r'[a-zA-Z]+', poem)
print("Poem word count:", len(words))
for i, w in enumerate(words, 1):
    print(f"{i:2d}: {w}")
