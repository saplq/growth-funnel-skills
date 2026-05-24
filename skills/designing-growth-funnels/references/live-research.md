# Live Research Protocol

Use this when the funnel depends on current market, pricing, competitor, platform, or current-practice claims.

## Research Capability

Live research is allowed only through available host tools or the bundled `scripts/research_web.py` collector. If neither path is available, do not claim that current research was performed. Mark the missing research in `runtime/gaps.json`; recommendations may still be ready to test only when they are explicitly assumption-backed and launch blockers remain visible.

`research_web.py` is a read-only, best-effort search-result collector. It uses the Python standard library, public search-result HTML, and no API keys. Public search pages can change or block automated requests, so host browser/search/MCP tools remain the preferred route for high-stakes work.

`research_competitors.py` is the companion competitor collector. It uses search-result discovery plus lightweight page fetches, rejects weak candidate domains, extracts observed pricing/CTA/onboarding/proof/first-value hints, and writes structured rows to `runtime/competitors.csv`. It does not perform deep crawling and does not replace manual review of primary competitor pages.

## Required Search Plan

For each funnel package, collect evidence for these topics when relevant:

- official offer or product pages for direct competitors;
- pricing, plan limits, demo/trial paths, and onboarding pages;
- docs, changelogs, or platform pages for current-practice claims;
- review sites or community discussions only for qualitative objections and language;
- category reports or benchmark sources only when publisher quality is clear.

Minimum launch-ready evidence:

- at least 3 current external source rows;
- at least 3 competitor rows with source and retrieval date;
- no current-sensitive source missing `retrieved_at`;
- no unresolved contradictions;
- every segment, screen, and experiment points to an evidence ref or explicit assumption.
- every competitor row has source, retrieval date, and at least one observed field such as positioning, pricing, CTA, onboarding, proof, or first-value path.

User-provided competitor categories or archetypes without a URL are useful context, but they do not count toward the 3 competitor rows and must not drive competitor pattern synthesis.

Ready-to-test evidence can be weaker when the project is in cold start. In that case, use `assumption_ids`, `evidence_mode=assumption_backed`, and `launch_blocked_reason`; do not set launch rows `ready=true`.

## Source Weight

Classify sources by weight before using them in recommendations.

High weight:

- official company pricing, product, docs, changelog, trust, security, or case-study pages;
- original research from a known publisher with methodology;
- first-party analytics, CRM, customer interview notes, or internal metrics provided by the user.

Medium weight:

- reputable review sites or marketplace listings;
- direct competitor landing pages without pricing;
- well-sourced industry analysis with a clear publisher and date.

Low weight:

- undated SEO summaries, listicles, scraped comparison pages, content farms, AI-generated articles, copied directories, and pages without clear publisher;
- social/community posts when used as performance proof.

Do not use low-weight sources as proof for recommendations. They may be recorded only as weak assumptions or qualitative language signals.

## Freshness Rules

- Pricing, plan limits, competitor CTAs, docs, changelogs, and platform behavior require retrieval date.
- Market/category reports can be `dated` when the claim is not time-sensitive.
- If a source has no retrieval date and the claim can change, it is a gap.
- If two sources conflict, record the conflict and do not resolve it by guessing.

## Search Query Patterns

Use focused queries instead of broad generic searches:

- `<competitor> pricing official`
- `<competitor> onboarding trial demo official`
- `<category> <audience> activation onboarding examples`
- `<platform/tool> changelog pricing docs <current year>`
- `<category> reviews objections G2 Capterra Reddit`
- `<competitor A> vs <competitor B> pricing`

## Rejection Rules

Reject or downgrade sources when:

- the page has no clear publisher/domain;
- the page makes unverifiable performance claims;
- the claim is current-sensitive but has no retrieval date;
- the source is only summarizing other pages without original evidence;
- the source is a review/community page being used as quantitative proof;
- the source contradicts a primary source.

## Recording Results

Record source rows with:

- `url`
- `title`
- `publisher`
- `retrieved_at`
- `source_type`
- `freshness`
- `confidence`
- `used_in`
- `evidence_weight`
- `publisher_type`
- `research_query`
- `notes`

Use `record_agent_result.py` for specialist summaries and `ingest_notes.py` or `research_web.py` for source rows. Analytics, CRM, customer interview, and private file evidence must come from host tools or user-provided files; the bundled collectors do not connect to private systems. Keep raw browsing transcripts out of `final/`.

Use `research_competitors.py` when competitor rows are missing:

```bash
python3 scripts/research_competitors.py "<workspace-dir>" --seed "<competitor name or domain>" --max-competitors 3 --json
```
