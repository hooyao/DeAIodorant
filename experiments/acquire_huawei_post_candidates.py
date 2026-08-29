"""Acquire recommended post-period engineering articles from Huawei Cloud."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
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


PROTOCOL_VERSION = "post-huawei-recommended-acquisition-staging-1.0"
BASE_URL = "https://bbs.huaweicloud.com"
LIST_URL = (
    BASE_URL + "/rest/cbc/ecocommunity/community/get-blogs-by-param"
)
ARTICLE_PATH_RE = re.compile(r"^/blogs/(\d+)$")
TOPIC_RE = re.compile(
    r"(?:数据库|GaussDB|openGauss|MySQL|PostgreSQL|Redis|SQL|数据仓库|数据湖|"
    r"大数据|云原生|Kubernetes|Docker|容器|DevOps|软件测试|单元测试|测试|"
    r"代码|编程|开发|架构|微服务|运维|存储|网络|云计算|API|Linux|Java|Python)",
    re.IGNORECASE,
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _numbers(node: object) -> list[int]:
    if not hasattr(node, "get_text"):
        return []
    return [int(value) for value in re.findall(r"\d+", node.get_text(" ", strip=True))]


def discover_recommended(
    client: HttpClient,
    *,
    pages: int,
    collected_at: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Discover topic-relevant entries from public recommendation pages."""

    entries: list[dict[str, object]] = []
    snapshots: list[dict[str, object]] = []
    seen: set[str] = set()
    for page_number in range(1, pages + 1):
        response = client.get(
            LIST_URL,
            params={
                "page_no": str(page_number),
                "page_size": "15",
                "user_id": "",
                "rec_num": "100",
                "isRecommend": "true",
                "tag_names": "",
                "home_query_type": "1",
                "is_limit": "0",
            },
        )
        snapshot = {
            "page": page_number,
            "url": response.url,
            "sha256": _sha256(response.content),
            "observed_at": collected_at,
        }
        page = BeautifulSoup(response.content, "html.parser")
        items = page.select(".blogs-item")
        snapshot["entries"] = len(items)
        relevant_count = 0
        for position, item in enumerate(items, start=1):
            title_node = item.select_one("a.blogs-title")
            date_node = item.select_one(".blogs-create-time")
            if title_node is None or date_node is None:
                continue
            href = str(title_node.get("href") or "")
            if ARTICLE_PATH_RE.fullmatch(href) is None:
                continue
            url = canonical_url(urljoin(BASE_URL, href))
            if url in seen:
                continue
            published = parse_date(date_node.get_text(" ", strip=True))
            if published is None or published < POST_START:
                continue
            title = title_node.get_text(" ", strip=True).removesuffix(" HOT").strip()
            description_node = item.select_one(".blogs-intro")
            description = (
                description_node.get_text(" ", strip=True)
                if description_node is not None
                else ""
            )
            tags = [
                node.get_text(" ", strip=True)
                for node in item.select(".blogs-tag a")
                if node.get_text(" ", strip=True)
            ]
            if TOPIC_RE.search(" ".join([title, description, *tags])) is None:
                continue
            author_node = item.select_one(".blogs-author-name")
            number_node = item.select_one(
                ".blogs-num-info:not(.blogs-publish-date)"
            )
            numbers = _numbers(number_node)
            entries.append(
                {
                    "url": url,
                    "list_published_at": published.isoformat(),
                    "list_title": title,
                    "list_description": description,
                    "list_tags": tags,
                    "list_author": (
                        author_node.get_text(" ", strip=True)
                        if author_node is not None
                        else ""
                    ),
                    "views": numbers[0] if len(numbers) >= 1 else None,
                    "comments": numbers[1] if len(numbers) >= 2 else None,
                    "likes": numbers[2] if len(numbers) >= 3 else None,
                    "recommendation_page": page_number,
                    "recommendation_position": position,
                    "recommendation_page_sha256": snapshot["sha256"],
                }
            )
            seen.add(url)
            relevant_count += 1
        snapshot["relevant_entries"] = relevant_count
        snapshots.append(snapshot)
    return entries, snapshots


