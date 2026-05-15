# Final Pack

Use this when rendering or reviewing `final/`.

## Requirements

- `final/` contains only `.md` and `.html`.
- Every Markdown file has a matching HTML page.
- Markdown does not start with YAML frontmatter.
- HTML is self-contained with inline CSS, semantic structure, navigation, and next/previous links.
- Pages separate ready recommendations from blocked assumptions.
- Evidence and competitor claims cite source rows by URL or title when available.
- HTML should make the decision faster to understand than raw Markdown: use callouts, compact tables, evidence/confidence badges, and risk heatmap styling.
- Markdown should be readable as a standalone expert report, not a runtime dump.

## Insight Layer

Render from `runtime/insights.json`, not directly from loose text blobs. The object must include:

- `decision_summary`
- `segments`
- `screens`
- `experiments`
- `risks`
- `evidence_refs`
- `assumptions`
- `confidence`

Every recommendation in `segments`, `screens`, and `experiments` needs a `support` value that points to an evidence ref or explicit assumption.

## Default Pages

Keep legacy filenames for compatibility, but render them in a user-first order:

1. `00_index`: start here and first action.
2. `01_status_next_steps`: decision summary and readiness.
3. `02_intake_brief`: segments, jobs, and normalized context.
4. `03_research_evidence`: evidence refs and assumptions.
5. `04_competitor_map`: competitor patterns.
6. `05_funnel_blueprint`: funnel map.
7. `06_screen_specs`: screen playbook.
8. `07_tracking_plan`: tracking and KPIs.
9. `08_experiment_card`: next experiment.
10. `09_risks_and_gaps`: risk heatmap and gaps.
11. `10_execution_plan`: execution plan.

## Review Checklist

- No raw runtime files leaked.
- Missing proof stays marked as missing.
- Current-sensitive claims have retrieval dates.
- The next step is operational, not a broad brainstorm.
- `recommendations_ready` is true only when `phase == "ready"`.
- Russian output does not keep English UI strings such as "Intake brief", "Research evidence", "Previous", or "Next".
