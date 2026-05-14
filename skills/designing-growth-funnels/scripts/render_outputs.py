#!/usr/bin/env python3
"""Render funnel artifacts from a validated workspace."""

from __future__ import annotations

import argparse
import csv
from html import escape
import json
import re
import sys
from pathlib import Path

from workspace_lib import (
    GAP_FILE,
    SEGMENT_FILE,
    append_csv_rows,
    critical_missing_fields,
    ensure_workspace,
    is_russian,
    load_workspace,
    localized_decision,
    localized_evidence_gap,
    localized_missing_field,
    minimum_gate_satisfied,
    output_language,
    qualification_score,
    select_skeleton,
    validate_and_write_status,
    write_flat_yaml,
)


SCREEN_STAGES = [
    (
        "Landing",
        "This is about my situation and worth continuing.",
        "Pain/outcome hero, proof band, channel message match, result preview.",
        "Check my path",
        "Brief Started / Landing Viewed",
    ),
    (
        "Brief",
        "The system understands my context and is not wasting my time.",
        "3-7 adaptive questions, progress, why-this-asks hints.",
        "Continue diagnosis",
        "Brief Completed / Brief Started",
    ),
    (
        "Diagnosis",
        "The problem is specific, provable, and fixable.",
        "Ranked gaps, severity, impact, confidence.",
        "Build my plan",
        "Roadmap Viewed / Diagnosis Generated",
    ),
    (
        "Roadmap",
        "There is a credible route to first value.",
        "Quick win, 7/30/90 path, effort/impact, path choice.",
        "Start the plan",
        "Onboarding Started / Roadmap Viewed",
    ),
    (
        "Onboarding",
        "Value can happen quickly without a tutorial.",
        "One task at a time, prefill/sample data, contextual help.",
        "Create first result",
        "First Value Reached / Onboarding Started",
    ),
    (
        "Paywall",
        "Payment is the next step after value, not a surprise interruption.",
        "Outcome-based plans, proof, FAQ, preserved state.",
        "Choose plan",
        "Payment Completed / Checkout Started",
    ),
    (
        "Retention",
        "Returning produces a new useful reward.",
        "Weekly insight, one recommended action, progress update.",
        "Run this week's improvement",
        "D7/D30 retention",
    ),
]


