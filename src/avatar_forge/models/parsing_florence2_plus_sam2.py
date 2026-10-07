from __future__ import annotations

import numpy as np
from PIL import Image

from avatar_forge.core.config import load_pipeline_config
from avatar_forge.models.base import ModelWrapper
from avatar_forge.models.parsing_utils import image_rgb_and_alpha

MODEL_LABEL_MAP = {
    "top": "upper_clothes",
    "stockings": "socks_stockings",
}


class Florence2PlusSam2(ModelWrapper):
    role = "parsing"
    name = "florence2-plus-sam2"

    def load(self) -> None:
        import torch
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        from transformers import AutoModelForCausalLM, AutoProcessor

        self.torch = torch
        self.device = (
            "cuda"
            if self.device.startswith("cuda") and torch.cuda.is_available()
            else "cpu"
        )
        weights = [part.strip() for part in str(self.entry["weights"]).split(";")]
        if len(weights) != 2:
            raise ValueError("Florence/SAM 2 weights must contain two model IDs")
        self.florence_processor = AutoProcessor.from_pretrained(
            weights[0], trust_remote_code=True
        )
        self.florence = AutoModelForCausalLM.from_pretrained(
            weights[0], trust_remote_code=True, attn_implementation="eager"
        ).to(self.device)
        self.florence.eval()
        self.sam = SAM2ImagePredictor.from_pretrained(weights[1])
        self.sam.model.to(self.device)
        self.prompts = list(
            load_pipeline_config()["stages"]["s03_parse"]["open_vocab_prompts"]
        )
        self.canonical_labels = set(
            load_pipeline_config()["stages"]["s03_parse"]["labels"]
        )

    def predict(self, image: Image.Image) -> dict[str, np.ndarray]:
        rgb, alpha = image_rgb_and_alpha(image)
        image_array = np.asarray(rgb)
        self.sam.set_image(image_array)
        masks_by_label: dict[str, np.ndarray] = {}

        for prompt in self.prompts:
            task = "<OPEN_VOCABULARY_DETECTION>"
            inputs = self.florence_processor(
                text=f"{task}{prompt}", images=rgb, return_tensors="pt"
            )
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            with self.torch.inference_mode():
                generated_ids = self.florence.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs["pixel_values"],
                    max_new_tokens=1024,
                    do_sample=False,
                )
            generated_text = self.florence_processor.batch_decode(
                generated_ids, skip_special_tokens=False
            )[0]
            detections = self.florence_processor.post_process_generation(
                generated_text,
                task=task,
                image_size=(image.height, image.width),
            )[task]
            if not detections["bboxes"]:
                continue

            canonical = MODEL_LABEL_MAP.get(prompt, prompt)
            if canonical not in self.canonical_labels:
                canonical = "accessory"
            target_mask = masks_by_label.setdefault(
                canonical, np.zeros((image.height, image.width), dtype=bool)
            )
            boxes = np.asarray(detections["bboxes"], dtype=np.float32)
            sam_masks, _, _ = self.sam.predict(
                box=boxes, multimask_output=False
            )
            for mask in np.asarray(sam_masks):
                target_mask |= mask.astype(bool) & alpha

        return masks_by_label
