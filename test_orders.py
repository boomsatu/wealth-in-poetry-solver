from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
validator = Bip39MnemonicValidator()

words = ['can', 'easy', 'point', 'country', 'where', 'people', 'trust', 'what', 'what', 'truly', 'unaware', 'trust']

orders = [
    ("original", words),
    ("reversed", list(reversed(words))),
    ("sorted", sorted(words)),
    ("sorted_rev", sorted(words, reverse=True)),
]

for name, wlist in orders:
    phrase = " ".join(wlist)
    val = validator.IsValid(phrase)
    print(f"{name:12s}: valid={val} -> {phrase}")
    if val:
        seed = Bip39SeedGenerator(phrase).Generate()
        mst = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
        for i in range(5):
            addr = mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
            print(f"  addr {i}: {addr}")
            if addr == target:
                print("  MATCH TARGET!!!")
