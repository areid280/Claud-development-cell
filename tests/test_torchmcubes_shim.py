from __future__ import annotations

import pytest


def test_shim_returns_xyz_like_torchmcubes() -> None:
    torch = pytest.importorskip("torch")
    pytest.importorskip("mcubes")
    from avatar_forge.models.vendor_shims.torchmcubes import marching_cubes

    # A box occupying z in [2, 5], y in [2, 9], x in [2, 13] of a volume indexed [z, y, x].
    volume = torch.zeros((8, 12, 16))
    volume[2:6, 2:10, 2:14] = 1.0

    vertices, faces = marching_cubes(volume, 0.5)

    extent = vertices.max(dim=0).values - vertices.min(dim=0).values
    # (x, y, z) order: x spans the longest axis, z the shortest.
    assert extent[0] > extent[1] > extent[2]
    assert faces.shape[1] == 3 and faces.dtype == torch.int64
