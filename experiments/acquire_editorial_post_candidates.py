"""Acquire public post-period candidates from Chinese editorial tech outlets."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from bs4 import BeautifulSoup

from deaiodorant.corpus.benchmark import file_sha256
from pilot_collect import (
    POST_START,
    HttpClient,
    canonical_url,
    is_translation_from_evidence,
    normalize_text,
    parse_date,
    quality_metrics,
    translation_evidence,
    write_jsonl,
)


PROTOCOL_VERSION = "post-editorial-acquisition-staging-1.0"
QBITAI_API = "https://www.qbitai.com/wp-json/wp/v2/posts"
QBITAI_FEED = "https://www.qbitai.com/feed"
LEIPHONE_BASE = "https://www.leiphone.com"
LEIPHONE_SITEMAP = "https://www.leiphone.com/sitemap.xml"
LEIPHONE_CATEGORIES = (
    "ai",
    "yanxishe",
    "academic",
    "digitalindustry",
    "industrynews",
)
LEIPHONE_ARTICLE_RE = re.compile(
    r"^https://www\.leiphone\.com/category/[^/]+/[A-Za-z0-9_-]+\.html$"
)
QBITAI_BYLINE_RE = re.compile(
    r"^\s*(.+?)\s+(?:发自|来自)\s+.+?(?:\n|$)|^\s*(.+?)\s*\|\s*(?:量子位|公众号)",
    re.MULTILINE,
)
LEIPHONE_BYLINE_RE = re.compile(r"本文作者[：:]?\s*(.+?)\s*$")


def _response_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _strip_nodes(node: BeautifulSoup) -> None:
    for unwanted in node.select(
        "script, style, noscript, iframe, figure, .wp-block-image, "
        ".realted-article, .related-article, .aboutAur-main, .article-right, "
        ".yp-copyright, .statement"
    ):
        unwanted.decompose()


def _qbitai_author(body: BeautifulSoup) -> list[str]:
    heading = body.find(["h2", "h3"])
    if heading is None:
        return []
    byline = heading.get_text(" ", strip=True)
    match = QBITAI_BYLINE_RE.search(byline)
    if match is None:
        return []
    author = next((value for value in match.groups() if value), "").strip()
    return [author] if author else []


def qbitai_record(
    post: dict[str, object],
    *,
    collected_at: str,
    visibility_snapshot: dict[str, object],
) -> dict[str, object] | None:
    """Convert one public WordPress API record into acquisition staging."""

    date_value = str(post.get("date") or "")
    try:
        published = dt.datetime.fromisoformat(date_value).date()
    except ValueError:
        return None
    if published < POST_START:
        return None
    link = canonical_url(str(post.get("link") or ""))
    title_value = post.get("title")
    content_value = post.get("content")
    if (
        not link
        or not isinstance(title_value, dict)
        or not isinstance(content_value, dict)
    ):
        return None
    rendered = content_value.get("rendered")
    if not isinstance(rendered, str):
        return None
    body = BeautifulSoup(rendered, "html.parser")
    authors = _qbitai_author(body)
    _strip_nodes(body)
    text = normalize_text(body)
    evidence = translation_evidence(text)
    record: dict[str, object] = {
        "doc_id": hashlib.sha256(link.encode("utf-8")).hexdigest()[:24],
        "source": "qbitai",
        "period": "post",
        "url": link,
        "title": html.unescape(
            BeautifulSoup(
                str(title_value.get("rendered") or ""), "html.parser"
            ).get_text(" ", strip=True)
        ),
        "authors": authors,
        "translators": [],
        "article_type": "editorial_article",
        "is_translation": is_translation_from_evidence(evidence),
        "translation_evidence": evidence,
        "published_at": published.isoformat(),
        "modified_at": str(post.get("modified") or "") or None,
        "collected_at": collected_at,
        "crawl_at": None,
        "date_confidence": "wordpress_public_api",
        "text": text,
        "views": None,
        "comments": None,
        "likes": None,
        "collects": None,
        "visibility_evidence": "official_public_feed_and_api_snapshot",
        "visibility_snapshot": visibility_snapshot,
        "acquisition_method": "public_wordpress_api",
        "corpus_stage": "acquisition_staging",
        "admission_status": "unreviewed",
    }
    record.update(quality_metrics(text))
    return record


def acquire_qbitai(
    client: HttpClient,
    *,
    target: int,
    collected_at: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Acquire recent QbitAI posts through its public WordPress API."""

    feed_response = client.get(QBITAI_FEED)
    page = 1
    records: list[dict[str, object]] = []
    page_snapshots: list[dict[str, object]] = []
    seen_urls: set[str] = set()
    while len(records) < target:
        response = client.get(
            QBITAI_API,
            params={
                "after": f"{POST_START.isoformat()}T00:00:00",
                "before": f"{(dt.date.today() + dt.timedelta(days=1)).isoformat()}T00:00:00",
                "per_page": "100",
                "page": str(page),
                "orderby": "date",
                "order": "desc",
                "_fields": "id,date,modified,link,title,content",
            },
        )
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            break
        page_snapshots.append(
            {
                "page": page,
                "url": response.url,
                "sha256": _response_sha256(response.content),
                "documents": len(payload),
            }
        )
        visibility_snapshot = {
            "basis": "official_public_feed_and_api_snapshot",
            "feed_url": QBITAI_FEED,
            "feed_sha256": _response_sha256(feed_response.content),
            "api_page": page,
            "api_page_sha256": page_snapshots[-1]["sha256"],
            "observed_at": collected_at,
        }
        for post in payload:
            if not isinstance(post, dict):
                continue
            record = qbitai_record(
                post,
                collected_at=collected_at,
                visibility_snapshot=visibility_snapshot,
            )
            if record is None or str(record["url"]) in seen_urls:
                continue
            seen_urls.add(str(record["url"]))
            if record["quality_pass"] is True:
                records.append(record)
            if len(records) >= target:
                break
        total_pages = int(response.headers.get("X-WP-TotalPages", "1"))
        if page >= total_pages:
            break
        page += 1
    stats = {
        "source": "qbitai",
        "target": target,
        "documents": len(records),
        "feed": {
            "url": QBITAI_FEED,
            "sha256": _response_sha256(feed_response.content),
        },
        "api_pages": page_snapshots,
        "deterministic_translation_flags": dict(
            sorted(Counter(str(item["is_translation"]) for item in records).items())
        ),
    }
    return records, stats


