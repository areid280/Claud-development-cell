# T00 — Install and verify on the pod
milestone: M0 · effort: low · depends: —
owner input: pod running, repo cloned to /workspace/avatar-forge, VS Code connected (docs/04_ENVIRONMENT.md A–C)

## Goal
Prove the scaffold installs and its tests pass on the rented GPU pod.

## Read first
- docs/04_ENVIRONMENT.md
- scripts/setup_pod.sh, scripts/doctor.sh, scripts/smoke_test_gpu.py

## Do
1. In the VS Code terminal (remote), from `/workspace/avatar-forge`:
   `bash scripts/setup_pod.sh`
2. Open a new terminal so `~/.avatar_forge_env` is loaded. Check `which python`
   points to `/workspace/venv-af/bin/python`.
3. Run `bash scripts/doctor.sh`.
4. Run `python scripts/smoke_test_gpu.py`.
5. Run `ruff check src tests` and `pytest -q`.
6. Run `bash scripts/setup_pod.sh` a second time and confirm it finishes
   without re-downloading Blender or recreating the venv.

## Must not
- Change any file under `src/avatar_forge/core/` or `schemas/`.
- Install CUDA, drivers or a different torch build.

## Verify
- doctor shows an NVIDIA GPU with ≥ 20 GB, `cuda=True`, Blender 4.2.x.
- smoke test prints `PASS`.
- `pytest -q`: all pass (GPU/Blender-marked tests may be skipped at this point).

## Done when
- [ ] All Verify items true
- [ ] Outputs pasted in Log

## Escalate if
- `pip install -e` fails on a dependency conflict with the template's torch.
- `cuda=False` although `nvidia-smi` shows a GPU.
- Python is not 3.11 (wrong template — tell the owner instead of working around it).

## Log

Session ran in a cloud container, not the GPU pod (no /workspace, no nvidia-smi, no Blender).
Python 3.11.15 is present. Steps 1-4 and 6 could not be run.

```
$ nvidia-smi        -> command not found
$ ls /workspace     -> No such file or directory
$ which blender     -> (not found)
$ pip install -e .  -> ok (root-pip warning only)
$ ruff check src tests -> All checks passed!
$ pytest -q         -> ImportError while loading conftest: No module named 'PIL'
```
Result: Verify NOT met. Task set to blocked; see E-001.
