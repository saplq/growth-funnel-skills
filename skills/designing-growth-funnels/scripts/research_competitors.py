#!/usr/bin/env python3
"""Collect competitor rows for a growth funnel workspace.

This is a read-only, best-effort competitor discovery collector. It uses
search-result pages plus lightweight page fetching, then writes normalized
source rows and competitor CSV rows into the workspace runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from research_web import (
    BLOCKED_DOMAINS,
    LOW_QUALITY_HINTS,
    REPUTABLE_QUALITATIVE_DOMAINS,
    USER_AGENT,
    clean_search_url,
    extract_results,
    fetch_search_html,
    source_type_for,
    strip_tags,
    today,
)
from workspace_lib import (
    COMPETITOR_HEADERS,
    append_csv_unique,
    append_jsonl_unique,
    ensure_workspace,
    load_workspace,
    normalize_competitor,
    normalize_source,
    present,
    runtime_path,
    source_domain,
    validate_and_write,
)


NON_COMPETITOR_DOMAINS = {
    "duckduckgo.com",
    "google.com",
    "bing.com",
    "forbes.com",
    "prnewswire.com",
    "businesswire.com",
    "globenewswire.com",
    "medium.com",
    "substack.com",
    "wikipedia.org",
}

PAGE_FETCH_BYTES = 600_000

CTA_PATTERNS = [
    "Start free",
    "Start trial",
    "Start your free trial",
    "Try for free",
    "Get started",
    "Book demo",
    "Book a demo",
    "Request demo",
    "Request a demo",
    "View demo",
    "Contact sales",
    "Sign up",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect competitor source and CSV rows.")
    parser.add_argument("workspace_dir", help="Workspace directory to update.")
    parser.add_argument("--seed", action="append", default=[], help="Known competitor name or domain. Repeat for multiple seeds.")
    parser.add_argument("--query", action="append", default=[], help="Additional competitor discovery query. Repeat for multiple queries.")
    parser.add_argument("--max-competitors", type=int, default=3, help="Maximum accepted competitors to write.")
    parser.add_argument("--max-results", type=int, default=8, help="Maximum search results to inspect per query.")
    parser.add_argument("--timeout", type=float, default=12.0, help="HTTP timeout in seconds.")
    parser.add_argument("--html-input", help="Parse a saved search HTML file instead of making a network request.")
    parser.add_argument("--page-fixture-dir", help="Directory containing page HTML fixtures named by domain, for tests.")
    parser.add_argument("--allow-insecure-tls", action="store_true", help="Disable TLS certificate verification for local environments with broken CA chains.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def compact(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit].strip()


def seed_label(seed: str) -> str:
    text = seed.strip()
    if not text:
        return ""
    if "." in text and " " not in text:
        text = source_domain("https://" + text if not text.startswith("http") else text)
        text = text.split(".")[0]
    text = re.sub(r"[-_]+", " ", text)
    return " ".join(part.capitalize() for part in text.split())


def query_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9-]{2,}", value.lower())


def seed_matches_domain(seed: str, domain: str) -> bool:
    clean_domain = domain.replace("-", "").replace(".", "").lower()
    for token in query_tokens(seed):
        if token in {"www", "com", "net", "org", "io", "app", "pricing", "official"}:
            continue
        if token.replace("-", "") in clean_domain:
            return True
    return False


def build_queries(intake: dict[str, Any], seeds: list[str], explicit_queries: list[str]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for seed in seeds:
        seed = compact(seed, 80)
        if not seed:
            continue
        items.append({"query": f"{seed} pricing official", "seed": seed})
        items.append({"query": f"{seed} onboarding trial demo official", "seed": seed})
    for query in explicit_queries:
        query = compact(query, 160)
        if query:
            items.append({"query": query, "seed": ""})

    offer = compact(intake.get("offer"), 100)
    audience = compact(intake.get("icp") or intake.get("primary_persona"), 80)
    sales_motion = compact(intake.get("sales_motion"), 50)
    if offer:
        base = " ".join(part for part in [offer, audience, sales_motion] if part)
        items.append({"query": compact(f"{base} competitors pricing official", 180), "seed": ""})
        items.append({"query": compact(f"{offer} alternatives official pricing", 160), "seed": ""})

    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for item in items:
        signature = item["query"].lower()
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(item)
    return deduped


def domain_stem(domain: str) -> str:
    parts = domain.split(".")
    if len(parts) >= 2 and parts[0] in {"www", "app", "go"}:
        parts = parts[1:]
    stem = parts[0] if parts else domain
    return " ".join(part.capitalize() for part in re.split(r"[-_]+", stem) if part)


def has_domain_suffix(domain: str, candidates: set[str]) -> bool:
    return any(domain == item or domain.endswith("." + item) for item in candidates)


def generic_result(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in LOW_QUALITY_HINTS) or any(
        token in lowered for token in ["alternatives to", "best alternatives", "software list", "comparison"]
    )


def candidate_rejection(result: dict[str, str], seed: str) -> str:
    url = result.get("url", "")
    domain = source_domain(url)
    text = f"{result.get('title', '')} {result.get('snippet', '')}"
    if not domain:
        return "missing domain"
    if has_domain_suffix(domain, BLOCKED_DOMAINS):
        return "blocked social/media domain"
    if has_domain_suffix(domain, REPUTABLE_QUALITATIVE_DOMAINS):
        return "review/community domain is not a competitor page"
    if has_domain_suffix(domain, NON_COMPETITOR_DOMAINS):
        return "publisher/search domain is not a competitor page"
    if generic_result(text):
        return "generic listicle/comparison result"
    if source_type_for(url, result.get("title", ""), result.get("snippet", "")) == "review":
        return "review result is not a competitor page"
    if seed and not seed_matches_domain(seed, domain) and seed.lower() not in text.lower():
        return "seed result does not match domain or title"
    return ""


def page_fixture_path(page_fixture_dir: str | None, url: str) -> Path | None:
    if not page_fixture_dir:
        return None
    directory = Path(page_fixture_dir).expanduser()
    parsed = urlparse(url)
    domain = source_domain(url)
    path_key = re.sub(r"[^a-zA-Z0-9]+", "-", (domain + parsed.path).strip("/")).strip("-")
    candidates = [
        directory / f"{domain}.html",
        directory / f"{path_key}.html",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def fetch_page_html(url: str, timeout: float, allow_insecure_tls: bool = False) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    with urlopen(request, timeout=timeout, context=context) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read(PAGE_FETCH_BYTES).decode(charset, errors="replace")


def read_page(url: str, args: argparse.Namespace) -> tuple[str, str]:
    fixture = page_fixture_path(args.page_fixture_dir, url)
    if fixture:
        return fixture.read_text(encoding="utf-8"), ""
    try:
        return fetch_page_html(url, args.timeout, args.allow_insecure_tls), ""
    except (OSError, HTTPError, URLError, TimeoutError) as exc:
        return "", str(exc)


def meta_content(page_html: str, name: str) -> str:
    pattern = re.compile(
        rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    match = pattern.search(page_html)
    return html.unescape(match.group(1)).strip() if match else ""


def page_title(page_html: str, fallback: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", page_html, re.IGNORECASE | re.DOTALL)
    if match:
        return strip_tags(match.group(1))
    return fallback


def page_text(page_html: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", page_html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    return strip_tags(text)


def extract_pricing(text: str) -> str:
    price = re.search(r"([$€£]\s?\d[\d,.]*(?:\s?/(?:mo|month|yr|year))?)", text, re.IGNORECASE)
    if price:
        return compact(price.group(1), 60)
    lowered = text.lower()
    if any(token in lowered for token in ["pricing", "plans", "free trial", "paid plan", "custom pricing"]):
        return "pricing page observed"
    return ""


def extract_cta(text: str) -> str:
    lowered = text.lower()
    for cta in CTA_PATTERNS:
        if cta.lower() in lowered:
            return cta
    return ""


def extract_onboarding(text: str) -> str:
    lowered = text.lower()
    if "connect stripe" in lowered:
        return "connect Stripe or billing data"
    if "connect" in lowered and "billing" in lowered:
        return "connect billing data"
    if "connect" in lowered and "crm" in lowered:
        return "connect CRM"
    if "import" in lowered and "data" in lowered:
        return "import data"
    if "sample" in lowered and ("workspace" in lowered or "data" in lowered):
        return "sample workspace or sample data"
    if "book a demo" in lowered or "request a demo" in lowered or "contact sales" in lowered:
        return "sales-assisted demo"
    if "sign up" in lowered or "start free" in lowered or "free trial" in lowered:
        return "self-serve signup"
    return ""


def extract_proof(text: str) -> str:
    lowered = text.lower()
    if "case study" in lowered or "customer story" in lowered:
        return "case studies or customer stories observed"
    if "testimonial" in lowered or "trusted by" in lowered:
        return "testimonials or trust proof observed"
    if "reviews" in lowered or "rating" in lowered:
        return "reviews observed"
    return ""


def extract_first_value(text: str) -> str:
    lowered = text.lower()
    if "dashboard" in lowered:
        return "dashboard or analytics view"
    if "report" in lowered or "insight" in lowered:
        return "report or insight preview"
    if "diagnosis" in lowered or "diagnostic" in lowered or "score" in lowered:
        return "diagnosis or score"
    if "roadmap" in lowered or "recommendation" in lowered:
        return "roadmap or recommendations"
    return ""


def observed_count(row: dict[str, str]) -> int:
    fields = ["positioning", "pricing", "primary_cta", "onboarding_pattern", "proof", "first_value_path"]
    return sum(1 for field in fields if present(row.get(field)))


def build_competitor_row(
    result: dict[str, str],
    page_html: str,
    query: str,
    seed: str,
    fetch_error: str = "",
) -> tuple[dict[str, str], str]:
    url = result.get("url", "")
    domain = source_domain(url)
    title = page_title(page_html, result.get("title", ""))
    description = meta_content(page_html, "description") or meta_content(page_html, "og:description")
    text = page_text(page_html) if page_html else f"{title} {result.get('snippet', '')}"
    combined = compact(" ".join([title, description, text]), 5000)
    name = seed_label(seed) if seed else domain_stem(domain)
    row = normalize_competitor(
        {
            "competitor": name,
            "domain": domain,
            "positioning": compact(description or result.get("snippet"), 180),
            "pricing": extract_pricing(combined),
            "primary_cta": extract_cta(combined),
            "onboarding_pattern": extract_onboarding(combined),
            "proof": extract_proof(combined),
            "first_value_path": extract_first_value(combined),
            "source": url,
            "confidence": "high" if seed and seed_matches_domain(seed, domain) and observed_count({"positioning": description or title}) else "medium",
            "retrieved_at": today(),
            "notes": compact(f"query: {query}; title: {title}; fetch_error: {fetch_error}", 300),
        }
    )
    count = observed_count(row)
    if count == 0:
        return row, "no observed competitor fields found"
    if row["confidence"] == "high" and count < 2:
        row["confidence"] = "medium"
    return row, ""


def source_row_for_competitor(row: dict[str, str], query: str) -> dict[str, Any]:
    source = normalize_source(
        {
            "source_id": "competitor-" + hashlib.sha1(row["source"].encode("utf-8")).hexdigest()[:10],
            "url": row["source"],
            "title": row["competitor"],
            "publisher": row["domain"],
            "retrieved_at": row["retrieved_at"],
            "source_type": "competitor",
            "freshness": "current",
            "confidence": row["confidence"],
            "used_in": ["competitor_map"],
            "notes": row.get("notes", ""),
        },
        default_type="competitor",
    )
    source["evidence_weight"] = "high" if row["confidence"] == "high" else "medium"
    source["publisher_type"] = "primary_or_official"
    source["research_query"] = query
    return source


def collect_search_results(args: argparse.Namespace, queries: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    results: list[dict[str, str]] = []
    errors: list[str] = []
    for index, item in enumerate(queries):
        query = item["query"]
        try:
            if args.html_input:
                if index > 0:
                    break
                search_html = Path(args.html_input).expanduser().read_text(encoding="utf-8")
            else:
                search_html = fetch_search_html(query, args.timeout, args.allow_insecure_tls)
            for result in extract_results(search_html)[: max(1, args.max_results)]:
                result["query"] = query
                result["seed"] = item.get("seed", "")
                results.append(result)
        except (OSError, HTTPError, URLError, TimeoutError) as exc:
            errors.append(f"{query}: {exc}")
    return results, errors


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    try:
        ensure_workspace(workspace)
        data = load_workspace(workspace)
        queries = build_queries(data.get("intake", {}), args.seed, args.query)
        search_results, errors = collect_search_results(args, queries)

        seen_domains: set[str] = set()
        competitor_rows: list[dict[str, str]] = []
        source_rows: list[dict[str, Any]] = []
        rejected: list[dict[str, str]] = []

        for result in search_results:
            if len(competitor_rows) >= max(1, args.max_competitors):
                break
            url = clean_search_url(result.get("url", ""))
            result["url"] = url
            domain = source_domain(url)
            if domain in seen_domains:
                rejected.append({"url": url, "title": result.get("title", ""), "reason": "duplicate domain"})
                continue
            reason = candidate_rejection(result, result.get("seed", ""))
            if reason:
                rejected.append({"url": url, "title": result.get("title", ""), "reason": reason})
                continue
            page_html, fetch_error = read_page(url, args)
            row, row_reason = build_competitor_row(result, page_html, result.get("query", ""), result.get("seed", ""), fetch_error)
            if row_reason:
                rejected.append({"url": url, "title": result.get("title", ""), "reason": row_reason})
                continue
            seen_domains.add(domain)
            competitor_rows.append(row)
            source_rows.append(source_row_for_competitor(row, result.get("query", "")))

        source_rows_added = append_jsonl_unique(runtime_path(workspace, "sources.jsonl"), source_rows, ["url", "title"]) if source_rows else 0
        competitor_rows_added = append_csv_unique(
            runtime_path(workspace, "competitors.csv"),
            COMPETITOR_HEADERS,
            competitor_rows,
            ["competitor", "domain", "source"],
        ) if competitor_rows else 0
        summary = validate_and_write(workspace)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "changed": {
                    "source_rows_added": source_rows_added,
                    "competitor_rows_added": competitor_rows_added,
                },
                "accepted_competitors": competitor_rows,
                "rejected_candidates": rejected[:30],
                "errors": errors,
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if competitor_rows or not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
