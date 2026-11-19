mod bip39;
mod crypto;
mod data;
mod solver;

use clap::Parser;
use solver::{run_cpu_solver, SolverConfig, Strategy};

#[derive(Parser, Debug)]
#[command(author, version, about = "High-Performance Revolution Solver for Wealth in Poetry BTC Puzzle")]
struct Args {
    /// Strategy to use: blocks, order-preserving, paragraphs, dispersal
    #[arg(short, long, default_value = "dispersal")]
    strategy: String,

    /// Block size for blocks strategy (0 to auto-test sizes 10, 15, 20, 25, 30, 40, 50)
    #[arg(short, long, default_value_t = 0)]
    block_size: usize,

    /// Minimum word gap for order-preserving strategy
    #[arg(long, default_value_t = 1)]
    min_gap: usize,

    /// Maximum word gap for order-preserving strategy
    #[arg(long, default_value_t = 15)]
    max_gap: usize,

    /// Optional BIP-39 passphrase
    #[arg(short, long, default_value = "")]
    passphrase: String,

    /// Number of CPU threads (0 = auto / all physical+logical cores)
    #[arg(short, long, default_value_t = 0)]
    threads: usize,
}

fn main() {
    let args = Args::parse();

    if args.threads > 0 {
        rayon::ThreadPoolBuilder::new()
            .num_threads(args.threads)
            .build_global()
            .unwrap();
    }

    let strat = match args.strategy.to_lowercase().as_str() {
        "blocks" | "block" => Strategy::Blocks,
        "order" | "order-preserving" | "subseq" => Strategy::OrderPreserving,
        "para" | "paragraphs" => Strategy::Paragraphs,
        "dispersal" | "dispersal12" | "sweep" => Strategy::Dispersal12,
        _ => {
            eprintln!("Unknown strategy: {}. Available: blocks, order-preserving, paragraphs, dispersal", args.strategy);
            std::process::exit(1);
        }
    };

    println!("============================================================");
    println!("  WEALTH IN POETRY: REVOLUTION SECTION SOLVER (RUST + GPU)");
    println!("  Target BTC Address: {}", crypto::TARGET_ADDRESS);
    println!("  Target Hash160:     {}", hex::encode(crypto::TARGET_HASH160));
    println!("  Passphrase:         '{}'", args.passphrase);
    println!("  CPU Threads:        {}", rayon::current_num_threads());
    println!("============================================================\n");

    let config = SolverConfig {
        strategy: strat,
        block_size: args.block_size,
        min_gap: args.min_gap,
        max_gap: args.max_gap,
        passphrase: args.passphrase,
    };

    run_cpu_solver(config);
}
