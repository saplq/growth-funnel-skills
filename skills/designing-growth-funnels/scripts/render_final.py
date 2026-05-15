#!/usr/bin/env python3
"""Render the clean user-facing final pack."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any

from workspace_lib import (
    FINAL_PAGES,
    clean_final_dir,
    ensure_workspace,
    final_dir,
    final_leakage,
    is_russian,
    load_workspace,
    minimum_gate_satisfied,
    numeric_value,
    output_language,
    validate_and_write,
    write_final_page,
    write_text_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render clean Markdown and HTML pages into final/.")
    parser.add_argument("workspace_dir", help="Workspace directory to render.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def dash(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text or "-"


def table_cell(value: Any) -> str:
    return dash(value).replace("|", "/")


def yes_no(value: bool, ru: bool) -> str:
    return ("да" if value else "нет") if ru else ("yes" if value else "no")


def nav_titles(data: dict[str, Any]) -> list[tuple[str, str]]:
    topics = data.get("topics", [])
    topic_titles = {
        str(item.get("topic_id", "")): str(item.get("title", ""))
        for item in topics
        if isinstance(item, dict)
    }
    mapping = {
        "00_index": "index",
        "01_status_next_steps": "status_next_steps",
        "02_intake_brief": "intake_brief",
        "03_research_evidence": "research_evidence",
        "04_competitor_map": "competitor_map",
        "05_funnel_blueprint": "funnel_blueprint",
        "06_screen_specs": "screen_specs",
        "07_tracking_plan": "tracking_plan",
        "08_experiment_card": "experiment_card",
        "09_risks_and_gaps": "risks_and_gaps",
        "10_execution_plan": "execution_plan",
    }
    return [(slug, topic_titles.get(mapping.get(slug, ""), title)) for slug, title in FINAL_PAGES]


def select_skeleton(data: dict[str, Any]) -> tuple[str, str]:
    intake = data["intake"]
    ttfv = numeric_value(intake.get("time_to_first_value_minutes"))
    text = " ".join(
        str(intake.get(field, ""))
        for field in ["offer", "sales_motion", "primary_channel", "pricing", "product_constraints"]
    ).lower()
    if "enterprise" in text or "sales" in text or (ttfv is not None and ttfv > 10):
        return "demo_led", "High value or longer setup needs assisted trust-building before activation."
    if "audit" in text or "diagnos" in text or "assessment" in text or "аудит" in text:
        return "diagnostic_to_roadmap", "The funnel should create first value through diagnosis and a prioritized path."
    if ttfv is not None and ttfv <= 5:
        return "trial_to_value", "Fast first value supports a product-led trial-to-value path."
    return "diagnostic_to_roadmap", "Default to diagnosis-first until first-value timing is proven."


def render_index(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    state = data["state"]
    if ru:
        return f"""# Итоговый пакет

Этот пакет собран из `runtime/` и предназначен для чтения человеком.

## Читать по порядку

- Статус и следующие шаги
- Intake brief
- Research и evidence
- Карта конкурентов
- Blueprint воронки
- Спецификация экранов
- План трекинга
- Карточка эксперимента
- Риски и gaps
- План исполнения

## Текущее состояние

- Minimum gate: {yes_no(state.get('minimum_gate_satisfied', False), ru)}
- Completeness score: {state.get('scores', {}).get('completeness', 0)}/100
- Qualification score: {state.get('scores', {}).get('qualification', 0)}/100
- Research readiness score: {state.get('scores', {}).get('research_readiness', 0)}/100
"""
    return f"""# Final Pack

This package is compiled from `runtime/` for human review.

## Read in Order

- Status and next steps
- Intake brief
- Research evidence
- Competitor map
- Funnel blueprint
- Screen specs
- Tracking plan
- Experiment card
- Risks and gaps
- Execution plan

## Current State

- Minimum gate: {yes_no(state.get('minimum_gate_satisfied', False), ru)}
- Completeness score: {state.get('scores', {}).get('completeness', 0)}/100
- Qualification score: {state.get('scores', {}).get('qualification', 0)}/100
- Research readiness score: {state.get('scores', {}).get('research_readiness', 0)}/100
"""


def render_status(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    state = data["state"]
    missing = state.get("critical_missing_fields", [])
    gaps = state.get("evidence_gaps", [])
    next_input = state.get("next_best_input", [])
    artifact_status = state.get("artifact_status", {})
    if ru:
        return f"""# Статус и следующие шаги

## Scores

