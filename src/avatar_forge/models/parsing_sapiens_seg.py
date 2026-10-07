from __future__ import annotations

import numpy as np
from PIL import Image

from avatar_forge.models.base import ModelWrapper
from avatar_forge.models.parsing_utils import (
    id_to_label_map,
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


class SapiensSeg(ModelWrapper):
    role = "parsing"
    name = "sapiens-seg"

    def load(self) -> None:
        import torch
        from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation

        self.torch = torch
        self.device = (
            "cuda"
            if self.device.startswith("cuda") and torch.cuda.is_available()
            else "cpu"
        )
        model_name = str(self.entry["weights"]).split("(")[0].strip()
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModelForSemanticSegmentation.from_pretrained(model_name).to(
            self.device
        )
        self.model.eval()

    def predict(self, image: Image.Image) -> dict[str, np.ndarray]:
        rgb, alpha = image_rgb_and_alpha(image)
        inputs = self.processor(images=rgb, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with self.torch.inference_mode():
            logits = self.model(**inputs).logits
        return semantic_logits_to_masks(
            logits,
            id_to_label_map(self.model.config.id2label),
            MODEL_LABEL_MAP,
            (image.height, image.width),
            alpha,
        )
