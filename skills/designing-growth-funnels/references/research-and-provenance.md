# Research and Provenance

Use this when collecting or normalizing external evidence.

## Source Contract

Each source row needs:

- `url`
- `title`
- `publisher` or domain
- `retrieved_at`
- `source_type`
- `freshness`
- `confidence`
- `used_in`
- `evidence_weight` when collected through live research
- `publisher_type` when collected through live research
- `research_query` when collected through live research

For pricing, changelog, and current-practice facts, missing `retrieved_at` is a gap. Do not treat those facts as current without a date.

## Source Types

- `pricing`
- `competitor`
- `review`
- `case_study`
- `docs`
- `current_practice`
- `benchmark`
- `changelog`
- `analytics`
- `customer_note`
- `other`

## Freshness

- `current`: retrieved recently enough for the claim.
- `dated`: useful but not current-sensitive.
- `stale`: likely outdated for pricing, market, or platform behavior.
- `unknown`: missing date or unclear provenance.

## Evidence Rules

- Prefer primary sources for pricing, docs, changelogs, and competitor claims.
- Use review sites and social proof as qualitative evidence, not verified performance proof.
- Use high/medium-weight sources for recommendations; low-weight sources are not support.
- Keep source summaries short and tied to where they are used.
- If evidence conflicts, record the conflict in `runtime/gaps.json`.
- Do not invent missing proof, customer claims, or private metrics. Default cold-start benchmarks are allowed only as `benchmark_assumption`, not evidence.
- Treat proof mechanics as format guidance only. A recommended proof format is not evidence unless a source, artifact, or explicit assumption backs the claim.
- Human reviewer approval can clear governance review for high-risk source-backed claims, but it does not create evidence and must not unblock weak, stale, missing, or low-weight proof for launch handoff.

## Live Collection

When network access exists, `scripts/research_web.py` can collect read-only search results and write normalized source rows:

```bash
python3 scripts/research_web.py "<workspace-dir>" --query "<focused query>" --json
python3 scripts/research_competitors.py "<workspace-dir>" --seed "<competitor name or domain>" --max-competitors 3 --json
```

The collectors are best-effort and should be treated as source discovery steps. `research_competitors.py` can populate `runtime/competitors.csv`, but final claims should still be verified against primary pages or host browser/search/MCP tools before synthesis.
