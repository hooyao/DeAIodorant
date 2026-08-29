"""Build a fresh multi-source post handoff with a frozen validation reserve."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from deaiodorant.corpus.benchmark import file_sha256, read_jsonl, write_jsonl
from experiments.validate_post_reader_handoff import exposed_doc_ids


PROTOCOL_VERSION = "post-reader-corpus-handoff-1.1"
SELECTION_VERSION = "expanded-post-reader-handoff-selection-2.0"
POST_START = dt.date(2025, 7, 1)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
REQUIRED_FORMATS = frozenset(
    {"technical_practice", "research_summary", "industry_reporting"}
)
HUAWEI_VISIBILITY_PERCENTILE = 0.40
RESERVE_SEED = "post-reader-handoff-v2-reserve-20260830"
RESERVE_TOPIC_QUOTAS = {
    "ai_models_agents": 16,
    "business_industry": 7,
    "data_infrastructure": 7,
}
PROVENANCE_MODELS = "qwen3.8-27b + deepseek/deepseek-v4-flash-0731"
PROVENANCE_PROMPT = (
    "translation-review-triage-foreign-source-safeguard-v2/"
    "two-model-intersection"
)
VALUE_MODELS = "qwen3.8-27b + deepseek/deepseek-v4-flash-0731"
VALUE_PROMPT = "research-value-primary-v3+verifier-v3/two-model-intersection"


def _normalize(text: str) -> tuple[str, str]:
    body = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    return body, body + "\n"


def _stable_key(doc_id: str) -> str:
    return hashlib.sha256(
        f"{RESERVE_SEED}\0{doc_id}".encode("utf-8")
    ).hexdigest()


def _quarter(date_value: str) -> str:
    date = dt.date.fromisoformat(date_value)
    return f"{date.year}-Q{(date.month - 1) // 3 + 1}"


def _percentile_ranks(values: list[int]) -> list[float]:
    if len(values) == 1:
        return [1.0]
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][0] == ordered[cursor][0]:
            end += 1
        rank = ((cursor + end - 1) / 2) / (len(values) - 1)
        for _, index in ordered[cursor:end]:
            ranks[index] = rank
        cursor = end
    return ranks


def _candidate_records(directory: Path) -> list[dict[str, Any]]:
    return [
        row
        for path in sorted(directory.glob("*_candidates.jsonl"))
        for row in read_jsonl(path)
    ]


def _eligible_new(
    candidates: list[dict[str, Any]],
    value_path: Path,
    strata_path: Path,
    *,
    huawei_visibility: bool,
) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    value = {row["doc_id"]: row for row in read_jsonl(value_path)}
    strata = {row["doc_id"]: row for row in read_jsonl(strata_path)}
    visibility: dict[str, float] = {}
    if huawei_visibility:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in candidates:
            if isinstance(record.get("views"), int):
                grouped[_quarter(str(record["published_at"]))].append(record)
        for items in grouped.values():
            ranks = _percentile_ranks([int(item["views"]) for item in items])
            for item, rank in zip(items, ranks, strict=True):
                visibility[str(item["doc_id"])] = rank

    output: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for record in candidates:
        doc_id = str(record["doc_id"])
        value_row = value.get(doc_id, {})
        strata_row = strata.get(doc_id, {})
        if value_row.get("value_status") != "model_assisted_substantive":
            continue
        if strata_row.get("confidence") != "high":
            continue
        if strata_row.get("format_stratum") not in REQUIRED_FORMATS:
            continue
        if strata_row.get("topic_stratum") == "other":
            continue
        if (
            huawei_visibility
            and visibility.get(doc_id, 0.0) < HUAWEI_VISIBILITY_PERCENTILE
        ):
            continue
        item = dict(record)
        if huawei_visibility:
            item["source_quarter_view_percentile"] = round(
                visibility[doc_id], 6
            )
        output.append((item, value_row, strata_row))
    return output


def _new_document(
    record: dict[str, Any],
    value_row: dict[str, Any],
    strata_row: dict[str, Any],
    *,
    role: str,
) -> tuple[dict[str, Any], str]:
    body, stored = _normalize(str(record["text"]))
    if str(record["source"]) == "huawei_cloud_community":
        visibility = dict(record.get("visibility_snapshot") or {})
        visibility.update(
            {
                "basis": "source_quarter_relative_views_on_recommended_articles",
                "source_quarter": _quarter(str(record["published_at"])),
                "source_quarter_percentile": record["source_quarter_view_percentile"],
                "minimum_percentile": HUAWEI_VISIBILITY_PERCENTILE,
                "article_level_metric": True,
            }
        )
    else:
        visibility = dict(record.get("visibility_snapshot") or {})
        visibility.update(
            {
                "basis": str(record["visibility_evidence"]),
                "article_level_metric": False,
            }
        )
    document = {
        "doc_id": record["doc_id"],
        "source": record["source"],
        "published_at": record["published_at"],
        "collected_at": record["collected_at"],
        "title": record["title"],
        "url": record["url"],
        "authors": record.get("authors") or [],
        "body_path": f"texts/{record['doc_id']}.txt",
        "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "cjk_chars": len(CJK_RE.findall(body)),
        "text_chars": len(body),
        "line_count": len(body.splitlines()),
        "quality_pass": True,
        "is_translation": False,
        "translation_evidence": list(record.get("translation_evidence") or [])
        + ["two_current_models_agree_high_confidence_original"],
        "provenance_status": "model_assisted_original",
        "provenance_basis": "two_model_intersection_measurement",
        "provenance_confidence": 1.0,
        "provenance_confidence_label": "high",
        "provenance_model": PROVENANCE_MODELS,
        "provenance_prompt_version": PROVENANCE_PROMPT,
        "value_status": "model_assisted_substantive",
        "value_basis": "two_model_intersection_measurement",
        "value_model": VALUE_MODELS,
        "value_prompt_version": VALUE_PROMPT,
        "value_evidence": ["two_current_models_agree_substantive"],
        "visibility_status": "verified_high_visibility",
        "visibility_evidence": visibility,
        "topic_stratum": strata_row["topic_stratum"],
        "format_stratum": strata_row["format_stratum"],
        "strata_basis": "model_assisted_measurement",
        "strata_model": strata_row["model"],
        "strata_prompt_version": strata_row["prompt_version"],
        "recommended_role": role,
        "prior_exposure": "none_after_admission",
    }
    return document, stored


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-handoff", type=Path, required=True)
    parser.add_argument("--editorial-candidate-dir", type=Path, required=True)
    parser.add_argument("--editorial-value", type=Path, required=True)
    parser.add_argument("--editorial-strata", type=Path, required=True)
    parser.add_argument("--huawei-candidate-dir", type=Path, required=True)
    parser.add_argument("--huawei-value", type=Path, required=True)
    parser.add_argument("--huawei-strata", type=Path, required=True)
    parser.add_argument("--input-artifact", type=Path, action="append", default=[])
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    texts_dir = output_dir / "texts"
    texts_dir.mkdir()

    exposure_ids = exposed_doc_ids(args.repository_root.resolve())
    base_root = args.base_handoff.resolve()
    base_documents = [
        row
        for row in read_jsonl(base_root / "documents.jsonl")
        if str(row["doc_id"]) not in exposure_ids
    ]

    editorial_candidates = _candidate_records(args.editorial_candidate_dir.resolve())
    editorial = _eligible_new(
        editorial_candidates,
        args.editorial_value.resolve(),
        args.editorial_strata.resolve(),
        huawei_visibility=False,
    )
    huawei_candidates = _candidate_records(args.huawei_candidate_dir.resolve())
    huawei = _eligible_new(
        huawei_candidates,
        args.huawei_value.resolve(),
        args.huawei_strata.resolve(),
        huawei_visibility=True,
    )
    new_items = editorial + huawei

    by_topic: dict[
        str,
        list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    ] = defaultdict(list)
    for item in new_items:
        by_topic[str(item[2]["topic_stratum"])].append(item)
    reserve_ids: set[str] = set()
    for topic, quota in RESERVE_TOPIC_QUOTAS.items():
        items = sorted(
            by_topic[topic],
            key=lambda item: _stable_key(str(item[0]["doc_id"])),
        )
        if len(items) < quota:
            raise RuntimeError(f"Insufficient reserve candidates for {topic}")
        reserve_ids.update(str(item[0]["doc_id"]) for item in items[:quota])

    documents: list[dict[str, Any]] = []
    for record in base_documents:
        source_path = base_root / str(record["body_path"])
        body, stored = _normalize(source_path.read_text(encoding="utf-8"))
        item = dict(record)
        item["body_path"] = f"texts/{record['doc_id']}.txt"
        item["content_hash"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        item["cjk_chars"] = len(CJK_RE.findall(body))
        item["text_chars"] = len(body)
        item["line_count"] = len(body.splitlines())
        item["recommended_role"] = "development"
        item["prior_exposure"] = "deterministic_feature_scan_only"
        (texts_dir / f"{record['doc_id']}.txt").write_text(
            stored, encoding="utf-8", newline="\n"
        )
        documents.append(item)

    for record, value_row, strata_row in new_items:
        role = (
            "validation_reserve"
            if str(record["doc_id"]) in reserve_ids
            else "development"
        )
        item, stored = _new_document(
            record,
            value_row,
            strata_row,
            role=role,
        )
        (texts_dir / f"{record['doc_id']}.txt").write_text(
            stored, encoding="utf-8", newline="\n"
        )
        documents.append(item)

    documents.sort(key=lambda row: str(row["doc_id"]))
    if len({row["doc_id"] for row in documents}) != len(documents):
        raise RuntimeError("Duplicate document ID in expanded handoff")
    if len({row["url"] for row in documents}) != len(documents):
        raise RuntimeError("Duplicate URL in expanded handoff")
    if len({row["content_hash"] for row in documents}) != len(documents):
        raise RuntimeError("Duplicate body hash in expanded handoff")

    documents_path = output_dir / "documents.jsonl"
    write_jsonl(documents_path, documents)
    source_counts = Counter(str(row["source"]) for row in documents)
    format_counts = Counter(str(row["format_stratum"]) for row in documents)
    topic_counts = Counter(str(row["topic_stratum"]) for row in documents)
    role_counts = Counter(str(row["recommended_role"]) for row in documents)
    role_composition: dict[str, dict[str, dict[str, int]]] = {}
    for role in sorted(role_counts):
        rows = [row for row in documents if row["recommended_role"] == role]
        role_composition[role] = {
            "sources": dict(sorted(Counter(row["source"] for row in rows).items())),
            "formats": dict(
                sorted(Counter(row["format_stratum"] for row in rows).items())
            ),
            "topics": dict(
                sorted(Counter(row["topic_stratum"] for row in rows).items())
            ),
        }

    identity_paths = [
        base_root / "manifest.json",
        base_root / "documents.jsonl",
        args.editorial_value.resolve(),
        args.editorial_strata.resolve(),
        args.huawei_value.resolve(),
        args.huawei_strata.resolve(),
        *[path.resolve() for path in args.input_artifact],
    ]
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "selection_version": SELECTION_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "candidate_pool_not_reader_exposed",
        "post_start": POST_START.isoformat(),
        "documents": len(documents),
        "documents_file": "documents.jsonl",
        "documents_sha256": file_sha256(documents_path),
        "texts_sha256": {
            row["doc_id"]: row["content_hash"] for row in documents
        },
        "period_counts": {"post": len(documents)},
        "source_counts": dict(sorted(source_counts.items())),
        "month_counts": dict(
            sorted(Counter(row["published_at"][:7] for row in documents).items())
        ),
        "format_counts": dict(sorted(format_counts.items())),
        "topic_counts": dict(sorted(topic_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "role_composition": role_composition,
        "allocation_status": "frozen_before_new_paragraph_analysis",
        "selection_policy": {
            "base_handoff_documents_retained_for_development": len(base_documents),
            "new_editorial_documents": len(editorial),
            "new_huawei_documents_after_visibility": len(huawei),
            "huawei_visibility_basis": "source-quarter relative views",
            "huawei_minimum_source_quarter_percentile": HUAWEI_VISIBILITY_PERCENTILE,
            "reserve_seed": RESERVE_SEED,
            "reserve_topic_quotas": RESERVE_TOPIC_QUOTAS,
            "reserve_documents": len(reserve_ids),
            "exposed_document_ids_excluded": len(exposure_ids),
        },
        "model_measurements": {
            "provenance_models": PROVENANCE_MODELS,
            "provenance_prompt": PROVENANCE_PROMPT,
            "value_models": VALUE_MODELS,
            "value_prompt": VALUE_PROMPT,
            "strata_model": "qwen3.8-27b",
            "strata_prompt": "post-corpus-format-topic-primary-v1",
            "restriction": "Model-assisted labels are measurements, not human gold.",
        },
        "input_sha256": [
            {"path": str(path), "sha256": file_sha256(path)}
            for path in identity_paths
        ],
        "limitations": [
            "The development partition remains exploratory and is not representative of all Chinese technical prose.",
            "The 30-document reserve is frozen but is not final validation without multiple independent readers.",
            "QbitAI and Leiphone visibility is source-level editorial distribution rather than article-level readership.",
            "Huawei visibility is a collection-time source-quarter percentile among acquired recommended articles.",
            "Source, format, and topic remain imbalanced and require matching in any time comparison.",
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
