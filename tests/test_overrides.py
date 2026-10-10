from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from avatar_forge.body.overrides import apply_overrides


@pytest.fixture
def body() -> dict[str, Any]:
    return {
        "units": "cm",
        "source": "s04_body_fit",
        "measurements": {
            "height": 168.0,
            "bust": 90.0,
            "underbust": 75.0,
            "waist": 70.0,
            "hips": 96.0,
            "shoulder_width": 40.0,
            "inseam": 80.0,
        },
        "confidence": {"height": 0.5, "bust": 0.5},
        "colors": {"hair": "#2b2420", "skin": "#c08060", "eyes": "#5a7a8c"},
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("175", 175.0),
        ("+5", 95.0),
        ("-3", 87.0),
        ("+10%", 99.0),
        ("-5%", 85.5),
        ("+2.5", 92.5),
        ("  177.2  ", 177.2),
    ],
)
def test_measurement_value_forms(
    body: dict[str, Any], value: str, expected: float
) -> None:
    updated, messages = apply_overrides(body, {"bust": value})
    assert updated["measurements"]["bust"] == expected
    assert updated["confidence"]["bust"] == 1.0
    assert messages == []


@pytest.mark.parametrize(
    "value",
    ["10%", "tall", "", "+", "1.2.3", "++5", "5%"],
)
def test_invalid_measurement_values_are_ignored(
    body: dict[str, Any], value: str
) -> None:
    updated, messages = apply_overrides(body, {"bust": value})
    assert updated["measurements"]["bust"] == 90.0
    assert len(messages) == 1
    assert messages[0] == (
        f"Invalid value '{value}' for 'bust' "
        "(use 175, +5, -3, +10% or -5%); ignored."
    )


@pytest.mark.parametrize(("value", "expected"), [("-90", 0.0), ("+211", 301.0)])
def test_measurements_out_of_range_are_ignored(
    body: dict[str, Any], value: str, expected: float
) -> None:
    updated, messages = apply_overrides(body, {"bust": value})
    assert updated["measurements"]["bust"] == 90.0
    assert messages == [
        f"'bust' would become {expected} cm (allowed: above 0, up to 300); ignored."
    ]


def test_missing_optional_measurement_supports_absolute_but_not_relative(
    body: dict[str, Any],
) -> None:
    relative, messages = apply_overrides(body, {"arm_length": "+2"})
    assert "arm_length" not in relative["measurements"]
    assert messages == [
        "Cannot apply '+2' to 'arm_length': no measured value; ignored."
    ]

    absolute, messages = apply_overrides(body, {"arm_length": "60"})
    assert absolute["measurements"]["arm_length"] == 60.0
    assert absolute["confidence"]["arm_length"] == 1.0
    assert messages == []


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("hair_color", "hair"),
        ("skin_color", "skin"),
        ("eye_color", "eyes"),
    ],
)
def test_valid_colors_are_stored_lowercase(
    body: dict[str, Any], key: str, name: str
) -> None:
    updated, messages = apply_overrides(body, {key: "#ABCDEF"})
    assert updated["colors"][name] == "#abcdef"
    assert messages == []


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("hair_color", "hair"),
        ("skin_color", "skin"),
        ("eye_color", "eyes"),
    ],
)
def test_invalid_color_is_ignored(
    body: dict[str, Any], key: str, name: str
) -> None:
    original = body["colors"][name]
    updated, messages = apply_overrides(body, {key: "red"})
    assert updated["colors"][name] == original
    assert messages == [
        f"Invalid colour 'red' for '{key}' (use #rrggbb); ignored."
    ]


def test_unknown_and_reserved_settings_have_exact_handling(
    body: dict[str, Any],
) -> None:
    updated, messages = apply_overrides(
        body, {"foo": "bar", "normalise": "true"}
    )
    assert updated == body
    assert messages == ["Unknown setting 'foo' ignored."]


def test_height_does_not_scale_other_measurements(body: dict[str, Any]) -> None:
    updated, messages = apply_overrides(body, {"height": "180"})
    assert updated["measurements"]["height"] == 180.0
    assert updated["measurements"]["bust"] == body["measurements"]["bust"]
    assert messages == []


def test_input_body_is_not_mutated(body: dict[str, Any]) -> None:
    original = deepcopy(body)
    apply_overrides(body, {"bust": "+5", "hair_color": "#FFFFFF"})
    assert body == original


def test_messages_are_in_sorted_key_order(body: dict[str, Any]) -> None:
    _, messages = apply_overrides(body, {"z_unknown": "x", "a_unknown": "y"})
    assert messages == [
        "Unknown setting 'a_unknown' ignored.",
        "Unknown setting 'z_unknown' ignored.",
    ]


def test_color_value_whitespace_is_trimmed(body: dict[str, Any]) -> None:
    updated, messages = apply_overrides(body, {"hair_color": " #2B1D14 "})

    assert messages == []
    assert updated["colors"]["hair"] == "#2b1d14"
