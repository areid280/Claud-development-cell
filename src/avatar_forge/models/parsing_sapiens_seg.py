from __future__ import annotations

import numpy as np
from PIL import Image

from avatar_forge.models.base import ModelWrapper
from avatar_forge.models.parsing_utils import (
    image_rgb_and_alpha,
    semantic_logits_to_masks,
)

MODEL_LABEL_MAP = {
    "background": "background",
    "apparel": "accessory",
    "face neck": "face",
    "hair": "hair",
    "left foot": "skin",
    "left hand": "skin",
    "left lower arm": "skin",
    "left lower leg": "skin",
    "left shoe": "shoes",
    "left sock": "socks_stockings",
    "left upper arm": "skin",
    "left upper leg": "skin",
    "lower clothing": "lower_clothes",
    "right foot": "skin",
    "right hand": "skin",
    "right lower arm": "skin",
    "right lower leg": "skin",
    "right shoe": "shoes",
    "right sock": "socks_stockings",
    "right upper arm": "skin",
    "right upper leg": "skin",
    "torso": "skin",
    "upper clothing": "upper_clothes",
    "lower lip": "face",
    "upper lip": "face",
    "lower teeth": "face",
    "upper teeth": "face",
    "tongue": "face",
}

GOLIATH_CLASSES = tuple(label.title() for label in (
    "background",
    "apparel",
    "face_neck",
    "hair",
    "left_foot",
    "left_hand",
    "left_lower_arm",
    "left_lower_leg",
    "left_shoe",
    "left_sock",
    "left_upper_arm",
    "left_upper_leg",
    "lower_clothing",
    "right_foot",
    "right_hand",
    "right_lower_arm",
    "right_lower_leg",
    "right_shoe",
    "right_sock",
    "right_upper_arm",
    "right_upper_leg",
    "torso",
    "upper_clothing",
    "lower_lip",
    "upper_lip",
    "lower_teeth",
    "upper_teeth",
    "tongue",
))

INPUT_MEAN = np.array([123.5, 116.5, 103.5], dtype=np.float32)
INPUT_STD = np.array([58.5, 57.0, 57.5], dtype=np.float32)


def preprocess_sapiens_image(image: Image.Image) -> np.ndarray:
    resized = image.convert("RGB").resize((768, 1024), Image.Resampling.BILINEAR)
    pixels = np.asarray(resized, dtype=np.float32)
    normalized = (pixels - INPUT_MEAN) / INPUT_STD
    return normalized.transpose(2, 0, 1)


class SapiensSeg(ModelWrapper):
    role = "parsing"
    name = "sapiens-seg"

    def load(self) -> None:
        import torch
        from huggingface_hub import hf_hub_download, list_repo_files

        repo_id = str(self.entry["weights"]).split("(")[0].strip()
        checkpoints = [
            filename
            for filename in list_repo_files(repo_id)
            if filename.endswith(".pt2")
        ]
        if len(checkpoints) != 1:
            raise ValueError(
                f"Expected one TorchScript .pt2 file in {repo_id!r}; "
                f"found {len(checkpoints)}"
            )

        self.torch = torch
        self.device = (
            "cuda"
            if self.device.startswith("cuda") and torch.cuda.is_available()
            else "cpu"
        )
        checkpoint = hf_hub_download(repo_id=repo_id, filename=checkpoints[0])
        self.model = torch.jit.load(checkpoint).eval().to(self.device)
        self.id_to_label = dict(enumerate(GOLIATH_CLASSES))

    def predict(self, image: Image.Image) -> dict[str, np.ndarray]:
        rgb, alpha = image_rgb_and_alpha(image)
        inputs = self.torch.from_numpy(preprocess_sapiens_image(rgb)).unsqueeze(0)
        inputs = inputs.to(device=self.device, dtype=self.torch.float32)

        with self.torch.inference_mode():
            outputs = self.model(inputs)
        if isinstance(outputs, (tuple, list)):
            if len(outputs) != 1:
                raise TypeError(
                    "Sapiens TorchScript model returned multiple output tensors"
                )
            outputs = outputs[0]
        if not isinstance(outputs, self.torch.Tensor):
            raise TypeError("Sapiens TorchScript model did not return logits")
        if outputs.ndim == 3:
            outputs = outputs.unsqueeze(0)

        return semantic_logits_to_masks(
            outputs,
            self.id_to_label,
            MODEL_LABEL_MAP,
            (image.height, image.width),
            alpha,
        )
