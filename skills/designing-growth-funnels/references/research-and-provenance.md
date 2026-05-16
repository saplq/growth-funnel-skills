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
- Keep source summaries short and tied to where they are used.
- If evidence conflicts, record the conflict in `runtime/gaps.json`.
- Do not invent missing proof, customer claims, benchmarks, or private metrics.
