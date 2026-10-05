# T53 — Third-party notices and docs
milestone: M5 · effort: low · depends: T52

## Goal
Accurate licence notices and docs that let a new person set up and use the tool.

## Do
1. `THIRD_PARTY_NOTICES.md`: every selected model (code + weights), every Python
   dependency with a non-permissive licence (`pip-licenses --format=markdown`),
   Blender (GPL, used as an external tool), garment library items (from index.yaml).
   Copy licence names from config/models.yaml exactly as Opus approved them.
2. README: update Quick start with the real commands; add a "Using the UI" section.
3. docs/INSTALL_LOG.md → fold the final install steps into `scripts/setup_pod.sh`
   and the `models` extra in pyproject.

## Log
