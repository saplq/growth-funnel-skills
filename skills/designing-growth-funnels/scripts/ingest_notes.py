#!/usr/bin/env python3
"""Ingest rough user notes into structured workspace files without deleting data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from workspace_lib import (
    COMPETITOR_FILE,
    CHANNEL_FILE,
    CSV_HEADERS,
    INTAKE_FILE,
    METRICS_FILE,
    PROOF_FILE,
    SEGMENT_FILE,
    SOURCE_FILE,
    append_csv_rows,
    append_jsonl_rows,
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


URL_PATTERN = re.compile(r"https?://[^\s),\]]+", re.IGNORECASE)


def clean_url(url: str) -> str:
    return url.rstrip(".,;)")


def source_type_from_line(line: str) -> str:
    lowered = line.lower()
    if "pricing" in lowered or "price" in lowered or "тариф" in lowered or "цена" in lowered:
        return "pricing"
    if "review" in lowered or "отзыв" in lowered:
        return "review"
    if (
        "proof" in lowered
        or "evidence" in lowered
        or "case" in lowered
        or "testimonial" in lowered
        or "кейс" in lowered
        or "доказатель" in lowered
    ):
        return "proof"
    if "docs" in lowered or "documentation" in lowered or "документац" in lowered:
        return "docs"
    if "competitor" in lowered or "конкурент" in lowered:
        return "competitor"
    return "url"


def extract_source_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        clean = line.strip(" -\t")
        if not clean:
            continue
        urls = [clean_url(match.group(0)) for match in URL_PATTERN.finditer(clean)]
        if not urls:
            continue
        for url in urls:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            title = clean.replace(url, "").strip(" :-|")[:120]
            rows.append(
                {
                    "source_id": f"source-{index}-{len(rows) + 1}",
                    "type": source_type_from_line(clean),
                    "title": title or domain or url,
                    "url": url,
                    "domain": domain,
                    "accessed_at": "",
                    "confidence": "unknown",
                    "linked_claim": clean[:180],
                    "notes": "",
                }
            )
    return rows


def value_after_label(segment: str) -> str:
    if ":" not in segment:
        return segment.strip()
    return segment.split(":", 1)[1].strip()


def extract_competitor_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    competitor_terms = re.compile(r"\bcompetitor\b|конкурент", re.IGNORECASE)
    field_map = {
        "domain": "domain",
        "url": "source",
        "source": "source",
        "источник": "source",
        "pricing": "pricing",
        "price": "pricing",
        "цена": "pricing",
        "тариф": "pricing",
        "positioning": "positioning",
        "позиционирование": "positioning",
        "cta": "primary_cta",
        "call to action": "primary_cta",
        "onboarding": "onboarding_pattern",
        "онбординг": "onboarding_pattern",
        "proof": "proof",
        "evidence": "proof",
        "review": "proof",
        "first value": "first_value_path",
        "ttfv": "first_value_path",
        "weakness": "observed_weaknesses",
        "слаб": "observed_weaknesses",
        "confidence": "confidence",
    }

    for line in text.splitlines():
        clean = line.strip(" -\t")
        if not clean or not competitor_terms.search(clean):
            continue
        row = {header: "" for header in CSV_HEADERS[COMPETITOR_FILE]}
        row["confidence"] = "unknown"
        content = clean
        if ":" in clean and competitor_terms.search(clean.split(":", 1)[0]):
            content = clean.split(":", 1)[1].strip()
        parts = [part.strip() for part in re.split(r"\s+\|\s+|;", content) if part.strip()]
        if parts:
            row["competitor"] = re.sub(
                r"^(competitor|конкурент)\s*:?\s*", "", parts[0], flags=re.IGNORECASE
            ).strip()
        urls = [clean_url(match.group(0)) for match in URL_PATTERN.finditer(clean)]
        if urls:
            row["source"] = urls[0]
            parsed = urlparse(urls[0])
            row["domain"] = parsed.netloc.lower().removeprefix("www.")
            if not row["competitor"]:
                row["competitor"] = row["domain"]
        for part in (parts[1:] if len(parts) > 1 else parts):
            normalized = normalize_label(part.split(":", 1)[0]) if ":" in part else ""
            for label, field in field_map.items():
                if normalized == label or (not normalized and label in part.lower()):
                    value = value_after_label(part)
                    if field == "domain":
                        row[field] = value.replace("https://", "").replace("http://", "").strip("/")
                    elif field == "source" and URL_PATTERN.search(value):
                        row[field] = clean_url(URL_PATTERN.search(value).group(0))
                    elif field != "source" or value:
                        row[field] = value
                    break
        if row["competitor"] or row["domain"] or row["source"]:
            row["notes"] = clean
            rows.append(row)
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
            "source_rows_added": append_jsonl_rows(
                workspace / SOURCE_FILE,
                extract_source_rows(text),
            ),
            "competitor_rows_added": append_csv_rows(
                workspace / COMPETITOR_FILE,
                CSV_HEADERS[COMPETITOR_FILE],
                extract_competitor_rows(text),
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
