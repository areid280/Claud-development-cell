"""Build one comparison image per role from jobs/_model_trials (for gate reviews).

Rows = sample images, columns = candidates (one preview image per cell), so a reviewer can
compare every candidate on every sample at a glance.

    python scripts/contact_sheet.py            # writes jobs/_model_trials/contact_<role>.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

# Which output file best represents a trial, per role (first match wins).
PREFERRED = {
    "pose": ["overlay.png"],
    "bg_remove": ["on_grey.png", "cutout.png"],
    "parsing": ["labels.png"],
    "body_measure": ["overlay.png", "front.png"],
    "image_to_3d": ["full_previews/front.png", "front.png"],
}
CELL = 256
LABEL_H = 18


def _cell_image(trial_dir: Path, role: str) -> Image.Image | None:
    for name in PREFERRED.get(role, []):
        path = trial_dir / name
        if path.is_file():
            image = Image.open(path).convert("RGB")
            image.thumbnail((CELL, CELL))
            return image
    return None


def build(out_root: Path, role: str) -> Path | None:
    role_dir = out_root / role
    if not role_dir.is_dir():
        return None
    candidates = sorted(path for path in role_dir.iterdir() if path.is_dir())
    samples = sorted(
        {trial.name for cand in candidates for trial in cand.iterdir() if trial.is_dir()}
    )
    if not candidates or not samples:
        return None
    sheet = Image.new("RGB", (CELL * (len(candidates) + 1), LABEL_H + CELL * len(samples)), "white")
    draw = ImageDraw.Draw(sheet)
    for col, cand in enumerate(candidates, start=1):
        draw.text((col * CELL + 4, 2), cand.name, fill="black")
    for row, sample in enumerate(samples):
        top = LABEL_H + row * CELL
        draw.text((4, top + CELL // 2), sample, fill="black")
        for col, cand in enumerate(candidates, start=1):
            image = _cell_image(cand / sample, role)
            if image is None:
                draw.text((col * CELL + 4, top + CELL // 2), "(none)", fill="red")
            else:
                sheet.paste(image, (col * CELL, top))
    out_path = out_root / f"contact_{role}.png"
    sheet.save(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=Path("jobs/_model_trials"))
    args = parser.parse_args()
    for role in PREFERRED:
        path = build(args.out_root, role)
        print(f"{role}: {path or 'no trials'}")


if __name__ == "__main__":
    main()