def _leiphone_links(page: BeautifulSoup) -> list[str]:
    links: list[str] = []
    for node in page.select("a[href]"):
        url = canonical_url(urljoin(LEIPHONE_BASE, str(node.get("href"))))
        if LEIPHONE_ARTICLE_RE.fullmatch(url):
            links.append(url)
    return list(dict.fromkeys(links))


def leiphone_record(
    html_text: str,
    url: str,
    *,
    collected_at: str,
    category_snapshot: dict[str, object],
    sitemap_sha256: str,
) -> dict[str, object] | None:
    """Extract one public Leiphone article page."""

    soup = BeautifulSoup(html_text, "html.parser")
    title_node = soup.select_one("h1.headTit")
    date_node = soup.select_one(".article-title .time") or soup.select_one(".time")
    body_node = soup.select_one(".lph-article-comView")
    if title_node is None or date_node is None or body_node is None:
        return None
    published = parse_date(date_node.get_text(" ", strip=True))
    if published is None or published < POST_START:
        return None
    author_node = soup.select_one(".article-title .aut") or soup.select_one(".aut")
    authors: list[str] = []
    if author_node is not None:
        author_text = author_node.get_text(" ", strip=True)
        author_text = LEIPHONE_BYLINE_RE.sub(r"\1", author_text).strip()
        if author_text:
            authors.append(author_text)
    _strip_nodes(body_node)
    text = normalize_text(body_node)
    evidence = translation_evidence(text)
    canonical = canonical_url(url)
    record: dict[str, object] = {
        "doc_id": hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24],
        "source": "leiphone",
        "period": "post",
        "url": canonical,
        "title": title_node.get_text(" ", strip=True),
        "authors": authors,
        "translators": [],
        "article_type": "editorial_article",
        "is_translation": is_translation_from_evidence(evidence),
        "translation_evidence": evidence,
        "published_at": published.isoformat(),
        "modified_at": None,
        "collected_at": collected_at,
        "crawl_at": None,
        "date_confidence": "visible_article_timestamp",
        "text": text,
        "views": None,
        "comments": None,
        "likes": None,
        "collects": None,
        "visibility_evidence": "official_category_and_sitemap_snapshot",
        "visibility_snapshot": {
            "basis": "official_category_and_sitemap_snapshot",
            "category": category_snapshot,
            "sitemap_url": LEIPHONE_SITEMAP,
            "sitemap_sha256": sitemap_sha256,
            "observed_at": collected_at,
        },
        "acquisition_method": "public_category_archive_and_live_page",
        "corpus_stage": "acquisition_staging",
        "admission_status": "unreviewed",
    }
    record.update(quality_metrics(text))
    return record


