"""Apply user-supplied body measurement and colour overrides."""

from __future__ import annotations

import copy
import re
from typing import Any

MEASUREMENT_KEYS = (
    "height",
    "bust",
    "underbust",
    "waist",
    "hips",
    "shoulder_width",
    "inseam",
    "arm_length",
    "thigh",
    "neck",
)
COLOR_KEYS = {"hair_color": "hair", "skin_color": "skin", "eye_color": "eyes"}
RESERVED_KEYS = frozenset({"normalise"})
MAX_CM = 300.0  # schemas/body_params.schema.json $defs.cm

_MEASUREMENT_VALUE = re.compile(r"^([+-])?(\d+(?:\.\d+)?)(%)?$")
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def apply_overrides(
    body: dict[str, Any], sets: dict[str, str]
) -> tuple[dict[str, Any], list[str]]:
    """Apply validated measurements and colours without mutating ``body``."""
    body = copy.deepcopy(body)
    messages: list[str] = []

    for key in sorted(sets):
        value = sets[key]
        if key in RESERVED_KEYS:
            continue
        if key in MEASUREMENT_KEYS:
            match = _MEASUREMENT_VALUE.fullmatch(value.strip())
            if match is None or (match.group(3) and match.group(1) is None):
                messages.append(
                    f"Invalid value '{value}' for '{key}' "
                    "(use 175, +5, -3, +10% or -5%); ignored."
                )
                continue

            sign, number, percent = match.groups()
            measurements = body["measurements"]
            old_value = measurements.get(key)
            if sign is None:
                new_value = float(number)
            elif old_value is None:
                messages.append(
                    f"Cannot apply '{value}' to '{key}': no measured value; ignored."
                )
                continue
            elif percent:
                change = float(number) / 100
                factor = 1 + change if sign == "+" else 1 - change
                new_value = float(old_value) * factor
            else:
                delta = float(number) if sign == "+" else -float(number)
                new_value = float(old_value) + delta

            new_value = round(new_value, 1)
            if new_value <= 0 or new_value > MAX_CM:
                messages.append(
                    f"'{key}' would become {new_value} cm "
                    "(allowed: above 0, up to 300); ignored."
                )
                continue
            measurements[key] = new_value
            body.setdefault("confidence", {})[key] = 1.0
            continue

        if key in COLOR_KEYS:
            if not _HEX_COLOR.fullmatch(value.strip()):
                messages.append(
                    f"Invalid colour '{value}' for '{key}' (use #rrggbb); ignored."
                )
                continue
            body["colors"][COLOR_KEYS[key]] = value.strip().lower()
            continue

        messages.append(f"Unknown setting '{key}' ignored.")

    return body, messages
