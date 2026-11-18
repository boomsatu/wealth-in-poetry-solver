from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

phrase_witch = "witch collapse practice feed shame open despair creek road again ice least"

print("Is valid:", Bip39MnemonicValidator().IsValid(phrase_witch))
seed_bytes = Bip39SeedGenerator(phrase_witch).Generate()
bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
for i in range(5):
    addr = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
    print(f"Address {i}: {addr}")

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
print("Match?", addr == target)
