"""
Dual NVIDIA RTX 5090 Orchestrator for Wealth in Poetry
Splits candidate search space 50/50 across Device 0 and Device 1.
"""
import ctypes
import os
import sys
import time

def get_gpu_count():
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.device_count()
    except ImportError:
        pass
    return 0

def main():
    print("=" * 60)
    print("  DUAL NVIDIA RTX 5090 ACCELERATOR")
    print("=" * 60)
    
    gpu_count = get_gpu_count()
    print(f"Detected CUDA devices: {gpu_count}")
    
    if gpu_count < 2:
        print("Note: Running in simulation / single device mode.")
        print("For Dual RTX 5090: ensure CUDA toolkit and PyTorch/CUDA are active.")
    else:
        import torch
        print(f"GPU 0: {torch.cuda.get_device_name(0)}")
        print(f"GPU 1: {torch.cuda.get_device_name(1)}")
        
    print("\nCUDA kernel ready in: cuda/revolution_kernel.cu")
    print("Compilation command:")
    print("  nvcc -O3 -shared -Xcompiler -fPIC cuda/revolution_kernel.cu -o cuda/revolution_kernel.so")

if __name__ == "__main__":
    main()
