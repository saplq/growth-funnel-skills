#!/usr/bin/env python3
"""Shared workspace helpers for the growth funnel skill."""

from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"

WORKSPACE_FILES = [
    "00_status.md",
    "01_intake_brief.yaml",
    "02_proof_library.csv",
    "03_current_metrics.csv",
    "04_channel_context.yaml",
    "05_segment_profile.yaml",
    "06_funnel_blueprint.md",
    "07_screen_specs.md",
    "08_tracking_plan.csv",
    "09_experiment_card.md",
    "10_postmortem_record.md",
    "11_presentation.html",
]

ARTIFACT_NAMES = {
    "01_intake_brief.yaml": "Intake brief",
    "02_proof_library.csv": "Proof library",
    "03_current_metrics.csv": "Current metrics",
    "04_channel_context.yaml": "Channel context",
    "05_segment_profile.yaml": "Segment profile",
    "06_funnel_blueprint.md": "Funnel blueprint",
    "07_screen_specs.md": "Screen specs",
    "08_tracking_plan.csv": "Tracking plan",
    "09_experiment_card.md": "Experiment card",
    "10_postmortem_record.md": "Postmortem record",
    "11_presentation.html": "Visual presentation",
}

INTAKE_FILE = "01_intake_brief.yaml"
PROOF_FILE = "02_proof_library.csv"
METRICS_FILE = "03_current_metrics.csv"
CHANNEL_FILE = "04_channel_context.yaml"
SEGMENT_FILE = "05_segment_profile.yaml"

