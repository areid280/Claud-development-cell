from __future__ import annotations

import argparse
import platform
import shutil
import sys
from pathlib import Path

from avatar_forge import __version__
from avatar_forge.core import manifest as mf
from avatar_forge.core.config import load_pipeline_config
from avatar_forge.core.job import ConsentError, create_job
from avatar_forge.core.log import configure, get_logger
from avatar_forge.core.paths import REPO_ROOT, jobs_root, weights_dir
from avatar_forge.core.runner import StageFailedError, run_job
from avatar_forge.stages import STAGE_ORDER

log = get_logger("avatar_forge.cli")


def _parse_sets(pairs: list[str]) -> dict[str, str]:
    """--set height=175 --set bust=+10%  ->  {"height": "175", "bust": "+10%"}.

    Values stay strings; s05_body_params interprets them (absolute, +/-N, +/-N%).
    """
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--set expects key=value, got '{pair}'")
        key, value = pair.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _apply_overrides(job_dir: Path, sets: dict[str, str]) -> None:
    if not sets:
        return
    manifest = mf.load(job_dir)
    manifest.setdefault("overrides", {}).setdefault("set", {}).update(sets)
    mf.save(job_dir, manifest)


def _run(job_dir: Path, args: argparse.Namespace, from_stage: str | None) -> int:
    config = load_pipeline_config(args.config)
    try:
        results = run_job(
            job_dir, config, from_stage=from_stage, to_stage=args.to, dry_run=args.dry_run
        )
    except StageFailedError as exc:
        print(f"FAILED: {exc}\nJob folder: {job_dir}", file=sys.stderr)
        return 2
    for name, res in results.items():
        msg = "; ".join(res.messages)
        print(f"{name:<16} {res.status:<8} {msg}")
    print(f"Job folder: {job_dir}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    images = {"front": args.front}
    for view in ("back", "left", "right"):
        if getattr(args, view):
            images[view] = getattr(args, view)
    try:
        job_dir = create_job(
            images,
            adult_confirmed=args.confirm_adult_consent,
            consent_confirmed=args.confirm_adult_consent,
            root=args.jobs_dir,
        )
    except ConsentError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    _apply_overrides(job_dir, _parse_sets(args.set))
    return _run(job_dir, args, from_stage=None)


def cmd_rerun(args: argparse.Namespace) -> int:
    job_dir = args.job_dir
    if not (job_dir / "manifest.json").exists():
        print(f"No manifest.json in {job_dir}", file=sys.stderr)
        return 1
    _apply_overrides(job_dir, _parse_sets(args.set))
    return _run(job_dir, args, from_stage=args.from_stage)


def cmd_validate_manifest(args: argparse.Namespace) -> int:
    mf.validate(mf.load(args.job_dir))
    print("manifest OK")
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    print(f"avatar-forge {__version__}")
    print(f"python       {platform.python_version()} ({sys.executable})")
    print(f"repo root    {REPO_ROOT}")
    print(f"jobs dir     {jobs_root()}")
    print(f"weights dir  {weights_dir()} (exists: {weights_dir().exists()})")
    try:
        import torch  # noqa: PLC0415  (optional heavy import)

        cuda = torch.cuda.is_available()
        name = torch.cuda.get_device_name(0) if cuda else "-"
        print(f"torch        {torch.__version__}  cuda={cuda}  gpu={name}")
    except ImportError:
        print("torch        not installed")
    blender = shutil.which("blender")
    print(f"blender      {blender or 'not found on PATH'}")
    usage = shutil.disk_usage(jobs_root().parent if jobs_root().parent.exists() else REPO_ROOT)
    print(f"disk free    {usage.free / 1e9:.1f} GB")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="avatar-forge", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--config", type=Path, help="extra YAML merged over config/pipeline.yaml")
        sp.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="override, e.g. height=175, bust=+10%%, hair_color=#2b1d14")
        sp.add_argument("--to", choices=STAGE_ORDER, help="stop after this stage")
        sp.add_argument("--dry-run", action="store_true", help="record stages without running them")

    r = sub.add_parser("run", help="start a new job from 1-4 images")
    r.add_argument("front", type=Path, help="front-view image (required)")
    r.add_argument("--back", type=Path)
    r.add_argument("--left", type=Path)
    r.add_argument("--right", type=Path)
    r.add_argument("--confirm-adult-consent", action="store_true",
                   help="confirm the subject is an adult and an original character or consenting")
    r.add_argument("--jobs-dir", type=Path, default=None)
    common(r)
    r.set_defaults(func=cmd_run)

    rr = sub.add_parser("rerun", help="re-run an existing job from a stage")
    rr.add_argument("job_dir", type=Path)
    rr.add_argument("--from", dest="from_stage", choices=STAGE_ORDER, required=True)
    common(rr)
    rr.set_defaults(func=cmd_rerun)

    v = sub.add_parser("validate-manifest", help="check a job's manifest against the schema")
    v.add_argument("job_dir", type=Path)
    v.set_defaults(func=cmd_validate_manifest)

    d = sub.add_parser("doctor", help="print an environment report")
    d.set_defaults(func=cmd_doctor)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure(10 if args.verbose else 20)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
