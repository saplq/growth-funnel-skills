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


VERSION = "2.2.0"

READY_MIN_COMPETITORS = 3

RUNTIME_FILES = [
    "run_state.json",
    "intake.json",
    "topics.json",
    "agent_tasks.json",
    "agent_results.jsonl",
    "sources.jsonl",
    "competitors.csv",
    "gaps.json",
    "insights.json",
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
    ("00_index", "Start Here"),
    ("01_status_next_steps", "Decision Summary"),
    ("02_intake_brief", "Segments and Jobs"),
    ("03_research_evidence", "Evidence and Assumptions"),
    ("04_competitor_map", "Competitive Patterns"),
    ("05_funnel_blueprint", "Funnel Map"),
    ("06_screen_specs", "Screen Playbook"),
    ("07_tracking_plan", "Tracking and KPIs"),
    ("08_experiment_card", "Next Experiment"),
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


def topic_titles(language: str = "English") -> dict[str, str]:
    if is_russian(language):
        return {
            "index": "С чего начать",
            "status_next_steps": "Резюме решения",
            "intake_brief": "Сегменты и задачи",
            "research_evidence": "Данные и допущения",
            "competitor_map": "Конкурентные паттерны",
            "funnel_blueprint": "Карта воронки",
            "screen_specs": "Сценарии экранов/бота",
            "tracking_plan": "Метрики и события",
            "experiment_card": "Следующий эксперимент",
            "risks_and_gaps": "Риски и пробелы",
            "execution_plan": "План внедрения",
        }
    return {
        "index": "Start Here",
        "status_next_steps": "Decision Summary",
        "intake_brief": "Segments and Jobs",
        "research_evidence": "Evidence and Assumptions",
        "competitor_map": "Competitive Patterns",
        "funnel_blueprint": "Funnel Map",
        "screen_specs": "Screen Playbook",
        "tracking_plan": "Tracking and KPIs",
        "experiment_card": "Next Experiment",
        "risks_and_gaps": "Risks and Gaps",
        "execution_plan": "Execution Plan",
    }


def ui_text(language: str, key: str) -> str:
    ru = is_russian(language)
    values = {
        "previous": "Назад" if ru else "Previous",
        "next": "Далее" if ru else "Next",
        "start": "Начать" if ru else "Start",
        "brand": "Воронка роста" if ru else "Growth Funnel",
        "index_intro": "Короткий рабочий маршрут: что сделать, зачем это нужно и какой результат получить." if ru else "A compact working route: what to do, why it matters, and what result to expect.",
    }
    return values.get(key, key)


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
    titles = topic_titles(language)
    return [
        {"topic_id": topic_id, "title": title, "status": "blocked", "purpose": ""}
        for topic_id, title in titles.items()
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


def default_insights(language: str = "English") -> dict[str, Any]:
    return {
        "version": VERSION,
        "output_language": language,
        "decision_summary": {},
        "segments": [],
        "screens": [],
        "experiments": [],
        "risks": [],
        "evidence_refs": [],
        "assumptions": [],
        "confidence": "low",
        "updated_at": utc_now(),
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
    insights_path = runtime_path(workspace, "insights.json")

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
    if not insights_path.exists():
        write_json(insights_path, default_insights(language))

    data = load_workspace(workspace)
    data["state"]["version"] = VERSION
    data["state"]["workspace_name"] = data["state"].get("workspace_name") or workspace_name
    current_language = data["state"].get("output_language") or data["intake"].get("output_language")
    if is_russian(language) and not is_russian(current_language) and str(current_language or "").lower() in {"", "english", "en"}:
        data["state"]["output_language"] = "Russian"
        data["intake"]["output_language"] = "Russian"
        if isinstance(data.get("gaps"), dict):
            data["gaps"]["output_language"] = "Russian"
        if isinstance(data.get("insights"), dict):
            data["insights"]["output_language"] = "Russian"
    else:
        data["state"]["output_language"] = data["state"].get("output_language") or language
    data["intake"]["project_name"] = data["intake"].get("project_name") or workspace_name
    data["intake"]["output_language"] = data["intake"].get("output_language") or language
    write_json(state_path, data["state"])
    write_json(intake_path, data["intake"])
    write_json(gaps_path, data["gaps"] if isinstance(data.get("gaps"), dict) else default_gaps(data["state"]["output_language"]))
    write_json(insights_path, data["insights"] if isinstance(data.get("insights"), dict) else default_insights(data["state"]["output_language"]))
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
    state = read_json(runtime_path(workspace, "run_state.json"), {})
    intake = read_json(runtime_path(workspace, "intake.json"), {})
    language = str(intake.get("output_language") or state.get("output_language") or "English")
    return {
        "workspace": workspace,
        "state": state,
        "intake": intake,
        "topics": read_json(runtime_path(workspace, "topics.json"), []),
        "tasks": read_json(runtime_path(workspace, "agent_tasks.json"), []),
        "agent_results": read_jsonl(runtime_path(workspace, "agent_results.jsonl")),
        "sources": read_jsonl(runtime_path(workspace, "sources.jsonl")),
        "competitors": read_csv(runtime_path(workspace, "competitors.csv")),
        "gaps": read_json(runtime_path(workspace, "gaps.json"), {}),
        "insights": read_json(runtime_path(workspace, "insights.json"), default_insights(language)),
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


def recommendations_are_ready(data: dict[str, Any], research_score: int, gaps: list[str], conflicts: list[str]) -> bool:
    gate = minimum_gate_satisfied(data.get("intake", {}))
    return gate and research_score >= 60 and not gaps and not conflicts


def evidence_gaps(data: dict[str, Any]) -> list[str]:
    ru = is_russian(data)
    sources = data.get("sources", [])
    competitors = data.get("competitors", [])
    gaps: list[str] = []
    if not sources:
        gaps.append("нет свежих источников в реестре данных" if ru else "source registry has no current sources")
    if len(competitors) < READY_MIN_COMPETITORS:
        gaps.append(f"карта конкурентов содержит меньше {READY_MIN_COMPETITORS} конкурентов" if ru else f"competitor map has fewer than {READY_MIN_COMPETITORS} competitors")
    current_sensitive = {"pricing", "changelog", "current_practice", "competitor"}
    for source in sources:
        label = source.get("url") or source.get("title") or "source"
        for field in ["url", "title", "publisher", "source_type", "freshness", "confidence"]:
            if not present(source.get(field)):
                gaps.append(f"у источника не заполнено поле {field}: {label}" if ru else f"source missing {field}: {label}")
        if not present(source.get("used_in")):
            gaps.append(f"не указано, где используется источник: {label}" if ru else f"source missing used_in: {label}")
        source_type = str(source.get("source_type", "")).strip().lower()
        if source_type in current_sensitive and not present(source.get("retrieved_at")):
            gaps.append(f"у источника типа {source_type} нет даты проверки: {label}" if ru else f"{source_type} source missing retrieved_at: {label}")
    for row in competitors:
        if (present(row.get("pricing")) or present(row.get("source"))) and not present(row.get("retrieved_at")):
            label = row.get("competitor") or row.get("domain") or "competitor"
            gaps.append(f"у строки конкурента нет даты проверки: {label}" if ru else f"competitor pricing/source missing retrieved_at: {label}")
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
    research = research_readiness_score(data)
    ev_gaps = evidence_gaps(data)
    conflicts = contradictions(data)
    ready = recommendations_are_ready(data, research, ev_gaps, conflicts)
    return {
        "runtime/intake.json": "ready" if not missing_fields(intake) else "partial" if any(present(v) for v in intake.values()) else "empty",
        "runtime/sources.jsonl": "ready" if sources else "empty",
        "runtime/competitors.csv": "ready" if len(competitors) >= READY_MIN_COMPETITORS else "partial" if competitors else "empty",
        "runtime/agent_results.jsonl": "ready" if results else "empty",
        "runtime/gaps.json": "ready",
        "runtime/insights.json": "ready" if data.get("insights") else "empty",
        "final": "ready" if ready else "draft" if gate else "blocked",
    }


def next_best_input(data: dict[str, Any], limit: int = 3) -> list[str]:
    ru = is_russian(data)
    questions = {
        "offer": "Какой оффер и какой результат он обещает?" if ru else "What is the offer and promised result?",
        "icp_or_primary_persona": "Кто основная целевая аудитория или ключевой тип клиента?" if ru else "Who is the ICP or primary persona?",
        "target_kpi": "Какую одну главную метрику должна улучшить воронка?" if ru else "What one target KPI should this funnel improve?",
        "primary_channel": "Какой основной канал даст трафик или лидов?" if ru else "What primary channel will bring traffic or leads?",
        "proof_assets_or_explicit_no_proof_yet": "Есть доказательства результата, или явно пометить, что доказательств пока нет?" if ru else "Do you have proof assets, or should this be marked no proof yet?",
    }
    priority = ["target_kpi", "offer", "icp_or_primary_persona", "primary_channel", "proof_assets_or_explicit_no_proof_yet"]
    missing = missing_fields(data.get("intake", {}))
    result = [questions[field] for field in priority if field in missing]
    if not result:
        result = post_gate_questions(data)
        limit = min(limit, 2)
    return result[:limit]


def post_gate_questions(data: dict[str, Any]) -> list[str]:
    ru = is_russian(data)
    intake = data.get("intake", {})
    proof_assets = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
    result: list[str] = []
    if not present(intake.get("primary_persona")) and not present(intake.get("jtbd")):
        result.append("Какой сегмент самый важный на ближайшие 14 дней и почему?" if ru else "Which segment matters most in the next 14 days, and why?")
    if not present(intake.get("product_constraints")):
        result.append("Какой текущий экран, бот-шаг или письмо сильнее всего проседает? Пришлите текст или краткое описание." if ru else "Which current screen, bot step, or email is underperforming most? Share the copy or a short description.")
    if not proof_assets or truthy(intake.get("explicit_no_proof_yet")):
        result.append("Какое главное возражение нужно снять перед целевым действием?" if ru else "What is the main objection to resolve before the target action?")
    if not present(intake.get("time_to_first_value_minutes")):
        result.append("Где пользователь впервые получает ценность и сколько минут это занимает?" if ru else "Where does the user first receive value, and how many minutes does it take?")
    if len(data.get("sources", [])) < 3:
        result.append("Какие 1-2 свежих источника или примера нужно учесть перед финальным решением?" if ru else "Which 1-2 current sources or examples should be considered before finalizing the decision?")
    if not result:
        result.append("Кто владелец первого эксперимента и какой срок запуска?" if ru else "Who owns the first experiment, and what is the launch deadline?")
    return dedupe(result)


def decision(score: int) -> str:
    if score >= 70:
        return "go_to_funnel_build"
    if score >= 55:
        return "strategy_or_research_sprint"
    return "no_go_until_proposition_proof_or_measurement_improves"


def select_funnel_skeleton(data: dict[str, Any]) -> tuple[str, str]:
    intake = data.get("intake", {})
    ttfv = numeric_value(intake.get("time_to_first_value_minutes"))
    text = " ".join(
        str(intake.get(field, ""))
        for field in ["offer", "sales_motion", "primary_channel", "pricing", "product_constraints"]
    ).lower()
    if "enterprise" in text or "sales" in text or (ttfv is not None and ttfv > 10):
        return "demo_led", "High value or longer setup needs assisted trust-building before activation."
    if any(token in text for token in ["audit", "diagnos", "assessment", "аудит", "диагност"]):
        return "diagnostic_to_roadmap", "The funnel should create first value through diagnosis and a prioritized path."
    if ttfv is not None and ttfv <= 5:
        return "trial_to_value", "Fast first value supports a product-led trial-to-value path."
    return "diagnostic_to_roadmap", "Default to diagnosis-first until first-value timing is proven."


def skeleton_label(skeleton: str, ru: bool) -> str:
    values_ru = {
        "demo_led": "консультация с подготовленным контекстом",
        "diagnostic_to_roadmap": "полезная диагностика, затем понятный план действий",
        "trial_to_value": "быстрый первый результат, затем следующий шаг",
        "lead_magnet_to_consult": "полезный подбор, затем телефон и консультация",
    }
    values_en = {
        "demo_led": "assisted consultation path",
        "diagnostic_to_roadmap": "diagnosis to roadmap",
        "trial_to_value": "trial to first value",
        "lead_magnet_to_consult": "lead magnet to consultation",
    }
    values = values_ru if ru else values_en
    return values.get(skeleton, skeleton.replace("_", " "))


def decision_label(value: str, ru: bool) -> str:
    if not ru:
        return value
    values = {
        "go_to_funnel_build": "можно собирать рабочий черновик воронки",
        "strategy_or_research_sprint": "сначала нужен короткий стратегический/исследовательский спринт",
        "no_go_until_proposition_proof_or_measurement_improves": "рано строить ростовую воронку: нужен сильнее оффер, доказательства или измерение",
    }
    return values.get(value, value.replace("_", " "))


def skeleton_rationale_text(skeleton: str, fallback: str, ru: bool) -> str:
    if not ru:
        return fallback
    values = {
        "demo_led": "Высокая ценность или длинная настройка требуют доверия и assisted path до активации.",
        "diagnostic_to_roadmap": "Воронка должна дать первую ценность через диагностику и приоритетный план.",
        "trial_to_value": "Быстрая первая ценность поддерживает product-led путь от триала к результату.",
    }
    return values.get(skeleton, "Диагностика выбрана по умолчанию, пока время до первой ценности не подтверждено.")


def first_support_ref(evidence_refs: list[dict[str, Any]], assumptions: list[dict[str, Any]]) -> str:
    if evidence_refs:
        return str(evidence_refs[0].get("id") or evidence_refs[0].get("source_id") or "evidence")
    if assumptions:
        return str(assumptions[0].get("id") or "A1")
    return "A1"


def compile_insights(data: dict[str, Any], phase: str) -> dict[str, Any]:
    language = output_language(data)
    ru = is_russian(language)
    intake = data.get("intake", {})
    sources = data.get("sources", [])
    competitors = data.get("competitors", [])
    gate = minimum_gate_satisfied(intake)
    skeleton, rationale = select_funnel_skeleton(data)
    path_label = skeleton_label(skeleton, ru)
    rationale_text = skeleton_rationale_text(skeleton, rationale, ru)
    offer = dash_text(intake.get("offer"), ru)
    audience = dash_text(intake.get("icp") or intake.get("primary_persona"), ru)
    target_kpi = dash_text(intake.get("target_kpi"), ru)
    channel = dash_text(intake.get("primary_channel"), ru)
    evidence_refs = build_evidence_refs(sources)
    assumptions = build_assumptions(data, skeleton, ru)
    support = first_support_ref(evidence_refs, assumptions)
    confidence = "high" if phase == "ready" else "medium" if gate else "low"
    status = (
        ("готово к внедрению" if phase == "ready" else "черновик: нужен ресерч" if gate else "заблокировано: нужен входной контекст")
        if ru
        else ("ready to execute" if phase == "ready" else "draft: research needed" if gate else "blocked: intake needed")
    )

    decision_summary = {
        "status": status,
        "recommendation": (
            f"Строить воронку «{path_label}» для аудитории: {audience}. Сначала снять ключевое сомнение, затем показать первую ценность и только после этого вести к метрике «{target_kpi}»."
            if ru
            else f"Build a `{skeleton}` path for {audience}: resolve the core doubt, show first value, then move users toward `{target_kpi}`."
        ),
        "why": (
            f"Оффер «{offer}» приходит из канала «{channel}»; выбранный путь снижает риск общего лендинга без понятного первого действия."
            if ru
            else f"The `{offer}` offer comes through `{channel}`; this path reduces the risk of a generic page without a clear first action."
        ),
        "first_action": (
            "Собрать один приоритетный сегмент, его главное возражение и текущий шаг воронки; затем запускать первый экран или шаг бота только с записью событий."
            if ru
            else "Lock one priority segment, its main objection, and the current funnel step; then launch the first screen or bot step only with tracking in place."
        ),
        "target_kpi": target_kpi,
        "skeleton": skeleton,
        "path_label": path_label,
        "rationale": rationale_text,
        "support": support,
    }

    segments = [
        {
            "segment": audience,
            "job": dash_text(intake.get("jtbd"), ru),
            "pain": (
                f"Нужно понять, решает ли «{offer}» их ситуацию без долгого созвона или лишних шагов."
                if ru
                else f"They need to understand whether `{offer}` solves their situation without a long call or extra steps."
            ),
            "belief_shift": (
                "Это применимо к моей ситуации и стоит следующего действия."
                if ru
                else "This fits my situation and is worth the next action."
            ),
            "priority": "primary",
            "support": support,
            "confidence": confidence,
        }
    ]

    screens = build_screen_insights(intake, skeleton, support, confidence, ru)
    experiments = build_experiment_insights(intake, skeleton, support, confidence, ru)
    risks = build_risk_insights(data, support, ru)

    return {
        "version": VERSION,
        "output_language": language,
        "decision_summary": decision_summary,
        "segments": segments,
        "screens": screens,
        "experiments": experiments,
        "risks": risks,
        "evidence_refs": evidence_refs,
        "assumptions": assumptions,
        "confidence": confidence,
        "competitor_count": len(competitors),
        "updated_at": utc_now(),
    }


def dash_text(value: Any, ru: bool = False) -> str:
    text = "" if value is None else str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text or ("не указано" if ru else "not provided")


def build_evidence_refs(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs = []
    for index, source in enumerate(sources, start=1):
        source_id = str(source.get("source_id") or f"source-{index}")
        refs.append(
            {
                "id": source_id,
                "title": str(source.get("title") or source.get("url") or "Untitled source"),
                "url": str(source.get("url") or ""),
                "confidence": str(source.get("confidence") or "unknown"),
                "used_in": source.get("used_in") if isinstance(source.get("used_in"), list) else [],
            }
        )
    return refs


def build_assumptions(data: dict[str, Any], skeleton: str, ru: bool = False) -> list[dict[str, str]]:
    intake = data.get("intake", {})
    proof_assets = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
    assumptions: list[dict[str, str]] = []
    if len(data.get("sources", [])) < 3:
        assumptions.append({"id": "A1", "statement": "В слое ресерча меньше 3 свежих источников." if ru else "Research layer has fewer than 3 current sources.", "used_in": "decision_summary"})
    if len(data.get("competitors", [])) < 3:
        assumptions.append({"id": "A2", "statement": "Конкурентный паттерн предварительный, пока не записаны 3 конкурента." if ru else "Competitive pattern is provisional until 3 competitors are recorded.", "used_in": "competitive_patterns"})
    if not proof_assets or truthy(intake.get("explicit_no_proof_yet")):
        assumptions.append({"id": "A3", "statement": "Доказательства нужно подтвердить до обещаний рядом с основным призывом к действию." if ru else "Proof must be validated before claims are used near the primary CTA.", "used_in": "screen_playbook"})
    if not present(intake.get("time_to_first_value_minutes")):
        assumptions.append({"id": "A4", "statement": (f"Путь «{skeleton_label(skeleton, ru)}» предполагает, что время до первой ценности еще нужно подтвердить." if ru else f"Skeleton `{skeleton}` assumes first value timing still needs validation."), "used_in": "funnel_map"})
    if not assumptions:
        assumptions.append({"id": "A1", "statement": "Текст экранов все еще нужно проверить на языке реальных клиентов перед запуском." if ru else "Screen copy still needs validation against customer language before launch.", "used_in": "screen_playbook"})
    return assumptions


def build_screen_insights(intake: dict[str, Any], skeleton: str, support: str, confidence: str, ru: bool) -> list[dict[str, str]]:
    target_kpi = dash_text(intake.get("target_kpi"), ru)
    offer = dash_text(intake.get("offer"), ru)
    audience = dash_text(intake.get("icp") or intake.get("primary_persona"), ru)
    if ru:
        return [
            {
                "stage": "Вход",
                "target_belief": "Это про мою ситуацию.",
                "content": f"Один экран с обещанием «{offer}», сегментом «{audience}» и примером результата.",
                "cta": "Начать диагностику",
                "metric": "Начали ввод / увидели вход",
                "guardrail": "доля нецелевых стартов",
                "proof_needed": "1 короткое доказательство или честная пометка, что доказательств пока нет",
                "support": support,
                "confidence": confidence,
            },
            {
                "stage": "Уточнение",
                "target_belief": "Система понимает мой контекст.",
                "content": "3-5 вопросов только о сегменте, текущем шаге, возражении и цели.",
                "cta": "Получить разбор",
                "metric": "Завершили ввод / начали ввод",
                "guardrail": "время заполнения",
                "proof_needed": "нет",
                "support": support,
                "confidence": confidence,
            },
            {
                "stage": "Первая ценность",
                "target_belief": "Проблема конкретна и решаема.",
                "content": f"Показать 1 главное узкое место и маршрут к метрике «{target_kpi}».",
                "cta": "Показать план",
                "metric": "Увидели план / получили разбор",
                "guardrail": "доля резервных разборов",
                "proof_needed": "пример похожего результата или явное допущение",
                "support": support,
                "confidence": confidence,
            },
            {
                "stage": "Конверсия",
                "target_belief": "Следующий шаг безопасен и полезен.",
                "content": "Один следующий шаг с ожиданиями, сроком и тем, что пользователь получит.",
                "cta": "Запланировать следующий шаг",
                "metric": target_kpi,
                "guardrail": "низкое качество лидов",
                "proof_needed": "элемент доверия рядом с призывом к действию",
                "support": support,
                "confidence": confidence,
            },
        ]
    return [
        {
            "stage": "Entry",
            "target_belief": "This is for my situation.",
            "content": f"One screen with the `{offer}` promise, `{audience}` segment, and a result preview.",
            "cta": "Start diagnosis",
            "metric": "Brief Started / Entry Viewed",
            "guardrail": "low-quality starts",
            "proof_needed": "one short proof point or an explicit no-proof state",
            "support": support,
            "confidence": confidence,
        },
        {
            "stage": "Qualification",
            "target_belief": "The system understands my context.",
            "content": "3-5 questions only about segment, current step, objection, and goal.",
            "cta": "Get diagnosis",
            "metric": "Brief Completed / Brief Started",
            "guardrail": "completion time",
            "proof_needed": "none",
            "support": support,
            "confidence": confidence,
        },
        {
            "stage": "First Value",
            "target_belief": "The problem is specific and fixable.",
            "content": f"Show the main bottleneck and a route to `{target_kpi}`.",
            "cta": "Show plan",
            "metric": "Plan Viewed / Diagnosis Generated",
            "guardrail": "fallback diagnosis rate",
            "proof_needed": "similar result example or explicit assumption",
            "support": support,
            "confidence": confidence,
        },
        {
            "stage": "Conversion",
            "target_belief": "The next step is safe and useful.",
            "content": "One next step with expectations, timing, and what the user receives.",
            "cta": "Book next step",
            "metric": target_kpi,
            "guardrail": "low-quality leads",
            "proof_needed": "trust element next to CTA",
            "support": support,
            "confidence": confidence,
        },
    ]


def build_experiment_insights(intake: dict[str, Any], skeleton: str, support: str, confidence: str, ru: bool) -> list[dict[str, str]]:
    audience = dash_text(intake.get("icp") or intake.get("primary_persona"), ru)
    target_kpi = dash_text(intake.get("target_kpi"), ru)
    channel = dash_text(intake.get("primary_channel"), ru)
    path_label = skeleton_label(skeleton, ru)
    if ru:
        return [
            {
                "name": "Проверка первого ценностного шага",
                "hypothesis": f"Если путь «{path_label}» даст аудитории «{audience}» конкретный разбор до основного призыва к действию, то метрика «{target_kpi}» вырастет для трафика из «{channel}».",
                "change": "Запустить один входной экран или шаг бота с примером диагностики и одним призывом к действию.",
                "primary_metric": target_kpi,
                "guardrail": "качество лидов, потери событий, время до первого результата",
                "decision_rule": "Оставить только если основная метрика растет, контрольные метрики не ухудшаются, а качественная обратная связь не противоречит результату.",
                "support": support,
                "confidence": confidence,
            }
        ]
    return [
        {
            "name": "First-value step test",
            "hypothesis": f"If the `{skeleton}` path gives {audience} a concrete diagnosis before the main CTA, `{target_kpi}` will improve for traffic from `{channel}`.",
            "change": "Launch one entry screen or bot step with a diagnosis preview and one CTA.",
            "primary_metric": target_kpi,
            "guardrail": "lead quality, event loss, time to first value",
            "decision_rule": "Keep it only if the primary metric improves, guardrails hold, and qualitative feedback does not contradict the result.",
            "support": support,
            "confidence": confidence,
        }
    ]


def build_risk_insights(data: dict[str, Any], support: str, ru: bool) -> list[dict[str, str]]:
    intake = data.get("intake", {})
    risks: list[dict[str, str]] = []
    if len(data.get("sources", [])) < 3:
        risks.append(
            {
                "risk": "Недостаточно свежих источников" if ru else "Not enough current sources",
                "level": "высокий" if ru else "high",
                "mitigation": "Не помечать рекомендации как готовые, пока не записаны минимум 3 источника." if ru else "Do not mark recommendations ready until at least 3 sources are recorded.",
                "support": support,
            }
        )
    if len(data.get("competitors", [])) < 3:
        risks.append(
            {
                "risk": "Слабая карта конкурентов" if ru else "Weak competitor map",
                "level": "средний" if ru else "medium",
                "mitigation": "Добавить 3 конкурента с призывом к действию, ценой/онбордингом и датой получения." if ru else "Add 3 competitors with CTA, pricing/onboarding, and retrieval dates.",
                "support": support,
            }
        )
    if truthy(intake.get("explicit_no_proof_yet")):
        risks.append(
            {
                "risk": "Нет доказательств результата" if ru else "No proof of result yet",
                "level": "высокий" if ru else "high",
                "mitigation": "Честно указать состояние доказательств и не писать обещания, пока не появятся доказательства результата." if ru else "Use an honest proof state and avoid claims until proof assets exist.",
                "support": support,
            }
        )
    if not risks:
        risks.append(
            {
                "risk": "Нужно подтвердить формулировки на реальных пользователях" if ru else "Messaging still needs user validation",
                "level": "низкий" if ru else "low",
                "mitigation": "Проверить первый экран на 5-10 целевых пользователях перед масштабированием." if ru else "Review the first screen with 5-10 target users before scaling.",
                "support": support,
            }
        )
    return risks


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
    ready = recommendations_are_ready(data, research, ev_gaps, conflicts)
    statuses = artifact_status(data)
    phase = "ready" if ready else "research" if gate else "intake"
    questions = next_best_input(data)
    insights = compile_insights(data, phase)

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
    localized_titles = topic_titles(language)
    for topic in topics:
        topic_id = topic.get("topic_id", "")
        if topic_id in localized_titles:
            topic["title"] = localized_titles[topic_id]
        if topic_id in {"index", "status_next_steps", "intake_brief", "risks_and_gaps", "execution_plan"}:
            topic["status"] = "ready"
        elif topic_id in {"research_evidence", "competitor_map"}:
            topic["status"] = "partial" if ev_gaps else "ready"
        else:
            topic["status"] = "draft" if gate else "blocked"

    write_json(runtime_path(workspace, "run_state.json"), state)
    write_json(runtime_path(workspace, "gaps.json"), gaps)
    write_json(runtime_path(workspace, "topics.json"), topics)
    write_json(runtime_path(workspace, "insights.json"), insights)

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
        "recommendations_ready": ready,
    }
    return summary


def build_warnings(data: dict[str, Any], gaps: list[str], conflicts: list[str]) -> list[str]:
    ru = is_russian(data)
    warnings = []
    if gaps:
        warnings.append("данных для уверенного решения пока не хватает" if ru else "research evidence is incomplete")
    if conflicts:
        warnings.append("состояние доказательств противоречиво и требует уточнения" if ru else "conflicting proof state needs resolution")
    ttfv = numeric_value(data.get("intake", {}).get("time_to_first_value_minutes"))
    if ttfv is not None and ttfv > 10:
        warnings.append("первая ценность появляется поздно; нужен пример результата, демо или concierge-разбор" if ru else "time to first value is long; consider demo, concierge setup, or sample-data preview")
    return warnings


def auto_collect_tasks(data: dict[str, Any]) -> list[str]:
    ru = is_russian(data)
    tasks = []
    if len(data.get("sources", [])) < 3:
        tasks.append("собрать минимум 3 свежих внешних источника с датой проверки" if ru else "collect at least 3 current external sources with retrieval dates")
    if len(data.get("competitors", [])) < READY_MIN_COMPETITORS:
        tasks.append(f"собрать минимум {READY_MIN_COMPETITORS} конкурента: цена, призыв к действию, первые шаги пользователя, источник и дата проверки" if ru else f"collect at least {READY_MIN_COMPETITORS} competitor rows with pricing, CTA, onboarding, and source")
    if not data.get("agent_results"):
        tasks.append("записать минимум один результат исследования или синтеза, если использовалась отдельная исследовательская работа" if ru else "record at least one research or synthesis result when specialist work is used")
    return tasks


def blocked_recommendations(data: dict[str, Any]) -> list[str]:
    if minimum_gate_satisfied(data.get("intake", {})):
        return []
    if is_russian(data):
        return [
            "карта воронки",
            "сценарии экранов/бота",
            "интерпретация метрик",
            "решение по эксперименту",
        ]
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
    previous_label = ui_text(language, "previous")
    next_label = ui_text(language, "next")
    prev_html = f'<a class="pager prev" href="{prev_link}.html">{escape(previous_label)}</a>' if prev_link else f'<span class="pager disabled">{escape(previous_label)}</span>'
    next_html = f'<a class="pager next" href="{next_link}.html">{escape(next_label)}</a>' if next_link else f'<span class="pager disabled">{escape(next_label)}</span>'
    lang = "ru" if is_russian(language) else "en"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #17202a; --muted: #627386; --line: #d9e0e7; --accent: #0f766e; --bg: #f7f9fb; --warn: #b45309; --bad: #b42318; --good: #047857; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
    .layout {{ display: grid; grid-template-columns: minmax(220px, 280px) minmax(0, 1fr); min-height: 100vh; }}
    nav {{ border-right: 1px solid var(--line); background: #fff; padding: 24px 18px; position: sticky; top: 0; height: 100vh; overflow: auto; }}
    .brand {{ font-size: 13px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 16px; }}
    .nav-link {{ display: block; padding: 9px 10px; margin: 2px 0; border-radius: 6px; color: var(--ink); text-decoration: none; font-size: 14px; }}
    .nav-link.active, .nav-link:hover {{ background: #e7f5f2; color: #0f5f59; }}
    main {{ max-width: 1040px; padding: 42px 42px 80px; }}
    h1 {{ font-size: 34px; line-height: 1.15; margin: 0 0 24px; }}
    h2 {{ font-size: 22px; margin-top: 32px; padding-top: 12px; border-top: 1px solid var(--line); }}
    h3 {{ font-size: 17px; margin-top: 24px; }}
    p, li {{ font-size: 16px; line-height: 1.62; }}
    blockquote {{ margin: 0 0 24px; padding: 18px 20px; border: 1px solid #b7d8d2; border-left: 5px solid var(--accent); border-radius: 8px; background: #f0fbf8; }}
    blockquote p {{ margin: 0; font-size: 17px; color: #103f3a; }}
    code {{ background: #eef2f5; padding: 2px 5px; border-radius: 4px; }}
    table {{ border-collapse: separate; border-spacing: 0; width: 100%; margin: 16px 0 28px; background: #fff; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #edf3f5; font-size: 13px; text-transform: uppercase; color: #425466; }}
    td.risk-high, td.risk-высокий {{ color: var(--bad); font-weight: 700; background: #fff1f0; }}
    td.risk-medium, td.risk-средний {{ color: var(--warn); font-weight: 700; background: #fff8eb; }}
    td.risk-low, td.risk-низкий {{ color: var(--good); font-weight: 700; background: #ecfdf3; }}
    td.confidence-high, td.confidence-высокая {{ color: var(--good); font-weight: 700; }}
    td.confidence-medium, td.confidence-средняя {{ color: var(--warn); font-weight: 700; }}
    td.confidence-low, td.confidence-низкая {{ color: var(--bad); font-weight: 700; }}
    .pager-row {{ display: flex; gap: 12px; justify-content: space-between; margin-top: 40px; }}
    .pager {{ border: 1px solid var(--line); background: #fff; color: var(--ink); padding: 10px 14px; border-radius: 6px; text-decoration: none; }}
    .pager.disabled {{ color: var(--muted); }}
    @media (max-width: 760px) {{ .layout {{ display: block; }} nav {{ position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }} main {{ padding: 28px 20px 56px; }} }}
  </style>
</head>
<body>
  <div class="layout">
    <nav>
      <div class="brand">{escape(ui_text(language, "brand"))}</div>
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
    in_blockquote = False
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

    def close_blockquote() -> None:
        nonlocal in_blockquote
        if in_blockquote:
            html.append("</blockquote>")
            in_blockquote = False

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
                html.append(
                    "<tr>"
                    + "".join(
                        f'<{tag}{table_cell_attr(cell.strip()) if tag == "td" else ""}>{inline_md(cell.strip())}</{tag}>'
                        for cell in cells
                    )
                    + "</tr>"
                )
            html.append("</table>")
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            close_lists()
            close_blockquote()
            in_table = True
            table_rows.append([cell for cell in stripped.strip("|").split("|")])
            continue
        flush_table()
        if not stripped:
            close_lists()
            close_blockquote()
            continue
        if stripped.startswith("> "):
            close_lists()
            if not in_blockquote:
                html.append("<blockquote>")
                in_blockquote = True
            html.append(f"<p>{inline_md(stripped[2:])}</p>")
            continue
        close_blockquote()
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
    close_blockquote()
    return "\n".join(html)


def table_cell_attr(text: str) -> str:
    normalized = text.strip().lower()
    class_names: list[str] = []
    if normalized in {"high", "medium", "low", "высокий", "средний", "низкий"}:
        class_names.append(f"risk-{normalized}")
    if normalized in {"high", "medium", "low", "высокая", "средняя", "низкая"}:
        class_names.append(f"confidence-{normalized}")
    return f' class="{" ".join(class_names)}"' if class_names else ""


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
