"""Combine s06 front/back previews of several jobs into one image for review.

    python scripts/preview_sheet.py /workspace/jobs/<job1> /workspace/jobs/<job2> ...
    -> writes jobs/_review/s06_previews.png (one row per job: front | back, labelled)
    --compare adds the vertex-colour previews (fused/vertex_colors/) as columns 3-4 (T28).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

CELL = 512
LABEL_H = 24


def build(job_dirs: list[Path], out_path: Path, compare: bool = False) -> Path:
    folders = ["", "vertex_colors"] if compare else [""]
    cells = [(folder, view) for folder in folders for view in ("front", "back")]
    sheet = Image.new("RGB", (CELL * len(cells), (CELL + LABEL_H) * len(job_dirs)), "white")
    draw = ImageDraw.Draw(sheet)
    for row, job in enumerate(job_dirs):
        top = row * (CELL + LABEL_H)
        draw.text((4, top + 4), job.name, fill="black")
        for col, (folder, view) in enumerate(cells):
            path = job / "s06_garments" / "fused" / folder / f"{view}.png"
            if path.is_file():
                with Image.open(path) as opened:
                    image = opened.convert("RGB")
                image.thumbnail((CELL, CELL))
                sheet.paste(image, (col * CELL, top + LABEL_H))
            else:
                draw.text((col * CELL + 4, top + LABEL_H + 4), f"missing {view}.png", fill="red")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jobs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("jobs/_review/s06_previews.png"))
    parser.add_argument("--compare", action="store_true", help="add vertex-colour previews")
    args = parser.parse_args()
    print(build(args.jobs, args.out, args.compare))


if __name__ == "__main__":
    main()
