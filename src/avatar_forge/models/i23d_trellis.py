from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

from avatar_forge.models.base import ModelWrapper

TRELLIS_SOURCE = Path("/opt/src/TRELLIS")


def _export_mesh_glb(mesh: object, mesh_path: Path) -> None:
    vertices = mesh.vertices.detach().cpu().numpy()
    faces = mesh.faces.detach().cpu().numpy()
    vertex_attrs = mesh.vertex_attrs
    if vertex_attrs is None or vertex_attrs.shape[0] != vertices.shape[0]:
        raise ValueError("TRELLIS mesh has no per-vertex appearance attributes")
    colors = vertex_attrs.detach().cpu().numpy()
    if colors.ndim != 2 or colors.shape[1] < 3:
        raise ValueError(f"Unexpected TRELLIS vertex color shape: {colors.shape}")
    colors = np.clip(colors[:, :3] * 255.0, 0, 255).astype(np.uint8)
    colored_mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        visual=trimesh.visual.ColorVisuals(vertex_colors=colors),
        process=False,
    )
    colored_mesh.export(str(mesh_path), file_type="glb")


class Trellis(ModelWrapper):
    role = "image_to_3d"
    name = "trellis"

    def load(self) -> None:
        if not TRELLIS_SOURCE.is_dir():
            raise FileNotFoundError(f"TRELLIS source is missing: {TRELLIS_SOURCE}")

        os.environ["ATTN_BACKEND"] = "xformers"
        os.environ["SPCONV_ALGO"] = "native"
        trellis_source = str(TRELLIS_SOURCE)
        if trellis_source in sys.path:
            sys.path.remove(trellis_source)
        sys.path.insert(0, trellis_source)

        import torch
        import xformers.ops.fmha as fmha
        from xformers.ops.fmha.attn_bias import BlockDiagonalMask

        fmha.BlockDiagonalMask = BlockDiagonalMask
        from trellis.pipelines import TrellisImageTo3DPipeline

        self.torch = torch
        self.pipeline = TrellisImageTo3DPipeline.from_pretrained(
            "microsoft/TRELLIS-image-large"
        )
        self.pipeline.to(torch.device(self.device))

    def predict(
        self,
        image_rgba: Image.Image,
        out_dir: Path,
        seed: int = 0,
        output_name: str = "full.glb",
    ) -> Path:
        import torch

        if Path(output_name).name != output_name or Path(output_name).suffix.lower() != ".glb":
            raise ValueError("TRELLIS output_name must be a .glb filename")
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        with torch.inference_mode():
            outputs = self.pipeline.run(
                image_rgba,
                seed=seed,
                formats=["mesh"],
            )

        meshes = outputs.get("mesh")
        if not meshes:
            raise RuntimeError("TRELLIS returned no mesh")
        out_dir.mkdir(parents=True, exist_ok=True)
        mesh_path = out_dir / output_name
        _export_mesh_glb(meshes[0], mesh_path)
        if not mesh_path.is_file():
            raise RuntimeError(f"TRELLIS did not create its GLB output: {mesh_path}")
        return mesh_path
