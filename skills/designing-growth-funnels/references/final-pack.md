# Final Pack

Use this when rendering or reviewing `final/`.

## Requirements

- Default output is one self-contained `final/index.html` file with inline CSS and anchor navigation.
- Do not create separate user-facing HTML pages such as `05_funnel_blueprint.html` unless legacy multi-page output was explicitly requested.
- `final/` must not contain `localhost`, generated `claudeusercontent.com` URLs, separate CSS files, local links to other HTML files, YAML, CSV, JSON, or JSONL.
- Machine-readable launch handoffs belong in `exports/`, not `final/`.
- Legacy multi-page mode may emit Markdown plus matching HTML pages, but it is not the default.
- Markdown does not start with YAML frontmatter.
- HTML is self-contained with inline CSS, semantic structure, anchor navigation, cards/badges/tables, and risk signals.
- Pages separate ready-to-test recommendations from launch blockers.
- Evidence and competitor claims cite source rows by URL or title when available.
- User-provided competitor archetypes without URL and retrieval date are observations, not a sourced competitor map.
- If live/current research did not run or produced no usable rows, show an explicit `research_missing` / "исследование не проведено" block before recommendations.
- Niche profiles render as readable vocabulary, risks, proof formats, funnel defaults, and event suggestions, not raw `niche_profile` JSON.
- Current-vs-proposed funnel changes render as a readable table, not raw `current_funnel_diff` JSON; missing current funnel is shown as an assumption, not invented current steps.
- Funnel visual maps render from `funnel_visual` as a readable visual path; assumption-backed nodes are highlighted in yellow.
- Copy/action variant bundles render as a readable table with hypothesis, event, proof requirement, and support refs, not raw `variant_bundles` JSON.
- Reviewer approval renders as status plus review items, not raw `reviewer_approval` JSON; approval handoff files belong in `exports/`.
- Orchestration/task-result contracts stay in `runtime/orchestration_contract.json` or `exports/orchestration_contract.*`, not `final/`.
- HTML should make the decision faster to understand than raw Markdown: use callouts, compact tables, evidence/confidence badges, and risk heatmap styling.
- The HTML should be readable as a standalone expert report, not a runtime dump.
- Start pages and execution pages must include a plain operational pipeline: what to do, why, what the user gets, and which proof/data is missing.
- Status/next-step sections must show the `user_inputs/` folder path and `00_next_input.md` so the user knows exactly where to add missing context.
- Localized output should use the user's business vocabulary. In Russian output, avoid untranslated internal labels such as "CTA", "guardrail", "support", "skeleton", "ICP", and raw snake_case path names unless they appear inside technical event/file identifiers.
- The agent's final chat message must lead with a clickable Markdown link to the absolute `final/index.html` file. Prefer the `final_index_chat_link` value returned by `render_final.py`.

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

## Default Sections

Render these sections inside the single `index.html` in a user-first order. Use plain anchor IDs such as `#funnel-map`, not legacy page-like IDs. Keep legacy slugs only when the user explicitly requests multi-page output:

1. Start here and first action.
2. Decision summary and readiness.
3. Segments, jobs, and normalized context.
4. Evidence refs and assumptions.
5. Competitor patterns.
6. Funnel map.
7. Screen playbook.
8. Tracking and KPIs.
9. Next experiment.
10. Risk heatmap and gaps.
11. Execution plan.

## Review Checklist

- No raw runtime files leaked.
- Missing proof can be ready to test only when visibly assumption-backed; it must stay blocked for launch handoff.
- Current-sensitive claims have retrieval dates.
- The next step is operational, not a broad brainstorm.
- `recommendations_ready` and `ready_to_test` are true only when `phase == "ready"`.
- `ready_for_launch` is true only when evidence, proof, approval, and row-level launch blockers are clear.
- Russian output does not keep English UI strings such as "Intake brief", "Research evidence", "Previous", or "Next".
- Russian output explains the launch pipeline in plain language: "что сделать", "зачем", and "что получишь".
- Final handoff is not just a raw path or shell command; it includes a clickable local-file Markdown link to `final/index.html`.
