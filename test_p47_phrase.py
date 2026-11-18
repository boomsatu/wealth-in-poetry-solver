from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
import itertools

phrase = "can easy point country where people trust what what truly unaware trust"
validator = Bip39MnemonicValidator()
is_valid = validator.IsValid(phrase)
print("Is valid BIP39:", is_valid)

words = phrase.split()
print("Words:", words)

# What if order is slightly permuted or duplicate words resolved?
# Let's test if phrase is valid or if any permutations are valid!
target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"

if is_valid:
    seed = Bip39SeedGenerator(phrase).Generate()
    mst = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
    for i in range(5):
        addr = mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
        print(f"Address {i}: {addr}")
        if addr == target:
            print("TARGET MATCH!!!")
