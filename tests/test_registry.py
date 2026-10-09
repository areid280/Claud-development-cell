from __future__ import annotations

import pytest

from avatar_forge.models.registry import wrapper_class


@pytest.mark.parametrize(
    ("role", "name", "class_name"),
    [
        ("pose", "rtmlib-rtmw", "RTMLibRTMW"),
        ("bg_remove", "birefnet", "BiRefNet"),
        ("parsing", "segformer-clothes", "SegformerClothes"),
        ("image_to_3d", "trellis", "Trellis"),
    ],
)
def test_selected_wrappers_resolve(role: str, name: str, class_name: str) -> None:
    assert wrapper_class(role, name).__name__ == class_name


def test_unknown_name_raises() -> None:
    with pytest.raises((LookupError, ModuleNotFoundError)):
        wrapper_class("pose", "does-not-exist")
