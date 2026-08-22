"""Acquire public post-period articles from the Meituan technical blog."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

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
    quality_metrics,
    translation_evidence,
    write_jsonl,
)


PROTOCOL_VERSION = "post-acquisition-staging-1.0"
HISTORY_URL = "https://tech.meituan.com/history.html"
FEED_URL = "https://tech.meituan.com/feed.json"
DATED_PATH_RE = re.compile(r"^/(\d{4})/(\d{2})/(\d{2})/[^/]+\.html$")


def parse_path_date(path: str) -> dt.date | None:
    """Parse the publication date encoded by an official article path."""

    match = DATED_PATH_RE.fullmatch(path)
    if not match:
        return None
    try:
        return dt.date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def article_record(
    html: str, url: str, collected_at: str, history_evidence: dict[str, object]
) -> dict[str, object] | None:
    """Extract one complete article from the public VuePress page."""

    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one("h1.vp-post-title")
    content = soup.select_one(".vp-page-content")
    if title_node is None or content is None:
        return None
    body_node = next(
        (
            child
            for child in content.find_all(recursive=False)
            if child.name == "div" and "vp-post-header" not in (child.get("class") or [])
        ),
        None,
    )
    if body_node is None:
        return None
    path = url.split("tech.meituan.com", 1)[-1]
    published = parse_path_date(path)
    if published is None:
        return None
    text = normalize_text(body_node)
    meta = soup.select_one(".vp-post-meta")
    meta_parts = [
        value.strip()
        for value in (meta.stripped_strings if meta is not None else [])
        if value.strip()
    ]
    authors = meta_parts[:1]
    evidence = translation_evidence(text)
    canonical = canonical_url(url)
    record: dict[str, object] = {
        "doc_id": hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24],
        "source": "meituan_tech",
        "period": "post",
        "url": canonical,
        "title": title_node.get_text(" ", strip=True),
        "authors": authors,
        "translators": [],
        "article_type": "official_technical_blog",
        "is_translation": is_translation_from_evidence(evidence),
        "translation_evidence": evidence,
        "published_at": published.isoformat(),
        "modified_at": None,
        "collected_at": collected_at,
        "crawl_at": None,
        "date_confidence": "official_dated_url_and_page_metadata",
        "text": text,
        "views": None,
        "comments": None,
        "likes": None,
        "collects": None,
        "visibility_evidence": "official_history_and_json_feed_snapshot",
        "visibility_snapshot": history_evidence,
        "acquisition_method": "official_public_history_and_live_page",
        "corpus_stage": "acquisition_staging",
        "admission_status": "unreviewed",
    }
    record.update(quality_metrics(text))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire public Meituan technical-blog post candidates."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--http-timeout", type=float, default=45.0)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    client = HttpClient(delay=args.delay, timeout=args.http_timeout)
    history_response = client.get(HISTORY_URL)
    feed_response = client.get(FEED_URL)
    history_hash = hashlib.sha256(history_response.content).hexdigest()
    feed_hash = hashlib.sha256(feed_response.content).hexdigest()
    soup = BeautifulSoup(history_response.text, "html.parser")
    paths = sorted(
        {
            str(node.get("href"))
            for node in soup.select("a[href]")
            if parse_path_date(str(node.get("href"))) is not None
            and parse_path_date(str(node.get("href"))) >= POST_START
        }
    )
    collected_at = dt.datetime.now(dt.timezone.utc).isoformat()
    visibility_evidence = {
        "basis": "official_history_and_json_feed_snapshot",
        "history_url": HISTORY_URL,
        "history_sha256": history_hash,
        "feed_url": FEED_URL,
        "feed_sha256": feed_hash,
        "observed_at": collected_at,
    }
    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for index, path in enumerate(paths, start=1):
        url = canonical_url("https://tech.meituan.com" + path)
        try:
            response = client.get(url)
            record = article_record(response.text, url, collected_at, visibility_evidence)
        except Exception as exc:
            failures.append({"url": url, "error": type(exc).__name__})
            continue
        if record is None or record["quality_pass"] is not True:
            failures.append({"url": url, "error": "extraction_or_quality_gate"})
            continue
        records.append(record)
        print(
            f"[meituan/post] {index}/{len(paths)} {record['published_at']} "
            f"{record['title']}",
            flush=True,
        )

    candidates_path = output_dir / "meituan_post_candidates.jsonl"
    write_jsonl(candidates_path, records)
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "acquisition_staging_not_admitted",
        "source": "meituan_tech",
        "post_start": POST_START.isoformat(),
        "configuration": {
            "delay_seconds": args.delay,
            "http_timeout_seconds": args.http_timeout,
            "history_url": HISTORY_URL,
            "feed_url": FEED_URL,
            "translation_model": None,
        },
        "input_sha256": {
            HISTORY_URL: history_hash,
            FEED_URL: feed_hash,
        },
        "discovered_urls": len(paths),
        "documents": len(records),
        "failures": failures,
        "candidates_file": str(candidates_path),
        "candidates_sha256": file_sha256(candidates_path),
        "limitations": [
            "This output is acquisition staging and cannot be used for reader tasks.",
            "The official history and feed establish source-level editorial distribution, not article view counts.",
            "Model provenance, research value, format, topic, and duplicate review remain required.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
