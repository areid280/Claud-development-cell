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


def canonical_label_for_prompt(prompt: str, labels: set[str]) -> str:
    label = MODEL_LABEL_MAP.get(prompt, prompt)
    return label if label in labels else "accessory"


class Florence2PlusSam(ModelWrapper):
    role = "parsing"
    name = "florence2-plus-sam"

    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor, SamModel, SamProcessor

        self.torch = torch
        self.device = (
            "cuda"
            if self.device.startswith("cuda") and torch.cuda.is_available()
            else "cpu"
        )
        weights = [part.strip() for part in str(self.entry["weights"]).split(";")]
        if len(weights) != 2:
            raise ValueError("Florence/SAM v1 weights must contain two model IDs")
        self.florence_processor = AutoProcessor.from_pretrained(
            weights[0], trust_remote_code=True
        )
        self.florence = AutoModelForCausalLM.from_pretrained(
            weights[0], trust_remote_code=True, attn_implementation="eager"
        ).to(self.device)
        self.florence.eval()
        self.sam_processor = SamProcessor.from_pretrained(weights[1])
        self.sam = SamModel.from_pretrained(weights[1]).to(self.device)
        self.sam.eval()
        self.prompts = list(
            load_pipeline_config()["stages"]["s03_parse"]["open_vocab_prompts"]
        )
        self.canonical_labels = set(
            load_pipeline_config()["stages"]["s03_parse"]["labels"]
        )

    def predict(self, image: Image.Image) -> dict[str, np.ndarray]:
        rgb, alpha = image_rgb_and_alpha(image)
        masks_by_label: dict[str, np.ndarray] = {}
        sam_image_inputs = self.sam_processor(images=rgb, return_tensors="pt")
        pixel_values = sam_image_inputs["pixel_values"].to(self.device)
        with self.torch.inference_mode():
            image_embeddings = self.sam.get_image_embeddings(pixel_values)

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
                    use_cache=False,
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

            canonical = canonical_label_for_prompt(prompt, self.canonical_labels)
            boxes = np.asarray(detections["bboxes"], dtype=np.float32)
            sam_inputs = self.sam_processor(
                images=rgb,
                input_boxes=[boxes.tolist()],
                return_tensors="pt",
            )
            sam_inputs = {key: value.to(self.device) for key, value in sam_inputs.items()}
            with self.torch.inference_mode():
                sam_outputs = self.sam(
                    image_embeddings=image_embeddings,
                    input_boxes=sam_inputs["input_boxes"],
                    multimask_output=False,
                )
            processed_masks = self.sam_processor.image_processor.post_process_masks(
                sam_outputs.pred_masks,
                sam_inputs["original_sizes"],
                sam_inputs["reshaped_input_sizes"],
            )[0]
            prompt_mask = processed_masks.any(dim=(0, 1)).detach().cpu().numpy()
            prompt_mask &= alpha
            if prompt_mask.any():
                masks_by_label[canonical] = masks_by_label.get(
                    canonical,
                    np.zeros((image.height, image.width), dtype=bool),
                ) | prompt_mask

        return masks_by_label
