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
    input_dir,
    is_russian,
    load_workspace,
    markdown_to_html,
    minimum_gate_satisfied,
    output_language,
    decision_label,
    select_funnel_skeleton,
    skeleton_label,
    truthy,
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


def reviewer_status_label(value: Any, ru: bool) -> str:
    text = str(value or "")
    if not ru:
        return {
            "not_required": "not required",
            "required": "approval required",
            "approved": "approved",
        }.get(text, text or "-")
    return {
        "not_required": "не требуется",
        "required": "требуется одобрение",
        "approved": "одобрено",
    }.get(text, text or "не указано")


def reviewer_support_refs(row: dict[str, Any]) -> str:
    return "; ".join(
        item
        for item in [
            ", ".join(list_items(row.get("claim_ids"))),
            ", ".join(list_items(row.get("source_ids"))),
            ", ".join(list_items(row.get("assumption_ids"))),
        ]
        if item
    )


def reviewer_item_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Что проверить", "Объект", "Риск", "Причина", "На чем основано") if ru else ("Review item", "Target", "Risk", "Reason", "Support")
    if not rows:
        empty = "нет обязательных проверок" if ru else "no required review items"
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n| {empty} | - | - | - | - |"
    body = "\n".join(
        (
            f"| {table_cell(row.get('review_type'), ru)} | {table_cell(row.get('target_id'), ru)} | "
            f"{table_cell(row.get('risk_level'), ru)} | {table_cell(row.get('reason'), ru)} | "
            f"{table_cell(reviewer_support_refs(row), ru)} |"
        )
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n{body}"


def reviewer_approval_section(approval: dict[str, Any], ru: bool) -> str:
    if not isinstance(approval, dict) or not approval:
        return "-" if not ru else "не указано"
    rows = [
        ("Статус" if ru else "Status", reviewer_status_label(approval.get("status"), ru)),
        ("Требуется" if ru else "Required", yes_no(bool(approval.get("required")), ru)),
        ("Одобрено" if ru else "Approved", yes_no(bool(approval.get("approved")), ru)),
        ("Кем" if ru else "Approved by", approval.get("approved_by")),
        ("Когда" if ru else "Approved at", approval.get("approved_at")),
        ("Блокер" if ru else "Blocked reason", approval.get("blocked_reason")),
    ]
    review_items = approval.get("review_items") if isinstance(approval.get("review_items"), list) else []
    return f"{rows_table(rows, 'Поле' if ru else 'Field', 'Значение' if ru else 'Value', ru)}\n\n{reviewer_item_table(review_items, ru)}"


def confidence_label(value: str, ru: bool) -> str:
    normalized = str(value or "").lower()
    if ru:
        return {"high": "высокая", "medium": "средняя", "low": "низкая"}.get(normalized, "неизвестная")
    return normalized or "unknown"


def readiness_label(data: dict[str, Any], ru: bool) -> str:
    state = data["state"]
    phase = str(state.get("phase") or "")
    if ru:
        if phase == "ready":
            return "готово к тесту с явными допущениями"
        if phase == "research":
            return "черновик: нужны данные перед запуском"
        return "заблокировано: не хватает входного контекста"
    if phase == "ready":
        return "ready to test with explicit assumptions"
    if phase == "research":
        return "draft: data needed before launch"
    return "blocked: intake needed"


def role_label(value: Any, ru: bool) -> str:
    text = dash(value, ru)
    if not ru:
        return text
    values = {
        "intake": "сбор контекста",
        "planner": "планирование",
        "research": "исследование",
        "competitor": "конкуренты",
        "synthesis": "синтез",
        "compiler_reviewer": "проверка финального пакета",
    }
    return values.get(text, text.replace("_", " "))


def usage_label(value: Any, ru: bool) -> str:
    text = dash(value, ru)
    if not ru:
        return text
    values = {
        "decision_summary": "резюме решения",
        "competitive_patterns": "карта конкурентов",
        "screen_playbook": "сценарии экранов/бота",
        "funnel_map": "карта воронки",
        "tracking_plan": "метрики и события",
        "experiment": "первый тест",
        "promise_proof": "проверка обещания и доказательства",
        "benchmark_assumption": "рыночное допущение для холодного старта",
        "all recommendations": "все рекомендации",
    }
    return values.get(text, text.replace("_", " "))


def pipeline_rows(data: dict[str, Any], ru: bool) -> list[dict[str, str]]:
    item = insights(data)
    summary = item.get("decision_summary", {}) if isinstance(item.get("decision_summary"), dict) else {}
    first_action = dash(summary.get("first_action"), ru)
    if ru:
        return [
            {
                "step": "1. Выбрать фокус",
                "do": first_action,
                "why": "Одна воронка не должна одновременно продавать всем сегментам и всем направлениям.",
                "result": "Один сегмент, одно возражение и одна главная метрика для первого запуска.",
            },
            {
                "step": "2. Проверить рынок",
                "do": "Собрать 3 свежих источника и 3 конкурента с датами проверки.",
                "why": "Так отчет не будет выдумывать цены, обещания, доказательства и конкурентные паттерны.",
                "result": "Понятные границы: что можно обещать, чем отличаться и где нужны доказательства.",
            },
            {
                "step": "3. Собрать путь пользователя",
                "do": "Описать рекламу/вход, первый полезный результат, сбор контакта и передачу в продажи.",
                "why": "Пользователь должен понимать следующий шаг до того, как оставит контакт или деньги.",
                "result": "Карта воронки и сценарий экранов/бота без лишних внутренних терминов.",
            },
            {
                "step": "4. Включить измерение",
                "do": "Зафиксировать события, статусы в CRM, владельца обработки и срок первого контакта.",
                "why": "Без этого нельзя честно понять, сработала воронка или просто пришел случайный трафик.",
                "result": "Чистые данные для решения: оставить, исправить или остановить запуск.",
            },
            {
                "step": "5. Запустить тест",
                "do": "Запустить один осмысленный тест на 14 дней или до достаточного числа лидов.",
                "why": "Сначала проверяется путь и качество лидов, а не косметика кнопок.",
                "result": "Решение по следующей итерации и список того, что узнали.",
            },
        ]
    return [
        {
            "step": "1. Choose focus",
            "do": first_action,
            "why": "One funnel should not sell every segment and every offer at once.",
            "result": "One segment, one objection, and one primary metric for the first launch.",
        },
        {
            "step": "2. Check the market",
            "do": "Collect 3 current sources and 3 competitors with retrieval dates.",
            "why": "This prevents invented prices, claims, proof, and competitor patterns.",
            "result": "Clear boundaries for what to promise, how to differ, and what proof is missing.",
        },
        {
            "step": "3. Build the user path",
            "do": "Define entry, first useful result, contact capture, and sales handoff.",
            "why": "The user should understand the next step before giving contact details or money.",
            "result": "A funnel map and screen/bot script without internal jargon.",
        },
        {
            "step": "4. Turn on measurement",
            "do": "Lock events, CRM statuses, owner, and first-contact SLA.",
            "why": "Without this, you cannot tell whether the funnel worked or traffic was random.",
            "result": "Clean data to decide whether to keep, fix, or stop the launch.",
        },
        {
            "step": "5. Run the test",
            "do": "Run one meaningful test for 14 days or until there are enough leads.",
            "why": "The first test checks the path and lead quality, not button cosmetics.",
            "result": "A decision for the next iteration and a list of learnings.",
        },
    ]


def pipeline_table(data: dict[str, Any], ru: bool) -> str:
    rows = pipeline_rows(data, ru)
    headers = ("Шаг", "Что сделать", "Зачем", "Что получишь") if ru else ("Step", "What to do", "Why", "What you get")
    body = "\n".join(
        f"| {table_cell(row['step'], ru)} | {table_cell(row['do'], ru)} | {table_cell(row['why'], ru)} | {table_cell(row['result'], ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n{body}"


def markdown_file_link(path: Path, label: str) -> str:
    target = str(path)
    if re.search(r"[\s()]", target):
        target = f"<{target}>"
    return f"[{label}]({target})"


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

- Статус: {readiness_label(data, ru)}
- Рекомендация: {dash(summary.get('recommendation'), ru)}
- Главная метрика: {dash(summary.get('target_kpi'), ru)}
- Уверенность: {confidence_label(str(item.get('confidence')), ru)}

## Пайплайн запуска

{pipeline_table(data, ru)}

## Как читать пакет

1. Резюме решения: что строить и почему.
2. Сегменты и задачи: для кого воронка и какое убеждение меняем.
3. Карта воронки и сценарии экранов/бота: что показать пользователю по шагам.
4. Метрики, эксперимент и риски: как запускать без самообмана.

## Состояние данных

- Минимальный входной набор: {yes_no(state.get('minimum_gate_satisfied', False), ru)}
- Полнота контекста: {state.get('scores', {}).get('completeness', 0)}/100
- Готовность к рабочей воронке: {state.get('scores', {}).get('qualification', 0)}/100
- Готовность данных: {state.get('scores', {}).get('research_readiness', 0)}/100
"""
    return f"""# Start Here

> **First action:** {dash(summary.get('first_action'))}

## Core Decision

- Status: {dash(summary.get('status'))}
- Recommendation: {dash(summary.get('recommendation'))}
- Primary KPI: {dash(summary.get('target_kpi'))}
- Confidence: {dash(item.get('confidence'))}

## Launch Pipeline

{pipeline_table(data, ru)}

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
    reviewer_approval = item.get("reviewer_approval") if isinstance(item.get("reviewer_approval"), dict) else {}
    missing = state.get("critical_missing_fields", [])
    next_input = state.get("next_best_input", [])
    no_more_user_data = truthy(state.get("no_more_user_data") or data["intake"].get("no_more_user_data"))
    path_label = summary.get("path_label") or skeleton_label(str(summary.get("skeleton") or ""), ru)
    input_directory = str(input_dir(data["workspace"]).resolve())
    next_input_file = str((input_dir(data["workspace"]) / "00_next_input.md").resolve())
    next_input_fallback = (
        "дальше работаем на явных допущениях; новых данных от пользователя не требуется"
        if no_more_user_data
        else "назначить владельца первого эксперимента"
    )
    english_next_input_fallback = (
        "continue with explicit assumptions; no further user data requested"
        if no_more_user_data
        else "assign the first experiment owner"
    )
    if ru:
        return f"""# Резюме решения

## Что решено

- Рекомендация: {dash(summary.get('recommendation'), ru)}
- Почему: {dash(summary.get('why'), ru)}
- Выбранный путь: {dash(path_label, ru)}
- На чем основано: {dash(summary.get('support'), ru)}

## Готовность

| Критерий | Значение |
| --- | --- |
| Статус | {table_cell(readiness_label(data, ru), ru)} |
| Готово к тесту | {yes_no(bool(state.get('ready_to_test')), ru)} |
| Готово к launch handoff | {yes_no(bool(state.get('ready_for_launch')), ru)} |
| Полнота контекста | {state.get('scores', {}).get('completeness', 0)}/100 |
| Готовность к рабочей воронке | {state.get('scores', {}).get('qualification', 0)}/100 |
| Готовность данных | {state.get('scores', {}).get('research_readiness', 0)}/100 |
| Решение системы | {table_cell(decision_label(str(state.get('decision') or ''), ru), ru)} |

## Папка для сбора данных

- Папка: {input_directory}
- Что заполнить дальше: {next_input_file}
- Основной бриф: {input_directory}/01_minimum_brief.md

## Проверка перед запуском

{reviewer_approval_section(reviewer_approval, ru)}

## Что блокирует уверенность

{bullet_list(missing or state.get('evidence_gaps', []), 'нет блокеров', ru)}

## Следующий точный ввод

{bullet_list(next_input, next_input_fallback, ru)}
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
| Ready to test | {yes_no(bool(state.get('ready_to_test')), ru)} |
| Ready for launch handoff | {yes_no(bool(state.get('ready_for_launch')), ru)} |
| Completeness | {state.get('scores', {}).get('completeness', 0)}/100 |
| Qualification | {state.get('scores', {}).get('qualification', 0)}/100 |
| Research readiness | {state.get('scores', {}).get('research_readiness', 0)}/100 |
| System decision | `{table_cell(state.get('decision'))}` |

## Input Folder

- Folder: {input_directory}
- Next input checklist: {next_input_file}
- Main brief: {input_directory}/01_minimum_brief.md

## Reviewer Approval

{reviewer_approval_section(reviewer_approval, ru)}

## What Blocks Confidence

{bullet_list(missing or state.get('evidence_gaps', []), 'no blockers', ru)}

## Next Precise Input

{bullet_list(next_input, english_next_input_fallback, ru)}
"""


def render_segments(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    intake = data["intake"]
    item = insights(data)
    segments = item.get("segments", []) if isinstance(item.get("segments"), list) else []
    niche_profile = item.get("niche_profile") if isinstance(item.get("niche_profile"), dict) else {}
    title = "Сегменты и задачи" if ru else "Segments and Jobs"
    context_title = "Нормализованный контекст" if ru else "Normalized Context"
    proof_title = "Доказательства и метрики" if ru else "Proof and Metrics"
    fields = [
        ("Проект" if ru else "Project", intake.get("project_name")),
        ("Оффер" if ru else "Offer", intake.get("offer")),
        ("Целевая аудитория" if ru else "ICP", intake.get("icp")),
        ("Основная персона" if ru else "Primary persona", intake.get("primary_persona")),
        ("Задача пользователя" if ru else "Job to be done", intake.get("jtbd")),
        ("Главная метрика" if ru else "Primary KPI", intake.get("target_kpi")),
        ("Канал" if ru else "Channel", intake.get("primary_channel")),
        ("Цена" if ru else "Pricing", intake.get("pricing")),
        ("Минут до первой ценности" if ru else "Minutes to first value", intake.get("time_to_first_value_minutes")),
        ("Ограничения" if ru else "Constraints", intake.get("product_constraints")),
    ]
    return f"""# {title}

## {title}

{segments_table(segments, ru)}

## {"Нишевый профиль" if ru else "Niche Profile"}

{niche_profile_section(niche_profile, ru)}

## {context_title}

{rows_table(fields, "Поле" if ru else "Field", "Значение" if ru else "Value", ru)}

## {proof_title}

- {"Доказательств пока нет" if ru else "Explicit no proof yet"}: {yes_no(bool(intake.get('explicit_no_proof_yet')), ru)}
- {"Что уже подтверждает доверие" if ru else "Proof assets"}:

{bullet_list(intake.get('proof_assets', []), 'нет', ru)}

### {"Метрики" if ru else "Metrics"}

{metrics_table(intake.get('metrics', []), ru)}
"""


def render_evidence(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    evidence_refs = item.get("evidence_refs", []) if isinstance(item.get("evidence_refs"), list) else []
    assumptions = item.get("assumptions", []) if isinstance(item.get("assumptions"), list) else []
    benchmark_assumptions = item.get("benchmark_assumptions", []) if isinstance(item.get("benchmark_assumptions"), list) else []
    promise_proof = item.get("promise_proof_model", []) if isinstance(item.get("promise_proof_model"), list) else []
    results = data["agent_results"]
    if ru:
        return f"""# Данные и допущения

## Источники, использованные в решениях

{evidence_refs_table(evidence_refs, ru)}

## Допущения вместо выдуманных фактов

{assumptions_table(assumptions, ru)}

## Бенчмарки для холодного старта

{benchmark_assumptions_table(benchmark_assumptions, ru)}

## Проверка обещания и доказательства

{promise_proof_table(promise_proof, ru)}

## Результаты исследования

{agent_results_section(results, ru)}

## Правило данных

Цены, журналы изменений и утверждения про текущую практику требуют даты получения. Без даты они остаются пробелом данных, а не фактом.
"""
    return f"""# Evidence and Assumptions

## Evidence Used In Decisions

{evidence_refs_table(evidence_refs, ru)}

## Assumptions Instead Of Invented Facts

{assumptions_table(assumptions, ru)}

## Cold-Start Benchmarks

{benchmark_assumptions_table(benchmark_assumptions, ru)}

## Promise-Proof Check

{promise_proof_table(promise_proof, ru)}

## Specialist Results

{agent_results_section(results, ru)}

## Evidence Rule

Pricing, changelog, and current-practice claims require retrieval dates. Missing dates remain evidence gaps instead of current facts.
"""


def render_competitors(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    competitors = data["competitors"]
    competitor_synthesis = item.get("competitor_synthesis") if isinstance(item.get("competitor_synthesis"), dict) else {}
    title = "Конкурентные паттерны" if ru else "Competitive Patterns"
    guidance = (
        "Используйте строки конкурентов как наблюдения. Не переносите утверждения в рекомендации без источника и даты получения."
        if ru
        else "Use competitor rows as observations. Do not copy claims into recommendations unless the source and retrieval date are present."
    )
    missing = ""
    if not competitors:
        missing = (
            "\n> **Пока нет карты конкурентов:** отчет не должен выдумывать цены, призывы к действию или доказательства конкурентов. Соберите минимум 3 прямых конкурента перед пометкой отчета как готового.\n"
            if ru
            else "\n> **No competitor map yet:** the report must not invent competitor pricing, CTAs, or proof. Collect at least 3 direct competitors before marking the report ready.\n"
        )
    return f"""# {title}

{missing}
{competitor_table(competitors, ru)}

## {"Синтез паттернов" if ru else "Pattern Synthesis"}

{competitor_synthesis_section(competitor_synthesis, ru)}

## {"Как применять" if ru else "How To Use This"}

{guidance}
"""


def render_blueprint(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    summary = item.get("decision_summary", {}) if isinstance(item.get("decision_summary"), dict) else {}
    screens = item.get("screens", []) if isinstance(item.get("screens"), list) else []
    channel_synthesis = item.get("channel_synthesis") if isinstance(item.get("channel_synthesis"), dict) else {}
    current_diff = item.get("current_funnel_diff") if isinstance(item.get("current_funnel_diff"), dict) else {}
    funnel_visual = item.get("funnel_visual") if isinstance(item.get("funnel_visual"), dict) else {}
    skeleton, fallback_rationale = select_funnel_skeleton(data)
    path_label = summary.get("path_label") or skeleton_label(skeleton, ru)
    rationale = str(summary.get("rationale") or fallback_rationale)
    gate = minimum_gate_satisfied(data["intake"])
    blocked = ""
    if not gate:
        blocked = "> **Статус:** карта заблокирована до заполнения минимального входного набора.\n\n" if ru else "> **Status:** map is blocked until the minimum gate is satisfied.\n\n"
    if ru:
        return f"""# Карта воронки

{blocked}## Логика пути

- Путь: {path_label}
- Основание выбора: {rationale}
- Главная метрика: {dash(summary.get('target_kpi'), ru)}
- На чем основано: {dash(summary.get('support'), ru)}

## Маршрут пользователя

{funnel_visual_block(funnel_visual, ru)}

{funnel_map_table(screens, ru)}

## Изменения относительно текущей воронки

{current_funnel_diff_section(current_diff, ru)}

## Канальный маршрут

{channel_route_table(channel_synthesis, ru)}
"""
    return f"""# Funnel Map

{blocked}## Path Logic

- Path: `{skeleton}`
- Rationale: {rationale}
- Target action: {dash(summary.get('target_kpi'))}
- Support: `{dash(summary.get('support'))}`

## User Route

{funnel_visual_block(funnel_visual, ru)}

{funnel_map_table(screens, ru)}

## Current vs Proposed Changes

{current_funnel_diff_section(current_diff, ru)}

## Channel Route

{channel_route_table(channel_synthesis, ru)}
"""


def render_screen_specs(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    screens = item.get("screens", []) if isinstance(item.get("screens"), list) else []
    variants = item.get("variant_bundles", []) if isinstance(item.get("variant_bundles"), list) else []
    gate = minimum_gate_satisfied(data["intake"])
    blocked = ""
    if not gate:
        blocked = (
            "Status: blocked until the minimum gate is satisfied. Treat the table below as a draft scaffold, not a ready recommendation.\n\n"
            if not ru
            else "Статус: заблокировано до заполнения минимального входного набора. Таблица ниже является черновиком, а не готовой рекомендацией.\n\n"
        )
    title = "Сценарии экранов/бота" if ru else "Screen Playbook"
    return f"""# {title}

{blocked}{screen_table(screens, ru)}

## {"Варианты текста и действий" if ru else "Variant Bundles"}

{variant_bundle_table(variants, ru)}
"""


def render_tracking(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    screens = item.get("screens", []) if isinstance(item.get("screens"), list) else []
    channel_synthesis = item.get("channel_synthesis") if isinstance(item.get("channel_synthesis"), dict) else {}
    niche_profile = item.get("niche_profile") if isinstance(item.get("niche_profile"), dict) else {}
    target_kpi = dash(data["intake"].get("target_kpi"), ru)
    title = "Метрики и события" if ru else "Tracking and KPIs"
    blocked = ""
    if not minimum_gate_satisfied(data["intake"]):
        blocked = (
            "Статус: заблокировано, пока неизвестны оффер, аудитория, канал, главная метрика и состояние доказательств.\n\n"
            if ru
            else "Status: blocked until the offer, audience, channel, KPI, and proof state are known.\n\n"
        )
    return f"""# {title}

{blocked}## {"Договоренность по главной метрике" if ru else "KPI Contract"}

- {"Главная метрика" if ru else "Primary metric"}: {target_kpi}
- {"Нельзя делать выводы по тесту без чисто записанных событий." if ru else "Do not interpret an experiment without clean event logging."}

## {"События по шагам" if ru else "Events By Step"}

{tracking_table(screens, ru)}

## {"Канальные события" if ru else "Channel Events"}

{channel_events_table(channel_synthesis, ru)}

## {"События профиля" if ru else "Profile Event Suggestions"}

{niche_events_table(niche_profile, ru)}
"""


def render_experiment(data: dict[str, Any]) -> str:
    ru = is_russian(data)
    item = insights(data)
    experiments = item.get("experiments", []) if isinstance(item.get("experiments"), list) else []
    title = "Следующий эксперимент" if ru else "Next Experiment"
    if not minimum_gate_satisfied(data["intake"]):
        missing = data["state"].get("critical_missing_fields", [])
        return f"""# {title}

{"Статус: заблокировано" if ru else "Status: blocked"}

## {"Чего не хватает" if ru else "Missing"}

{bullet_list(missing, '-', ru)}
"""
    return f"""# {title}

{experiment_table(experiments, ru)}

## {"Пороги качества эксперимента" if ru else "Experiment Quality Gates"}

{experiment_quality_table(experiments, ru)}
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

## Пайплайн запуска

{pipeline_table(data, ru)}

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

## Launch Pipeline

{pipeline_table(data, ru)}

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
        return f"| {'Сегмент' if ru else 'Segment'} | {'Задача' if ru else 'Job'} | {'Сдвиг убеждения' if ru else 'Belief shift'} | {'На чем основано' if ru else 'Support'} |\n| --- | --- | --- | --- |\n| {empty} | {empty} | {empty} | {empty} |"
    headers = ("Сегмент", "Задача", "Боль", "Сдвиг убеждения", "На чем основано", "Насколько уверенно") if ru else ("Segment", "Job", "Pain", "Belief shift", "Support", "Confidence")
    body = "\n".join(
        f"| {table_cell(row.get('segment'), ru)} | {table_cell(row.get('job'), ru)} | {table_cell(row.get('pain'), ru)} | {table_cell(row.get('belief_shift'), ru)} | {table_cell(row.get('support'), ru)} | {table_cell(confidence_label(str(row.get('confidence')), ru), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n{body}"


def funnel_map_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Шаг", "Что должно измениться в голове", "Что показать/сделать", "Действие пользователя", "Как понять, что шаг сработал") if ru else ("Step", "Belief", "Content", "CTA", "Metric")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n| - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('stage'), ru)} | {table_cell(row.get('target_belief'), ru)} | {table_cell(row.get('content'), ru)} | {table_cell(row.get('cta'), ru)} | {table_cell(row.get('metric'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n{body}"


def change_type_label(value: Any, ru: bool) -> str:
    text = str(value or "").strip()
    if not ru:
        return text or "-"
    return {
        "keep": "оставить",
        "replace": "заменить",
        "add": "добавить",
        "remove": "убрать",
        "instrument": "измерить",
        "clarify": "уточнить",
    }.get(text, text or "не указано")


def current_funnel_support_label(row: dict[str, Any], ru: bool) -> str:
    pieces = []
    claim_ids = ", ".join(list_items(row.get("claim_ids")))
    source_ids = ", ".join(list_items(row.get("source_ids")))
    assumption_ids = ", ".join(list_items(row.get("assumption_ids")))
    blocked_reason = dash(row.get("blocked_reason"), ru)
    assumption_notice = dash(row.get("assumption_notice"), ru)
    if claim_ids:
        pieces.append(("утверждения: " if ru else "claims: ") + claim_ids)
    if source_ids:
        pieces.append(("источники: " if ru else "sources: ") + source_ids)
    if assumption_ids:
        pieces.append(("допущения: " if ru else "assumptions: ") + assumption_ids)
    if blocked_reason not in {"-", "не указано"}:
        pieces.append(("блокер: " if ru else "blocked: ") + blocked_reason)
    if assumption_notice not in {"-", "не указано"}:
        pieces.append(("допущение: " if ru else "assumption: ") + assumption_notice)
    return "; ".join(pieces) or ("не указано" if ru else "-")


def current_funnel_diff_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = (
        ("Текущий шаг", "Предложенный шаг", "Тип изменения", "Почему", "Событие", "На чем основано")
        if ru
        else ("Current step", "Proposed step", "Change", "Reason", "Event", "Support")
    )
    if not rows:
        empty = "текущая воронка не предоставлена" if ru else "current funnel not provided"
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n| - | - | - | {empty} | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('current_step'), ru)} | {table_cell(row.get('proposed_step'), ru)} | {table_cell(change_type_label(row.get('change_type'), ru), ru)} | {table_cell(row.get('reason'), ru)} | {table_cell(row.get('measurement_event'), ru)} | {table_cell(current_funnel_support_label(row, ru), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n{body}"


def current_funnel_diff_section(diff: dict[str, Any], ru: bool) -> str:
    status = str(diff.get("status") or "")
    rows = diff.get("rows") if isinstance(diff.get("rows"), list) else []
    if status == "missing_current_funnel":
        message = (
            "Текущая воронка не предоставлена. Таблица ниже показывает только предложенный маршрут как допущение; она не выдумывает текущие шаги, метрики, каналы, тексты или инструменты."
            if ru
            else "No current funnel was provided. The table below shows only the proposed route as an assumption; it does not invent current steps, metrics, channels, copy, or tools."
        )
        return f"> **{message}**\n\n{current_funnel_diff_table(rows, ru)}"
    return current_funnel_diff_table(rows, ru)


def screen_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Экран/шаг", "Что должен поверить пользователь", "Что показать/спросить", "Действие пользователя", "Что нужно подтвердить", "На чем основано") if ru else ("Screen", "Target belief", "Content", "CTA", "Proof needed", "Support")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('stage'), ru)} | {table_cell(row.get('target_belief'), ru)} | {table_cell(row.get('content'), ru)} | {table_cell(row.get('cta'), ru)} | {table_cell(row.get('proof_needed'), ru)} | {table_cell(row.get('support'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n{body}"


def variant_type_label(value: Any, ru: bool) -> str:
    text = str(value or "")
    if not ru:
        return text or "-"
    return {
        "copy": "текст",
        "cta": "действие",
        "route": "маршрут",
        "proof_placement": "доказательство",
        "qualification": "квалификация",
    }.get(text, text or "не указано")


def variant_change_text(row: dict[str, Any], ru: bool) -> str:
    return dash(row.get("variant_copy") or row.get("variant_action"), ru)


def variant_control_text(row: dict[str, Any], ru: bool) -> str:
    current_step = str(row.get("current_step") or "").strip()
    if current_step:
        return current_step
    return dash(row.get("control_reference"), ru)


def variant_support_label(row: dict[str, Any], ru: bool) -> str:
    pieces = []
    claim_ids = ", ".join(list_items(row.get("claim_ids")))
    source_ids = ", ".join(list_items(row.get("source_ids")))
    assumption_ids = ", ".join(list_items(row.get("assumption_ids")))
    blocked_reason = dash(row.get("blocked_reason"), ru)
    if claim_ids:
        pieces.append(("утверждения: " if ru else "claims: ") + claim_ids)
    if source_ids:
        pieces.append(("источники: " if ru else "sources: ") + source_ids)
    if assumption_ids:
        pieces.append(("допущения: " if ru else "assumptions: ") + assumption_ids)
    if blocked_reason not in {"-", "не указано"}:
        pieces.append(("блокер: " if ru else "blocked: ") + blocked_reason)
    return "; ".join(pieces) or ("не указано" if ru else "-")


def variant_bundle_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = (
        ("Вариант", "Шаг", "Тип", "Контроль", "Что меняем", "Гипотеза", "Событие", "Доказательство и опора")
        if ru
        else ("Variant", "Stage", "Type", "Control", "Change", "Hypothesis", "Event", "Proof and support")
    )
    if not rows:
        empty = "нет вариантов с понятным событием" if ru else "no variants with a clear event"
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} | {headers[7]} |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| - | - | - | - | {empty} | - | - | - |"
    body = "\n".join(
        (
            f"| {table_cell(row.get('variant_id'), ru)} | {table_cell(row.get('stage') or row.get('funnel_stage'), ru)} | "
            f"{table_cell(variant_type_label(row.get('variant_type'), ru), ru)} | {table_cell(variant_control_text(row, ru), ru)} | "
            f"{table_cell(variant_change_text(row, ru), ru)} | {table_cell(row.get('hypothesis'), ru)} | "
            f"{table_cell(row.get('measurement_event'), ru)} | "
            f"{table_cell('; '.join([dash(row.get('proof_requirement'), ru), variant_support_label(row, ru)]), ru)} |"
        )
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} | {headers[7]} |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n{body}"


def tracking_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Событие", "Шаг", "Главная метрика", "Контрольный риск") if ru else ("Event", "Step", "Primary metric", "Guardrail")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n| - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('event_id') or event_name(row.get('stage'), ru), ru)} | {table_cell(row.get('stage'), ru)} | {table_cell(row.get('metric'), ru)} | {table_cell(row.get('guardrail'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n{body}"


def channel_route_rows(synthesis: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(synthesis, dict) or synthesis.get("status") != "matched":
        return []
    packs = synthesis.get("packs") if isinstance(synthesis.get("packs"), list) else []
    rows: list[dict[str, Any]] = []
    if packs and isinstance(packs[0], dict):
        primary = packs[0]
        rows.append(
            {
                "role": "primary",
                "label": primary.get("label"),
                "route": primary.get("journey"),
                "event_ids": primary.get("event_ids"),
                "risk": primary.get("risk"),
            }
        )
    support_loops = synthesis.get("support_loops") if isinstance(synthesis.get("support_loops"), list) else []
    for loop in support_loops:
        if not isinstance(loop, dict):
            continue
        rows.append(
            {
                "role": "support",
                "label": loop.get("label"),
                "route": loop.get("support_loop") or loop.get("journey"),
                "event_ids": loop.get("event_ids"),
                "risk": loop.get("risk") or loop.get("guardrail"),
            }
        )
    return rows


def channel_role_label(value: Any, ru: bool) -> str:
    text = str(value or "")
    if not ru:
        return {"primary": "Primary", "support": "Support loop"}.get(text, dash(value, ru))
    return {"primary": "основной путь", "support": "поддерживающий цикл"}.get(text, dash(value, ru))


def channel_route_table(synthesis: dict[str, Any], ru: bool) -> str:
    headers = ("Роль", "Канал", "Маршрут", "События", "Риск") if ru else ("Role", "Channel", "Route", "Event IDs", "Risk")
    rows = channel_route_rows(synthesis)
    if not rows:
        empty = "канальный маршрут не распознан" if ru else "no matched channel route"
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n| - | - | {empty} | - | - |"
    body = "\n".join(
        f"| {table_cell(channel_role_label(row.get('role'), ru), ru)} | {table_cell(row.get('label'), ru)} | {table_cell(row.get('route'), ru)} | {table_cell(', '.join(list_items(row.get('event_ids'))), ru)} | {table_cell(row.get('risk'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n{body}"


def channel_events_table(synthesis: dict[str, Any], ru: bool) -> str:
    headers = ("Канал", "Роль", "События") if ru else ("Channel", "Role", "Event IDs")
    rows = channel_route_rows(synthesis)
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} |\n| --- | --- | --- |\n| - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('label'), ru)} | {table_cell(channel_role_label(row.get('role'), ru), ru)} | {table_cell(', '.join(list_items(row.get('event_ids'))), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} |\n| --- | --- | --- |\n{body}"


def event_name(stage: Any, ru: bool) -> str:
    text = dash(stage, ru)
    return f"{text}: {'событие зафиксировано' if ru else 'event logged'}"


def experiment_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Название", "Гипотеза", "Что меняем", "Главная метрика", "Событие решения", "Когда считать успешным", "На чем основано") if ru else ("Name", "Hypothesis", "Change", "Metric", "Decision event", "Decision rule", "Support")
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} |\n| --- | --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('name'), ru)} | {table_cell(row.get('hypothesis'), ru)} | {table_cell(row.get('change'), ru)} | {table_cell(row.get('primary_metric'), ru)} | {table_cell(row.get('event_id'), ru)} | {table_cell(row.get('decision_rule'), ru)} | {table_cell(row.get('support'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} |\n| --- | --- | --- | --- | --- | --- | --- |\n{body}"


def experiment_quality_table(rows: list[dict[str, Any]], ru: bool) -> str:
    low_traffic = any(
        "too low for reliable srm" in str(row.get("srm_check") or "").lower()
        or "трафика мало" in str(row.get("srm_check") or "").lower()
        for row in rows
        if isinstance(row, dict)
    )
    if low_traffic:
        headers = (
            ("Событие", "План обучения", "Проверка качества", "Оставить / итерировать", "Риск ошибки")
            if ru
            else ("Event", "Learning plan", "Quality check", "Ship / iterate", "Failure mode")
        )
        if not rows:
            return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n| - | - | - | - | - |"
        body = "\n".join(
            (
                f"| {table_cell(row.get('event_id'), ru)} | {table_cell(row.get('expected_effect_range'), ru)} | "
                f"{table_cell(row.get('event_instrumentation'), ru)} | "
                f"{table_cell('; '.join([dash(row.get('ship_rule'), ru), dash(row.get('iterate_rule'), ru)]), ru)} | "
                f"{table_cell(row.get('failure_mode'), ru)} |"
            )
            for row in rows
        )
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |\n| --- | --- | --- | --- | --- |\n{body}"
    headers = (
        ("Событие", "Экспозиция", "Контрольные метрики", "SRM", "Потеря событий", "Ожидаемый эффект", "Остановить / оставить / итерировать", "Риск ошибки")
        if ru
        else ("Event", "Exposure", "Guardrails", "SRM check", "Event loss", "Expected effect", "Stop / ship / iterate", "Failure mode")
    )
    if not rows:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} | {headers[7]} |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| - | - | - | - | - | - | - | - |"
    body = "\n".join(
        (
            f"| {table_cell(row.get('event_id'), ru)} | {table_cell(row.get('exposure_definition'), ru)} | "
            f"{table_cell(row.get('guardrail_metrics'), ru)} | {table_cell(row.get('srm_check'), ru)} | "
            f"{table_cell(row.get('event_loss_threshold'), ru)} | {table_cell(row.get('expected_effect_range'), ru)} | "
            f"{table_cell('; '.join([dash(row.get('stop_rule'), ru), dash(row.get('ship_rule'), ru), dash(row.get('iterate_rule'), ru)]), ru)} | "
            f"{table_cell(row.get('failure_mode'), ru)} |"
        )
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} | {headers[6]} | {headers[7]} |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n{body}"


def risk_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Риск", "Уровень", "Что сделать", "На чем основано") if ru else ("Risk", "Level", "Mitigation", "Support")
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
        f"| {table_cell(row.get('id'), ru)} | {table_cell(row.get('statement'), ru)} | {table_cell(usage_label(row.get('used_in'), ru), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} |\n| --- | --- | --- |\n{body}"


def benchmark_assumptions_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("ID", "Метрика", "Ориентир", "Статус") if ru else ("ID", "Metric", "Prior", "Status")
    if not rows:
        empty = "нет benchmark-допущений" if ru else "no benchmark assumptions"
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n| - | - | - | {empty} |"
    label = "допущение, не доказанный факт" if ru else "assumption, not a proven fact"
    body = "\n".join(
        f"| {table_cell(row.get('id'), ru)} | {table_cell(row.get('metric'), ru)} | {table_cell(row.get('range'), ru)} | {label} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n{body}"


def visual_support_badge(node: dict[str, Any], ru: bool) -> str:
    if node.get("blocked_reason"):
        return "Блокер" if ru else "Blocked"
    if str(node.get("evidence_mode") or "") == "assumption_backed":
        return "Допущение" if ru else "Assumption"
    return "Источник" if ru else "Source"


def funnel_visual_block(visual: dict[str, Any], ru: bool) -> str:
    nodes = visual.get("nodes") if isinstance(visual.get("nodes"), list) else []
    if not nodes:
        return ""
    title = "Визуальная карта пути" if ru else "Visual Funnel Map"
    node_html = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        mode = "assumption-backed" if str(node.get("evidence_mode") or "") == "assumption_backed" else "source-backed"
        if node.get("blocked_reason"):
            mode += " blocked"
        assumption_ids = ", ".join(list_items(node.get("assumption_ids")))
        meta_parts = [
            str(node.get("event") or "").strip(),
            ("допущения: " + assumption_ids) if ru and assumption_ids else ("assumptions: " + assumption_ids) if assumption_ids else "",
        ]
        meta = " / ".join(part for part in meta_parts if part)
        node_html.append(
            "<div class=\"funnel-node {mode}\">"
            "<span class=\"funnel-badge\">{badge}</span>"
            "<strong>{label}</strong>"
            "<p>{belief}</p>"
            "<small>{meta}</small>"
            "</div>".format(
                mode=mode,
                badge=escape(visual_support_badge(node, ru)),
                label=escape(str(node.get("label") or "")),
                belief=escape(str(node.get("belief") or node.get("action") or "")),
                meta=escape(meta),
            )
        )
    return f"""### {title}

<div class="funnel-visual" role="img" aria-label="{title}">
{''.join(node_html)}
</div>"""


def promise_status_label(value: Any, ru: bool) -> str:
    text = str(value or "")
    if not ru:
        return text or "-"
    return {
        "source_backed": "подтверждено источником",
        "asset_backed": "есть внутренний артефакт доказательства",
        "weak_proof": "доказательство слабое",
        "no_proof": "доказательства нет",
        "risky_unverified": "рискованное обещание не подтверждено",
    }.get(text, text or "не указано")


def promise_proof_table(rows: list[dict[str, Any]], ru: bool) -> str:
    headers = ("Обещание", "Возражение", "Что доказать", "Формат proof", "Статус", "Запасной вариант") if ru else ("Promise", "Objection", "Proof requirement", "Proof format", "Status", "Fallback")
    if not rows:
        empty = "нет проверенных обещаний" if ru else "no promise checks"
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n| {empty} | - | - | - | - | - |"
    body = "\n".join(
        f"| {table_cell(row.get('promise'), ru)} | {table_cell(row.get('objection'), ru)} | {table_cell(row.get('proof_requirement'), ru)} | {table_cell(proof_mechanic_label(row.get('recommended_proof_mechanic'), ru), ru)} | {table_cell(promise_status_label(row.get('evidence_status'), ru), ru)} | {table_cell(row.get('fallback'), ru)} |"
        for row in rows
    )
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |\n| --- | --- | --- | --- | --- | --- |\n{body}"


def proof_mechanic_label(value: Any, ru: bool) -> str:
    if not isinstance(value, dict):
        return "не указано" if ru else "-"
    pieces = [
        str(value.get("recommended_format") or "").strip(),
        str(value.get("placement") or "").strip(),
    ]
    return "; ".join(piece for piece in pieces if piece) or ("не указано" if ru else "-")


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


def list_items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    if str(value or "").strip():
        return [str(value).strip()]
    return []


def niche_profile_section(profile: dict[str, Any], ru: bool) -> str:
    status = str(profile.get("status") or "")
    if status != "matched":
        return "- " + ("Профиль не распознан; используется общий путь." if ru else "No niche profile matched; using the generic path.")
    rows = [
        ("Профиль" if ru else "Profile", profile.get("label")),
        ("Словарь" if ru else "Vocabulary", ", ".join(list_items(profile.get("vocabulary")))),
        ("Funnel defaults" if not ru else "Базовый путь", "; ".join(list_items(profile.get("funnel_defaults")))),
        ("Proof patterns" if not ru else "Форматы proof", "; ".join(list_items(profile.get("proof_patterns")))),
        ("Риски" if ru else "Risks", "; ".join(list_items(profile.get("risks")))),
        ("Matched terms" if not ru else "Сигналы профиля", ", ".join(list_items(profile.get("matched_terms")))),
    ]
    summary = dash(profile.get("summary_text"), ru)
    return f"{rows_table(rows, 'Поле' if ru else 'Field', 'Значение' if ru else 'Value', ru)}\n\n> **{summary}**"


def niche_events_table(profile: dict[str, Any], ru: bool) -> str:
    headers = ("Событие", "Назначение") if ru else ("Event", "Purpose")
    events = list_items(profile.get("event_suggestions")) if isinstance(profile, dict) else []
    defaults = list_items(profile.get("funnel_defaults")) if isinstance(profile, dict) else []
    if not events:
        return f"| {headers[0]} | {headers[1]} |\n| --- | --- |\n| - | - |"
    rows = []
    for index, event in enumerate(events):
        purpose = defaults[index] if index < len(defaults) else profile.get("summary_text")
        rows.append(f"| {table_cell(event, ru)} | {table_cell(purpose, ru)} |")
    return f"| {headers[0]} | {headers[1]} |\n| --- | --- |\n" + "\n".join(rows)


def competitor_synthesis_status(value: Any, ru: bool) -> str:
    status = str(value or "").strip()
    if not ru:
        return status or "-"
    return {
        "observed": "наблюдаемые паттерны найдены",
        "insufficient_competitor_patterns": "недостаточно повторяемых паттернов",
    }.get(status, status or "не указано")


def competitor_synthesis_section(synthesis: dict[str, Any], ru: bool) -> str:
    status = str(synthesis.get("status") or "")
    source_ids = ", ".join(list_items(synthesis.get("source_ids"))) or ("нет" if ru else "-")
    if status != "observed":
        message = (
            "Повторяемых конкурентных паттернов пока недостаточно; финальный отчет не должен выдумывать цены, призывы к действию, доказательства или первые шаги конкурентов."
            if ru
            else "Repeatable competitor patterns are not strong enough yet; the final report must not invent competitor pricing, CTAs, proof, or onboarding."
        )
        return f"- {'Статус' if ru else 'Status'}: {competitor_synthesis_status(status, ru)}\n- {'Source IDs' if not ru else 'ID источников'}: {source_ids}\n\n> **{message}**"
    return (
        f"- {'Статус' if ru else 'Status'}: {competitor_synthesis_status(status, ru)}\n"
        f"- {'Source IDs' if not ru else 'ID источников'}: {source_ids}\n\n"
        f"{competitor_patterns_table(synthesis.get('patterns'), ru)}\n\n"
        f"### {'Наблюдаемые слабые места' if ru else 'Observed Weaknesses'}\n\n"
        f"{competitor_weaknesses_table(synthesis.get('observations'), ru)}"
    )


def competitor_patterns_table(patterns: Any, ru: bool) -> str:
    headers = ("Паттерн", "Наблюдения", "ID источников", "Сколько строк") if ru else ("Pattern", "Values", "Source IDs", "Rows")
    if not isinstance(patterns, dict) or not patterns:
        return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n| - | - | - | - |"
    order = ["positioning", "pricing", "primary_cta", "onboarding_pattern", "proof", "first_value_path", "observed_weaknesses"]
    rows = []
    for key in order:
        pattern = patterns.get(key)
        if not isinstance(pattern, dict):
            continue
        values = "; ".join(list_items(pattern.get("values")))
        source_ids = ", ".join(list_items(pattern.get("source_ids")))
        rows.append(
            f"| {table_cell(pattern.get('label'), ru)} | {table_cell(values, ru)} | {table_cell(source_ids, ru)} | {table_cell(pattern.get('observation_count'), ru)} |"
        )
    if not rows:
        rows.append("| - | - | - | - |")
    return f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |\n| --- | --- | --- | --- |\n" + "\n".join(rows)


def competitor_weaknesses_table(observations: Any, ru: bool) -> str:
    headers = ("Конкурент", "Слабое место", "ID источников") if ru else ("Competitor", "Weakness", "Source IDs")
    rows = []
    if isinstance(observations, dict):
        for observation in observations.get("observed_weaknesses", []):
            if not isinstance(observation, dict):
                continue
            rows.append(
                f"| {table_cell(observation.get('competitor'), ru)} | {table_cell(observation.get('value'), ru)} | {table_cell(', '.join(list_items(observation.get('source_ids'))), ru)} |"
            )
    if not rows:
        rows.append("| - | - | - |")
    return f"| {headers[0]} | {headers[1]} | {headers[2]} |\n| --- | --- | --- |\n" + "\n".join(rows)


def competitor_table(rows: list[dict[str, str]], ru: bool) -> str:
    headers = ("Конкурент", "Как себя подает", "Цена", "Призыв к действию", "Первые шаги пользователя", "Дата проверки", "Насколько уверенно", "Источник") if ru else ("Competitor", "Positioning", "Pricing", "CTA", "Onboarding", "Retrieved", "Confidence", "Source")
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
                f"### {role_label(result.get('role'), ru)}: {dash(result.get('topic_id'), ru)}\n\n"
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
    pipeline_title = "Пайплайн запуска" if ru else "Launch Pipeline"
    pipeline = markdown_to_html(f"## {pipeline_title}\n\n{pipeline_table(data, ru)}")
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
    h2 {{ font-size: 24px; margin: 34px 0 12px; }}
    p {{ color: #627386; font-size: 18px; }}
    table {{ border-collapse: separate; border-spacing: 0; width: 100%; margin: 16px 0 28px; background: #fff; border: 1px solid #d9e0e7; border-radius: 8px; overflow: hidden; }}
    th, td {{ border: 1px solid #d9e0e7; padding: 9px 11px; text-align: left; vertical-align: top; }}
    th {{ background: #edf3f5; color: #425466; font-size: 13px; }}
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
    {pipeline}
    <div class="index-grid">
      {links}
    </div>
  </main>
</body>
</html>
"""
    write_text_file(final_dir(workspace) / "index.html", html)


def write_standalone_html(
    workspace: Path,
    data: dict[str, Any],
    nav: list[tuple[str, str]],
    page_markdowns: dict[str, str],
) -> None:
    ru = is_russian(data)
    language = output_language(data)
    lang = "ru" if ru else "en"
    title = "Единый отчет по воронке" if ru else "Standalone Growth Funnel Report"
    intro = (
        "Один HTML-файл со всеми разделами. Он не требует localhost, дополнительных файлов или ссылок на соседние страницы."
        if ru
        else "One HTML file with every section. It does not require localhost, extra files, or links to sibling pages."
    )
    nav_html = "\n".join(
        f'<a class="nav-link" href="#{escape(slug)}"><span>{number + 1:02d}</span>{escape(page_title)}</a>'
        for number, (slug, page_title) in enumerate(nav)
    )
    sections = "\n".join(
        f'<section id="{escape(slug)}" class="report-section"><div class="section-number">{number + 1:02d}</div>{markdown_to_html(page_markdowns.get(slug, ""))}</section>'
        for number, (slug, _) in enumerate(nav)
    )
    pipeline_title = "Пайплайн запуска" if ru else "Launch Pipeline"
    pipeline = markdown_to_html(f"## {pipeline_title}\n\n{pipeline_table(data, ru)}")
    html = f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #17202a; --muted: #627386; --line: #d9e0e7; --accent: #0f766e; --bg: #f7f9fb; --warn: #b45309; --bad: #b42318; --good: #047857; }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
    .layout {{ display: grid; grid-template-columns: minmax(220px, 300px) minmax(0, 1fr); min-height: 100vh; }}
    nav {{ border-right: 1px solid var(--line); background: #fff; padding: 24px 18px; position: sticky; top: 0; height: 100vh; overflow: auto; }}
    .brand {{ font-size: 13px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 16px; }}
    .nav-link {{ display: flex; gap: 10px; align-items: baseline; padding: 9px 10px; margin: 2px 0; border-radius: 6px; color: var(--ink); text-decoration: none; font-size: 14px; }}
    .nav-link span {{ color: var(--accent); font-weight: 700; }}
    .nav-link:hover {{ background: #e7f5f2; color: #0f5f59; }}
    main {{ max-width: 1120px; padding: 42px 42px 88px; }}
    .hero {{ margin-bottom: 28px; }}
    .hero h1 {{ font-size: 40px; line-height: 1.1; margin: 0 0 12px; }}
    .hero p {{ color: var(--muted); font-size: 18px; line-height: 1.55; max-width: 780px; }}
    .jump-start {{ display: inline-block; margin-top: 10px; color: #fff; background: var(--accent); padding: 11px 15px; border-radius: 6px; text-decoration: none; }}
    .report-section {{ position: relative; margin-top: 28px; padding: 30px 0 12px; border-top: 1px solid var(--line); scroll-margin-top: 24px; }}
    .section-number {{ display: inline-block; margin-bottom: 14px; padding: 4px 8px; border-radius: 999px; background: #e7f5f2; color: #0f5f59; font-size: 12px; font-weight: 700; }}
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
    .funnel-visual {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 16px 0 28px; }}
    .funnel-node {{ position: relative; min-height: 150px; border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 16px; }}
    .funnel-node::after {{ content: "→"; position: absolute; right: -13px; top: 50%; transform: translateY(-50%); color: var(--muted); font-weight: 700; }}
    .funnel-node:last-child::after {{ content: ""; }}
    .funnel-node p {{ margin: 10px 0; font-size: 14px; line-height: 1.45; }}
    .funnel-node small {{ display: block; color: var(--muted); line-height: 1.4; }}
    .funnel-node.assumption-backed {{ background: #fffbeb; border-color: #f7c948; }}
    .funnel-node.blocked {{ background: #fff1f0; border-color: #ffb4ad; }}
    .funnel-badge {{ display: inline-block; margin-bottom: 8px; padding: 3px 7px; border-radius: 999px; background: #eef2f5; color: #425466; font-size: 12px; font-weight: 700; }}
    .assumption-backed .funnel-badge {{ background: #fef3c7; color: #92400e; }}
    .blocked .funnel-badge {{ background: #fee2e2; color: #991b1b; }}
    @media (max-width: 760px) {{ .layout {{ display: block; }} nav {{ position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }} main {{ padding: 28px 20px 56px; }} .hero h1 {{ font-size: 32px; }} }}
  </style>
</head>
<body>
  <div class="layout">
    <nav>
      <div class="brand">{escape(ui_text(language, "brand"))}</div>
      {nav_html}
    </nav>
    <main>
      <header class="hero">
        <h1>{escape(title)}</h1>
        <p>{escape(intro)}</p>
        <a class="jump-start" href="#00_index">{escape(ui_text(language, "start"))}</a>
      </header>
      {pipeline}
      {sections}
    </main>
  </div>
</body>
</html>
"""
    write_text_file(final_dir(workspace) / "standalone.html", html)


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
    page_markdowns: dict[str, str] = {}
    for slug, title in nav:
        markdown = page_builders[slug](data)
        page_markdowns[slug] = markdown
        write_final_page(workspace, slug, title, markdown, nav, output_language(data))
    write_index_html(workspace, data, nav)
    write_standalone_html(workspace, data, nav, page_markdowns)
    summary = validate_and_write(workspace)
    leaks = final_leakage(workspace)
    final_index = final_dir(workspace) / "index.html"
    final_standalone = final_dir(workspace) / "standalone.html"
    link_label = "Открыть финальный HTML" if is_russian(data) else "Open final HTML"
    standalone_label = "Открыть единый HTML" if is_russian(data) else "Open standalone HTML"
    summary["rendered"] = True
    summary["recommendations_ready"] = summary.get("phase") == "ready"
    summary["ready_to_test"] = summary.get("phase") == "ready"
    summary["final_index_path"] = str(final_index)
    summary["final_index_chat_link"] = markdown_file_link(final_index, link_label)
    summary["final_standalone_path"] = str(final_standalone)
    summary["final_standalone_chat_link"] = markdown_file_link(final_standalone, standalone_label)
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