CSV_HEADERS = {
    PROOF_FILE: [
        "proof_id",
        "type",
        "claim",
        "evidence",
        "source",
        "confidence",
        "notes",
    ],
    METRICS_FILE: ["metric_name", "value", "period", "segment", "source", "notes"],
    "08_tracking_plan.csv": [
        "event_name",
        "stage",
        "purpose",
        "required_properties",
        "primary_metric",
        "guardrail",
        "owner",
        "status",
    ],
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "funnel-workspace"


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return bool(str(value).strip())


def to_number(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", "."))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def read_flat_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not match:
            continue
        key, raw_value = match.groups()
        value = raw_value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        lower = value.lower()
        if lower == "true":
            data[key] = True
        elif lower == "false":
            data[key] = False
        else:
            data[key] = value
    return data


def write_flat_yaml(path: Path, updates: dict[str, Any], overwrite: bool = False) -> list[str]:
    existing = read_flat_yaml(path)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    changed: list[str] = []
    output: list[str] = []

    for line in lines:
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not match:
            output.append(line)
            continue
        key = match.group(1)
        seen.add(key)
        if key in updates and (overwrite or not present(existing.get(key))):
            output.append(f"{key}: {format_yaml_value(updates[key])}")
            if existing.get(key) != updates[key]:
                changed.append(key)
        else:
            output.append(line)

    for key, value in updates.items():
        if key not in seen:
            output.append(f"{key}: {format_yaml_value(value)}")
            changed.append(key)

    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    return changed


def format_yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = "" if value is None else str(value).strip()
    text = text.replace('"', '\\"')
    return f'"{text}"'


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def write_csv_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def append_csv_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> int:
    existing = read_csv_rows(path)
    signatures = {json.dumps(row, sort_keys=True) for row in existing}
    added = 0
    for row in rows:
        normalized = {key: str(row.get(key, "")).strip() for key in headers}
        if not any(normalized.values()):
            continue
        signature = json.dumps(normalized, sort_keys=True)
        if signature in signatures:
            continue
        existing.append(normalized)
        signatures.add(signature)
        added += 1
    write_csv_rows(path, headers, existing)
    return added


def ensure_workspace(
    workspace: Path, project_name: str | None = None, output_language: str | None = None
) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    for filename in WORKSPACE_FILES:
        destination = workspace / filename
        source = TEMPLATE_DIR / filename
        if not destination.exists():
            shutil.copyfile(source, destination)
    if project_name:
        updates = {"project_name": project_name}
        if output_language:
            updates["output_language"] = normalize_language(output_language)
        write_flat_yaml(workspace / INTAKE_FILE, updates, overwrite=False)


def normalize_language(language: str | None) -> str:
    if not language:
        return ""
    text = language.strip().lower()
    aliases = {
        "ru": "Russian",
        "rus": "Russian",
        "russian": "Russian",
        "русский": "Russian",
        "рус": "Russian",
        "en": "English",
        "eng": "English",
        "english": "English",
        "английский": "English",
        "es": "Spanish",
        "spanish": "Spanish",
        "español": "Spanish",
        "ua": "Ukrainian",
        "uk": "Ukrainian",
        "ukrainian": "Ukrainian",
        "українська": "Ukrainian",
        "украинский": "Ukrainian",
    }
    return aliases.get(text, language.strip())


def detect_language(text: str) -> str:
    if not text.strip():
        return ""
    cyrillic = len(re.findall(r"[А-Яа-яЁё]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if cyrillic > latin * 0.25 and cyrillic >= 12:
        return "Russian"
    return "English"


def output_language(data: dict[str, Any]) -> str:
    return normalize_language(str(data["intake"].get("output_language", ""))) or "English"


def is_russian(data_or_language: dict[str, Any] | str) -> bool:
    if isinstance(data_or_language, dict):
        language = output_language(data_or_language)
    else:
        language = normalize_language(data_or_language)
    return language.lower() == "russian"


def load_workspace(workspace: Path) -> dict[str, Any]:
    ensure_workspace(workspace)
    return {
        "workspace": workspace,
        "intake": read_flat_yaml(workspace / INTAKE_FILE),
        "channel": read_flat_yaml(workspace / CHANNEL_FILE),
        "segment": read_flat_yaml(workspace / SEGMENT_FILE),
        "proof_rows": read_csv_rows(workspace / PROOF_FILE),
        "metric_rows": read_csv_rows(workspace / METRICS_FILE),
        "tracking_rows": read_csv_rows(workspace / "08_tracking_plan.csv"),
    }


def has_proof(data: dict[str, Any]) -> bool:
    return bool(data["proof_rows"])


def no_proof_flag(data: dict[str, Any]) -> bool:
    return truthy(data["intake"].get("explicit_no_proof_yet"))


def proof_gate_satisfied(data: dict[str, Any]) -> bool:
    return has_proof(data) or no_proof_flag(data)


def critical_missing_fields(data: dict[str, Any]) -> list[str]:
    intake = data["intake"]
    channel = data["channel"]
    missing: list[str] = []
    if not present(intake.get("offer")):
        missing.append("offer")
    if not (present(intake.get("icp")) or present(intake.get("primary_persona"))):
        missing.append("ICP or primary persona")
    if not present(intake.get("target_kpi")):
        missing.append("target KPI")
    if not present(channel.get("primary_channel")):
        missing.append("primary channel")
    if not proof_gate_satisfied(data):
        missing.append("proof assets or explicit no-proof flag")
    return missing


def minimum_gate_satisfied(data: dict[str, Any]) -> bool:
    return not critical_missing_fields(data)


def completeness_score(data: dict[str, Any]) -> int:
    intake = data["intake"]
    channel = data["channel"]
    segment = data["segment"]
    score = 0
    checks = [
        (15, present(intake.get("offer"))),
        (10, present(intake.get("icp")) or present(intake.get("primary_persona"))),
        (10, present(intake.get("jtbd"))),
        (10, present(intake.get("target_kpi"))),
        (10, present(channel.get("primary_channel"))),
        (10, proof_gate_satisfied(data)),
        (10, bool(data["metric_rows"])),
        (
            10,
            present(intake.get("time_to_first_value_minutes"))
            or present(intake.get("product_constraints")),
        ),
        (5, present(intake.get("pricing")) or present(intake.get("sales_motion"))),
        (
            5,
            present(segment.get("awareness"))
            or present(segment.get("intent"))
            or present(segment.get("value_tier")),
        ),
        (5, present(intake.get("experiment_bandwidth"))),
    ]
    for points, ok in checks:
        if ok:
            score += points
    return min(score, 100)


def qualification_score(data: dict[str, Any]) -> int:
    intake = data["intake"]
    channel = data["channel"]
    segment = data["segment"]
    ttfv = to_number(intake.get("time_to_first_value_minutes"))
    score = 0
    if present(intake.get("offer")):
        score += 20
    if proof_gate_satisfied(data):
        score += 10 if has_proof(data) else 4
    if present(channel.get("primary_channel")) and (
        present(channel.get("audience_access")) or present(channel.get("traffic_source"))
    ):
        score += 15
    elif present(channel.get("primary_channel")):
        score += 8
    if present(intake.get("target_kpi")) and data["metric_rows"]:
        score += 15
    elif present(intake.get("target_kpi")):
        score += 8
    if ttfv is not None:
        score += 15 if ttfv <= 5 else 8
    elif present(intake.get("sales_motion")) and "demo" in str(intake.get("sales_motion")).lower():
        score += 8
    if present(intake.get("unit_economics")) or present(intake.get("pricing")):
        score += 10
    if present(intake.get("implementation_bandwidth")) or present(
        intake.get("experiment_bandwidth")
    ):
        score += 10
    if present(intake.get("jtbd")) or present(segment.get("persona_jtbd")):
        score += 5
    return min(score, 100)


def decision_from_score(score: int) -> str:
    if score >= 70:
        return "Go to funnel build"
    if score >= 55:
        return "Strategy or research sprint"
    return "Not ready for growth build"


def localized_decision(decision: str, language: str) -> str:
    if normalize_language(language).lower() != "russian":
        return decision
    return {
        "Go to funnel build": "Готово к сборке воронки",
        "Strategy or research sprint": "Нужен strategy/research sprint",
        "Not ready for growth build": "Пока не готово к growth-сборке",
    }.get(decision, decision)


def localized_missing_field(field: str, language: str) -> str:
    if normalize_language(language).lower() != "russian":
        return field
    return {
        "offer": "оффер",
        "ICP or primary persona": "ICP или основная персона",
        "target KPI": "целевой KPI",
        "primary channel": "основной канал",
        "proof assets or explicit no-proof flag": "доказательства или явный no-proof flag",
    }.get(field, field)


def yaml_status(data: dict[str, Any], filename: str, required: list[str]) -> str:
    if filename == INTAKE_FILE:
        values = data["intake"]
    elif filename == CHANNEL_FILE:
        values = data["channel"]
    else:
        values = data["segment"]
    meaningful = [value for key, value in values.items() if key != "project_name" and present(value)]
    if not meaningful:
        return "empty"
    if all(present(values.get(key)) for key in required):
        return "ready"
    return "partial"


def markdown_status(path: Path) -> str:
    if not path.exists():
        return "blocked"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^status:\s*([A-Za-z_-]+)\s*$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "draft" if text.strip() else "empty"


def artifact_statuses(data: dict[str, Any]) -> dict[str, str]:
    workspace = data["workspace"]
    min_gate = minimum_gate_satisfied(data)
    statuses = {
        INTAKE_FILE: yaml_status(
            data,
            INTAKE_FILE,
            ["offer", "target_kpi"],
        ),
        PROOF_FILE: "ready"
        if proof_gate_satisfied(data)
        else ("partial" if has_proof(data) else "empty"),
        METRICS_FILE: "ready" if data["metric_rows"] else "empty",
        CHANNEL_FILE: yaml_status(data, CHANNEL_FILE, ["primary_channel"]),
        SEGMENT_FILE: yaml_status(data, SEGMENT_FILE, ["selected_skeleton"]),
    }
    for filename in [
        "06_funnel_blueprint.md",
        "07_screen_specs.md",
        "09_experiment_card.md",
        "10_postmortem_record.md",
    ]:
        status = markdown_status(workspace / filename)
        statuses[filename] = status if min_gate or filename == "10_postmortem_record.md" else "blocked"
    if not min_gate:
        statuses["08_tracking_plan.csv"] = "blocked"
    else:
        statuses["08_tracking_plan.csv"] = "draft" if data["tracking_rows"] else "empty"
    presentation_exists = (workspace / "11_presentation.html").exists()
    statuses["11_presentation.html"] = "draft" if presentation_exists else "empty"
    return statuses


def contradictions(data: dict[str, Any]) -> list[str]:
    intake = data["intake"]
    channel = data["channel"]
    segment = data["segment"]
    warnings: list[str] = []
    if has_proof(data) and no_proof_flag(data):
        warnings.append("Proof rows exist while explicit_no_proof_yet is true.")
    if data["metric_rows"] and not present(intake.get("target_kpi")):
        warnings.append("Current metrics exist, but target_kpi is missing.")
    ttfv = to_number(intake.get("time_to_first_value_minutes"))
    self_serve = str(segment.get("self_serve_possible", "")).lower()
    sales_motion = str(intake.get("sales_motion", "")).lower()
    if ttfv is not None and ttfv > 5 and ("true" in self_serve or "self" in sales_motion):
        warnings.append("Estimated TTFV exceeds 5 minutes; use an assisted fallback path.")
    if (
        "sales" in str(channel.get("primary_channel", "")).lower()
        and "self-serve only" in sales_motion
    ):
        warnings.append("Sales-assisted channel conflicts with self-serve-only sales motion.")
    return warnings


def next_best_input(data: dict[str, Any]) -> list[str]:
    intake = data["intake"]
    channel = data["channel"]
    ru = is_russian(data)
    questions: list[str] = []
    if not present(intake.get("offer")):
        questions.append(
            "Что вы продаете и какой результат обещаете?"
            if ru
            else "What do you sell, and what result do you promise?"
        )
    if not (present(intake.get("icp")) or present(intake.get("primary_persona"))):
        questions.append(
            "Кто основной покупатель или пользователь?"
            if ru
            else "Who is the primary buyer or user?"
        )
    if not present(intake.get("target_kpi")):
        questions.append(
            "Какой один KPI должна улучшить эта воронка?"
            if ru
            else "Which single KPI should this funnel improve?"
        )
    if len(questions) < 3 and not present(channel.get("primary_channel")):
        questions.append(
            "Из какого канала придет трафик или лиды?"
            if ru
            else "Which channel will bring this traffic or lead source?"
        )
    if len(questions) < 3 and not proof_gate_satisfied(data):
        questions.append(
            "Какие доказательства уже есть, или поставить explicit_no_proof_yet=true?"
            if ru
            else "What proof exists, or should explicit_no_proof_yet be set to true?"
        )
    if len(questions) < 3 and not data["metric_rows"]:
        questions.append(
            "Какие базовые метрики воронки уже известны?"
            if ru
            else "What baseline funnel metrics do you already know?"
        )
    if len(questions) < 3 and not present(intake.get("time_to_first_value_minutes")):
        questions.append(
            "За сколько минут реально показать первую осмысленную ценность?"
            if ru
            else "How many minutes should first meaningful value realistically take?"
        )
    return questions[:3]


def select_skeleton(data: dict[str, Any]) -> tuple[str, str, str]:
    intake = data["intake"]
    segment = data["segment"]
    awareness = str(segment.get("awareness", "")).lower().replace("-", "_")
    intent = str(segment.get("intent", "")).lower()
    value_tier = str(segment.get("value_tier", "")).lower()
    lifecycle = str(segment.get("lifecycle", "")).lower()
    persona = (
        str(segment.get("persona_jtbd", ""))
        + " "
        + str(intake.get("primary_persona", ""))
        + " "
        + str(intake.get("jtbd", ""))
    ).lower()
    monetization = str(segment.get("monetization_model", "")).lower()
    stakeholders = to_number(segment.get("stakeholders_count"))
    ttfv = to_number(intake.get("time_to_first_value_minutes"))
    self_serve_text = str(segment.get("self_serve_possible", "")).lower()
    sales_motion = str(intake.get("sales_motion", "")).lower()
    self_serve_possible = truthy(self_serve_text) or "self" in sales_motion

    if "existing" in lifecycle or "customer" in lifecycle:
        skeleton = "expansion_rescue"
        rationale = "Existing-customer lifecycle points to expansion, rescue, or reactivation."
    elif "creator" in persona and any(
        token in monetization for token in ["recurring", "subscription", "community", "access"]
    ):
        skeleton = "creator_subscription"
        rationale = "Creator or community value is monetized through recurring access."
    elif value_tier == "high" or (stakeholders is not None and stakeholders > 1) or (
        ttfv is not None and ttfv > 5
    ):
        skeleton = "demo_led"
        rationale = "High value, multiple stakeholders, or slow first value needs assisted selling."
    elif awareness in {"product_aware", "most_aware", "productaware", "mostaware"} and intent in {
        "start",
        "buy",
    }:
        skeleton = "direct_offer"
        rationale = "High-intent product-aware traffic can handle a direct offer."
    elif self_serve_possible and ttfv is not None and ttfv <= 5:
        skeleton = "trial_to_value"
        rationale = "Self-serve path can reach meaningful value within one short session."
    elif awareness in {"problem_aware", "solution_aware", "problemaware", "solutionaware"}:
        skeleton = "diagnostic"
        rationale = "The lead understands the problem or solution category but still needs diagnosis."
    else:
        skeleton = "problem_aware"
        rationale = "Default for cold or unclear awareness: start with problem recognition."

    fallback_map = {
        "problem_aware": "diagnostic",
        "diagnostic": "demo_led",
        "trial_to_value": "diagnostic",
        "direct_offer": "trial_to_value",
        "demo_led": "diagnostic",
        "creator_subscription": "direct_offer",
        "expansion_rescue": "demo_led",
    }
    return skeleton, fallback_map[skeleton], rationale


def build_summary(workspace: Path) -> dict[str, Any]:
    data = load_workspace(workspace)
    completeness = completeness_score(data)
    qualification = qualification_score(data)
    summary = {
        "workspace": str(workspace),
        "completeness_score": completeness,
        "qualification_score": qualification,
        "decision": decision_from_score(qualification),
        "output_language": output_language(data),
        "minimum_gate_satisfied": minimum_gate_satisfied(data),
        "critical_missing_fields": critical_missing_fields(data),
        "contradictions": contradictions(data),
        "artifact_status": artifact_statuses(data),
        "next_best_input": next_best_input(data),
    }
    return summary


def write_status(workspace: Path, summary: dict[str, Any]) -> None:
    language = str(summary.get("output_language", "English"))
    ru = normalize_language(language).lower() == "russian"
    status_lines = [
        "# Статус funnel workspace" if ru else "# Funnel Workspace Status",
        "",
        f"Workspace: `{summary['workspace']}`",
        "",
        f"- Язык выдачи: {summary.get('output_language', 'English')}"
        if ru
        else f"- Output language: {summary.get('output_language', 'English')}",
        f"- Completeness score: {summary['completeness_score']}/100",
        f"- Qualification score: {summary['qualification_score']}/100",
        f"- Решение: {localized_decision(str(summary['decision']), language)}"
        if ru
        else f"- Decision: {summary['decision']}",
        f"- Minimum input gate: {'satisfied' if summary['minimum_gate_satisfied'] else 'blocked'}",
        "",
        "## Статус артефактов" if ru else "## Artifact Status",
        "",
        "| Artifact | Status |",
        "| --- | --- |",
    ]
    for filename in WORKSPACE_FILES[1:]:
        status_lines.append(
            f"| {filename} | {summary['artifact_status'].get(filename, 'empty')} |"
        )

    status_lines.extend(["", "## Критично не хватает" if ru else "## Critical Missing Fields", ""])
    if summary["critical_missing_fields"]:
        status_lines.extend(
            f"- {localized_missing_field(str(field), language)}"
            for field in summary["critical_missing_fields"]
        )
    else:
        status_lines.append("- Нет" if ru else "- None")

    status_lines.extend(
        ["", "## Противоречия и предупреждения" if ru else "## Contradictions and Warnings", ""]
    )
    if summary["contradictions"]:
        status_lines.extend(f"- {item}" for item in summary["contradictions"])
    else:
        status_lines.append("- Не обнаружены" if ru else "- None detected")

    status_lines.extend(["", "## Следующий лучший ввод" if ru else "## Next Best Input", ""])
    if summary["next_best_input"]:
        status_lines.extend(
            f"{index}. {question}"
            for index, question in enumerate(summary["next_best_input"], start=1)
        )
    else:
        status_lines.append(
            "Блокирующих вводных не осталось. Проверьте draft-артефакты и presentation HTML."
            if ru
            else "No blocking input remains. Render or review the draft artifacts and presentation HTML."
        )

    (workspace / "00_status.md").write_text("\n".join(status_lines) + "\n", encoding="utf-8")


def validate_and_write_status(workspace: Path) -> dict[str, Any]:
    summary = build_summary(workspace)
    write_status(workspace, summary)
    return summary


def write_initial_presentation(workspace: Path, summary: dict[str, Any]) -> None:
    language = str(summary.get("output_language", "English"))
    ru = normalize_language(language).lower() == "russian"
    title = "Презентация growth funnel" if ru else "Growth Funnel Presentation"
    subtitle = (
        "Визуальный статус workspace. Добавьте вводные, чтобы разблокировать blueprint, screen specs, tracking plan и experiment card."
        if ru
        else "Visual workspace status. Add inputs to unlock the blueprint, screen specs, tracking plan, and experiment card."
    )
    missing_title = "Критично не хватает" if ru else "Critical Missing"
    next_title = "Следующий ввод" if ru else "Next Input"
    missing_items = "\n".join(
        f"          <li>{localized_missing_field(str(field), language)}</li>"
        for field in summary["critical_missing_fields"]
    ) or ("          <li>Нет</li>" if ru else "          <li>None</li>")
    next_items = "\n".join(
        f"          <li>{question}</li>" for question in summary["next_best_input"]
    ) or (
        "          <li>Блокирующих вводных не осталось.</li>"
        if ru
        else "          <li>No blocking input remains.</li>"
    )
    html = f"""<!doctype html>
<html lang="{'ru' if ru else 'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #172033; background: #f6f7f9; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px; }}
    section {{ margin: 0 0 24px; padding: 24px; background: #fff; border: 1px solid #d9dee7; border-radius: 8px; }}
    h1, h2 {{ margin: 0 0 12px; }}
    p, li {{ line-height: 1.55; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    .metric {{ padding: 16px; border: 1px solid #e0e5ee; border-radius: 8px; background: #fbfcfe; }}
    .metric strong {{ display: block; font-size: 28px; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>{title}</h1>
      <p>{subtitle}</p>
      <div class="grid">
        <div class="metric"><strong>{summary['completeness_score']}</strong>Completeness</div>
        <div class="metric"><strong>{summary['qualification_score']}</strong>Qualification</div>
      </div>
    </section>
    <section>
      <h2>{missing_title}</h2>
      <ul>
{missing_items}
      </ul>
    </section>
    <section>
      <h2>{next_title}</h2>
      <ul>
{next_items}
      </ul>
    </section>
  </main>
</body>
</html>
"""
    (workspace / "11_presentation.html").write_text(html, encoding="utf-8")
