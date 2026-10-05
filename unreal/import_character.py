"""Run inside Unreal Editor (Tools -> Execute Python Script). Implemented by T26, extended in T38/T44.

Contract:
- Ask the user for an import_manifest.json (or read AF_IMPORT_MANIFEST env var).
- Import every FBX listed under "meshes" into /Game/AvatarForge/<job_id>/.
- Import textures, create a material instance per garment from M_AF_Garment
  (create the parent material once if it does not exist), assign textures.
- Print body parameters from "body" so the user can enter them in MetaHuman Creator.

This file must only use the `unreal` module and the Python standard library.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_import_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    import unreal  # noqa: F401  (only available inside the editor)

    raise NotImplementedError("Implemented in task T26")


if __name__ == "__main__":
    main()