def acquire_leiphone(
    client: HttpClient,
    *,
    target: int,
    max_pages_per_category: int,
    collected_at: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Acquire recent articles from multiple public editorial categories."""

    sitemap_response = client.get(LEIPHONE_SITEMAP)
    sitemap_sha256 = _response_sha256(sitemap_response.content)
    category_queues: dict[str, list[tuple[str, dict[str, object]]]] = {}
    category_pages: list[dict[str, object]] = []
    for category in LEIPHONE_CATEGORIES:
        queue: list[tuple[str, dict[str, object]]] = []
        seen_category_urls: set[str] = set()
        for page_number in range(1, max_pages_per_category + 1):
            page_url = (
                f"{LEIPHONE_BASE}/category/{category}"
                if page_number == 1
                else f"{LEIPHONE_BASE}/category/{category}/page/{page_number}"
            )
            response = client.get(page_url)
            snapshot = {
                "category": category,
                "page": page_number,
                "url": response.url,
                "sha256": _response_sha256(response.content),
            }
            page_soup = BeautifulSoup(response.content, "html.parser")
            links = _leiphone_links(page_soup)
            snapshot["discovered_article_links"] = len(links)
            category_pages.append(snapshot)
            new_links = [url for url in links if url not in seen_category_urls]
            for url in new_links:
                seen_category_urls.add(url)
                queue.append((url, snapshot))
            if not new_links:
                break
        category_queues[category] = queue

    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    cursor = {category: 0 for category in LEIPHONE_CATEGORIES}
    while len(records) < target:
        progressed = False
        for category in LEIPHONE_CATEGORIES:
            queue = category_queues[category]
            while cursor[category] < len(queue):
                url, snapshot = queue[cursor[category]]
                cursor[category] += 1
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                progressed = True
                try:
                    response = client.get(url)
                    response.encoding = response.apparent_encoding
                    record = leiphone_record(
                        response.text,
                        url,
                        collected_at=collected_at,
                        category_snapshot=snapshot,
                        sitemap_sha256=sitemap_sha256,
                    )
                except Exception as exc:
                    failures.append({"url": url, "error": type(exc).__name__})
                    break
                if record is None:
                    failures.append({"url": url, "error": "shape_or_period"})
                    break
                if record["quality_pass"] is not True:
                    failures.append({"url": url, "error": "deterministic_quality_gate"})
                    break
                records.append(record)
                print(
                    f"[leiphone/post] {len(records)}/{target} "
                    f"{record['published_at']} {record['title']}",
                    flush=True,
                )
                break
            if len(records) >= target:
                break
        if not progressed:
            break
    stats = {
        "source": "leiphone",
        "target": target,
        "documents": len(records),
        "categories": list(LEIPHONE_CATEGORIES),
        "max_pages_per_category": max_pages_per_category,
        "category_pages": category_pages,
        "sitemap": {"url": LEIPHONE_SITEMAP, "sha256": sitemap_sha256},
        "failures": failures,
        "deterministic_translation_flags": dict(
            sorted(Counter(str(item["is_translation"]) for item in records).items())
        ),
    }
    return records, stats


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Acquire public post-period editorial candidates."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--qbitai-target", type=int, default=100)
    parser.add_argument("--leiphone-target", type=int, default=100)
    parser.add_argument("--leiphone-pages", type=int, default=10)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--http-timeout", type=float, default=45.0)
    args = parser.parse_args()
    if min(args.qbitai_target, args.leiphone_target, args.leiphone_pages) < 1:
        raise SystemExit("Targets and page limits must be positive")
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    client = HttpClient(delay=args.delay, timeout=args.http_timeout)
    collected_at = dt.datetime.now(dt.timezone.utc).isoformat()
    qbitai, qbitai_stats = acquire_qbitai(
        client,
        target=args.qbitai_target,
        collected_at=collected_at,
    )
    leiphone, leiphone_stats = acquire_leiphone(
        client,
        target=args.leiphone_target,
        max_pages_per_category=args.leiphone_pages,
        collected_at=collected_at,
    )
    outputs: list[dict[str, object]] = []
    for source, records in (("qbitai", qbitai), ("leiphone", leiphone)):
        path = output_dir / f"{source}_post_candidates.jsonl"
        write_jsonl(path, records)
        outputs.append(
            {
                "source": source,
                "path": str(path),
                "documents": len(records),
                "sha256": file_sha256(path),
            }
        )
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generated_at": collected_at,
        "status": "acquisition_staging_not_admitted",
        "post_start": POST_START.isoformat(),
        "configuration": {
            "qbitai_target": args.qbitai_target,
            "leiphone_target": args.leiphone_target,
            "leiphone_pages": args.leiphone_pages,
            "delay_seconds": args.delay,
            "http_timeout_seconds": args.http_timeout,
            "translation_model": None,
        },
        "documents": len(qbitai) + len(leiphone),
        "source_counts": {"qbitai": len(qbitai), "leiphone": len(leiphone)},
        "outputs": outputs,
        "source_stats": {"qbitai": qbitai_stats, "leiphone": leiphone_stats},
        "limitations": [
            "This output is acquisition staging and cannot be used for reader tasks.",
            "Official feeds, APIs, categories, and sitemaps establish editorial distribution, not article-level readership.",
            "Model provenance, research value, visibility admission, strata classification, and cross-corpus deduplication remain required.",
            "Editorial outlets may contain translated, compiled, promoted, or low-value articles; uncertainty must fail closed during admission.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if len(qbitai) >= args.qbitai_target and len(leiphone) >= args.leiphone_target else 1


if __name__ == "__main__":
    raise SystemExit(main())
