"""Axis conventions for exported meshes.

TripoSR and TRELLIS produce Z-up meshes, but glTF/GLB (and therefore Blender's importer, UE5's
glTF importer and every viewer) expects Y-up. Every wrapper converts before writing a GLB, so
downstream code never guesses orientation (E-018).
"""

from __future__ import annotations

import numpy as np

# Rotation of -90 degrees about X: (x, y, z) -> (x, z, -y). Z-up becomes Y-up, front stays front.
Z_UP_TO_Y_UP = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)


def z_up_to_y_up(vertices: np.ndarray) -> np.ndarray:
    """Return (N, 3) vertices converted from Z-up to glTF's Y-up."""
    return np.asarray(vertices, dtype=np.float64) @ Z_UP_TO_Y_UP[:3, :3].T
