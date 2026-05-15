# Orchestration

Use this when splitting work across specialists or recording specialist outputs.

## Roles

- `intake`: normalize user context and missing fields.
- `planner`: create topics and bounded tasks.
- `research`: gather current sources and practice patterns.
- `competitor`: gather competitor observations.
- `synthesis`: draft recommendations from normalized state.
- `compiler_reviewer`: render and check the final pack.

## Result Contract

Specialists return one JSON object:

```json
{
  "role": "research",
  "topic_id": "research_evidence",
  "task_id": "research-1",
  "summary": "Short synthesis",
  "key_findings": ["Finding"],
  "citations": [{"url": "https://example.com", "title": "Example"}],
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

## Boundaries

- Specialists write to runtime artifacts only through scripts or clear normalized notes.
- Only the compiler writes `final/`.
- Subagents should return summaries and source rows, not raw browsing transcripts.
- Sensitive external writes require user approval.
