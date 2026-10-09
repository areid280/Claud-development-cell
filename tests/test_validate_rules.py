from __future__ import annotations

from copy import deepcopy

import pytest

from avatar_forge.stages.validate_rules import evaluate


def _base_cfg(**extra: object) -> dict[str, object]:
    cfg: dict[str, object] = {
        "min_long_side_px": 1024,
        "keypoint_min_score": 0.3,
        "max_people": 1,
        "required_keypoints": [
            "nose",
            "left_ankle",
            "right_ankle",
        ],
        "min_person_height_frac": 0.5,
        "warn_crossed_arms": True,
        "warn_wrists_inside_torso": True,
    }
    cfg.update(extra)
    return cfg


def _person(
    *,
    bbox: tuple[float, float, float, float] = (200.0, 60.0, 800.0, 1450.0),
    score: float = 0.9,
    keypoints: dict[str, list[float]] | None = None,
) -> dict:
    default_keypoints = {
        "nose": [512.0, 150.0, 0.95],
        "left_shoulder": [430.0, 430.0, 0.90],
        "right_shoulder": [610.0, 430.0, 0.90],
        "left_hip": [460.0, 750.0, 0.88],
        "right_hip": [590.0, 750.0, 0.88],
        "left_knee": [470.0, 1050.0, 0.88],
        "right_knee": [570.0, 1050.0, 0.88],
        "left_ankle": [470.0, 1380.0, 0.88],
        "right_ankle": [570.0, 1380.0, 0.88],
        "left_wrist": [350.0, 570.0, 0.67],
        "right_wrist": [680.0, 570.0, 0.67],
    }
    person = {
        "bbox": list(bbox),
        "score": score,
        "keypoints": deepcopy(
            default_keypoints if keypoints is None else {**default_keypoints, **keypoints}
        ),
    }
    return person


@pytest.mark.parametrize(
    ("persons", "image_size", "cfg", "expected_status", "expected_message"),
    [
        (
            [_person()],
            (500, 500),
            _base_cfg(),
            "fail",
            "Image is too small",
        ),
        (
            [],
            (1024, 1536),
            _base_cfg(),
            "fail",
            "No person found.",
        ),
        (
            [_person(), _person()],
            (1024, 1536),
            _base_cfg(),
            "fail",
            "More than one person found.",
        ),
        (
            [_person(keypoints={"right_ankle": [120.0, 120.0, 0.05]})],
            (1024, 1536),
            _base_cfg(),
            "fail",
            "Not visible: right_ankle",
        ),
        (
            [_person(bbox=(200.0, 60.0, 800.0, 1521.0))],
            (1024, 1536),
            _base_cfg(),
            "fail",
            "Feet may be cut off",
        ),
        (
            [_person(bbox=(200.0, 5.0, 800.0, 1450.0))],
            (1024, 1536),
            _base_cfg(),
            "fail",
            "Head may be cut off",
        ),
        (
            [_person(bbox=(450.0, 120.0, 550.0, 500.0))],
            (1024, 1536),
            _base_cfg(),
            "fail",
            "Person is too small",
        ),
    ],
)
def test_evaluate_rule_rows(persons, image_size, cfg, expected_status, expected_message):
    status, messages = evaluate(persons, image_size, cfg)

    assert status == expected_status
    assert expected_message in "\n".join(messages)


def test_crossed_arms_warns() -> None:
    person = _person(
        keypoints={
            "left_shoulder": [450.0, 450.0, 0.9],
            "right_shoulder": [550.0, 450.0, 0.9],
            "left_hip": [470.0, 760.0, 0.9],
            "right_hip": [530.0, 760.0, 0.9],
            "left_wrist": [490.0, 600.0, 0.6],
            "right_wrist": [510.0, 600.0, 0.6],
        }
    )
    cfg = _base_cfg()
    status, messages = evaluate([person], (1024, 1536), cfg)
    assert status == "warn"
    assert "Arms look crossed" in "\n".join(messages)


def test_wrists_inside_torso_warns() -> None:
    person = _person(
        keypoints={
            "left_shoulder": [400.0, 420.0, 0.9],
            "right_shoulder": [620.0, 420.0, 0.9],
            "left_hip": [440.0, 760.0, 0.9],
            "right_hip": [580.0, 760.0, 0.9],
            "left_wrist": [500.0, 650.0, 0.6],
            "right_wrist": [700.0, 700.0, 0.6],
        }
    )
    cfg = _base_cfg()
    status, messages = evaluate([person], (1024, 1536), cfg)
    assert status == "warn"
    assert "An arm covers the torso" in "\n".join(messages)


def test_valid_person_is_ok() -> None:
    cfg = _base_cfg(
        required_keypoints=[
            "nose",
            "left_shoulder",
            "right_shoulder",
            "left_hip",
            "right_hip",
            "left_knee",
            "right_knee",
            "left_ankle",
            "right_ankle",
        ]
    )
    status, messages = evaluate([_person()], (1024, 1536), cfg)
    assert status == "ok"
    assert messages == []