TRACKING_ROWS = [
    {
        "event_name": "Landing Viewed",
        "stage": "Landing",
        "purpose": "Count qualified exposure to the funnel entry point",
        "required_properties": "channel,campaign_id,creative_id,awareness_guess",
        "primary_metric": "Brief Started / Landing Viewed",
        "guardrail": "bounce proxy,rage clicks",
        "owner": "Growth",
        "status": "draft",
    },
    {
        "event_name": "Brief Started",
        "stage": "Brief",
        "purpose": "Measure transition from message to diagnostic intent",
        "required_properties": "segment_id,skeleton_id,entry_cta",
        "primary_metric": "Brief Started / Landing Viewed",
        "guardrail": "low-quality starts",
        "owner": "Growth",
        "status": "draft",
    },
    {
        "event_name": "Brief Completed",
        "stage": "Brief",
        "purpose": "Measure completion of required context capture",
        "required_properties": "question_count,branch_id,completion_time_seconds",
        "primary_metric": "Brief Completed / Brief Started",
        "guardrail": "median completion time",
        "owner": "PM",
        "status": "draft",
    },
    {
        "event_name": "Diagnosis Generated",
        "stage": "Diagnosis",
        "purpose": "Confirm the system produced a segment-specific insight",
        "required_properties": "diagnosis_category,severity,confidence_score",
        "primary_metric": "Roadmap Viewed / Diagnosis Generated",
        "guardrail": "fallback diagnosis rate",
        "owner": "PMM",
        "status": "draft",
    },
    {
        "event_name": "First Value Reached",
        "stage": "Onboarding",
        "purpose": "Measure first meaningful outcome",
        "required_properties": "setup_path,time_to_first_value_seconds,sample_data_used",
        "primary_metric": "First Value Reached / Onboarding Started",
        "guardrail": "support contact rate",
        "owner": "Product",
        "status": "draft",
    },
    {
        "event_name": "Payment Completed",
        "stage": "Paywall",
        "purpose": "Measure monetization after value exposure",
        "required_properties": "plan_id,billing_period,price_local,discount",
        "primary_metric": "Payment Completed / Checkout Started",
        "guardrail": "refunds,payment error rate",
        "owner": "Growth",
        "status": "draft",
    },
    {
        "event_name": "Experiment Exposed",
        "stage": "Experimentation",
        "purpose": "Create trustworthy exposure logging",
        "required_properties": "experiment_id,variant_id,eligibility_rule,exposure_time",
        "primary_metric": "target KPI",
        "guardrail": "SRM,event loss",
        "owner": "Data",
        "status": "draft",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render draft funnel outputs once the minimum input gate is satisfied."
    )
    parser.add_argument("workspace_dir", help="Workspace directory to render.")
    return parser.parse_args()


def blocked_markdown(
    artifact: str, title: str, missing: list[str], language: str = "English"
) -> str:
    ru = language.lower() == "russian"
    missing_lines = "\n".join(f"- {field}" for field in missing)
    if ru:
        return f"""---
artifact: {artifact}
status: blocked
---

# {title}

Этот артефакт заблокирован, пока не выполнен minimum input gate.

## Не хватает

{missing_lines}
"""
    return f"""---
artifact: {artifact}
status: blocked
---

# {title}

This artifact is blocked until the minimum input gate is satisfied.

## Missing

{missing_lines}
"""


def render_blueprint(data: dict, skeleton: str, fallback: str, rationale: str) -> str:
    intake = data["intake"]
    channel = data["channel"]
    segment = data["segment"]
    score = qualification_score(data)
    if is_russian(data):
        return f"""---
artifact: funnel_blueprint
status: draft
---

# Blueprint воронки

## Резюме

- Оффер: {intake.get('offer', '')}
- ICP/персона: {intake.get('icp') or intake.get('primary_persona', '')}
- Целевой KPI: {intake.get('target_kpi', '')}
- Основной канал: {channel.get('primary_channel', '')}
- Qualification score: {score}/100

## Маршрутизация

- Основной skeleton: `{skeleton}`
- Запасной skeleton: `{fallback}`
- Логика выбора: {rationale}
- Awareness: {segment.get('awareness', 'unknown') or 'unknown'}
- Intent: {segment.get('intent', 'unknown') or 'unknown'}
- Value tier: {segment.get('value_tier', 'unknown') or 'unknown'}

## Путь воронки

1. Согласовать первое сообщение с каналом и ICP.
2. Собрать только тот контекст, который нужен для сегментации и первой рекомендации.
3. Показать конкретную диагностику с confidence и уровнем доказательств.
4. Дать один маршрут: self-serve, если ценность быстрая; assisted path, если setup долгий.
5. Инструментировать этапы до интерпретации эксперимента.

## Правило первой ценности

Цель - первая осмысленная ценность в рамках короткой сессии. Если реалистичный TTFV больше 5 минут, нужен demo, concierge setup или preview на sample data.

## Что проверить

- Доказательства достаточно сильные для обещания.
- Канал способен дать достаточно релевантного объема.
- Целевой KPI имеет baseline или может быть измерен до запуска.
"""
    return f"""---
artifact: funnel_blueprint
status: draft
---

# Funnel Blueprint

## Summary

- Offer: {intake.get('offer', '')}
- ICP/persona: {intake.get('icp') or intake.get('primary_persona', '')}
- Target KPI: {intake.get('target_kpi', '')}
- Primary channel: {channel.get('primary_channel', '')}
- Qualification score: {score}/100

## Routing

- Primary skeleton: `{skeleton}`
- Fallback skeleton: `{fallback}`
- Rationale: {rationale}
- Awareness: {segment.get('awareness', 'unknown') or 'unknown'}
- Intent: {segment.get('intent', 'unknown') or 'unknown'}
- Value tier: {segment.get('value_tier', 'unknown') or 'unknown'}

## Funnel Path

1. Match the entry message to the channel and ICP.
2. Capture only the context needed for segmentation and first recommendation.
3. Show a specific diagnosis with confidence and proof level.
4. Offer one roadmap path: self-serve if first value is fast, assisted if setup is slow.
5. Instrument each stage before running the experiment.

## First Value Rule

Target first meaningful value in one short session. If realistic TTFV exceeds 5 minutes, route to assisted demo, concierge setup, or sample-data preview.

## Assumptions To Verify

- Proof strength is sufficient for the promise being made.
- The selected channel can deliver enough qualified volume.
- The target KPI has a measurable baseline or can be instrumented before launch.
"""


def render_screen_specs(data: dict, skeleton: str) -> str:
    intake = data["intake"]
    if is_russian(data):
        lines = [
            "---",
            "artifact: screen_specs",
            "status: draft",
            "---",
            "",
            "# Спецификации экранов",
            "",
            f"Основной skeleton: `{skeleton}`",
            f"Целевой KPI: {intake.get('target_kpi', '')}",
            "",
            "| Этап | Сдвиг убеждения | Что показать | Primary CTA | Метрика успеха |",
            "| --- | --- | --- | --- | --- |",
        ]
    else:
        lines = [
        "---",
        "artifact: screen_specs",
        "status: draft",
        "---",
        "",
        "# Screen Specs",
        "",
        f"Primary skeleton: `{skeleton}`",
        f"Target KPI: {intake.get('target_kpi', '')}",
        "",
        "| Stage | Target belief | Show | Primary CTA | Success metric |",
        "| --- | --- | --- | --- | --- |",
        ]
    for stage, belief, show, cta, metric in SCREEN_STAGES:
        lines.append(f"| {stage} | {belief} | {show} | {cta} | `{metric}` |")
    if is_russian(data):
        lines.extend(
            [
                "",
                "## Направление микрокопи",
                "",
                "- Использовать язык оффера пользователя, а не общий маркетинговый текст.",
                "- Не делать proof-claims, которых нет в proof library.",
                "- Каждый экран держать вокруг одного belief shift и одного primary CTA.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Microcopy Direction",
                "",
                "- Use the user's own offer language where possible.",
                "- Avoid proof claims that are not present in the proof library.",
                "- Keep each screen tied to one belief shift and one primary CTA.",
            ]
        )
    return "\n".join(lines) + "\n"


def render_experiment_card(data: dict, skeleton: str) -> str:
    intake = data["intake"]
    channel = data["channel"]
    segment = data["segment"]
    if is_russian(data):
        return f"""---
artifact: experiment_card
status: draft
---

# Карточка эксперимента

## Setup

- Сегмент: {segment.get('persona_jtbd') or intake.get('primary_persona') or intake.get('icp')}
- Skeleton: `{skeleton}`
- Канал: {channel.get('primary_channel', '')}
- Изменяемый этап: Landing to brief start

## Гипотеза

Если первый экран точнее совпадает с болью, результатом и уровнем proof сегмента, больше релевантных посетителей начнут brief, потому что быстрее поймут "это про меня".

## Метрики

- Primary metric: {intake.get('target_kpi', '')}
- Stage proxy: `Brief Started / Landing Viewed`
- Guardrails: bounce proxy, low-quality starts, support contact rate

## Data Quality Checks

- SRM check до чтения результата.
- Exposure logging проверен для каждого eligible visitor.
- Event loss и duplicate event checks завершены.

## Decision Rule

Ship только если primary metric проходит practical threshold, guardrails не проседают, а качественные наблюдения не противоречат результату.
"""
    return f"""---
artifact: experiment_card
status: draft
---

# Experiment Card

## Setup

- Segment: {segment.get('persona_jtbd') or intake.get('primary_persona') or intake.get('icp')}
- Skeleton: `{skeleton}`
- Channel: {channel.get('primary_channel', '')}
- Primary stage changed: Landing to brief start

## Hypothesis

If the first screen matches the segment's pain, outcome, and proof level, then more qualified visitors will start the brief because the page will answer "is this for me?" faster.

## Metrics

- Primary metric: {intake.get('target_kpi', '')}
- Stage proxy: `Brief Started / Landing Viewed`
- Guardrails: bounce proxy, low-quality starts, support contact rate

## Data Quality Checks

- SRM check before reading results.
- Exposure logging verified for every eligible visitor.
- Event loss and duplicate event checks completed.

## Decision Rule

Ship only if the primary metric clears the practical threshold, guardrails do not degrade, and qualitative evidence does not contradict the result.
"""


def render_postmortem(language: str = "English") -> str:
    if language.lower() == "russian":
        return """---
artifact: postmortem_record
status: draft
---

# Postmortem Record

Experiment / Release ID:

Date range:

Owner:

Segment:

Skeleton:

Изменяемый этап:

## Гипотеза

## Change Log

## Data Quality Checks

- SRM status:
- Exposure logging status:
- Event loss / missing events:
- Guardrail alerts:

## Результаты

- Primary KPI:
- Guardrails:
- By segment / channel / persona:
- Time to first value:
- Monetization / retention deltas:

## Qualitative Evidence

## Root Cause Classification

Proposition / Segment / Skeleton / Screen-level UX / Instrumentation / Channel mismatch / Economics

## Decision

Ship / Hold / Kill / Re-test

## Permanent Learning

Какое routing rule, screen pattern, scoring rule или risk note нужно обновить навсегда?

## Follow-up

Owner:

Due date:
"""
    return """---
artifact: postmortem_record
status: draft
---

# Postmortem Record

Experiment / Release ID:

Date range:

Owner:

Segment:

Skeleton:

Primary stage changed:

## Hypothesis

## Change Log

## Data Quality Checks

- SRM status:
- Exposure logging status:
- Event loss / missing events:
- Guardrail alerts:

## Results

- Primary KPI:
- Guardrails:
- By segment / channel / persona:
- Time to first value:
- Monetization / retention deltas:

## Qualitative Evidence

## Root Cause Classification

Proposition / Segment / Skeleton / Screen-level UX / Instrumentation / Channel mismatch / Economics

## Decision

Ship / Hold / Kill / Re-test

## Permanent Learning

Which routing rule, screen pattern, scoring rule, or risk note changes permanently?

## Follow-up

Owner:

Due date:
"""


def md_cell(value: object) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def source_registry_markdown(data: dict, summary: dict) -> str:
    language = output_language(data)
    ru = language.lower() == "russian"
    title = "Research и evidence summary" if ru else "Research and Evidence Summary"
    lines = [
        f"# {title}",
        "",
        f"- {'Research readiness' if not ru else 'Research readiness'}: {summary['research_readiness_score']}/100",
        f"- {'Источников' if ru else 'Sources'}: {summary['source_count']}",
        f"- {'Конкурентов' if ru else 'Competitors'}: {summary['competitor_count']}",
        "",
        "## Evidence gaps" if not ru else "## Пробелы evidence",
        "",
    ]
    gaps = summary["evidence_gaps"] or []
    if gaps:
        lines.extend(f"- {localized_evidence_gap(str(gap), language)}" for gap in gaps)
    else:
        lines.append("- Нет" if ru else "- None")
    lines.extend(["", "## Sources" if not ru else "## Источники", ""])
    if not data["source_rows"]:
        lines.append(
            "Источники пока не добавлены. Агент может собрать их внешними инструментами и затем внести через ingest."
            if ru
            else "No sources have been added yet. The agent can collect them with external tools, then ingest them here."
        )
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "| Type | Title | Domain | URL | Confidence | Claim |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in data["source_rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.get("type")),
                    md_cell(row.get("title")),
                    md_cell(row.get("domain")),
                    md_cell(row.get("url")),
                    md_cell(row.get("confidence")),
                    md_cell(row.get("linked_claim")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def competitor_map_markdown(data: dict) -> str:
    language = output_language(data)
    ru = language.lower() == "russian"
    title = "Карта конкурентов" if ru else "Competitor Map"
    lines = [f"# {title}", ""]
    if not data["competitor_rows"]:
        lines.append(
            "Конкуренты пока не добавлены. Для v1 достаточно 3-7 конкурентов с pricing, positioning, CTA и onboarding evidence."
            if ru
            else "No competitors have been added yet. For v1, add 3-7 competitors with pricing, positioning, CTA, and onboarding evidence."
        )
        return "\n".join(lines) + "\n"
    if ru:
        lines.extend(
            [
                "| Конкурент | Domain | Positioning | Pricing | CTA | Onboarding | Proof | Source |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
    else:
        lines.extend(
            [
                "| Competitor | Domain | Positioning | Pricing | CTA | Onboarding | Proof | Source |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
    for row in data["competitor_rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.get("competitor")),
                    md_cell(row.get("domain")),
                    md_cell(row.get("positioning")),
                    md_cell(row.get("pricing")),
                    md_cell(row.get("primary_cta")),
                    md_cell(row.get("onboarding_pattern")),
                    md_cell(row.get("proof")),
                    md_cell(row.get("source")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def gap_map_markdown(data: dict, summary: dict) -> str:
    language = output_language(data)
    ru = language.lower() == "russian"
    title = "Gap map" if not ru else "Карта пробелов"
    lines = [
        f"# {title}",
        "",
        f"- {'Known sources' if not ru else 'Известные источники'}: {summary['source_count']}",
        f"- {'Known competitors' if not ru else 'Известные конкуренты'}: {summary['competitor_count']}",
        "",
        "## Evidence gaps" if not ru else "## Пробелы evidence",
        "",
    ]
    if summary["evidence_gaps"]:
        lines.extend(
            f"- {localized_evidence_gap(str(gap), language)}" for gap in summary["evidence_gaps"]
        )
    else:
        lines.append("- None" if not ru else "- Нет")
    lines.extend(["", "## Next collection" if not ru else "## Следующий сбор данных", ""])
    if summary["source_count"] == 0:
        lines.append(
            "- Add official site, pricing, docs, review, and case-study sources."
            if not ru
            else "- Добавить официальный сайт, pricing, docs, reviews и case-study sources."
        )
    if summary["competitor_count"] < 3:
        lines.append(
            "- Add 3-7 named competitors with source URLs."
            if not ru
            else "- Добавить 3-7 конкурентов с source URLs."
        )
    if not summary["evidence_gaps"]:
        lines.append(
            "- Evidence coverage is enough for a first funnel recommendation pass."
            if not ru
            else "- Evidence coverage достаточно для первого recommendation pass."
        )
    return "\n".join(lines) + "\n"


def execution_plan_markdown(data: dict, summary: dict, rendered: bool) -> str:
    language = output_language(data)
    ru = language.lower() == "russian"
    title = "Execution Plan"
    next_items = summary["next_best_input"] or (
        ["Review generated artifacts and prepare the next experiment."]
        if not ru
        else ["Проверить сгенерированные артефакты и подготовить следующий эксперимент."]
    )
    auto_collect: list[str] = []
    if summary["source_count"] == 0:
        auto_collect.append(
            "Collect current official/product/pricing/review sources and ingest URLs."
            if not ru
            else "Собрать текущие official/product/pricing/review sources и внести URLs."
        )
    if summary["competitor_count"] < 3:
        auto_collect.append(
            "Collect 3-7 competitor pages with pricing, CTA, onboarding, and proof notes."
            if not ru
            else "Собрать 3-7 competitor pages с pricing, CTA, onboarding и proof notes."
        )
    if not auto_collect:
        auto_collect.append(
            "No automatic collection blocker remains for v1."
            if not ru
            else "Для v1 не осталось блокирующего automatic collection."
        )
    lines = [
        "---",
        "artifact: execution_plan",
        "status: draft",
        "---",
        "",
        f"# {title}",
        "",
        "## Auto-collect" if not ru else "## Собрать автоматически",
        "",
    ]
    lines.extend(f"- {item}" for item in auto_collect)
    lines.extend(["", "## Ask user" if not ru else "## Спросить у пользователя", ""])
    lines.extend(f"- {item}" for item in next_items)
    lines.extend(["", "## Draft" if not ru else "## Собрать draft", ""])
    lines.append(
        "- Use the current funnel artifacts as draft recommendations."
        if rendered and not ru
        else "- Использовать текущие funnel artifacts как draft-рекомендации."
        if rendered
        else "- Keep recommendations blocked until the minimum gate is satisfied."
        if not ru
        else "- Держать рекомендации заблокированными, пока minimum gate не выполнен."
    )
    lines.extend(["", "## Verify" if not ru else "## Проверить", ""])
    lines.extend(
        [
            "- Confirm proof claims against source registry before publishing."
            if not ru
            else "- Проверить proof claims по source registry перед публикацией.",
            "- Confirm tracking events before interpreting experiment outcomes."
            if not ru
            else "- Проверить tracking events до интерпретации результатов эксперимента.",
        ]
    )
    return "\n".join(lines) + "\n"


def research_log_markdown(data: dict, summary: dict) -> str:
    language = output_language(data)
    ru = language.lower() == "russian"
    lines = [
        "---",
        "artifact: research_log",
        "status: draft",
        "---",
        "",
        "# Research Log",
        "",
        (
            "This skill made no network calls. It only normalized evidence that was provided by the user, agent, or external tooling."
            if not ru
            else "Этот skill не делал network calls. Он только нормализовал evidence, предоставленные пользователем, агентом или внешними инструментами."
        ),
        "",
        f"- Sources: {summary['source_count']}",
        f"- Competitors: {summary['competitor_count']}",
        f"- Research readiness: {summary['research_readiness_score']}/100",
        "",
        "## Conflicts" if not ru else "## Конфликты",
        "",
    ]
    if summary["contradictions"]:
        lines.extend(f"- {item}" for item in summary["contradictions"])
    else:
        lines.append("- None detected" if not ru else "- Не обнаружены")
    return "\n".join(lines) + "\n"


def write_research_artifacts(
    workspace: Path, data: dict, summary: dict, rendered: bool
) -> None:
    gaps = summary["evidence_gaps"]
    auto_collect = []
    if summary["source_count"] == 0:
        auto_collect.append("collect current source URLs")
    if summary["competitor_count"] < 3:
        auto_collect.append("collect 3-7 competitor benchmarks")
    ask_user = summary["next_best_input"]
    write_flat_yaml(
        workspace / GAP_FILE,
        {
            "known_sources_count": summary["source_count"],
            "known_competitors_count": summary["competitor_count"],
            "evidence_gaps": "; ".join(gaps) if gaps else "none",
            "auto_collect_next": "; ".join(auto_collect) if auto_collect else "none",
            "ask_user_next": "; ".join(ask_user) if ask_user else "none",
        },
        overwrite=True,
    )
    (workspace / "15_execution_plan.md").write_text(
        execution_plan_markdown(data, summary, rendered), encoding="utf-8"
    )
    (workspace / "16_research_log.md").write_text(
        research_log_markdown(data, summary), encoding="utf-8"
    )


def render_presentation(
    data: dict,
    summary: dict,
    rendered: bool,
    skeleton: str = "",
    fallback: str = "",
    rationale: str = "",
) -> str:
    ru = is_russian(data)
    intake = data["intake"]
    channel = data["channel"]
    segment = data["segment"]
    title = "Презентация growth funnel" if ru else "Growth Funnel Presentation"
    subtitle = (
        "Визуальный обзор workspace, статусов, маршрута и следующих действий."
        if ru
        else "Visual overview of the workspace, status, path, and next actions."
    )
    gate = "готов" if summary["minimum_gate_satisfied"] else "заблокирован"
    if not ru:
        gate = "satisfied" if summary["minimum_gate_satisfied"] else "blocked"
    missing_title = "Критично не хватает" if ru else "Critical Missing"
    next_title = "Следующий ввод" if ru else "Next Input"
    status_title = "Статус артефактов" if ru else "Artifact Status"
    path_title = "Маршрут" if ru else "Path"
    screens_title = "Этапы экранов" if ru else "Screen Stages"

    missing_items = "".join(
        f"<li>{escape(item)}</li>" for item in summary["critical_missing_fields"]
    ) or ("<li>Нет</li>" if ru else "<li>None</li>")
    next_items = "".join(f"<li>{escape(item)}</li>" for item in summary["next_best_input"]) or (
        "<li>Проверьте draft-артефакты и запускайте следующий шаг.</li>"
        if ru
        else "<li>Review draft artifacts and run the next operational step.</li>"
    )
    status_cards = "".join(
        f"<div class='artifact'><span>{escape(name)}</span><strong>{escape(status)}</strong></div>"
        for name, status in summary["artifact_status"].items()
    )
    screen_cards = "".join(
        f"<div class='stage'><strong>{escape(stage)}</strong><p>{escape(belief)}</p><small>{escape(metric)}</small></div>"
        for stage, belief, _show, _cta, metric in SCREEN_STAGES
    )

    skeleton_text = skeleton or segment.get("selected_skeleton", "") or "blocked"
    fallback_text = fallback or segment.get("fallback_skeleton", "") or "blocked"
    rationale_text = rationale or segment.get("routing_rationale", "") or (
        "Нужны минимальные вводные для выбора skeleton." if ru else "Minimum inputs needed."
    )

    return f"""<!doctype html>
<html lang="{'ru' if ru else 'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #172033; --muted: #5e6a7d; --line: #d9dee7; --bg: #f6f7f9; --panel: #fff; --accent: #0f766e; --warn: #a16207; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, Arial, sans-serif; color: var(--ink); background: var(--bg); }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }}
    section {{ margin: 0 0 18px; padding: 22px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }}
    h1, h2, h3 {{ margin: 0 0 10px; letter-spacing: 0; }}
    p {{ margin: 0 0 10px; color: var(--muted); line-height: 1.5; }}
    ul {{ margin: 8px 0 0 20px; padding: 0; }}
    li {{ margin: 5px 0; }}
    .hero {{ display: grid; gap: 18px; grid-template-columns: minmax(0, 1.3fr) minmax(260px, .7fr); align-items: stretch; }}
    .scores {{ display: grid; gap: 12px; grid-template-columns: repeat(3, 1fr); }}
    .score {{ padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: #fbfcfe; }}
    .score strong {{ display: block; font-size: 34px; line-height: 1; margin-bottom: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .artifact, .stage, .path {{ padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: #fbfcfe; }}
    .artifact {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; }}
    .artifact strong {{ color: var(--accent); }}
    .badge {{ display: inline-flex; padding: 5px 9px; border-radius: 999px; background: #e8f3f1; color: #115e59; font-size: 13px; }}
    .blocked {{ background: #fff7ed; color: #9a3412; }}
    .path strong, .stage strong {{ display: block; margin-bottom: 6px; }}
    small {{ color: var(--muted); }}
    @media (max-width: 760px) {{ main {{ padding: 18px 12px 40px; }} .hero {{ grid-template-columns: 1fr; }} .scores {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <span class="badge {'blocked' if not rendered else ''}">{escape(gate)}</span>
        <h1>{escape(title)}</h1>
        <p>{escape(subtitle)}</p>
        <p><strong>{'Оффер' if ru else 'Offer'}:</strong> {escape(str(intake.get('offer', '') or ''))}</p>
        <p><strong>{'Канал' if ru else 'Channel'}:</strong> {escape(str(channel.get('primary_channel', '') or ''))}</p>
      </div>
      <div class="scores">
        <div class="score"><strong>{summary['completeness_score']}</strong><span>Completeness</span></div>
        <div class="score"><strong>{summary['qualification_score']}</strong><span>Qualification</span></div>
        <div class="score"><strong>{summary['research_readiness_score']}</strong><span>Research</span></div>
      </div>
    </section>
    <section>
      <h2>{escape(path_title)}</h2>
      <div class="grid">
        <div class="path"><strong>Primary skeleton</strong><p>{escape(str(skeleton_text))}</p></div>
        <div class="path"><strong>Fallback skeleton</strong><p>{escape(str(fallback_text))}</p></div>
        <div class="path"><strong>Rationale</strong><p>{escape(str(rationale_text))}</p></div>
      </div>
    </section>
    <section>
      <h2>{escape(missing_title)}</h2>
      <ul>{missing_items}</ul>
    </section>
    <section>
      <h2>{escape(next_title)}</h2>
      <ul>{next_items}</ul>
    </section>
    <section>
      <h2>{escape(status_title)}</h2>
      <div class="grid">{status_cards}</div>
    </section>
    <section>
      <h2>{escape(screens_title)}</h2>
      <div class="grid">{screen_cards}</div>
    </section>
  </main>
</body>
</html>
"""


def strip_frontmatter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown.strip() + "\n"
    match = re.match(r"^---\n.*?\n---\n?", markdown, flags=re.DOTALL)
    if not match:
        return markdown.strip() + "\n"
    return markdown[match.end() :].strip() + "\n"


def table_to_html(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    html = ["<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">", "<thead><tr>"]
    html.extend(f"<th>{escape(cell)}</th>" for cell in header)
    html.append("</tr></thead><tbody>")
    for row in body:
        html.append("<tr>")
        html.extend(f"<td>{escape(cell)}</td>" for cell in row)
        html.append("</tr>")
    html.append("</tbody></table>")
    return "\n".join(html)


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html: list[str] = []
    in_ul = False
    in_ol = False
    in_pre = False
    table_lines: list[str] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html.append("</ul>")
            in_ul = False
        if in_ol:
            html.append("</ol>")
            in_ol = False

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            close_lists()
            html.append(table_to_html(table_lines))
            table_lines = []

    for line in lines:
        if line.startswith("```"):
            flush_table()
            close_lists()
            if in_pre:
                html.append("</code></pre>")
                in_pre = False
            else:
                html.append("<pre><code>")
                in_pre = True
            continue
        if in_pre:
            html.append(escape(line))
            continue
        if line.startswith("|") and line.endswith("|"):
            table_lines.append(line)
            continue
        flush_table()
        stripped = line.strip()
        if not stripped:
            close_lists()
            continue
        if stripped.startswith("# "):
            close_lists()
            html.append(f"<h1>{escape(stripped[2:].strip())}</h1>")
        elif stripped.startswith("## "):
            close_lists()
            html.append(f"<h2>{escape(stripped[3:].strip())}</h2>")
        elif stripped.startswith("### "):
            close_lists()
            html.append(f"<h3>{escape(stripped[4:].strip())}</h3>")
        elif stripped.startswith("- "):
            if not in_ul:
                close_lists()
                html.append("<ul>")
                in_ul = True
            html.append(f"<li>{escape(stripped[2:].strip())}</li>")
        elif re.match(r"^\d+\.\s+", stripped):
            if not in_ol:
                close_lists()
                html.append("<ol>")
                in_ol = True
            html.append(f"<li>{escape(re.sub(r'^\d+\.\s+', '', stripped))}</li>")
        else:
            close_lists()
            html.append(f"<p>{escape(stripped)}</p>")
    flush_table()
    close_lists()
    if in_pre:
        html.append("</code></pre>")
    return "\n".join(html)


def html_page(title: str, markdown: str, language: str, nav: list[tuple[str, str]]) -> str:
    nav_links = " | ".join(
        f'<a href="{escape(filename)}">{escape(label)}</a>' for filename, label in nav
    )
    return f"""<!doctype html>
<html lang="{'ru' if language.lower() == 'russian' else 'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
</head>
<body>
  <nav>{nav_links}</nav>
  <main>
{markdown_to_html(markdown)}
  </main>
</body>
</html>
"""


def read_clean_markdown(workspace: Path, filename: str) -> str:
    path = workspace / filename
    if not path.exists():
        return ""
    return strip_frontmatter(path.read_text(encoding="utf-8"))


def tracking_plan_markdown(workspace: Path, language: str) -> str:
    ru = language.lower() == "russian"
    path = workspace / "08_tracking_plan.csv"
    title = "План трекинга" if ru else "Tracking Plan"
    if not path.exists():
        message = (
            "События пока не сгенерированы."
            if ru
            else "No tracking events have been generated yet."
        )
        return f"# {title}\n\n{message}\n"
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if any((value or "").strip() for value in row.values()):
                rows.append(row)
    if not rows:
        message = (
            "События пока не сгенерированы."
            if ru
            else "No tracking events have been generated yet."
        )
        return f"# {title}\n\n{message}\n"
    headers = [
        "event_name",
        "stage",
        "purpose",
        "primary_metric",
        "guardrail",
        "status",
    ]
    if ru:
        table_header = "| Событие | Этап | Назначение | Основная метрика | Ограничение | Статус |"
    else:
        table_header = "| Event | Stage | Purpose | Primary metric | Guardrail | Status |"
    lines = [f"# {title}", "", table_header, "| --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(row.get(header, "")).replace("|", "/") for header in headers)
            + " |"
        )
    return "\n".join(lines) + "\n"


def status_markdown(summary: dict, language: str) -> str:
    ru = language.lower() == "russian"
    title = "Статус и следующие шаги" if ru else "Status and Next Steps"
    missing_title = "Критично не хватает" if ru else "Critical missing"
    next_title = "Следующий ввод" if ru else "Next input"
    completeness_label = "Оценка полноты" if ru else "Completeness score"
    qualification_label = "Оценка квалификации" if ru else "Qualification score"
    decision_label = "Решение" if ru else "Decision"
    gate_label = "Минимальный набор вводных" if ru else "Minimum input gate"
    gate_value = (
        "собран"
        if summary["minimum_gate_satisfied"] and ru
        else "заблокирован"
        if ru
        else "satisfied"
        if summary["minimum_gate_satisfied"]
        else "blocked"
    )
    missing = [
        localized_missing_field(str(item), language)
        for item in summary["critical_missing_fields"]
    ] or (["Нет"] if ru else ["None"])
    next_items = summary["next_best_input"] or (
        ["Блокирующих вводных не осталось. Изучите документы в этой папке."]
        if ru
        else ["No blocking input remains. Review the documents in this folder."]
    )
    lines = [
        f"# {title}",
        "",
        f"- {completeness_label}: {summary['completeness_score']}/100",
        f"- {qualification_label}: {summary['qualification_score']}/100",
        f"- {decision_label}: {localized_decision(str(summary['decision']), language)}",
        f"- {gate_label}: {gate_value}",
        "",
        f"## {missing_title}",
        "",
    ]
    lines.extend(f"- {item}" for item in missing)
    lines.extend(["", f"## {next_title}", ""])
    lines.extend(f"- {item}" for item in next_items)
    return "\n".join(lines) + "\n"


def index_markdown(language: str, docs: list[tuple[str, str, str]]) -> str:
    ru = language.lower() == "russian"
    title = "Итоговый пакет" if ru else "Final Pack"
    intro = (
        "Эта папка содержит только итоговые документы для чтения: Markdown и HTML-страницу к каждому документу. Сырые YAML/CSV остаются уровнем агента в корне workspace."
        if ru
        else "This folder contains only the readable final output: Markdown documents and one HTML page per document. Raw YAML/CSV files stay in the workspace root for the agent."
    )
    order_title = "Читать по порядку" if ru else "Read in order"
    lines = [f"# {title}", "", intro, "", f"## {order_title}", ""]
    for md_name, html_name, label in docs:
        lines.append(f"- `{md_name}` / `{html_name}` - {label}")
    return "\n".join(lines) + "\n"


def write_final_pack(
    workspace: Path,
    data: dict,
    summary: dict,
    rendered: bool,
    skeleton: str = "",
    fallback: str = "",
    rationale: str = "",
) -> Path:
    language = output_language(data)
    ru = language.lower() == "russian"
    final_dir = workspace / "final"
    final_dir.mkdir(exist_ok=True)
    for child in final_dir.iterdir():
        if child.is_file():
            child.unlink()

    doc_specs: list[tuple[str, str, str]] = []
    doc_specs.append(
        (
            "01_status_next_steps",
            "Статус и следующие шаги" if ru else "Status and Next Steps",
            status_markdown(summary, language),
        )
    )
    doc_specs.append(
        (
            "02_funnel_blueprint",
            "Blueprint воронки" if ru else "Funnel Blueprint",
            read_clean_markdown(workspace, "06_funnel_blueprint.md"),
        )
    )
    doc_specs.append(
        (
            "03_screen_specs",
            "Спецификации экранов" if ru else "Screen Specs",
            read_clean_markdown(workspace, "07_screen_specs.md"),
        )
    )
    doc_specs.append(
        (
            "04_tracking_plan",
            "План трекинга" if ru else "Tracking Plan",
            tracking_plan_markdown(workspace, language),
        )
    )
    doc_specs.append(
        (
            "05_experiment_card",
            "Карточка эксперимента" if ru else "Experiment Card",
            read_clean_markdown(workspace, "09_experiment_card.md"),
        )
    )
    doc_specs.append(
        (
            "06_postmortem_template",
            "Шаблон postmortem" if ru else "Postmortem Template",
            read_clean_markdown(workspace, "10_postmortem_record.md"),
        )
    )
    doc_specs.append(
        (
            "07_research_evidence",
            "Research и evidence" if ru else "Research and Evidence",
            source_registry_markdown(data, summary),
        )
    )
    doc_specs.append(
        (
            "08_competitor_map",
            "Карта конкурентов" if ru else "Competitor Map",
            competitor_map_markdown(data),
        )
    )
    doc_specs.append(
        (
            "09_gap_map",
            "Карта пробелов" if ru else "Gap Map",
            gap_map_markdown(data, summary),
        )
    )
    doc_specs.append(
        (
            "10_execution_plan",
            "Execution Plan",
            read_clean_markdown(workspace, "15_execution_plan.md"),
        )
    )

    docs = [(f"{slug}.md", f"{slug}.html", title) for slug, title, _markdown in doc_specs]
    index_body = index_markdown(language, docs)
    (final_dir / "00_index.md").write_text(index_body, encoding="utf-8")

    index_title = "Оглавление" if ru else "Index"
    nav = [("00_index.html", index_title)] + [
        (html_name, title) for _md_name, html_name, title in docs
    ]
    (final_dir / "00_index.html").write_text(
        html_page(index_title, index_body, language, nav), encoding="utf-8"
    )
    (final_dir / "index.html").write_text(
        html_page(index_title, index_body, language, nav), encoding="utf-8"
    )

    for slug, title, markdown in doc_specs:
        md_name = f"{slug}.md"
        html_name = f"{slug}.html"
        body = markdown.strip() + "\n"
        if not body.strip():
            body = f"# {title}\n\n{'Пока нет данных.' if ru else 'No data yet.'}\n"
        (final_dir / md_name).write_text(body, encoding="utf-8")
        (final_dir / html_name).write_text(
            html_page(title, body, language, nav), encoding="utf-8"
        )
    return final_dir


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        ensure_workspace(workspace)
        data = load_workspace(workspace)
        missing = critical_missing_fields(data)
        language = output_language(data)
        if not minimum_gate_satisfied(data):
            (workspace / "06_funnel_blueprint.md").write_text(
                blocked_markdown(
                    "funnel_blueprint",
                    "Blueprint воронки" if language == "Russian" else "Funnel Blueprint",
                    missing,
                    language,
                ),
                encoding="utf-8",
            )
            (workspace / "07_screen_specs.md").write_text(
                blocked_markdown(
                    "screen_specs",
                    "Спецификации экранов" if language == "Russian" else "Screen Specs",
                    missing,
                    language,
                ),
                encoding="utf-8",
            )
            (workspace / "09_experiment_card.md").write_text(
                blocked_markdown(
                    "experiment_card",
                    "Карточка эксперимента" if language == "Russian" else "Experiment Card",
                    missing,
                    language,
                ),
                encoding="utf-8",
            )
            summary = validate_and_write_status(workspace)
            write_research_artifacts(workspace, data, summary, rendered=False)
            data = load_workspace(workspace)
            summary = validate_and_write_status(workspace)
            (workspace / "11_presentation.html").write_text(
                render_presentation(data, summary, rendered=False), encoding="utf-8"
            )
            final_dir = write_final_pack(data["workspace"], data, summary, rendered=False)
            summary["presentation_path"] = str(workspace / "11_presentation.html")
            summary["final_dir"] = str(final_dir)
            summary["final_index_path"] = str(final_dir / "index.html")
            print(json.dumps({"rendered": False, "summary": summary}, indent=2, sort_keys=True))
            return 0

        skeleton, fallback, rationale = select_skeleton(data)
        write_flat_yaml(
            workspace / SEGMENT_FILE,
            {
                "selected_skeleton": skeleton,
                "fallback_skeleton": fallback,
                "routing_rationale": rationale,
            },
            overwrite=False,
        )
        data = load_workspace(workspace)
        (workspace / "06_funnel_blueprint.md").write_text(
            render_blueprint(data, skeleton, fallback, rationale), encoding="utf-8"
        )
        (workspace / "07_screen_specs.md").write_text(
            render_screen_specs(data, skeleton), encoding="utf-8"
        )
        append_csv_rows(
            workspace / "08_tracking_plan.csv",
            [
                "event_name",
                "stage",
                "purpose",
                "required_properties",
                "primary_metric",
                "guardrail",
                "owner",
                "status",
            ],
            TRACKING_ROWS,
        )
        (workspace / "09_experiment_card.md").write_text(
            render_experiment_card(data, skeleton), encoding="utf-8"
        )
        (workspace / "10_postmortem_record.md").write_text(
            render_postmortem(language), encoding="utf-8"
        )
        summary = validate_and_write_status(workspace)
        write_research_artifacts(workspace, data, summary, rendered=True)
        data = load_workspace(workspace)
        summary = validate_and_write_status(workspace)
        (workspace / "11_presentation.html").write_text(
            render_presentation(data, summary, rendered=True, skeleton=skeleton, fallback=fallback, rationale=rationale),
            encoding="utf-8",
        )
        final_dir = write_final_pack(
            workspace,
            data,
            summary,
            rendered=True,
            skeleton=skeleton,
            fallback=fallback,
            rationale=rationale,
        )
        summary["presentation_path"] = str(workspace / "11_presentation.html")
        summary["final_dir"] = str(final_dir)
        summary["final_index_path"] = str(final_dir / "index.html")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"rendered": True, "summary": summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
