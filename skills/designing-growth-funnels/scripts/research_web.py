#!/usr/bin/env python3
"""Collect current web source rows for a growth funnel workspace.

This is a read-only, best-effort collector. It intentionally uses only the
Python standard library and records source metadata instead of raw page dumps.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

from workspace_lib import (
    append_jsonl_unique,
    ensure_workspace,
    normalize_source,
    runtime_path,
    source_domain,
    validate_and_write,
)


SEARCH_URL = "https://duckduckgo.com/html/?q={query}"
USER_AGENT = "Mozilla/5.0 (compatible; GrowthFunnelResearch/1.0; +https://example.local)"

BLOCKED_DOMAINS = {
    "pinterest.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "x.com",
    "twitter.com",
}

REPUTABLE_QUALITATIVE_DOMAINS = {
    "g2.com",
    "capterra.com",
    "trustradius.com",
    "producthunt.com",
    "reddit.com",
}

LOW_QUALITY_HINTS = {
    "best tools",
    "top 10",
    "top 20",
    "ultimate guide",
    "alternatives",
    "comparison list",
    "ai tools",
}

QUERY_STOPWORDS = {
    "official",
    "pricing",
    "price",
    "prices",
    "plans",
    "docs",
    "documentation",
    "changelog",
    "reviews",
    "review",
    "competitor",
    "competitors",
    "onboarding",
    "trial",
    "demo",
    "examples",
    "best",
    "current",
    "practice",
    "practices",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect current web research source rows.")
    parser.add_argument("workspace_dir", help="Workspace directory to update.")
    parser.add_argument("--query", action="append", required=True, help="Search query. Repeat for multiple queries.")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum accepted sources per query.")
    parser.add_argument("--timeout", type=float, default=12.0, help="HTTP timeout in seconds.")
    parser.add_argument("--html-input", help="Parse a saved search HTML file instead of making a network request.")
    parser.add_argument("--allow-insecure-tls", action="store_true", help="Disable TLS certificate verification for local environments with broken CA chains.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary. Accepted for compatibility; JSON is always printed.")
    return parser.parse_args()


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def fetch_search_html(query: str, timeout: float, allow_insecure_tls: bool = False) -> str:
    url = SEARCH_URL.format(query=quote_plus(query))
    request = Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    with urlopen(request, timeout=timeout, context=context) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def clean_search_url(value: str) -> str:
    value = html.unescape(value or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    elif value.startswith("/"):
        value = "https://duckduckgo.com" + value
    parsed = urlparse(value)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target)
    return value


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_results(search_html: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    pattern = re.compile(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(search_html):
        url = clean_search_url(match.group("href"))
        title = strip_tags(match.group("title"))
        if not url or not title or url in seen:
            continue
        seen.add(url)
        results.append({"url": url, "title": title, "snippet": ""})

    snippet_matches = re.findall(
        r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>|<div[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>',
        search_html,
        re.IGNORECASE | re.DOTALL,
    )
    clean_snippets = []
    for item in snippet_matches:
        if isinstance(item, tuple):
            clean_snippets.append(strip_tags(next((part for part in item if part), "")))
        else:
            clean_snippets.append(strip_tags(item))
    for index, snippet in enumerate(clean_snippets):
        if index < len(results):
            results[index]["snippet"] = strip_tags(snippet)
    return results


def source_type_for(url: str, title: str, snippet: str) -> str:
    domain = source_domain(url)
    if domain in REPUTABLE_QUALITATIVE_DOMAINS or any(domain.endswith("." + item) for item in REPUTABLE_QUALITATIVE_DOMAINS):
        return "review"
    text = f"{url} {title} {snippet}".lower()
    if any(token in text for token in ["review", "reviews", "ratings", "capterra", "trustradius", "reddit"]):
        return "review"
    if any(token in text for token in ["pricing", "price", "plans", "тариф", "цена"]):
        return "pricing"
    if any(token in text for token in ["changelog", "release notes", "updates"]):
        return "changelog"
    if any(token in text for token in ["docs", "documentation", "api reference", "guide"]):
        return "docs"
    if any(token in text for token in ["case study", "customer story", "testimonial"]):
        return "case_study"
    if any(token in text for token in ["competitor", "alternative", "vs "]):
        return "competitor"
    return "current_practice"


def publisher_type_for(domain: str, source_type: str) -> str:
    if domain in REPUTABLE_QUALITATIVE_DOMAINS or any(domain.endswith("." + item) for item in REPUTABLE_QUALITATIVE_DOMAINS):
        return "review_or_community"
    if source_type in {"pricing", "docs", "changelog", "case_study"}:
        return "primary_or_official"
    return "publisher"


def query_entity_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9][a-z0-9-]{2,}", query.lower())
    return [token for token in tokens if token not in QUERY_STOPWORDS]


def looks_primary_for_query(domain: str, query: str) -> bool:
    compact_domain = domain.replace("-", "").replace(".", "")
    for token in query_entity_tokens(query):
        compact_token = token.replace("-", "")
        if compact_token and compact_token in compact_domain:
            return True
    return False


def evidence_weight_for(url: str, title: str, snippet: str, source_type: str, query: str) -> tuple[str, str]:
    domain = source_domain(url)
    text = f"{title} {snippet}".lower()
    if any(domain == blocked or domain.endswith("." + blocked) for blocked in BLOCKED_DOMAINS):
        return "low", "social media result is not accepted as decision proof"
    if any(hint in text for hint in LOW_QUALITY_HINTS) and source_type not in {"pricing", "docs", "changelog"}:
        return "low", "generic SEO/listicle pattern"
    if source_type in {"pricing", "docs", "changelog", "case_study"}:
        if looks_primary_for_query(domain, query):
            return "high", "primary/current-sensitive source on matching domain"
        return "medium", "secondary current-sensitive source; verify against primary source before final claims"
    if domain in REPUTABLE_QUALITATIVE_DOMAINS or any(domain.endswith("." + item) for item in REPUTABLE_QUALITATIVE_DOMAINS):
        return "medium", "qualitative review/community source"
    return "medium", "usable publisher source with retrievable URL"


def accepted(weight: str) -> bool:
    return weight in {"high", "medium"}


def build_source_rows(query: str, results: list[dict[str, str]], max_results: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    retrieved_at = today()
    for index, result in enumerate(results, start=1):
        url = result["url"]
        title = result["title"]
        snippet = result.get("snippet", "")
        source_type = source_type_for(url, title, snippet)
        weight, reason = evidence_weight_for(url, title, snippet, source_type, query)
        domain = source_domain(url)
        if not accepted(weight):
            rejected.append({"url": url, "title": title, "reason": reason})
            continue
        confidence = "high" if weight == "high" else "medium"
        row = normalize_source(
            {
                "source_id": "web-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:10],
                "url": url,
                "title": title,
                "publisher": domain,
                "retrieved_at": retrieved_at,
                "source_type": source_type,
                "freshness": "current",
                "confidence": confidence,
                "used_in": ["research_evidence"],
                "notes": f"query: {query}; snippet: {snippet}"[:500],
            },
            index=index,
            default_type="current_practice",
        )
        row["evidence_weight"] = weight
        row["publisher_type"] = publisher_type_for(domain, source_type)
        row["research_query"] = query
        rows.append(row)
        if len(rows) >= max_results:
            break
    return rows, rejected


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace_dir).expanduser().resolve()
    ensure_workspace(workspace)

    all_rows: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    errors: list[str] = []

    for index, query in enumerate(args.query):
        try:
            if args.html_input:
                if index > 0:
                    break
                search_html = Path(args.html_input).expanduser().read_text(encoding="utf-8")
            else:
                search_html = fetch_search_html(query, args.timeout, args.allow_insecure_tls)
            results = extract_results(search_html)
            rows, rejected_rows = build_source_rows(query, results, max(1, args.max_results))
            all_rows.extend(rows)
            rejected.extend(rejected_rows)
        except (OSError, HTTPError, URLError, TimeoutError) as exc:
            errors.append(f"{query}: {exc}")

    added = append_jsonl_unique(runtime_path(workspace, "sources.jsonl"), all_rows, ["url", "title"]) if all_rows else 0
    summary = validate_and_write(workspace)
    print(
        json.dumps(
            {
                "changed": {"source_rows_added": added},
                "accepted_count": len(all_rows),
                "rejected_count": len(rejected),
                "rejected": rejected[:20],
                "errors": errors,
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_rows or not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
