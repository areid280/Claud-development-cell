# Stage contracts: what every `run(ctx)` can rely on

Opus-owned. Read this before implementing **any** stage (`src/avatar_forge/stages/s*.py`).
It summarises `src/avatar_forge/core/stage.py`, `core/runner.py` and `cli.py` so a task card
does not have to repeat them. A card's own "Contracts" section wins where it is more specific.

## 1. `StageContext` (frozen dataclass, `core/stage.py`)

| attribute | type | meaning |
|-----------|------|---------|
| `ctx.name` | `str` | this stage's name, e.g. `"s05_body_params"` |
| `ctx.job_dir` | `Path` | the job folder (`$AF_JOBS_DIR/<job_id>`) |
| `ctx.stage_dir` | `Path` | `job_dir / ctx.name`. The runner creates it; still call `ctx.stage_dir.mkdir(parents=True, exist_ok=True)` before writing (tests build `ctx` by hand) |
| `ctx.config` | `dict` | the whole of `config/pipeline.yaml` |
| `ctx.stage_config()` | `dict` | `config["stages"][ctx.name]` (or `{}`). Read tunables from here, never hard-code them |
| `ctx.manifest` | `dict` | read-only snapshot of `manifest.json`. **Never mutate it** and never write `manifest.json` |
| `ctx.overrides` | `dict` | deep copy of `manifest["overrides"]` (see §3) |
| `ctx.logger` | `logging.Logger` | use it for progress/debug lines; no `print` |
| `ctx.previous_output(stage, rel)` | `Path` | `job_dir / stage / rel`; raises `FileNotFoundError` with a clear message if missing |

## 2. `StageResult` (dataclass)

```python
StageResult(
    status="ok" | "warn" | "fail" | "skipped",
    outputs=["s05_body_params/body_params.json"],  # paths RELATIVE to job_dir, posix
    messages=["Unknown setting 'foo' ignored."],   # human-readable; CLI/UI show them
    data={"normalised": False},                    # small JSON-able summary
)
```

- There is **no separate warning API.** A warning is a string in `messages` plus `status="warn"`.
  `warn` means "outputs are usable, but look at the messages"; the runner continues.
- `fail` stops the run. Return it (with a message) for expected problems such as bad input;
  let unexpected exceptions propagate (the runner logs the traceback to `logs/<stage>.log`
  and records them as `fail`).
- `data` is stored as `manifest["stages"][name]["data"]`. Keep it small (no arrays, no images).
  Facts that do not fit a schema'd output file go here (E-022).
- Build output paths for `outputs` with `path.relative_to(ctx.job_dir).as_posix()`.

## 3. Overrides (`--set key=value`)

- `avatar-forge run|rerun ... --set bust=+10% --set height=175` stores
  `manifest["overrides"]["set"] = {"bust": "+10%", "height": "175"}`.
  **Values are always strings** (manifest schema) and accumulate across reruns: a later
  `--set` replaces the same key and keeps the others.
- Read them with `ctx.overrides.get("set", {})`. Never assume a key exists.
- Other override keys (manifest schema): `normalise` (bool), `disabled_garments` (list of ids).
- Overrides are declarative: a stage applies them to its **inputs**, never to its own previous
  output, so rerunning a stage gives the same result.

## 4. Files between stages

- Read only files that earlier stages wrote, through `ctx.previous_output(...)`.
- Write only inside `ctx.stage_dir`. Write JSON as
  `json.dumps(data, indent=2) + "\n"` with `encoding="utf-8"`.
- If an output has a schema in `schemas/`, validate before writing and return `fail` on error.
  Use the shared helper; it also resolves `$ref`s between schema files (e.g. import_manifest → body_params):
  ```python
  from avatar_forge.core import schemas
  schemas.validate(data, "import_manifest.schema.json")   # raises jsonschema.ValidationError
  ```
- Copy files with `shutil.copyfile` only. Jobs live on the network volume, which refuses chmod, so
  `shutil.copy`, `copy2` and `copytree` fail there with "Operation not permitted" (E-025).
- The runner copies these fixed-name files into the manifest after the stage returns.
  Stages never do it themselves:
  - `s05_body_params/body_params.json` goes to `manifest["body"]`
  - `s06_garments/*/garment.json` goes to `manifest["garments"]`

## 5. Models

- Load the gate-approved model with `avatar_forge.models.registry.load_selected(role)`.
  Never import a specific wrapper by name. If a role has no approved model, it raises: let it.
- Load lazily inside `run`, never at import time (tests import every stage without a GPU).

## 6. Tests

- Unit-test the pure logic in its own module (e.g. `avatar_forge/body/overrides.py`).
- Test `run(ctx)` by building a `StageContext` by hand with `tmp_path` as `job_dir`.
  See `tests/test_s04_body_fit.py`. Write the input files the stage expects, and
  monkeypatch any model call.
- GPU tests: `@pytest.mark.gpu`.
