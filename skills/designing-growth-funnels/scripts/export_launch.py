#!/usr/bin/env python3
"""Write machine-readable launch exports outside final/."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workspace_lib import ensure_workspace, export_launch_package


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate launch JSON/CSV exports into exports/.")
    parser.add_argument("workspace_dir", help="Workspace directory to export.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        ensure_workspace(workspace)
        summary = export_launch_package(workspace)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
