import hashlib
import hmac
import ecdsa
import base58

TARGET = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"

def hash160(data):
    sha = hashlib.sha256(data).digest()
    h = hashlib.new('ripemd160', sha).digest()
    return h

def pubkey_to_address(pubkey_bytes):
    h = hash160(pubkey_bytes)
    vh = b'\x00' + h
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    return base58.b58encode(vh + chk).decode()

def derive_bip32_child(parent_key, parent_chain, index, hardened=False):
    if hardened:
        data = b'\x00' + parent_key + index.to_bytes(4, 'big')
    else:
        sk = ecdsa.SigningKey.from_string(parent_key, curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        x = vk.to_string()[:32]
        y = vk.to_string()[32:]
        prefix = b'\x02' if y[-1] % 2 == 0 else b'\x03'
        pub = prefix + x
        data = pub + index.to_bytes(4, 'big')
    
    I = hmac.new(parent_chain, data, hashlib.sha512).digest()
    IL, IR = I[:32], I[32:]
    
    # parse IL as int and add to parent_key
    il_int = int.from_bytes(IL, 'big')
    pk_int = int.from_bytes(parent_key, 'big')
    curve_order = ecdsa.SECP256k1.order
    child_int = (il_int + pk_int) % curve_order
    child_key = child_int.to_bytes(32, 'big')
    return child_key, IR

def get_pubkey(privkey_bytes):
    sk = ecdsa.SigningKey.from_string(privkey_bytes, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    x = vk.to_string()[:32]
    y = vk.to_string()[32:]
    prefix = b'\x02' if y[-1] % 2 == 0 else b'\x03'
    return prefix + x

def test_raw_mnemonic(phrase, passphrases=[""]):
    norm_phrase = ' '.join(phrase.strip().split())
    for pp in passphrases:
        # BIP39 PBKDF2: salt = "mnemonic" + passphrase
        salt = ("mnemonic" + pp).encode('utf-8')
        seed = hashlib.pbkdf2_hmac('sha512', norm_phrase.encode('utf-8'), salt, 2048)
        
        # BIP32 root key
        I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        master_secret, master_chain = I[:32], I[32:]
        
        # Check root key address
        root_addr = pubkey_to_address(get_pubkey(master_secret))
        if root_addr == TARGET:
            print(f"!!! MATCH ROOT KEY: '{norm_phrase}' pp='{pp}'")
            return True
            
        # Try m/0/0, m/0/1, m/0/2
        try:
            k0, c0 = derive_bip32_child(master_secret, master_chain, 0, False)
            for i in range(10):
                ki, _ = derive_bip32_child(k0, c0, i, False)
                addr = pubkey_to_address(get_pubkey(ki))
                if addr == TARGET:
                    print(f"!!! MATCH m/0/{i}: '{norm_phrase}' pp='{pp}'")
                    return True
        except:
            pass

        # Try BIP44: m/44'/0'/0'/0/i
        try:
            k44, c44 = derive_bip32_child(master_secret, master_chain, 44 + 0x80000000, True)
            k_coin, c_coin = derive_bip32_child(k44, c44, 0 + 0x80000000, True)
            k_acct, c_acct = derive_bip32_child(k_coin, c_coin, 0 + 0x80000000, True)
            k_change0, c_change0 = derive_bip32_child(k_acct, c_acct, 0, False)
            for i in range(10):
                ki, _ = derive_bip32_child(k_change0, c_change0, i, False)
                addr = pubkey_to_address(get_pubkey(ki))
                if addr == TARGET:
                    print(f"!!! MATCH BIP44 m/44'/0'/0'/0/{i}: '{norm_phrase}' pp='{pp}'")
                    return True
            # change 1 (internal)
            k_change1, c_change1 = derive_bip32_child(k_acct, c_acct, 1, False)
            for i in range(5):
                ki, _ = derive_bip32_child(k_change1, c_change1, i, False)
                addr = pubkey_to_address(get_pubkey(ki))
                if addr == TARGET:
                    print(f"!!! MATCH BIP44 m/44'/0'/0'/1/{i}: '{norm_phrase}' pp='{pp}'")
                    return True
        except:
            pass

        # Electrum 2.x PBKDF2: salt = "electrum" + passphrase
        salt_e = ("electrum" + pp).encode('utf-8')
        seed_e = hashlib.pbkdf2_hmac('sha512', norm_phrase.encode('utf-8'), salt_e, 2048)
        # Electrum root
        I_e = hmac.new(b"Bitcoin seed", seed_e, hashlib.sha512).digest()
        ms_e, mc_e = I_e[:32], I_e[32:]
        root_addr_e = pubkey_to_address(get_pubkey(ms_e))
        if root_addr_e == TARGET:
            print(f"!!! MATCH ELECTRUM ROOT: '{norm_phrase}' pp='{pp}'")
            return True
        # Electrum standard path: m/0/i
        try:
            k0_e, c0_e = derive_bip32_child(ms_e, mc_e, 0, False)
            for i in range(10):
                ki, _ = derive_bip32_child(k0_e, c0_e, i, False)
                addr = pubkey_to_address(get_pubkey(ki))
                if addr == TARGET:
                    print(f"!!! MATCH ELECTRUM m/0/{i}: '{norm_phrase}' pp='{pp}'")
                    return True
        except:
            pass
            
    return False

# Candidate phrases
candidates = [
    # witch phrase from line 69
    "witch collapse practice feed shame open despair creek road again ice least",
    # Example 1 variants
    "faint lonely scale gate camera shoulder adult game medal language a payment",
    "faint lonely scale gate camera shoulder adult game medal language good payment",
    "faint lonely scale gate camera shoulder adult game medal language enough payment",
    "faint lonely scale gate camera shoulder adult game medal language payment border",
    # Example 2 phrase
    "asset trial load escape symbol story bomb picnic river aerobic mystery honey",
    # Paragraph 47 (12 BIP-39 words)
    "can easy point country where people trust what what truly unaware trust",
    "can easy point country where people trust what truly unaware trust",
    # Paragraph 26 (12 BIP-39 words)
    "seed often that wealth found list seed can amount journey one major",
]

pps = ["", "trithemius", "Trithemius", "bitcoin", "Bitcoin", "poetry", "wealth"]

print("Testing candidate phrases with unchecksummed derivation...")
for c in candidates:
    print(f"Testing: {c[:40]}...")
    test_raw_mnemonic(c, pps)

print("Done testing candidates.")
