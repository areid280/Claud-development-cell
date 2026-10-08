from __future__ import annotations

from avatar_forge.models import trial_adapters_parsing  # noqa: F401
from avatar_forge.models.parsing_florence2_plus_sam import (
    Florence2PlusSam,
    canonical_label_for_prompt,
)
from avatar_forge.models.trials import REGISTRY


def test_florence_sam_candidate_uses_configured_name() -> None:
    assert Florence2PlusSam.name == "florence2-plus-sam"
    assert ("parsing", Florence2PlusSam.name) in REGISTRY


def test_prompt_labels_map_to_canonical_labels() -> None:
    labels = {"upper_clothes", "socks_stockings", "hair", "accessory"}

    assert canonical_label_for_prompt("top", labels) == "upper_clothes"
    assert canonical_label_for_prompt("stockings", labels) == "socks_stockings"
    assert canonical_label_for_prompt("hair", labels) == "hair"
    assert canonical_label_for_prompt("skirt", labels) == "accessory"
