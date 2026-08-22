from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup

from deaiodorant.corpus.benchmark import (
    BENCHMARK_PROTOCOL_VERSION,
    ExclusionIndex,
    REVIEW_FIELDS,
    assert_disjoint,
    balanced_take,
    content_hash,
    file_sha256,
    read_jsonl,
    read_review_decisions,
    stable_order,
    write_jsonl,
    write_review_queue,
)
from deaiodorant.corpus.label_studio_review import (
    VALUE_LABEL_CONFIG,
    bootstrap_label_studio_project,
    create_label_studio_subset_project,
    export_label_studio_decisions,
    export_label_studio_project_decisions,
    export_label_studio_value_decisions,
    prepare_label_studio_workspace,
)
from deaiodorant.corpus.review_triage import (
    ReviewTriageClassifier,
    run_review_triage,
)
from deaiodorant.corpus.value_triage import (
    ResearchValueClassifier,
    run_value_triage,
)
from pilot_collect import (
    HttpClient,
    common_crawl_records,
    extract_infoq,
    extract_jiqizhixin,
    infoq_sitemap_urls,
    quality_metrics,
    strong_original_evidence,
    translation_evidence,
    warc_html,
)


TRANSITION_START = dt.date(2023, 1, 1)
TRANSITION_END = dt.date(2025, 6, 30)
DEFAULT_EXCLUSIONS = [
    Path("data/translation_eval/gold.jsonl"),
    Path("data/translation_holdout/gold.jsonl"),
    Path("data/translation_test/gold.jsonl"),
    Path("data/pilot/pilot_corpus.jsonl"),
    Path("data/smoke/pilot_corpus.jsonl"),
]
LCTT_REPOSITORY = "LCTT/TranslateProject"
LCTT_LICENSE = "Apache-2.0"
LCTT_METADATA_RE = re.compile(
    r"^\[#\]:\s*([A-Za-z_]+):\s*[\(\"]?(.*?)[\)\"]?\s*$"
)
MARKDOWN_REFERENCE_RE = re.compile(r"^\[[^]]+\]:\s+\S+.*$", re.MULTILINE)
MARKDOWN_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^]]*\]\([^)]*\)|!\[[^]]*\]\[[^]]*\]")
MARKDOWN_LINK_RE = re.compile(r"\[([^]]+)\]\([^)]*\)|\[([^]]+)\]\[[^]]*\]")
ORIGINAL_CANDIDATE_RE = re.compile(
    r"(?:采访|受访|现场|发布会|技术沙龙|分享嘉宾|本期邀请|项目复盘|建设历程|"
    r"中国|阿里|腾讯|百度|华为|美团|工商银行|研究组|实验室|作者[｜|：:]|我们团队)"
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def in_transition_period(value: str) -> bool:
    try:
        published = dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return TRANSITION_START <= published <= TRANSITION_END


def candidate_record(
    record: dict[str, Any],
    *,
    candidate_label: str,
    label_evidence: list[str],
    label_status: str,
) -> dict[str, Any]:
    item = dict(record)
    item["candidate_label"] = candidate_label
    item["label_evidence"] = label_evidence
    item["label_status"] = label_status
    item["benchmark_protocol_version"] = BENCHMARK_PROTOCOL_VERSION
    item["content_hash"] = content_hash(item["text"])
    return item


def admit_candidate(
    record: dict[str, Any],
    *,
    exclusion: ExclusionIndex,
    output: list[dict[str, Any]],
    exclusions: Counter[str],
) -> bool:
    match = exclusion.match(record)
    if match is not None:
        exclusions[match.reason] += 1
        return False
    exclusion.add(record)
    output.append(record)
    return True


def collect_infoq(
    client: HttpClient,
    exclusion: ExclusionIndex,
    *,
    translation_target: int,
    original_target: int,
    max_attempts: int,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    records: list[dict[str, Any]] = []
    exclusions: Counter[str] = Counter()
    translations = 0
    originals = 0
    urls = infoq_sitemap_urls(client, [1, 2, 3, 4])
    ordered_urls = sorted(
        set(urls),
        key=lambda url: hashlib.sha256(
            f"translation-v2-infoq\0{url}".encode("utf-8")
        ).digest(),
    )
    for attempt, url in enumerate(ordered_urls, start=1):
        if attempt > max_attempts:
            break
        if translations >= translation_target and originals >= original_target:
            break
        try:
            response = client.get(url)
            record = extract_infoq(response.text, url, utc_now())
        except Exception:
            exclusions["fetch_or_extract_error"] += 1
            continue
        if not record or not record.get("quality_pass"):
            exclusions["shape_or_quality"] += 1
            continue
        if not in_transition_period(record["published_at"]):
            exclusions["outside_transition_period"] += 1
            continue
        candidate: dict[str, Any] | None = None
        if (
            translations < translation_target
            and "explicit_translator_field" in record.get("translation_evidence", [])
        ):
            candidate = candidate_record(
                record,
                candidate_label="translation",
                label_evidence=[
                    "explicit_translator_field",
                    *record.get("translators", []),
                ],
                label_status="deterministic",
            )
        elif (
            originals < original_target
            and record.get("authors")
            and not record.get("translation_evidence")
            and ORIGINAL_CANDIDATE_RE.search(record["text"])
        ):
            evidence = strong_original_evidence(record)
            candidate = candidate_record(
                record,
                candidate_label="original_pending_review",
                label_evidence=["original_candidate_signal", *evidence],
                label_status="manual_review_required",
            )
        if candidate is None:
            exclusions["insufficient_label_evidence"] += 1
            continue
        if admit_candidate(
            candidate, exclusion=exclusion, output=records, exclusions=exclusions
        ):
            if candidate["candidate_label"] == "translation":
                translations += 1
            else:
                originals += 1
            print(
                f"[infoq] translations={translations}/{translation_target} "
                f"originals={originals}/{original_target}",
                flush=True,
            )
    if translations < translation_target or originals < original_target:
        raise RuntimeError(
            f"Insufficient InfoQ candidates: translations={translations}, "
            f"originals={originals}"
        )
    return records, exclusions


def _crawl_at(record: dict[str, Any]) -> str:
    return dt.datetime.strptime(record["timestamp"], "%Y%m%d%H%M%S").replace(
        tzinfo=dt.timezone.utc
    ).isoformat()


def collect_jiqizhixin(
    client: HttpClient,
    exclusion: ExclusionIndex,
    *,
    translation_target: int,
    original_target: int,
    max_attempts: int,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    records: list[dict[str, Any]] = []
    exclusions: Counter[str] = Counter()
    translations = 0
    originals = 0
    queries = [
        ("CC-MAIN-2023-50", "www.jiqizhixin.com/articles/2023-*"),
        ("CC-MAIN-2024-26", "www.jiqizhixin.com/articles/2024-*"),
        ("CC-MAIN-2025-21", "www.jiqizhixin.com/articles/2025-*"),
        ("CC-MAIN-2022-49", "www.jiqizhixin.com/articles/2022-*"),
        ("CC-MAIN-2021-49", "www.jiqizhixin.com/articles/2021-*"),
    ]
    crawl_records: dict[str, dict[str, Any]] = {}
    for index, pattern in queries:
        for record in common_crawl_records(client, index, pattern):
            crawl_records.setdefault(record["url"], record)
    ordered = sorted(
        crawl_records.values(),
        key=lambda record: hashlib.sha256(
            f"translation-v2-jiqizhixin\0{record['url']}".encode("utf-8")
        ).digest(),
    )
    for attempt, warc_record in enumerate(ordered, start=1):
        if attempt > max_attempts:
            break
        if translations >= translation_target and originals >= original_target:
            break
        try:
            html = warc_html(client, warc_record)
            record = extract_jiqizhixin(
                html,
                warc_record["url"],
                _crawl_at(warc_record),
                warc_record,
            )
        except Exception:
            exclusions["fetch_or_extract_error"] += 1
            continue
        if not record or not record.get("quality_pass"):
            exclusions["shape_or_quality"] += 1
            continue
        article_type = record.get("article_type")
        candidate: dict[str, Any] | None = None
        if translations < translation_target and article_type in {"翻译", "编译"}:
            candidate = candidate_record(
                record,
                candidate_label="translation",
                label_evidence=[f"article_type={article_type}"],
                label_status="deterministic",
            )
        elif (
            originals < original_target
            and article_type == "原创"
            and not record.get("is_translation")
            and not record.get("translation_evidence")
        ):
            candidate = candidate_record(
                record,
                candidate_label="original_pending_review",
                label_evidence=["article_type=原创"],
                label_status="manual_review_required",
            )
        if candidate is None:
            exclusions["insufficient_label_evidence"] += 1
            continue
        if admit_candidate(
            candidate, exclusion=exclusion, output=records, exclusions=exclusions
        ):
            if candidate["candidate_label"] == "translation":
                translations += 1
            else:
                originals += 1
            print(
                f"[jiqizhixin] translations={translations}/{translation_target} "
                f"originals={originals}/{original_target}",
                flush=True,
            )
    if translations < translation_target or originals < original_target:
        raise RuntimeError(
            f"Insufficient Machine Heart candidates: translations={translations}, "
            f"originals={originals}"
        )
    return records, exclusions


def lctt_metadata(markdown: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in markdown.splitlines()[:30]:
        match = LCTT_METADATA_RE.match(line.strip())
        if match:
            metadata[match.group(1).lower()] = match.group(2).strip()
    return metadata


def markdown_to_text(markdown: str) -> str:
    text = MARKDOWN_FENCE_RE.sub("\n", markdown)
    text = MARKDOWN_REFERENCE_RE.sub("", text)
    text = MARKDOWN_IMAGE_RE.sub("", text)
    text = MARKDOWN_LINK_RE.sub(lambda match: match.group(1) or match.group(2), text)
    text = re.sub(r"^\[#\]:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-=]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`>]", "", text)
    text = BeautifulSoup(text, "html.parser").get_text("\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def github_json(url: str) -> Any:
    response = requests.get(
        url,
        headers={"User-Agent": "deaiodorant-translation-benchmark/2.0"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def collect_lctt(
    exclusion: ExclusionIndex,
    *,
    target: int,
    delay: float,
) -> tuple[list[dict[str, Any]], Counter[str], str]:
    records: list[dict[str, Any]] = []
    exclusions: Counter[str] = Counter()
    ref = github_json(
        f"https://api.github.com/repos/{LCTT_REPOSITORY}/git/ref/heads/master"
    )
    commit = ref["object"]["sha"]
    tree = github_json(
        f"https://api.github.com/repos/{LCTT_REPOSITORY}/git/trees/{commit}?recursive=1"
    )["tree"]
    paths = [
        item["path"]
        for item in tree
        if item["type"] == "blob"
        and item["path"].endswith(".md")
        and item["path"].startswith(("published/2023", "published/2024"))
    ]
    ordered_paths = sorted(
        paths,
        key=lambda path: hashlib.sha256(
            f"translation-v2-lctt\0{path}".encode("utf-8")
        ).digest(),
    )
    session = requests.Session()
    session.headers["User-Agent"] = "deaiodorant-translation-benchmark/2.0"
    for path in ordered_paths:
        if len(records) >= target:
            break
        raw_url = f"https://raw.githubusercontent.com/{LCTT_REPOSITORY}/{commit}/{path}"
        try:
            response = session.get(raw_url, timeout=45)
            response.raise_for_status()
        except requests.RequestException:
            exclusions["fetch_error"] += 1
            continue
        metadata = lctt_metadata(response.text)
        if not metadata.get("translator") or not metadata.get("via"):
            exclusions["missing_translation_metadata"] += 1
            continue
        text = markdown_to_text(response.text)
        metrics = quality_metrics(text)
        if not metrics["quality_pass"]:
            exclusions["low_quality"] += 1
            continue
        month_match = re.match(r"published/(20\d{2})(\d{2})/", path)
        if not month_match:
            exclusions["missing_publication_month"] += 1
            continue
        published_at = f"{month_match.group(1)}-{month_match.group(2)}-01"
        blob_url = f"https://github.com/{LCTT_REPOSITORY}/blob/{commit}/{path}"
        record = {
            "doc_id": hashlib.sha256(blob_url.encode("utf-8")).hexdigest()[:24],
            "source": "lctt",
            "url": blob_url,
            "title": metadata.get("subject") or Path(path).stem,
            "authors": [metadata["author"]] if metadata.get("author") else [],
            "translators": [metadata["translator"]],
            "reviewers": [metadata["reviewer"]] if metadata.get("reviewer") else [],
            "published_at": published_at,
            "publication_date_precision": "month",
            "collected_at": utc_now(),
            "text": text,
            "original_url": metadata["via"],
            "acquisition_method": "pinned_github_raw_file",
            "repository": LCTT_REPOSITORY,
            "repository_commit": commit,
            "repository_path": path,
            "license": LCTT_LICENSE,
            "visibility_evidence": "established_public_translation_project",
            **metrics,
        }
        candidate = candidate_record(
            record,
            candidate_label="translation",
            label_evidence=[
                "lctt_published_translation",
                f"translator={metadata['translator']}",
                "original_url",
            ],
            label_status="deterministic",
        )
        if admit_candidate(
            candidate, exclusion=exclusion, output=records, exclusions=exclusions
        ):
            print(f"[lctt] translations={len(records)}/{target}", flush=True)
        time.sleep(delay)
    if len(records) < target:
        raise RuntimeError(f"Only {len(records)} LCTT translations were collected")
    return records, exclusions, commit


def summarize_candidates(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(records)
    return {
        "documents": len(rows),
        "candidate_labels": dict(Counter(row["candidate_label"] for row in rows)),
        "sources": dict(Counter(row["source"] for row in rows)),
    }


def collect(args: argparse.Namespace) -> None:
    exclusions = list(DEFAULT_EXCLUSIONS) + list(args.exclude_dataset or [])
    index = ExclusionIndex.from_paths(exclusions)
    client = HttpClient(delay=args.delay, timeout=args.http_timeout)
    infoq, infoq_exclusions = collect_infoq(
        client,
        index,
        translation_target=args.infoq_translations,
        original_target=args.infoq_originals,
        max_attempts=args.infoq_max_attempts,
    )
    jiqizhixin, jiqizhixin_exclusions = collect_jiqizhixin(
        client,
        index,
        translation_target=args.jiqizhixin_translations,
        original_target=args.jiqizhixin_originals,
        max_attempts=args.jiqizhixin_max_attempts,
    )
    lctt, lctt_exclusions, lctt_commit = collect_lctt(
        index, target=args.lctt_translations, delay=args.delay
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "infoq_candidates.jsonl", infoq)
    write_jsonl(args.output_dir / "jiqizhixin_candidates.jsonl", jiqizhixin)
    write_jsonl(args.output_dir / "lctt_candidates.jsonl", lctt)
    all_records = infoq + jiqizhixin + lctt
    write_review_queue(args.output_dir / "review_queue.csv", all_records)
    report = {
        "protocol_version": BENCHMARK_PROTOCOL_VERSION,
        "generated_at": utc_now(),
        "transition_period": [TRANSITION_START.isoformat(), TRANSITION_END.isoformat()],
        "exclusion_datasets": [str(path) for path in exclusions],
        "candidates": summarize_candidates(all_records),
        "lctt_commit": lctt_commit,
        "exclusions": {
            "infoq": dict(infoq_exclusions),
            "jiqizhixin": dict(jiqizhixin_exclusions),
            "lctt": dict(lctt_exclusions),
        },
    }
    (args.output_dir / "collection_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _reviewed_records(
    records: list[dict[str, Any]], decisions: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    finalized: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        if item["candidate_label"] == "translation":
            item["gold_label"] = "translation"
            item["gold_evidence"] = item["label_evidence"]
            item["reviewer"] = "deterministic_evidence"
            finalized.append(item)
            continue
        decision = decisions.get(item["doc_id"])
        if not decision or decision.get("review_include", "").strip().lower() != "yes":
            continue
        if decision.get("review_gold_label", "").strip() != "original":
            continue
        for field in ("reviewer", "reviewed_at"):
            if not decision.get(field, "").strip():
                raise RuntimeError(f"Missing {field} for reviewed document {item['doc_id']}")
        item["gold_label"] = "original"
        item["gold_evidence"] = ["manual_reviewed_chinese_original"]
        item["reviewer"] = decision["reviewer"].strip()
        item["reviewed_at"] = decision["reviewed_at"].strip()
        item["review_notes"] = decision.get("review_notes", "").strip()
        finalized.append(item)
    return finalized


def _take_split(
    pools: dict[str, list[dict[str, Any]]],
    *,
    count_per_class: int,
    name: str,
    allowed_sources: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for label in ("original", "translation"):
        candidates = [
            record
            for record in pools[label]
            if allowed_sources is None or record["source"] in allowed_sources
        ]
        taken, _ = balanced_take(
            candidates,
            count_per_class,
            seed=f"{BENCHMARK_PROTOCOL_VERSION}-{name}-{label}",
        )
        selected.extend(taken)
        taken_ids = {record["doc_id"] for record in taken}
        pools[label] = [
            record for record in pools[label] if record["doc_id"] not in taken_ids
        ]
    return stable_order(selected, f"{BENCHMARK_PROTOCOL_VERSION}-{name}-order")


def finalize(args: argparse.Namespace) -> None:
    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    records = [record for path in candidate_paths for record in read_jsonl(path)]
    decisions = read_review_decisions(args.decisions)
    finalized = _reviewed_records(records, decisions)
    pools = {
        label: [record for record in finalized if record["gold_label"] == label]
        for label in ("original", "translation")
    }
    sealed_test = _take_split(
        pools,
        count_per_class=args.test_per_class,
        name="sealed-test",
        allowed_sources={"infoq", "jiqizhixin"},
    )
    validation = _take_split(
        pools,
        count_per_class=args.validation_per_class,
        name="validation",
        allowed_sources={"infoq", "jiqizhixin"},
    )
    development = _take_split(
        pools,
        count_per_class=args.development_per_class,
        name="development",
    )
    splits = {
        "development": development,
        "validation": validation,
        "sealed_test": sealed_test,
    }
    assert_disjoint(splits)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, split_records in splits.items():
        path = args.output_dir / f"{name}.jsonl"
        write_jsonl(path, split_records)
        paths[name] = path
    manifest = {
        "protocol_version": BENCHMARK_PROTOCOL_VERSION,
        "status": "unfrozen_development",
        "generated_at": utc_now(),
        "split_seed": BENCHMARK_PROTOCOL_VERSION,
        "splits": {
            name: {
                "path": str(path),
                "sha256": file_sha256(path),
                "documents": len(splits[name]),
                "labels": dict(Counter(row["gold_label"] for row in splits[name])),
                "sources": dict(Counter(row["source"] for row in splits[name])),
            }
            for name, path in paths.items()
        },
        "test_access_policy": (
            "Do not run or inspect sealed_test predictions until prompt, model digest, "
            "decision policy, and thresholds are frozen. Test outcomes may not be used "
            "to revise the same protocol version."
        ),
        "old_exposed_final_reused": False,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def bootstrap_development(args: argparse.Namespace) -> None:
    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    records = [record for path in candidate_paths for record in read_jsonl(path)]
    translations = [
        record for record in records if record["candidate_label"] == "translation"
    ]
    originals = [
        record
        for record in records
        if record["source"] == "jiqizhixin"
        and record["candidate_label"] == "original_pending_review"
        and "article_type=原创" in record.get("label_evidence", [])
        and not record.get("is_translation")
        and not translation_evidence(
            record["text"],
            translators=record.get("translators"),
            article_type=record.get("article_type"),
        )
    ]
    selected_translations, _ = balanced_take(
        translations,
        args.per_class,
        seed=f"{BENCHMARK_PROTOCOL_VERSION}-silver-development-translation",
    )
    selected_originals, _ = balanced_take(
        originals,
        args.per_class,
        seed=f"{BENCHMARK_PROTOCOL_VERSION}-silver-development-original",
    )
    development: list[dict[str, Any]] = []
    for record in selected_translations:
        item = dict(record)
        item["gold_label"] = "translation"
        item["gold_evidence"] = item["label_evidence"]
        item["label_quality"] = "deterministic_translation_evidence"
        development.append(item)
    for record in selected_originals:
        item = dict(record)
        item["gold_label"] = "original"
        item["gold_evidence"] = ["platform_article_type_original"]
        item["label_quality"] = "silver_platform_label_not_human_gold"
        development.append(item)
    development = stable_order(
        development, f"{BENCHMARK_PROTOCOL_VERSION}-silver-development-order"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output, development)
    manifest = {
        "protocol_version": BENCHMARK_PROTOCOL_VERSION,
        "status": "development_only_silver_labels",
        "generated_at": utc_now(),
        "path": str(args.output),
        "sha256": file_sha256(args.output),
        "documents": len(development),
        "labels": dict(Counter(row["gold_label"] for row in development)),
        "sources": dict(Counter(row["source"] for row in development)),
        "restriction": (
            "This artifact may be used for prompt development only. It must not be "
            "reported as human gold, validation, or final-test evidence."
        ),
    }
    manifest_path = args.output.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def prepare_review(args: argparse.Namespace) -> None:
    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    if not candidate_paths:
        raise RuntimeError(f"No candidate files found in {args.candidate_dir}")
    manifest = prepare_label_studio_workspace(
        candidate_paths,
        args.workspace,
        reviewer=args.reviewer,
        port=args.port,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def bootstrap_review(args: argparse.Namespace) -> None:
    manifest = bootstrap_label_studio_project(args.workspace, timeout=args.timeout)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def export_review(args: argparse.Namespace) -> None:
    summary = export_label_studio_decisions(
        args.workspace, args.output, reviewer=args.reviewer
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def triage_review(args: argparse.Namespace) -> None:
    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    if not candidate_paths:
        raise RuntimeError(f"No candidate files found in {args.candidate_dir}")
    records = [record for path in candidate_paths for record in read_jsonl(path)]
    pending = [
        record
        for record in records
        if record.get("candidate_label") == "original_pending_review"
    ]
    decisions = read_review_decisions(args.decisions)
    primary = ReviewTriageClassifier(
        args.model,
        args.output_dir / "primary_cache.jsonl",
        endpoint=args.endpoint,
        timeout=args.timeout,
        profile="primary",
        backend=args.backend,
    )
    verifier = ReviewTriageClassifier(
        args.model,
        args.output_dir / "verifier_cache.jsonl",
        endpoint=args.endpoint,
        timeout=args.timeout,
        profile="verifier",
        backend=args.backend,
    )
    safeguard = ReviewTriageClassifier(
        args.model,
        args.output_dir / "safeguard_cache.jsonl",
        endpoint=args.endpoint,
        timeout=args.timeout,
        profile="safeguard",
        backend=args.backend,
    )
    _, manifest = run_review_triage(
        pending,
        decisions,
        primary=primary,
        verifier=verifier,
        safeguard=safeguard,
        output_dir=args.output_dir,
        candidate_paths=candidate_paths,
        decisions_path=args.decisions,
        concurrency=args.concurrency,
        model_digest=args.model_digest,
        routing_only=args.routing_only,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def publish_triage_review(args: argparse.Namespace) -> None:
    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    records = [record for path in candidate_paths for record in read_jsonl(path)]
    records_by_id = {record["doc_id"]: record for record in records}
    triage_results = read_jsonl(args.triage_dir / "triage_results.jsonl")
    uncertain_ids = [
        row["doc_id"]
        for row in triage_results
        if row.get("triage_status") == "uncertain"
    ]
    uncertain_records = [records_by_id[doc_id] for doc_id in uncertain_ids]
    project = create_label_studio_subset_project(
        args.workspace,
        uncertain_records,
        title="DeAIodorant uncertain review v2",
        description=(
            "Human review subset containing only candidates that remained uncertain "
            "after conservative, three-profile local model triage."
        ),
    )
    manifest_path = args.triage_dir / "triage_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["human_review_project"] = project
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(project, ensure_ascii=False, indent=2))


def export_triage_review(args: argparse.Namespace) -> None:
    manifest = json.loads(
        (args.triage_dir / "triage_manifest.json").read_text(encoding="utf-8")
    )
    project = manifest.get("human_review_project") or {}
    project_id = project.get("project_id")
    if not project_id:
        raise RuntimeError("The uncertain-review Label Studio project is not available")

    base_output = args.triage_dir / "base_project_decisions.csv"
    subset_output = args.triage_dir / "uncertain_project_decisions.csv"
    base_summary = export_label_studio_decisions(
        args.workspace, base_output, reviewer=args.reviewer
    )
    subset_summary = export_label_studio_project_decisions(
        args.workspace,
        int(project_id),
        subset_output,
        reviewer=args.reviewer,
    )

    merged: dict[str, dict[str, str]] = {}
    for path in (base_output, subset_output):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("review_include", "").strip().lower() not in {"yes", "no"}:
                    continue
                merged[row["doc_id"]] = row
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged.values())
    summary = {
        "base_project": base_summary,
        "uncertain_project": subset_summary,
        "merged_human_decisions": len(merged),
        "output": str(args.output.resolve()),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def triage_value(args: argparse.Namespace) -> None:
    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    records = [record for path in candidate_paths for record in read_jsonl(path)]
    pending = [
        record
        for record in records
        if record.get("candidate_label") == "original_pending_review"
    ]
    provenance_rows = read_jsonl(args.provenance_results)
    provenance = {row["doc_id"]: row for row in provenance_rows}
    primary = ResearchValueClassifier(
        args.model,
        args.output_dir / "primary_cache.jsonl",
        endpoint=args.endpoint,
        timeout=args.timeout,
        profile="primary",
        backend=args.backend,
    )
    verifier = ResearchValueClassifier(
        args.model,
        args.output_dir / "verifier_cache.jsonl",
        endpoint=args.endpoint,
        timeout=args.timeout,
        profile="verifier",
        backend=args.backend,
    )
    _, manifest = run_value_triage(
        pending,
        provenance,
        primary=primary,
        verifier=verifier,
        output_dir=args.output_dir,
        candidate_paths=candidate_paths,
        concurrency=args.concurrency,
        model_digest=args.model_digest,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def publish_value_review(args: argparse.Namespace) -> None:
    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    records = [record for path in candidate_paths for record in read_jsonl(path)]
    records_by_id = {record["doc_id"]: record for record in records}
    value_results = read_jsonl(args.value_dir / "value_results.jsonl")
    uncertain_ids = [
        row["doc_id"]
        for row in value_results
        if row.get("value_status") == "value_uncertain"
    ]
    uncertain_records = [records_by_id[doc_id] for doc_id in uncertain_ids]
    project = create_label_studio_subset_project(
        args.workspace,
        uncertain_records,
        title="DeAIodorant research value review v1",
        description=(
            "Human quality review for documents whose research value remained "
            "uncertain after two-profile Qwen3.8-27B BF16 triage."
        ),
        label_config=VALUE_LABEL_CONFIG,
        instruction=(
            "Judge research value separately from translation provenance. Keep concrete "
            "facts, technical detail, implementation experience, evidence-rich "
            "interviews, or independent analysis. Exclude promotional and "
            "information-thin material."
        ),
    )
    manifest_path = args.value_dir / "value_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["human_review_project"] = project
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(project, ensure_ascii=False, indent=2))


def export_value_review(args: argparse.Namespace) -> None:
    manifest = json.loads(
        (args.value_dir / "value_manifest.json").read_text(encoding="utf-8")
    )
    project = manifest.get("human_review_project") or {}
    project_id = project.get("project_id")
    if not project_id:
        raise RuntimeError("The research-value review project is not available")
    summary = export_label_studio_value_decisions(
        args.workspace,
        int(project_id),
        args.output,
        reviewer=args.reviewer,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a leak-resistant translation-gate v2 benchmark."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument(
        "--output-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    collect_parser.add_argument("--exclude-dataset", type=Path, action="append")
    collect_parser.add_argument("--infoq-translations", type=int, default=80)
    collect_parser.add_argument("--infoq-originals", type=int, default=100)
    collect_parser.add_argument("--infoq-max-attempts", type=int, default=2500)
    collect_parser.add_argument("--jiqizhixin-translations", type=int, default=40)
    collect_parser.add_argument("--jiqizhixin-originals", type=int, default=120)
    collect_parser.add_argument("--jiqizhixin-max-attempts", type=int, default=1600)
    collect_parser.add_argument("--lctt-translations", type=int, default=100)
    collect_parser.add_argument("--delay", type=float, default=0.12)
    collect_parser.add_argument("--http-timeout", type=float, default=60.0)

    development_parser = subparsers.add_parser("bootstrap-development")
    development_parser.add_argument(
        "--candidate-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    development_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/translation_v2/development_silver.jsonl"),
    )
    development_parser.add_argument("--per-class", type=int, default=80)

    review_parser = subparsers.add_parser("prepare-review")
    review_parser.add_argument(
        "--candidate-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    review_parser.add_argument(
        "--workspace", type=Path, default=Path("data/local/translation_v2_review")
    )
    review_parser.add_argument("--reviewer")
    review_parser.add_argument("--port", type=int, default=8080)

    bootstrap_review_parser = subparsers.add_parser("bootstrap-review")
    bootstrap_review_parser.add_argument(
        "--workspace", type=Path, default=Path("data/local/translation_v2_review")
    )
    bootstrap_review_parser.add_argument("--timeout", type=float, default=180.0)

    export_review_parser = subparsers.add_parser("export-review")
    export_review_parser.add_argument(
        "--workspace", type=Path, default=Path("data/local/translation_v2_review")
    )
    export_review_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/local/translation_v2_review/review_decisions.csv"),
    )
    export_review_parser.add_argument("--reviewer")

    triage_review_parser = subparsers.add_parser("triage-review")
    triage_review_parser.add_argument(
        "--candidate-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    triage_review_parser.add_argument(
        "--decisions",
        type=Path,
        default=Path("data/local/translation_v2_review/review_decisions.csv"),
    )
    triage_review_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/local/translation_v2_review/triage"),
    )
    triage_review_parser.add_argument("--model", default="qwen3.5:9b")
    triage_review_parser.add_argument(
        "--endpoint", "--ollama-endpoint", dest="endpoint", default="http://127.0.0.1:11434"
    )
    triage_review_parser.add_argument(
        "--backend", choices=["ollama", "openai"], default="ollama"
    )
    triage_review_parser.add_argument("--concurrency", type=int, default=1)
    triage_review_parser.add_argument("--model-digest")
    triage_review_parser.add_argument("--routing-only", action="store_true")
    triage_review_parser.add_argument("--timeout", type=float, default=600.0)

    publish_triage_parser = subparsers.add_parser("publish-triage-review")
    publish_triage_parser.add_argument(
        "--candidate-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    publish_triage_parser.add_argument(
        "--triage-dir",
        type=Path,
        default=Path("data/local/translation_v2_review/triage"),
    )
    publish_triage_parser.add_argument(
        "--workspace", type=Path, default=Path("data/local/translation_v2_review")
    )

    export_triage_parser = subparsers.add_parser("export-triage-review")
    export_triage_parser.add_argument(
        "--triage-dir",
        type=Path,
        default=Path("data/local/translation_v2_review/triage"),
    )
    export_triage_parser.add_argument(
        "--workspace", type=Path, default=Path("data/local/translation_v2_review")
    )
    export_triage_parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/local/translation_v2_review/human_review_decisions_merged.csv"
        ),
    )
    export_triage_parser.add_argument("--reviewer", required=True)

    value_triage_parser = subparsers.add_parser("triage-value")
    value_triage_parser.add_argument(
        "--candidate-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    value_triage_parser.add_argument(
        "--provenance-results",
        type=Path,
        default=Path("data/local/translation_v2_review/triage/triage_results.jsonl"),
    )
    value_triage_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/local/translation_v2_review/triage/value"),
    )
    value_triage_parser.add_argument("--model", default="qwen3.5:9b")
    value_triage_parser.add_argument(
        "--endpoint", "--ollama-endpoint", dest="endpoint", default="http://127.0.0.1:11434"
    )
    value_triage_parser.add_argument(
        "--backend", choices=["ollama", "openai"], default="ollama"
    )
    value_triage_parser.add_argument("--concurrency", type=int, default=1)
    value_triage_parser.add_argument("--model-digest")
    value_triage_parser.add_argument("--timeout", type=float, default=600.0)

    publish_value_parser = subparsers.add_parser("publish-value-review")
    publish_value_parser.add_argument(
        "--candidate-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    publish_value_parser.add_argument(
        "--value-dir",
        type=Path,
        default=Path("data/local/translation_v2_review/triage_qwen38/value"),
    )
    publish_value_parser.add_argument(
        "--workspace", type=Path, default=Path("data/local/translation_v2_review")
    )

    export_value_parser = subparsers.add_parser("export-value-review")
    export_value_parser.add_argument(
        "--value-dir",
        type=Path,
        default=Path("data/local/translation_v2_review/triage_qwen38/value"),
    )
    export_value_parser.add_argument(
        "--workspace", type=Path, default=Path("data/local/translation_v2_review")
    )
    export_value_parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/local/translation_v2_review/research_value_decisions.csv"
        ),
    )
    export_value_parser.add_argument("--reviewer", required=True)

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument(
        "--candidate-dir", type=Path, default=Path("data/translation_v2/candidates")
    )
    finalize_parser.add_argument(
        "--decisions",
        type=Path,
        default=Path("data/translation_v2/candidates/review_queue.csv"),
    )
    finalize_parser.add_argument(
        "--output-dir", type=Path, default=Path("data/translation_v2")
    )
    finalize_parser.add_argument("--development-per-class", type=int, default=80)
    finalize_parser.add_argument("--validation-per-class", type=int, default=40)
    finalize_parser.add_argument("--test-per-class", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    if args.command == "collect":
        collect(args)
    elif args.command == "bootstrap-development":
        bootstrap_development(args)
    elif args.command == "prepare-review":
        prepare_review(args)
    elif args.command == "bootstrap-review":
        bootstrap_review(args)
    elif args.command == "export-review":
        export_review(args)
    elif args.command == "triage-review":
        triage_review(args)
    elif args.command == "publish-triage-review":
        publish_triage_review(args)
    elif args.command == "export-triage-review":
        export_triage_review(args)
    elif args.command == "triage-value":
        triage_value(args)
    elif args.command == "publish-value-review":
        publish_value_review(args)
    elif args.command == "export-value-review":
        export_value_review(args)
    elif args.command == "finalize":
        finalize(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
