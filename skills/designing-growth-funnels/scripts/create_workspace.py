#!/usr/bin/env python3
"""Create a complete growth funnel workspace with empty explicit-state files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workspace_lib import ensure_workspace, validate_and_write_status, write_initial_presentation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create all growth funnel workspace files and print a JSON status summary."
    )
    parser.add_argument("--name", required=True, help="Human-readable project name.")
    parser.add_argument(
        "--out",
        required=True,
        help="Workspace directory to create or update. Existing filled fields are preserved.",
    )
    parser.add_argument(
        "--language",
        default="",
        help="Output language for generated artifacts, usually the user's chat language.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.out).expanduser().resolve()
    try:
        ensure_workspace(workspace, project_name=args.name, output_language=args.language)
        summary = validate_and_write_status(workspace)
        write_initial_presentation(workspace, summary)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
