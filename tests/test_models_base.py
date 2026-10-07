from __future__ import annotations

import pytest

from avatar_forge.models.base import ModelWrapper, model_entry, vram_peak_gb


def test_model_entry_returns_configured_candidate() -> None:
    entry = model_entry("pose", "vitpose-hf")

    assert isinstance(entry, dict)
    assert "weights" in entry


def test_model_entry_unknown_name_raises_key_error() -> None:
    with pytest.raises(KeyError, match="unknown-model"):
        model_entry("pose", "unknown-model")


def test_vram_peak_gb_is_non_negative_float() -> None:
    peak = vram_peak_gb()

    assert isinstance(peak, float)
    assert peak >= 0.0


def test_wrapper_context_manager_loads_and_unloads_once() -> None:
    class DummyWrapper(ModelWrapper):
        role = "test"
        name = "dummy"

        def __init__(self) -> None:
            super().__init__({})
            self.load_count = 0
            self.unload_count = 0

        def load(self) -> None:
            self.load_count += 1

        def unload(self) -> None:
            self.unload_count += 1

    wrapper = DummyWrapper()
    with wrapper as loaded:
        assert loaded is wrapper
        assert wrapper.load_count == 1
        assert wrapper.unload_count == 0

    assert wrapper.unload_count == 1
