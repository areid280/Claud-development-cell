from __future__ import annotations

from typing import TypedDict

import numpy as np
from PIL import Image

from avatar_forge.models.base import ModelWrapper

COCO_NAMES = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)


class Person(TypedDict):
    bbox: list[float]
    score: float
    keypoints: dict[str, list[float]]


class RTMLibRTMW(ModelWrapper):
    role = "pose"
    name = "rtmlib-rtmw"

    def load(self) -> None:
        from rtmlib import Wholebody

        from avatar_forge.models.ort_cuda import prepare_onnxruntime_cuda

        prepare_onnxruntime_cuda()  # else ONNX Runtime silently runs on CPU (E-020)

        device = "cuda" if self.device.startswith("cuda") else "cpu"
        self.model = Wholebody(mode="balanced", backend="onnxruntime", device=device)

    def predict(self, image: Image.Image) -> list[Person]:
        keypoints, scores = self.model(np.asarray(image.convert("RGB"))[:, :, ::-1].copy())
        points = np.asarray(keypoints)
        confidences = np.asarray(scores)
        if points.ndim == 2:
            points = points[None, ...]
        if confidences.ndim == 1:
            confidences = confidences[None, ...]

        people: list[Person] = []
        for person_points, person_scores in zip(points, confidences, strict=True):
            count = min(len(COCO_NAMES), len(person_points), len(person_scores))
            named_points = {
                COCO_NAMES[index]: [
                    float(person_points[index][0]),
                    float(person_points[index][1]),
                    float(person_scores[index]),
                ]
                for index in range(count)
            }
            valid_points = person_points[:count]
            if not count:
                continue
            people.append(
                {
                    "bbox": [
                        float(valid_points[:, 0].min()),
                        float(valid_points[:, 1].min()),
                        float(valid_points[:, 0].max()),
                        float(valid_points[:, 1].max()),
                    ],
                    "score": float(person_scores[:count].mean()),
                    "keypoints": named_points,
                }
            )
        return people
