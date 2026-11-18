use hmac::Hmac;
use pbkdf2::pbkdf2;
use sha2::{Digest, Sha256, Sha512};
use std::collections::HashMap;
use std::sync::OnceLock;

pub const WORDLIST: &str = include_str!("../../english.txt");

static WORD_TO_INDEX: OnceLock<HashMap<&'static str, u16>> = OnceLock::new();
static WORDS_ARRAY: OnceLock<Vec<&'static str>> = OnceLock::new();

pub fn get_words() -> &'static Vec<&'static str> {
    WORDS_ARRAY.get_or_init(|| WORDLIST.lines().map(|l| l.trim()).collect())
}

pub fn get_word_to_index() -> &'static HashMap<&'static str, u16> {
    WORD_TO_INDEX.get_or_init(|| {
        let mut map = HashMap::with_capacity(2048);
        for (i, word) in get_words().iter().enumerate() {
            map.insert(*word, i as u16);
        }
        map
    })
}

pub fn word_index(word: &str) -> Option<u16> {
    get_word_to_index().get(word).copied()
}

pub fn index_to_word(idx: u16) -> &'static str {
    get_words()[idx as usize]
}

/// Fast BIP-39 checksum verification for 12 words (128 bits entropy + 4 bits checksum).
/// 12 words = 132 bits.
/// Returns true if valid BIP-39 checksum, false otherwise.
/// Extremely fast (~5 CPU cycles): does NOT perform PBKDF2!
#[inline(always)]
pub fn fast_verify_checksum(indices: &[u16; 12]) -> bool {
    let mut bits = [0u8; 17]; // 132 bits = 16.5 bytes
    // Pack 12 * 11 bits into byte array
    let mut bit_pos = 0;
    for &idx in indices.iter() {
        for b in (0..11).rev() {
            let bit = ((idx >> b) & 1) as u8;
            let byte_idx = bit_pos / 8;
            let bit_idx = 7 - (bit_pos % 8);
            bits[byte_idx] |= bit << bit_idx;
            bit_pos += 1;
        }
    }

    // Entropy is the first 16 bytes (128 bits)
    let entropy: &[u8; 16] = bits[0..16].try_into().unwrap();
    let expected_checksum = (bits[16] >> 4) & 0x0F;

    // SHA-256 of entropy
    let hash = Sha256::digest(entropy);
    let actual_checksum = (hash[0] >> 4) & 0x0F;

    actual_checksum == expected_checksum
}

/// Convert 12 word indices into a space-separated mnemonic phrase.
pub fn indices_to_phrase(indices: &[u16; 12]) -> String {
    let words = get_words();
    let mut phrase = String::with_capacity(120);
    for (i, &idx) in indices.iter().enumerate() {
        if i > 0 {
            phrase.push(' ');
        }
        phrase.push_str(words[idx as usize]);
    }
    phrase
}

/// Generate 64-byte BIP-39 seed using PBKDF2-HMAC-SHA512 (2048 iterations).
pub fn mnemonic_to_seed(phrase: &str, passphrase: &str) -> [u8; 64] {
    let salt = format!("mnemonic{}", passphrase);
    let mut seed = [0u8; 64];
    pbkdf2::<Hmac<Sha512>>(phrase.as_bytes(), salt.as_bytes(), 2048, &mut seed)
        .expect("PBKDF2 failed");
    seed
}
