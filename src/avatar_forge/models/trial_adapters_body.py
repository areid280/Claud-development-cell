from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from avatar_forge.blender_runner import run_blender
from avatar_forge.body.keypoint_ratio import measure
from avatar_forge.body.mesh_measure import measure_mesh
from avatar_forge.core.config import load_pipeline_config, load_yaml
from avatar_forge.core.paths import REPO_ROOT
from avatar_forge.models.body_measure_sam3d_body import SAM3DBody
from avatar_forge.models.mesh_axes import z_up_to_y_up
from avatar_forge.models.pose_rtmlib_rtmw import RTMLibRTMW
from avatar_forge.models.trials import TrialSkippedError, register

REFERENCE_PATH = REPO_ROOT / "samples" / "reference.yaml"


@register("body_measure", "keypoint-ratio")
def trial_keypoint_ratio(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    trial_root = out_dir.parents[2]
    cutout_path = (
        trial_root / "bg_remove" / "birefnet" / image_path.stem / "cutout.png"
    )
    keypoints_path = (
        trial_root / "pose" / "rtmlib-rtmw" / image_path.stem / "keypoints.json"
    )
    if not cutout_path.is_file():
        raise FileNotFoundError(
            f"BiRefNet cut-out required for keypoint-ratio trial: {cutout_path}"
        )

    with Image.open(image_path) as source_image:
        image = source_image.convert("RGB")
    with Image.open(cutout_path) as source_cutout:
        cutout = source_cutout.convert("RGBA")
    if cutout.size != image.size:
        raise ValueError(
            f"BiRefNet cut-out size {cutout.size} does not match input {image.size}"
        )

    references = load_yaml(REFERENCE_PATH) if REFERENCE_PATH.is_file() else {}
    reference = references.get(image_path.stem, {})
    cfg = load_pipeline_config()
    body_cfg = cfg["stages"]["s04_body_fit"]
    height_cm = float(reference.get("height", body_cfg["default_height_cm"]))

    if keypoints_path.is_file():
        with keypoints_path.open(encoding="utf-8") as keypoints_file:
            people = json.load(keypoints_file)
    else:
        with RTMLibRTMW(entry) as pose_model:
            people = pose_model.predict(image)
    if not people:
        raise ValueError(f"Pose model found no people in {image_path}")
    person = max(people, key=lambda candidate: candidate["score"])
    alpha = np.asarray(cutout.getchannel("A"))
    measurements = measure(person["keypoints"], alpha, height_cm, cfg)

    output = {
        "units": "cm",
        "source": "trial:keypoint-ratio",
        "measurements": measurements,
    }
    measurements_path = out_dir / "measurements.json"
    measurements_path.write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "measurements": str(measurements_path),
        "height_cm": height_cm,
        "measurement_values_cm": measurements,
    }


def _write_mesh_trial(
    wrapper_type: type[Any],
    entry: dict[str, Any],
    image_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    trial_root = out_dir.parents[2]
    cutout_path = (
        trial_root / "bg_remove" / "birefnet" / image_path.stem / "cutout.png"
    )
    if not cutout_path.is_file():
        raise FileNotFoundError(f"BiRefNet cut-out required: {cutout_path}")

    with Image.open(cutout_path) as source:
        cutout = source.convert("RGBA")
    cfg = load_pipeline_config()
    body_cfg = cfg["stages"]["s04_body_fit"]
    references = load_yaml(REFERENCE_PATH) if REFERENCE_PATH.is_file() else {}
    reference = references.get(image_path.stem, {})
    height_cm = float(reference.get("height", body_cfg["default_height_cm"]))

    with wrapper_type(entry) as model:
        vertices, faces, joints = model.predict(cutout)
    measurements = measure_mesh(vertices, faces, height_cm, cfg)
    if joints is not None:
        required_joints = (
            "left_shoulder",
            "right_shoulder",
            "left_hip",
            "right_hip",
            "left_ankle",
            "right_ankle",
        )
        if any(name not in joints for name in required_joints):
            raise ValueError("3D joints are missing shoulder, hip, or ankle points")
        joint_scale = height_cm / float(np.ptp(vertices, axis=0).max())
        shoulder_span = np.linalg.norm(
            np.asarray(joints["right_shoulder"]) - np.asarray(joints["left_shoulder"])
        )
        left_leg = np.linalg.norm(
            np.asarray(joints["left_ankle"]) - np.asarray(joints["left_hip"])
        )
        right_leg = np.linalg.norm(
            np.asarray(joints["right_ankle"]) - np.asarray(joints["right_hip"])
        )
        measurements["shoulder_width"] = float(shoulder_span * 1.15 * joint_scale)
        measurements["inseam"] = float(
            (left_leg + right_leg) / 2 * 0.92 * joint_scale
        )

    output_mesh = np.asarray(vertices, dtype=np.float64)
    up_axis = int(np.argmax(np.ptp(output_mesh, axis=0)))
    if up_axis == 2:
        output_mesh = z_up_to_y_up(output_mesh)
    elif up_axis != 1:
        raise ValueError(f"Cannot export mesh with axis {up_axis} as glTF Y-up")

    out_dir.mkdir(parents=True, exist_ok=True)
    mesh_path = out_dir / "mesh.glb"
    import trimesh

    trimesh.Trimesh(vertices=output_mesh, faces=faces, process=False).export(mesh_path)
    measurements_path = out_dir / "measurements.json"
    measurements_path.write_text(
        json.dumps(
            {
                "units": "cm",
                "source": f"trial:{entry['name']}",
                "measurements": measurements,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    preview_dir = out_dir / "previews"
    run_blender(
        REPO_ROOT / "src/avatar_forge/blender/render_previews.py",
        ["--in", str(mesh_path), "--out-dir", str(preview_dir)],
        cfg,
        log_path=out_dir / "previews.log",
    )
    return {
        "measurements": str(measurements_path),
        "measurement_values_cm": measurements,
        "mesh_glb": str(mesh_path),
        "front": str(preview_dir / "front.png"),
        "back": str(preview_dir / "back.png"),
        "height_cm": height_cm,
    }


@register("body_measure", "sam-3d-body")
def trial_sam3d_body(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _write_mesh_trial(SAM3DBody, entry, image_path, out_dir)


@register("body_measure", "smpler-x")
def trial_smpler_x(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    raise TrialSkippedError("needs owner SMPL-X registration")
