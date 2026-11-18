use hmac::{Hmac, Mac};
use k256::elliptic_curve::sec1::ToEncodedPoint;
use k256::elliptic_curve::PrimeField;
use k256::{AffinePoint, ProjectivePoint, Scalar};
use ripemd::Ripemd160;
use sha2::{Digest, Sha256, Sha512};

pub const TARGET_ADDRESS: &str = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo";
pub const TARGET_HASH160: [u8; 20] = [
    0xc6, 0x23, 0x3a, 0xeb, 0x3a, 0x50, 0xa7, 0x0b, 0x82, 0xfc, 0xd8, 0x8d, 0x69, 0xb5, 0xf1,
    0xa3, 0xec, 0x6e, 0x35, 0x5a,
];

pub struct ExtendedKey {
    pub key: [u8; 32],
    pub chain_code: [u8; 32],
}

impl ExtendedKey {
    pub fn from_seed(seed: &[u8; 64]) -> Self {
        let mut mac = Hmac::<Sha512>::new_from_slice(b"Bitcoin seed").unwrap();
        mac.update(seed);
        let result = mac.finalize().into_bytes();
        let mut key = [0u8; 32];
        let mut chain_code = [0u8; 32];
        key.copy_from_slice(&result[0..32]);
        chain_code.copy_from_slice(&result[32..64]);
        Self { key, chain_code }
    }

    pub fn derive_child(&self, index: u32, hardened: bool) -> Option<Self> {
        let mut mac = Hmac::<Sha512>::new_from_slice(&self.chain_code).unwrap();
        let actual_index = if hardened {
            index | 0x8000_0000
        } else {
            index
        };

        if hardened {
            mac.update(&[0u8]);
            mac.update(&self.key);
            mac.update(&actual_index.to_be_bytes());
        } else {
            let pubkey = private_key_to_compressed_pubkey(&self.key)?;
            mac.update(&pubkey);
            mac.update(&actual_index.to_be_bytes());
        }

        let result = mac.finalize().into_bytes();
        let mut il_bytes = [0u8; 32];
        let mut chain_code = [0u8; 32];
        il_bytes.copy_from_slice(&result[0..32]);
        chain_code.copy_from_slice(&result[32..64]);

        // Child key = (IL + parent_key) mod n
        let il_scalar = Scalar::from_repr(il_bytes.into());
        let parent_scalar = Scalar::from_repr(self.key.into());

        if bool::from(il_scalar.is_none()) || bool::from(parent_scalar.is_none()) {
            return None;
        }

        let child_scalar = il_scalar.unwrap() + parent_scalar.unwrap();
        let child_key_bytes = child_scalar.to_bytes();
        let mut key = [0u8; 32];
        key.copy_from_slice(&child_key_bytes);

        Some(Self { key, chain_code })
    }
}

pub fn private_key_to_compressed_pubkey(privkey: &[u8; 32]) -> Option<[u8; 33]> {
    let scalar = Scalar::from_repr((*privkey).into());
    if bool::from(scalar.is_none()) {
        return None;
    }
    let point = ProjectivePoint::GENERATOR * scalar.unwrap();
    let affine = AffinePoint::from(point);
    let encoded = affine.to_encoded_point(true);
    let bytes = encoded.as_bytes();
    let mut compressed = [0u8; 33];
    compressed.copy_from_slice(bytes);
    Some(compressed)
}

pub fn pubkey_to_hash160(compressed_pubkey: &[u8; 33]) -> [u8; 20] {
    let sha = Sha256::digest(compressed_pubkey);
    let rip = Ripemd160::digest(sha);
    let mut hash160 = [0u8; 20];
    hash160.copy_from_slice(&rip);
    hash160
}

pub fn hash160_to_address(hash160: &[u8; 20]) -> String {
    let mut payload = Vec::with_capacity(25);
    payload.push(0x00); // Mainnet prefix
    payload.extend_from_slice(hash160);
    let checksum = Sha256::digest(Sha256::digest(&payload));
    payload.extend_from_slice(&checksum[0..4]);
    bs58::encode(payload).into_string()
}

/// Check if a 64-byte seed derives the target Bitcoin address.
/// Tests standard BIP-44 path: m/44'/0'/0'/0/i for i in 0..5
/// and direct path m/0/i for i in 0..3
pub fn check_seed_matches_target(seed: &[u8; 64]) -> Option<(String, String)> {
    let master = ExtendedKey::from_seed(seed);

    // 1. Check root key directly
    if let Some(pubkey) = private_key_to_compressed_pubkey(&master.key) {
        if pubkey_to_hash160(&pubkey) == TARGET_HASH160 {
            return Some(("m".to_string(), hash160_to_address(&TARGET_HASH160)));
        }
    }

    // 2. Check BIP-44: m/44'/0'/0'/0/i
    if let Some(m44) = master.derive_child(44, true) {
        if let Some(coin) = m44.derive_child(0, true) {
            if let Some(acct) = coin.derive_child(0, true) {
                // External chain (0)
                if let Some(change0) = acct.derive_child(0, false) {
                    for idx in 0..5 {
                        if let Some(child) = change0.derive_child(idx, false) {
                            if let Some(pubkey) = private_key_to_compressed_pubkey(&child.key) {
                                if pubkey_to_hash160(&pubkey) == TARGET_HASH160 {
                                    return Some((
                                        format!("m/44'/0'/0'/0/{}", idx),
                                        hash160_to_address(&TARGET_HASH160),
                                    ));
                                }
                            }
                        }
                    }
                }
                // Internal/change chain (1)
                if let Some(change1) = acct.derive_child(1, false) {
                    for idx in 0..3 {
                        if let Some(child) = change1.derive_child(idx, false) {
                            if let Some(pubkey) = private_key_to_compressed_pubkey(&child.key) {
                                if pubkey_to_hash160(&pubkey) == TARGET_HASH160 {
                                    return Some((
                                        format!("m/44'/0'/0'/1/{}", idx),
                                        hash160_to_address(&TARGET_HASH160),
                                    ));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // 3. Check direct path: m/0/i (Electrum / older wallets)
    if let Some(m0) = master.derive_child(0, false) {
        for idx in 0..3 {
            if let Some(child) = m0.derive_child(idx, false) {
                if let Some(pubkey) = private_key_to_compressed_pubkey(&child.key) {
                    if pubkey_to_hash160(&pubkey) == TARGET_HASH160 {
                        return Some((
                            format!("m/0/{}", idx),
                            hash160_to_address(&TARGET_HASH160),
                        ));
                    }
                }
            }
        }
    }

    None
}
