from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from avatar_forge.models.base import ModelWrapper
from avatar_forge.models.trials import TrialSkippedError


class SAM3DBody(ModelWrapper):
    """Lazy wrapper for the gated SAM 3D Body estimator."""

    role = "body_measure"
    name = "sam-3d-body"

    def load(self) -> None:
        os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
        try:
            from sam_3d_body import SAM3DBodyEstimator, load_sam_3d_body_hf
        except ImportError as error:
            raise RuntimeError(
                "SAM 3D Body is not installed; follow its INSTALL.md before trialling"
            ) from error

        try:
            model, model_cfg = load_sam_3d_body_hf(
                "facebook/sam-3d-body-dinov3", device=self.device
            )
        except Exception as error:
            response = getattr(error, "response", None)
            if getattr(response, "status_code", None) in (401, 403):
                raise TrialSkippedError("needs owner HF access request") from error
            raise
        self.estimator = SAM3DBodyEstimator(
            sam_3d_body_model=model,
            model_cfg=model_cfg,
            human_detector=None,
            human_segmentor=None,
            fov_estimator=None,
        )
        self.faces = np.asarray(self.estimator.faces, dtype=np.int64)

    def predict(
        self, image_rgba: Image.Image
    ) -> tuple[np.ndarray, np.ndarray, dict[str, tuple[float, float, float]] | None]:
        rgba = image_rgba.convert("RGBA")
        alpha = np.asarray(rgba.getchannel("A"))
        occupied_y, occupied_x = np.nonzero(alpha)
        if len(occupied_x) == 0:
            raise ValueError("SAM 3D Body input has an empty alpha mask")

        x_min, x_max = int(occupied_x.min()), int(occupied_x.max()) + 1
        y_min, y_max = int(occupied_y.min()), int(occupied_y.max()) + 1
        bbox = np.asarray(
            [[x_min, y_min, x_max, y_max]], dtype=np.float32
        )
        mask = (alpha > 0).astype(np.uint8)

        with tempfile.TemporaryDirectory(prefix="avatar-forge-sam3d-") as temp_dir:
            image_path = Path(temp_dir) / "input.png"
            rgba.save(image_path)
            outputs = self.estimator.process_one_image(
                str(image_path), bboxes=bbox, masks=mask
            )
        if not outputs:
            raise ValueError("SAM 3D Body did not detect a person in the cut-out")

        vertices = outputs[0].get("pred_vertices")
        if vertices is None:
            raise ValueError("SAM 3D Body output is missing pred_vertices")
        if hasattr(vertices, "detach"):
            vertices = vertices.detach().cpu().numpy()
        mesh_vertices = np.asarray(vertices, dtype=np.float64).reshape(-1, 3)
        return mesh_vertices, self.faces.copy(), None