def article_record(
    client: HttpClient,
    entry: dict[str, object],
    *,
    collected_at: str,
) -> dict[str, object] | None:
    """Extract one complete public article and retain visibility evidence."""

    response = client.get(str(entry["url"]))
    page = BeautifulSoup(response.content, "html.parser")
    title_node = page.select_one("h1.cloud-blog-detail-title")
    body_node = page.select_one("#blogContent")
    date_node = page.select_one(".article-write-time.isPc")
    author_node = page.select_one(".sub-content-username")
    if title_node is None or body_node is None or date_node is None:
        return None
    published = parse_date(date_node.get_text(" ", strip=True))
    if published is None or published < POST_START:
        return None
    text = normalize_text(body_node)
    evidence = translation_evidence(text)
    canonical = canonical_url(str(entry["url"]))
    record: dict[str, object] = {
        "doc_id": hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24],
        "source": "huawei_cloud_community",
        "period": "post",
        "url": canonical,
        "title": title_node.get_text(" ", strip=True),
        "authors": (
            [author_node.get_text(" ", strip=True)]
            if author_node is not None
            else []
        ),
        "translators": [],
        "article_type": "recommended_technical_community_article",
        "is_translation": is_translation_from_evidence(evidence),
        "translation_evidence": evidence,
        "published_at": published.isoformat(),
        "modified_at": None,
        "collected_at": collected_at,
        "crawl_at": None,
        "date_confidence": "visible_article_timestamp",
        "text": text,
        "views": entry["views"],
        "comments": entry["comments"],
        "likes": entry["likes"],
        "collects": None,
        "visibility_evidence": "public_recommendation_and_view_snapshot",
        "visibility_snapshot": {
            "basis": "public_recommendation_and_view_snapshot",
            "list_endpoint": LIST_URL,
            "recommendation_page": entry["recommendation_page"],
            "recommendation_position": entry["recommendation_position"],
            "recommendation_page_sha256": entry["recommendation_page_sha256"],
            "views": entry["views"],
            "comments": entry["comments"],
            "likes": entry["likes"],
            "tags": entry["list_tags"],
            "observed_at": collected_at,
        },
        "acquisition_method": "public_recommendation_archive_and_live_page",
        "corpus_stage": "acquisition_staging",
        "admission_status": "unreviewed",
    }
    record.update(quality_metrics(text))
    return record


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pages", type=int, default=30)
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--http-timeout", type=float, default=45.0)
    args = parser.parse_args()
    if args.pages < 1 or args.target < 1:
        raise SystemExit("Pages and target must be positive")
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    client = HttpClient(delay=args.delay, timeout=args.http_timeout)
    collected_at = dt.datetime.now(dt.timezone.utc).isoformat()
    discovered, snapshots = discover_recommended(
        client,
        pages=args.pages,
        collected_at=collected_at,
    )
    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for entry in discovered:
        if len(records) >= args.target:
            break
        try:
            record = article_record(client, entry, collected_at=collected_at)
        except Exception as exc:
            failures.append(
                {"url": str(entry["url"]), "error": type(exc).__name__}
            )
            continue
        if record is None or record["quality_pass"] is not True:
            failures.append(
                {"url": str(entry["url"]), "error": "shape_or_quality_gate"}
            )
            continue
        records.append(record)
        print(
            f"[huawei/post] {len(records)}/{args.target} "
            f"{record['published_at']} views={record['views']} {record['title']}",
            flush=True,
        )

    candidates_path = output_dir / "huawei_cloud_community_post_candidates.jsonl"
    write_jsonl(candidates_path, records)
    snapshots_path = output_dir / "recommendation_pages.jsonl"
    write_jsonl(snapshots_path, snapshots)
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generated_at": collected_at,
        "status": "acquisition_staging_not_admitted",
        "source": "huawei_cloud_community",
        "post_start": POST_START.isoformat(),
        "configuration": {
            "pages": args.pages,
            "target": args.target,
            "delay_seconds": args.delay,
            "http_timeout_seconds": args.http_timeout,
            "topic_filter": TOPIC_RE.pattern,
            "translation_model": None,
        },
        "discovered_relevant": len(discovered),
        "documents": len(records),
        "failures": failures,
        "candidates_file": str(candidates_path),
        "candidates_sha256": file_sha256(candidates_path),
        "recommendation_snapshots": str(snapshots_path),
        "recommendation_snapshots_sha256": file_sha256(snapshots_path),
        "limitations": [
            "This output is acquisition staging and cannot be used for reader tasks.",
            "Recommendation membership and view counts are collection-time snapshots, not fixed-age visibility measures.",
            "Community articles may be promotional, duplicated, translated, or low value; fail-closed review remains required.",
            "The topic filter is an acquisition aid and does not assign the final topic stratum.",
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if len(records) >= args.target else 1


if __name__ == "__main__":
    raise SystemExit(main())