- Оценка полноты: {state.get('scores', {}).get('completeness', 0)}/100
- Qualification score: {state.get('scores', {}).get('qualification', 0)}/100
- Research readiness score: {state.get('scores', {}).get('research_readiness', 0)}/100
- Minimum gate: {yes_no(state.get('minimum_gate_satisfied', False), ru)}
- Decision: `{state.get('decision', '-')}`

## Не хватает

{bullet_list(missing, '-')}

## Evidence gaps

{bullet_list(gaps, '-')}

## Artifact status

{dict_table(artifact_status, 'Artifact', 'Status')}

## Следующий ввод

{bullet_list(next_input, '-')}
"""
    return f"""# Status and Next Steps

## Scores

- Completeness score: {state.get('scores', {}).get('completeness', 0)}/100
- Qualification score: {state.get('scores', {}).get('qualification', 0)}/100
- Research readiness score: {state.get('scores', {}).get('research_readiness', 0)}/100
- Minimum gate: {yes_no(state.get('minimum_gate_satisfied', False), ru)}
- Decision: `{state.get('decision', '-')}`

## Missing

{bullet_list(missing, '-')}

## Evidence Gaps

{bullet_list(gaps, '-')}

## Artifact Status

{dict_table(artifact_status, 'Artifact', 'Status')}

## Next Input

{bullet_list(next_input, '-')}
"""


def render_intake(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    intake = data["intake"]
    fields = [
        ("Project", intake.get("project_name")),
        ("Offer", intake.get("offer")),
        ("ICP", intake.get("icp")),
        ("Primary persona", intake.get("primary_persona")),
        ("JTBD", intake.get("jtbd")),
        ("Target KPI", intake.get("target_kpi")),
        ("Primary channel", intake.get("primary_channel")),
        ("Pricing", intake.get("pricing")),
        ("TTFV minutes", intake.get("time_to_first_value_minutes")),
        ("Sales motion", intake.get("sales_motion")),
        ("Constraints", intake.get("product_constraints")),
        ("Output language", intake.get("output_language")),
    ]
    proof_assets = intake.get("proof_assets") if isinstance(intake.get("proof_assets"), list) else []
    metrics = intake.get("metrics") if isinstance(intake.get("metrics"), list) else []
    title = "Intake brief" if not ru else "Intake brief"
    return f"""# {title}

## Normalized Context

{rows_table(fields, 'Field', 'Value')}

## Proof State

- Explicit no proof yet: {yes_no(bool(intake.get('explicit_no_proof_yet')), ru)}
- Proof assets:

{bullet_list(proof_assets, '-')}

## Metrics

{metrics_table(metrics)}
"""


def render_research(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    sources = data["sources"]
    results = data["agent_results"]
    title = "Research и evidence summary" if ru else "Research Evidence Summary"
    return f"""# {title}

## Source Registry

{source_table(sources)}

## Specialist Results

{agent_results_section(results)}

## Research Rule

Pricing, changelog, and current-practice claims require retrieval dates. Missing dates remain evidence gaps instead of being treated as current facts.
"""


def render_competitors(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    title = "Карта конкурентов" if ru else "Competitor Map"
    competitors = data["competitors"]
    return f"""# {title}

{competitor_table(competitors)}

## Interpretation

Use competitor rows as observed evidence only. Do not copy competitor claims into recommendations unless the source and retrieval date are present.
"""


def render_blueprint(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    intake = data["intake"]
    gate = minimum_gate_satisfied(intake)
    skeleton, rationale = select_skeleton(data)
    fallback = "diagnostic_to_roadmap" if skeleton != "diagnostic_to_roadmap" else "demo_led"
    blocked = "" if gate else "\n## Blocked\n\nFinal recommendations are blocked until the minimum gate is satisfied.\n"
    if ru:
        blocked = "" if gate else "\n## Заблокировано\n\nФинальные рекомендации заблокированы, пока не выполнен minimum gate.\n"
        return f"""# Blueprint воронки

## Резюме

- Оффер: {dash(intake.get('offer'))}
- ICP/персона: {dash(intake.get('icp') or intake.get('primary_persona'))}
- Target KPI: {dash(intake.get('target_kpi'))}
- Канал: {dash(intake.get('primary_channel'))}
- Skeleton: `{skeleton}`
- Fallback: `{fallback}`
- Логика: {rationale}
{blocked}
## Путь

