from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _is_hugging_face_id(weights: object) -> bool:
    if (
        not isinstance(weights, str)
        or any(character.isspace() for character in weights)
        or "://" in weights
    ):
        return False
    parts = weights.split("/")
    return len(parts) == 2 and all(parts)


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from avatar_forge.core.config import load_models_config
    from avatar_forge.core.paths import weights_dir
    from avatar_forge.models.base import model_entry

    parser = argparse.ArgumentParser(description="Fetch model weights or list configured models.")
    parser.add_argument("--role")
    parser.add_argument("--name")
    parser.add_argument("--list", action="store_true", dest="list_models")
    args = parser.parse_args()

    if args.list_models:
        config = load_models_config()
        roles = config.get("roles", config)
        for role, role_config in roles.items():
            for candidate in role_config.get("candidates", []):
                print(f"{role}/{candidate['name']}: {candidate.get('licence', '')}")
        return

    if not args.role or not args.name:
        parser.error("--role and --name are required unless --list is used")

    entry = model_entry(args.role, args.name)
    weights = entry.get("weights")
    if not _is_hugging_face_id(weights):
        print(weights if weights is not None else "")
        return

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=weights,
        local_dir=weights_dir() / args.role / args.name,
    )


if __name__ == "__main__":
    main()
