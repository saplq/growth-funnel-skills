# Final Pack

Use this when rendering or reviewing `final/`.

## Requirements

- `final/` contains only `.md` and `.html`.
- Machine-readable launch handoffs belong in `exports/`, not `final/`.
- Every Markdown file has a matching HTML page.
- Markdown does not start with YAML frontmatter.
- Per-page HTML is self-contained with inline CSS, semantic structure, navigation, and next/previous links.
- `standalone.html` is the portable artifact file: it contains all sections in one document, uses inline CSS and internal `#section` navigation only, and does not link to sibling `.html` files.
- Pages separate ready-to-test recommendations from launch blockers.
- Evidence and competitor claims cite source rows by URL or title when available.
- Niche profiles render as readable vocabulary, risks, proof formats, funnel defaults, and event suggestions, not raw `niche_profile` JSON.
- Current-vs-proposed funnel changes render as a readable table, not raw `current_funnel_diff` JSON; missing current funnel is shown as an assumption, not invented current steps.
- Funnel visual maps render from `funnel_visual` as a readable visual path; assumption-backed nodes are highlighted in yellow.
- Copy/action variant bundles render as a readable table with hypothesis, event, proof requirement, and support refs, not raw `variant_bundles` JSON.
- Reviewer approval renders as status plus review items, not raw `reviewer_approval` JSON; approval handoff files belong in `exports/`.
- Orchestration/task-result contracts stay in `runtime/orchestration_contract.json` or `exports/orchestration_contract.*`, not `final/`.
- HTML should make the decision faster to understand than raw Markdown: use callouts, compact tables, evidence/confidence badges, and risk heatmap styling.
- Markdown should be readable as a standalone expert report, not a runtime dump.
- Start pages and execution pages must include a plain operational pipeline: what to do, why, what the user gets, and which proof/data is missing.
- Status/next-step pages must show the `user_inputs/` folder path and `00_next_input.md` so the user knows exactly where to add missing context.
- Localized output should use the user's business vocabulary. In Russian output, avoid untranslated internal labels such as "CTA", "guardrail", "support", "skeleton", "ICP", and raw snake_case path names unless they appear inside technical event/file identifiers.
- The agent's final chat message must lead with `final_standalone_chat_link` when available. Use `final_index_chat_link` only as a local navigation fallback. Hosted artifact surfaces such as Claude.ai and ChatGPT should present or attach `final/standalone.html`, not manually constructed CDN URLs and not child-page links.

## Insight Layer

Render from `runtime/insights.json`, not directly from loose text blobs. The object must include:

- `decision_summary`
- `segments`
- `screens`
- `experiments`
- `risks`
- `evidence_refs`
- `current_funnel_diff`
- `variant_bundles`
- `reviewer_approval`
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
- Missing proof can be ready to test only when visibly assumption-backed; it must stay blocked for launch handoff.
- Current-sensitive claims have retrieval dates.
- The next step is operational, not a broad brainstorm.
- `recommendations_ready` and `ready_to_test` are true only when `phase == "ready"`.
- `ready_for_launch` is true only when evidence, proof, approval, and row-level launch blockers are clear.
- Russian output does not keep English UI strings such as "Intake brief", "Research evidence", "Previous", or "Next".
- Russian output explains the launch pipeline in plain language: "что сделать", "зачем", and "что получишь".
- Final handoff is not just a raw path or shell command; it includes a clickable local-file Markdown link to `final/standalone.html`, with `final/index.html` only as an optional local fallback.
