use crate::bip39::{fast_verify_checksum, indices_to_phrase, mnemonic_to_seed};
use crate::crypto::check_seed_matches_target;
use crate::data::{get_revolution_bip39_occurrences, get_revolution_words, DISPERSAL_12_BLOCKS, REVOLUTION_PARAGRAPHS};
use indicatif::{ProgressBar, ProgressStyle};
use rayon::prelude::*;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::time::Instant;

#[derive(Debug, Clone, Copy)]
pub enum Strategy {
    Blocks,
    OrderPreserving,
    Paragraphs,
    Dispersal12,
}

pub struct SolverConfig {
    pub strategy: Strategy,
    pub block_size: usize,
    pub min_gap: usize,
    pub max_gap: usize,
    pub passphrase: String,
}

pub fn run_cpu_solver(config: SolverConfig) {
    let start_time = Instant::now();
    let found = Arc::new(AtomicBool::new(false));
    let tested_count = Arc::new(AtomicU64::new(0));
    let valid_checksum_count = Arc::new(AtomicU64::new(0));

    let pb = ProgressBar::new_spinner();
    pb.set_style(
        ProgressStyle::default_spinner()
            .template("{spinner:.green} [{elapsed_precise}] Tested: {pos} | Valid Checksums: {msg} ({per_sec})")
            .unwrap(),
    );

    match config.strategy {
        Strategy::Blocks => {
            run_blocks_strategy(&config, &found, &tested_count, &valid_checksum_count, &pb);
        }
        Strategy::OrderPreserving => {
            run_order_preserving_strategy(&config, &found, &tested_count, &valid_checksum_count, &pb);
        }
        Strategy::Paragraphs => {
            run_paragraphs_strategy(&config, &found, &tested_count, &valid_checksum_count, &pb);
        }
        Strategy::Dispersal12 => {
            run_dispersal12_strategy(&config, &found, &tested_count, &valid_checksum_count, &pb);
        }
    }

    pb.finish_and_clear();
    let elapsed = start_time.elapsed().as_secs_f64();
    let total = tested_count.load(Ordering::Relaxed);
    let valid = valid_checksum_count.load(Ordering::Relaxed);

    println!("\n=== CPU Search Completed ===");
    println!("Elapsed Time: {:.2}s", elapsed);
    println!("Total Tested: {}", total);
    println!("Valid BIP-39 Checksums: {}", valid);
    println!("Throughput: {:.0} comb/s", total as f64 / elapsed.max(0.001));

    if !found.load(Ordering::Relaxed) {
        println!("No match found in current search space.");
    }
}

fn check_candidate(
    indices: &[u16; 12],
    passphrase: &str,
    found: &AtomicBool,
    tested_count: &AtomicU64,
    valid_checksum_count: &AtomicU64,
    pb: &ProgressBar,
) -> bool {
    tested_count.fetch_add(1, Ordering::Relaxed);

    // Phase 1: Fast Checksum Filter (rejects 93.75% instantly!)
    if !fast_verify_checksum(indices) {
        return false;
    }

    valid_checksum_count.fetch_add(1, Ordering::Relaxed);
    let v_count = valid_checksum_count.load(Ordering::Relaxed);
    if v_count % 100 == 0 {
        pb.set_message(format!("{}", v_count));
        pb.set_position(tested_count.load(Ordering::Relaxed));
    }

    // Phase 2: Derive seed with PBKDF2 (2048 rounds)
    let phrase = indices_to_phrase(indices);
    let seed = mnemonic_to_seed(&phrase, passphrase);

    // Phase 3: Derive Bitcoin address and compare
    if let Some((path, addr)) = check_seed_matches_target(&seed) {
        found.store(true, Ordering::SeqCst);
        println!("\n🎯🎯🎯 TARGET WALLET FOUND! 🎯🎯🎯");
        println!("Mnemonic: {}", phrase);
        println!("Derivation Path: {}", path);
        println!("Target Address: {}", addr);
        println!("Passphrase: '{}'", passphrase);
        return true;
    }

    false
}

