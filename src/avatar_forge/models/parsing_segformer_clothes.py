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
    "hat": "hat",
    "hair": "hair",
    "sunglasses": "accessory",
    "upper clothes": "upper_clothes",
    "skirt": "lower_clothes",
    "pants": "lower_clothes",
    "dress": "dress",
    "belt": "belt",
    "left shoe": "shoes",
    "right shoe": "shoes",
    "face": "face",
    "left leg": "skin",
    "right leg": "skin",
    "left arm": "skin",
    "right arm": "skin",
    "bag": "bag",
    "scarf": "accessory",
}


class SegformerClothes(ModelWrapper):
    role = "parsing"
    name = "segformer-clothes"

    def load(self) -> None:
        import torch
        from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation

        self.torch = torch
        self.device = (
            "cuda"
            if self.device.startswith("cuda") and torch.cuda.is_available()
            else "cpu"
        )
        model_name = str(self.entry["weights"])
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
