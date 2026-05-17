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


VERSION = "2.3.0"

READY_MIN_COMPETITORS = 3

RUNTIME_FILES = [
    "run_state.json",
    "intake.json",
    "topics.json",
    "agent_tasks.json",
    "agent_results.jsonl",
    "orchestration_contract.json",
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

COMPETITOR_SYNTHESIS_FIELDS = [
    "positioning",
    "pricing",
    "primary_cta",
    "onboarding_pattern",
    "proof",
    "first_value_path",
    "observed_weaknesses",
]

CHANNEL_ORDER = ["search", "meta", "linkedin", "telegram", "webinar", "email"]

CHANNEL_ALIASES = {
    "search": ["search", "google", "seo", "sem", "keyword", "comparison"],
    "meta": ["meta", "facebook", "instagram", "fb", "ig", "paid social"],
    "linkedin": ["linkedin", "linked in", "social selling"],
    "telegram": ["telegram", "tg", "telegram bot", "bot", "mini app"],
    "webinar": ["webinar", "workshop", "masterclass", "live class"],
    "email": ["email", "newsletter", "nurture", "lifecycle", "crm follow-up", "crm follow up", "follow-up", "reactivation"],
}

NICHE_PROFILE_ORDER = ["saas", "real_estate", "education", "marketplace", "local_services"]

NICHE_PROFILE_ALIASES = {
    "saas": [
        "saas",
        "software",
        "trial",
        "mrr",
        "arr",
        "stripe",
        "crm",
        "dashboard",
        "subscription",
        "activation",
        "product-led",
        "revops",
    ],
    "real_estate": [
        "real estate",
        "property",
        "properties",
        "developer",
        "apartment",
        "apartments",
        "relocation",
        "buyer",
        "buyers",
        "investor",
        "mortgage",
        "rental",
        "недвиж",
        "квартир",
        "покупател",
        "релокац",
    ],
    "education": [
        "education",
        "course",
        "program",
        "cohort",
        "student",
        "students",
        "school",
        "lesson",
        "lessons",
        "mentorship",
        "masterclass",
        "graduates",
        "обуч",
        "курс",
        "школ",
        "студент",
        "выпускник",
    ],
    "marketplace": [
        "marketplace",
        "two-sided",
        "two sided",
        "provider",
        "providers",
        "supply",
        "demand",
        "match",
        "matching",
        "shortlist",
        "verified providers",
        "маркетплейс",
        "поставщик",
        "исполнител",
        "подбор",
    ],
    "local_services": [
        "local service",
        "local business",
        "clinic",
        "dental",
        "dentist",
        "salon",
        "appointment",
        "booking",
        "whatsapp",
        "near me",
        "city",
        "home service",
        "клиник",
        "стоматолог",
        "запис",
        "услуг",
        "локальн",
    ],
}

RISKY_PROMISE_TERMS = [
    "guarantee",
    "guaranteed",
    "roi",
    "return",
    "income",
    "profit",
    "revenue",
    "legal",
    "tax",
    "investment",
    "payment",
    "compliance",
    "гарант",
    "доход",
    "прибыль",
    "выруч",
    "окупаем",
    "доходност",
    "инвест",
    "юрид",
    "налог",
    "платеж",
]

PERFORMANCE_PROMISE_TERMS = [
    "%",
    "x",
    "increase",
    "reduce",
    "recover",
    "save",
    "minutes",
    "faster",
    "рост",
    "сниз",
    "увелич",
    "сэконом",
    "минут",
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

RECOMMENDATION_CONTRACT_FIELDS = [
    "id",
    "type",
    "target_segment",
    "funnel_stage",
    "claim_ids",
    "source_ids",
    "assumption_ids",
    "confidence",
    "blocked_reason",
    "owner_action",
    "measurement_event",
]

EVIDENCE_CLAIM_CONTRACT_FIELDS = [
    "claim_id",
    "claim_text",
    "claim_type",
    "source_ids",
    "freshness_required",
    "freshness_status",
    "relevance_score",
    "confidence",
    "used_in",
]

EXPERIMENT_QUALITY_FIELDS = [
    "event_id",
    "guardrail_metrics",
    "exposure_definition",
    "event_instrumentation",
    "srm_check",
    "event_loss_threshold",
    "expected_effect_range",
    "stop_rule",
    "ship_rule",
    "iterate_rule",
    "failure_mode",
]

VARIANT_BUNDLE_CONTRACT_FIELDS = [
    "variant_id",
    "stage",
    "funnel_stage",
    "target_segment",
    "variant_type",
    "control_reference",
    "current_step",
    "hypothesis",
    "proof_requirement",
    "measurement_event",
    "guardrail",
    "claim_ids",
    "source_ids",
    "assumption_ids",
    "blocked_reason",
]

VARIANT_BUNDLE_TYPES = {"copy", "cta", "route", "proof_placement", "qualification"}

REVIEWER_APPROVAL_CONTRACT_FIELDS = [
    "status",
    "required",
    "approved",
    "approved_by",
    "approved_at",
    "approval_source",
    "blocked_reason",
    "review_items",
]

REVIEWER_APPROVAL_STATUSES = {"not_required", "required", "approved"}

REVIEW_ITEM_CONTRACT_FIELDS = [
    "review_id",
    "review_type",
    "target_id",
    "target_type",
    "risk_level",
    "reason",
    "claim_ids",
    "source_ids",
    "assumption_ids",
    "blocked_reason",
]

ORCHESTRATION_TASK_CONTRACT_FIELDS = [
    "task_id",
    "role",
    "specialist",
    "objective",
    "input_refs",
    "context_refs",
    "output_refs",
    "artifact_refs",
    "claim_ids",
    "source_ids",
    "assumption_ids",
    "blocked_reason",
    "status",
    "created_at",
    "updated_at",
]

ORCHESTRATION_TASK_STATUSES = {
    "pending",
    "in_progress",
    "completed",
    "blocked",
    "research_only",
    "ready",
    "draft",
}

CURRENT_FUNNEL_CHANGE_TYPES = {"keep", "replace", "add", "remove", "instrument", "clarify"}

CURRENT_SENSITIVE_SOURCE_TYPES = {"pricing", "changelog", "current_practice", "competitor"}
STALE_FRESHNESS_VALUES = {"stale", "outdated", "expired", "old"}
EVIDENCE_READY_THRESHOLD = 60


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


def exports_dir(workspace: Path) -> Path:
    return workspace / "exports"


def runtime_path(workspace: Path, filename: str) -> Path:
    return runtime_dir(workspace) / filename


def export_path(workspace: Path, filename: str) -> Path:
    return exports_dir(workspace) / filename


def ensure_exports_dir(workspace: Path) -> Path:
    directory = exports_dir(workspace)
    reject_symlink(directory)
    directory.mkdir(parents=True, exist_ok=True)
    reject_symlink(directory)
    return directory


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
        "current_funnel": [],
        "pricing": "",
        "time_to_first_value_minutes": "",
        "sales_motion": "",
        "product_constraints": "",
        "unit_economics": "",
        "implementation_bandwidth": "",
        "experiment_bandwidth": "",
        "reviewer_approval": "",
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


def default_task_objectives() -> dict[str, str]:
    return {
        "intake": "Normalize user context, missing fields, proof assets, metrics, and constraints.",
        "planner": "Keep topic/task scope bounded and route unresolved work to the right specialist.",
        "research": "Gather source-backed current-practice evidence and identify evidence gaps.",
        "competitor": "Gather sourced competitor observations for pricing, CTA, onboarding, proof, and first value.",
        "synthesis": "Compile decision-grade insights with claim/source/assumption coverage.",
        "compiler_reviewer": "Render the user-facing final pack and verify that raw machine-readable files stay outside final/.",
    }


def default_tasks() -> list[dict[str, str]]:
    roles = ["intake", "planner", "research", "competitor", "synthesis", "compiler_reviewer"]
    objectives = default_task_objectives()
    now = utc_now()
    return [
        {
            "task_id": f"{role}-1",
            "role": role,
            "topic_id": role if role != "compiler_reviewer" else "final_pack",
            "status": "pending",
            "objective": objectives.get(role, f"Complete {role} work."),
            "summary": "",
            "created_at": now,
            "updated_at": now,
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
        "reviewer_approval": {},
        "assumptions": [],
        "confidence": "low",
        "updated_at": utc_now(),
    }


def default_orchestration_contract(language: str = "English") -> dict[str, Any]:
    now = utc_now()
    return {
        "contract_type": "orchestration_task_results",
        "version": VERSION,
        "output_language": language,
        "generated_at": now,
        "phase": "intake",
        "status": "draft",
        "tasks": [],
        "validation_errors": [],
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
    orchestration_path = runtime_path(workspace, "orchestration_contract.json")
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
    if not orchestration_path.exists():
        write_json(orchestration_path, default_orchestration_contract(language))
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
        "orchestration_contract": read_json(runtime_path(workspace, "orchestration_contract.json"), default_orchestration_contract(language)),
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
    for source in sources:
        label = source.get("url") or source.get("title") or "source"
        for field in ["url", "title", "publisher", "source_type", "freshness", "confidence"]:
            if not present(source.get(field)):
                gaps.append(f"у источника не заполнено поле {field}: {label}" if ru else f"source missing {field}: {label}")
        if not present(source.get("used_in")):
            gaps.append(f"не указано, где используется источник: {label}" if ru else f"source missing used_in: {label}")
        source_type = str(source.get("source_type", "")).strip().lower()
        if source_type in CURRENT_SENSITIVE_SOURCE_TYPES and not present(source.get("retrieved_at")):
            gaps.append(f"у источника типа {source_type} нет даты проверки: {label}" if ru else f"{source_type} source missing retrieved_at: {label}")
        if source_type in CURRENT_SENSITIVE_SOURCE_TYPES and str(source.get("freshness", "")).strip().lower() in STALE_FRESHNESS_VALUES:
            gaps.append(f"у источника типа {source_type} устаревший статус свежести: {label}" if ru else f"{source_type} source has stale freshness status: {label}")
        if str(source.get("evidence_weight", "")).strip().lower() == "low":
            gaps.append(f"слабый источник нельзя использовать как доказательство: {label}" if ru else f"low-weight source cannot support recommendations: {label}")
    for row in competitors:
        label = row.get("competitor") or row.get("domain") or "competitor"
        if not present(row.get("source")):
            gaps.append(f"у строки конкурента нет источника: {label}" if ru else f"competitor row missing source: {label}")
        if present(row.get("source")) and not present(row.get("retrieved_at")):
            gaps.append(f"у строки конкурента нет даты проверки: {label}" if ru else f"competitor source missing retrieved_at: {label}")
        observed_fields = ["positioning", "pricing", "primary_cta", "onboarding_pattern", "proof", "first_value_path"]
        if not any(present(row.get(field)) for field in observed_fields):
            gaps.append(f"у строки конкурента нет наблюдений по офферу, цене, призыву или первым шагам: {label}" if ru else f"competitor row missing observed positioning/pricing/CTA/onboarding/proof: {label}")
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


def normalized_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def confidence_value(value: Any) -> float:
    normalized = str(value or "").strip().lower()
    if normalized in {"high", "высокая", "высокий"}:
        return 1.0
    if normalized in {"medium", "med", "средняя", "средний"}:
        return 0.75
    if normalized in {"low", "низкая", "низкий"}:
        return 0.25
    return 0.4


def source_quality_value(source: dict[str, Any]) -> float:
    weight = str(source.get("evidence_weight") or "").strip().lower()
    if weight == "high":
        base = 1.0
    elif weight == "medium":
        base = 0.75
    elif weight == "low":
        base = 0.1
    else:
        base = 0.55

    source_type = str(source.get("source_type") or "").strip().lower()
    publisher_type = str(source.get("publisher_type") or "").strip().lower()
    url = str(source.get("url") or "").strip().lower()
    publisher = str(source.get("publisher") or source_domain(url) or "").strip().lower()
    if source_type in {"pricing", "docs", "changelog", "competitor", "case_study"}:
        base += 0.1
    if publisher_type in {"primary_or_official", "official", "primary"}:
        base += 0.15
    elif publisher and url and publisher in url and source_type in CURRENT_SENSITIVE_SOURCE_TYPES:
        base += 0.1
    return min(1.0, base)


def source_signature(source: dict[str, Any]) -> str:
    url = str(source.get("url") or "").strip().lower()
    if url:
        return url
    domain = str(source.get("publisher") or source_domain(url) or "").strip().lower()
    title = re.sub(r"\s+", " ", str(source.get("title") or "").strip().lower())
    return domain or title


def is_stale_source(source: dict[str, Any]) -> bool:
    source_type = str(source.get("source_type") or "").strip().lower()
    freshness = str(source.get("freshness") or "").strip().lower()
    if freshness in STALE_FRESHNESS_VALUES:
        return True
    return source_type in CURRENT_SENSITIVE_SOURCE_TYPES and not present(source.get("retrieved_at"))


def source_label(source: dict[str, Any]) -> str:
    return str(source.get("url") or source.get("title") or source.get("source_id") or "source")


def claim_relevance_value(claim: dict[str, Any]) -> float:
    raw = claim.get("relevance_score")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = 0.0
    if value > 1:
        value = value / 100
    used_in = list_value(claim.get("used_in"))
    if used_in:
        value = max(value, 0.35)
    return max(0.0, min(1.0, value))


def recommendation_rows(insights: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(insights, dict):
        return []
    rows: list[dict[str, Any]] = []
    for section in ["screens", "experiments"]:
        section_rows = insights.get(section)
        if isinstance(section_rows, list):
            rows.extend(row for row in section_rows if isinstance(row, dict))
    return rows


def claim_coverage_value(row: dict[str, Any], claim_by_id: dict[str, dict[str, Any]]) -> float:
    row_claim_ids = list_value(row.get("claim_ids"))
    row_source_ids = set(list_value(row.get("source_ids")))
    row_assumption_ids = set(list_value(row.get("assumption_ids")))
    if not row_claim_ids:
        return 0.0

    covered = 0.0
    for claim_id in row_claim_ids:
        claim = claim_by_id.get(claim_id)
        if not claim:
            continue
        claim_source_ids = set(list_value(claim.get("source_ids")))
        claim_status = str(claim.get("freshness_status") or "").strip().lower()
        if claim_source_ids:
            if row_source_ids & claim_source_ids:
                covered += 1.0
            continue
        if claim_status == "assumption" and row_assumption_ids:
            covered += 0.45
    return covered / len(row_claim_ids)


def semantic_evidence_quality(
    data: dict[str, Any],
    insights: dict[str, Any] | None = None,
    contract_errors: list[str] | None = None,
    conflicts: list[str] | None = None,
) -> dict[str, Any]:
    ru = is_russian(data)
    sources = data.get("sources") if isinstance(data.get("sources"), list) else []
    errors = contract_errors if isinstance(contract_errors, list) else []
    conflict_rows = conflicts if isinstance(conflicts, list) else []
    blockers: list[str] = []

    if not sources:
        blockers.append("semantic evidence: no usable sources" if not ru else "качество данных: нет пригодных источников")

    quality_values = [source_quality_value(source) for source in sources]
    low_weight_sources = [source for source in sources if str(source.get("evidence_weight") or "").strip().lower() == "low"]
    if low_weight_sources:
        blockers.append("semantic evidence: low-weight sources cannot carry ready state" if not ru else "качество данных: слабые источники не могут переводить пакет в ready")
    source_quality_score = normalized_score((sum(quality_values) / len(quality_values)) * 100) if quality_values else 0

    freshness_values: list[float] = []
    stale_sources: list[dict[str, Any]] = []
    for source in sources:
        if is_stale_source(source):
            freshness_values.append(0.0)
            stale_sources.append(source)
        elif present(source.get("retrieved_at")) or str(source.get("freshness") or "").strip().lower() == "current":
            freshness_values.append(1.0)
        else:
            freshness_values.append(0.45)
    if stale_sources:
        labels = ", ".join(source_label(source) for source in stale_sources[:3])
        blockers.append((f"semantic evidence: stale current-sensitive sources: {labels}") if not ru else f"качество данных: устаревшие current-sensitive источники: {labels}")
    freshness_score = normalized_score((sum(freshness_values) / len(freshness_values)) * 100) if freshness_values else 0

    unique_signatures = {source_signature(source) for source in sources if source_signature(source)}
    unique_domains = {str(source.get("publisher") or source_domain(str(source.get("url") or ""))).strip().lower() for source in sources if present(source.get("publisher") or source.get("url"))}
    unique_count = max(len(unique_domains), len(unique_signatures))
    independence_score = normalized_score(min(1.0, unique_count / 3) * 100) if sources else 0
    if sources and unique_count < min(3, len(sources)):
        blockers.append("semantic evidence: duplicate or same-publisher sources do not provide independent support" if not ru else "качество данных: дубли или один издатель не дают независимой опоры")

    confidence_values = [confidence_value(source.get("confidence")) for source in sources]
    confidence_score = normalized_score((sum(confidence_values) / len(confidence_values)) * 100) if confidence_values else 0

    claims = insights.get("evidence_claims") if isinstance(insights, dict) and isinstance(insights.get("evidence_claims"), list) else []
    source_claims = [claim for claim in claims if isinstance(claim, dict) and list_value(claim.get("source_ids"))]
    relevance_values = [claim_relevance_value(claim) for claim in source_claims]
    relevance_score = normalized_score((sum(relevance_values) / len(relevance_values)) * 100) if relevance_values else 0
    if insights is not None and not source_claims:
        blockers.append("semantic evidence: no source-backed claims" if not ru else "качество данных: нет утверждений с источниками")
    elif relevance_values and max(relevance_values) < 0.6:
        blockers.append("semantic evidence: source-backed claims are weakly relevant" if not ru else "качество данных: утверждения слабо связаны с рекомендациями")

    claim_by_id = {
        str(claim.get("claim_id")): claim
        for claim in claims
        if isinstance(claim, dict) and present(claim.get("claim_id"))
    }
    recommendations = recommendation_rows(insights)
    coverage_values = [claim_coverage_value(row, claim_by_id) for row in recommendations]
    claim_coverage_score = normalized_score((sum(coverage_values) / len(coverage_values)) * 100) if coverage_values else 0
    if insights is not None and not recommendations:
        blockers.append("semantic evidence: no structured recommendations to cover" if not ru else "качество данных: нет структурированных рекомендаций для покрытия")
    if coverage_values and max(coverage_values) < 0.7:
        blockers.append("semantic evidence: recommendations rely on assumptions or uncovered claims" if not ru else "качество данных: рекомендации опираются на допущения или непокрытые утверждения")
    elif coverage_values and any(value < 0.7 for value in coverage_values):
        blockers.append("semantic evidence: at least one recommendation has weak claim coverage" if not ru else "качество данных: минимум одна рекомендация слабо покрыта утверждениями")

    proof_blockers = promise_proof_blockers(insights, ru)
    if proof_blockers:
        blockers.extend(proof_blockers)

    conflict_score = 100
    if errors or conflict_rows:
        conflict_score = 0
        if errors:
            blockers.append("semantic evidence: contract errors block ready state" if not ru else "качество данных: contract errors блокируют ready")
        if conflict_rows:
            blockers.append("semantic evidence: unresolved contradictions block ready state" if not ru else "качество данных: нерешенные противоречия блокируют ready")

    dimensions = {
        "source_quality": {
            "score": source_quality_score,
            "reason": f"{len(sources)} sources; {len(low_weight_sources)} low-weight" if not ru else f"источников: {len(sources)}; слабых: {len(low_weight_sources)}",
        },
        "freshness": {
            "score": freshness_score,
            "reason": "current-sensitive sources need current freshness and retrieved_at" if not ru else "current-sensitive источникам нужны current freshness и retrieved_at",
        },
        "relevance": {
            "score": relevance_score,
            "reason": f"{len(source_claims)} source-backed claims scored" if not ru else f"утверждений с источниками оценено: {len(source_claims)}",
        },
        "independence": {
            "score": independence_score,
            "reason": f"{unique_count} independent source signatures/domains" if not ru else f"независимых сигнатур/доменов: {unique_count}",
        },
        "confidence": {
            "score": confidence_score,
            "reason": "average source confidence" if not ru else "средняя уверенность источников",
        },
        "claim_coverage": {
            "score": claim_coverage_score,
            "reason": f"{len(recommendations)} recommendations checked" if not ru else f"рекомендаций проверено: {len(recommendations)}",
        },
        "conflict_handling": {
            "score": conflict_score,
            "reason": "contract errors or contradictions reduce readiness to draft" if (errors or conflict_rows) and not ru else ("contract errors или противоречия переводят готовность в draft" if errors or conflict_rows else "no unresolved contract errors or contradictions"),
        },
    }
    weighted_score = (
        dimensions["source_quality"]["score"] * 0.20
        + dimensions["freshness"]["score"] * 0.15
        + dimensions["relevance"]["score"] * 0.15
        + dimensions["independence"]["score"] * 0.10
        + dimensions["confidence"]["score"] * 0.10
        + dimensions["claim_coverage"]["score"] * 0.25
        + dimensions["conflict_handling"]["score"] * 0.05
    )
    score = normalized_score(weighted_score)
    if errors or conflict_rows:
        score = min(score, EVIDENCE_READY_THRESHOLD - 1)
    if proof_blockers:
        score = min(score, EVIDENCE_READY_THRESHOLD - 1)
    if score < EVIDENCE_READY_THRESHOLD:
        blockers.append((f"semantic evidence: readiness score {score}/{EVIDENCE_READY_THRESHOLD} is below ready threshold") if not ru else f"качество данных: score {score}/{EVIDENCE_READY_THRESHOLD} ниже порога ready")

    return {
        "score": score,
        "ready_threshold": EVIDENCE_READY_THRESHOLD,
        "dimensions": dimensions,
        "blockers": dedupe(blockers),
    }


def research_readiness_score(data: dict[str, Any]) -> int:
    return int(semantic_evidence_quality(data).get("score", 0))


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
        "runtime/orchestration_contract.json": "ready",
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


def list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if present(item)]
    if present(value):
        return [str(value).strip()]
    return []


def first_ids(rows: list[dict[str, Any]], key: str, limit: int = 2) -> list[str]:
    ids: list[str] = []
    for row in rows:
        value = row.get(key)
        if present(value):
            ids.append(str(value))
        if len(ids) >= limit:
            break
    return ids


def compact_fragment(value: Any, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def url_signature(value: Any) -> str:
    return str(value or "").strip().lower().rstrip("/")


def source_id(source: dict[str, Any]) -> str:
    return str(source.get("source_id") or "").strip()


def competitor_source_ids(row: dict[str, Any], sources: list[dict[str, Any]]) -> list[str]:
    row_source = url_signature(row.get("source"))
    row_domain = str(row.get("domain") or source_domain(str(row.get("source") or ""))).strip().lower()
    exact_ids = [
        source_id(source)
        for source in sources
        if source_id(source) and row_source and url_signature(source.get("url")) == row_source
    ]
    if exact_ids:
        return dedupe(exact_ids)
    if not row_domain:
        return []
    domain_ids = []
    for source in sources:
        candidate_domain = str(source.get("publisher") or source_domain(str(source.get("url") or ""))).strip().lower()
        if source_id(source) and candidate_domain == row_domain:
            domain_ids.append(source_id(source))
    return dedupe(domain_ids)


def competitor_label(row: dict[str, Any]) -> str:
    return compact_fragment(row.get("competitor") or row.get("domain") or "competitor", 80)


def competitor_field_label(field: str, ru: bool) -> str:
    labels_ru = {
        "positioning": "позиционирование",
        "pricing": "упаковка/цены",
        "primary_cta": "призывы к действию",
        "onboarding_pattern": "онбординг",
        "proof": "механики доверия",
        "first_value_path": "путь к первой ценности",
        "observed_weaknesses": "наблюдаемые слабые места",
    }
    labels_en = {
        "positioning": "positioning",
        "pricing": "offer packaging/pricing",
        "primary_cta": "competitor CTAs",
        "onboarding_pattern": "onboarding patterns",
        "proof": "proof mechanics",
        "first_value_path": "first-value paths",
        "observed_weaknesses": "observed weaknesses",
    }
    return (labels_ru if ru else labels_en).get(field, field.replace("_", " "))


def competitor_pattern_sentence(field: str, values: list[str], ru: bool) -> str:
    joined = "; ".join(values[:4])
    if ru:
        return f"Наблюдаемый конкурентный паттерн: {competitor_field_label(field, ru)} — {joined}."
    return f"Observed competitor {competitor_field_label(field, ru)}: {joined}."


def build_competitor_synthesis(
    competitors: list[dict[str, str]],
    sources: list[dict[str, Any]],
    support_ids: list[str],
    ru: bool,
) -> dict[str, Any]:
    support_id_set = set(support_ids)
    observations: dict[str, list[dict[str, Any]]] = {}
    patterns: dict[str, dict[str, Any]] = {}

    for field in COMPETITOR_SYNTHESIS_FIELDS:
        field_observations: list[dict[str, Any]] = []
        for row in competitors:
            value = compact_fragment(row.get(field))
            if not value:
                continue
            row_source_ids = competitor_source_ids(row, sources)
            if support_id_set:
                row_source_ids = [source_id_value for source_id_value in row_source_ids if source_id_value in support_id_set]
            if not row_source_ids:
                continue
            field_observations.append(
                {
                    "competitor": competitor_label(row),
                    "domain": compact_fragment(row.get("domain"), 80),
                    "value": value,
                    "source": str(row.get("source") or "").strip(),
                    "source_ids": row_source_ids,
                }
            )
        if field_observations:
            observations[field] = field_observations
        if len(field_observations) < 2:
            continue
        values = dedupe([observation["value"] for observation in field_observations])
        source_ids = dedupe(
            [
                source_id_value
                for observation in field_observations
                for source_id_value in list_value(observation.get("source_ids"))
            ]
        )
        patterns[field] = {
            "field": field,
            "label": competitor_field_label(field, ru),
            "values": values,
            "competitors": dedupe([observation["competitor"] for observation in field_observations]),
            "source_ids": source_ids,
            "observation_count": len(field_observations),
            "pattern": competitor_pattern_sentence(field, values, ru),
        }

    pattern_texts = [pattern["pattern"] for pattern in patterns.values()]
    return {
        "status": "observed" if patterns else "insufficient_competitor_patterns",
        "competitor_count": len(competitors),
        "source_ids": dedupe(
            [
                source_id_value
                for pattern in patterns.values()
                for source_id_value in list_value(pattern.get("source_ids"))
            ]
        ),
        "patterns": patterns,
        "observations": observations,
        "summary_text": " ".join(pattern_texts[:3]),
    }


def competitor_pattern_values(competitor_synthesis: dict[str, Any] | None, field: str, limit: int = 3) -> list[str]:
    if not isinstance(competitor_synthesis, dict):
        return []
    patterns = competitor_synthesis.get("patterns")
    if not isinstance(patterns, dict):
        return []
    pattern = patterns.get(field)
    if not isinstance(pattern, dict):
        return []
    values = pattern.get("values")
    if not isinstance(values, list):
        return []
    return [compact_fragment(value) for value in values if present(value)][:limit]


def competitor_values_phrase(competitor_synthesis: dict[str, Any] | None, field: str, ru: bool, limit: int = 3) -> str:
    values = competitor_pattern_values(competitor_synthesis, field, limit)
    if not values:
        return ""
    separator = "; " if ru else "; "
    return separator.join(f"`{value}`" for value in values)


def competitor_pattern_phrase(competitor_synthesis: dict[str, Any] | None, field: str, ru: bool, limit: int = 3) -> str:
    values = competitor_values_phrase(competitor_synthesis, field, ru, limit)
    if not values:
        return ""
    return f"{competitor_field_label(field, ru)} ({values})"


def competitor_synthesis_has_patterns(competitor_synthesis: dict[str, Any] | None) -> bool:
    return bool(isinstance(competitor_synthesis, dict) and isinstance(competitor_synthesis.get("patterns"), dict) and competitor_synthesis["patterns"])


def channel_pack_templates(ru: bool) -> dict[str, dict[str, Any]]:
    if ru:
        return {
            "search": {
                "label": "Поиск",
                "intent": "высокое намерение и сравнение вариантов",
                "journey": "поисковый запрос -> сравнение -> доказательство рядом с призывом -> быстрый первый результат",
                "entry_focus": "Связать запрос пользователя с конкретным обещанием и доказательством рядом с основным призывом.",
                "qualification_focus": "Уточнить сравниваемый сценарий, текущий инструмент и срочность без длинного брифа.",
                "first_value_route": "Дать быстрый пример первой ценности, который отвечает на поисковый запрос.",
                "conversion_focus": "Показать ожидания следующего шага, доказательство и ценовой/квалификационный ориентир рядом с призывом.",
                "cta": "Сравнить мой вариант",
                "event_ids": ["SearchIntentMatched", "ComparisonCTAStarted", "FirstValuePreviewViewed", "SearchConversionQualified"],
                "risk": "Поисковый запрос не совпадает с обещанием или рядом с призывом нет сильного доказательства.",
                "guardrail": "несовпадение намерения, некачественные старты, потери событий",
                "experiment_focus": "вариант для сравнивающего поискового трафика с доказательством рядом с призывом",
                "support_loop": "повторное касание или прогрев для тех, кто сравнивает, но не готов к следующему шагу",
            },
            "meta": {
                "label": "Meta",
                "intent": "низкое намерение: креатив сначала формирует проблему",
                "journey": "креатив -> короткая предквалификация -> передача в лендинг/бот -> отфильтрованный лид",
                "entry_focus": "Продолжить мысль креатива и дать короткую предквалификацию вместо тяжелой продающей страницы.",
                "qualification_focus": "Отсечь нецелевые клики через 2-3 вопроса о боли, срочности и соответствии офферу.",
                "first_value_route": "Показать микро-диагностику или пример результата до просьбы о созвоне.",
                "conversion_focus": "Передать в следующий шаг только отфильтрованный лид с понятными ожиданиями.",
                "cta": "Проверить fit за минуту",
                "event_ids": ["MetaCreativeClicked", "MessagePrequalified", "HandoffCompleted", "QualityLeadQualified"],
                "risk": "Большой объем холодных кликов может ухудшить качество лидов.",
                "guardrail": "качество лидов, выгорание креативов, потери при передаче",
                "experiment_focus": "переход от креатива к предквалификации и передаче лида",
                "support_loop": "повторное касание с доказательством и креативами под конкретные возражения",
            },
            "linkedin": {
                "label": "LinkedIn",
                "intent": "доверие, узкий ICP и маршрут с участием продаж",
                "journey": "контент от возражения -> экспертное доказательство -> проверка ICP -> следующий шаг с продажами",
                "entry_focus": "Открыть путь доверия через экспертное доказательство и узкий ICP вместо широкого обещания.",
                "qualification_focus": "Спросить роль, контекст и главное возражение, чтобы выбрать маршрут с поддержкой продаж.",
                "first_value_route": "Дать экспертный разбор или сравнительный ориентир, который выглядит применимым к роли.",
                "conversion_focus": "Перевести подходящий сегмент в следующий шаг с продажами и контекстом для разговора.",
                "cta": "Получить экспертный разбор",
                "event_ids": ["LinkedInTrustClicked", "ICPFitCaptured", "ExpertProofViewed", "SalesAssistedRouted"],
                "risk": "Слишком широкий ICP снижает доверие и качество передачи в продажи.",
                "guardrail": "несовпадение ICP, скепсис к доказательствам, качество передачи в продажи",
                "experiment_focus": "экспертное доказательство от главного возражения для узкого ICP",
                "support_loop": "догревающий контент по возражениям и роли",
            },
            "telegram": {
                "label": "Telegram",
                "intent": "ветвление бота, оценка намерения и напоминания",
                "journey": "вход в бот -> ветка намерения -> напоминание -> передача в CRM",
                "entry_focus": "Начать с ветки Telegram-бота и сразу выбрать путь по намерению и срочности.",
                "qualification_focus": "Считать оценку намерения по ответам и показывать разные ветки для горячих и холодных лидов.",
                "first_value_route": "Дать короткий результат в боте до передачи в CRM или созвон.",
                "conversion_focus": "Передать квалифицированный путь в CRM и включить напоминание для незавершивших.",
                "cta": "Запустить разбор в боте",
                "event_ids": ["TelegramBotStarted", "TelegramIntentScored", "TelegramReminderQueued", "CRMHandoffCreated"],
                "risk": "Пользователи могут бросить ветку бота, а CRM может потерять источник лида.",
                "guardrail": "отвал в боте, усталость от напоминаний, потеря передачи в CRM",
                "experiment_focus": "ветка бота с оценкой намерения и напоминанием",
                "support_loop": "напоминания и последующий контакт в CRM для незавершивших",
            },
            "webinar": {
                "label": "Вебинар",
                "intent": "регистрация, доходимость, живое доказательство и разбор возражений",
                "journey": "регистрация -> посещение -> живое доказательство/вопросы -> развилка после вебинара",
                "entry_focus": "Позиционировать регистрацию вокруг конкретного результата и причины прийти в прямой эфир.",
                "qualification_focus": "Собрать вопросы и данные по возражениям до вебинара.",
                "first_value_route": "Дать живое доказательство, разбор примера и ответы на возражения во время события.",
                "conversion_focus": "После вебинара разделить ветки для участников, неявок и тех, кто смотрит запись.",
                "cta": "Забронировать место",
                "event_ids": ["WebinarRegistered", "WebinarAttended", "LiveProofEngaged", "PostWebinarDecisionRouted"],
                "risk": "Регистрации могут не перейти в посещение, а возражения могут остаться без ответа.",
                "guardrail": "доходимость, неявки, задержка обработки после вебинара",
                "experiment_focus": "путь от регистрации к посещению с живым доказательством и ответами на возражения",
                "support_loop": "развилка после вебинара для участников, неявок и тех, кто смотрит запись",
            },
            "email": {
                "label": "Email",
                "intent": "сегментация, жизненный цикл и прогрев по возражениям",
                "journey": "сегмент -> триггер жизненного цикла -> прогрев по возражению -> удержание/реактивация",
                "entry_focus": "Начать с сегментации и триггера жизненного цикла, а не с одинакового письма всем.",
                "qualification_focus": "Разделить намерение по кликам, ответам и стадии жизненного цикла.",
                "first_value_route": "Дать прогрев под конкретное возражение с маленьким полезным шагом.",
                "conversion_focus": "Вести к удержанию или реактивации с понятным следующим шагом.",
                "cta": "Получить следующий шаг",
                "event_ids": ["EmailSegmentMatched", "LifecycleTriggerFired", "ObjectionNurtureClicked", "ReactivationActionTaken"],
                "risk": "Одинаковый прогрев для разных сегментов ухудшит удержание и реактивацию.",
                "guardrail": "отписки, доставляемость, устаревшие сегменты",
                "experiment_focus": "сегментированный триггер жизненного цикла с прогревом под возражение",
                "support_loop": "цепочка удержания и реактивации",
            },
        }
    return {
        "search": {
            "label": "Search",
            "intent": "high-intent comparison traffic",
            "journey": "search query -> comparison -> proof near CTA -> fast first value",
            "entry_focus": "Match keyword-to-promise intent to the offer and put proof near the primary CTA.",
            "qualification_focus": "Ask about the comparison context, current tool, and urgency without a long brief.",
            "first_value_route": "Deliver a fast first-value preview that answers the search intent.",
            "conversion_focus": "Show next-step expectations, proof, and a price or qualification anchor near the CTA.",
            "cta": "Compare my fit",
            "event_ids": ["SearchIntentMatched", "ComparisonCTAStarted", "FirstValuePreviewViewed", "SearchConversionQualified"],
            "risk": "Keyword-to-promise mismatch or thin proof near the CTA.",
            "guardrail": "query intent mismatch, low-quality starts, event loss",
            "experiment_focus": "comparison/high-intent variant with proof near the CTA",
            "support_loop": "retargeting or nurture for comparison visitors who are not ready for the next step",
        },
        "meta": {
            "label": "Meta",
            "intent": "low-intent traffic shaped by the creative angle",
            "journey": "creative angle -> message prequalification -> landing/bot handoff -> quality-filtered lead",
            "entry_focus": "Continue the creative angle and use message prequalification instead of a heavy sales page.",
            "qualification_focus": "Filter low-intent clicks with 2-3 questions about pain, urgency, and fit.",
            "first_value_route": "Show a micro-diagnosis or result preview before asking for a call.",
            "conversion_focus": "Pass only a quality-filtered lead into the next step with clear expectations.",
            "cta": "Check my fit",
            "event_ids": ["MetaCreativeClicked", "MessagePrequalified", "HandoffCompleted", "QualityLeadQualified"],
            "risk": "High low-intent volume can drag down lead quality.",
            "guardrail": "lead quality, creative fatigue, handoff drop-off",
            "experiment_focus": "creative-angle to prequalification handoff",
            "support_loop": "retargeting with proof and objection-specific creative",
        },
        "linkedin": {
            "label": "LinkedIn",
            "intent": "trust path, narrow ICP, and sales-assisted routing",
            "journey": "objection-led content -> expert proof -> narrow ICP fit -> sales-assisted next step",
            "entry_focus": "Open with a trust path using expert proof and narrow ICP fit instead of a broad promise.",
            "qualification_focus": "Ask for role, context, and the main objection so the assisted route is relevant.",
            "first_value_route": "Give an expert review or benchmark preview that feels role-specific.",
            "conversion_focus": "Route fit-qualified users into a sales-assisted next step with context attached.",
            "cta": "Get expert review",
            "event_ids": ["LinkedInTrustClicked", "ICPFitCaptured", "ExpertProofViewed", "SalesAssistedRouted"],
            "risk": "A broad ICP weakens trust and sales-assisted routing quality.",
            "guardrail": "ICP mismatch, proof skepticism, sales handoff quality",
            "experiment_focus": "objection-led expert proof for a narrow ICP",
            "support_loop": "role-specific follow-up content by objection",
        },
        "telegram": {
            "label": "Telegram",
            "intent": "bot branching, intent scoring, and reminders",
            "journey": "bot entry -> intent branch -> reminder loop -> CRM handoff",
            "entry_focus": "Start with a Telegram bot branch that immediately chooses the intent and urgency path.",
            "qualification_focus": "Use intent scoring from answers and split hot and cold leads into different branches.",
            "first_value_route": "Show a short bot-result preview before CRM handoff or a call.",
            "conversion_focus": "Create the CRM handoff for qualified paths and queue reminders for unfinished flows.",
            "cta": "Start bot diagnosis",
            "event_ids": ["TelegramBotStarted", "TelegramIntentScored", "TelegramReminderQueued", "CRMHandoffCreated"],
            "risk": "Bot-branch drop-off and lost CRM attribution.",
            "guardrail": "bot drop-off, reminder fatigue, CRM handoff loss",
            "experiment_focus": "intent-scored bot branch with a reminder loop",
            "support_loop": "reminder loop and CRM follow-up for unfinished bot sessions",
        },
        "webinar": {
            "label": "Webinar",
            "intent": "registration, attendance, live proof, and Q&A objections",
            "journey": "registration -> attendance -> live proof/Q&A -> post-webinar decision tree",
            "entry_focus": "Position registration around a concrete result and a reason to attend live.",
            "qualification_focus": "Capture questions and objection data before the webinar.",
            "first_value_route": "Deliver live proof, a worked example, and Q&A objection handling during the event.",
            "conversion_focus": "Split attended, no-show, and replay paths after the webinar.",
            "cta": "Reserve my seat",
            "event_ids": ["WebinarRegistered", "WebinarAttended", "LiveProofEngaged", "PostWebinarDecisionRouted"],
            "risk": "Registrations without attendance and unanswered Q&A objections.",
            "guardrail": "attendance rate, no-show rate, post-webinar delay",
            "experiment_focus": "registration-to-attendance path with live proof and Q&A objections",
            "support_loop": "post-webinar decision tree for attendees, no-shows, and replay viewers",
        },
        "email": {
            "label": "Email",
            "intent": "segmentation, lifecycle triggers, and objection-specific nurture",
            "journey": "segment -> lifecycle trigger -> objection nurture -> retention/reactivation action",
            "entry_focus": "Start from segmentation and lifecycle trigger instead of sending the same email to everyone.",
            "qualification_focus": "Infer intent from clicks, replies, and lifecycle stage.",
            "first_value_route": "Use objection-specific nurture with one small useful step.",
            "conversion_focus": "Move users toward retention or reactivation with a clear next action.",
            "cta": "Get next step",
            "event_ids": ["EmailSegmentMatched", "LifecycleTriggerFired", "ObjectionNurtureClicked", "ReactivationActionTaken"],
            "risk": "One-size-fits-all nurture can hurt retention and reactivation.",
            "guardrail": "unsubscribe rate, deliverability, stale segment data",
            "experiment_focus": "segmented lifecycle trigger with objection-specific nurture",
            "support_loop": "retention and reactivation sequence",
        },
    }


def alias_matches(text: str, alias: str) -> list[int]:
    if not text or not alias:
        return []
    pattern = r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])"
    return [match.start() for match in re.finditer(pattern, text)]


def matched_channel_keys(raw_channel: Any) -> list[str]:
    text = str(raw_channel or "").strip().lower()
    if not text:
        return []
    matches: list[tuple[int, int, str]] = []
    for order, channel_key in enumerate(CHANNEL_ORDER):
        positions: list[int] = []
        for alias in CHANNEL_ALIASES[channel_key]:
            positions.extend(alias_matches(text, alias))
        if positions:
            matches.append((min(positions), order, channel_key))
    return [channel_key for _, _, channel_key in sorted(matches)]


def profile_detection_text(intake: dict[str, Any]) -> str:
    fields = [
        "project_name",
        "offer",
        "icp",
        "primary_persona",
        "jtbd",
        "target_kpi",
        "primary_channel",
        "pricing",
        "sales_motion",
        "product_constraints",
        "unit_economics",
    ]
    return " ".join(str(intake.get(field) or "") for field in fields).lower()


def matched_niche_profile_key(intake: dict[str, Any]) -> tuple[str, list[str]]:
    text = profile_detection_text(intake)
    if not text.strip():
        return "", []
    scored: list[tuple[int, int, str, list[str]]] = []
    for order, profile_key in enumerate(NICHE_PROFILE_ORDER):
        terms: list[str] = []
        score = 0
        for alias in NICHE_PROFILE_ALIASES[profile_key]:
            positions = alias_matches(text, alias)
            if not positions:
                continue
            terms.append(alias)
            score += max(1, len(positions))
            if alias in {"saas", "real estate", "marketplace", "local service", "local business"}:
                score += 2
        if score:
            scored.append((score, -order, profile_key, terms))
    if not scored:
        return "", []
    score, _, profile_key, terms = sorted(scored, reverse=True)[0]
    if score <= 0:
        return "", []
    return profile_key, dedupe(terms)


def niche_profile_templates(ru: bool) -> dict[str, dict[str, Any]]:
    if ru:
        return {
            "saas": {
                "label": "SaaS",
                "sales_motion": "self_serve_or_sales_assisted",
                "vocabulary": ["активация", "trial", "time to first value", "workspace", "интеграция", "account"],
                "risks": ["длинная настройка до первой ценности", "слабая связь trial с нужным аккаунтом", "потери событий между продуктом и CRM"],
                "proof_patterns": ["короткий product walkthrough", "source-backed case study", "интеграционный screenshot с анонимизированными данными"],
                "funnel_defaults": ["показать первый полезный результат до upgrade", "свести onboarding к одному подключению или demo dataset", "держать product event как главный decision event"],
                "event_suggestions": ["WorkspaceCreated", "IntegrationConnected", "FirstValueReached", "TrialQualified"],
                "summary_text": "Использовать SaaS-словарь: активация, trial, интеграция, workspace и первый полезный результат.",
            },
            "real_estate": {
                "label": "Real Estate",
                "sales_motion": "assisted_consultation",
                "vocabulary": ["покупатель", "объект", "шортлист", "бюджет", "юридическая готовность", "консультация"],
                "risks": ["нельзя обещать доходность или юридический результат без источника и review", "низкое качество лидов из-за бюджета", "недоверие к процессу покупки"],
                "proof_patterns": ["проверяемый property shortlist sample", "credentials или лицензии", "case narrative без обещания доходности"],
                "funnel_defaults": ["сначала квалифицировать бюджет и страну", "показать safe shortlist preview", "вести к консультации с подготовленным контекстом"],
                "event_suggestions": ["BuyerFitCaptured", "BudgetRangeSubmitted", "ShortlistPreviewViewed", "AdvisorConsultationBooked"],
                "summary_text": "Использовать путь доверия и квалификации покупателя без инвестиционных, юридических или return claims.",
            },
            "education": {
                "label": "Education",
                "sales_motion": "webinar_or_cohort",
                "vocabulary": ["урок", "программа", "когорта", "результат обучения", "домашнее задание", "стратегический звонок"],
                "risks": ["income claims без proof", "регистрации не переходят в attendance", "неясный результат обучения до оплаты"],
                "proof_patterns": ["lesson preview", "student work sample", "source-backed graduate story без гарантий дохода"],
                "funnel_defaults": ["дать учебный результат до продажи", "собирать возражения до вебинара", "разделить attendance/no-show/replay ветки"],
                "event_suggestions": ["LessonPreviewViewed", "WebinarQuestionSubmitted", "WebinarAttended", "StrategyCallQualified"],
                "summary_text": "Использовать education-путь: учебный preview, возражения, attendance и следующий шаг после вебинара.",
            },
            "marketplace": {
                "label": "Marketplace",
                "sales_motion": "matchmaking",
                "vocabulary": ["спрос", "предложение", "матчинг", "поставщик", "заявка", "shortlist"],
                "risks": ["несбалансированный supply/demand", "качество поставщиков", "потеря доверия к проверке и срокам матчинга"],
                "proof_patterns": ["verified supply criteria", "sample shortlist", "partner endorsement или quality review"],
                "funnel_defaults": ["квалифицировать demand-side заявку", "показать проверку поставщиков", "измерять matched consultation как decision event"],
                "event_suggestions": ["RequestQualified", "ProviderCriteriaViewed", "ShortlistDelivered", "MatchedConsultationBooked"],
                "summary_text": "Использовать marketplace-путь: квалификация спроса, доверие к supply и прозрачный матчинг.",
            },
            "local_services": {
                "label": "Local Services",
                "sales_motion": "appointment_led",
                "vocabulary": ["запись", "район", "специалист", "слоты", "консультация", "WhatsApp follow-up"],
                "risks": ["ограниченные слоты", "compliance для медицинских/юридических услуг", "некачественные заявки и no-show"],
                "proof_patterns": ["credentials", "review summary without guarantees", "before/after only when allowed and sourced"],
                "funnel_defaults": ["сначала подтвердить fit и доступные слоты", "показать доверие рядом с записью", "закрепить follow-up SLA"],
                "event_suggestions": ["ServiceFitCaptured", "SlotPreferenceSubmitted", "AppointmentBooked", "FollowUpSlaMet"],
                "summary_text": "Использовать local-services путь: доверие, доступность слотов, запись и быстрый follow-up.",
            },
        }
    return {
        "saas": {
            "label": "SaaS",
            "sales_motion": "self_serve_or_sales_assisted",
            "vocabulary": ["activation", "trial", "time to first value", "workspace", "integration", "account"],
            "risks": ["setup takes too long before first value", "trial intent does not map to the right account", "product and CRM events drift apart"],
            "proof_patterns": ["short product walkthrough", "source-backed case study", "anonymized integration screenshot"],
            "funnel_defaults": ["show first value before upgrade", "reduce onboarding to one connection or demo dataset", "make the product event the decision event"],
            "event_suggestions": ["WorkspaceCreated", "IntegrationConnected", "FirstValueReached", "TrialQualified"],
            "summary_text": "Use SaaS vocabulary: activation, trial, integration, workspace, and first value.",
        },
        "real_estate": {
            "label": "Real Estate",
            "sales_motion": "assisted_consultation",
            "vocabulary": ["buyer", "property", "shortlist", "budget", "legal readiness", "consultation"],
            "risks": ["return, legal, or payment claims need source-backed proof and review", "lead quality depends on budget fit", "buyers may distrust the purchase process"],
            "proof_patterns": ["verifiable property shortlist sample", "credentials or licenses", "case narrative without return promises"],
            "funnel_defaults": ["qualify budget and country first", "show a safe shortlist preview", "route to a consultation with context attached"],
            "event_suggestions": ["BuyerFitCaptured", "BudgetRangeSubmitted", "ShortlistPreviewViewed", "AdvisorConsultationBooked"],
            "summary_text": "Use a buyer trust and qualification path without investment, legal, or return claims.",
        },
        "education": {
            "label": "Education",
            "sales_motion": "webinar_or_cohort",
            "vocabulary": ["lesson", "program", "cohort", "learning outcome", "assignment", "strategy call"],
            "risks": ["income claims need proof", "registrations may not become attendance", "the learning outcome may stay unclear before purchase"],
            "proof_patterns": ["lesson preview", "student work sample", "source-backed graduate story without income guarantees"],
            "funnel_defaults": ["deliver a learning result before selling", "capture objections before the webinar", "split attended, no-show, and replay branches"],
            "event_suggestions": ["LessonPreviewViewed", "WebinarQuestionSubmitted", "WebinarAttended", "StrategyCallQualified"],
            "summary_text": "Use an education path: lesson preview, objection capture, attendance, and post-webinar next step.",
        },
        "marketplace": {
            "label": "Marketplace",
            "sales_motion": "matchmaking",
            "vocabulary": ["demand", "supply", "matching", "provider", "request", "shortlist"],
            "risks": ["supply/demand imbalance", "provider quality uncertainty", "trust can break if verification or matching timing is unclear"],
            "proof_patterns": ["verified supply criteria", "sample shortlist", "partner endorsement or quality review"],
            "funnel_defaults": ["qualify the demand-side request", "show provider verification", "measure matched consultation as the decision event"],
            "event_suggestions": ["RequestQualified", "ProviderCriteriaViewed", "ShortlistDelivered", "MatchedConsultationBooked"],
            "summary_text": "Use a marketplace path: demand qualification, supply trust, and transparent matching.",
        },
        "local_services": {
            "label": "Local Services",
            "sales_motion": "appointment_led",
            "vocabulary": ["appointment", "local area", "specialist", "slots", "consultation", "WhatsApp follow-up"],
            "risks": ["limited appointment slots", "medical/legal services may need compliance review", "low-quality requests and no-shows"],
            "proof_patterns": ["credentials", "review summary without guarantees", "before/after only when allowed and sourced"],
            "funnel_defaults": ["confirm fit and available slots first", "place trust proof near booking", "lock follow-up SLA"],
            "event_suggestions": ["ServiceFitCaptured", "SlotPreferenceSubmitted", "AppointmentBooked", "FollowUpSlaMet"],
            "summary_text": "Use a local-services path: trust, slot availability, appointment, and fast follow-up.",
        },
    }


def build_niche_profile(intake: dict[str, Any], ru: bool) -> dict[str, Any]:
    profile_key, matched_terms = matched_niche_profile_key(intake)
    if not profile_key:
        return {
            "status": "unmatched",
            "profile_key": "",
            "label": "Общий профиль" if ru else "General",
            "matched_terms": [],
            "vocabulary": [],
            "risks": [],
            "proof_patterns": [],
            "funnel_defaults": [],
            "event_suggestions": [],
            "sales_motion": "",
            "summary_text": "Нишевый профиль не выбран; используется общий путь." if ru else "No niche profile matched; using the generic path.",
        }
    template = dict(niche_profile_templates(ru)[profile_key])
    template.update(
        {
            "status": "matched",
            "profile_key": profile_key,
            "matched_terms": matched_terms,
        }
    )
    return template


def niche_profile_event(profile: dict[str, Any] | None, index: int, fallback: str = "") -> str:
    if not isinstance(profile, dict):
        return fallback
    events = list_value(profile.get("event_suggestions"))
    if index < len(events):
        return events[index]
    return fallback


def niche_profile_has_match(profile: dict[str, Any] | None) -> bool:
    return bool(isinstance(profile, dict) and profile.get("status") == "matched" and profile.get("profile_key"))


def build_channel_synthesis(intake: dict[str, Any], ru: bool) -> dict[str, Any]:
    raw_channel = str(intake.get("primary_channel") or "").strip()
    templates = channel_pack_templates(ru)
    channel_keys = matched_channel_keys(raw_channel)
    if not channel_keys:
        return {
            "status": "unmatched_channel",
            "raw_channel": raw_channel,
            "primary_channel_pack": "",
            "support_loops": [],
            "packs": [],
            "summary_text": "No channel pack matched; use the generic draft path." if not ru else "Канал не распознан; используется общий черновой путь.",
        }
    packs = []
    for channel_key in channel_keys:
        pack = dict(templates[channel_key])
        pack["channel"] = channel_key
        packs.append(pack)
    primary = packs[0]
    support_loops = [
        {
            "channel": pack["channel"],
            "label": pack["label"],
            "support_loop": pack["support_loop"],
            "event_ids": pack["event_ids"],
            "journey": pack["journey"],
            "risk": pack["risk"],
            "guardrail": pack["guardrail"],
        }
        for pack in packs[1:]
    ]
    return {
        "status": "matched",
        "raw_channel": raw_channel,
        "primary_channel_pack": primary["channel"],
        "primary_label": primary["label"],
        "intent": primary["intent"],
        "journey": primary["journey"],
        "event_ids": primary["event_ids"],
        "risk": primary["risk"],
        "support_loops": support_loops,
        "packs": packs,
        "summary_text": (
            f"Primary channel pack: {primary['label']}; journey: {primary['journey']}."
            if not ru
            else f"Основной канальный маршрут: {primary['label']}; путь: {primary['journey']}."
        ),
    }


def primary_channel_pack(channel_synthesis: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(channel_synthesis, dict):
        return None
    packs = channel_synthesis.get("packs")
    if isinstance(packs, list) and packs and isinstance(packs[0], dict):
        return packs[0]
    return None


def source_claim_group(source: dict[str, Any]) -> str:
    source_type = str(source.get("source_type") or "").strip().lower()
    text = " ".join(
        str(source.get(field) or "")
        for field in ["title", "url", "publisher", "notes", "research_query"]
    ).lower()
    if source_type == "pricing":
        return "pricing"
    if source_type == "competitor":
        return "competitor"
    if source_type in {"case_study", "review"} or any(token in text for token in ["case", "testimonial", "proof", "customer story"]):
        return "proof"
    if source_type in {"current_practice", "docs", "changelog"}:
        return "current_practice"
    return "market_evidence"


def select_support_source_ids(
    sources: list[dict[str, Any]],
    evidence_refs: list[dict[str, Any]],
    competitors: list[dict[str, str]],
    limit: int = 3,
) -> list[str]:
    selected: list[str] = []

    def add(source_id_value: str) -> None:
        if source_id_value and source_id_value not in selected and len(selected) < limit:
            selected.append(source_id_value)

    for source in sources:
        if source_claim_group(source) == "proof":
            add(source_id(source))
        if len(selected) >= limit:
            return selected

    for competitor in competitors:
        for source_id_value in competitor_source_ids(competitor, sources):
            add(source_id_value)
        if len(selected) >= limit:
            return selected

    for claim_group in ["pricing", "competitor", "current_practice", "market_evidence"]:
        for source in sources:
            if source_claim_group(source) == claim_group:
                add(source_id(source))
            if len(selected) >= limit:
                return selected

    for ref in evidence_refs:
        add(str(ref.get("id") or ref.get("source_id") or ""))
        if len(selected) >= limit:
            return selected
    return selected


def source_ids_for_claim(sources: list[dict[str, Any]], support_id_set: set[str], claim_type: str) -> list[str]:
    ids = [
        source_id(source)
        for source in sources
        if source_id(source) in support_id_set and source_claim_group(source) == claim_type
    ]
    return dedupe(ids)


def claim_confidence(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "low"
    values = [confidence_value(source.get("confidence")) for source in sources]
    if min(values) <= 0.25:
        return "low"
    if sum(values) / len(values) >= 0.9:
        return "high"
    return "medium"


def claim_freshness_status(sources: list[dict[str, Any]]) -> str:
    if any(is_stale_source(source) for source in sources):
        return "stale"
    if sources and all(str(source.get("freshness") or "").strip().lower() == "current" or present(source.get("retrieved_at")) for source in sources):
        return "current"
    return "unknown"


def claim_usage(claim_type: str) -> list[str]:
    usage = {
        "pricing": ["screen-1", "screen-4", "experiment-1"],
        "competitor": ["screen-1", "screen-2", "screen-3", "screen-4", "experiment-1"],
        "current_practice": ["screen-2", "screen-3", "experiment-1"],
        "proof": ["screen-1", "screen-3", "screen-4", "experiment-1"],
        "market_evidence": ["screen-1", "screen-2", "screen-3", "screen-4", "experiment-1"],
        "assumption": ["screens", "experiments", "decision_summary"],
    }
    return usage.get(claim_type, usage["market_evidence"])


def claim_text_for(claim_type: str, source_count: int, ru: bool) -> str:
    if ru:
        values = {
            "pricing": f"Свежие pricing/offer источники ({source_count}) должны влиять на упаковку оффера, призыв к действию и ожидания перед конверсией.",
            "competitor": f"Наблюдаемые конкурентные источники ({source_count}) дают паттерны для первого экрана, квалификации и следующего эксперимента.",
            "current_practice": f"Текущие практики и документация ({source_count}) поддерживают шаги уточнения, первой ценности и измерения.",
            "proof": f"Proof/review источники ({source_count}) можно использовать только там, где нужен элемент доверия или пример результата.",
            "market_evidence": f"Исследовательские источники ({source_count}) дают общую опору для черновика пути воронки.",
        }
    else:
        values = {
            "pricing": f"Current pricing and offer sources ({source_count}) should shape offer packaging, CTA expectations, and conversion steps.",
            "competitor": f"Observed competitor sources ({source_count}) provide patterns for entry screens, qualification, and the next experiment.",
            "current_practice": f"Current practice and documentation sources ({source_count}) support qualification, first-value, and measurement recommendations.",
            "proof": f"Proof and review sources ({source_count}) can support trust elements or result examples where proof is needed.",
            "market_evidence": f"Research sources ({source_count}) provide general support for the draft funnel path.",
        }
    return values.get(claim_type, values["market_evidence"])


def source_backed_claim(
    claim_id: str,
    claim_type: str,
    claim_sources: list[dict[str, Any]],
    source_ids: list[str],
    ru: bool,
) -> dict[str, Any]:
    freshness_required = any(
        str(source.get("source_type") or "").strip().lower() in CURRENT_SENSITIVE_SOURCE_TYPES
        for source in claim_sources
    )
    relevance = {
        "pricing": 0.9,
        "competitor": 0.85,
        "current_practice": 0.8,
        "proof": 0.85,
        "market_evidence": 0.65,
    }.get(claim_type, 0.65)
    return {
        "claim_id": claim_id,
        "claim_text": claim_text_for(claim_type, len(source_ids), ru),
        "claim_type": claim_type,
        "source_ids": source_ids,
        "freshness_required": freshness_required,
        "freshness_status": claim_freshness_status(claim_sources),
        "relevance_score": relevance,
        "confidence": claim_confidence(claim_sources),
        "used_in": claim_usage(claim_type),
    }


def build_evidence_claims(
    sources: list[dict[str, Any]],
    assumptions: list[dict[str, Any]],
    support_ids: list[str],
    ru: bool,
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    support_id_set = set(support_ids)
    source_by_id = {source_id(source): source for source in sources if source_id(source)}
    if support_ids:
        grouped_ids: dict[str, list[str]] = {}
        for claim_type in ["pricing", "competitor", "current_practice", "proof", "market_evidence"]:
            ids = source_ids_for_claim(sources, support_id_set, claim_type)
            if ids:
                grouped_ids[claim_type] = ids
        if "competitor" not in grouped_ids and len(grouped_ids.get("pricing", [])) >= 2:
            grouped_ids["competitor"] = grouped_ids["pricing"]
        if not grouped_ids:
            grouped_ids["market_evidence"] = support_ids

        for claim_type in ["pricing", "competitor", "current_practice", "proof", "market_evidence"]:
            ids = grouped_ids.get(claim_type, [])
            if not ids:
                continue
            claim_sources = [source_by_id[source_id_value] for source_id_value in ids if source_id_value in source_by_id]
            claims.append(source_backed_claim(f"claim-{len(claims) + 1}", claim_type, claim_sources, ids, ru))
    else:
        claims.append(
            {
                "claim_id": "claim-1",
                "claim_text": "Recommendation is draft-only until external evidence is recorded." if not ru else "Рекомендация остается черновиком, пока не записаны внешние источники.",
                "claim_type": "assumption",
                "source_ids": [],
                "freshness_required": False,
                "freshness_status": "assumption",
                "relevance_score": 0.2,
                "confidence": "low",
                "used_in": claim_usage("assumption"),
            }
        )
    if assumptions:
        assumption_ids = first_ids(assumptions, "id", 3)
        claims.append(
            {
                "claim_id": f"claim-{len(claims) + 1}",
                "claim_text": "Open assumptions must stay visible before launch." if not ru else "Открытые допущения должны оставаться видимыми до запуска.",
                "claim_type": "assumption",
                "source_ids": [],
                "freshness_required": False,
                "freshness_status": "assumption",
                "relevance_score": 0.4,
                "confidence": "low" if not support_ids else "medium",
                "used_in": dedupe(assumption_ids + claim_usage("assumption")),
            }
        )
    return claims


def contains_term(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def promise_risk_level(promise: str) -> str:
    if contains_term(promise, RISKY_PROMISE_TERMS):
        return "high"
    if contains_term(promise, PERFORMANCE_PROMISE_TERMS) or re.search(r"\d+\s*(%|x|times|minutes|min|мин)", promise, re.IGNORECASE):
        return "medium"
    return "low"


def proof_source_candidates(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [source for source in sources if source_claim_group(source) == "proof"]


def proof_source_ready(source: dict[str, Any]) -> bool:
    if not source_id(source):
        return False
    if is_stale_source(source):
        return False
    if str(source.get("evidence_weight") or "").strip().lower() == "low":
        return False
    if str(source.get("confidence") or "").strip().lower() == "low":
        return False
    return source_quality_value(source) >= 0.55


def proof_requirement_for(risk_level: str, ru: bool) -> str:
    if risk_level == "high":
        return (
            "нужен источник с доказательством результата и отдельная проверка рискованного коммерческого/юридического обещания"
            if ru
            else "needs source-backed result proof plus review for the risky commercial or legal claim"
        )
    if risk_level == "medium":
        return (
            "нужен кейс, отзыв или метрика, привязанная к обещанному результату"
            if ru
            else "needs a case, review, or metric tied to the promised result"
        )
    return (
        "нужно конкретное доказательство или явное допущение до появления доказательства"
        if ru
        else "needs a concrete proof asset or an explicit assumption until proof exists"
    )


def objection_for_promise(status: str, risk_level: str, ru: bool) -> str:
    if risk_level == "high":
        return (
            "Почему можно доверять рискованному обещанию без подтвержденного доказательства?"
            if ru
            else "Why should the buyer trust a risky claim without verified proof?"
        )
    if status in {"no_proof", "weak_proof"}:
        return "Почему этому результату можно верить?" if ru else "Why should I believe this result?"
    return (
        "Похоже ли это доказательство на мою ситуацию?"
        if ru
        else "Does this proof match my situation?"
    )


def proof_fallback_for(status: str, ru: bool) -> str:
    values_ru = {
        "source_backed": "Можно использовать доказательство рядом с призывом, сохранив ссылку на источник.",
        "asset_backed": "Использовать как черновое доказательство, но перед масштабированием записать источник или артефакт.",
        "weak_proof": "Оставить обещание как допущение, смягчить формулировку и собрать более сильный источник.",
        "no_proof": "Не выносить обещание результата в основной призыв; сначала собрать доказательство или явно показать его отсутствие.",
        "risky_unverified": "Не использовать рискованное обещание в призыве к действию; заменить на нейтральный шаг до подтверждения и проверки.",
    }
    values_en = {
        "source_backed": "Use the proof near the CTA while preserving the source link.",
        "asset_backed": "Use it as draft proof, but record a source or artifact before scaling.",
        "weak_proof": "Keep the promise as an assumption, soften the wording, and collect stronger proof.",
        "no_proof": "Do not put the result promise into the primary CTA; collect proof first or show the no-proof state.",
        "risky_unverified": "Do not use the risky promise in the CTA; replace it with a neutral step until proof and review exist.",
    }
    return (values_ru if ru else values_en).get(status, values_ru["weak_proof"] if ru else values_en["weak_proof"])


def promise_claim_type(promise: str, risk_level: str) -> str:
    lowered = promise.lower()
    if risk_level == "high":
        return "regulated_or_financial_claim"
    if contains_term(lowered, PERFORMANCE_PROMISE_TERMS) or re.search(r"\d+\s*(%|x|times|minutes|min|мин)", promise, re.IGNORECASE):
        return "performance_outcome"
    if any(token in lowered for token in ["trust", "verified", "safe", "credential", "license", "довер", "провер", "лиценз"]):
        return "trust_or_safety"
    return "fit_or_workflow"


def proof_sales_motion(
    intake: dict[str, Any],
    channel_synthesis: dict[str, Any] | None,
    niche_profile: dict[str, Any] | None,
) -> str:
    explicit = str(intake.get("sales_motion") or "").strip().lower()
    if explicit:
        if any(token in explicit for token in ["self", "plg", "product", "trial"]):
            return "self_serve"
        if any(token in explicit for token in ["webinar", "cohort", "education"]):
            return "webinar_led"
        if any(token in explicit for token in ["marketplace", "match"]):
            return "matchmaking"
        if any(token in explicit for token in ["appointment", "consult", "sales", "demo", "assisted"]):
            return "assisted_consultation"

    channel = ""
    if isinstance(channel_synthesis, dict):
        channel = str(channel_synthesis.get("primary_channel_pack") or "").strip()
    profile_key = str(niche_profile.get("profile_key") or "") if isinstance(niche_profile, dict) else ""
    if profile_key == "marketplace":
        return "matchmaking"
    if profile_key == "education" or channel == "webinar":
        return "webinar_led"
    if channel in {"telegram", "meta"}:
        return "bot_or_messaging"
    if profile_key == "saas" and channel == "search":
        return "self_serve"
    if profile_key in {"real_estate", "local_services"}:
        return "assisted_consultation"
    if channel == "linkedin":
        return "assisted_consultation"
    return "self_serve" if profile_key == "saas" else "assisted_consultation"


def proof_mechanic_guidance(claim_type: str, sales_motion: str, risk_level: str, ru: bool) -> dict[str, Any]:
    if ru:
        claim_formats = {
            "performance_outcome": "кейс или метрика результата с источником, датой и контекстом сегмента",
            "trust_or_safety": "credentials, review summary или критерии проверки с источником",
            "regulated_or_financial_claim": "подтвержденный источник плюс ручной review; не использовать как обещание результата без проверки",
            "fit_or_workflow": "пример workflow, demo walkthrough или sample output, который показывает применимость",
        }
        motion_formats = {
            "self_serve": "показать доказательство рядом с first-value preview или trial step",
            "assisted_consultation": "использовать proof в pre-call контексте и передать его владельцу консультации",
            "webinar_led": "поставить proof в live example/Q&A и post-webinar decision route",
            "bot_or_messaging": "дать короткий proof snippet в ветке qualification до handoff",
            "matchmaking": "показать критерии проверки supply и sample shortlist до заявки",
        }
        fallback = "если формата нет, смягчить обещание и оставить explicit assumption до появления источника"
        note = "guidance only: это рекомендация по формату доказательства, не источник"
    else:
        claim_formats = {
            "performance_outcome": "case or outcome metric with source, retrieval date, and segment context",
            "trust_or_safety": "credentials, review summary, or verification criteria with a source",
            "regulated_or_financial_claim": "source-backed proof plus manual review; do not use as a result promise without approval",
            "fit_or_workflow": "workflow example, demo walkthrough, or sample output that shows fit",
        }
        motion_formats = {
            "self_serve": "place proof next to the first-value preview or trial step",
            "assisted_consultation": "use proof in the pre-call context and pass it to the consultation owner",
            "webinar_led": "put proof inside the live example/Q&A and post-webinar decision route",
            "bot_or_messaging": "show a short proof snippet in the qualification branch before handoff",
            "matchmaking": "show supply verification criteria and a sample shortlist before the request",
        }
        fallback = "if the format is missing, soften the promise and keep an explicit assumption until a source exists"
        note = "guidance only: this recommends a proof format, not evidence"

    recommended_format = claim_formats.get(claim_type, claim_formats["fit_or_workflow"])
    placement = motion_formats.get(sales_motion, motion_formats["assisted_consultation"])
    if risk_level == "high":
        recommended_format = (
            f"{recommended_format}; {'отдельно зафиксировать legal/commercial review' if ru else 'record separate legal/commercial review'}"
        )
    return {
        "mechanic_id": f"{claim_type}:{sales_motion}:{risk_level}",
        "claim_type": claim_type,
        "sales_motion": sales_motion,
        "risk_level": risk_level,
        "recommended_format": recommended_format,
        "placement": placement,
        "fallback": fallback,
        "guidance_only": True,
        "note": note,
    }


def proof_blocked_reason_for(status: str, ru: bool) -> str:
    values_ru = {
        "weak_proof": "доказательство слабое или не готово для запуска",
        "no_proof": "обещание результата не подтверждено proof",
        "risky_unverified": "рискованное обещание требует подтвержденного источника и review",
    }
    values_en = {
        "weak_proof": "proof is weak or not launch-ready",
        "no_proof": "result promise has no proof yet",
        "risky_unverified": "risky promise needs source-backed proof and review",
    }
    return (values_ru if ru else values_en).get(status, "")


def proof_assumption_ids(assumptions: list[dict[str, Any]]) -> list[str]:
    ids = []
    for row in assumptions:
        used_in = str(row.get("used_in") or "")
        statement = str(row.get("statement") or "").lower()
        if used_in in {"screen_playbook", "promise_proof"} or "proof" in statement or "доказ" in statement:
            ids.append(str(row.get("id") or ""))
    return [value for value in dedupe(ids) if value]


def proof_claim_ids(evidence_claims: list[dict[str, Any]], source_ids: list[str], status: str) -> list[str]:
    result = []
    source_id_set = set(source_ids)
    for claim in evidence_claims:
        claim_type = str(claim.get("claim_type") or "")
        claim_sources = set(list_value(claim.get("source_ids")))
        if claim_type == "proof" and (not source_id_set or claim_sources & source_id_set):
            result.append(str(claim.get("claim_id") or ""))
    if result:
        return [value for value in dedupe(result) if value]
    if status != "source_backed":
        for claim in evidence_claims:
            if str(claim.get("freshness_status") or "").strip().lower() == "assumption":
                result.append(str(claim.get("claim_id") or ""))
    return [value for value in dedupe(result) if value]


def build_promise_proof_model(
    intake: dict[str, Any],
    sources: list[dict[str, Any]],
    evidence_claims: list[dict[str, Any]],
    assumptions: list[dict[str, Any]],
    ru: bool,
    niche_profile: dict[str, Any] | None = None,
    channel_synthesis: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    promise = dash_text(intake.get("offer"), ru)
    proof_assets = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
    proof_sources = proof_source_candidates(sources)
    ready_sources = [source for source in proof_sources if proof_source_ready(source)]
    weak_sources = [source for source in proof_sources if not proof_source_ready(source)]
    risk_level = promise_risk_level(" ".join([promise, str(intake.get("target_kpi") or "")]))
    claim_type = promise_claim_type(" ".join([promise, str(intake.get("target_kpi") or "")]), risk_level)
    sales_motion = proof_sales_motion(intake, channel_synthesis, niche_profile)
    proof_mechanic = proof_mechanic_guidance(claim_type, sales_motion, risk_level, ru)
    explicit_no_proof = truthy(intake.get("explicit_no_proof_yet"))

    ready_source_ids = [source_id(source) for source in ready_sources if source_id(source)]
    all_proof_source_ids = [source_id(source) for source in proof_sources if source_id(source)]
    if explicit_no_proof or (not proof_assets and not proof_sources):
        status = "no_proof"
    elif risk_level == "high" and not ready_source_ids:
        status = "risky_unverified"
    elif ready_source_ids:
        status = "source_backed"
    elif weak_sources:
        status = "weak_proof"
    else:
        status = "asset_backed"

    source_ids = ready_source_ids if ready_source_ids else all_proof_source_ids
    assumption_ids = proof_assumption_ids(assumptions) if status in {"no_proof", "weak_proof", "risky_unverified"} else []
    blocked_reason = proof_blocked_reason_for(status, ru)
    proof_requirement = proof_requirement_for(risk_level, ru)
    fallback = proof_fallback_for(status, ru)
    proof_requirement = append_sentence(
        proof_requirement,
        (
            f"Рекомендованный формат proof: {proof_mechanic['recommended_format']}; {proof_mechanic['placement']}."
            if ru
            else f"Recommended proof format: {proof_mechanic['recommended_format']}; {proof_mechanic['placement']}."
        ),
    )
    fallback = append_sentence(fallback, str(proof_mechanic.get("fallback") or ""))
    return [
        {
            "promise_id": "promise-1",
            "promise": promise,
            "objection": objection_for_promise(status, risk_level, ru),
            "proof_requirement": proof_requirement,
            "evidence_status": status,
            "risk_level": risk_level,
            "claim_type": claim_type,
            "claim_ids": proof_claim_ids(evidence_claims, source_ids, status),
            "source_ids": source_ids,
            "assumption_ids": assumption_ids,
            "fallback": fallback,
            "blocked_reason": blocked_reason,
            "recommended_proof_mechanic": proof_mechanic,
        }
    ]


def promise_proof_blocks_ready(status: str) -> bool:
    return status in {"no_proof", "weak_proof", "risky_unverified"}


def promise_proof_blockers(insights: dict[str, Any] | None, ru: bool) -> list[str]:
    if not isinstance(insights, dict):
        return []
    model = insights.get("promise_proof_model")
    if not isinstance(model, list):
        return []
    blockers: list[str] = []
    for row in model:
        if not isinstance(row, dict):
            continue
        status = str(row.get("evidence_status") or "")
        if not promise_proof_blocks_ready(status):
            continue
        promise_id = str(row.get("promise_id") or "promise")
        reason = str(row.get("blocked_reason") or status)
        blockers.append(
            f"качество данных: обещание {promise_id} не готово к запуску: {reason}"
            if ru
            else f"semantic evidence: promise {promise_id} is not launch-ready: {reason}"
        )
    return blockers


def append_blocked_reason(existing: Any, addition: str) -> str:
    existing_text = str(existing or "").strip()
    addition_text = str(addition or "").strip()
    if not addition_text:
        return existing_text
    if not existing_text:
        return addition_text
    if addition_text in existing_text:
        return existing_text
    return f"{existing_text}; {addition_text}"


def apply_promise_proof_to_recommendations(
    rows: list[dict[str, Any]],
    promise_proof_model: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blockers = [
        row
        for row in promise_proof_model
        if isinstance(row, dict) and promise_proof_blocks_ready(str(row.get("evidence_status") or ""))
    ]
    if not blockers:
        return rows
    assumption_ids = dedupe(
        [
            assumption_id
            for row in blockers
            for assumption_id in list_value(row.get("assumption_ids"))
        ]
    )
    blocked_reason = "; ".join(
        str(row.get("blocked_reason") or "").strip()
        for row in blockers
        if str(row.get("blocked_reason") or "").strip()
    )
    for row in rows:
        row["assumption_ids"] = dedupe(list_value(row.get("assumption_ids")) + assumption_ids)
        row["blocked_reason"] = append_blocked_reason(row.get("blocked_reason"), blocked_reason)
    return rows


def event_id_from_text(value: Any, fallback: str = "ExperimentDecisionEvent") -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", " ", str(value or "")).strip()
    if not text:
        return fallback
    parts = [part for part in text.split() if part]
    if not parts:
        return fallback
    event_id = "".join(part[:1].upper() + part[1:] for part in parts)
    return event_id if event_id.endswith(("Clicked", "Viewed", "Started", "Completed", "Qualified", "Routed", "Taken", "Reached")) else f"{event_id}Recorded"


def metric_count_from_row(metric: Any) -> float | None:
    if isinstance(metric, dict):
        return numeric_value(metric.get("value")) or numeric_value(metric.get("notes")) or numeric_value(metric.get("metric_name"))
    return numeric_value(metric)


def low_traffic_context(intake: dict[str, Any]) -> bool:
    fields = [
        "primary_channel",
        "product_constraints",
        "implementation_bandwidth",
        "experiment_bandwidth",
        "unit_economics",
    ]
    text = " ".join(str(intake.get(field) or "") for field in fields).lower()
    low_terms = ["low traffic", "small sample", "few leads", "limited traffic", "малый трафик", "мало трафика", "мало лидов"]
    if any(term in text for term in low_terms):
        return True
    metrics = intake.get("metrics") if isinstance(intake.get("metrics"), list) else []
    traffic_terms = ["traffic", "visit", "session", "lead", "signup", "trial", "registration", "call", "show", "трафик", "визит", "сесс", "лид", "заяв", "регистрац", "созвон"]
    for metric in metrics:
        metric_text = json.dumps(metric, ensure_ascii=False).lower() if isinstance(metric, dict) else str(metric).lower()
        if not any(term in metric_text for term in traffic_terms):
            continue
        count = metric_count_from_row(metric)
        if count is not None and count < 100:
            return True
    return False


def experiment_quality_defaults(
    row: dict[str, Any],
    intake: dict[str, Any],
    ru: bool,
) -> dict[str, Any]:
    channel = dash_text(intake.get("primary_channel"), ru)
    target_segment = dash_text(row.get("target_segment") or intake.get("icp") or intake.get("primary_persona"), ru)
    primary_metric = dash_text(row.get("primary_metric") or intake.get("target_kpi"), ru)
    event_id = str(row.get("event_id") or row.get("measurement_event") or "").strip()
    if not event_id:
        event_id = event_id_from_text(primary_metric)
    guardrail = dash_text(row.get("guardrail"), ru)
    low_traffic = low_traffic_context(intake)
    if ru:
        if low_traffic:
            return {
                "event_id": event_id,
                "measurement_event": event_id,
                "guardrail_metrics": guardrail,
                "exposure_definition": f"Только подходящие пользователи из канала «{channel}», дошедшие до тестируемого шага; одну экспозицию считать по стабильному session/user id.",
                "event_instrumentation": f"Записывать `{event_id}` с experiment_id, variant_id, channel, source, session/user id, timestamp и сегментом.",
                "srm_check": "Трафика мало для надежного SRM; вручную проверить баланс экспозиций и отсутствие перекоса по каналу/сегменту.",
                "event_loss_threshold": "Разобрать трекинг, если потеря события между frontend/backend/CRM выше 5% или не сходится ручная проверка.",
                "expected_effect_range": "Не заявлять статистический lift; искать повторяемый качественный сигнал в 5-10 целевых сессиях или последовательный тренд.",
                "stop_rule": "Остановить, если качественная обратная связь противоречит гипотезе, событие теряется или контрольный риск ухудшается.",
                "ship_rule": "Расширять только как guarded rollout, если повторяется нужный сигнал и контрольные риски стабильны.",
                "iterate_rule": "Итерировать формулировку/маршрут, если сигнал есть, но событие или следующий шаг ломается.",
                "failure_mode": "Главный риск: принять единичные наблюдения за статистический эффект.",
            }
        return {
            "event_id": event_id,
            "measurement_event": event_id,
            "guardrail_metrics": guardrail,
            "exposure_definition": f"Подходящий трафик из канала «{channel}», который дошел до тестируемого шага; первая экспозиция фиксируется по стабильному session/user id.",
            "event_instrumentation": f"Записывать `{event_id}` с experiment_id, variant_id, channel, source, session/user id, timestamp и сегментом.",
            "srm_check": "Ежедневно проверять split: расследовать отклонение распределения вариантов больше 10% от плана.",
            "event_loss_threshold": "Не интерпретировать тест, если потеря decision event между frontend/backend/CRM выше 5%.",
            "expected_effect_range": "Ожидать +5-15% relative movement по главной метрике; меньший эффект считать шумом без достаточного объема.",
            "stop_rule": "Остановить, если SRM не проходит, потеря событий выше порога или контрольный риск заметно ухудшается.",
            "ship_rule": "Оставить, если главная метрика растет в ожидаемом диапазоне, SRM чистый, потеря событий <=5%, а контрольные метрики стабильны.",
            "iterate_rule": "Итерировать, если метрика плоская, но качественная обратная связь подтверждает гипотезу или показывает узкое место.",
            "failure_mode": f"Ложный вывод из-за атрибуции, потери событий или ухудшения контрольной метрики для сегмента «{target_segment}».",
        }
    if low_traffic:
        return {
            "event_id": event_id,
            "measurement_event": event_id,
            "guardrail_metrics": guardrail,
            "exposure_definition": f"Eligible users from `{channel}` who reach the tested step; count one exposure by stable session/user id.",
            "event_instrumentation": f"Log `{event_id}` with experiment_id, variant_id, channel, source, session/user id, timestamp, and segment.",
            "srm_check": "Traffic is too low for reliable SRM; manually check exposure balance and channel/segment skew.",
            "event_loss_threshold": "Audit tracking if frontend/backend/CRM event loss exceeds 5% or manual reconciliation fails.",
            "expected_effect_range": "Do not claim statistical lift; look for repeated qualitative signal across 5-10 qualified sessions or a sequential trend.",
            "stop_rule": "Stop if qualitative feedback contradicts the hypothesis, event logging breaks, or guardrails worsen.",
            "ship_rule": "Ship only as a guarded rollout when the signal repeats and guardrails stay stable.",
            "iterate_rule": "Iterate the wording or route if the signal exists but the event or next step breaks.",
            "failure_mode": "Main failure mode: treating anecdotes as statistical lift.",
        }
    return {
        "event_id": event_id,
        "measurement_event": event_id,
        "guardrail_metrics": guardrail,
        "exposure_definition": f"Eligible traffic from `{channel}` that reaches the tested step; first exposure is assigned by stable session/user id.",
        "event_instrumentation": f"Log `{event_id}` with experiment_id, variant_id, channel, source, session/user id, timestamp, and segment.",
        "srm_check": "Check split daily: investigate allocation drift greater than 10% from the planned variant split.",
        "event_loss_threshold": "Do not interpret the test if decision-event loss between frontend/backend/CRM exceeds 5%.",
        "expected_effect_range": "Expect +5-15% relative movement in the primary metric; smaller changes are noise until sample is sufficient.",
        "stop_rule": "Stop if SRM fails, event loss exceeds the threshold, or a guardrail materially worsens.",
        "ship_rule": "Ship if the primary metric moves in the expected range, SRM is clean, event loss <=5%, and guardrails hold.",
        "iterate_rule": "Iterate if the metric is flat but qualitative feedback supports the hypothesis or reveals the bottleneck.",
        "failure_mode": f"False positive from attribution noise, event loss, or guardrail damage for `{target_segment}`.",
    }


def apply_experiment_quality_gates(
    experiments: list[dict[str, Any]],
    intake: dict[str, Any],
    ru: bool,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in experiments:
        enriched = dict(row)
        defaults = experiment_quality_defaults(enriched, intake, ru)
        for key, value in defaults.items():
            if key not in enriched or not present(enriched.get(key)):
                enriched[key] = value
        enriched["measurement_event"] = enriched["event_id"]
        result.append(enriched)
    return result


def claim_ready_for_recommendation(claim: dict[str, Any]) -> bool:
    if not list_value(claim.get("source_ids")):
        return False
    if str(claim.get("freshness_status") or "").strip().lower() in STALE_FRESHNESS_VALUES | {"unknown"}:
        return False
    if str(claim.get("confidence") or "").strip().lower() == "low":
        return False
    return True


def claim_matches_recommendation(claim: dict[str, Any], recommendation_id: str, recommendation_type: str) -> bool:
    usage = set(list_value(claim.get("used_in")))
    return bool(
        recommendation_id in usage
        or recommendation_type in usage
        or f"{recommendation_type}s" in usage
        or ("screens" in usage and recommendation_type == "screen")
        or ("experiments" in usage and recommendation_type == "experiment")
    )


def select_recommendation_claims(
    evidence_claims: list[dict[str, Any]],
    recommendation_id: str,
    recommendation_type: str,
    phase: str,
) -> list[dict[str, Any]]:
    source_claims = [
        claim
        for claim in evidence_claims
        if list_value(claim.get("source_ids")) and claim_matches_recommendation(claim, recommendation_id, recommendation_type)
    ]
    if phase == "ready":
        source_claims = [claim for claim in source_claims if claim_ready_for_recommendation(claim)]
    if source_claims:
        return source_claims[:2]
    assumption_claims = [
        claim
        for claim in evidence_claims
        if str(claim.get("freshness_status") or "").strip().lower() == "assumption"
        and claim_matches_recommendation(claim, recommendation_id, recommendation_type)
    ]
    return assumption_claims[:1]


def add_recommendation_contract(
    rows: list[dict[str, Any]],
    recommendation_type: str,
    target_segment: str,
    source_ids: list[str],
    assumption_ids: list[str],
    claim_ids: list[str],
    phase: str,
    ru: bool,
    evidence_claims: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    claims = evidence_claims if isinstance(evidence_claims, list) else []
    for index, row in enumerate(rows, start=1):
        stage = str(row.get("stage") or row.get("name") or recommendation_type).strip()
        metric = str(row.get("metric") or row.get("primary_metric") or "").strip()
        owner_action = str(row.get("change") or row.get("content") or row.get("cta") or "").strip()
        enriched = dict(row)
        recommendation_id = str(enriched.get("id") or f"{recommendation_type}-{index}")
        selected_claims = select_recommendation_claims(claims, recommendation_id, recommendation_type, phase) if claims else []
        selected_claim_ids = first_ids(selected_claims, "claim_id", 2)
        selected_source_ids = dedupe(
            [
                source_id_value
                for claim in selected_claims
                for source_id_value in list_value(claim.get("source_ids"))
            ]
        )
        resolved_claim_ids = list_value(enriched.get("claim_ids")) or selected_claim_ids or claim_ids
        resolved_source_ids = list_value(enriched.get("source_ids")) or selected_source_ids or ([] if selected_claims else source_ids)
        has_source_support = bool(resolved_source_ids)
        resolved_assumption_ids = list_value(enriched.get("assumption_ids")) or ([] if has_source_support else assumption_ids)
        blocked_reason = "" if phase == "ready" and has_source_support else ("нужно подтвердить источники перед запуском" if ru else "needs evidence before launch")
        enriched.update(
            {
                "id": recommendation_id,
                "type": enriched.get("type") or recommendation_type,
                "target_segment": enriched.get("target_segment") or target_segment,
                "funnel_stage": enriched.get("funnel_stage") or stage,
                "claim_ids": resolved_claim_ids,
                "source_ids": resolved_source_ids,
                "assumption_ids": resolved_assumption_ids,
                "blocked_reason": str(enriched.get("blocked_reason") or blocked_reason),
                "owner_action": enriched.get("owner_action") or owner_action,
                "measurement_event": enriched.get("measurement_event") or metric,
            }
        )
        result.append(enriched)
    return result


def validate_insights_contract(insights: dict[str, Any], sources: list[dict[str, Any]] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(insights, dict):
        return ["insights contract error: insights must be an object"]

    source_rows = sources if isinstance(sources, list) else []
    source_by_id = {str(row.get("source_id") or ""): row for row in source_rows if present(row.get("source_id"))}
    evidence_refs = insights.get("evidence_refs") if isinstance(insights.get("evidence_refs"), list) else []
    evidence_ref_ids = {str(row.get("id") or row.get("source_id") or "") for row in evidence_refs if present(row.get("id") or row.get("source_id"))}
    allowed_source_ids = set(source_by_id) | evidence_ref_ids

    assumptions = insights.get("assumptions") if isinstance(insights.get("assumptions"), list) else []
    allowed_assumption_ids = {str(row.get("id") or "") for row in assumptions if present(row.get("id"))}

    claims = insights.get("evidence_claims")
    if not isinstance(claims, list) or not claims:
        errors.append("insights contract error: evidence_claims must be a non-empty list")
        claims = []
    claim_ids = set()
    claim_by_id: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            errors.append(f"insights contract error: evidence_claims[{index}] must be an object")
            continue
        label = str(claim.get("claim_id") or f"evidence_claims[{index}]")
        for field in EVIDENCE_CLAIM_CONTRACT_FIELDS:
            if field not in claim or (field not in {"source_ids", "freshness_required"} and not present(claim.get(field))):
                errors.append(f"insights contract error: evidence claim {label} missing {field}")
        if present(claim.get("claim_id")):
            claim_id = str(claim.get("claim_id"))
            claim_ids.add(claim_id)
            claim_by_id[claim_id] = claim
        claim_source_ids = list_value(claim.get("source_ids"))
        if not claim_source_ids and str(claim.get("freshness_status") or "").lower() != "assumption":
            errors.append(f"insights contract error: evidence claim {label} has no source_ids")
        if str(claim.get("freshness_status") or "").strip().lower() in STALE_FRESHNESS_VALUES:
            errors.append(f"insights contract error: evidence claim {label} has stale freshness_status")
        if claim_source_ids and str(claim.get("confidence") or "").strip().lower() == "low":
            errors.append(f"insights contract error: evidence claim {label} has low confidence")
        for source_id in claim_source_ids:
            if allowed_source_ids and source_id not in allowed_source_ids:
                errors.append(f"insights contract error: evidence claim {label} references unknown source_id {source_id}")

    for section in ["screens", "experiments"]:
        rows = insights.get(section)
        if not isinstance(rows, list):
            errors.append(f"insights contract error: {section} must be a list")
            continue
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                errors.append(f"insights contract error: {section}[{index}] must be an object")
                continue
            label = str(row.get("id") or f"{section}[{index}]")
            for field in RECOMMENDATION_CONTRACT_FIELDS:
                if field not in row or (field not in {"source_ids", "assumption_ids", "blocked_reason"} and not present(row.get(field))):
                    errors.append(f"insights contract error: recommendation {label} missing {field}")
            if section == "experiments":
                for field in EXPERIMENT_QUALITY_FIELDS:
                    if field not in row or not present(row.get(field)):
                        errors.append(f"insights contract error: experiment {label} missing {field}")
                if not present(row.get("event_id")) or not present(row.get("measurement_event")):
                    errors.append(f"insights contract error: experiment {label} has no measurable event")
            row_claim_ids = list_value(row.get("claim_ids"))
            row_source_ids = list_value(row.get("source_ids"))
            row_assumption_ids = list_value(row.get("assumption_ids"))
            if not row_claim_ids:
                errors.append(f"insights contract error: recommendation {label} has no claim_ids")
            for claim_id in row_claim_ids:
                if claim_ids and claim_id not in claim_ids:
                    errors.append(f"insights contract error: recommendation {label} references unknown claim_id {claim_id}")
                    continue
                claim = claim_by_id.get(claim_id)
                if not claim:
                    continue
                claim_source_ids = set(list_value(claim.get("source_ids")))
                claim_status = str(claim.get("freshness_status") or "").strip().lower()
                if claim_source_ids and not (set(row_source_ids) & claim_source_ids):
                    errors.append(f"insights contract error: recommendation {label} claim_id {claim_id} is not covered by recommendation source_ids")
                if not claim_source_ids and claim_status == "assumption" and not row_assumption_ids:
                    errors.append(f"insights contract error: recommendation {label} claim_id {claim_id} is not covered by assumption_ids")
            if not row_source_ids and not row_assumption_ids:
                errors.append(f"insights contract error: recommendation {label} has no source_ids or assumption_ids")
            for source_id in row_source_ids:
                if allowed_source_ids and source_id not in allowed_source_ids:
                    errors.append(f"insights contract error: recommendation {label} references unknown source_id {source_id}")
                source = source_by_id.get(source_id, {})
                source_type = str(source.get("source_type") or "").strip().lower()
                if source_type in CURRENT_SENSITIVE_SOURCE_TYPES and not present(source.get("retrieved_at")):
                    errors.append(f"insights contract error: recommendation {label} references stale current-sensitive source_id {source_id}")
                if str(source.get("freshness") or "").strip().lower() in STALE_FRESHNESS_VALUES:
                    errors.append(f"insights contract error: recommendation {label} references stale source_id {source_id}")
                if str(source.get("evidence_weight") or "").strip().lower() == "low":
                    errors.append(f"insights contract error: recommendation {label} references low-weight source_id {source_id}")
            for assumption_id in row_assumption_ids:
                if allowed_assumption_ids and assumption_id not in allowed_assumption_ids:
                    errors.append(f"insights contract error: recommendation {label} references unknown assumption_id {assumption_id}")
            if is_generic_recommendation(row):
                errors.append(f"insights contract error: recommendation {label} is too generic or unsupported")
    promise_model = insights.get("promise_proof_model")
    if isinstance(promise_model, list):
        required_fields = [
            "promise_id",
            "promise",
            "objection",
            "proof_requirement",
            "evidence_status",
            "risk_level",
            "claim_ids",
            "source_ids",
            "assumption_ids",
            "fallback",
            "blocked_reason",
        ]
        for index, row in enumerate(promise_model, start=1):
            if not isinstance(row, dict):
                errors.append(f"insights contract error: promise_proof_model[{index}] must be an object")
                continue
            label = str(row.get("promise_id") or f"promise_proof_model[{index}]")
            for field in required_fields:
                if field not in row or (field not in {"source_ids", "assumption_ids", "blocked_reason"} and not present(row.get(field))):
                    errors.append(f"insights contract error: promise proof {label} missing {field}")
            status = str(row.get("evidence_status") or "").strip()
            if status == "source_backed" and not list_value(row.get("source_ids")):
                errors.append(f"insights contract error: promise proof {label} is source_backed without source_ids")
            if promise_proof_blocks_ready(status):
                if not list_value(row.get("assumption_ids")):
                    errors.append(f"insights contract error: promise proof {label} has no assumption fallback")
                if not present(row.get("blocked_reason")):
                    errors.append(f"insights contract error: promise proof {label} has no blocked_reason")
    current_diff = insights.get("current_funnel_diff")
    if isinstance(current_diff, dict):
        diff_rows = current_diff.get("rows")
        if not isinstance(diff_rows, list):
            errors.append("insights contract error: current_funnel_diff rows must be a list")
            diff_rows = []
        for index, row in enumerate(diff_rows, start=1):
            if not isinstance(row, dict):
                errors.append(f"insights contract error: current_funnel_diff[{index}] must be an object")
                continue
            label = str(row.get("id") or f"current_funnel_diff[{index}]")
            for field in [
                "id",
                "current_step",
                "proposed_step",
                "change_type",
                "reason",
                "measurement_event",
                "claim_ids",
                "source_ids",
                "assumption_ids",
                "blocked_reason",
            ]:
                if field not in row or (field not in {"current_step", "source_ids", "assumption_ids", "blocked_reason"} and not present(row.get(field))):
                    errors.append(f"insights contract error: current funnel diff {label} missing {field}")
            change_type = str(row.get("change_type") or "").strip()
            if change_type and change_type not in CURRENT_FUNNEL_CHANGE_TYPES:
                errors.append(f"insights contract error: current funnel diff {label} has invalid change_type {change_type}")
            row_claim_ids = list_value(row.get("claim_ids"))
            row_source_ids = list_value(row.get("source_ids"))
            row_assumption_ids = list_value(row.get("assumption_ids"))
            if not row_claim_ids:
                errors.append(f"insights contract error: current funnel diff {label} has no claim_ids")
            if not row_source_ids and not row_assumption_ids:
                errors.append(f"insights contract error: current funnel diff {label} has no source_ids or assumption_ids")
            for claim_id in row_claim_ids:
                if claim_ids and claim_id not in claim_ids:
                    errors.append(f"insights contract error: current funnel diff {label} references unknown claim_id {claim_id}")
                    continue
                claim = claim_by_id.get(claim_id)
                if not claim:
                    continue
                claim_source_ids = set(list_value(claim.get("source_ids")))
                claim_status = str(claim.get("freshness_status") or "").strip().lower()
                if claim_source_ids and row_source_ids and not (set(row_source_ids) & claim_source_ids):
                    errors.append(f"insights contract error: current funnel diff {label} claim_id {claim_id} is not covered by source_ids")
                if not claim_source_ids and claim_status == "assumption" and not row_assumption_ids:
                    errors.append(f"insights contract error: current funnel diff {label} claim_id {claim_id} is not covered by assumption_ids")
            for source_id in row_source_ids:
                if allowed_source_ids and source_id not in allowed_source_ids:
                    errors.append(f"insights contract error: current funnel diff {label} references unknown source_id {source_id}")
            for assumption_id in row_assumption_ids:
                if allowed_assumption_ids and assumption_id not in allowed_assumption_ids:
                    errors.append(f"insights contract error: current funnel diff {label} references unknown assumption_id {assumption_id}")
    variant_bundles = insights.get("variant_bundles")
    if variant_bundles is not None:
        if not isinstance(variant_bundles, list):
            errors.append("insights contract error: variant_bundles must be a list")
            variant_bundles = []
        for index, row in enumerate(variant_bundles, start=1):
            if not isinstance(row, dict):
                errors.append(f"insights contract error: variant_bundles[{index}] must be an object")
                continue
            label = str(row.get("variant_id") or f"variant_bundles[{index}]")
            for field in VARIANT_BUNDLE_CONTRACT_FIELDS:
                if field not in row or (field not in {"control_reference", "current_step", "source_ids", "assumption_ids", "blocked_reason"} and not present(row.get(field))):
                    errors.append(f"insights contract error: variant bundle {label} missing {field}")
            variant_type = str(row.get("variant_type") or "").strip()
            if variant_type and variant_type not in VARIANT_BUNDLE_TYPES:
                errors.append(f"insights contract error: variant bundle {label} has invalid variant_type {variant_type}")
            if not present(row.get("variant_copy")) and not present(row.get("variant_action")):
                errors.append(f"insights contract error: variant bundle {label} has no variant_copy or variant_action")
            row_claim_ids = list_value(row.get("claim_ids"))
            row_source_ids = list_value(row.get("source_ids"))
            row_assumption_ids = list_value(row.get("assumption_ids"))
            if not row_claim_ids:
                errors.append(f"insights contract error: variant bundle {label} has no claim_ids")
            if not row_source_ids and not row_assumption_ids:
                errors.append(f"insights contract error: variant bundle {label} has no source_ids or assumption_ids")
            for claim_id in row_claim_ids:
                if claim_ids and claim_id not in claim_ids:
                    errors.append(f"insights contract error: variant bundle {label} references unknown claim_id {claim_id}")
                    continue
                claim = claim_by_id.get(claim_id)
                if not claim:
                    continue
                claim_source_ids = set(list_value(claim.get("source_ids")))
                claim_status = str(claim.get("freshness_status") or "").strip().lower()
                if claim_source_ids and row_source_ids and not (set(row_source_ids) & claim_source_ids):
                    errors.append(f"insights contract error: variant bundle {label} claim_id {claim_id} is not covered by source_ids")
                if not claim_source_ids and claim_status == "assumption" and not row_assumption_ids:
                    errors.append(f"insights contract error: variant bundle {label} claim_id {claim_id} is not covered by assumption_ids")
            for source_id in row_source_ids:
                if allowed_source_ids and source_id not in allowed_source_ids:
                    errors.append(f"insights contract error: variant bundle {label} references unknown source_id {source_id}")
            for assumption_id in row_assumption_ids:
                if allowed_assumption_ids and assumption_id not in allowed_assumption_ids:
                    errors.append(f"insights contract error: variant bundle {label} references unknown assumption_id {assumption_id}")
    reviewer_approval = insights.get("reviewer_approval")
    if reviewer_approval is not None:
        if not isinstance(reviewer_approval, dict):
            errors.append("insights contract error: reviewer_approval must be an object")
        elif reviewer_approval:
            for field in REVIEWER_APPROVAL_CONTRACT_FIELDS:
                if field not in reviewer_approval or (field not in {"required", "approved", "approved_by", "approved_at", "approval_source", "blocked_reason", "review_items"} and not present(reviewer_approval.get(field))):
                    errors.append(f"insights contract error: reviewer_approval missing {field}")
            status = str(reviewer_approval.get("status") or "").strip()
            if status and status not in REVIEWER_APPROVAL_STATUSES:
                errors.append(f"insights contract error: reviewer_approval has invalid status {status}")
            required = bool(reviewer_approval.get("required"))
            approved = bool(reviewer_approval.get("approved"))
            if status == "required" and not present(reviewer_approval.get("blocked_reason")):
                errors.append("insights contract error: reviewer_approval required without blocked_reason")
            if status == "approved" and (not approved or not present(reviewer_approval.get("approved_by")) or not present(reviewer_approval.get("approval_source"))):
                errors.append("insights contract error: reviewer_approval approved without explicit approval source")
            review_items = reviewer_approval.get("review_items")
            if not isinstance(review_items, list):
                errors.append("insights contract error: reviewer_approval review_items must be a list")
                review_items = []
            if required and not review_items:
                errors.append("insights contract error: reviewer_approval required without review_items")
            for index, row in enumerate(review_items, start=1):
                if not isinstance(row, dict):
                    errors.append(f"insights contract error: reviewer_approval review_items[{index}] must be an object")
                    continue
                label = str(row.get("review_id") or f"review_items[{index}]")
                for field in REVIEW_ITEM_CONTRACT_FIELDS:
                    if field not in row or (field not in {"source_ids", "assumption_ids", "blocked_reason"} and not present(row.get(field))):
                        errors.append(f"insights contract error: reviewer item {label} missing {field}")
                row_claim_ids = list_value(row.get("claim_ids"))
                row_source_ids = list_value(row.get("source_ids"))
                row_assumption_ids = list_value(row.get("assumption_ids"))
                if not row_claim_ids:
                    errors.append(f"insights contract error: reviewer item {label} has no claim_ids")
                if not row_source_ids and not row_assumption_ids:
                    errors.append(f"insights contract error: reviewer item {label} has no source_ids or assumption_ids")
                for claim_id in row_claim_ids:
                    if claim_ids and claim_id not in claim_ids:
                        errors.append(f"insights contract error: reviewer item {label} references unknown claim_id {claim_id}")
                for source_id in row_source_ids:
                    if allowed_source_ids and source_id not in allowed_source_ids:
                        errors.append(f"insights contract error: reviewer item {label} references unknown source_id {source_id}")
                for assumption_id in row_assumption_ids:
                    if allowed_assumption_ids and assumption_id not in allowed_assumption_ids:
                        errors.append(f"insights contract error: reviewer item {label} references unknown assumption_id {assumption_id}")
    return dedupe(errors)


def is_generic_recommendation(row: dict[str, Any]) -> bool:
    combined = " ".join(
        str(row.get(field) or "")
        for field in ["content", "change", "hypothesis", "owner_action", "name", "cta"]
    ).strip().lower()
    measurement = str(row.get("measurement_event") or row.get("metric") or row.get("primary_metric") or "").strip().lower()
    generic_actions = [
        "improve conversion",
        "increase conversion",
        "optimize funnel",
        "grow revenue",
        "get more leads",
        "boost sales",
        "make it better",
    ]
    generic_measurements = {"conversion", "conversions", "leads", "sales", "revenue", "kpi", "metric"}
    return any(phrase in combined for phrase in generic_actions) and measurement in generic_measurements


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
    source_ids = select_support_source_ids(sources, evidence_refs, competitors, 3)
    support = source_ids[0] if source_ids else support
    assumption_ids = first_ids(assumptions, "id", 3)
    competitor_synthesis = build_competitor_synthesis(competitors, sources, source_ids, ru)
    channel_synthesis = build_channel_synthesis(intake, ru)
    niche_profile = build_niche_profile(intake, ru)
    evidence_claims = build_evidence_claims(sources, assumptions, source_ids, ru)
    promise_proof_model = build_promise_proof_model(intake, sources, evidence_claims, assumptions, ru, niche_profile, channel_synthesis)
    source_backed_claims = [claim for claim in evidence_claims if list_value(claim.get("source_ids"))]
    claim_ids = first_ids(source_backed_claims if source_ids else evidence_claims, "claim_id", 2)
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
        "niche_profile": str(niche_profile.get("profile_key") or ""),
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

    screens = add_recommendation_contract(
        build_screen_insights(intake, skeleton, support, confidence, ru, competitor_synthesis, channel_synthesis, niche_profile),
        "screen",
        audience,
        source_ids,
        assumption_ids,
        claim_ids,
        phase,
        ru,
        evidence_claims,
    )
    screens = apply_proof_mechanics_to_screens(screens, promise_proof_model, ru)
    screens = apply_promise_proof_to_recommendations(screens, promise_proof_model)
    experiments = add_recommendation_contract(
        build_experiment_insights(intake, skeleton, support, confidence, ru, competitor_synthesis, channel_synthesis, niche_profile),
        "experiment",
        audience,
        source_ids,
        assumption_ids,
        claim_ids,
        phase,
        ru,
        evidence_claims,
    )
    experiments = apply_experiment_quality_gates(experiments, intake, ru)
    experiments = apply_promise_proof_to_recommendations(experiments, promise_proof_model)
    risks = build_risk_insights(data, support, ru, competitor_synthesis, channel_synthesis, promise_proof_model, niche_profile)
    current_funnel_diff = build_current_funnel_diff(intake, screens, assumptions, evidence_claims, phase, ru)
    variant_bundles = build_variant_bundles(
        screens,
        experiments,
        promise_proof_model,
        competitor_synthesis,
        channel_synthesis,
        niche_profile,
        current_funnel_diff,
        ru,
    )

    return {
        "version": VERSION,
        "output_language": language,
        "decision_summary": decision_summary,
        "segments": segments,
        "screens": screens,
        "experiments": experiments,
        "risks": risks,
        "evidence_refs": evidence_refs,
        "evidence_claims": evidence_claims,
        "promise_proof_model": promise_proof_model,
        "competitor_synthesis": competitor_synthesis,
        "channel_synthesis": channel_synthesis,
        "niche_profile": niche_profile,
        "current_funnel_diff": current_funnel_diff,
        "variant_bundles": variant_bundles,
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
    if promise_risk_level(" ".join([str(intake.get("offer") or ""), str(intake.get("target_kpi") or "")])) == "high":
        assumptions.append({"id": "A5", "statement": "Рискованные утверждения про деньги, юридические последствия или гарантии требуют подтвержденного источника и проверки." if ru else "Risky money, legal, or guarantee claims need source-backed proof and review.", "used_in": "promise_proof"})
    if not current_funnel_step_values(intake):
        assumptions.append({"id": "A6", "statement": "Текущая воронка не предоставлена; сравнение текущей и предложенной воронки остается допущением." if ru else "Current funnel was not provided; current vs proposed changes remain an assumption.", "used_in": "current_funnel_diff"})
    if not assumptions:
        assumptions.append({"id": "A1", "statement": "Текст экранов все еще нужно проверить на языке реальных клиентов перед запуском." if ru else "Screen copy still needs validation against customer language before launch.", "used_in": "screen_playbook"})
    return assumptions


def current_funnel_step_values(intake: dict[str, Any]) -> list[str]:
    raw = intake.get("current_funnel")
    if isinstance(raw, list):
        candidates = raw
    elif present(raw):
        candidates = re.split(r"\s*(?:->|=>|→)\s*|\n+", str(raw))
    else:
        candidates = []
    steps: list[str] = []
    for candidate in candidates:
        text = re.sub(r"^\s*[-*]\s*", "", str(candidate or ""))
        text = re.sub(r"^\s*\d+[.)]\s*", "", text)
        text = compact_fragment(re.sub(r"\s+", " ", text.strip()), 180)
        if text:
            steps.append(text)
    return dedupe(steps)


def current_funnel_assumption_ids(assumptions: list[dict[str, Any]]) -> list[str]:
    ids = []
    for row in assumptions:
        used_in = str(row.get("used_in") or "")
        statement = str(row.get("statement") or "").lower()
        if used_in == "current_funnel_diff" or "current funnel" in statement or "текущая воронка" in statement:
            ids.append(str(row.get("id") or ""))
    return [value for value in dedupe(ids) if value]


def diff_contract_from_screen(row: dict[str, Any], fallback_assumption_ids: list[str]) -> dict[str, Any]:
    return {
        "claim_ids": list_value(row.get("claim_ids")),
        "source_ids": list_value(row.get("source_ids")),
        "assumption_ids": list_value(row.get("assumption_ids")) or fallback_assumption_ids,
        "blocked_reason": str(row.get("blocked_reason") or ""),
    }


def current_funnel_change_type(index: int, current_step: str, screen_count: int) -> str:
    if not current_step:
        return "add"
    if screen_count and index == screen_count - 1:
        return "instrument"
    if index == 1:
        return "clarify"
    return "replace"


def current_funnel_diff_reason(change_type: str, current_step: str, proposed_stage: str, measurement_event: str, ru: bool) -> str:
    if ru:
        if change_type == "add":
            return f"В текущем описании нет отдельного шага для «{proposed_stage}»; добавить его только как предложенный шаг и проверить у пользователя."
        if change_type == "clarify":
            return f"Текущий шаг «{current_step}» нужно уточнить: предложенный маршрут делает цель шага и следующий вопрос явными."
        if change_type == "instrument":
            return f"Текущий шаг «{current_step}» сопоставлен с «{proposed_stage}» и должен записывать событие `{measurement_event}` перед интерпретацией результата."
        return f"Текущий шаг «{current_step}» сопоставлен с «{proposed_stage}»; предложенный маршрут меняет содержание шага, а не выдумывает новый текущий шаг."
    if change_type == "add":
        return f"The current notes do not include a separate `{proposed_stage}` step; add it as a proposed step and confirm it with the user."
    if change_type == "clarify":
        return f"The current step `{current_step}` needs clarification: the proposed route makes the step goal and next question explicit."
    if change_type == "instrument":
        return f"The current step `{current_step}` maps to `{proposed_stage}` and should log `{measurement_event}` before results are interpreted."
    return f"The current step `{current_step}` maps to `{proposed_stage}`; the proposed route changes the step content without inventing a current step."


def proposed_step_text(screen: dict[str, Any], ru: bool) -> str:
    stage = dash_text(screen.get("stage") or screen.get("funnel_stage"), ru)
    content = compact_fragment(screen.get("content"), 180)
    return f"{stage}: {content}" if content else stage


def build_current_funnel_diff(
    intake: dict[str, Any],
    screens: list[dict[str, Any]],
    assumptions: list[dict[str, Any]],
    evidence_claims: list[dict[str, Any]],
    phase: str,
    ru: bool,
) -> dict[str, Any]:
    current_steps = current_funnel_step_values(intake)
    fallback_assumption_ids = first_ids(assumptions, "id", 3)
    missing_current_assumptions = current_funnel_assumption_ids(assumptions)
    fallback_claim_ids = first_ids(evidence_claims, "claim_id", 2)
    rows: list[dict[str, Any]] = []

    if not current_steps:
        first_screen = screens[0] if screens else {}
        contract = diff_contract_from_screen(first_screen, fallback_assumption_ids) if first_screen else {
            "claim_ids": fallback_claim_ids,
            "source_ids": [],
            "assumption_ids": fallback_assumption_ids,
            "blocked_reason": "",
        }
        contract["assumption_ids"] = dedupe(list_value(contract.get("assumption_ids")) + missing_current_assumptions)
        missing_reason = (
            "Текущая воронка не предоставлена; сначала нужно подтвердить текущие шаги discovery/evaluation/conversion."
            if ru
            else "Current funnel was not provided; confirm the existing discovery, evaluation, and conversion steps first."
        )
        rows.append(
            {
                "id": "funnel-diff-1",
                "current_step": "",
                "proposed_stage": str(first_screen.get("stage") or first_screen.get("funnel_stage") or ""),
                "proposed_step": proposed_step_text(first_screen, ru) if first_screen else "",
                "change_type": "clarify",
                "reason": missing_reason,
                "measurement_event": str(first_screen.get("event_id") or first_screen.get("measurement_event") or first_screen.get("metric") or "CurrentFunnelClarified"),
                **contract,
                "blocked_reason": append_blocked_reason(contract.get("blocked_reason"), missing_reason),
            }
        )
        return {
            "status": "missing_current_funnel",
            "raw_current_steps": [],
            "proposed_steps": [proposed_step_text(screen, ru) for screen in screens],
            "rows": rows,
            "assumption_ids": missing_current_assumptions,
            "blocked_reason": missing_reason,
        }

    for index, screen in enumerate(screens):
        current_step = current_steps[index] if index < len(current_steps) else ""
        stage = str(screen.get("stage") or screen.get("funnel_stage") or "")
        measurement_event = str(screen.get("event_id") or screen.get("measurement_event") or screen.get("metric") or "")
        change_type = current_funnel_change_type(index, current_step, len(screens))
        contract = diff_contract_from_screen(screen, fallback_assumption_ids)
        rows.append(
            {
                "id": f"funnel-diff-{len(rows) + 1}",
                "current_step": current_step,
                "proposed_stage": stage,
                "proposed_step": proposed_step_text(screen, ru),
                "change_type": change_type,
                "reason": current_funnel_diff_reason(change_type, current_step, stage, measurement_event, ru),
                "measurement_event": measurement_event,
                **contract,
            }
        )

    for current_step in current_steps[len(screens) :]:
        reason = (
            f"Текущий шаг «{current_step}» не сопоставлен с предложенным маршрутом; не удалять его по умолчанию, пока пользователь не подтвердит роль шага."
            if ru
            else f"The current step `{current_step}` is not mapped to the proposed route; do not remove it by default until the user confirms its role."
        )
        rows.append(
            {
                "id": f"funnel-diff-{len(rows) + 1}",
                "current_step": current_step,
                "proposed_stage": "",
                "proposed_step": "",
                "change_type": "clarify",
                "reason": reason,
                "measurement_event": "CurrentFunnelStepClarified",
                "claim_ids": fallback_claim_ids,
                "source_ids": [],
                "assumption_ids": fallback_assumption_ids,
                "blocked_reason": reason,
            }
        )

    return {
        "status": "provided",
        "raw_current_steps": current_steps,
        "proposed_steps": [proposed_step_text(screen, ru) for screen in screens],
        "rows": rows,
        "assumption_ids": [],
        "blocked_reason": "",
    }


def primary_promise_proof_row(promise_proof_model: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not isinstance(promise_proof_model, list):
        return {}
    for row in promise_proof_model:
        if isinstance(row, dict):
            return row
    return {}


def current_funnel_diff_row(current_funnel_diff: dict[str, Any] | None, index: int) -> dict[str, Any]:
    if not isinstance(current_funnel_diff, dict):
        return {}
    rows = current_funnel_diff.get("rows")
    if not isinstance(rows, list) or index >= len(rows) or not isinstance(rows[index], dict):
        return {}
    return rows[index]


def variant_measurement_event(row: dict[str, Any]) -> str:
    return str(row.get("event_id") or row.get("measurement_event") or row.get("metric") or row.get("primary_metric") or "").strip()


def variant_control_reference(row: dict[str, Any], diff_row: dict[str, Any], ru: bool) -> str:
    current_step = str(diff_row.get("current_step") or "").strip()
    if current_step:
        return current_step
    stage = str(row.get("stage") or row.get("funnel_stage") or row.get("name") or "").strip()
    cta = str(row.get("cta") or "").strip()
    content = compact_fragment(row.get("content") or row.get("change") or row.get("owner_action"), 140)
    if cta:
        return f"{stage}: {cta}" if stage else cta
    if content:
        return f"{stage}: {content}" if stage else content
    return "текущий контроль нужно подтвердить" if ru else "current control needs confirmation"


def variant_proof_requirement(row: dict[str, Any], promise_row: dict[str, Any], ru: bool) -> str:
    proof_needed = str(row.get("proof_needed") or "").strip()
    promise_requirement = str(promise_row.get("proof_requirement") or "").strip()
    if proof_needed.lower() in {"", "none", "нет", "-", "не указано", "not provided"}:
        return promise_requirement or ("доказательство не требуется для этого шага" if ru else "no proof requirement for this step")
    if promise_requirement and promise_requirement not in proof_needed:
        return f"{proof_needed} {promise_requirement}"
    return proof_needed


def variant_guardrail(row: dict[str, Any], experiment: dict[str, Any], ru: bool) -> str:
    return str(
        row.get("guardrail")
        or row.get("guardrail_metrics")
        or experiment.get("guardrail_metrics")
        or experiment.get("guardrail")
        or ("качество лидов и потери событий" if ru else "lead quality and event loss")
    ).strip()


def variant_contract_fields(row: dict[str, Any], promise_row: dict[str, Any]) -> dict[str, Any]:
    promise_status = str(promise_row.get("evidence_status") or "")
    include_promise = bool(promise_row and (promise_proof_blocks_ready(promise_status) or list_value(promise_row.get("source_ids"))))
    claim_ids = list_value(row.get("claim_ids"))
    source_ids = list_value(row.get("source_ids"))
    assumption_ids = list_value(row.get("assumption_ids"))
    blocked_reason = str(row.get("blocked_reason") or "")
    if include_promise:
        claim_ids = dedupe(claim_ids + list_value(promise_row.get("claim_ids")))
        source_ids = dedupe(source_ids + list_value(promise_row.get("source_ids")))
        assumption_ids = dedupe(assumption_ids + list_value(promise_row.get("assumption_ids")))
        blocked_reason = append_blocked_reason(blocked_reason, str(promise_row.get("blocked_reason") or ""))
    return {
        "claim_ids": claim_ids,
        "source_ids": source_ids,
        "assumption_ids": assumption_ids,
        "blocked_reason": blocked_reason,
    }


def variant_signal_parts(
    row: dict[str, Any],
    current_step: str,
    competitor_synthesis: dict[str, Any] | None,
    channel_synthesis: dict[str, Any] | None,
    niche_profile: dict[str, Any] | None,
    ru: bool,
) -> list[str]:
    parts: list[str] = []
    pack = primary_channel_pack(channel_synthesis)
    if pack:
        label = str(pack.get("label") or pack.get("channel") or "").strip()
        focus = str(row.get("channel_focus") or pack.get("experiment_focus") or pack.get("journey") or "").strip()
        if label and focus:
            parts.append(f"{label}: {focus}")
        elif label:
            parts.append(label)
    if niche_profile_has_match(niche_profile):
        label = str(niche_profile.get("label") or "").strip()
        defaults = list_value(niche_profile.get("funnel_defaults"))
        if label and defaults:
            parts.append(f"{label}: {defaults[min(1, len(defaults) - 1)]}")
        elif label:
            parts.append(label)
    competitor_pattern = str(row.get("competitor_pattern") or "").strip()
    if competitor_pattern:
        parts.append(competitor_pattern)
    elif competitor_synthesis_has_patterns(competitor_synthesis):
        competitor_cta = competitor_pattern_phrase(competitor_synthesis, "primary_cta", ru, 2)
        if competitor_cta:
            parts.append(competitor_cta)
    if current_step:
        parts.append(("текущий шаг: " if ru else "current step: ") + current_step)
    return [compact_fragment(part, 180) for part in parts if part]


def variant_hypothesis(
    variant_type: str,
    row: dict[str, Any],
    current_step: str,
    measurement_event: str,
    guardrail: str,
    competitor_synthesis: dict[str, Any] | None,
    channel_synthesis: dict[str, Any] | None,
    niche_profile: dict[str, Any] | None,
    ru: bool,
) -> str:
    target_segment = dash_text(row.get("target_segment"), ru)
    signals = "; ".join(variant_signal_parts(row, current_step, competitor_synthesis, channel_synthesis, niche_profile, ru))
    signal_clause = f" с учетом сигналов: {signals}" if ru and signals else f" using signals: {signals}" if signals else ""
    if ru:
        type_text = {
            "copy": "текст входного шага",
            "cta": "действие пользователя",
            "route": "маршрут шага",
            "proof_placement": "размещение доказательства",
            "qualification": "квалификацию",
        }.get(variant_type, "вариант")
        return f"Если изменить {type_text} для сегмента «{target_segment}»{signal_clause}, событие `{measurement_event}` даст чистый сигнал без ухудшения контрольного риска «{guardrail}»."
    type_text = {
        "copy": "entry copy",
        "cta": "user action",
        "route": "step route",
        "proof_placement": "proof placement",
        "qualification": "qualification path",
    }.get(variant_type, "variant")
    return f"If the {type_text} changes for `{target_segment}`{signal_clause}, `{measurement_event}` should produce a clean signal without worsening `{guardrail}`."


def variant_copy_text(row: dict[str, Any], ru: bool) -> str:
    content = compact_fragment(row.get("content"), 240)
    cta = str(row.get("cta") or "").strip()
    if ru:
        return f"{content} Действие пользователя: {cta}." if cta else content
    return f"{content} User action: {cta}." if cta else content


def variant_action_text(
    variant_type: str,
    row: dict[str, Any],
    promise_row: dict[str, Any],
    ru: bool,
) -> str:
    if variant_type == "proof_placement":
        fallback = str(promise_row.get("fallback") or "").strip()
        proof_needed = str(row.get("proof_needed") or "").strip()
        cta = str(row.get("cta") or "").strip()
        if fallback:
            return (
                f"Поставить proof/no-proof состояние рядом с действием «{cta}»: {fallback}"
                if ru
                else f"Place the proof/no-proof state next to `{cta}`: {fallback}"
            )
        return (
            f"Поставить «{proof_needed}» рядом с действием «{cta}» и сохранить ссылки на источники."
            if ru
            else f"Place `{proof_needed}` next to `{cta}` and preserve source references."
        )
    content = compact_fragment(row.get("content") or row.get("change") or row.get("owner_action"), 240)
    cta = str(row.get("cta") or "").strip()
    if ru:
        return f"{content} Следующее действие: {cta}." if cta else content
    return f"{content} Next action: {cta}." if cta else content


def build_variant_bundle_from_screen(
    variant_number: int,
    screen_index: int,
    variant_type: str,
    row: dict[str, Any],
    experiment: dict[str, Any],
    promise_row: dict[str, Any],
    current_funnel_diff: dict[str, Any] | None,
    competitor_synthesis: dict[str, Any] | None,
    channel_synthesis: dict[str, Any] | None,
    niche_profile: dict[str, Any] | None,
    ru: bool,
) -> dict[str, Any] | None:
    measurement_event = variant_measurement_event(row)
    if not measurement_event:
        return None
    diff_row = current_funnel_diff_row(current_funnel_diff, screen_index)
    current_step = str(diff_row.get("current_step") or "").strip()
    guardrail = variant_guardrail(row, experiment, ru)
    contract = variant_contract_fields(row, promise_row)
    variant: dict[str, Any] = {
        "variant_id": f"variant-{variant_number}",
        "stage": str(row.get("stage") or row.get("funnel_stage") or row.get("name") or ""),
        "funnel_stage": str(row.get("funnel_stage") or row.get("stage") or row.get("name") or ""),
        "target_segment": str(row.get("target_segment") or ""),
        "variant_type": variant_type,
        "control_reference": variant_control_reference(row, diff_row, ru),
        "current_step": current_step,
        "hypothesis": variant_hypothesis(
            variant_type,
            row,
            current_step,
            measurement_event,
            guardrail,
            competitor_synthesis,
            channel_synthesis,
            niche_profile,
            ru,
        ),
        "proof_requirement": variant_proof_requirement(row, promise_row, ru),
        "measurement_event": measurement_event,
        "guardrail": guardrail,
        **contract,
    }
    if variant_type in {"copy", "cta"}:
        variant["variant_copy"] = variant_copy_text(row, ru)
        variant["variant_action"] = ""
    else:
        variant["variant_copy"] = ""
        variant["variant_action"] = variant_action_text(variant_type, row, promise_row, ru)
    return variant


def build_variant_bundles(
    screens: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    promise_proof_model: list[dict[str, Any]],
    competitor_synthesis: dict[str, Any] | None,
    channel_synthesis: dict[str, Any] | None,
    niche_profile: dict[str, Any] | None,
    current_funnel_diff: dict[str, Any] | None,
    ru: bool,
) -> list[dict[str, Any]]:
    if not screens:
        return []
    promise_row = primary_promise_proof_row(promise_proof_model)
    experiment = experiments[0] if experiments and isinstance(experiments[0], dict) else {}
    current_status = str(current_funnel_diff.get("status") or "") if isinstance(current_funnel_diff, dict) else ""
    specs: list[tuple[int, str]] = []
    if screens:
        specs.append((0, "copy"))
    if len(screens) > 1:
        specs.append((1, "route" if current_status == "provided" else "qualification"))
    proof_index = next(
        (
            index
            for index, row in enumerate(screens)
            if index not in {spec[0] for spec in specs}
            and str(row.get("proof_needed") or "").strip().lower() not in {"", "none", "нет", "-", "не указано"}
        ),
        -1,
    )
    if proof_index >= 0:
        specs.append((proof_index, "proof_placement"))

    bundles: list[dict[str, Any]] = []
    used: set[tuple[int, str]] = set()
    for screen_index, variant_type in specs:
        if len(bundles) >= 3 or screen_index >= len(screens) or (screen_index, variant_type) in used:
            continue
        row = screens[screen_index]
        if not isinstance(row, dict):
            continue
        bundle = build_variant_bundle_from_screen(
            len(bundles) + 1,
            screen_index,
            variant_type,
            row,
            experiment,
            promise_row,
            current_funnel_diff,
            competitor_synthesis,
            channel_synthesis,
            niche_profile,
            ru,
        )
        if bundle:
            bundles.append(bundle)
            used.add((screen_index, variant_type))
    return bundles


def reviewer_approval_input(intake: dict[str, Any]) -> dict[str, Any]:
    raw = intake.get("reviewer_approval")
    if isinstance(raw, dict):
        text = " ".join(str(raw.get(field) or "") for field in ["status", "approved_by", "approved_at", "notes"]).strip()
        approved_by = str(raw.get("approved_by") or "").strip()
        approved_at = str(raw.get("approved_at") or "").strip()
    else:
        text = str(raw or "").strip()
        approved_by = ""
        approved_at = ""
    normalized = text.lower()
    negative = bool(re.search(r"\b(not approved|no approval|not reviewed|needs review|pending)\b|(не одобр|нет одобр|нужно соглас|ожидает)", normalized))
    approved = bool(re.search(r"\b(approved|approve|sign[ -]?off|signed off|ok to launch|reviewed)\b|(одобр|согласован|согласовано|апрув|можно запускать)", normalized)) and not negative
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if date_match and not approved_at:
        approved_at = date_match.group(1)
    by_match = re.search(r"\bby\s+([^,;|]+)", text, re.IGNORECASE)
    if by_match and not approved_by:
        approved_by = by_match.group(1).strip()
        approved_by = re.sub(r"\s+on\s+20\d{2}-\d{2}-\d{2}.*$", "", approved_by, flags=re.IGNORECASE).strip()
    ru_by_match = re.search(r"(?:от|ревьюер|reviewer)\s+([^,;|]+)", text, re.IGNORECASE)
    if ru_by_match and not approved_by:
        approved_by = ru_by_match.group(1).strip()
    if approved and not approved_by:
        approved_by = "human reviewer"
    return {
        "approved": approved,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "approval_source": text,
    }


def reviewer_item(
    review_id: str,
    review_type: str,
    target_id: str,
    target_type: str,
    risk_level: str,
    reason: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "review_type": review_type,
        "target_id": target_id,
        "target_type": target_type,
        "risk_level": risk_level,
        "reason": reason,
        "claim_ids": list_value(row.get("claim_ids")),
        "source_ids": list_value(row.get("source_ids")),
        "assumption_ids": list_value(row.get("assumption_ids")),
        "blocked_reason": str(row.get("blocked_reason") or reason),
    }


def build_reviewer_approval(data: dict[str, Any], insights: dict[str, Any], ru: bool) -> dict[str, Any]:
    intake = data.get("intake", {}) if isinstance(data.get("intake"), dict) else {}
    items: list[dict[str, Any]] = []

    promise_rows = insights.get("promise_proof_model") if isinstance(insights.get("promise_proof_model"), list) else []
    for row in promise_rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("risk_level") or "").strip().lower() != "high":
            continue
        reason = (
            "Рискованное коммерческое, юридическое или финансовое обещание требует ручного review перед ready."
            if ru
            else "Risky commercial, legal, or financial promise requires human review before ready."
        )
        items.append(
            reviewer_item(
                f"review-{len(items) + 1}",
                "high_risk_promise",
                str(row.get("promise_id") or "promise"),
                "promise_proof",
                "high",
                reason,
                row,
            )
        )

    for row in recommendation_rows(insights):
        if not isinstance(row, dict):
            continue
        blocked = str(row.get("blocked_reason") or "").strip()
        assumption_ids = list_value(row.get("assumption_ids"))
        source_ids = list_value(row.get("source_ids"))
        generic_research_blocker = blocked in {
            "needs evidence before launch",
            "нужно подтвердить источники перед запуском",
        }
        if generic_research_blocker and source_ids:
            continue
        if not blocked and (not assumption_ids or source_ids):
            continue
        reason = (
            "Рекомендация опирается на допущение или блокер и требует review перед ready."
            if ru
            else "Recommendation relies on an assumption or blocker and requires review before ready."
        )
        items.append(
            reviewer_item(
                f"review-{len(items) + 1}",
                "under_supported_recommendation",
                str(row.get("id") or row.get("type") or "recommendation"),
                str(row.get("type") or "recommendation"),
                "medium",
                reason,
                row,
            )
        )

    approval = reviewer_approval_input(intake)
    required = bool(items)
    approved = bool(required and approval["approved"])
    if not required:
        status = "not_required"
        blocked_reason = ""
    elif approved:
        status = "approved"
        blocked_reason = ""
    else:
        status = "required"
        blocked_reason = (
            "Нужно явное одобрение человека для рискованных или слабо подтвержденных рекомендаций."
            if ru
            else "Explicit human approval is required for risky or under-supported recommendations."
        )
    return {
        "status": status,
        "required": required,
        "approved": approved,
        "approved_by": approval["approved_by"] if approved else "",
        "approved_at": approval["approved_at"] if approved else "",
        "approval_source": approval["approval_source"] if approved else "",
        "blocked_reason": blocked_reason,
        "review_items": items,
    }


def reviewer_approval_blockers(reviewer_approval: dict[str, Any], ru: bool) -> list[str]:
    if not isinstance(reviewer_approval, dict):
        return []
    if reviewer_approval.get("status") != "required":
        return []
    reason = str(reviewer_approval.get("blocked_reason") or "").strip()
    if not reason:
        reason = "reviewer approval required" if not ru else "требуется одобрение ревьюера"
    prefix = "одобрение ревьюера" if ru else "reviewer approval"
    return [f"{prefix}: {reason}"]


def apply_competitor_patterns_to_screens(
    rows: list[dict[str, str]],
    offer: str,
    target_kpi: str,
    competitor_synthesis: dict[str, Any] | None,
    ru: bool,
) -> list[dict[str, str]]:
    if not competitor_synthesis_has_patterns(competitor_synthesis):
        return rows

    cta = competitor_values_phrase(competitor_synthesis, "primary_cta", ru)
    onboarding = competitor_values_phrase(competitor_synthesis, "onboarding_pattern", ru)
    first_value = competitor_values_phrase(competitor_synthesis, "first_value_path", ru)
    proof = competitor_values_phrase(competitor_synthesis, "proof", ru)
    pricing = competitor_values_phrase(competitor_synthesis, "pricing", ru)
    weaknesses = competitor_values_phrase(competitor_synthesis, "observed_weaknesses", ru)

    if cta and rows:
        rows[0]["competitor_pattern"] = competitor_pattern_phrase(competitor_synthesis, "primary_cta", ru)
        rows[0]["content"] = (
            f"Отстроить первый экран от наблюдаемых призывов конкурентов ({cta}): связать обещание «{offer}» с конкретным превью результата до следующего действия."
            if ru
            else f"Differentiate the entry screen from observed competitor CTAs ({cta}) by pairing the `{offer}` promise with a concrete result preview before the next action."
        )
        rows[0]["cta"] = "Увидеть мой результат" if ru else "See my result preview"
        rows[0]["proof_needed"] = "короткое доказательство рядом с примером результата или честная пометка о его отсутствии" if ru else "short proof next to the preview or an explicit no-proof state"

    if onboarding and len(rows) > 1:
        rows[1]["competitor_pattern"] = competitor_pattern_phrase(competitor_synthesis, "onboarding_pattern", ru)
        rows[1]["content"] = (
            f"Сделать уточнение не тяжелее наблюдаемого онбординга конкурентов ({onboarding}); спрашивать только контекст, нужный для первого разбора."
            if ru
            else f"Keep qualification no heavier than observed competitor onboarding patterns ({onboarding}); ask only for the context needed to create the first diagnosis."
        )
        rows[1]["guardrail"] = "время заполнения и брошенные шаги" if ru else "completion time and abandoned steps"

    first_value_parts = [part for part in [first_value, proof] if part]
    if first_value_parts and len(rows) > 2:
        label = "; ".join(first_value_parts)
        rows[2]["competitor_pattern"] = "; ".join(
            part
            for part in [
                competitor_pattern_phrase(competitor_synthesis, "first_value_path", ru),
                competitor_pattern_phrase(competitor_synthesis, "proof", ru),
            ]
            if part
        )
        rows[2]["content"] = (
            f"Показать первую ценность через наблюдаемые конкурентные механики ({label}): 1 узкое место, маршрут к метрике «{target_kpi}» и состояние доказательств."
            if ru
            else f"Make first value tangible through observed competitor mechanics ({label}): one bottleneck, the route to `{target_kpi}`, and the proof state."
        )
        rows[2]["proof_needed"] = "использовать только подтвержденный паттерн доказательства или явное допущение" if ru else "use only the confirmed proof pattern or an explicit assumption"

    packaging_parts = [part for part in [pricing, weaknesses] if part]
    if packaging_parts and len(rows) > 3:
        rows[3]["competitor_pattern"] = "; ".join(
            part
            for part in [
                competitor_pattern_phrase(competitor_synthesis, "pricing", ru),
                competitor_pattern_phrase(competitor_synthesis, "observed_weaknesses", ru),
            ]
            if part
        )
        weakness_clause = (
            f" и явно избежать наблюдаемых слабых мест ({weaknesses})"
            if weaknesses and ru
            else f" while avoiding observed weaknesses ({weaknesses})"
            if weaknesses
            else ""
        )
        rows[3]["content"] = (
            f"Упаковать следующий шаг относительно наблюдаемой цены/офера конкурентов ({pricing or '; '.join(packaging_parts)}){weakness_clause}: ожидания, срок, доказательство и что пользователь получит."
            if ru
            else f"Package the conversion step against observed competitor offer packaging ({pricing or '; '.join(packaging_parts)}){weakness_clause}: expectations, timing, proof, and what the user receives."
        )
        rows[3]["guardrail"] = "низкое качество лидов и расхождение ожиданий" if ru else "lead quality and expectation mismatch"

    return rows


def append_sentence(base: Any, addition: Any) -> str:
    base_text = re.sub(r"\s+", " ", str(base or "").strip())
    addition_text = re.sub(r"\s+", " ", str(addition or "").strip())
    if not base_text:
        return addition_text
    if not addition_text:
        return base_text
    return f"{addition_text} {base_text}"


def apply_channel_pack_to_screens(
    rows: list[dict[str, str]],
    channel_synthesis: dict[str, Any] | None,
) -> list[dict[str, str]]:
    pack = primary_channel_pack(channel_synthesis)
    if not pack:
        return rows
    focus_fields = ["entry_focus", "qualification_focus", "first_value_route", "conversion_focus"]
    event_ids = list_value(pack.get("event_ids"))
    for index, row in enumerate(rows):
        if index < len(focus_fields):
            row["channel_pack"] = str(pack.get("channel") or "")
            row["channel_focus"] = str(pack.get(focus_fields[index]) or "")
            row["content"] = append_sentence(row.get("content"), row["channel_focus"])
        if index < len(event_ids):
            row["event_id"] = event_ids[index]
            if index < len(rows) - 1:
                row["metric"] = event_ids[index]
        if index == 0 and present(pack.get("cta")):
            row["cta"] = str(pack.get("cta"))
        if present(pack.get("guardrail")):
            row["guardrail"] = append_sentence(row.get("guardrail"), pack.get("guardrail"))
    return rows


def append_profile_list(base: Any, values: Any, limit: int = 2) -> str:
    items = list_value(values)[:limit]
    if not items:
        return str(base or "")
    return append_sentence(base, "; ".join(items))


def apply_niche_profile_to_screens(
    rows: list[dict[str, str]],
    niche_profile: dict[str, Any] | None,
    ru: bool,
) -> list[dict[str, str]]:
    if not niche_profile_has_match(niche_profile):
        return rows
    label = str(niche_profile.get("label") or "")
    defaults = list_value(niche_profile.get("funnel_defaults"))
    vocabulary = list_value(niche_profile.get("vocabulary"))
    proof_patterns = list_value(niche_profile.get("proof_patterns"))
    risks = list_value(niche_profile.get("risks"))
    for index, row in enumerate(rows):
        row["niche_profile"] = str(niche_profile.get("profile_key") or "")
        if vocabulary:
            row["niche_vocabulary"] = ", ".join(vocabulary[:4])
        if index < len(defaults):
            prefix = (
                f"Нишевый профиль {label}: {defaults[index]}."
                if ru
                else f"{label} profile default: {defaults[index]}."
            )
            row["content"] = append_sentence(row.get("content"), prefix)
        if proof_patterns and str(row.get("proof_needed") or "").strip().lower() not in {"", "none", "нет"}:
            proof_prefix = (
                f"Профильный proof pattern: {proof_patterns[min(index, len(proof_patterns) - 1)]}"
                if ru
                else f"Profile proof pattern: {proof_patterns[min(index, len(proof_patterns) - 1)]}"
            )
            row["proof_needed"] = append_sentence(row.get("proof_needed"), proof_prefix)
        if risks:
            row["guardrail"] = append_sentence(row.get("guardrail"), risks[min(index, len(risks) - 1)])
        if not present(row.get("event_id")):
            event = niche_profile_event(niche_profile, index)
            if event:
                row["event_id"] = event
                if index < len(rows) - 1:
                    row["metric"] = event
    return rows


def proof_mechanic_from_model(promise_proof_model: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not isinstance(promise_proof_model, list):
        return None
    for row in promise_proof_model:
        if isinstance(row, dict) and isinstance(row.get("recommended_proof_mechanic"), dict):
            return row["recommended_proof_mechanic"]
    return None


def apply_proof_mechanics_to_screens(
    rows: list[dict[str, Any]],
    promise_proof_model: list[dict[str, Any]] | None,
    ru: bool,
) -> list[dict[str, Any]]:
    mechanic = proof_mechanic_from_model(promise_proof_model)
    if not mechanic:
        return rows
    format_text = str(mechanic.get("recommended_format") or "").strip()
    if not format_text:
        return rows
    prefix = f"Рекомендованный формат proof: {format_text}" if ru else f"Recommended proof format: {format_text}"
    for row in rows:
        proof_needed = str(row.get("proof_needed") or "").strip().lower()
        if proof_needed in {"", "none", "нет"}:
            continue
        row["proof_needed"] = append_sentence(row.get("proof_needed"), prefix)
    return rows


def build_screen_insights(
    intake: dict[str, Any],
    skeleton: str,
    support: str,
    confidence: str,
    ru: bool,
    competitor_synthesis: dict[str, Any] | None = None,
    channel_synthesis: dict[str, Any] | None = None,
    niche_profile: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    target_kpi = dash_text(intake.get("target_kpi"), ru)
    offer = dash_text(intake.get("offer"), ru)
    audience = dash_text(intake.get("icp") or intake.get("primary_persona"), ru)
    if ru:
        rows = [
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
        rows = apply_competitor_patterns_to_screens(rows, offer, target_kpi, competitor_synthesis, ru)
        rows = apply_channel_pack_to_screens(rows, channel_synthesis)
        return apply_niche_profile_to_screens(rows, niche_profile, ru)
    rows = [
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
    rows = apply_competitor_patterns_to_screens(rows, offer, target_kpi, competitor_synthesis, ru)
    rows = apply_channel_pack_to_screens(rows, channel_synthesis)
    return apply_niche_profile_to_screens(rows, niche_profile, ru)


def competitor_differentiation_focus(competitor_synthesis: dict[str, Any] | None, ru: bool) -> str:
    fields = ["primary_cta", "onboarding_pattern", "proof", "pricing", "first_value_path", "observed_weaknesses"]
    parts = [competitor_pattern_phrase(competitor_synthesis, field, ru) for field in fields]
    return "; ".join(part for part in parts if part)


def build_experiment_insights(
    intake: dict[str, Any],
    skeleton: str,
    support: str,
    confidence: str,
    ru: bool,
    competitor_synthesis: dict[str, Any] | None = None,
    channel_synthesis: dict[str, Any] | None = None,
    niche_profile: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    audience = dash_text(intake.get("icp") or intake.get("primary_persona"), ru)
    target_kpi = dash_text(intake.get("target_kpi"), ru)
    channel = dash_text(intake.get("primary_channel"), ru)
    offer = dash_text(intake.get("offer"), ru)
    path_label = skeleton_label(skeleton, ru)
    differentiation_focus = competitor_differentiation_focus(competitor_synthesis, ru)
    pack = primary_channel_pack(channel_synthesis)
    channel_focus = str(pack.get("experiment_focus") or "") if pack else ""
    channel_label = str(pack.get("label") or "") if pack else ""
    channel_guardrail = str(pack.get("guardrail") or "") if pack else ""
    event_ids = list_value(pack.get("event_ids")) if pack else []
    profile_label = str(niche_profile.get("label") or "") if niche_profile_has_match(niche_profile) else ""
    profile_defaults = list_value(niche_profile.get("funnel_defaults")) if niche_profile_has_match(niche_profile) else []
    profile_risks = list_value(niche_profile.get("risks")) if niche_profile_has_match(niche_profile) else []
    profile_focus = "; ".join(profile_defaults[:2])
    channel_event = event_ids[-1] if event_ids else niche_profile_event(niche_profile, 3, "")
    profile_clause = (
        f" Нишевый профиль {profile_label}: {profile_focus}."
        if ru and profile_focus
        else f" {profile_label} profile: {profile_focus}."
        if profile_focus
        else ""
    )
    if differentiation_focus:
        if ru:
            channel_clause = f" и канальный сценарий {channel_label}: {channel_focus}" if channel_focus else ""
            return [
                {
                    "name": f"Тест отстройки: {channel_label}" if channel_label else "Тест отстройки от конкурентов",
                    "hypothesis": f"Если путь «{path_label}» отстроится от наблюдаемых конкурентных паттернов ({differentiation_focus}){channel_clause} через конкретный пример оффера «{offer}» до основного призыва, то метрика «{target_kpi}» вырастет для трафика из «{channel}».{profile_clause}",
                    "change": f"Запустить один вариант с отличающимся призывом, легким онбордингом, размещением доказательства и упаковкой оффера на основе наблюдений: {differentiation_focus}. {channel_focus}{profile_clause}",
                    "primary_metric": target_kpi,
                    "guardrail": append_profile_list(channel_guardrail or "качество лидов, потери событий, время до первого результата, расхождение ожиданий", profile_risks),
                    "decision_rule": "Оставить только если основная метрика растет, контрольные метрики не ухудшаются, а обратная связь подтверждает, что отличие от конкурентов понятно.",
                    "event_id": channel_event,
                    "support": support,
                    "confidence": confidence,
                }
            ]
        channel_clause = f" and the {channel_label} channel pack ({channel_focus})" if channel_focus else ""
        return [
            {
                "name": f"{channel_label} differentiation test" if channel_label else "Competitor differentiation test",
                "hypothesis": f"If the `{skeleton}` path differentiates from observed competitor patterns ({differentiation_focus}){channel_clause} by leading with a concrete `{offer}` preview before the main CTA, `{target_kpi}` will improve for traffic from `{channel}`.{profile_clause}",
                "change": f"Ship one variant with a differentiated CTA, lean onboarding, proof placement, and offer packaging based on the observed patterns: {differentiation_focus}. {channel_focus}{profile_clause}",
                "primary_metric": target_kpi,
                "guardrail": append_profile_list(channel_guardrail or "lead quality, event loss, time to first value, expectation mismatch", profile_risks),
                "decision_rule": "Keep it only if the primary metric improves, guardrails hold, and qualitative feedback shows the differentiation is understood.",
                "event_id": channel_event,
                "support": support,
                "confidence": confidence,
            }
        ]
    if pack:
        if ru:
            return [
                {
                    "name": f"Тест канального сценария: {channel_label}",
                    "hypothesis": f"Если путь «{path_label}» использует {channel_focus} для аудитории «{audience}», то метрика «{target_kpi}» вырастет для трафика из «{channel}».{profile_clause}",
                    "change": f"Запустить вариант под канал: {pack.get('journey')}.{profile_clause}",
                    "primary_metric": target_kpi,
                    "guardrail": append_profile_list(channel_guardrail, profile_risks),
                    "decision_rule": "Оставить только если основная метрика растет, контрольные метрики не ухудшаются, а события канального сценария записаны без потерь.",
                    "event_id": channel_event,
                    "support": support,
                    "confidence": confidence,
                }
            ]
        return [
            {
                "name": f"{channel_label} channel-pack test",
                "hypothesis": f"If the `{skeleton}` path uses {channel_focus} for {audience}, `{target_kpi}` will improve for traffic from `{channel}`.{profile_clause}",
                "change": f"Launch the channel-specific path: {pack.get('journey')}.{profile_clause}",
                "primary_metric": target_kpi,
                "guardrail": append_profile_list(channel_guardrail, profile_risks),
                "decision_rule": "Keep it only if the primary metric improves, guardrails hold, and channel-pack events are logged without loss.",
                "event_id": channel_event,
                "support": support,
                "confidence": confidence,
            }
        ]
    if ru:
        return [
            {
                "name": "Проверка первого ценностного шага",
                "hypothesis": f"Если путь «{path_label}» даст аудитории «{audience}» конкретный разбор до основного призыва к действию, то метрика «{target_kpi}» вырастет для трафика из «{channel}».{profile_clause}",
                "change": f"Запустить один входной экран или шаг бота с примером диагностики и одним призывом к действию.{profile_clause}",
                "primary_metric": target_kpi,
                "guardrail": append_profile_list("качество лидов, потери событий, время до первого результата", profile_risks),
                "decision_rule": "Оставить только если основная метрика растет, контрольные метрики не ухудшаются, а качественная обратная связь не противоречит результату.",
                "event_id": channel_event,
                "support": support,
                "confidence": confidence,
            }
        ]
    return [
        {
            "name": "First-value step test",
            "hypothesis": f"If the `{skeleton}` path gives {audience} a concrete diagnosis before the main CTA, `{target_kpi}` will improve for traffic from `{channel}`.{profile_clause}",
            "change": f"Launch one entry screen or bot step with a diagnosis preview and one CTA.{profile_clause}",
            "primary_metric": target_kpi,
            "guardrail": append_profile_list("lead quality, event loss, time to first value", profile_risks),
            "decision_rule": "Keep it only if the primary metric improves, guardrails hold, and qualitative feedback does not contradict the result.",
            "event_id": channel_event,
            "support": support,
            "confidence": confidence,
        }
    ]


def build_risk_insights(
    data: dict[str, Any],
    support: str,
    ru: bool,
    competitor_synthesis: dict[str, Any] | None = None,
    channel_synthesis: dict[str, Any] | None = None,
    promise_proof_model: list[dict[str, Any]] | None = None,
    niche_profile: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
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
    for row in promise_proof_model or []:
        if not isinstance(row, dict) or not promise_proof_blocks_ready(str(row.get("evidence_status") or "")):
            continue
        risks.append(
            {
                "risk": "Обещание не покрыто доказательством" if ru else "Promise is not proof-backed",
                "level": ("высокий" if ru else "high") if str(row.get("risk_level") or "") == "high" else ("средний" if ru else "medium"),
                "mitigation": str(row.get("fallback") or ""),
                "support": ", ".join(list_value(row.get("source_ids")) or list_value(row.get("assumption_ids"))) or support,
            }
        )
    pack = primary_channel_pack(channel_synthesis)
    if pack:
        risks.append(
            {
                "risk": str(pack.get("risk") or ("Channel-specific execution risk" if not ru else "Риск исполнения канального маршрута")),
                "level": "средний" if ru else "medium",
                "mitigation": (
                    f"Записать события {', '.join(list_value(pack.get('event_ids')))} и проверять контрольный риск: {pack.get('guardrail')}."
                    if ru
                    else f"Log {', '.join(list_value(pack.get('event_ids')))} and watch guardrail: {pack.get('guardrail')}."
                ),
                "support": support,
            }
        )
    support_loops = channel_synthesis.get("support_loops") if isinstance(channel_synthesis, dict) and isinstance(channel_synthesis.get("support_loops"), list) else []
    if support_loops:
        labels = ", ".join(str(loop.get("label") or loop.get("channel")) for loop in support_loops if isinstance(loop, dict))
        risks.append(
            {
                "risk": "Multi-channel handoff can lose attribution or follow-up context" if not ru else "Передача между каналами может потерять атрибуцию или контекст следующего контакта",
                "level": "средний" if ru else "medium",
                "mitigation": (
                    f"Держать основной путь отдельно от support loops: {labels}."
                    if ru
                    else f"Keep the primary path separate from support loops: {labels}."
                ),
                "support": support,
            }
        )
    if niche_profile_has_match(niche_profile):
        label = str(niche_profile.get("label") or "")
        for risk in list_value(niche_profile.get("risks"))[:2]:
            risks.append(
                {
                    "risk": f"Нишевый риск {label}: {risk}" if ru else f"{label} profile risk: {risk}",
                    "level": "средний" if ru else "medium",
                    "mitigation": (
                        f"Проверить профильные defaults: {'; '.join(list_value(niche_profile.get('funnel_defaults'))[:2])}."
                        if ru
                        else f"Check profile defaults: {'; '.join(list_value(niche_profile.get('funnel_defaults'))[:2])}."
                    ),
                    "support": support,
                }
            )
    weaknesses = competitor_values_phrase(competitor_synthesis, "observed_weaknesses", ru)
    if weaknesses:
        risks.append(
            {
                "risk": "Наблюдаемые слабые места конкурентов могут повториться в запуске" if ru else "Observed competitor weaknesses could repeat in the launch",
                "level": "средний" if ru else "medium",
                "mitigation": (
                    f"Проверить первый экран, онбординг и оффер против наблюдаемых слабых мест ({weaknesses}) до масштабирования."
                    if ru
                    else f"Review the entry screen, onboarding, and offer packaging against observed weaknesses ({weaknesses}) before scaling."
                ),
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
    ru = is_russian(language)
    missing = missing_fields(data["intake"])
    base_ev_gaps = evidence_gaps(data)
    conflicts = contradictions(data)
    completeness = completeness_score(data)
    qualification = qualification_score(data)
    evidence_quality = semantic_evidence_quality(data, conflicts=conflicts)
    research = int(evidence_quality.get("score", 0))
    gate = not missing
    ready = recommendations_are_ready(data, research, base_ev_gaps, conflicts)
    phase = "ready" if ready else "research" if gate else "intake"
    initial_phase = phase
    questions = next_best_input(data)
    insights = compile_insights(data, phase)
    insights["reviewer_approval"] = build_reviewer_approval(data, insights, ru)
    contract_errors = validate_insights_contract(insights, data["sources"])
    evidence_quality = semantic_evidence_quality(data, insights, contract_errors, conflicts)
    research = int(evidence_quality.get("score", 0))
    reviewer_blockers = reviewer_approval_blockers(insights.get("reviewer_approval", {}), ru)
    ev_gaps = dedupe(base_ev_gaps + contract_errors + list_value(evidence_quality.get("blockers")) + reviewer_blockers)
    ready = recommendations_are_ready(data, research, ev_gaps, conflicts)
    phase = "ready" if ready else "research" if gate else "intake"
    if phase != initial_phase:
        insights = compile_insights(data, phase)
        insights["reviewer_approval"] = build_reviewer_approval(data, insights, ru)
        contract_errors = validate_insights_contract(insights, data["sources"])
        evidence_quality = semantic_evidence_quality(data, insights, contract_errors, conflicts)
        research = int(evidence_quality.get("score", 0))
        reviewer_blockers = reviewer_approval_blockers(insights.get("reviewer_approval", {}), ru)
        ev_gaps = dedupe(base_ev_gaps + contract_errors + list_value(evidence_quality.get("blockers")) + reviewer_blockers)
        ready = recommendations_are_ready(data, research, ev_gaps, conflicts)
        phase = "ready" if ready else "research" if gate else "intake"
    insights["evidence_quality"] = evidence_quality
    statuses = artifact_status(data)
    statuses["final"] = "ready" if ready else "draft" if gate else "blocked"

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
            "blocked_recommendations": dedupe(blocked_recommendations(data) + contract_errors),
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
    contract_data = {
        **data,
        "state": state,
        "gaps": gaps,
        "topics": topics,
        "insights": insights,
    }
    orchestration_contract = build_orchestration_contract(workspace, contract_data, summary)
    write_json(runtime_path(workspace, "orchestration_contract.json"), orchestration_contract)
    summary["orchestration_contract_path"] = str(runtime_path(workspace, "orchestration_contract.json"))
    summary["orchestration_contract_errors"] = orchestration_contract.get("validation_errors", [])
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


def orchestration_existing_final_refs(workspace: Path) -> list[str]:
    fd = final_dir(workspace)
    if not fd.exists():
        return []
    refs: list[str] = []
    index = fd / "index.html"
    if index.exists() and not index.is_symlink():
        refs.append("final/index.html")
    for slug, _ in FINAL_PAGES:
        for suffix in [".md", ".html"]:
            path = fd / f"{slug}{suffix}"
            if path.exists() and not path.is_symlink():
                refs.append(f"final/{path.name}")
    return refs


def orchestration_existing_export_refs(workspace: Path) -> list[str]:
    directory = exports_dir(workspace)
    if not directory.exists() or directory.is_symlink():
        return []
    refs: list[str] = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and not path.is_symlink() and path.suffix in {".json", ".csv"}:
            refs.append(f"exports/{path.name}")
    return refs


def orchestration_role_refs(role: str, workspace: Path) -> dict[str, list[str]]:
    base_context = ["runtime/run_state.json", "runtime/gaps.json", "runtime/topics.json"]
    mapping = {
        "intake": {
            "input_refs": ["runtime/intake.json"],
            "context_refs": ["runtime/run_state.json"],
            "output_refs": ["runtime/intake.json", "runtime/run_state.json", "runtime/gaps.json"],
        },
        "planner": {
            "input_refs": ["runtime/intake.json", "runtime/gaps.json"],
            "context_refs": ["runtime/run_state.json"],
            "output_refs": ["runtime/topics.json", "runtime/agent_tasks.json"],
        },
        "research": {
            "input_refs": ["runtime/intake.json", "runtime/gaps.json"],
            "context_refs": base_context,
            "output_refs": ["runtime/agent_results.jsonl", "runtime/sources.jsonl", "runtime/insights.json#evidence_claims"],
        },
        "competitor": {
            "input_refs": ["runtime/intake.json", "runtime/sources.jsonl"],
            "context_refs": base_context,
            "output_refs": ["runtime/competitors.csv", "runtime/sources.jsonl", "runtime/insights.json#competitor_synthesis"],
        },
        "synthesis": {
            "input_refs": ["runtime/intake.json", "runtime/sources.jsonl", "runtime/competitors.csv", "runtime/agent_results.jsonl"],
            "context_refs": base_context,
            "output_refs": ["runtime/insights.json"],
        },
        "compiler_reviewer": {
            "input_refs": ["runtime/insights.json", "runtime/gaps.json"],
            "context_refs": ["runtime/run_state.json", "runtime/orchestration_contract.json"],
            "output_refs": ["runtime/orchestration_contract.json"] + orchestration_existing_final_refs(workspace) + orchestration_existing_export_refs(workspace),
        },
    }
    return mapping.get(
        role,
        {
            "input_refs": ["runtime/intake.json"],
            "context_refs": base_context,
            "output_refs": ["runtime/agent_results.jsonl"],
        },
    )


def contract_ids_from_rows(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    ids = {"claim_ids": [], "source_ids": [], "assumption_ids": []}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ids["claim_ids"].extend(list_value(row.get("claim_ids")))
        ids["source_ids"].extend(list_value(row.get("source_ids")))
        ids["assumption_ids"].extend(list_value(row.get("assumption_ids")))
    return {key: dedupe(value) for key, value in ids.items()}


def orchestration_result_source_ids(result: dict[str, Any], sources: list[dict[str, Any]]) -> list[str]:
    ids = list_value(result.get("source_ids"))
    url_to_id = {url_signature(source.get("url")): source_id(source) for source in sources if source_id(source) and url_signature(source.get("url"))}
    title_to_id = {
        re.sub(r"\s+", " ", str(source.get("title") or "").strip().lower()): source_id(source)
        for source in sources
        if source_id(source) and present(source.get("title"))
    }
    for citation in result.get("citations", []) if isinstance(result.get("citations"), list) else []:
        if isinstance(citation, str):
            url_key = url_signature(citation)
            title_key = re.sub(r"\s+", " ", citation.strip().lower())
        elif isinstance(citation, dict):
            url_key = url_signature(citation.get("url"))
            title_key = re.sub(r"\s+", " ", str(citation.get("title") or "").strip().lower())
        else:
            continue
        if url_key and url_key in url_to_id:
            ids.append(url_to_id[url_key])
        elif title_key and title_key in title_to_id:
            ids.append(title_to_id[title_key])
    return dedupe(ids)


def orchestration_role_ids(role: str, data: dict[str, Any]) -> dict[str, list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    evidence_claims = insights.get("evidence_claims") if isinstance(insights.get("evidence_claims"), list) else []
    assumptions = insights.get("assumptions") if isinstance(insights.get("assumptions"), list) else []
    sources = data.get("sources") if isinstance(data.get("sources"), list) else []
    if role == "research":
        return {
            "claim_ids": first_ids(evidence_claims, "claim_id", 20),
            "source_ids": [source_id(row) for row in sources if source_id(row)],
            "assumption_ids": first_ids(assumptions, "id", 20),
        }
    if role == "competitor":
        competitor_synthesis = insights.get("competitor_synthesis") if isinstance(insights.get("competitor_synthesis"), dict) else {}
        competitor_claims = [
            claim
            for claim in evidence_claims
            if str(claim.get("claim_type") or "").strip().lower() in {"competitor", "pricing", "proof", "current_practice"}
        ]
        source_ids = list_value(competitor_synthesis.get("source_ids"))
        for row in data.get("competitors", []) if isinstance(data.get("competitors"), list) else []:
            source_ids.extend(competitor_source_ids(row, sources))
        return {
            "claim_ids": first_ids(competitor_claims, "claim_id", 20),
            "source_ids": dedupe(source_ids),
            "assumption_ids": first_ids(assumptions, "id", 20) if not source_ids else [],
        }
    if role == "synthesis":
        rows = recommendation_rows(insights)
        current_diff = insights.get("current_funnel_diff") if isinstance(insights.get("current_funnel_diff"), dict) else {}
        if isinstance(current_diff.get("rows"), list):
            rows.extend(row for row in current_diff["rows"] if isinstance(row, dict))
        if isinstance(insights.get("variant_bundles"), list):
            rows.extend(row for row in insights["variant_bundles"] if isinstance(row, dict))
        if isinstance(insights.get("promise_proof_model"), list):
            rows.extend(row for row in insights["promise_proof_model"] if isinstance(row, dict))
        return contract_ids_from_rows(rows)
    if role == "compiler_reviewer":
        approval = insights.get("reviewer_approval") if isinstance(insights.get("reviewer_approval"), dict) else {}
        rows = approval.get("review_items") if isinstance(approval.get("review_items"), list) else []
        ids = contract_ids_from_rows(rows)
        if not any(ids.values()):
            ids = contract_ids_from_rows(recommendation_rows(insights))
        return ids
    return {"claim_ids": [], "source_ids": [], "assumption_ids": []}


def orchestration_results_for_task(task: dict[str, Any], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    task_id = str(task.get("task_id") or "").strip()
    role = str(task.get("role") or "").strip()
    topic_id = str(task.get("topic_id") or "").strip()
    matches = []
    for result in results:
        if not isinstance(result, dict):
            continue
        if task_id and str(result.get("task_id") or "").strip() == task_id:
            matches.append(result)
        elif role and topic_id and str(result.get("role") or "").strip() == role and str(result.get("topic_id") or "").strip() == topic_id:
            matches.append(result)
    return matches


def orchestration_orphan_result_tasks(tasks: list[dict[str, Any]], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    known_task_ids = {str(task.get("task_id") or "").strip() for task in tasks}
    known_role_topics = {(str(task.get("role") or "").strip(), str(task.get("topic_id") or "").strip()) for task in tasks}
    synthetic: list[dict[str, Any]] = []
    for result in results:
        task_id = str(result.get("task_id") or "").strip()
        role = str(result.get("role") or "").strip()
        topic_id = str(result.get("topic_id") or "").strip()
        if (task_id and task_id in known_task_ids) or (role, topic_id) in known_role_topics:
            continue
        synthetic.append(
            {
                "task_id": task_id or f"{role or 'specialist'}-{len(synthetic) + 1}",
                "role": role or "specialist",
                "topic_id": topic_id or "runtime",
                "status": str(result.get("status") or "completed"),
                "objective": str(result.get("objective") or result.get("next_action") or result.get("summary") or "Record specialist output."),
                "summary": str(result.get("summary") or ""),
                "created_at": str(result.get("recorded_at") or ""),
                "updated_at": str(result.get("recorded_at") or ""),
            }
        )
    return synthetic


def orchestration_blocked_reason(
    task: dict[str, Any],
    result_rows: list[dict[str, Any]],
    data: dict[str, Any],
    summary: dict[str, Any] | None = None,
) -> str:
    reasons: list[str] = []
    for result in result_rows:
        reasons.extend(list_value(result.get("blocked_reason")))
    reasons.extend(list_value(task.get("blocked_reason")))
    role = str(task.get("role") or "").strip()
    state = data.get("state") if isinstance(data.get("state"), dict) else {}
    phase = str((summary or {}).get("phase") or state.get("phase") or "")
    if role == "research":
        reasons.extend(list_value(state.get("evidence_gaps"))[:6])
    elif role == "competitor" and len(data.get("competitors", [])) < READY_MIN_COMPETITORS:
        reasons.append(f"needs at least {READY_MIN_COMPETITORS} sourced competitor rows")
    elif role in {"synthesis", "compiler_reviewer"} and phase != "ready":
        missing = list_value(state.get("critical_missing_fields"))
        gaps = list_value(state.get("evidence_gaps"))
        if missing:
            reasons.append("missing_fields: " + ", ".join(missing))
        if gaps:
            reasons.append("evidence_gaps: " + "; ".join(gaps[:6]))
    return "; ".join(dedupe([reason for reason in reasons if present(reason)])[:8])


def orchestration_task_status(
    task: dict[str, Any],
    result_rows: list[dict[str, Any]],
    data: dict[str, Any],
    blocked_reason: str,
    summary: dict[str, Any] | None = None,
) -> str:
    for result in reversed(result_rows):
        status = str(result.get("status") or "").strip()
        if status in ORCHESTRATION_TASK_STATUSES:
            return status
    status = str(task.get("status") or "").strip()
    if status in ORCHESTRATION_TASK_STATUSES and status not in {"pending", "completed"}:
        return status
    phase = str((summary or {}).get("phase") or data.get("state", {}).get("phase") or "")
    role = str(task.get("role") or "").strip()
    if blocked_reason and phase == "intake":
        return "blocked"
    if blocked_reason and phase == "research":
        return "research_only"
    if status == "completed" or result_rows:
        return "completed"
    if phase == "ready" and role in {"research", "competitor", "synthesis", "compiler_reviewer"}:
        return "ready"
    return status if status in ORCHESTRATION_TASK_STATUSES else "pending"


def build_orchestration_contract(
    workspace: Path,
    data: dict[str, Any],
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = data.get("state") if isinstance(data.get("state"), dict) else {}
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    sources = data.get("sources") if isinstance(data.get("sources"), list) else []
    results = data.get("agent_results") if isinstance(data.get("agent_results"), list) else []
    base_tasks = data.get("tasks") if isinstance(data.get("tasks"), list) else []
    tasks = [task for task in base_tasks if isinstance(task, dict)]
    tasks.extend(orchestration_orphan_result_tasks(tasks, results))
    objectives = default_task_objectives()
    generated_at = utc_now()
    task_contracts: list[dict[str, Any]] = []
    for task in tasks:
        role = str(task.get("role") or "specialist").strip()
        result_rows = orchestration_results_for_task(task, results)
        refs = orchestration_role_refs(role, workspace)
        result_input_refs = [ref for result in result_rows for ref in list_value(result.get("input_refs"))]
        result_context_refs = [ref for result in result_rows for ref in list_value(result.get("context_refs"))]
        result_output_refs = [ref for result in result_rows for ref in list_value(result.get("output_refs"))]
        result_artifact_refs = [ref for result in result_rows for ref in list_value(result.get("artifact_refs"))]
        role_ids = orchestration_role_ids(role, data)
        claim_ids = dedupe([claim_id for result in result_rows for claim_id in list_value(result.get("claim_ids"))] or role_ids["claim_ids"])
        source_ids = dedupe([source_id_value for result in result_rows for source_id_value in orchestration_result_source_ids(result, sources)] or role_ids["source_ids"])
        assumption_ids = dedupe([assumption_id for result in result_rows for assumption_id in list_value(result.get("assumption_ids"))] or role_ids["assumption_ids"])
        blocked_reason = orchestration_blocked_reason(task, result_rows, data, summary)
        updated_candidates = [str(task.get("updated_at") or ""), str(state.get("updated_at") or "")]
        updated_candidates.extend(str(result.get("recorded_at") or "") for result in result_rows)
        contract = {
            "task_id": str(task.get("task_id") or "").strip(),
            "role": role,
            "specialist": str(task.get("specialist") or role).strip(),
            "topic_id": str(task.get("topic_id") or "").strip(),
            "objective": str(task.get("objective") or objectives.get(role) or task.get("summary") or "Complete specialist task.").strip(),
            "input_refs": dedupe(refs["input_refs"] + result_input_refs),
            "context_refs": dedupe(refs["context_refs"] + result_context_refs),
            "output_refs": dedupe(refs["output_refs"] + result_output_refs),
            "artifact_refs": dedupe(refs["output_refs"] + result_output_refs + result_artifact_refs),
            "result_refs": [
                {
                    "file": "runtime/agent_results.jsonl",
                    "task_id": str(result.get("task_id") or ""),
                    "recorded_at": str(result.get("recorded_at") or ""),
                }
                for result in result_rows
            ],
            "claim_ids": claim_ids,
            "source_ids": source_ids,
            "assumption_ids": assumption_ids,
            "blocked_reason": blocked_reason,
            "status": orchestration_task_status(task, result_rows, data, blocked_reason, summary),
            "created_at": str(task.get("created_at") or state.get("created_at") or generated_at),
            "updated_at": next((value for value in reversed(updated_candidates) if present(value)), generated_at),
        }
        task_contracts.append(contract)

    evidence_claims = insights.get("evidence_claims") if isinstance(insights.get("evidence_claims"), list) else []
    assumptions = insights.get("assumptions") if isinstance(insights.get("assumptions"), list) else []
    contract = {
        "contract_type": "orchestration_task_results",
        "version": VERSION,
        "workspace": str(workspace),
        "generated_at": generated_at,
        "phase": (summary or {}).get("phase") or state.get("phase") or "intake",
        "status": "ready" if ((summary or {}).get("phase") or state.get("phase")) == "ready" else "draft",
        "output_language": output_language(data),
        "runtime_refs": {
            "tasks": "runtime/agent_tasks.json",
            "results": "runtime/agent_results.jsonl",
            "insights": "runtime/insights.json",
            "sources": "runtime/sources.jsonl",
            "gaps": "runtime/gaps.json",
        },
        "export_refs": orchestration_existing_export_refs(workspace),
        "final_refs": orchestration_existing_final_refs(workspace),
        "claim_ids": first_ids(evidence_claims, "claim_id", 100),
        "source_ids": [source_id(row) for row in sources if source_id(row)],
        "assumption_ids": first_ids(assumptions, "id", 100),
        "tasks": task_contracts,
        "validation_errors": [],
    }
    contract["validation_errors"] = validate_orchestration_contract(contract, insights, sources)
    return contract


def validate_orchestration_contract(
    contract: dict[str, Any],
    insights: dict[str, Any] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["orchestration contract error: contract must be an object"]
    if contract.get("contract_type") != "orchestration_task_results":
        errors.append("orchestration contract error: contract_type must be orchestration_task_results")
    tasks = contract.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("orchestration contract error: tasks must be a non-empty list")
        tasks = []
    insights = insights if isinstance(insights, dict) else {}
    evidence_claims = insights.get("evidence_claims") if isinstance(insights.get("evidence_claims"), list) else []
    assumptions = insights.get("assumptions") if isinstance(insights.get("assumptions"), list) else []
    evidence_refs = insights.get("evidence_refs") if isinstance(insights.get("evidence_refs"), list) else []
    allowed_claim_ids = {str(row.get("claim_id") or "") for row in evidence_claims if present(row.get("claim_id"))}
    allowed_assumption_ids = {str(row.get("id") or "") for row in assumptions if present(row.get("id"))}
    source_rows = sources if isinstance(sources, list) else []
    allowed_source_ids = {str(row.get("source_id") or "") for row in source_rows if present(row.get("source_id"))}
    allowed_source_ids |= {str(row.get("id") or row.get("source_id") or "") for row in evidence_refs if present(row.get("id") or row.get("source_id"))}
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            errors.append(f"orchestration contract error: tasks[{index}] must be an object")
            continue
        label = str(task.get("task_id") or f"tasks[{index}]")
        for field in ORCHESTRATION_TASK_CONTRACT_FIELDS:
            if field not in task or (field not in {"blocked_reason", "claim_ids", "source_ids", "assumption_ids"} and not present(task.get(field))):
                errors.append(f"orchestration contract error: task {label} missing {field}")
        status = str(task.get("status") or "").strip()
        if status and status not in ORCHESTRATION_TASK_STATUSES:
            errors.append(f"orchestration contract error: task {label} has invalid status {status}")
        for field in ["input_refs", "context_refs", "output_refs", "artifact_refs", "claim_ids", "source_ids", "assumption_ids"]:
            if not isinstance(task.get(field), list):
                errors.append(f"orchestration contract error: task {label} {field} must be a list")
        for claim_id in list_value(task.get("claim_ids")):
            if allowed_claim_ids and claim_id not in allowed_claim_ids:
                errors.append(f"orchestration contract error: task {label} references unknown claim_id {claim_id}")
        for source_id_value in list_value(task.get("source_ids")):
            if allowed_source_ids and source_id_value not in allowed_source_ids:
                errors.append(f"orchestration contract error: task {label} references unknown source_id {source_id_value}")
        for assumption_id in list_value(task.get("assumption_ids")):
            if allowed_assumption_ids and assumption_id not in allowed_assumption_ids:
                errors.append(f"orchestration contract error: task {label} references unknown assumption_id {assumption_id}")
    return dedupe(errors)


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def csv_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if present(item))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value or "")


def global_export_blocked_reason(summary: dict[str, Any]) -> str:
    if summary.get("recommendations_ready") and summary.get("phase") == "ready":
        return ""
    reasons: list[str] = []
    missing = list_value(summary.get("critical_missing_fields"))
    if missing:
        reasons.append("missing_fields: " + ", ".join(missing))
    gaps = list_value(summary.get("evidence_gaps"))
    if gaps:
        reasons.append("evidence_gaps: " + "; ".join(gaps[:6]))
    conflicts = list_value(summary.get("contradictions"))
    if conflicts:
        reasons.append("contradictions: " + "; ".join(conflicts))
    if not reasons:
        reasons.append(f"phase is {summary.get('phase') or 'unknown'}; recommendations are not ready")
    return "; ".join(reasons)


def export_contract_fields(
    row: dict[str, Any],
    summary: dict[str, Any],
    fallback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fallback = fallback or {}
    global_blocker = global_export_blocked_reason(summary)
    blocked_reason = append_blocked_reason(row.get("blocked_reason") or fallback.get("blocked_reason"), global_blocker)
    source_ids = list_value(row.get("source_ids")) or list_value(fallback.get("source_ids"))
    ready = bool(summary.get("recommendations_ready") and summary.get("phase") == "ready" and source_ids and not blocked_reason)
    return {
        "claim_ids": list_value(row.get("claim_ids")) or list_value(fallback.get("claim_ids")),
        "source_ids": source_ids,
        "assumption_ids": list_value(row.get("assumption_ids")) or list_value(fallback.get("assumption_ids")),
        "blocked_reason": blocked_reason,
        "ready": ready,
    }


def first_contract_row(rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    for row in rows:
        if list_value(row.get("claim_ids")) or list_value(row.get("source_ids")) or list_value(row.get("assumption_ids")):
            return export_contract_fields(row, summary)
    return {
        "claim_ids": [],
        "source_ids": [],
        "assumption_ids": [],
        "blocked_reason": global_export_blocked_reason(summary),
        "ready": False,
    }


def base_export_payload(
    export_type: str,
    workspace: Path,
    data: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "export_type": export_type,
        "version": VERSION,
        "workspace": str(workspace),
        "generated_at": utc_now(),
        "phase": summary.get("phase"),
        "ready_for_launch": bool(summary.get("recommendations_ready") and summary.get("phase") == "ready"),
        "blocked_reason": global_export_blocked_reason(summary),
        "output_language": output_language(data),
    }


def action_plan_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    rows = recommendation_rows(insights)
    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        contract = export_contract_fields(row, summary)
        item = {
            "id": str(row.get("id") or f"action-{index}"),
            "type": str(row.get("type") or "recommendation"),
            "stage": str(row.get("funnel_stage") or row.get("stage") or row.get("name") or ""),
            "title": str(row.get("name") or row.get("stage") or row.get("type") or ""),
            "owner_action": str(row.get("owner_action") or row.get("change") or row.get("content") or ""),
            "measurement_event": str(row.get("measurement_event") or row.get("event_id") or row.get("metric") or row.get("primary_metric") or ""),
            **contract,
        }
        items.append(item)
    payload = base_export_payload("action_plan", workspace, data, summary)
    payload["items"] = items
    headers = ["id", "type", "stage", "title", "owner_action", "measurement_event", "ready", "blocked_reason", "claim_ids", "source_ids", "assumption_ids"]
    return payload, [{key: csv_value(item.get(key)) for key in headers} for item in items], headers


def event_schema_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    screens = insights.get("screens") if isinstance(insights.get("screens"), list) else []
    experiments = insights.get("experiments") if isinstance(insights.get("experiments"), list) else []
    fallback = first_contract_row(recommendation_rows(insights), summary)
    events: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_event(event: dict[str, Any]) -> None:
        event_id = str(event.get("event_id") or "").strip()
        source_type = str(event.get("source_type") or "").strip()
        signature = f"{source_type}:{event_id}:{event.get('source_id') or ''}"
        if not event_id or signature in seen:
            return
        seen.add(signature)
        events.append(event)

    for row in screens:
        if not isinstance(row, dict):
            continue
        contract = export_contract_fields(row, summary)
        event_id = str(row.get("event_id") or event_id_from_text(row.get("measurement_event") or row.get("metric") or row.get("stage"), "FunnelStepRecorded"))
        add_event(
            {
                "event_id": event_id,
                "source_type": "screen",
                "source_id": str(row.get("id") or ""),
                "stage": str(row.get("stage") or row.get("funnel_stage") or ""),
                "description": str(row.get("measurement_event") or row.get("metric") or row.get("target_belief") or ""),
                "required_properties": ["channel", "source", "session_id", "user_id", "timestamp", "segment"],
                **contract,
            }
        )
    for row in experiments:
        if not isinstance(row, dict):
            continue
        contract = export_contract_fields(row, summary)
        event_id = str(row.get("event_id") or event_id_from_text(row.get("measurement_event") or row.get("primary_metric"), "ExperimentDecisionRecorded"))
        add_event(
            {
                "event_id": event_id,
                "source_type": "experiment",
                "source_id": str(row.get("id") or ""),
                "stage": str(row.get("name") or "experiment"),
                "description": str(row.get("event_instrumentation") or row.get("hypothesis") or ""),
                "required_properties": ["experiment_id", "variant_id", "channel", "source", "session_id", "user_id", "timestamp", "segment"],
                **contract,
            }
        )
    channel_synthesis = insights.get("channel_synthesis") if isinstance(insights.get("channel_synthesis"), dict) else {}
    packs = channel_synthesis.get("packs") if isinstance(channel_synthesis.get("packs"), list) else []
    support_loops = channel_synthesis.get("support_loops") if isinstance(channel_synthesis.get("support_loops"), list) else []
    for role, pack_rows in [("primary_channel_pack", packs[:1]), ("support_loop", support_loops)]:
        for pack in pack_rows:
            if not isinstance(pack, dict):
                continue
            for event_id in list_value(pack.get("event_ids")):
                add_event(
                    {
                        "event_id": event_id,
                        "source_type": role,
                        "source_id": str(pack.get("channel") or ""),
                        "stage": str(pack.get("label") or pack.get("channel") or ""),
                        "description": str(pack.get("journey") or pack.get("support_loop") or pack.get("risk") or ""),
                        "required_properties": ["channel", "source", "session_id", "user_id", "timestamp", "segment"],
                        **fallback,
                    }
                )
    niche_profile = insights.get("niche_profile") if isinstance(insights.get("niche_profile"), dict) else {}
    if niche_profile_has_match(niche_profile):
        defaults = list_value(niche_profile.get("funnel_defaults"))
        for index, event_id in enumerate(list_value(niche_profile.get("event_suggestions"))):
            add_event(
                {
                    "event_id": event_id,
                    "source_type": "niche_profile",
                    "source_id": str(niche_profile.get("profile_key") or ""),
                    "stage": str(niche_profile.get("label") or ""),
                    "description": defaults[index] if index < len(defaults) else str(niche_profile.get("summary_text") or ""),
                    "required_properties": ["channel", "source", "session_id", "user_id", "timestamp", "segment"],
                    **fallback,
                }
            )
    payload = base_export_payload("event_schema", workspace, data, summary)
    payload["events"] = events
    headers = ["event_id", "source_type", "source_id", "stage", "description", "required_properties", "ready", "blocked_reason", "claim_ids", "source_ids", "assumption_ids"]
    return payload, [{key: csv_value(event.get(key)) for key in headers} for event in events], headers


def content_brief_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    screens = insights.get("screens") if isinstance(insights.get("screens"), list) else []
    briefs: list[dict[str, Any]] = []
    for index, row in enumerate(screens, start=1):
        if not isinstance(row, dict):
            continue
        briefs.append(
            {
                "brief_id": str(row.get("id") or f"content-{index}"),
                "stage": str(row.get("stage") or row.get("funnel_stage") or ""),
                "target_belief": str(row.get("target_belief") or ""),
                "content": str(row.get("content") or ""),
                "cta": str(row.get("cta") or ""),
                "proof_needed": str(row.get("proof_needed") or ""),
                "channel_pack": str(row.get("channel_pack") or ""),
                **export_contract_fields(row, summary),
            }
        )
    payload = base_export_payload("content_brief", workspace, data, summary)
    payload["briefs"] = briefs
    headers = ["brief_id", "stage", "target_belief", "content", "cta", "proof_needed", "channel_pack", "ready", "blocked_reason", "claim_ids", "source_ids", "assumption_ids"]
    return payload, [{key: csv_value(brief.get(key)) for key in headers} for brief in briefs], headers


def crm_handoff_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    screens = [row for row in insights.get("screens", []) if isinstance(row, dict)] if isinstance(insights.get("screens"), list) else []
    intake = data.get("intake", {})
    conversion_rows = [
        row for row in screens if "conversion" in str(row.get("stage") or row.get("funnel_stage") or "").lower() or "конверс" in str(row.get("stage") or row.get("funnel_stage") or "").lower()
    ] or (screens[-1:] if screens else [])
    handoffs: list[dict[str, Any]] = []
    for index, row in enumerate(conversion_rows, start=1):
        event_id = str(row.get("event_id") or event_id_from_text(row.get("measurement_event") or row.get("metric"), "QualifiedLeadRecorded"))
        handoffs.append(
            {
                "handoff_id": str(row.get("id") or f"crm-handoff-{index}"),
                "trigger_event": event_id,
                "target_segment": str(row.get("target_segment") or intake.get("icp") or intake.get("primary_persona") or ""),
                "primary_channel": str(intake.get("primary_channel") or ""),
                "owner_action": str(row.get("owner_action") or row.get("cta") or ""),
                "crm_fields": ["lead_id", "person_id", "channel", "source", "campaign_id", "segment", "last_event_id", "proof_state", "owner"],
                "handoff_note": "Prepared for CRM import or manual handoff only; this export does not write to external systems.",
                **export_contract_fields(row, summary),
            }
        )
    payload = base_export_payload("crm_handoff", workspace, data, summary)
    payload["handoffs"] = handoffs
    headers = ["handoff_id", "trigger_event", "target_segment", "primary_channel", "owner_action", "crm_fields", "handoff_note", "ready", "blocked_reason", "claim_ids", "source_ids", "assumption_ids"]
    return payload, [{key: csv_value(handoff.get(key)) for key in headers} for handoff in handoffs], headers


def funnel_diff_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    current_diff = insights.get("current_funnel_diff") if isinstance(insights.get("current_funnel_diff"), dict) else {}
    rows = current_diff.get("rows") if isinstance(current_diff.get("rows"), list) else []
    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "diff_id": str(row.get("id") or f"funnel-diff-{index}"),
                "current_step": str(row.get("current_step") or ""),
                "proposed_stage": str(row.get("proposed_stage") or ""),
                "proposed_step": str(row.get("proposed_step") or ""),
                "change_type": str(row.get("change_type") or ""),
                "reason": str(row.get("reason") or ""),
                "measurement_event": str(row.get("measurement_event") or ""),
                **export_contract_fields(row, summary),
            }
        )
    payload = base_export_payload("funnel_diff", workspace, data, summary)
    payload["status"] = str(current_diff.get("status") or "")
    payload["raw_current_steps"] = list_value(current_diff.get("raw_current_steps"))
    payload["diffs"] = items
    headers = ["diff_id", "current_step", "proposed_stage", "proposed_step", "change_type", "reason", "measurement_event", "ready", "blocked_reason", "claim_ids", "source_ids", "assumption_ids"]
    return payload, [{key: csv_value(item.get(key)) for key in headers} for item in items], headers


def variant_bundles_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    rows = insights.get("variant_bundles") if isinstance(insights.get("variant_bundles"), list) else []
    variants: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        variants.append(
            {
                "variant_id": str(row.get("variant_id") or f"variant-{index}"),
                "stage": str(row.get("stage") or ""),
                "funnel_stage": str(row.get("funnel_stage") or ""),
                "target_segment": str(row.get("target_segment") or ""),
                "variant_type": str(row.get("variant_type") or ""),
                "current_step": str(row.get("current_step") or ""),
                "control_reference": str(row.get("control_reference") or ""),
                "variant_copy": str(row.get("variant_copy") or ""),
                "variant_action": str(row.get("variant_action") or ""),
                "hypothesis": str(row.get("hypothesis") or ""),
                "proof_requirement": str(row.get("proof_requirement") or ""),
                "measurement_event": str(row.get("measurement_event") or ""),
                "guardrail": str(row.get("guardrail") or ""),
                **export_contract_fields(row, summary),
            }
        )
    payload = base_export_payload("variant_bundles", workspace, data, summary)
    payload["variants"] = variants
    headers = [
        "variant_id",
        "stage",
        "funnel_stage",
        "target_segment",
        "variant_type",
        "current_step",
        "control_reference",
        "variant_copy",
        "variant_action",
        "hypothesis",
        "proof_requirement",
        "measurement_event",
        "guardrail",
        "ready",
        "blocked_reason",
        "claim_ids",
        "source_ids",
        "assumption_ids",
    ]
    return payload, [{key: csv_value(variant.get(key)) for key in headers} for variant in variants], headers


def reviewer_approval_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    approval = insights.get("reviewer_approval") if isinstance(insights.get("reviewer_approval"), dict) else {}
    rows = approval.get("review_items") if isinstance(approval.get("review_items"), list) else []
    fallback = {
        "claim_ids": [],
        "source_ids": [],
        "assumption_ids": [],
        "blocked_reason": str(approval.get("blocked_reason") or ""),
    }
    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "review_id": str(row.get("review_id") or f"review-{index}"),
                "review_type": str(row.get("review_type") or ""),
                "target_id": str(row.get("target_id") or ""),
                "target_type": str(row.get("target_type") or ""),
                "risk_level": str(row.get("risk_level") or ""),
                "reason": str(row.get("reason") or ""),
                **export_contract_fields(row, summary, fallback),
            }
        )
    payload = base_export_payload("reviewer_approval", workspace, data, summary)
    payload.update(
        {
            "status": str(approval.get("status") or "not_required"),
            "required": bool(approval.get("required")),
            "approved": bool(approval.get("approved")),
            "approved_by": str(approval.get("approved_by") or ""),
            "approved_at": str(approval.get("approved_at") or ""),
            "approval_source": str(approval.get("approval_source") or ""),
            "review_items": items,
        }
    )
    headers = ["review_id", "review_type", "target_id", "target_type", "risk_level", "reason", "ready", "blocked_reason", "claim_ids", "source_ids", "assumption_ids"]
    return payload, [{key: csv_value(item.get(key)) for key in headers} for item in items], headers


def orchestration_contract_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    contract = build_orchestration_contract(workspace, data, summary)
    payload = base_export_payload("orchestration_contract", workspace, data, summary)
    payload.update(
        {
            "contract_type": contract.get("contract_type"),
            "runtime_refs": contract.get("runtime_refs", {}),
            "export_refs": contract.get("export_refs", []),
            "final_refs": contract.get("final_refs", []),
            "claim_ids": contract.get("claim_ids", []),
            "source_ids": contract.get("source_ids", []),
            "assumption_ids": contract.get("assumption_ids", []),
            "tasks": contract.get("tasks", []),
            "validation_errors": contract.get("validation_errors", []),
        }
    )
    headers = [
        "task_id",
        "role",
        "specialist",
        "objective",
        "status",
        "blocked_reason",
        "input_refs",
        "context_refs",
        "output_refs",
        "artifact_refs",
        "claim_ids",
        "source_ids",
        "assumption_ids",
        "created_at",
        "updated_at",
    ]
    rows = [{key: csv_value(task.get(key)) for key in headers} for task in payload["tasks"] if isinstance(task, dict)]
    return payload, rows, headers


def experiment_card_export(workspace: Path, data: dict[str, Any], summary: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    insights = data.get("insights") if isinstance(data.get("insights"), dict) else {}
    experiments = insights.get("experiments") if isinstance(insights.get("experiments"), list) else []
    cards: list[dict[str, Any]] = []
    for index, row in enumerate(experiments, start=1):
        if not isinstance(row, dict):
            continue
        cards.append(
            {
                "experiment_id": str(row.get("id") or f"experiment-{index}"),
                "name": str(row.get("name") or ""),
                "hypothesis": str(row.get("hypothesis") or ""),
                "target_segment": str(row.get("target_segment") or ""),
                "primary_metric": str(row.get("primary_metric") or ""),
                "event_id": str(row.get("event_id") or ""),
                "guardrail_metrics": str(row.get("guardrail_metrics") or ""),
                "exposure_definition": str(row.get("exposure_definition") or ""),
                "event_instrumentation": str(row.get("event_instrumentation") or ""),
                "srm_check": str(row.get("srm_check") or ""),
                "event_loss_threshold": str(row.get("event_loss_threshold") or ""),
                "expected_effect_range": str(row.get("expected_effect_range") or ""),
                "stop_rule": str(row.get("stop_rule") or ""),
                "ship_rule": str(row.get("ship_rule") or ""),
                "iterate_rule": str(row.get("iterate_rule") or ""),
                "failure_mode": str(row.get("failure_mode") or ""),
                **export_contract_fields(row, summary),
            }
        )
    payload = base_export_payload("experiment_card", workspace, data, summary)
    payload["experiments"] = cards
    headers = [
        "experiment_id",
        "name",
        "hypothesis",
        "target_segment",
        "primary_metric",
        "event_id",
        "guardrail_metrics",
        "exposure_definition",
        "event_instrumentation",
        "srm_check",
        "event_loss_threshold",
        "expected_effect_range",
        "stop_rule",
        "ship_rule",
        "iterate_rule",
        "failure_mode",
        "ready",
        "blocked_reason",
        "claim_ids",
        "source_ids",
        "assumption_ids",
    ]
    return payload, [{key: csv_value(card.get(key)) for key in headers} for card in cards], headers


def write_launch_export(
    workspace: Path,
    stem: str,
    payload: dict[str, Any],
    csv_rows: list[dict[str, str]],
    csv_headers: list[str],
) -> dict[str, Any]:
    json_file = export_path(workspace, f"{stem}.json")
    csv_file = export_path(workspace, f"{stem}.csv")
    write_json(json_file, payload)
    write_csv(csv_file, csv_headers, csv_rows)
    return {
        "json": str(json_file),
        "csv": str(csv_file),
        "rows": len(csv_rows),
    }


def export_launch_package(workspace: Path) -> dict[str, Any]:
    ensure_workspace(workspace)
    summary = validate_and_write(workspace)
    data = load_workspace(workspace)
    directory = ensure_exports_dir(workspace)

    builders = {
        "action_plan": action_plan_export,
        "event_schema": event_schema_export,
        "content_brief": content_brief_export,
        "crm_handoff": crm_handoff_export,
        "funnel_diff": funnel_diff_export,
        "variant_bundles": variant_bundles_export,
        "reviewer_approval": reviewer_approval_export,
        "orchestration_contract": orchestration_contract_export,
        "experiment_card": experiment_card_export,
    }
    exports: dict[str, Any] = {}
    for stem, builder in builders.items():
        payload, csv_rows, csv_headers = builder(workspace, data, summary)
        exports[stem] = write_launch_export(workspace, stem, payload, csv_rows, csv_headers)

    manifest = {
        "version": VERSION,
        "workspace": str(workspace),
        "generated_at": utc_now(),
        "phase": summary.get("phase"),
        "ready_for_launch": bool(summary.get("recommendations_ready") and summary.get("phase") == "ready"),
        "blocked_reason": global_export_blocked_reason(summary),
        "exports": exports,
    }
    write_json(export_path(workspace, "manifest.json"), manifest)
    refreshed_data = load_workspace(workspace)
    orchestration_contract = build_orchestration_contract(workspace, refreshed_data, summary)
    write_json(runtime_path(workspace, "orchestration_contract.json"), orchestration_contract)
    return {
        "exported": True,
        "exports_dir": str(directory),
        "ready_for_launch": manifest["ready_for_launch"],
        "blocked_reason": manifest["blocked_reason"],
        "files": exports | {"manifest": {"json": str(export_path(workspace, "manifest.json")), "rows": len(exports)}},
        "summary": summary,
    }


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
        elif key == "current_funnel":
            existing_steps = intake.get("current_funnel") if isinstance(intake.get("current_funnel"), list) else list_value(intake.get("current_funnel"))
            for item in value if isinstance(value, list) else [value]:
                text = compact_fragment(item, 180)
                if present(text) and text not in existing_steps:
                    existing_steps.append(text)
                    changed.append(key)
            intake["current_funnel"] = existing_steps
        elif key == "reviewer_approval":
            text = compact_fragment(value, 300)
            if present(text) and intake.get(key) != text:
                intake[key] = text
                changed.append(key)
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
