---
applyTo: "**/*.py"
---

- Python 3.11, type hints on every function, `from __future__ import annotations` at the top.
- Use `pathlib.Path`, never string paths.
- Library code logs via `avatar_forge.core.log.get_logger(__name__)`; no `print`.
- Stage modules expose exactly `run(ctx: StageContext) -> StageResult`.
- Read thresholds and sizes from `ctx.config`, not hard-coded numbers.
- Heavy imports (torch, model libraries) go inside functions so `pytest` without a GPU still imports the package.
- New behaviour needs a test in `tests/`. GPU-only tests get `@pytest.mark.gpu`.
- Run `ruff check src tests` and `pytest -q` before finishing.
