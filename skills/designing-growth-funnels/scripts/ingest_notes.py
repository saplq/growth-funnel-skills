#!/usr/bin/env python3
"""Ingest rough user notes into structured workspace files without deleting data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from workspace_lib import (
    CHANNEL_FILE,
    INTAKE_FILE,
    METRICS_FILE,
    PROOF_FILE,
    SEGMENT_FILE,
    append_csv_rows,
    detect_language,
    ensure_workspace,
    present,
    read_flat_yaml,
    validate_and_write_status,
    write_flat_yaml,
)


INTAKE_LABELS = {
    "project": "project_name",
    "project name": "project_name",
    "проект": "project_name",
    "название проекта": "project_name",
    "offer": "offer",
    "оффер": "offer",
    "предложение": "offer",
    "product": "offer",
    "продукт": "offer",
    "promise": "offer",
    "обещание": "offer",
    "pricing": "pricing",
    "price": "pricing",
    "цена": "pricing",
    "тариф": "pricing",
    "icp": "icp",
    "ицп": "icp",
    "целевая аудитория": "icp",
    "audience": "icp",
    "аудитория": "icp",
    "customer": "icp",
    "buyer": "primary_persona",
    "покупатель": "primary_persona",
    "persona": "primary_persona",
    "персона": "primary_persona",
    "primary persona": "primary_persona",
    "user": "primary_persona",
    "пользователь": "primary_persona",
    "jtbd": "jtbd",
    "job": "jtbd",
    "job to be done": "jtbd",
    "работа": "jtbd",
    "задача": "jtbd",
    "target kpi": "target_kpi",
    "kpi": "target_kpi",
    "цель": "target_kpi",
    "целевой kpi": "target_kpi",
    "метрика": "target_kpi",
    "goal metric": "target_kpi",
    "time to first value": "time_to_first_value_minutes",
    "ttfv": "time_to_first_value_minutes",
    "время до ценности": "time_to_first_value_minutes",
    "constraints": "product_constraints",
    "product constraints": "product_constraints",
    "ограничения": "product_constraints",
    "sales motion": "sales_motion",
    "модель продаж": "sales_motion",
    "unit economics": "unit_economics",
    "юнит экономика": "unit_economics",
    "implementation bandwidth": "implementation_bandwidth",
    "experiment bandwidth": "experiment_bandwidth",
    "язык": "output_language",
    "language": "output_language",
    "output language": "output_language",
}

CHANNEL_LABELS = {
    "channel": "primary_channel",
    "primary channel": "primary_channel",
    "канал": "primary_channel",
    "основной канал": "primary_channel",
    "traffic source": "traffic_source",
    "traffic": "traffic_source",
    "трафик": "traffic_source",
    "источник трафика": "traffic_source",
    "campaign": "campaign_context",
    "campaign context": "campaign_context",
    "message match": "message_match_notes",
    "audience access": "audience_access",
    "доступ к аудитории": "audience_access",
    "volume": "volume_estimate",
    "volume estimate": "volume_estimate",
    "utm": "utm_or_referrer_notes",
    "referrer": "utm_or_referrer_notes",
}

SEGMENT_LABELS = {
    "awareness": "awareness",
    "осведомленность": "awareness",
    "intent": "intent",
    "намерение": "intent",
    "value tier": "value_tier",
    "уровень ценности": "value_tier",
    "lifecycle": "lifecycle",
    "жизненный цикл": "lifecycle",
    "persona jtbd": "persona_jtbd",
    "stakeholders": "stakeholders_count",
    "stakeholders count": "stakeholders_count",
    "стейкхолдеры": "stakeholders_count",
    "self serve": "self_serve_possible",
    "self-serve": "self_serve_possible",
    "самообслуживание": "self_serve_possible",
    "monetization": "monetization_model",
    "monetization model": "monetization_model",
    "монетизация": "monetization_model",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest rough notes into the structured funnel workspace."
    )
    parser.add_argument("workspace_dir", help="Workspace directory to update.")
    parser.add_argument(
        "--input",
        required=True,
        help="Input note file path, or '-' to read from stdin.",
    )
    return parser.parse_args()


def read_input(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).expanduser().read_text(encoding="utf-8")


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower().replace("_", " "))


def parse_labeled_values(text: str) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    intake: dict[str, str] = {}
    channel: dict[str, str] = {}
    segment: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        value = value.strip()
        if not value:
            continue
        normalized = normalize_label(label)
        if normalized in INTAKE_LABELS:
            intake[INTAKE_LABELS[normalized]] = value
        elif normalized in CHANNEL_LABELS:
            channel[CHANNEL_LABELS[normalized]] = value
        elif normalized in SEGMENT_LABELS:
            segment[SEGMENT_LABELS[normalized]] = value
    return intake, channel, segment


def extract_proof_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    proof_terms = re.compile(
        r"\b(proof|case|testimonial|customer|benchmark|screenshot|demo|review|evidence)\b|"
        r"(доказательств|кейс|отзыв|клиент|бенчмарк|скриншот|демо)",
        re.IGNORECASE,
    )
    negative_proof_terms = re.compile(
        r"\b(no proof|no proofs|no case studies|no testimonials)\b|"
        r"(нет доказательств|нет кейсов|нет отзывов)",
        re.IGNORECASE,
    )
    for index, line in enumerate(text.splitlines(), start=1):
        clean = line.strip(" -\t")
        if not clean or negative_proof_terms.search(clean) or not proof_terms.search(clean):
            continue
        rows.append(
            {
                "proof_id": f"proof-{index}",
                "type": "raw_note",
                "claim": clean[:120],
                "evidence": clean,
                "source": "ingested_notes",
                "confidence": "unknown",
                "notes": "",
            }
        )
    return rows


def extract_metric_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    metric_terms = re.compile(
        r"\b(metric|conversion|ctr|cvr|activation|retention|trial|paid|signup|ttfv|revenue|cac|ltv)\b|"
        r"(метрик|конверс|активац|удержан|триал|оплат|регистрац|выручк|доход|cac|ltv)",
        re.IGNORECASE,
    )
    number_pattern = re.compile(r"\d+(?:[.,]\d+)?%?")
    for index, line in enumerate(text.splitlines(), start=1):
        clean = line.strip(" -\t")
        if not clean or not metric_terms.search(clean) or not number_pattern.search(clean):
            continue
        value = number_pattern.search(clean).group(0)
        metric_name = clean.split(":", 1)[0][:80] if ":" in clean else "raw_metric"
        rows.append(
            {
                "metric_name": metric_name,
                "value": value,
                "period": "",
                "segment": "",
                "source": "ingested_notes",
                "notes": clean,
            }
        )
    return rows


def append_note(existing: str, text: str) -> str:
    note = text.strip()
    if not note:
        return existing
    if not existing:
        return note
    if note in existing:
        return existing
    return existing.rstrip() + "\n\n" + note


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        ensure_workspace(workspace)
        text = read_input(args.input)
        intake_updates, channel_updates, segment_updates = parse_labeled_values(text)
        current_intake = read_flat_yaml(workspace / INTAKE_FILE)
        if not present(current_intake.get("output_language")):
            detected_language = detect_language(text)
            if detected_language:
                intake_updates["output_language"] = detected_language

        if re.search(
            r"\b(no proof|no proofs|no case studies|no testimonials)\b|"
            r"(нет доказательств|нет кейсов|нет отзывов)",
            text,
            re.I,
        ):
            intake_updates["explicit_no_proof_yet"] = True

        if not intake_updates and not channel_updates and not segment_updates:
            existing = read_flat_yaml(workspace / INTAKE_FILE).get("notes", "")
            intake_updates["notes"] = append_note(str(existing), text)

        changed = {
            "intake": write_flat_yaml(workspace / INTAKE_FILE, intake_updates, overwrite=False)
            if intake_updates
            else [],
            "channel": write_flat_yaml(workspace / CHANNEL_FILE, channel_updates, overwrite=False)
            if channel_updates
            else [],
            "segment": write_flat_yaml(workspace / SEGMENT_FILE, segment_updates, overwrite=False)
            if segment_updates
            else [],
            "proof_rows_added": append_csv_rows(
                workspace / PROOF_FILE,
                [
                    "proof_id",
                    "type",
                    "claim",
                    "evidence",
                    "source",
                    "confidence",
                    "notes",
                ],
                extract_proof_rows(text),
            ),
            "metric_rows_added": append_csv_rows(
                workspace / METRICS_FILE,
                ["metric_name", "value", "period", "segment", "source", "notes"],
                extract_metric_rows(text),
            ),
        }
        summary = validate_and_write_status(workspace)
    except (OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"changed": changed, "summary": summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
