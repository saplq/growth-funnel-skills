#!/usr/bin/env python3
"""Shared helpers for the designing-growth-funnels v2 workspace."""

from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VERSION = "2.0.0"

RUNTIME_FILES = [
    "run_state.json",
    "intake.json",
    "topics.json",
    "agent_tasks.json",
    "agent_results.jsonl",
    "sources.jsonl",
    "competitors.csv",
    "gaps.json",
]

COMPETITOR_HEADERS = [
    "competitor",
    "domain",
    "positioning",
    "pricing",
    "primary_cta",
    "onboarding_pattern",
    "proof",
    "first_value_path",
    "observed_weaknesses",
    "source",
    "confidence",
    "retrieved_at",
    "notes",
]

FINAL_PAGES = [
    ("00_index", "Index"),
    ("01_status_next_steps", "Status and Next Steps"),
    ("02_intake_brief", "Intake Brief"),
    ("03_research_evidence", "Research Evidence"),
    ("04_competitor_map", "Competitor Map"),
    ("05_funnel_blueprint", "Funnel Blueprint"),
    ("06_screen_specs", "Screen Specs"),
    ("07_tracking_plan", "Tracking Plan"),
    ("08_experiment_card", "Experiment Card"),
    ("09_risks_and_gaps", "Risks and Gaps"),
    ("10_execution_plan", "Execution Plan"),
]

FINAL_FORBIDDEN_SUFFIXES = {".json", ".jsonl", ".csv", ".yaml", ".yml", ".css"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "funnel-workspace"


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return bool(str(value).strip())


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "да", "истина"}


def detect_language(text: str) -> str:
    if re.search(r"[А-Яа-яЁё]", text):
        return "Russian"
    return "English"


def is_russian(language_or_data: Any) -> bool:
    if isinstance(language_or_data, dict):
        language = output_language(language_or_data)
    else:
        language = str(language_or_data or "")
    return language.lower().startswith(("ru", "rus", "рус"))


def output_language(data: dict[str, Any]) -> str:
    intake = data.get("intake") if isinstance(data.get("intake"), dict) else {}
    state = data.get("state") if isinstance(data.get("state"), dict) else {}
    return str(intake.get("output_language") or state.get("output_language") or "English")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    reject_symlink(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}") from exc


