from __future__ import annotations

import numpy as np

from avatar_forge.models.mesh_axes import Z_UP_TO_Y_UP, z_up_to_y_up


def test_z_up_head_becomes_y_up_and_front_stays_front() -> None:
    head = np.array([[0.0, 0.0, 1.0]])   # Z-up: head above the origin
    front = np.array([[0.0, -1.0, 0.0]])  # Z-up convention: facing -Y
    assert np.allclose(z_up_to_y_up(head), [[0.0, 1.0, 0.0]])    # now +Y (glTF up)
    assert np.allclose(z_up_to_y_up(front), [[0.0, 0.0, 1.0]])   # now +Z (glTF forward)


def test_transform_is_a_proper_rotation() -> None:
    assert np.isclose(np.linalg.det(Z_UP_TO_Y_UP[:3, :3]), 1.0)
