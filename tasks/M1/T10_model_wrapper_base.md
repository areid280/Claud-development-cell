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