1. Согласовать сообщение с каналом и ICP.
2. Собрать минимальный brief для сегментации.
3. Показать diagnosis или preview первой ценности.
4. Выбрать self-serve или assisted path по TTFV и уровню доверия.
5. Инструментировать события до запуска эксперимента.
"""
    return f"""# Funnel Blueprint

## Summary

- Offer: {dash(intake.get('offer'))}
- ICP/persona: {dash(intake.get('icp') or intake.get('primary_persona'))}
- Target KPI: {dash(intake.get('target_kpi'))}
- Channel: {dash(intake.get('primary_channel'))}
- Skeleton: `{skeleton}`
- Fallback: `{fallback}`
- Rationale: {rationale}
{blocked}
## Path

1. Match message to channel and ICP.
2. Collect the minimum brief for segmentation.
3. Show diagnosis or first-value preview.
4. Choose self-serve or assisted path by TTFV and trust requirement.
5. Instrument events before interpreting experiments.
"""


def render_screen_specs(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    title = "Спецификация экранов" if ru else "Screen Specs"
    gate = minimum_gate_satisfied(data["intake"])
    blocked = ""
    if not gate:
        blocked = (
            "Status: blocked until the minimum gate is satisfied. Treat the table below as a generic draft scaffold, not a ready recommendation.\n\n"
            if not ru
            else "Статус: заблокировано до выполнения minimum gate. Таблица ниже является черновым scaffold, а не готовой рекомендацией.\n\n"
        )
    rows = [
        ("Landing", "This is for my situation.", "Pain/outcome hero, proof band, result preview.", "Start brief", "Brief Started / Landing Viewed"),
        ("Brief", "The system understands context.", "3-7 adaptive questions with progress.", "Continue diagnosis", "Brief Completed / Brief Started"),
        ("Diagnosis", "The problem is specific and fixable.", "Ranked gaps, severity, confidence.", "Build my plan", "Roadmap Viewed / Diagnosis Generated"),
        ("Roadmap", "There is a credible route to value.", "Quick win and 7/30/90 path.", "Start the plan", "Onboarding Started / Roadmap Viewed"),
        ("Onboarding", "Value can happen quickly.", "One task, prefill/sample data, contextual help.", "Create first result", "First Value Reached / Onboarding Started"),
        ("Paywall", "Payment follows value.", "Outcome-based plans, proof, preserved state.", "Choose plan", "Payment Completed / Checkout Started"),
        ("Retention", "Returning creates new value.", "Weekly insight and one recommended action.", "Run next improvement", "D7/D30 retention"),
    ]
    return f"""# {title}

{blocked}
| Stage | Target belief | Content | CTA | Primary metric |
| --- | --- | --- | --- | --- |
{chr(10).join(f"| {table_cell(a)} | {table_cell(b)} | {table_cell(c)} | {table_cell(d)} | {table_cell(e)} |" for a, b, c, d, e in rows)}
"""


def render_tracking(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    intake = data["intake"]
    gate = minimum_gate_satisfied(intake)
    target_kpi = dash(intake.get("target_kpi"))
    blocked = ""
    if not gate:
        blocked = (
            "Status: blocked until the target KPI, audience, channel, offer, and proof state are known. Use this only as an instrumentation scaffold.\n\n"
            if not ru
            else "Статус: заблокировано, пока неизвестны target KPI, аудитория, канал, оффер и proof state. Используйте это только как scaffold для instrumentation.\n\n"
        )
    headers = ("Событие", "Этап", "Назначение", "Primary metric", "Guardrail") if ru else ("Event", "Stage", "Purpose", "Primary metric", "Guardrail")
    rows = [
        ("Landing Viewed", "Landing", "Qualified exposure", "Brief Started / Landing Viewed", "bounce proxy"),
        ("Brief Started", "Brief", "Message-to-diagnostic intent", "Brief Started / Landing Viewed", "low-quality starts"),
        ("Brief Completed", "Brief", "Required context capture", "Brief Completed / Brief Started", "completion time"),
        ("Diagnosis Generated", "Diagnosis", "Segment-specific insight", "Roadmap Viewed / Diagnosis Generated", "fallback diagnosis rate"),
        ("First Value Reached", "Onboarding", "First meaningful outcome", "First Value Reached / Onboarding Started", "support contact rate"),
        ("Payment Completed", "Paywall", "Monetization after value", "Payment Completed / Checkout Started", "refund/payment error rate"),
        ("Experiment Exposed", "Experiment", "Trustworthy exposure logging", target_kpi, "SRM/event loss"),
    ]
    return f"""# {"План трекинга" if ru else "Tracking Plan"}

