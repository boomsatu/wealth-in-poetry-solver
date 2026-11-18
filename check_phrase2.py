from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

phrase2 = "asset trial load escape symbol story bomb picnic river aerobic mystery honey"

validator = Bip39MnemonicValidator()
is_valid = validator.IsValid(phrase2)
print("Is phrase 2 valid BIP39 mnemonic:", is_valid)

if is_valid:
    seed_bytes = Bip39SeedGenerator(phrase2).Generate()
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    # m/44'/0'/0'/0/0
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    print("m/44'/0'/0'/0/0 address:", bip44_acc.PublicKey().ToAddress())
    
    # check first 5 addresses
    for i in range(5):
        addr = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
        print(f"Address {i}:", addr)

target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
print("Target match?", target == bip44_acc.PublicKey().ToAddress())
