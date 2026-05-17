#!/usr/bin/env python3
"""Install or package the designing-growth-funnels skill for common hosts."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "designing-growth-funnels"
SKILL_DIR = REPO_ROOT / "skills" / SKILL_NAME


TARGETS = {
    "codex": Path.home() / ".codex" / "skills" / SKILL_NAME,
    "claude": Path.home() / ".claude" / "skills" / SKILL_NAME,
    "claude-project": Path.cwd() / ".claude" / "skills" / SKILL_NAME,
    "agents-project": Path.cwd() / ".agents" / "skills" / SKILL_NAME,
}


def copy_skill(destination: Path, force: bool) -> None:
    if not SKILL_DIR.exists():
        raise SystemExit(f"Skill directory not found: {SKILL_DIR}")

    if destination.exists():
        if not force:
            raise SystemExit(f"Destination exists, rerun with --force: {destination}")
        shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    shutil.copytree(SKILL_DIR, destination, ignore=ignore)
    print(f"Installed {SKILL_NAME} -> {destination}")


def package_zip(output_dir: Path, force: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{SKILL_NAME}.zip"

    if archive_path.exists():
        if not force:
            raise SystemExit(f"Archive exists, rerun with --force: {archive_path}")
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(SKILL_DIR.rglob("*")):
            if path.is_dir():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc" or path.name == ".DS_Store":
                continue
            archive.write(path, path.relative_to(SKILL_DIR.parent))
    print(f"Created upload archive -> {archive_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        choices=[*TARGETS.keys(), "all-local", "zip"],
        help="Host target. Use zip for ChatGPT Skills, Claude.ai, or API upload workflows.",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing install or archive.")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "dist",
        help="Output directory for zip archives. Defaults to ./dist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.target == "zip":
        package_zip(args.out.resolve(), args.force)
        return

    if args.target == "all-local":
        for key in ("codex", "claude"):
            copy_skill(TARGETS[key], args.force)
        return

    copy_skill(TARGETS[args.target], args.force)


if __name__ == "__main__":
    main()
