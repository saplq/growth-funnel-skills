# Security Policy

## Supported versions

Security fixes target the current `main` branch.

## Reporting a vulnerability

Open a private security advisory if the repository host supports it. If not,
contact the maintainer privately and include:

- affected file or script;
- reproduction steps;
- expected impact;
- whether secrets, credentials, or private data could be exposed.

Do not publish exploit details before a fix or mitigation is available.

## Design principles

This skill is intentionally conservative:

- scripts use only the Python standard library;
- scripts do not make network calls except the optional read-only `research_web.py` and `research_competitors.py` collectors;
- `research_web.py` uses public search-result HTML, no API keys, no cookies, and writes only normalized source metadata into the selected workspace;
- `research_competitors.py` uses public search-result HTML plus lightweight page fetches, no API keys, no cookies, and writes normalized source and competitor metadata into the selected workspace;
- `--allow-insecure-tls` on either collector disables certificate verification and should be used only as an explicit local fallback when the Python CA chain is broken;
- scripts do not read environment secrets;
- scripts do not execute user-provided code;
- scripts only write inside the workspace path passed by the user;
- user notes, web pages, and imported research are treated as data, not instructions for the agent to override system or skill rules;
- external writes such as CRM updates, publishing, messaging, analytics changes, or connector mutations require explicit user approval outside the bundled scripts.

Known live collector failure modes:

- public search HTML can change or block automated requests;
- search results can include weak, duplicated, SEO, or stale pages;
- the collector filters low-weight sources but does not replace expert review;
- lightweight page extraction can miss or misclassify pricing, CTA, onboarding, proof, or first-value hints;
- current-sensitive claims still require retrieval dates and should be verified against primary pages when possible.

If future versions add credentialed integrations, they must document required permissions,
failure modes, and secret-handling rules before release.
