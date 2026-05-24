# Orchestration

Use this when splitting work across specialists or recording specialist outputs.

## Roles

Prefer three compact roles:

- `intake_research`: normalize user context, missing fields, source evidence, competitor observations, metrics, and constraints.
- `synthesis`: draft recommendations from normalized state and compile decision-grade insights into `runtime/insights.json`.
- `review_render`: review readiness, render the final pack, and check leakage.

Compatibility aliases remain valid when older contracts already exist: `intake`, `planner`, `research`, `competitor`, and `compiler_reviewer`.

## Result Contract

Specialists return one JSON object:

```json
{
  "role": "intake_research",
  "specialist": "intake_research",
  "topic_id": "research_evidence",
  "task_id": "research-1",
  "objective": "Verify current-practice evidence for the main recommendation.",
  "input_refs": ["runtime/intake.json"],
  "context_refs": ["runtime/gaps.json"],
  "output_refs": ["runtime/sources.jsonl", "runtime/agent_results.jsonl"],
  "artifact_refs": ["runtime/sources.jsonl"],
  "summary": "Short synthesis",
  "key_findings": ["Finding"],
  "citations": [{"url": "https://example.com", "title": "Example"}],
  "claim_ids": [],
  "source_ids": [],
  "assumption_ids": ["A1"],
  "blocked_reason": "Need two more independent sources before launch handoff is ready.",
  "status": "blocked",
  "freshness_date": "2026-05-15",
  "confidence": "medium",
  "open_questions": ["Question"],
  "next_action": "Recommended next step"
}
```

Record results with:

```bash
python3 scripts/record_agent_result.py "<workspace-dir>" --input "<result.json>" --json
```

Validation writes `runtime/orchestration_contract.json`. Each task row includes `task_id`, `role`, `specialist`, `objective`, `input_refs`, `context_refs`, `output_refs`, `artifact_refs`, `claim_ids`, `source_ids`, `assumption_ids`, `blocked_reason`, `status`, `created_at`, and `updated_at`. If launch handoff is requested, the same contract is exported to `exports/orchestration_contract.json` and `.csv`.

## Boundaries

- Specialists write to runtime artifacts only through scripts or clear normalized notes.
- Only `review_render` writes `final/`.
- Subagents should return summaries and source rows, not raw browsing transcripts.
- Raw orchestration contracts stay in `runtime/` or `exports/`; `final/` may show only readable summaries.
- Sensitive external writes require user approval.

## Synthesis Contract

Before rendering, the synthesis role must ensure:

- each segment, screen, and experiment has `support`;
- `support` points to an evidence ref or explicit assumption;
- blocked or weak evidence is visible to the user as a launch blocker, not silently converted into proof;
- the first action is concrete enough for a marketer to execute.
