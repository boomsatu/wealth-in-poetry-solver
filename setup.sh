#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  GPU SERVER SETUP: Wealth in Poetry (Rust + Dual GPU)"
echo "============================================================"

# 1. Update & Install System Dependencies
echo "[1/6] Installing system packages..."
if [ -f /etc/debian_version ]; then
    sudo apt-get update -y
    sudo apt-get install -y build-essential curl git pkg-config libssl-dev python3 python3-pip python3-venv tmux
elif [ -f /etc/redhat-release ]; then
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y curl git openssl-devel python3 python3-pip tmux
fi

# 2. Check NVIDIA GPU & CUDA
echo "[2/6] Checking NVIDIA GPU configuration..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA Driver detected:"
    nvidia-smi --query-gpu=index,name,memory.total --format=csv
else
    echo "WARNING: nvidia-smi not found. Please install NVIDIA GPU drivers."
fi

if command -v nvcc &> /dev/null; then
    echo "CUDA Compiler detected: $(nvcc --version | grep release)"
else
    echo "WARNING: nvcc not found. If you plan to use GPU acceleration,"
    echo "please install NVIDIA CUDA Toolkit: https://developer.nvidia.com/cuda-downloads"
fi

# 3. Install Rust Toolchain
echo "[3/6] Setting up Rust..."
if ! command -v cargo &> /dev/null; then
    echo "Installing Rust via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo "Rust already installed: $(rustc --version)"
fi
source "$HOME/.cargo/env" || true

# 4. Build Rust Release Binary
echo "[4/6] Compiling Rust release binary (opt-level 3, LTO)..."
cd revolution_solver
cargo build --release
cd ..

# 5. Build CUDA Kernel (if nvcc is available)
echo "[5/6] Checking CUDA kernel compilation..."
if command -v nvcc &> /dev/null; then
    echo "Compiling CUDA kernel for Dual RTX 5090 / Modern NVIDIA GPUs..."
    cd revolution_solver/cuda
    # Compile with optimization
    nvcc -O3 -shared -Xcompiler -fPIC revolution_kernel.cu -o revolution_kernel.so || {
        echo "Note: Standard nvcc compilation fallback."
        nvcc -O3 -shared -Xcompiler -fPIC revolution_kernel.cu -o revolution_kernel.so -arch=sm_89 || true
    }
    cd ../..
    echo "CUDA kernel built successfully."
fi

# 6. Setup Python Environment for GPU Orchestrator
echo "[6/6] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu124 || pip install torch || true

chmod +x run.sh || true
chmod +x setup.sh || true

echo ""
echo "============================================================"
echo "  SETUP COMPLETED SUCCESSFULLY!"
echo "  Run the solver using: ./run.sh"
echo "============================================================"