fn run_blocks_strategy(
    config: &SolverConfig,
    found: &Arc<AtomicBool>,
    tested_count: &Arc<AtomicU64>,
    valid_checksum_count: &Arc<AtomicU64>,
    pb: &ProgressBar,
) {
    let words = get_revolution_words();
    let occ = get_revolution_bip39_occurrences();
    println!("Strategy: Blocks (Window Dispersal)");
    println!("Total Revolution words: {}, BIP occurrences: {}", words.len(), occ.len());

    let block_sizes = if config.block_size > 0 {
        vec![config.block_size]
    } else {
        vec![10, 15, 20, 25, 30, 40, 50]
    };

    for b_size in block_sizes {
        if found.load(Ordering::Relaxed) {
            break;
        }
        let total_window = b_size * 12;
        if total_window > words.len() {
            println!("Block size {} (window {}) exceeds word count {}, skipping", b_size, total_window, words.len());
            continue;
        }

        let max_start = words.len() - total_window;
        println!("Testing Block Size: {} words (Window size: {}, start offsets: 0..{})", b_size, total_window, max_start);

        (0..=max_start).into_par_iter().for_each(|start_idx| {
            if found.load(Ordering::Relaxed) {
                return;
            }

            // Build 12 blocks
            let mut blocks: Vec<Vec<u16>> = Vec::with_capacity(12);
            for b in 0..12 {
                let b_start = start_idx + b * b_size;
                let b_end = b_start + b_size;
                let mut block_bip = Vec::new();
                for &(pos, idx, _) in &occ {
                    if pos >= b_start && pos < b_end {
                        block_bip.push(idx);
                    }
                }
                if block_bip.is_empty() {
                    return; // Can't form 12 words if one block has no BIP words
                }
                blocks.push(block_bip);
            }

            // Cartesian product of the 12 blocks
            let mut current = [0u16; 12];
            cartesian_product_helper(
                &blocks,
                0,
                &mut current,
                &config.passphrase,
                found,
                tested_count,
                valid_checksum_count,
                pb,
            );
        });
    }
}

