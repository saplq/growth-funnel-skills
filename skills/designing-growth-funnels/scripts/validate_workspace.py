#!/usr/bin/env python3
"""Validate a growth funnel workspace and update 00_status.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workspace_lib import ensure_workspace, validate_and_write_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate workspace completeness, qualification, blocked artifacts, and warnings."
    )
    parser.add_argument("workspace_dir", help="Workspace directory to validate.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        ensure_workspace(workspace)
        summary = validate_and_write_status(workspace)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Completeness: {summary['completeness_score']}/100")
        print(f"Qualification: {summary['qualification_score']}/100")
        print(f"Research readiness: {summary['research_readiness_score']}/100")
        print(f"Decision: {summary['decision']}")
        if summary["critical_missing_fields"]:
            print("Missing: " + ", ".join(summary["critical_missing_fields"]))
        if summary["evidence_gaps"]:
            print("Evidence gaps: " + ", ".join(summary["evidence_gaps"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
