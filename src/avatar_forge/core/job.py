from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from avatar_forge.core import manifest as mf
from avatar_forge.core.paths import jobs_root

VALID_VIEWS = ("front", "back", "left", "right")


class ConsentError(RuntimeError):
    pass


def new_job_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{uuid.uuid4().hex[:6]}"


def create_job(
    images: dict[str, Path],
    *,
    adult_confirmed: bool,
    consent_confirmed: bool,
    root: Path | None = None,
) -> Path:
    """Create a job folder, copy inputs to inputs/<view><ext>, write the first manifest.

    `images` maps view name ("front", "back", "left", "right") to an image path.
    A front view is required. Both confirmations are required (docs/00_PROJECT_BRIEF.md §5).
    """
    if not (adult_confirmed and consent_confirmed):
        raise ConsentError(
            "Confirm the subject is an adult and that the image is an original "
            "character or used with the person's consent (--confirm-adult-consent)."
        )
    if "front" not in images:
        raise ValueError("A front view is required")
    unknown = set(images) - set(VALID_VIEWS)
    if unknown:
        raise ValueError(f"Unknown view(s): {sorted(unknown)}; use {VALID_VIEWS}")

    job_id = new_job_id()
    job_dir = (root or jobs_root()) / job_id
    inputs_dir = job_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=False)
    (job_dir / "logs").mkdir()

    manifest = mf.new_manifest(
        job_id,
        {
            "adult_confirmed": True,
            "consent_confirmed": True,
            "confirmed_at": mf.now_iso(),
        },
    )
    for view, src in images.items():
        src = Path(src)
        if not src.is_file():
            raise FileNotFoundError(src)
        dest = inputs_dir / f"{view}{src.suffix.lower()}"
        shutil.copyfile(src, dest)
        manifest["inputs"].append({"view": view, "path": str(dest.relative_to(job_dir))})

    mf.save(job_dir, manifest)
    return job_dir
