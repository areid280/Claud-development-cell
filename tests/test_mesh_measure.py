from __future__ import annotations

import numpy as np
import pytest

trimesh = pytest.importorskip("trimesh")  # models extra; CI installs only [dev]
pytest.importorskip("scipy")  # trimesh's mesh sections need scipy
pytest.importorskip("networkx")  # ... and networkx

from avatar_forge.body.mesh_measure import measure_mesh  # noqa: E402 (after the skips)


def _config() -> dict:
    return {
        "stages": {
            "s04_body_fit": {
                "mesh_slice": {
                    "bust": 0.72,
                    "underbust": 0.68,
                    "waist_range": [0.58, 0.66],
                    "hips_range": [0.46, 0.54],
                    "range_steps": 9,
                }
            }
        }
    }


def _measure(mesh: trimesh.Trimesh) -> dict[str, float]:
    return measure_mesh(mesh.vertices, mesh.faces, 180.0, _config())


def test_cylinder_circumferences_scale_to_requested_height() -> None:
    radius, source_height, height_cm = 1.25, 5.0, 180.0
    cylinder = trimesh.creation.cylinder(radius=radius, height=source_height)

    measurements = _measure(cylinder)
    expected = 2 * np.pi * radius * height_cm / source_height

    for key in ("bust", "underbust", "waist", "hips"):
        assert abs(measurements[key] - expected) / expected <= 0.02
    assert measurements["height"] == height_cm


def test_central_torso_loop_is_chosen_with_arm_loops() -> None:
    torso = trimesh.creation.cylinder(radius=1.0, height=5.0)
    left_arm = trimesh.creation.cylinder(radius=0.15, height=5.0)
    right_arm = left_arm.copy()
    left_arm.apply_translation([-1.4, 0.0, 0.0])
    right_arm.apply_translation([1.4, 0.0, 0.0])
    mesh = trimesh.util.concatenate((torso, left_arm, right_arm))

    measurements = _measure(mesh)
    expected = 2 * np.pi * 180.0 / 5.0

    for key in ("bust", "underbust", "waist", "hips"):
        assert abs(measurements[key] - expected) / expected <= 0.02
