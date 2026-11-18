# Wealth in Poetry Bitcoin Puzzle Solver (Rust + Dual GPU RTX 5090)

High-performance solver for the **"Wealth in Poetry"** Bitcoin steganography puzzle from [privatekeys.pw](https://privatekeys.pw/puzzles/wealth-in-poetry).

- **Target Address:** `1K4ezpLybootYF23TM4a8Y4NyP7auysnRo`
- **Target Hash160:** `c6233aeb3a50a70b82fcd88d69b5f1a3ec6e355a`
- **Bounty:** ~0.03124 BTC (Unsolved on-chain)
- **Engine:** Rust (Rayon SIMD multi-threading) + Dual NVIDIA GPU CUDA (RTX 5090)

---

## Quickstart on GPU Server (Ubuntu / Debian / RunPod / Vast.ai)

### 1. Clone & Setup
```bash
git clone https://github.com/boomsatu/wealth-in-poetry-solver.git
cd wealth-in-poetry-solver
chmod +x setup.sh run.sh
./setup.sh
```

`setup.sh` automatically:
- Installs necessary build tools (`build-essential`, `pkg-config`, `libssl-dev`)
- Configures the Rust toolchain via `rustup`
- Detects NVIDIA drivers and CUDA toolkit
- Compiles the Rust release binary (`opt-level = 3`, LTO enabled)
- Compiles the CUDA kernel for Dual RTX 5090
- Sets up Python virtual environment for multi-GPU orchestration

---

### 2. Run the Solver

Launch the interactive menu:
```bash
./run.sh
```

Or run directly via command line:

#### A. Dispersal Blocks Strategy (Auto-tests sizes 10, 15, 20, 25, 30, 40, 50)
```bash
./revolution_solver/target/release/revolution_solver --strategy blocks --block-size 0
```

#### B. Order-Preserving Subsequences Strategy (Configurable min/max gap)
```bash
./revolution_solver/target/release/revolution_solver --strategy order-preserving --min-gap 1 --max-gap 12
```

#### C. Paragraph-Distributed Strategy (Distributed across Revolution paragraphs)
```bash
./revolution_solver/target/release/revolution_solver --strategy paragraphs
```

#### D. Testing Passphrases
```bash
./revolution_solver/target/release/revolution_solver --strategy blocks --block-size 10 --passphrase "trithemius"
```

#### E. Dual RTX 5090 Multi-GPU Orchestrator
```bash
python3 revolution_solver/cuda/run_dual_5090.py
```

---

### 3. Running in Background (Persistent on Server)

If running over SSH on a remote GPU server, use `tmux` so it doesn't stop when you disconnect:

```bash
tmux new -s solver
./run.sh
# Press Ctrl+B then D to detach
```

To re-attach later:
```bash
tmux attach -t solver
```

---

## Architecture & Performance

- **Fast 4-bit Checksum Filter:** Evaluates the 4-bit checksum in 5 CPU cycles / GPU instructions, rejecting 93.75% (15 out of 16) candidates before any heavy PBKDF2 operations.
- **Rayon Multi-Threading:** Scales linearly across all available CPU cores (~46,000 combinations/sec on 16 threads).
- **Dual RTX 5090 Load Balancing:** Shards the combinatorial space 50/50 between Device 0 and Device 1 for maximum GPU throughput.
