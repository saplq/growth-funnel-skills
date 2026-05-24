#!/usr/bin/env python3
"""Ingest rough notes, research, competitors, or metrics into runtime state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from workspace_lib import (
    COMPETITOR_HEADERS,
    append_csv_unique,
    append_jsonl_unique,
    detect_language,
    ensure_workspace,
    load_workspace,
    normalize_competitor,
    normalize_source,
    runtime_path,
    update_intake,
    validate_and_write,
)


LABELS = {
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
    "icp": "icp",
    "ицп": "icp",
    "audience": "icp",
    "аудитория": "icp",
    "целевая аудитория": "icp",
    "persona": "primary_persona",
    "primary persona": "primary_persona",
    "персона": "primary_persona",
    "пользователь": "primary_persona",
    "buyer": "primary_persona",
    "jtbd": "jtbd",
    "job to be done": "jtbd",
    "задача": "jtbd",
    "target kpi": "target_kpi",
    "kpi": "target_kpi",
    "целевой kpi": "target_kpi",
    "метрика": "target_kpi",
    "goal metric": "target_kpi",
    "channel": "primary_channel",
    "primary channel": "primary_channel",
    "канал": "primary_channel",
    "основной канал": "primary_channel",
    "current funnel": "current_funnel",
    "existing funnel": "current_funnel",
    "current funnel steps": "current_funnel",
    "existing funnel steps": "current_funnel",
    "текущая воронка": "current_funnel",
    "текущий путь": "current_funnel",
    "текущие шаги": "current_funnel",
    "pricing": "pricing",
    "price": "pricing",
    "цена": "pricing",
    "тариф": "pricing",
    "ttfv": "time_to_first_value_minutes",
    "time to first value": "time_to_first_value_minutes",
    "время до ценности": "time_to_first_value_minutes",
    "sales motion": "sales_motion",
    "модель продаж": "sales_motion",
    "constraints": "product_constraints",
    "product constraints": "product_constraints",
    "ограничения": "product_constraints",
    "unit economics": "unit_economics",
    "юнит экономика": "unit_economics",
    "implementation bandwidth": "implementation_bandwidth",
    "experiment bandwidth": "experiment_bandwidth",
    "reviewer approval": "reviewer_approval",
    "review approval": "reviewer_approval",
    "human approval": "reviewer_approval",
    "approval": "reviewer_approval",
    "reviewer": "reviewer_approval",
    "одобрение": "reviewer_approval",
    "апрув": "reviewer_approval",
    "согласование": "reviewer_approval",
    "ревьюер": "reviewer_approval",
    "language": "output_language",
    "язык": "output_language",
}

URL_PATTERN = re.compile(r"https?://[^\s),\]]+", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
CURRENT_FUNNEL_KEYS = {"current_funnel"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest normalized or rough growth funnel notes into runtime state.")
    parser.add_argument("workspace_dir", help="Workspace directory to update.")
    parser.add_argument("--input", required=True, help="Input path or '-' for stdin.")
    parser.add_argument("--kind", choices=["notes", "research", "competitor", "metrics"], default="notes", help="How to interpret the input.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def read_input(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).expanduser().read_text(encoding="utf-8")


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower().replace("_", " "))


def parse_labeled_updates(text: str) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        key = LABELS.get(normalize_label(label))
        if key and value.strip():
            updates[key] = value.strip()
    if re.search(r"\b(no proof yet|no proof|no proofs|no case studies|no testimonials)\b", text, re.IGNORECASE) or re.search(r"(нет доказательств|нет кейсов|нет отзывов)", text, re.IGNORECASE):
        updates["explicit_no_proof_yet"] = True
    current_funnel = extract_current_funnel_steps(text)
    if current_funnel:
        updates["current_funnel"] = current_funnel
    return updates


def clean_current_funnel_step(value: str) -> str:
    text = re.sub(r"^\s*[-*]\s*", "", value)
    text = re.sub(r"^\s*\d+[.)]\s*", "", text)
    return re.sub(r"\s+", " ", text.strip()).strip()


def split_current_funnel_step(value: str) -> list[str]:
    clean = clean_current_funnel_step(value)
    if not clean:
        return []
    if re.search(r"\s*(?:->|=>|→)\s*", clean):
        return [item for item in (clean_current_funnel_step(part) for part in re.split(r"\s*(?:->|=>|→)\s*", clean)) if item]
    return [clean]


def is_section_heading(line: str) -> bool:
    if ":" not in line:
        return False
    label, _ = line.split(":", 1)
    normalized = normalize_label(label)
    return normalized in LABELS or normalized in {"proof", "current metrics", "competitor", "конкурент"}


def extract_current_funnel_steps(text: str) -> list[str]:
    rows: list[str] = []
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in stripped:
            label, value = stripped.split(":", 1)
            key = LABELS.get(normalize_label(label))
            if key in CURRENT_FUNNEL_KEYS:
                collecting = True
                rows.extend(split_current_funnel_step(value))
                continue
            if collecting and is_section_heading(stripped):
                collecting = False
        if not collecting:
            continue
        if is_section_heading(stripped) and not stripped.startswith(("-", "*")):
            collecting = False
            continue
        rows.extend(split_current_funnel_step(stripped))
    return list(dict.fromkeys(row for row in rows if row))


def extract_proofs(text: str) -> list[str]:
    rows: list[str] = []
    proof_terms = re.compile(
        r"\b(proof|case|testimonial|customer|benchmark|screenshot|demo|review|evidence)\b|"
        r"(доказательств|доказательство|кейс|отзыв|клиент|бенчмарк|скриншот|демо)",
        re.IGNORECASE,
    )
    negative = re.compile(r"\b(no proof|no proofs|no case studies|no testimonials)\b|(нет доказательств|нет кейсов|нет отзывов)", re.IGNORECASE)
    for line in text.splitlines():
        clean = line.strip(" -\t")
        if clean.lower().startswith("competitor:") or clean.lower().startswith("конкурент:"):
            continue
        if clean and proof_terms.search(clean) and not negative.search(clean):
            rows.append(clean)
    return rows


def extract_metrics(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    metric_terms = re.compile(
        r"\b(metric|conversion|ctr|cvr|activation|retention|trial|paid|signup|ttfv|revenue|cac|ltv|mrr|arr)\b|"
        r"(метрик|конверс|активац|удержан|триал|оплат|регистрац|выручк|доход)",
        re.IGNORECASE,
    )
    number_pattern = re.compile(r"\d+(?:[.,]\d+)?%?")
    for line in text.splitlines():
        clean = line.strip(" -\t")
        if not clean or not metric_terms.search(clean) or not number_pattern.search(clean):
            continue
        value = number_pattern.search(clean)
        rows.append(
            {
                "metric_name": clean.split(":", 1)[0][:80] if ":" in clean else "raw_metric",
                "value": value.group(0) if value else "",
                "source": "ingested_notes",
                "notes": clean,
            }
        )
    return rows


def source_type_from_line(line: str, default: str) -> str:
    lowered = line.lower()
    if "pricing" in lowered or "price" in lowered or "тариф" in lowered or "цена" in lowered:
        return "pricing"
    if "changelog" in lowered or "release" in lowered:
        return "changelog"
    if "current practice" in lowered or "best practice" in lowered:
        return "current_practice"
    if "review" in lowered or "отзыв" in lowered:
        return "review"
    if "case" in lowered or "testimonial" in lowered or "proof" in lowered or "кейс" in lowered:
        return "case_study"
    if "docs" in lowered or "documentation" in lowered or "документац" in lowered:
        return "docs"
    if "competitor" in lowered or "конкурент" in lowered:
        return "competitor"
    return default


def extract_sources(text: str, default_type: str = "other") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        clean = line.strip(" -\t")
        if not clean:
            continue
        urls = [match.group(0).rstrip(".,;)") for match in URL_PATTERN.finditer(clean)]
        if not urls:
            continue
        retrieved = ""
        date_match = DATE_PATTERN.search(clean)
        if date_match:
            retrieved = date_match.group(1)
        for url in urls:
            title = clean.replace(url, "").strip(" :-|")
            source = normalize_source(
                {
                    "source_id": f"source-{line_no}-{len(rows) + 1}",
                    "url": url,
                    "title": title[:140],
                    "retrieved_at": retrieved,
                    "source_type": source_type_from_line(clean, default_type),
                    "confidence": "medium",
                    "used_in": ["research_evidence"],
                    "notes": clean,
                },
                index=line_no,
                default_type=default_type,
            )
            rows.append(source)
    return rows


def parse_kv_segments(segments: list[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for segment in segments:
        if ":" not in segment:
            continue
        label, value = segment.split(":", 1)
        key = normalize_label(label)
        mapped = {
            "domain": "domain",
            "positioning": "positioning",
            "pricing": "pricing",
            "price": "pricing",
            "cta": "primary_cta",
            "primary cta": "primary_cta",
            "onboarding": "onboarding_pattern",
            "proof": "proof",
            "first value": "first_value_path",
            "first value path": "first_value_path",
            "weakness": "observed_weaknesses",
            "weaknesses": "observed_weaknesses",
            "source": "source",
            "confidence": "confidence",
            "retrieved": "retrieved_at",
            "retrieved at": "retrieved_at",
            "retrieved_at": "retrieved_at",
            "notes": "notes",
        }.get(key)
        if mapped:
            data[mapped] = value.strip()
    return data


def extract_competitors(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        clean = line.strip(" -\t")
        if not clean or not re.match(r"^(competitor|конкурент)\s*:", clean, re.IGNORECASE):
            continue
        _, payload = clean.split(":", 1)
        segments = [segment.strip() for segment in payload.split("|")]
        if not segments:
            continue
        row = {"competitor": segments[0]}
        row.update(parse_kv_segments(segments[1:]))
        date_match = DATE_PATTERN.search(clean)
        if date_match and not row.get("retrieved_at"):
            row["retrieved_at"] = date_match.group(1)
        if not row.get("source"):
            urls = URL_PATTERN.findall(clean)
            if urls:
                row["source"] = urls[-1].rstrip(".,;)")
        rows.append(normalize_competitor(row))
    return rows


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        text = read_input(args.input)
        language = detect_language(text)
        ensure_workspace(workspace, language=language)

        changed: dict[str, Any] = {
            "intake": [],
            "proof_assets_added": 0,
            "metrics_added": 0,
            "source_rows_added": 0,
            "competitor_rows_added": 0,
        }

        if args.kind in {"notes", "metrics"}:
            updates = parse_labeled_updates(text)
            proofs = extract_proofs(text)
            metrics = extract_metrics(text)
            before = load_workspace(workspace)["intake"]
            before_proofs = before.get("proof_assets") if isinstance(before.get("proof_assets"), list) else []
            before_metrics = before.get("metrics") if isinstance(before.get("metrics"), list) else []
            if proofs:
                updates["proof_assets"] = proofs
            if metrics:
                updates["metrics"] = metrics
            changed["intake"] = update_intake(workspace, updates)
            after = load_workspace(workspace)["intake"]
            after_proofs = after.get("proof_assets") if isinstance(after.get("proof_assets"), list) else []
            after_metrics = after.get("metrics") if isinstance(after.get("metrics"), list) else []
            changed["proof_assets_added"] = max(0, len(after_proofs) - len(before_proofs))
            changed["metrics_added"] = max(0, len(after_metrics) - len(before_metrics))

        if args.kind in {"notes", "research", "competitor"}:
            sources = extract_sources(text, "current_practice" if args.kind == "research" else "other")
            if sources:
                changed["source_rows_added"] = append_jsonl_unique(
                    runtime_path(workspace, "sources.jsonl"),
                    sources,
                    ["url", "title"],
                )

        if args.kind in {"notes", "competitor"}:
            competitors = extract_competitors(text)
            if competitors:
                changed["competitor_rows_added"] = append_csv_unique(
                    runtime_path(workspace, "competitors.csv"),
                    COMPETITOR_HEADERS,
                    competitors,
                    ["competitor", "domain", "source"],
                )

        summary = validate_and_write(workspace)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"changed": changed, "summary": summary}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
