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


def test_onnxruntime_probe_model_runs() -> None:
    import pytest as _pytest

    ort = _pytest.importorskip("onnxruntime")
    import numpy as np

    from avatar_forge.models.ort_cuda import PROBE_MODEL

    session = ort.InferenceSession(PROBE_MODEL, providers=["CPUExecutionProvider"])
    (out,) = session.run(None, {"x": np.array([-1.0], dtype=np.float32)})
    assert out.tolist() == [0.0]


@pytest.mark.gpu
def test_onnxruntime_really_uses_cuda() -> None:
    pytest.importorskip("onnxruntime")
    from avatar_forge.models.ort_cuda import cuda_session_works

    assert cuda_session_works(), "ONNX Runtime fell back to CPU (E-020)"