{blocked}
| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |
| --- | --- | --- | --- | --- |
{chr(10).join(f"| {table_cell(a)} | {table_cell(b)} | {table_cell(c)} | {table_cell(d)} | {table_cell(e)} |" for a, b, c, d, e in rows)}
"""


def render_experiment(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    intake = data["intake"]
    gate = minimum_gate_satisfied(intake)
    title = "Карточка эксперимента" if ru else "Experiment Card"
    if not gate:
        missing = data["state"].get("critical_missing_fields", [])
        return f"""# {title}

Status: blocked

## Missing

{bullet_list(missing, '-')}
"""
    skeleton, _ = select_skeleton(data)
    return f"""# {title}

## Hypothesis

If the `{skeleton}` path aligns the promise, brief, and first-value moment, then `{dash(intake.get('target_kpi'))}` will improve for `{dash(intake.get('icp') or intake.get('primary_persona'))}` from `{dash(intake.get('primary_channel'))}`.

## Primary Metric

{dash(intake.get('target_kpi'))}

## Guardrail

Support contact rate, event loss, payment errors, and low-quality starts must not degrade materially.

## Decision Rule

Ship only when exposure logging is clean, the primary metric clears the practical threshold, guardrails hold, and qualitative evidence does not contradict the result.
"""


def render_gaps(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    gaps = data["gaps"]
    title = "Риски и gaps" if ru else "Risks and Gaps"
    return f"""# {title}

## Missing Fields

{bullet_list(gaps.get('missing_fields', []), '-')}

## Evidence Gaps

{bullet_list(gaps.get('evidence_gaps', []), '-')}

## Conflicts

{bullet_list(gaps.get('conflicts', []), '-')}

## Blocked Recommendations

{bullet_list(gaps.get('blocked_recommendations', []), '-')}
"""


def render_execution(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    gaps = data["gaps"]
    title = "План исполнения" if ru else "Execution Plan"
    auto_title = "Auto-collect" if not ru else "Auto-collect"
    ask_title = "Ask user" if not ru else "Спросить пользователя"
    return f"""# {title}

## {auto_title}

{bullet_list(gaps.get('auto_collect', []), '-')}

## {ask_title}

{bullet_list(gaps.get('ask_user', []), '-')}

## Verify