fn cartesian_product_helper(
    blocks: &[Vec<u16>],
    depth: usize,
    current: &mut [u16; 12],
    passphrase: &str,
    found: &AtomicBool,
    tested_count: &AtomicU64,
    valid_checksum_count: &AtomicU64,
    pb: &ProgressBar,
) {
    if found.load(Ordering::Relaxed) {
        return;
    }

    if depth == 12 {
        check_candidate(
            current,
            passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
        return;
    }

    for &val in &blocks[depth] {
        current[depth] = val;
        cartesian_product_helper(
            blocks,
            depth + 1,
            current,
            passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
        if found.load(Ordering::Relaxed) {
            return;
        }
    }
}

fn run_order_preserving_strategy(
    config: &SolverConfig,
    found: &Arc<AtomicBool>,
    tested_count: &Arc<AtomicU64>,
    valid_checksum_count: &Arc<AtomicU64>,
    pb: &ProgressBar,
) {
    let occ = get_revolution_bip39_occurrences();
    println!("Strategy: Order-Preserving Combinations");
    println!("BIP occurrences: {}, Min Gap: {}, Max Gap: {}", occ.len(), config.min_gap, config.max_gap);

    // Parallelize by starting word index
    let n = occ.len();
    (0..n.saturating_sub(11)).into_par_iter().for_each(|start_i| {
        if found.load(Ordering::Relaxed) {
            return;
        }
        let mut chosen = [0u16; 12];
        chosen[0] = occ[start_i].1;
        dfs_order_preserving(
            &occ,
            start_i,
            1,
            &mut chosen,
            config.min_gap,
            config.max_gap,
            &config.passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
    });
}

fn dfs_order_preserving(
    occ: &[(usize, u16, String)],
    last_i: usize,
    depth: usize,
    chosen: &mut [u16; 12],
    min_gap: usize,
    max_gap: usize,
    passphrase: &str,
    found: &AtomicBool,
    tested_count: &AtomicU64,
    valid_checksum_count: &AtomicU64,
    pb: &ProgressBar,
) {
    if found.load(Ordering::Relaxed) {
        return;
    }

    if depth == 12 {
        check_candidate(
            chosen,
            passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
        return;
    }

    let remaining_needed = 12 - depth;
    let start = last_i + min_gap;
    let end = (last_i + max_gap + 1).min(occ.len().saturating_sub(remaining_needed - 1));

    for next_i in start..end {
        chosen[depth] = occ[next_i].1;
        dfs_order_preserving(
            occ,
            next_i,
            depth + 1,
            chosen,
            min_gap,
            max_gap,
            passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
        if found.load(Ordering::Relaxed) {
            return;
        }
    }
}

fn run_paragraphs_strategy(
    config: &SolverConfig,
    found: &Arc<AtomicBool>,
    tested_count: &Arc<AtomicU64>,
    valid_checksum_count: &Arc<AtomicU64>,
    pb: &ProgressBar,
) {
    println!("Strategy: Paragraph-Distributed Combinations (9 Paragraphs -> 12 words)");
    // Extract BIP words for each of the 9 paragraphs
    let mut para_bip: Vec<Vec<u16>> = Vec::new();
    for p in REVOLUTION_PARAGRAPHS {
        let mut words_in_p = Vec::new();
        for w in p.split_whitespace() {
            let clean: String = w.chars().filter(|c| c.is_alphabetic()).flat_map(|c| c.to_lowercase()).collect();
            if let Some(idx) = crate::bip39::word_index(&clean) {
                words_in_p.push(idx);
            }
        }
        para_bip.push(words_in_p);
    }

    for (i, b) in para_bip.iter().enumerate() {
        println!("  P{} BIP-39 words: {}", i, b.len());
    }

    // Paragraph count allocations that sum to 12 across 9 paragraphs:
    // e.g. [2, 2, 2, 1, 1, 1, 1, 1, 1] (and permutations) or [1, 1, 1, 1, 1, 1, 2, 2, 2]
    // Run order-preserving with min_gap=1, max_gap=15
    println!("Running with dynamic paragraph distribution...");
    let occ = get_revolution_bip39_occurrences();
    (0..occ.len().saturating_sub(11)).into_par_iter().for_each(|start_i| {
        let mut chosen = [0u16; 12];
        chosen[0] = occ[start_i].1;
        dfs_order_preserving(
            &occ,
            start_i,
            1,
            &mut chosen,
            1,
            12,
            &config.passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
    });
}

fn run_dispersal12_strategy(
    config: &SolverConfig,
    found: &Arc<AtomicBool>,
    tested_count: &Arc<AtomicU64>,
    valid_checksum_count: &Arc<AtomicU64>,
    pb: &ProgressBar,
) {
    println!("Strategy: 12-Story Dispersal Blocks Sweep (Exhaustive 10.74T Search)");
    println!("Block sizes: [10, 7, 7, 13, 8, 8, 4, 10, 12, 7, 12, 13]");
    let mut total_combos: u64 = 1;
    for b in &DISPERSAL_12_BLOCKS {
        total_combos *= b.len() as u64;
    }
    println!("Total Combinations: {} (~10.74 Trillion)", total_combos);

    // Parallelize across the first 2 blocks (10 * 7 = 70 tasks)
    let b0 = DISPERSAL_12_BLOCKS[0];
    let b1 = DISPERSAL_12_BLOCKS[1];
    let tasks: Vec<(u16, u16)> = b0
        .iter()
        .flat_map(|&w0| b1.iter().map(move |&w1| (w0, w1)))
        .collect();

    tasks.into_par_iter().for_each(|(w0, w1)| {
        if found.load(Ordering::Relaxed) {
            return;
        }
        let mut candidate = [0u16; 12];
        candidate[0] = w0;
        candidate[1] = w1;

        dfs_dispersal12(
            2,
            &mut candidate,
            &config.passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
    });
}

fn dfs_dispersal12(
    depth: usize,
    candidate: &mut [u16; 12],
    passphrase: &str,
    found: &AtomicBool,
    tested_count: &AtomicU64,
    valid_checksum_count: &AtomicU64,
    pb: &ProgressBar,
) {
    if found.load(Ordering::Relaxed) {
        return;
    }

    if depth == 12 {
        check_candidate(
            candidate,
            passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
        return;
    }

    for &val in DISPERSAL_12_BLOCKS[depth] {
        candidate[depth] = val;
        dfs_dispersal12(
            depth + 1,
            candidate,
            passphrase,
            found,
            tested_count,
            valid_checksum_count,
            pb,
        );
        if found.load(Ordering::Relaxed) {
            return;
        }
    }
}
