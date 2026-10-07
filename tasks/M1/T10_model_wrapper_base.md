# T10 — Model wrapper base and weights fetcher
milestone: M1 · effort: low · depends: G0, T04
owner input: a Hugging Face account token **only if** a gated model needs it (store it with `huggingface-cli login` on the pod; never in the repo or chat)

## Goal
One consistent pattern for loading third-party models and downloading their weights.

## Read first
- src/avatar_forge/models/__init__.py
- config/models.yaml (structure only; don't edit licence fields)
- src/avatar_forge/core/paths.py

## Do
1. Add to `pyproject.toml` a new optional extra:
   `models = ["huggingface_hub>=0.24", "onnxruntime-gpu>=1.18", "transformers>=4.44", "trimesh>=4.4"]`
   then `pip install -e ".[dev,models]"`.
2. Create `src/avatar_forge/models/base.py`:
   ```python
   class ModelWrapper(ABC):
       role: ClassVar[str]
       name: ClassVar[str]
       def __init__(self, entry: dict, device: str = "cuda"): ...   # entry from models.yaml
       @abstractmethod
       def load(self) -> None: ...
       def unload(self) -> None:   # default: drop attrs, gc.collect(), torch.cuda.empty_cache() if torch importable
       def __enter__/__exit__      # load/unload

   def vram_peak_gb() -> float     # torch.cuda.max_memory_allocated()/1e9, 0.0 if no torch/cuda
   def reset_vram_peak() -> None
   def model_entry(role: str, name: str) -> dict   # from load_models_config(); KeyError with clear message
   ```
   All torch imports inside functions.
3. Create `scripts/fetch_weights.py`:
   `python scripts/fetch_weights.py --role pose --name vitpose-hf`
   - Reads the entry; if `weights` looks like a Hugging Face id (`owner/name`, no spaces, no "://"),
     call `huggingface_hub.snapshot_download(repo_id, local_dir=weights_dir()/role/name)`.
   - Otherwise print the entry's `weights` text and exit 0 (manual/auto-download models).
   - `--list` prints every role/name with its licence field.
4. Tests `tests/test_models_base.py` (CPU only):
   - `model_entry("pose", "vitpose-hf")` returns a dict with `weights`.
   - unknown name → `KeyError`.
   - `vram_peak_gb()` returns a float ≥ 0 without a GPU.
   - A dummy subclass works as a context manager (load/unload called once each).

## Must not
- Set `selected` or `licence_ok`. Download any weights in tests.

## Verify
- `ruff check src tests scripts` · `pytest -q`
- `python scripts/fetch_weights.py --list`

## Done when
- [ ] Tests pass; `--list` output in Log

## Escalate if
- `onnxruntime-gpu` conflicts with the template's CUDA version.

## Log
- `pip install -e ".[dev,models]"`
  ```
  Successfully built avatar-forge
  Successfully installed avatar-forge-0.0.1
  ```
- `ruff check src tests scripts`
  ```
  All checks passed!
  ```
- `pytest -q`
  ```
  27 passed in 4.05s
  ```
- `python scripts/fetch_weights.py --list`
  ```
  pose/rtmlib-rtmw: Apache-2.0 (claimed; VERIFY code and weights)
  pose/vitpose-hf: Apache-2.0 (claimed; VERIFY)
  bg_remove/birefnet: MIT (claimed; VERIFY)
  bg_remove/rembg: MIT code (claimed); each bundled model has its own licence (VERIFY)
  parsing/segformer-clothes: VERIFY (model card; trained on ATR dataset, check dataset terms)
  parsing/florence2-plus-sam2: MIT (Florence-2) + Apache-2.0 (SAM 2) (claimed; VERIFY)
  parsing/sapiens-seg: VERIFY (Sapiens has its own licence; may be non-commercial)
  body_measure/keypoint-ratio: ours
  body_measure/sam-3d-body: VERIFY (Meta release; check code, weights and body-model licence)
  body_measure/smpler-x: VERIFY - SMPL-X body model is non-commercial by default
  image_to_3d/trellis: MIT (claimed; VERIFY incl. any dependency with NVIDIA source licence)
  image_to_3d/hunyuan3d-2: VERIFY - Tencent Hunyuan community licence has had territory exclusions (reportedly incl. UK/EU)
  image_to_3d/stable-fast-3d: VERIFY - Stability community licence (revenue thresholds)
  ```
- [x] Tests pass; `--list` output in Log

Opus post-check (2026-10-07, A40 pod): the `models` extra was missing from the venv, and
setup_pod.sh only installed `[dev]`; fixed in d91e46f (installs `[dev,models]`). After re-running setup:
```
hf_hub_download("hf-internal-testing/tiny-random-bert", "config.json") -> OK, file under
  /workspace/cache/hf/hub/.../snapshots/... (warning "Could not set the permissions ...
  Continuing without setting permissions." is expected on geesefs, D-006)
onnxruntime 1.30.0 ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
torch 2.4.1+cu124 cuda=True, numpy 1.26.3 (not upgraded)
```
D-006 HF-on-volume check: PASS.
