# Orchestration

Use this when splitting work across specialists or recording specialist outputs.

## Roles

- `intake`: normalize user context and missing fields.
- `planner`: create topics and bounded tasks.
- `research`: gather current sources and practice patterns.
- `competitor`: gather competitor observations.
- `synthesis`: draft recommendations from normalized state and compile decision-grade insights into `runtime/insights.json`.
- `compiler_reviewer`: render and check the final pack.

## Result Contract

Specialists return one JSON object:

```json
{
  "role": "research",
  "specialist": "research",
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
  "blocked_reason": "Need two more independent sources before ready state.",
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
- Only the compiler writes `final/`.
- Subagents should return summaries and source rows, not raw browsing transcripts.
- Raw orchestration contracts stay in `runtime/` or `exports/`; `final/` may show only readable summaries.
- Sensitive external writes require user approval.

## Synthesis Contract

Before rendering, the synthesis role must ensure:

- each segment, screen, and experiment has `support`;
- `support` points to an evidence ref or explicit assumption;
- blocked or weak evidence is visible to the user;
- the first action is concrete enough for a marketer to execute.
