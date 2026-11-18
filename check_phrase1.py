from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

phrase1 = "faint lonely scale gate camera shoulder adult game medal language good payment"

validator = Bip39MnemonicValidator()
is_valid = validator.IsValid(phrase1)
print("Is phrase 1 valid BIP39 mnemonic:", is_valid)

if is_valid:
    seed_bytes = Bip39SeedGenerator(phrase1).Generate()
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    print("m/44'/0'/0'/0/0 address:", bip44_acc.PublicKey().ToAddress())
    target = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
    print("Target match?", target == bip44_acc.PublicKey().ToAddress())
