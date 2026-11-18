#!/usr/bin/env bash
set -e

# Ensure Rust environment is loaded
source "$HOME/.cargo/env" 2>/dev/null || true

BINARY="./revolution_solver/target/release/revolution_solver"
if [ ! -f "$BINARY" ] && [ -f "./target/release/revolution_solver" ]; then
    BINARY="./target/release/revolution_solver"
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
echo "  4) Dual NVIDIA RTX 5090 GPU Solver (100 Billion Candidates, sm_120)"
echo "  5) Background Execution with tmux (continues if SSH closes)"
echo "  6) Custom command"
echo ""

read -p "Enter choice [1-6] (default: 4): " CHOICE
CHOICE=${CHOICE:-4}

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
        echo "Running Dual NVIDIA RTX 5090 GPU Solver..."
        cd revolution_solver/cuda
        echo "Compiling native CUDA for Dual RTX 5090 (Blackwell sm_120)..."
        nvcc -O3 -std=c++17 gpu_solver.cu -o gpu_solver
        ./gpu_solver
        cd ../..
        ;;
    5)
        echo "Launching in background via tmux session 'btc-solver'..."
        tmux new-session -d -s btc-solver "$BINARY --strategy blocks --block-size 0 | tee solver.log"
        echo "Solver is running in background!"
        echo "To attach: tmux attach -t btc-solver"
        echo "To view logs: tail -f solver.log"
        ;;
    6)
        read -p "Enter custom arguments: " CUSTOM_ARGS
        "$BINARY" $CUSTOM_ARGS
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
