#!/usr/bin/env bash
set -e

# Ensure Rust environment is loaded
source "$HOME/.cargo/env" 2>/dev/null || true
if [ -d "venv" ]; then
    source venv/bin/activate
fi

BINARY="./revolution_solver/target/release/revolution_solver"

# Fallback if inside revolution_solver folder
if [ ! -f "$BINARY" ] && [ -f "./target/release/revolution_solver" ]; then
    BINARY="./target/release/revolution_solver"
fi

if [ ! -f "$BINARY" ]; then
    echo "Binary not found. Compiling first..."
    cd revolution_solver && cargo build --release && cd ..
fi

echo "============================================================"
echo "  WEALTH IN POETRY SOLVER - RUNNER"
echo "  Target: 1K4ezpLybootYF23TM4a8Y4NyP7auysnRo"
echo "============================================================"
echo ""
echo "Select execution mode:"
echo "  1) Rust Multi-Threaded: Dispersal Blocks (auto-test 10,15,20,25,30,40,50)"
echo "  2) Rust Multi-Threaded: Order-Preserving (gap 1 to 12)"
echo "  3) Rust Multi-Threaded: Paragraph-Distributed"
echo "  4) Dual RTX 5090 GPU Orchestrator (Device 0 & Device 1)"
echo "  5) Background Execution with tmux (continues if SSH closes)"
echo "  6) Custom command"
echo ""

read -p "Enter choice [1-6] (default: 1): " CHOICE
CHOICE=${CHOICE:-1}

case "$CHOICE" in
    1)
        echo "Running Strategy: Blocks..."
        "$BINARY" --strategy blocks --block-size 0
        ;;
    2)
        echo "Running Strategy: Order-Preserving..."
        "$BINARY" --strategy order-preserving --min-gap 1 --max-gap 12
        ;;
    3)
        echo "Running Strategy: Paragraphs..."
        "$BINARY" --strategy paragraphs
        ;;
    4)
        echo "Running Dual RTX 5090 GPU Orchestrator..."
        if [ -f "revolution_solver/cuda/run_dual_5090.py" ]; then
            python3 revolution_solver/cuda/run_dual_5090.py
        else
            python3 cuda/run_dual_5090.py
        fi
        ;;
    5)
        echo "Launching in background via tmux session 'btc-solver'..."
        tmux new-session -d -s btc-solver "$BINARY --strategy blocks --block-size 0 | tee solver.log"
        echo "Solver is running in background!"
        echo "To attach: tmux attach -t btc-solver"
        echo "To view logs: tail -f solver.log"
        ;;
    6)
        read -p "Enter custom arguments (e.g., --strategy blocks --block-size 15 --passphrase trithemius): " CUSTOM_ARGS
        "$BINARY" $CUSTOM_ARGS
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