- Re-run `validate_workspace.py`.
- Re-render `final/`.
- Check that no raw runtime files leaked into `final/`.
"""


def bullet_list(values: Any, fallback: str) -> str:
    if not values:
        return f"- {fallback}"
    if isinstance(values, dict):
        values = [f"{key}: {value}" for key, value in values.items()]
    return "\n".join(f"- {dash(value)}" for value in values)


def dict_table(values: dict[str, Any], key_label: str, value_label: str) -> str:
    if not values:
        return f"| {key_label} | {value_label} |\n| --- | --- |\n| - | - |"
    rows = "\n".join(f"| {table_cell(key)} | {table_cell(value)} |" for key, value in values.items())
    return f"| {key_label} | {value_label} |\n| --- | --- |\n{rows}"


def rows_table(rows: list[tuple[str, Any]], key_label: str, value_label: str) -> str:
    body = "\n".join(f"| {table_cell(key)} | {table_cell(value)} |" for key, value in rows)
    return f"| {key_label} | {value_label} |\n| --- | --- |\n{body}"


def metrics_table(metrics: Any) -> str:
    if not metrics:
        return "| Metric | Value | Source | Notes |\n| --- | --- | --- | --- |\n| - | - | - | - |"
    rows = []
    for metric in metrics:
        if isinstance(metric, dict):
            rows.append(f"| {table_cell(metric.get('metric_name'))} | {table_cell(metric.get('value'))} | {table_cell(metric.get('source'))} | {table_cell(metric.get('notes'))} |")
        else:
            rows.append(f"| raw_metric | - | ingested_notes | {table_cell(metric)} |")
    return "| Metric | Value | Source | Notes |\n| --- | --- | --- | --- |\n" + "\n".join(rows)


def source_table(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "| Title | Type | Publisher | Retrieved | Freshness | Confidence | Used in | URL |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - | - | - |"
    rows = []
    for source in sources:
        used_in = source.get("used_in", [])
        used_in_text = ", ".join(str(item) for item in used_in) if isinstance(used_in, list) else dash(used_in)
        rows.append(
            f"| {table_cell(source.get('title'))} | {table_cell(source.get('source_type'))} | {table_cell(source.get('publisher'))} | {table_cell(source.get('retrieved_at'))} | {table_cell(source.get('freshness'))} | {table_cell(source.get('confidence'))} | {table_cell(used_in_text)} | {table_cell(source.get('url'))} |"
        )
    return "| Title | Type | Publisher | Retrieved | Freshness | Confidence | Used in | URL |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(rows)


def competitor_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "| Competitor | Positioning | Pricing | CTA | Onboarding | Retrieved | Confidence | Source |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('competitor'))} | {table_cell(row.get('positioning'))} | {table_cell(row.get('pricing'))} | {table_cell(row.get('primary_cta'))} | {table_cell(row.get('onboarding_pattern'))} | {table_cell(row.get('retrieved_at'))} | {table_cell(row.get('confidence'))} | {table_cell(row.get('source'))} |"
        for row in rows
    )
    return "| Competitor | Positioning | Pricing | CTA | Onboarding | Retrieved | Confidence | Source |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n" + body


def agent_results_section(results: list[dict[str, Any]]) -> str:
    if not results:
        return "- No specialist results recorded yet."
    sections = []
    for result in results:
        findings = bullet_list(result.get("key_findings", []), "-")
        sections.append(
            f"### {dash(result.get('role'))}: {dash(result.get('topic_id'))}\n\n"
            f"{dash(result.get('summary'))}\n\n"
            f"Findings:\n\n{findings}\n\n"
            f"Confidence: {dash(result.get('confidence'))}"
        )
    return "\n\n".join(sections)


def write_index_html(workspace: Path, data: dict[str, Any], nav: list[tuple[str, str]]) -> None:
    ru = is_russian(data)
    links = "\n".join(
        f'<a class="index-card" href="{escape(slug)}.html"><span>{number + 1:02d}</span>{escape(title)}</a>'
        for number, (slug, title) in enumerate(nav)
    )
    title = "Оглавление" if ru else "Index"
    start = "Начать" if ru else "Start"
    lang = "ru" if ru else "en"
    html = f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f7f9fb; color: #17202a; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 48px 24px 80px; }}
    h1 {{ font-size: 42px; margin: 0 0 12px; }}
    p {{ color: #627386; font-size: 18px; }}
    .index-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 28px; }}
    .index-card {{ display: flex; gap: 12px; align-items: center; min-height: 78px; padding: 16px; background: #fff; border: 1px solid #d9e0e7; border-radius: 8px; color: inherit; text-decoration: none; }}
    .index-card:hover {{ border-color: #0f766e; }}
    .index-card span {{ color: #0f766e; font-weight: 700; }}
    .start {{ display: inline-block; margin-top: 24px; color: #fff; background: #0f766e; padding: 11px 15px; border-radius: 6px; text-decoration: none; }}
  </style>
</head>
<body>
  <main>
    <h1>{escape(title)}</h1>
    <p>{'Чистый финальный пакет по growth funnel workspace.' if ru else 'Clean final package for the growth funnel workspace.'}</p>
    <a class="start" href="00_index.html">{start}</a>
    <div class="index-grid">
      {links}
    </div>
  </main>
</body>
</html>
"""
    write_text_file(final_dir(workspace) / "index.html", html)


def render_pages(workspace: Path) -> dict[str, Any]:
    validate_and_write(workspace)
    data = load_workspace(workspace)
    clean_final_dir(workspace)
    nav = nav_titles(data)
    page_builders = {
        "00_index": render_index,
        "01_status_next_steps": render_status,
        "02_intake_brief": render_intake,
        "03_research_evidence": render_research,
        "04_competitor_map": render_competitors,
        "05_funnel_blueprint": render_blueprint,
        "06_screen_specs": render_screen_specs,
        "07_tracking_plan": render_tracking,
        "08_experiment_card": render_experiment,
        "09_risks_and_gaps": render_gaps,
        "10_execution_plan": render_execution,
    }
    for slug, title in nav:
        markdown = page_builders[slug](data)
        write_final_page(workspace, slug, title, markdown, nav, output_language(data))
    write_index_html(workspace, data, nav)
    summary = validate_and_write(workspace)
    leaks = final_leakage(workspace)
    summary["rendered"] = True
    summary["recommendations_ready"] = bool(summary["minimum_gate_satisfied"])
    summary["final_index_path"] = str(final_dir(workspace) / "index.html")
    summary["final_leakage"] = leaks
    return summary


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        ensure_workspace(workspace)
        summary = render_pages(workspace)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
