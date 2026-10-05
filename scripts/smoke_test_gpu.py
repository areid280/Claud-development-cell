"""Quick GPU sanity check: device, VRAM, and a timed matrix multiply. Exit code 0 = pass."""

from __future__ import annotations

import sys
import time


def main() -> int:
    try:
        import torch
    except ImportError:
        print("FAIL: torch is not installed")
        return 1
    if not torch.cuda.is_available():
        print("FAIL: CUDA not available")
        return 1
    props = torch.cuda.get_device_properties(0)
    vram_gb = props.total_memory / 1e9
    print(f"GPU: {props.name}  VRAM: {vram_gb:.1f} GB")
    print(f"torch {torch.__version__}  CUDA {torch.version.cuda}")
    a = torch.randn(8192, 8192, device="cuda", dtype=torch.float16)
    b = torch.randn(8192, 8192, device="cuda", dtype=torch.float16)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(10):
        _ = a @ b
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    tflops = 10 * 2 * 8192**3 / dt / 1e12
    print(f"matmul fp16: {dt:.3f}s for 10 iters (~{tflops:.0f} TFLOPS)")
    if vram_gb < 20:
        print("WARN: less than 20 GB VRAM; some image-to-3D models may not fit")
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
