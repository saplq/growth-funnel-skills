# Implementation Chunks

## 1. Repo Recovery and Plan Folder

- Create `implementation-plan/`.
- Record the v2 architecture and progress tracker.
- Treat old tracked deletions as context, not as a command to restore every file unchanged.

## 2. Skill Skeleton

- Restore `skills/designing-growth-funnels/SKILL.md`.
- Keep instructions concise and use progressive disclosure.
- Replace old references with v2 references: intake, research, orchestration, funnel, tracking, final pack.
- Sync `agents/openai.yaml` with the expanded deep-research trigger scope.

## 3. Runtime Scripts

- Implement idempotent create, validate, ingest, record, and render scripts.
- Use Python standard library only.
- Print structured JSON to stdout; send diagnostics to stderr.
- Keep all writes inside the provided workspace path.

## 4. Final Compiler

- Render ordered Markdown and semantic self-contained HTML.
- Delete or block raw runtime formats from `final/`.
- Include status, evidence, competitors, funnel blueprint, screens, tracking, experiment, risks, and execution plan.

## 5. Research and Orchestration

- Normalize source provenance and competitor rows.
- Record specialist outputs through `record_agent_result.py`.
- Mark stale or missing research as gaps instead of blocking the minimum input gate.

## 6. Tests and Evals

- Add unit tests for empty, partial, rich, Russian, no-proof, conflict, source, competitor, resume, and final-pack leakage cases.
- Add trigger and output-quality eval fixtures.
- Run compile checks.

## 7. README, Security, Release

- Update install and usage docs for v2 scripts and workspace layout.
- Keep security docs aligned with offline deterministic scripts.
- Preserve cross-agent installation instructions.
