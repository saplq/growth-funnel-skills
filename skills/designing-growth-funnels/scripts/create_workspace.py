#!/usr/bin/env python3
"""Create an idempotent growth funnel workspace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workspace_lib import ensure_workspace, validate_and_write


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v2 growth funnel workspace.")
    parser.add_argument("--name", required=True, help="Human-readable project name.")
    parser.add_argument("--out", required=True, help="Workspace directory to create or update.")
    parser.add_argument("--language", default="English", help="Output language, inferred by the agent.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.out).expanduser().resolve()
    try:
        ensure_workspace(workspace, name=args.name, language=args.language)
        summary = validate_and_write(workspace)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
