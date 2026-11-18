poem = "Fishing freshwater bends and saltwater coasts rewards anyone feeling stressed. Resourceful anglers usually find masterful leapers fun and admit swordfish rank overwhelming any day."
words = poem.replace('.', '').split()
print("Words count:", len(words))
letters = [w[2] for w in words]
print("3rd letters:", "".join(letters))
for i, w in enumerate(words):
    print(f"{i+1:2d}: {w:15s} -> {w[2]}")
