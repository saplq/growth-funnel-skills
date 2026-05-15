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
    output_language,
    select_funnel_skeleton,
    ui_text,
    validate_and_write,
    write_final_page,
    write_text_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render clean Markdown and HTML pages into final/.")
    parser.add_argument("workspace_dir", help="Workspace directory to render.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def dash(value: Any, ru: bool = False) -> str:
    text = "" if value is None else str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text or ("не указано" if ru else "-")


def table_cell(value: Any, ru: bool = False) -> str:
    return dash(value, ru).replace("|", "/")


def yes_no(value: bool, ru: bool) -> str:
    return ("да" if value else "нет") if ru else ("yes" if value else "no")


def confidence_label(value: str, ru: bool) -> str:
    normalized = str(value or "").lower()
    if ru:
        return {"high": "высокая", "medium": "средняя", "low": "низкая"}.get(normalized, "неизвестная")
    return normalized or "unknown"


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


def insights(data: dict[str, Any]) -> dict[str, Any]:
    item = data.get("insights")
    return item if isinstance(item, dict) else {}


def render_index(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    state = data["state"]
    item = insights(data)
    summary = item.get("decision_summary", {}) if isinstance(item.get("decision_summary"), dict) else {}
    if ru:
        return f"""# С чего начать

> **Что делать первым:** {dash(summary.get('first_action'), ru)}

## Главное решение

- Статус: {dash(summary.get('status'), ru)}
- Рекомендация: {dash(summary.get('recommendation'), ru)}
- Основной KPI: {dash(summary.get('target_kpi'), ru)}
- Уверенность: {confidence_label(str(item.get('confidence')), ru)}

## Как читать пакет

1. Резюме решения: что строить и почему.
2. Сегменты и задачи: для кого воронка и какое убеждение меняем.
3. Карта воронки и плейбук экранов: что показать пользователю по шагам.
4. Метрики, эксперимент и риски: как запускать без самообмана.

## Состояние данных

- Минимальный входной набор: {yes_no(state.get('minimum_gate_satisfied', False), ru)}
- Полнота контекста: {state.get('scores', {}).get('completeness', 0)}/100
- Квалификация: {state.get('scores', {}).get('qualification', 0)}/100
- Готовность ресерча: {state.get('scores', {}).get('research_readiness', 0)}/100
"""
    return f"""# Start Here

> **First action:** {dash(summary.get('first_action'))}

## Core Decision

- Status: {dash(summary.get('status'))}
- Recommendation: {dash(summary.get('recommendation'))}
- Primary KPI: {dash(summary.get('target_kpi'))}
- Confidence: {dash(item.get('confidence'))}

## How To Read This Pack

1. Decision summary: what to build and why.
2. Segments and jobs: who the funnel is for and which belief changes.
3. Funnel map and screen playbook: what the user sees step by step.
4. Tracking, experiment, and risks: how to launch without fooling yourself.

## Data State

- Minimum gate: {yes_no(state.get('minimum_gate_satisfied', False), ru)}
- Completeness score: {state.get('scores', {}).get('completeness', 0)}/100
- Qualification score: {state.get('scores', {}).get('qualification', 0)}/100
- Research readiness score: {state.get('scores', {}).get('research_readiness', 0)}/100
"""


def render_status(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    state = data["state"]
    item = insights(data)
    summary = item.get("decision_summary", {}) if isinstance(item.get("decision_summary"), dict) else {}
    missing = state.get("critical_missing_fields", [])
    next_input = state.get("next_best_input", [])
    if ru:
        return f"""# Резюме решения

## Что решено

- Рекомендация: {dash(summary.get('recommendation'), ru)}
- Почему: {dash(summary.get('why'), ru)}
- Выбранный путь: `{dash(summary.get('skeleton'), ru)}`
- Основание: `{dash(summary.get('support'), ru)}`

## Готовность

| Критерий | Значение |
| --- | --- |
| Статус | {table_cell(summary.get('status'), ru)} |
| Готово к рекомендациям | {yes_no(state.get('phase') == 'ready', ru)} |
| Полнота контекста | {state.get('scores', {}).get('completeness', 0)}/100 |
| Квалификация | {state.get('scores', {}).get('qualification', 0)}/100 |
| Готовность ресерча | {state.get('scores', {}).get('research_readiness', 0)}/100 |
| Решение системы | `{table_cell(state.get('decision'), ru)}` |

## Что блокирует уверенность

{bullet_list(missing or state.get('evidence_gaps', []), 'нет блокеров', ru)}

## Следующий точный ввод

{bullet_list(next_input, 'назначить владельца первого эксперимента', ru)}
"""
    return f"""# Decision Summary

## What Is Decided

- Recommendation: {dash(summary.get('recommendation'))}
- Why: {dash(summary.get('why'))}
- Selected path: `{dash(summary.get('skeleton'))}`
- Support: `{dash(summary.get('support'))}`

## Readiness

| Criterion | Value |
| --- | --- |
| Status | {table_cell(summary.get('status'))} |
| Recommendations ready | {yes_no(state.get('phase') == 'ready', ru)} |
| Completeness | {state.get('scores', {}).get('completeness', 0)}/100 |
| Qualification | {state.get('scores', {}).get('qualification', 0)}/100 |
| Research readiness | {state.get('scores', {}).get('research_readiness', 0)}/100 |
| System decision | `{table_cell(state.get('decision'))}` |

## What Blocks Confidence

{bullet_list(missing or state.get('evidence_gaps', []), 'no blockers', ru)}

## Next Precise Input

{bullet_list(next_input, 'assign the first experiment owner', ru)}
"""


def render_segments(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    intake = data["intake"]
    item = insights(data)
    segments = item.get("segments", []) if isinstance(item.get("segments"), list) else []
    title = "Сегменты и задачи" if ru else "Segments and Jobs"
    context_title = "Нормализованный контекст" if ru else "Normalized Context"
    proof_title = "Доказательства и метрики" if ru else "Proof and Metrics"
    fields = [
        ("Проект" if ru else "Project", intake.get("project_name")),
        ("Оффер" if ru else "Offer", intake.get("offer")),
        ("ICP" if ru else "ICP", intake.get("icp")),
        ("Основная персона" if ru else "Primary persona", intake.get("primary_persona")),
        ("Задача пользователя" if ru else "Job to be done", intake.get("jtbd")),
        ("Основной KPI" if ru else "Primary KPI", intake.get("target_kpi")),
        ("Канал" if ru else "Channel", intake.get("primary_channel")),
        ("Цена" if ru else "Pricing", intake.get("pricing")),
        ("Минут до первой ценности" if ru else "Minutes to first value", intake.get("time_to_first_value_minutes")),
        ("Ограничения" if ru else "Constraints", intake.get("product_constraints")),
    ]
    return f"""# {title}

## {title}

{segments_table(segments, ru)}

## {context_title}

{rows_table(fields, "Поле" if ru else "Field", "Значение" if ru else "Value", ru)}

## {proof_title}

- {"Доказательств пока нет" if ru else "Explicit no proof yet"}: {yes_no(bool(intake.get('explicit_no_proof_yet')), ru)}
- {"Доказательства" if ru else "Proof assets"}:

{bullet_list(intake.get('proof_assets', []), 'нет', ru)}

### {"Метрики" if ru else "Metrics"}

{metrics_table(intake.get('metrics', []), ru)}
"""


def render_evidence(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    evidence_refs = item.get("evidence_refs", []) if isinstance(item.get("evidence_refs"), list) else []
    assumptions = item.get("assumptions", []) if isinstance(item.get("assumptions"), list) else []
    results = data["agent_results"]
    if ru:
        return f"""# Данные и допущения

## Источники, использованные в решениях

{evidence_refs_table(evidence_refs, ru)}

## Допущения вместо выдуманных фактов

{assumptions_table(assumptions, ru)}

## Результаты специалистов

{agent_results_section(results, ru)}

## Правило данных

Цены, журналы изменений и утверждения про текущую практику требуют даты получения. Без даты они остаются пробелом данных, а не фактом.
"""
    return f"""# Evidence and Assumptions

## Evidence Used In Decisions

{evidence_refs_table(evidence_refs, ru)}

## Assumptions Instead Of Invented Facts

{assumptions_table(assumptions, ru)}

## Specialist Results

{agent_results_section(results, ru)}

## Evidence Rule

Pricing, changelog, and current-practice claims require retrieval dates. Missing dates remain evidence gaps instead of current facts.
"""


def render_competitors(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    title = "Конкурентные паттерны" if ru else "Competitive Patterns"
    guidance = (
        "Используйте строки конкурентов как наблюдения. Не переносите утверждения в рекомендации без источника и даты получения."
        if ru
        else "Use competitor rows as observations. Do not copy claims into recommendations unless the source and retrieval date are present."
    )
    return f"""# {title}

{competitor_table(data["competitors"], ru)}

## {"Как применять" if ru else "How To Use This"}

{guidance}
"""


def render_blueprint(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    summary = item.get("decision_summary", {}) if isinstance(item.get("decision_summary"), dict) else {}
    screens = item.get("screens", []) if isinstance(item.get("screens"), list) else []
    skeleton, fallback_rationale = select_funnel_skeleton(data)
    rationale = str(summary.get("rationale") or fallback_rationale)
    gate = minimum_gate_satisfied(data["intake"])
    blocked = ""
    if not gate:
        blocked = "> **Статус:** карта заблокирована до заполнения минимального входного набора.\n\n" if ru else "> **Status:** map is blocked until the minimum gate is satisfied.\n\n"
    if ru:
        return f"""# Карта воронки

{blocked}## Логика пути

- Путь: `{skeleton}`
- Основание выбора: {rationale}
- Целевое действие: {dash(summary.get('target_kpi'), ru)}
- Основание: `{dash(summary.get('support'), ru)}`

## Маршрут пользователя

{funnel_map_table(screens, ru)}
"""
    return f"""# Funnel Map

{blocked}## Path Logic

- Path: `{skeleton}`
- Rationale: {rationale}
- Target action: {dash(summary.get('target_kpi'))}
- Support: `{dash(summary.get('support'))}`

## User Route

{funnel_map_table(screens, ru)}
"""


def render_screen_specs(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    screens = item.get("screens", []) if isinstance(item.get("screens"), list) else []
    gate = minimum_gate_satisfied(data["intake"])
    blocked = ""
    if not gate:
        blocked = (
            "Status: blocked until the minimum gate is satisfied. Treat the table below as a draft scaffold, not a ready recommendation.\n\n"
            if not ru
            else "Статус: заблокировано до заполнения минимального входного набора. Таблица ниже является черновиком, а не готовой рекомендацией.\n\n"
        )
    title = "Плейбук экранов" if ru else "Screen Playbook"
    return f"""# {title}

{blocked}{screen_table(screens, ru)}
"""


def render_tracking(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    screens = item.get("screens", []) if isinstance(item.get("screens"), list) else []
    target_kpi = dash(data["intake"].get("target_kpi"), ru)
    title = "Метрики и события" if ru else "Tracking and KPIs"
    blocked = ""
    if not minimum_gate_satisfied(data["intake"]):
        blocked = (
            "Статус: заблокировано, пока неизвестны оффер, аудитория, канал, KPI и состояние доказательств.\n\n"
            if ru
            else "Status: blocked until the offer, audience, channel, KPI, and proof state are known.\n\n"
        )
    return f"""# {title}

{blocked}## {"Контракт KPI" if ru else "KPI Contract"}

- {"Основная метрика" if ru else "Primary metric"}: {target_kpi}
- {"Нельзя интерпретировать эксперимент без чистого event logging." if ru else "Do not interpret an experiment without clean event logging."}

## {"События по шагам" if ru else "Events By Step"}

{tracking_table(screens, ru)}
"""


def render_experiment(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    experiments = item.get("experiments", []) if isinstance(item.get("experiments"), list) else []
    title = "Следующий эксперимент" if ru else "Next Experiment"
    if not minimum_gate_satisfied(data["intake"]):
        missing = data["state"].get("critical_missing_fields", [])
        return f"""# {title}

Status: blocked

## Missing

{bullet_list(missing, '-', ru)}
"""
    return f"""# {title}

{experiment_table(experiments, ru)}
"""


def render_gaps(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    gaps = data["gaps"]
    risks = item.get("risks", []) if isinstance(item.get("risks"), list) else []
    title = "Риски и пробелы" if ru else "Risks and Gaps"
    return f"""# {title}

## {"Карта рисков" if ru else "Risk Heatmap"}

{risk_table(risks, ru)}

## {"Пробелы данных" if ru else "Evidence Gaps"}

{bullet_list(gaps.get('evidence_gaps', []), 'нет', ru)}

## {"Конфликты" if ru else "Conflicts"}

{bullet_list(gaps.get('conflicts', []), 'нет', ru)}

## {"Заблокированные рекомендации" if ru else "Blocked Recommendations"}

{bullet_list(gaps.get('blocked_recommendations', []), 'нет', ru)}
"""


def render_execution(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    gaps = data["gaps"]
    item = insights(data)
    summary = item.get("decision_summary", {}) if isinstance(item.get("decision_summary"), dict) else {}
    title = "План внедрения" if ru else "Execution Plan"
    if ru:
        return f"""# {title}

> **Первый шаг:** {dash(summary.get('first_action'), ru)}

## Собрать автоматически

{bullet_list(gaps.get('auto_collect', []), 'нет задач', ru)}

## Спросить пользователя

{bullet_list(gaps.get('ask_user', []), 'нет вопросов', ru)}

## Проверить перед запуском

- Повторно запустить `validate_workspace.py`.
- Повторно отрендерить `final/`.
- Проверить, что `runtime/insights.json` не попал в `final/`.
- Убедиться, что каждая рекомендация ссылается на источник или явное допущение.
"""
    return f"""# {title}

> **First step:** {dash(summary.get('first_action'))}

## Auto-Collect

{bullet_list(gaps.get('auto_collect', []), 'no tasks', ru)}

## Ask User

{bullet_list(gaps.get('ask_user', []), 'no questions', ru)}

## Verify Before Launch

- Re-run `validate_workspace.py`.
- Re-render `final/`.
- Check that `runtime/insights.json` did not leak into `final/`.
- Confirm that every recommendation references evidence or an explicit assumption.
"""


def bullet_list(values: Any, fallback: str, ru: bool = False) -> str:
    if not values:
        return f"- {fallback}"
    if isinstance(values, dict):
        values = [f"{key}: {value}" for key, value in values.items()]
    return "\n".join(f"- {dash(value, ru)}" for value in values)


def rows_table(rows: list[tuple[str, Any]], key_label: str, value_label: str, ru: bool = False) -> str:
    body = "\n".join(f"| {table_cell(key, ru)} | {table_cell(value, ru)} |" for key, value in rows)
    return f"| {key_label} | {value_label} |\n| --- | --- |\n{body}"


def segments_table(rows: list[dict[str, Any]], ru: bool) -> str:
    if not rows:
        empty = "нет" if ru else "-"
        return f"| {'Сегмент' if ru else 'Segment'} | {'Задача' if ru else 'Job'} | {'Сдвиг убеждения' if ru else 'Belief shift'} | {'Основание' if ru else 'Support'} |\n| --- | --- | --- | --- |\n| {empty} | {empty} | {empty} | {empty} |"
    headers = ("Сегмент", "Задача", "Боль", "Сдвиг убеждения", "Основание", "Уверенность") if ru else ("Segment", "Job", "Pain", "Belief shift", "Support", "Confidence")
    body = "\n".join(
        f"| {table_cell(row.get('segment'), ru)} | {table_cell(row.get('job'), ru)} | {table_cell(row.get('pain'), ru)} | {table_cell(row.get('belief_shift'), ru)} | {table_cell(row.get('support'), ru)} | {table_cell(confidence_label(str(row.get('confidence')), ru), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n{body}"


def funnel_map_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Шаг", "Убеждение", "Контент", "CTA", "Метрика") if ru else ("Step", "Belief", "Content", "CTA", "Metric")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n| - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('stage'), ru)} | {table_cell(row.get('target_belief'), ru)} | {table_cell(row.get('content'), ru)} | {table_cell(row.get('cta'), ru)} | {table_cell(row.get('metric'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n{body}"


def screen_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Экран", "Убеждение", "Контент", "CTA", "Доказательство", "Основание") if ru else ("Screen", "Target belief", "Content", "CTA", "Proof needed", "Support")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('stage'), ru)} | {table_cell(row.get('target_belief'), ru)} | {table_cell(row.get('content'), ru)} | {table_cell(row.get('cta'), ru)} | {table_cell(row.get('proof_needed'), ru)} | {table_cell(row.get('support'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n{body}"


def tracking_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Событие", "Шаг", "Главная метрика", "Guardrail") if ru else ("Event", "Step", "Primary metric", "Guardrail")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n| - | - | - | - |"
    body = "\n".join(
        f"| {event_name(row.get('stage'), ru)} | {table_cell(row.get('stage'), ru)} | {table_cell(row.get('metric'), ru)} | {table_cell(row.get('guardrail'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n{body}"


def event_name(stage: Any, ru: bool) -> str:
    text = dash(stage, ru)
    return f"{text}: {'событие зафиксировано' if ru else 'event logged'}"


def experiment_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Название", "Гипотеза", "Изменение", "Метрика", "Правило решения", "Основание") if ru else ("Name", "Hypothesis", "Change", "Metric", "Decision rule", "Support")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('name'), ru)} | {table_cell(row.get('hypothesis'), ru)} | {table_cell(row.get('change'), ru)} | {table_cell(row.get('primary_metric'), ru)} | {table_cell(row.get('decision_rule'), ru)} | {table_cell(row.get('support'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n{body}"


def risk_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Риск", "Уровень", "Снижение риска", "Основание") if ru else ("Risk", "Level", "Mitigation", "Support")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n| - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('risk'), ru)} | {table_cell(row.get('level'), ru)} | {table_cell(row.get('mitigation'), ru)} | {table_cell(row.get('support'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n{body}"


def assumptions_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("ID", "Допущение", "Где используется") if ru else ("ID", "Assumption", "Used in")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} |\n| --- | --- | --- |\n| - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('id'), ru)} | {table_cell(row.get('statement'), ru)} | {table_cell(row.get('used_in'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} |\n| --- | --- | --- |\n{body}"


def evidence_refs_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("ID", "Название", "Уверенность", "URL") if ru else ("ID", "Title", "Confidence", "URL")
    if not rows:
        empty = "нет источников" if ru else "no sources"
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n| - | {empty} | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('id'), ru)} | {table_cell(row.get('title'), ru)} | {table_cell(confidence_label(str(row.get('confidence')), ru), ru)} | {table_cell(row.get('url'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n{body}"


def metrics_table(metrics: Any, ru: bool) -> str:
    headers = ("Метрика", "Значение", "Источник", "Заметки") if ru else ("Metric", "Value", "Source", "Notes")
    if not metrics:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n| - | - | - | - |"
    rows = []
    for metric in metrics:
        if isinstance(metric, dict):
            rows.append(f"| {table_cell(metric.get('metric_name'), ru)} | {table_cell(metric.get('value'), ru)} | {table_cell(metric.get('source'), ru)} | {table_cell(metric.get('notes'), ru)} |")
        else:
            rows.append(f"| raw_metric | - | ingested_notes | {table_cell(metric, ru)} |")
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n" + "\n".join(rows)


def competitor_table(rows: list[dict[str, str]], ru: bool) -> str:
    headers = ("Конкурент", "Позиционирование", "Цена", "CTA", "Онбординг", "Дата", "Уверенность", "Источник") if ru else ("Competitor", "Positioning", "Pricing", "CTA", "Onboarding", "Retrieved", "Confidence", "Source")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} | {headers[7]} |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('competitor'), ru)} | {table_cell(row.get('positioning'), ru)} | {table_cell(row.get('pricing'), ru)} | {table_cell(row.get('primary_cta'), ru)} | {table_cell(row.get('onboarding_pattern'), ru)} | {table_cell(row.get('retrieved_at'), ru)} | {table_cell(confidence_label(str(row.get('confidence')), ru), ru)} | {table_cell(row.get('source'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} | {headers[7]} |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n" + body


def agent_results_section(results: list[dict[str, Any]], ru: bool) -> str:
    if not results:
        return "- Результаты специалистов пока не записаны." if ru else "- No specialist results recorded yet."
    sections = []
    for result in results:
        findings = bullet_list(result.get("key_findings", []), "-", ru)
        if ru:
            sections.append(
                f"### {dash(result.get('role'), ru)}: {dash(result.get('topic_id'), ru)}\n\n"
                f"{dash(result.get('summary'), ru)}\n\n"
                f"Выводы:\n\n{findings}\n\n"
                f"Уверенность: {confidence_label(str(result.get('confidence')), ru)}"
            )
        else:
            sections.append(
                f"### {dash(result.get('role'))}: {dash(result.get('topic_id'))}\n\n"
                f"{dash(result.get('summary'))}\n\n"
                f"Findings:\n\n{findings}\n\n"
                f"Confidence: {dash(result.get('confidence'))}"
            )
    return "\n\n".join(sections)


def write_index_html(workspace: Path, data: dict[str, Any], nav: list[tuple[str, str]]) -> None:
    ru = is_russian(data)
    language = output_language(data)
    links = "\n".join(
        f'<a class="index-card" href="{escape(slug)}.html"><span>{number + 1:02d}</span>{escape(title)}</a>'
        for number, (slug, title) in enumerate(nav)
    )
    title = "Оглавление" if ru else "Index"
    start = ui_text(language, "start")
    intro = ui_text(language, "index_intro")
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
    <p>{escape(intro)}</p>
    <a class="start" href="00_index.html">{escape(start)}</a>
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
        "02_intake_brief": render_segments,
        "03_research_evidence": render_evidence,
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
    summary["recommendations_ready"] = summary.get("phase") == "ready"
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
