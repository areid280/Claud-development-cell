from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from avatar_forge.models.base import ModelWrapper
from avatar_forge.models.mesh_axes import TRIPOSR_TO_GLTF

TRIPOSR_SOURCE = Path("/opt/src/TripoSR")
FOREGROUND_RATIO = 0.85


def prepare_model_input(image_rgba: Image.Image) -> np.ndarray:
    rgba = image_rgba.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"))
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        raise ValueError("TripoSR input has no non-transparent foreground")

    foreground = rgba.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    width, height = foreground.size
    square_size = max(width, height)
    square = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
    square.alpha_composite(foreground, ((square_size - width) // 2, (square_size - height) // 2))

    padded_size = int(square_size / FOREGROUND_RATIO)
    padded = Image.new("RGBA", (padded_size, padded_size), (0, 0, 0, 0))
    padding = (padded_size - square_size) // 2
    padded.alpha_composite(square, (padding, padding))
    pixels = np.asarray(padded, dtype=np.float32) / 255.0
    rgb = pixels[..., :3] * pixels[..., 3:4] + 0.5 * (1.0 - pixels[..., 3:4])
    return (rgb * 255.0).astype(np.uint8)


class TripoSR(ModelWrapper):
    role = "image_to_3d"
    name = "triposr"

    def load(self) -> None:
        if not TRIPOSR_SOURCE.is_dir():
            raise FileNotFoundError(f"TripoSR source is missing: {TRIPOSR_SOURCE}")

        shim_dir = Path(__file__).parent / "vendor_shims"
        for path in (str(TRIPOSR_SOURCE), str(shim_dir)):
            if path in sys.path:
                sys.path.remove(path)
        sys.path[:0] = [str(shim_dir), str(TRIPOSR_SOURCE)]

        import torch
        from tsr.system import TSR

        self.torch = torch
        self.model = TSR.from_pretrained(
            "stabilityai/TripoSR",
            config_name="config.yaml",
            weight_name="model.ckpt",
        )
        self.model.to(self.device)

    def predict(
        self,
        image_rgba: Image.Image,
        out_dir: Path,
        seed: int = 0,
        output_name: str = "full.glb",
    ) -> Path:
        import torch

        if Path(output_name).name != output_name or Path(output_name).suffix.lower() != ".glb":
            raise ValueError("TripoSR output_name must be a .glb filename")
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        model_input = prepare_model_input(image_rgba)
        with torch.inference_mode():
            scene_codes = self.model([model_input], device=self.device)
            meshes = self.model.extract_mesh(
                scene_codes, True, resolution=256
            )

        if not meshes:
            raise RuntimeError("TripoSR returned no mesh")
        out_dir.mkdir(parents=True, exist_ok=True)
        mesh_path = out_dir / output_name
        mesh = meshes[0]
        mesh.apply_transform(TRIPOSR_TO_GLTF)  # Z-up, faces X -> glTF Y-up, faces +Z (E-018)
        mesh.export(str(mesh_path), file_type="glb")
        if not mesh_path.is_file():
            raise RuntimeError(f"TripoSR did not create its GLB output: {mesh_path}")
        return mesh_path
