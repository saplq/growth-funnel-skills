# Artifact Contracts

## `runtime/run_state.json`

```json
{
  "version": "2.0.0",
  "workspace_name": "Acme funnel",
  "output_language": "Russian",
  "phase": "intake",
  "minimum_gate_satisfied": false,
  "scores": {
    "completeness": 40,
    "qualification": 35,
    "research_readiness": 10
  },
  "artifact_status": {
    "intake": "partial",
    "research": "blocked",
    "final": "blocked"
  },
  "critical_missing_fields": ["target_kpi"],
  "evidence_gaps": ["source registry has no current sources"],
  "next_best_input": ["What single KPI should this funnel improve?"]
}
```

## `runtime/intake.json`

Stores normalized product and funnel context. Required minimum gate fields:

- `offer`
- `icp` or `primary_persona`
- `target_kpi`
- `primary_channel`
- `proof_assets` or `explicit_no_proof_yet`

## `runtime/sources.jsonl`

Each line is one source:

```json
{"source_id":"source-1","url":"https://example.com/pricing","title":"Pricing","publisher":"example.com","retrieved_at":"2026-05-15","source_type":"pricing","freshness":"current","confidence":"medium","used_in":["research_evidence"]}
```

For pricing, changelog, and current-practice facts, `retrieved_at` is required. Missing dates create evidence gaps.

## `runtime/competitors.csv`

Required headers:

```text
competitor,domain,positioning,pricing,primary_cta,onboarding_pattern,proof,first_value_path,observed_weaknesses,source,confidence,retrieved_at,notes
```

## `runtime/agent_results.jsonl`

Each line is one specialist result:

```json
{
  "role": "research",
  "topic_id": "research_evidence",
  "task_id": "research-1",
  "summary": "Short synthesis",
  "key_findings": ["Finding 1"],
  "citations": [{"url": "https://example.com", "title": "Example"}],
  "freshness_date": "2026-05-15",
  "confidence": "medium",
  "open_questions": ["Question"],
  "next_action": "Ingest competitor pricing"
}
```

## `final/`

- Must contain only `.md` and `.html`.
- Markdown must not start with YAML frontmatter.
- HTML must be self-contained with inline styles and navigation.
- No runtime JSON, JSONL, CSV, YAML, traces, or separate CSS files may appear in `final/`.
