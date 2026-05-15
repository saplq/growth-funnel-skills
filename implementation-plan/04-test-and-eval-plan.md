# Test and Eval Plan

## Unit Tests

- Empty workspace creates `runtime/` and `final/` structure.
- Partial notes update intake and keep blocked recommendations blocked.
- Rich SaaS notes satisfy minimum gate and render all final pages.
- Russian language creates Russian status/final text.
- `No proof yet` satisfies the proof gate but lowers qualification.
- Proof plus `No proof yet` creates a contradiction warning.
- Research notes add source rows with provenance.
- Competitor notes add competitor rows.
- Re-running create/validate/render is idempotent.
- `final/` rejects raw `.json`, `.jsonl`, `.csv`, `.yaml`, `.yml`, and `.css`.

## Evals

Maintain two fixtures:

- `evals/trigger_queries.json`: prompts that should and should not activate the skill.
- `evals/output_quality_cases.json`: realistic cases and expected qualities.

## Forward Testing

Use fresh subagents only after core tests pass. Pass only the skill path, task prompt, input files, and output directory. Do not pass expected answers or hidden diagnosis.

Suggested prompts:

- Empty founder idea with no proof.
- Existing SaaS onboarding with metrics and current competitors.
- Russian-language funnel request with pasted notes.
- Research-heavy request requiring external sources.

## Acceptance

- Tests and compile checks pass.
- Final package has no runtime leakage.
- Missing evidence is shown as gaps, not fabricated claims.
- Scripts remain offline and stdlib-only.
