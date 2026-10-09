"""Make ONNX Runtime actually use the GPU (E-020).

onnxruntime-gpu needs CUDA 12 / cuDNN 9 shared libraries at session-creation time. On the pod they
come from the template's PyTorch wheels (nvidia-* packages), not from the system. If they are not
found, ONNX Runtime silently falls back to CPU. Call `prepare_onnxruntime_cuda()` before creating
any session, and `cuda_session_works()` to verify (used by setup_pod.sh and tests).
"""

from __future__ import annotations

import contextlib
from pathlib import Path

PROBE_MODEL = Path(__file__).parent / "data" / "probe_relu.onnx"


def prepare_onnxruntime_cuda() -> None:
    """Load the CUDA 12 runtime libraries that ship with PyTorch into this process."""
    with contextlib.suppress(ImportError):
        import torch  # noqa: F401  (importing torch loads its bundled libcublas/libcudnn)
    import onnxruntime

    preload = getattr(onnxruntime, "preload_dlls", None)  # onnxruntime >= 1.21
    if preload is not None:
        with contextlib.suppress(Exception):  # best effort; cuda_session_works() reports it
            preload()


def cuda_session_works() -> bool:
    """True only if a real session runs on CUDAExecutionProvider (no silent CPU fallback)."""
    prepare_onnxruntime_cuda()
    import onnxruntime

    session = onnxruntime.InferenceSession(
        str(PROBE_MODEL), providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
    )
    return session.get_providers()[0] == "CUDAExecutionProvider"
