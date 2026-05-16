#!/usr/bin/env python3
"""Record a normalized specialist result into a growth funnel workspace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from workspace_lib import (
    append_jsonl_unique,
    ensure_workspace,
    normalize_source,
    read_json,
    runtime_path,
    utc_now,
    validate_and_write,
    write_json,
)


REQUIRED_FIELDS = ["role", "topic_id", "task_id", "summary"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a specialist/subagent result.")
    parser.add_argument("workspace_dir", help="Workspace directory to update.")
    parser.add_argument("--input", required=True, help="JSON result path or '-' for stdin.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def read_result(source: str) -> dict[str, Any]:
    raw = sys.stdin.read() if source == "-" else Path(source).expanduser().read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("agent result must be a JSON object")
    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        raise ValueError("agent result missing required fields: " + ", ".join(missing))
    return data


def normalize_result(data: dict[str, Any]) -> dict[str, Any]:
    def listify(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    return {
        "role": str(data.get("role", "")).strip(),
        "topic_id": str(data.get("topic_id", "")).strip(),
        "task_id": str(data.get("task_id", "")).strip(),
        "summary": str(data.get("summary", "")).strip(),
        "key_findings": [str(item).strip() for item in listify(data.get("key_findings")) if str(item).strip()],
        "citations": listify(data.get("citations")),
        "freshness_date": str(data.get("freshness_date") or data.get("retrieved_at") or "").strip(),
        "confidence": str(data.get("confidence") or "unknown").strip(),
        "open_questions": [str(item).strip() for item in listify(data.get("open_questions")) if str(item).strip()],
        "next_action": str(data.get("next_action") or "").strip(),
        "recorded_at": utc_now(),
    }


def citation_sources(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, citation in enumerate(result.get("citations", []), start=1):
        if isinstance(citation, str):
            raw = {"url": citation, "title": citation}
        elif isinstance(citation, dict):
            raw = dict(citation)
        else:
            continue
        if not raw.get("url"):
            continue
        raw.setdefault("retrieved_at", result.get("freshness_date", ""))
        raw.setdefault("confidence", result.get("confidence", "unknown"))
        raw.setdefault("used_in", [result.get("topic_id", "")])
        raw.setdefault("source_type", "current_practice" if result.get("role") == "research" else "other")
        rows.append(normalize_source(raw, index=index))
    return rows


def update_task_status(workspace: Path, result: dict[str, Any]) -> None:
    path = runtime_path(workspace, "agent_tasks.json")
    tasks = read_json(path, [])
    if not isinstance(tasks, list):
        tasks = []
    updated = False
    for task in tasks:
        if task.get("task_id") == result["task_id"] or (
            task.get("role") == result["role"] and task.get("topic_id") == result["topic_id"]
        ):
            task["status"] = "completed"
            task["summary"] = result["summary"]
            task["updated_at"] = result["recorded_at"]
            updated = True
    if not updated:
        tasks.append(
            {
                "task_id": result["task_id"],
                "role": result["role"],
                "topic_id": result["topic_id"],
                "status": "completed",
                "summary": result["summary"],
                "updated_at": result["recorded_at"],
            }
        )
    write_json(path, tasks)


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        ensure_workspace(workspace)
        result = normalize_result(read_result(args.input))
        result_added = append_jsonl_unique(runtime_path(workspace, "agent_results.jsonl"), [result], ["task_id", "summary"])
        sources_added = append_jsonl_unique(runtime_path(workspace, "sources.jsonl"), citation_sources(result), ["url", "title"])
        update_task_status(workspace, result)
        summary = validate_and_write(workspace)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "changed": {
                    "agent_results_added": result_added,
                    "source_rows_added": sources_added,
                },
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
