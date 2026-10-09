from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import trimesh
from PIL import Image

from avatar_forge.blender_runner import run_blender
from avatar_forge.core.config import load_pipeline_config
from avatar_forge.core.paths import REPO_ROOT
from avatar_forge.models.i23d_triposr import TripoSR
from avatar_forge.models.trials import register

PARSING_CANDIDATES = ("florence2-plus-sam", "sapiens-seg", "segformer-clothes")
GARMENT_LABELS = ("boots", "jacket", "shoes")


def _garment_crop(
    cutout: Image.Image, trial_root: Path, image_stem: str
) -> tuple[Image.Image, str]:
    for candidate in PARSING_CANDIDATES:
        candidate_dir = trial_root / "parsing" / candidate / image_stem
        trial_path = candidate_dir / "trial.json"
        if not trial_path.is_file():
            continue
        trial = json.loads(trial_path.read_text(encoding="utf-8"))
        if not trial.get("ok"):
            continue

        for label in GARMENT_LABELS:
            mask_path = candidate_dir / "masks" / f"{label}.png"
            if not mask_path.is_file():
                continue
            with Image.open(mask_path) as source_mask:
                mask = np.asarray(source_mask.convert("L")) > 0
            if mask.shape != (cutout.height, cutout.width):
                raise ValueError(
                    f"Mask size for {candidate}/{label}/{image_stem} "
                    f"does not match BiRefNet cut-out"
                )
            ys, xs = np.nonzero(mask)
            if len(xs) == 0:
                continue

            pad_x = max(1, round((int(xs.max()) - int(xs.min()) + 1) * 0.1))
            pad_y = max(1, round((int(ys.max()) - int(ys.min()) + 1) * 0.1))
            left = max(0, int(xs.min()) - pad_x)
            top = max(0, int(ys.min()) - pad_y)
            right = min(cutout.width, int(xs.max()) + 1 + pad_x)
            bottom = min(cutout.height, int(ys.max()) + 1 + pad_y)

            rgba = np.asarray(cutout.convert("RGBA")).copy()
            alpha = rgba[..., 3]
            alpha[~mask] = 0
            cropped = Image.fromarray(rgba, mode="RGBA").crop((left, top, right, bottom))
            return cropped, f"{candidate}/{label}"

    raise FileNotFoundError(
        f"No non-empty boots, jacket, or shoes mask found for {image_stem}"
    )


def _mesh_metrics(glb_path: Path) -> dict[str, int | bool]:
    scene = trimesh.load(glb_path, force="scene")
    meshes = [
        geometry
        for geometry in scene.geometry.values()
        if isinstance(geometry, trimesh.Trimesh)
    ]
    if not meshes:
        raise ValueError(f"GLB contains no triangle meshes: {glb_path}")
    return {
        "triangle_count": sum(len(mesh.faces) for mesh in meshes),
        "watertight": all(mesh.is_watertight for mesh in meshes),
    }


def _render_previews(glb_path: Path, out_dir: Path) -> dict[str, str]:
    preview_dir = out_dir / f"{glb_path.stem}_previews"
    run_blender(
        REPO_ROOT / "src/avatar_forge/blender/render_previews.py",
        ["--in", str(glb_path), "--out-dir", str(preview_dir)],
        load_pipeline_config(),
        log_path=out_dir / f"{glb_path.stem}_previews.log",
    )
    return {
        view: str(preview_dir / f"{view}.png")
        for view in ("front", "back")
    }


@register("image_to_3d", "triposr")
def trial_triposr(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    trial_root = out_dir.parents[2]
    cutout_path = trial_root / "bg_remove" / "birefnet" / image_path.stem / "cutout.png"
    if not cutout_path.is_file():
        raise FileNotFoundError(f"BiRefNet cut-out required: {cutout_path}")

    with Image.open(cutout_path) as source:
        cutout = source.convert("RGBA")
    garment, mask_source = _garment_crop(cutout, trial_root, image_path.stem)

    with TripoSR(entry) as model:
        full_path = model.predict(cutout, out_dir, seed=0)
        garment_path = model.predict(
            garment, out_dir, seed=0, output_name="garment.glb"
        )

    full_metrics = _mesh_metrics(full_path)
    garment_metrics = _mesh_metrics(garment_path)
    full_previews = _render_previews(full_path, out_dir)
    garment_previews = _render_previews(garment_path, out_dir)
    return {
        "full_glb": str(full_path),
        "full": full_metrics,
        "full_previews": full_previews,
        "garment_glb": str(garment_path),
        "garment": garment_metrics,
        "garment_mask_source": mask_source,
        "garment_previews": garment_previews,
    }
