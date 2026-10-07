from __future__ import annotations

import numpy as np
from PIL import Image

from avatar_forge.models.base import ModelWrapper


class BiRefNet(ModelWrapper):
    role = "bg_remove"
    name = "birefnet"

    def load(self) -> None:
        import torch
        from transformers import AutoModelForImageSegmentation

        self.torch = torch
        self.device = (
            "cuda"
            if self.device.startswith("cuda") and torch.cuda.is_available()
            else "cpu"
        )
        self.model = AutoModelForImageSegmentation.from_pretrained(
            "ZhengPeng7/BiRefNet", trust_remote_code=True
        ).to(self.device)
        self.model.eval()

    def predict(self, image: Image.Image) -> Image.Image:
        torch = self.torch
        original_size = image.size
        rgb = image.convert("RGB").resize((1024, 1024), Image.Resampling.BILINEAR)
        image_tensor = torch.from_numpy(np.asarray(rgb)).permute(2, 0, 1)
        image_tensor = image_tensor.to(dtype=torch.float32).div_(255)
        mean = torch.tensor((0.485, 0.456, 0.406))[:, None, None]
        std = torch.tensor((0.229, 0.224, 0.225))[:, None, None]
        inputs = ((image_tensor - mean) / std).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            prediction = self.model(inputs)
            prediction = prediction[-1] if isinstance(prediction, (tuple, list)) else prediction
            alpha = prediction.sigmoid()[0, 0].cpu()
            alpha = torch.nn.functional.interpolate(
                alpha[None, None],
                size=(original_size[1], original_size[0]),
                mode="bilinear",
                align_corners=False,
            )[0, 0]
        alpha_image = Image.fromarray((alpha.clamp(0, 1).numpy() * 255).astype("uint8"))
        result = image.convert("RGBA")
        result.putalpha(alpha_image)
        return result
