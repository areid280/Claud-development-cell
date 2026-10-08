"""Drop-in replacement for `torchmcubes.marching_cubes`, backed by PyMCubes (E-016).

torchmcubes does not compile against CUDA 12.4 (its `lerp` clashes with `std::lerp`). TripoSR only
calls `marching_cubes(volume, threshold)`, so the TripoSR wrapper puts this directory on `sys.path`
before importing `tsr`.

torchmcubes reads `volume[z, y, x]` and returns vertices as (x, y, z); PyMCubes returns vertices in
array-index order (z, y, x). The columns are therefore reversed to match torchmcubes exactly.
"""

from __future__ import annotations

from typing import Any


def marching_cubes(volume: Any, threshold: float) -> tuple[Any, Any]:
    import mcubes
    import numpy as np
    import torch

    vertices, faces = mcubes.marching_cubes(volume.detach().float().cpu().numpy(), float(threshold))
    vertices = np.ascontiguousarray(vertices[:, ::-1], dtype=np.float32)
    return (
        torch.from_numpy(vertices).to(volume.device),
        torch.from_numpy(faces.astype(np.int64)).to(volume.device),
    )
