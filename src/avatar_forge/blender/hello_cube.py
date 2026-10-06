from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :]
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args(args)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(size=1)
    bpy.ops.export_scene.fbx(filepath=str(options.out))


if __name__ == "__main__":
    main()