def write_json(path: Path, data: Any) -> None:
    write_text_file(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    reject_symlink(path)
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    write_text_file(path, "\n".join(lines) + ("\n" if lines else ""))


def append_jsonl_unique(path: Path, rows: list[dict[str, Any]], key_fields: list[str]) -> int:
    existing = read_jsonl(path)
    by_signature = {signature_for(row, key_fields): row for row in existing}
    signatures = set(by_signature)
    added = 0
    for row in rows:
        signature = signature_for(row, key_fields)
        if not signature:
            continue
        if signature in signatures:
            merge_missing_fields(by_signature[signature], row)
            continue
        existing.append(row)
        by_signature[signature] = row
        signatures.add(signature)
        added += 1
    write_jsonl(path, existing)
    return added


def signature_for(row: dict[str, Any], key_fields: list[str]) -> str:
    values = [str(row.get(field, "")).strip().lower() for field in key_fields]
    if not any(values):
        return ""
    return "|".join(values)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    reject_symlink(path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []
        rows = []
        for row in reader:
            clean = {key: (value or "").strip() for key, value in row.items() if key}
            if any(clean.values()):
                rows.append(clean)
        return rows


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    reject_symlink(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def append_csv_unique(path: Path, headers: list[str], rows: list[dict[str, str]], key_fields: list[str]) -> int:
    existing = read_csv(path)
    by_signature = {signature_for(row, key_fields): row for row in existing}
    signatures = set(by_signature)
    added = 0
    for row in rows:
        normalized = {key: str(row.get(key, "")).strip() for key in headers}
        signature = signature_for(normalized, key_fields)
        if not signature:
            continue
        if signature in signatures:
            merge_missing_fields(by_signature[signature], normalized)
            continue
        existing.append(normalized)
        by_signature[signature] = normalized
        signatures.add(signature)
        added += 1
    write_csv(path, headers, existing)
    return added


def runtime_dir(workspace: Path) -> Path:
    return workspace / "runtime"


def final_dir(workspace: Path) -> Path:
    return workspace / "final"


def runtime_path(workspace: Path, filename: str) -> Path:
    return runtime_dir(workspace) / filename


def reject_symlink(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to read or write symlinked workspace path: {path}")


def write_text_file(path: Path, text: str) -> None:
    reject_symlink(path)
    path.write_text(text, encoding="utf-8")


def merge_missing_fields(target: dict[str, Any], incoming: dict[str, Any]) -> bool:
    changed = False
    for key, value in incoming.items():
        target_value = target.get(key)
        target_unknown = str(target_value).strip().lower() == "unknown"
        incoming_known = str(value).strip().lower() not in {"", "unknown"}
        if present(value) and (not present(target_value) or (target_unknown and incoming_known)):
            target[key] = value
            changed = True
    return changed


def default_intake(name: str, language: str) -> dict[str, Any]:
    return {
        "project_name": name,
        "output_language": language,
        "offer": "",
        "icp": "",
        "primary_persona": "",
        "jtbd": "",
        "target_kpi": "",
        "primary_channel": "",
        "pricing": "",
        "time_to_first_value_minutes": "",
        "sales_motion": "",
        "product_constraints": "",
        "unit_economics": "",
        "implementation_bandwidth": "",
        "experiment_bandwidth": "",
        "explicit_no_proof_yet": False,
        "proof_assets": [],
        "metrics": [],
        "assumptions": [],
    }


def default_topics(language: str = "English") -> list[dict[str, str]]:
    ru = is_russian(language)
    titles = [
        ("index", "Оглавление" if ru else "Index"),
        ("status_next_steps", "Статус и следующие шаги" if ru else "Status and Next Steps"),
        ("intake_brief", "Intake brief" if not ru else "Intake brief"),
        ("research_evidence", "Research и evidence" if ru else "Research Evidence"),
        ("competitor_map", "Карта конкурентов" if ru else "Competitor Map"),
        ("funnel_blueprint", "Blueprint воронки" if ru else "Funnel Blueprint"),
        ("screen_specs", "Спецификация экранов" if ru else "Screen Specs"),
        ("tracking_plan", "План трекинга" if ru else "Tracking Plan"),
        ("experiment_card", "Карточка эксперимента" if ru else "Experiment Card"),
        ("risks_and_gaps", "Риски и gaps" if ru else "Risks and Gaps"),
        ("execution_plan", "План исполнения" if ru else "Execution Plan"),
    ]
    return [
        {"topic_id": topic_id, "title": title, "status": "blocked", "purpose": ""}
        for topic_id, title in titles
    ]


def default_tasks() -> list[dict[str, str]]:
    roles = ["intake", "planner", "research", "competitor", "synthesis", "compiler_reviewer"]
    return [
        {
            "task_id": f"{role}-1",
            "role": role,
            "topic_id": role if role != "compiler_reviewer" else "final_pack",
            "status": "pending",
            "summary": "",
        }
        for role in roles
    ]


def default_state(name: str, language: str) -> dict[str, Any]:
    now = utc_now()
    return {
        "version": VERSION,
        "workspace_name": name,
        "output_language": language,
        "created_at": now,
        "updated_at": now,
        "phase": "intake",
        "minimum_gate_satisfied": False,
        "scores": {"completeness": 0, "qualification": 0, "research_readiness": 0},
        "artifact_status": {},
        "critical_missing_fields": [],
        "evidence_gaps": [],
        "contradictions": [],
        "warnings": [],
        "next_best_input": [],
    }


def ensure_workspace(workspace: Path, name: str | None = None, language: str = "English") -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    for directory in [runtime_dir(workspace), final_dir(workspace)]:
        reject_symlink(directory)
        directory.mkdir(parents=True, exist_ok=True)
        reject_symlink(directory)

    state_path = runtime_path(workspace, "run_state.json")
    intake_path = runtime_path(workspace, "intake.json")
    topics_path = runtime_path(workspace, "topics.json")
    tasks_path = runtime_path(workspace, "agent_tasks.json")
    results_path = runtime_path(workspace, "agent_results.jsonl")
    sources_path = runtime_path(workspace, "sources.jsonl")
    competitors_path = runtime_path(workspace, "competitors.csv")
    gaps_path = runtime_path(workspace, "gaps.json")

    workspace_name = name or workspace.name
    if not state_path.exists():
        write_json(state_path, default_state(workspace_name, language))
    if not intake_path.exists():
        write_json(intake_path, default_intake(workspace_name, language))
    if not topics_path.exists():
        write_json(topics_path, default_topics(language))
    if not tasks_path.exists():
        write_json(tasks_path, default_tasks())
    if not results_path.exists():
        write_jsonl(results_path, [])
    if not sources_path.exists():
        write_jsonl(sources_path, [])
    if not competitors_path.exists():
        write_csv(competitors_path, COMPETITOR_HEADERS, [])
    if not gaps_path.exists():
        write_json(gaps_path, default_gaps(language))

    data = load_workspace(workspace)
    data["state"]["version"] = VERSION
    data["state"]["workspace_name"] = data["state"].get("workspace_name") or workspace_name
    data["state"]["output_language"] = data["state"].get("output_language") or language
    data["intake"]["project_name"] = data["intake"].get("project_name") or workspace_name
    data["intake"]["output_language"] = data["intake"].get("output_language") or language
    write_json(state_path, data["state"])
    write_json(intake_path, data["intake"])
    return data


def default_gaps(language: str = "English") -> dict[str, Any]:
    return {
        "missing_fields": [],
        "evidence_gaps": [],
        "auto_collect": [],
        "ask_user": [],
        "blocked_recommendations": [],
        "conflicts": [],
        "updated_at": utc_now(),
        "output_language": language,
    }


def load_workspace(workspace: Path) -> dict[str, Any]:
    return {
        "workspace": workspace,
        "state": read_json(runtime_path(workspace, "run_state.json"), {}),
        "intake": read_json(runtime_path(workspace, "intake.json"), {}),
        "topics": read_json(runtime_path(workspace, "topics.json"), []),
        "tasks": read_json(runtime_path(workspace, "agent_tasks.json"), []),
        "agent_results": read_jsonl(runtime_path(workspace, "agent_results.jsonl")),
        "sources": read_jsonl(runtime_path(workspace, "sources.jsonl")),
        "competitors": read_csv(runtime_path(workspace, "competitors.csv")),
        "gaps": read_json(runtime_path(workspace, "gaps.json"), {}),
    }


def missing_fields(intake: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not present(intake.get("offer")):
        missing.append("offer")
    if not (present(intake.get("icp")) or present(intake.get("primary_persona"))):
        missing.append("icp_or_primary_persona")
    if not present(intake.get("target_kpi")):
        missing.append("target_kpi")
    if not present(intake.get("primary_channel")):
        missing.append("primary_channel")
    proof_assets = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
    if not proof_assets and not truthy(intake.get("explicit_no_proof_yet")):
        missing.append("proof_assets_or_explicit_no_proof_yet")
    return missing


def minimum_gate_satisfied(intake: dict[str, Any]) -> bool:
    return not missing_fields(intake)


def source_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().removeprefix("www.")


def evidence_gaps(data: dict[str, Any]) -> list[str]:
    sources = data.get("sources", [])
    competitors = data.get("competitors", [])
    gaps: list[str] = []
    if not sources:
        gaps.append("source registry has no current sources")
    if len(competitors) < 3:
        gaps.append("competitor map has fewer than 3 competitors")
    current_sensitive = {"pricing", "changelog", "current_practice", "competitor"}
    for source in sources:
        label = source.get("url") or source.get("title") or "source"
        for field in ["url", "title", "publisher", "source_type", "freshness", "confidence"]:
            if not present(source.get(field)):
                gaps.append(f"source missing {field}: {label}")
        if not present(source.get("used_in")):
            gaps.append(f"source missing used_in: {label}")
        source_type = str(source.get("source_type", "")).strip().lower()
        if source_type in current_sensitive and not present(source.get("retrieved_at")):
            gaps.append(f"{source_type} source missing retrieved_at: {label}")
    for row in competitors:
        if (present(row.get("pricing")) or present(row.get("source"))) and not present(row.get("retrieved_at")):
            label = row.get("competitor") or row.get("domain") or "competitor"
            gaps.append(f"competitor pricing/source missing retrieved_at: {label}")
    return dedupe(gaps)


def contradictions(data: dict[str, Any]) -> list[str]:
    intake = data.get("intake", {})
    proof_assets = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
    conflicts = []
    if proof_assets and truthy(intake.get("explicit_no_proof_yet")):
        conflicts.append("explicit_no_proof_yet is true but proof assets exist")
    return conflicts


def completeness_score(data: dict[str, Any]) -> int:
    intake = data.get("intake", {})
    required = 5
    missing_count = len(missing_fields(intake))
    base = max(0, int(((required - missing_count) / required) * 70))
    optional_fields = [
        "jtbd",
        "pricing",
        "time_to_first_value_minutes",
        "sales_motion",
        "product_constraints",
        "unit_economics",
        "implementation_bandwidth",
        "experiment_bandwidth",
    ]
    optional_score = sum(1 for field in optional_fields if present(intake.get(field))) * 3
    metrics_score = 3 if intake.get("metrics") else 0
    return min(100, base + optional_score + metrics_score)


def qualification_score(data: dict[str, Any]) -> int:
    intake = data.get("intake", {})
    score = 0
    if present(intake.get("offer")):
        score += 20
    proof_assets = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
    if proof_assets:
        score += 10
    elif truthy(intake.get("explicit_no_proof_yet")):
        score += 3
    if present(intake.get("primary_channel")) and (present(intake.get("icp")) or present(intake.get("primary_persona"))):
        score += 15
    if present(intake.get("target_kpi")):
        score += 15
    ttfv = numeric_value(intake.get("time_to_first_value_minutes"))
    if ttfv is not None:
        score += 15 if ttfv <= 5 else 8 if ttfv <= 30 else 4
    elif minimum_gate_satisfied(intake):
        score += 6
    if present(intake.get("pricing")) or present(intake.get("unit_economics")):
        score += 10
    if present(intake.get("implementation_bandwidth")) or present(intake.get("experiment_bandwidth")):
        score += 10
    if present(intake.get("jtbd")) or present(intake.get("primary_persona")):
        score += 5
    return min(100, score)


def research_readiness_score(data: dict[str, Any]) -> int:
    source_count = len(data.get("sources", []))
    competitor_count = len(data.get("competitors", []))
    agent_result_count = len(data.get("agent_results", []))
    dated_sources = sum(1 for row in data.get("sources", []) if present(row.get("retrieved_at")))
    return min(100, min(40, source_count * 10) + min(30, competitor_count * 10) + min(20, dated_sources * 5) + min(10, agent_result_count * 2))


def numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+(?:[\.,]\d+)?", str(value))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", "."))
    except ValueError:
        return None


def artifact_status(data: dict[str, Any]) -> dict[str, str]:
    intake = data.get("intake", {})
    gate = minimum_gate_satisfied(intake)
    sources = data.get("sources", [])
    competitors = data.get("competitors", [])
    results = data.get("agent_results", [])
    return {
        "runtime/intake.json": "ready" if not missing_fields(intake) else "partial" if any(present(v) for v in intake.values()) else "empty",
        "runtime/sources.jsonl": "ready" if sources else "empty",
        "runtime/competitors.csv": "ready" if len(competitors) >= 3 else "partial" if competitors else "empty",
        "runtime/agent_results.jsonl": "ready" if results else "empty",
        "runtime/gaps.json": "ready",
        "final": "draft" if gate else "blocked",
    }


def next_best_input(data: dict[str, Any], limit: int = 3) -> list[str]:
    ru = is_russian(data)
    questions = {
        "offer": "Какой оффер и какой результат он обещает?" if ru else "What is the offer and promised result?",
        "icp_or_primary_persona": "Кто основной ICP или primary persona?" if ru else "Who is the ICP or primary persona?",
        "target_kpi": "Какой один target KPI должна улучшить воронка?" if ru else "What one target KPI should this funnel improve?",
        "primary_channel": "Какой primary channel даст трафик или лидов?" if ru else "What primary channel will bring traffic or leads?",
        "proof_assets_or_explicit_no_proof_yet": "Есть proof assets, или явно пометить no proof yet?" if ru else "Do you have proof assets, or should this be marked no proof yet?",
    }
    priority = ["target_kpi", "offer", "icp_or_primary_persona", "primary_channel", "proof_assets_or_explicit_no_proof_yet"]
    missing = missing_fields(data.get("intake", {}))
    result = [questions[field] for field in priority if field in missing]
    if not result:
        gaps = evidence_gaps(data)
        if gaps:
            result.append("Собрать 3 свежих источника и 3 конкурента для research layer." if ru else "Collect 3 current sources and 3 competitors for the research layer.")
        else:
            result.append("Согласовать первый experiment card и owner." if ru else "Confirm the first experiment card and owner.")
    return result[:limit]


def decision(score: int) -> str:
    if score >= 70:
        return "go_to_funnel_build"
    if score >= 55:
        return "strategy_or_research_sprint"
    return "no_go_until_proposition_proof_or_measurement_improves"


def validate_and_write(workspace: Path) -> dict[str, Any]:
    ensure_workspace(workspace)
    data = load_workspace(workspace)
    language = output_language(data)
    missing = missing_fields(data["intake"])
    ev_gaps = evidence_gaps(data)
    conflicts = contradictions(data)
    completeness = completeness_score(data)
    qualification = qualification_score(data)
    research = research_readiness_score(data)
    gate = not missing
    statuses = artifact_status(data)
    phase = "ready" if gate and research >= 60 else "research" if gate else "intake"
    questions = next_best_input(data)

    state = data["state"]
    state.update(
        {
            "version": VERSION,
            "output_language": language,
            "updated_at": utc_now(),
            "phase": phase,
            "minimum_gate_satisfied": gate,
            "scores": {
                "completeness": completeness,
                "qualification": qualification,
                "research_readiness": research,
            },
            "artifact_status": statuses,
            "critical_missing_fields": missing,
            "evidence_gaps": ev_gaps,
            "contradictions": conflicts,
            "warnings": build_warnings(data, ev_gaps, conflicts),
            "next_best_input": questions,
            "decision": decision(qualification),
            "source_count": len(data["sources"]),
            "competitor_count": len(data["competitors"]),
        }
    )

    gaps = data["gaps"] if isinstance(data["gaps"], dict) else default_gaps(language)
    gaps.update(
        {
            "missing_fields": missing,
            "evidence_gaps": ev_gaps,
            "ask_user": questions,
            "auto_collect": auto_collect_tasks(data),
            "blocked_recommendations": blocked_recommendations(data),
            "conflicts": conflicts,
            "updated_at": state["updated_at"],
            "output_language": language,
        }
    )

    topics = data["topics"] if isinstance(data["topics"], list) else default_topics(language)
    for topic in topics:
        topic_id = topic.get("topic_id", "")
        if topic_id in {"index", "status_next_steps", "intake_brief", "risks_and_gaps", "execution_plan"}:
            topic["status"] = "ready"
        elif topic_id in {"research_evidence", "competitor_map"}:
            topic["status"] = "partial" if ev_gaps else "ready"
        else:
            topic["status"] = "draft" if gate else "blocked"

    write_json(runtime_path(workspace, "run_state.json"), state)
    write_json(runtime_path(workspace, "gaps.json"), gaps)
    write_json(runtime_path(workspace, "topics.json"), topics)

    summary = {
        "version": VERSION,
        "workspace": str(workspace),
        "runtime_dir": str(runtime_dir(workspace)),
        "final_dir": str(final_dir(workspace)),
        "output_language": language,
        "phase": phase,
        "minimum_gate_satisfied": gate,
        "completeness_score": completeness,
        "qualification_score": qualification,
        "research_readiness_score": research,
        "decision": state["decision"],
        "critical_missing_fields": missing,
        "evidence_gaps": ev_gaps,
        "contradictions": conflicts,
        "warnings": state["warnings"],
        "next_best_input": questions,
        "artifact_status": statuses,
        "source_count": len(data["sources"]),
        "competitor_count": len(data["competitors"]),
    }
    return summary


def build_warnings(data: dict[str, Any], gaps: list[str], conflicts: list[str]) -> list[str]:
    warnings = []
    if gaps:
        warnings.append("research evidence is incomplete")
    if conflicts:
        warnings.append("conflicting proof state needs resolution")
    ttfv = numeric_value(data.get("intake", {}).get("time_to_first_value_minutes"))
    if ttfv is not None and ttfv > 10:
        warnings.append("time to first value is long; consider demo, concierge setup, or sample-data preview")
    return warnings


def auto_collect_tasks(data: dict[str, Any]) -> list[str]:
    tasks = []
    if len(data.get("sources", [])) < 3:
        tasks.append("collect at least 3 current external sources with retrieval dates")
    if len(data.get("competitors", [])) < 3:
        tasks.append("collect at least 3 competitor rows with pricing, CTA, onboarding, and source")
    if not data.get("agent_results"):
        tasks.append("record at least one research or synthesis result when specialist work is used")
    return tasks


def blocked_recommendations(data: dict[str, Any]) -> list[str]:
    if minimum_gate_satisfied(data.get("intake", {})):
        return []
    return [
        "funnel blueprint",
        "screen specs",
        "tracking interpretation",
        "experiment decision",
    ]


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def normalize_source(raw: dict[str, Any], index: int = 1, default_type: str = "other") -> dict[str, Any]:
    url = str(raw.get("url") or "").strip()
    publisher = str(raw.get("publisher") or raw.get("domain") or source_domain(url) or "").strip()
    source_type = str(raw.get("source_type") or raw.get("type") or default_type or "other").strip() or "other"
    used_in = raw.get("used_in")
    if isinstance(used_in, str):
        used_in_value: list[str] = [used_in]
    elif isinstance(used_in, list):
        used_in_value = [str(item) for item in used_in if present(item)]
    else:
        used_in_value = []
    retrieved_at = str(raw.get("retrieved_at") or raw.get("freshness_date") or "").strip()
    return {
        "source_id": str(raw.get("source_id") or f"source-{index}"),
        "url": url,
        "title": str(raw.get("title") or publisher or url or "Untitled source").strip(),
        "publisher": publisher,
        "retrieved_at": retrieved_at,
        "source_type": source_type,
        "freshness": str(raw.get("freshness") or ("current" if retrieved_at else "unknown")).strip(),
        "confidence": str(raw.get("confidence") or "unknown").strip(),
        "used_in": used_in_value,
        "notes": str(raw.get("notes") or raw.get("summary") or "").strip(),
    }


def normalize_competitor(raw: dict[str, Any]) -> dict[str, str]:
    row = {key: str(raw.get(key, "") or "").strip() for key in COMPETITOR_HEADERS}
    if not row["domain"] and row["source"]:
        row["domain"] = source_domain(row["source"])
    return row


def update_intake(workspace: Path, updates: dict[str, Any], overwrite: bool = False) -> list[str]:
    data = load_workspace(workspace)
    intake = data["intake"]
    changed: list[str] = []
    for key, value in updates.items():
        if key == "proof_assets":
            existing = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
            for item in value if isinstance(value, list) else [value]:
                if present(item) and item not in existing:
                    existing.append(item)
                    changed.append(key)
            intake["proof_assets"] = existing
        elif key == "metrics":
            existing_metrics = intake.get("metrics") if isinstance(intake.get("metrics"), list) else []
            for item in value if isinstance(value, list) else [value]:
                if item and item not in existing_metrics:
                    existing_metrics.append(item)
                    changed.append(key)
            intake["metrics"] = existing_metrics
        elif overwrite or not present(intake.get(key)):
            if intake.get(key) != value:
                intake[key] = value
                changed.append(key)
    write_json(runtime_path(workspace, "intake.json"), intake)
    return dedupe(changed)


def write_final_page(
    workspace: Path,
    slug: str,
    title: str,
    markdown: str,
    nav: list[tuple[str, str]],
    language: str = "English",
) -> None:
    fd = final_dir(workspace)
    md_path = fd / f"{slug}.md"
    html_path = fd / f"{slug}.html"
    write_text_file(md_path, markdown.rstrip() + "\n")
    write_text_file(html_path, markdown_to_html_page(title, markdown, slug, nav, language))


def clean_final_dir(workspace: Path) -> None:
    fd = final_dir(workspace)
    fd.mkdir(parents=True, exist_ok=True)
    for path in fd.iterdir():
        if path.is_symlink():
            path.unlink()
        elif path.is_file() and (path.suffix in FINAL_FORBIDDEN_SUFFIXES or path.name == "style.css"):
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


def markdown_to_html_page(title: str, markdown: str, slug: str, nav: list[tuple[str, str]], language: str = "English") -> str:
    body = markdown_to_html(markdown)
    nav_html = "\n".join(
        f'<a class="nav-link{" active" if item_slug == slug else ""}" href="{item_slug}.html">{escape(item_title)}</a>'
        for item_slug, item_title in nav
    )
    index = [item_slug for item_slug, _ in nav].index(slug) if slug in [item_slug for item_slug, _ in nav] else 0
    prev_link = nav[index - 1][0] if index > 0 else ""
    next_link = nav[index + 1][0] if index < len(nav) - 1 else ""
    prev_html = f'<a class="pager prev" href="{prev_link}.html">Previous</a>' if prev_link else '<span class="pager disabled">Previous</span>'
    next_html = f'<a class="pager next" href="{next_link}.html">Next</a>' if next_link else '<span class="pager disabled">Next</span>'
    lang = "ru" if is_russian(language) else "en"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #17202a; --muted: #627386; --line: #d9e0e7; --accent: #0f766e; --bg: #f7f9fb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
    .layout {{ display: grid; grid-template-columns: minmax(220px, 280px) minmax(0, 1fr); min-height: 100vh; }}
    nav {{ border-right: 1px solid var(--line); background: #fff; padding: 24px 18px; position: sticky; top: 0; height: 100vh; overflow: auto; }}
    .brand {{ font-size: 13px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 16px; }}
    .nav-link {{ display: block; padding: 9px 10px; margin: 2px 0; border-radius: 6px; color: var(--ink); text-decoration: none; font-size: 14px; }}
    .nav-link.active, .nav-link:hover {{ background: #e7f5f2; color: #0f5f59; }}
    main {{ max-width: 980px; padding: 42px 42px 80px; }}
    h1 {{ font-size: 34px; line-height: 1.15; margin: 0 0 24px; }}
    h2 {{ font-size: 22px; margin-top: 32px; padding-top: 12px; border-top: 1px solid var(--line); }}
    h3 {{ font-size: 17px; margin-top: 24px; }}
    p, li {{ font-size: 16px; line-height: 1.62; }}
    code {{ background: #eef2f5; padding: 2px 5px; border-radius: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 24px; background: #fff; }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #edf3f5; }}
    .pager-row {{ display: flex; gap: 12px; justify-content: space-between; margin-top: 40px; }}
    .pager {{ border: 1px solid var(--line); background: #fff; color: var(--ink); padding: 10px 14px; border-radius: 6px; text-decoration: none; }}
    .pager.disabled {{ color: var(--muted); }}
    @media (max-width: 760px) {{ .layout {{ display: block; }} nav {{ position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }} main {{ padding: 28px 20px 56px; }} }}
  </style>
</head>
<body>
  <div class="layout">
    <nav>
      <div class="brand">Growth Funnel</div>
      {nav_html}
    </nav>
    <main>
      {body}
      <div class="pager-row">{prev_html}{next_html}</div>
    </main>
  </div>
</body>
</html>
"""


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html: list[str] = []
    in_ul = False
    in_ol = False
    in_table = False
    table_rows: list[list[str]] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html.append("</ul>")
            in_ul = False
        if in_ol:
            html.append("</ol>")
            in_ol = False

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not in_table:
            return
        if table_rows:
            html.append("<table>")
            for idx, cells in enumerate(table_rows):
                if idx == 1 and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells):
                    continue
                tag = "th" if idx == 0 else "td"
                html.append("<tr>" + "".join(f"<{tag}>{inline_md(cell.strip())}</{tag}>" for cell in cells) + "</tr>")
            html.append("</table>")
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            close_lists()
            in_table = True
            table_rows.append([cell for cell in stripped.strip("|").split("|")])
            continue
        flush_table()
        if not stripped:
            close_lists()
            continue
        if stripped.startswith("# "):
            close_lists()
            html.append(f"<h1>{inline_md(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            close_lists()
            html.append(f"<h2>{inline_md(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            close_lists()
            html.append(f"<h3>{inline_md(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            if not in_ul:
                close_lists()
                html.append("<ul>")
                in_ul = True
            html.append(f"<li>{inline_md(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s+", stripped):
            if not in_ol:
                close_lists()
                html.append("<ol>")
                in_ol = True
            numbered_text = re.sub(r"^\d+\.\s+", "", stripped)
            html.append(f"<li>{inline_md(numbered_text)}</li>")
        else:
            close_lists()
            html.append(f"<p>{inline_md(stripped)}</p>")
    flush_table()
    close_lists()
    return "\n".join(html)


def inline_md(text: str) -> str:
    escaped = escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def final_leakage(workspace: Path) -> list[str]:
    leaks = []
    fd = final_dir(workspace)
    if not fd.exists():
        return ["final directory is missing"]
    for path in fd.iterdir():
        if path.suffix in FINAL_FORBIDDEN_SUFFIXES or path.name == "style.css" or path.is_dir():
            leaks.append(path.name)
    return leaks
