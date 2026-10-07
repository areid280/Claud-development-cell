from __future__ import annotations

from PIL import Image

from avatar_forge.models.base import ModelWrapper
from avatar_forge.models.pose_rtmlib_rtmw import COCO_NAMES, Person


class ViTPoseHF(ModelWrapper):
    role = "pose"
    name = "vitpose-hf"

    def load(self) -> None:
        import torch
        from transformers import (
            AutoProcessor,
            RTDetrForObjectDetection,
            VitPoseForPoseEstimation,
        )

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.detector_processor = AutoProcessor.from_pretrained(
            "PekingU/rtdetr_r50vd_coco_o365"
        )
        self.detector = RTDetrForObjectDetection.from_pretrained(
            "PekingU/rtdetr_r50vd_coco_o365"
        ).to(self.device)
        self.processor = AutoProcessor.from_pretrained("usyd-community/vitpose-base-simple")
        self.model = VitPoseForPoseEstimation.from_pretrained(
            "usyd-community/vitpose-base-simple"
        ).to(self.device)

    def predict(self, image: Image.Image) -> list[Person]:
        torch = self.torch
        with torch.inference_mode():
            detection_inputs = self.detector_processor(
                images=image.convert("RGB"), return_tensors="pt"
            ).to(self.device)
            detections = self.detector(**detection_inputs)
            detection_results = self.detector_processor.post_process_object_detection(
                detections,
                target_sizes=torch.tensor([(image.height, image.width)], device=self.device),
                threshold=0.3,
            )[0]
            boxes = detection_results["boxes"][detection_results["labels"] == 0]
            if not len(boxes):
                return []

            coco_boxes = boxes.clone()
            coco_boxes[:, 2] -= coco_boxes[:, 0]
            coco_boxes[:, 3] -= coco_boxes[:, 1]
            pose_inputs = self.processor(
                image.convert("RGB"),
                boxes=[coco_boxes.cpu().numpy()],
                return_tensors="pt",
            ).to(self.device)
            pose_outputs = self.model(**pose_inputs)
            pose_results = self.processor.post_process_pose_estimation(
                pose_outputs, boxes=[coco_boxes.cpu().numpy()]
            )[0]

        people: list[Person] = []
        for box, result in zip(boxes.cpu().numpy(), pose_results, strict=True):
            points = result["keypoints"].detach().cpu().numpy()
            scores = result["scores"].detach().cpu().numpy()
            keypoints = {
                COCO_NAMES[index]: [
                    float(points[index][0]),
                    float(points[index][1]),
                    float(scores[index]),
                ]
                for index in range(min(len(COCO_NAMES), len(points), len(scores)))
            }
            people.append(
                {
                    "bbox": [float(value) for value in box],
                    "score": float(scores.mean()) if len(scores) else 0.0,
                    "keypoints": keypoints,
                }
            )
        return people
