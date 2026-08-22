"""Build a validated post-period reader-corpus handoff from reviewed staging."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from deaiodorant.corpus.benchmark import file_sha256, read_jsonl, write_jsonl
from pilot_collect import CJK_RE, POST_START


PROTOCOL_VERSION = "post-reader-corpus-handoff-1.1"
SELECTION_VERSION = "post-reader-handoff-selection-1.1"
DEFAULT_SEED = "post-reader-handoff-v1-20260822"
REQUIRED_FORMATS = (
    "technical_practice",
    "research_summary",
    "industry_reporting",
)
REQUIRED_SOURCES = ("infoq", "meituan_tech")
MIN_PER_SOURCE = 12
MIN_PER_FORMAT = 6
MIN_TOPICS = 3
MIN_PER_TOPIC = 6
INFOQ_MIN_QUARTER_PERCENTILE = 0.40


def quarter(date_value: str) -> str:
    """Return an ISO year-quarter label."""

    date = dt.date.fromisoformat(date_value)
    return f"{date.year}-Q{(date.month - 1) // 3 + 1}"


def percentile_ranks(values: list[int]) -> list[float]:
    """Return deterministic midranks in [0, 1]."""

    if len(values) <= 1:
        return [1.0] * len(values)
    ordered = sorted((value, index) for index, value in enumerate(values))
    output = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][0] == ordered[cursor][0]:
            end += 1
        rank = ((cursor + end - 1) / 2) / (len(values) - 1)
        for _, index in ordered[cursor:end]:
            output[index] = rank
        cursor = end
    return output


def infoq_visibility(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compute publication-quarter view percentiles before value selection."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("source") == "infoq" and isinstance(record.get("views"), int):
            grouped[quarter(record["published_at"])].append(record)
    output: dict[str, dict[str, Any]] = {}
    for period, items in grouped.items():
        ranks = percentile_ranks([int(item["views"]) for item in items])
        for item, rank in zip(items, ranks, strict=True):
            output[item["doc_id"]] = {
                "basis": "source_quarter_relative_page_views",
                "quarter": period,
                "views": item["views"],
                "source_quarter_percentile": round(rank, 6),
                "observed_at": item["collected_at"],
                "article_level_metric": True,
            }
    return output


def stable_key(seed: str, doc_id: str) -> str:
    """Return a stable selection tiebreak independent of outcomes."""

    return hashlib.sha256(f"{seed}\0{doc_id}".encode("utf-8")).hexdigest()


def select_records(
    records: list[dict[str, Any]], seed: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Retain every admitted record after checking minimum coverage."""

    selected = sorted(records, key=lambda record: stable_key(seed, record["doc_id"]))
    source_counts = Counter(record["source"] for record in selected)
    format_counts = Counter(record["format_stratum"] for record in selected)
    topic_counts = Counter(record["topic_stratum"] for record in selected)
    source_format_counts = Counter(
        f"{record['source']}/{record['format_stratum']}" for record in selected
    )
    for source in REQUIRED_SOURCES:
        if source_counts[source] < MIN_PER_SOURCE:
            raise RuntimeError(f"Source {source} has fewer than 12 documents")
    for format_name in REQUIRED_FORMATS:
        if format_counts[format_name] < MIN_PER_FORMAT:
            raise RuntimeError(f"Format {format_name} has fewer than six documents")
    target_topics = [
        topic
        for topic, count in sorted(topic_counts.items(), key=lambda item: (-item[1], item[0]))
        if topic != "other" and count >= MIN_PER_TOPIC
    ]
    if len(target_topics) < MIN_TOPICS:
        raise RuntimeError("Fewer than three topics have six documents")
    diagnostics = {
        "source_counts": dict(sorted(source_counts.items())),
        "format_counts": dict(sorted(format_counts.items())),
        "source_format_counts": dict(sorted(source_format_counts.items())),
        "eligible_topic_counts": dict(sorted(topic_counts.items())),
        "target_topics": target_topics,
        "selected_documents": len(selected),
    }
    return selected, diagnostics


def normalize_body(text: str) -> str:
    """Normalize materialized source text to one terminal LF."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    return normalized + "\n"


def input_identity(paths: list[Path]) -> list[dict[str, str]]:
    """Record resolved paths and hashes for input artifacts."""

    return [
        {"path": str(path.resolve()), "sha256": file_sha256(path.resolve())}
        for path in paths
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the fresh post-period reader corpus handoff."
    )
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--provenance-results", type=Path, required=True)
    parser.add_argument("--provenance-manifest", type=Path, required=True)
    parser.add_argument("--value-results", type=Path, required=True)
    parser.add_argument("--value-manifest", type=Path, required=True)
    parser.add_argument("--strata-results", type=Path, required=True)
    parser.add_argument("--strata-manifest", type=Path, required=True)
    parser.add_argument("--preparation-manifest", type=Path, required=True)
    parser.add_argument("--acquisition-manifest", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    texts_dir = output_dir / "texts"
    texts_dir.mkdir()

    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    candidates = [record for path in candidate_paths for record in read_jsonl(path)]
    records_by_id = {record["doc_id"]: record for record in candidates}
    provenance_rows = read_jsonl(args.provenance_results)
    provenance = {row["doc_id"]: row for row in provenance_rows}
    value_rows = read_jsonl(args.value_results)
    value = {row["doc_id"]: row for row in value_rows}
    strata_rows = read_jsonl(args.strata_results)
    strata = {row["doc_id"]: row for row in strata_rows}
    visibility = infoq_visibility(candidates)

    eligible: list[dict[str, Any]] = []
    exclusion_counts: Counter[str] = Counter()
    for doc_id, record in records_by_id.items():
        provenance_row = provenance.get(doc_id, {})
        value_row = value.get(doc_id, {})
        strata_row = strata.get(doc_id, {})
        reason: str | None = None
        if provenance_row.get("triage_status") != "model_assisted_original":
            reason = "provenance_not_high_confidence_original"
        elif value_row.get("value_status") != "model_assisted_substantive":
            reason = "value_not_high_confidence_substantive"
        elif strata_row.get("confidence") != "high":
            reason = "strata_not_high_confidence"
        elif strata_row.get("format_stratum") not in REQUIRED_FORMATS:
            reason = "format_not_admitted"
        elif strata_row.get("topic_stratum") == "other":
            reason = "topic_not_admitted"
        elif record["source"] == "infoq":
            visibility_item = visibility.get(doc_id)
            if visibility_item is None:
                reason = "missing_page_view_visibility"
            elif (
                visibility_item["source_quarter_percentile"]
                < INFOQ_MIN_QUARTER_PERCENTILE
            ):
                reason = "below_infoq_quarter_visibility_median"
        elif record["source"] == "meituan_tech":
            visibility_item = dict(record.get("visibility_snapshot") or {})
            if not visibility_item:
                reason = "missing_official_source_visibility"
            else:
                visibility_item.update(
                    {
                        "basis": "official_history_and_json_feed_snapshot",
                        "article_level_metric": False,
                    }
                )
        else:
            reason = "source_not_admitted"
        if reason is not None:
            exclusion_counts[reason] += 1
            continue
        item = dict(record)
        item["provenance_row"] = provenance_row
        item["value_row"] = value_row
        item["strata_row"] = strata_row
        item["format_stratum"] = strata_row["format_stratum"]
        item["topic_stratum"] = strata_row["topic_stratum"]
        item["visibility_item"] = visibility_item
        item["visibility_score"] = (
            float(visibility_item["source_quarter_percentile"])
            if record["source"] == "infoq"
            else 1.0
        )
        eligible.append(item)

    selected, selection_diagnostics = select_records(eligible, args.seed)
    documents: list[dict[str, Any]] = []
    text_hashes: dict[str, str] = {}
    for record in selected:
        stored = normalize_body(record["text"])
        body = stored[:-1]
        text_path = texts_dir / f"{record['doc_id']}.txt"
        text_path.write_text(stored, encoding="utf-8", newline="\n")
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        text_hashes[record["doc_id"]] = content_hash
        provenance_row = record["provenance_row"]
        value_row = record["value_row"]
        strata_row = record["strata_row"]
        documents.append(
            {
                "doc_id": record["doc_id"],
                "source": record["source"],
                "published_at": record["published_at"],
                "collected_at": record["collected_at"],
                "title": record["title"],
                "url": record["url"],
                "authors": record.get("authors") or [],
                "body_path": f"texts/{record['doc_id']}.txt",
                "content_hash": content_hash,
                "cjk_chars": len(CJK_RE.findall(body)),
                "text_chars": len(body),
                "line_count": len(body.splitlines()),
                "quality_pass": True,
                "is_translation": False,
                "translation_evidence": list(record.get("translation_evidence") or [])
                + list(provenance_row.get("safeguard_evidence") or []),
                "provenance_status": "model_assisted_original",
                "provenance_basis": "model_assisted_measurement",
                "provenance_confidence": 1.0,
                "provenance_confidence_label": provenance_row[
                    "safeguard_confidence"
                ],
                "provenance_model": provenance_row["model"],
                "provenance_prompt_version": provenance_row[
                    "safeguard_prompt_version"
                ],
                "value_status": "model_assisted_substantive",
                "value_basis": "model_assisted_measurement",
                "value_model": value_row["model"],
                "value_prompt_version": value_row["primary_prompt_version"],
                "value_verifier_prompt_version": value_row[
                    "verifier_prompt_version"
                ],
                "value_evidence": list(value_row.get("primary_evidence") or [])
                + list(value_row.get("verifier_evidence") or []),
                "visibility_status": "verified_high_visibility",
                "visibility_evidence": record["visibility_item"],
                "topic_stratum": strata_row["topic_stratum"],
                "format_stratum": strata_row["format_stratum"],
                "strata_basis": "model_assisted_measurement",
                "strata_model": strata_row["model"],
                "strata_prompt_version": strata_row["prompt_version"],
                "recommended_role": "unassigned_fresh_pool",
            }
        )

    documents_path = output_dir / "documents.jsonl"
    write_jsonl(documents_path, documents)
    sources = Counter(row["source"] for row in documents)
    months = Counter(row["published_at"][:7] for row in documents)
    formats = Counter(row["format_stratum"] for row in documents)
    topics = Counter(row["topic_stratum"] for row in documents)
    source_formats = Counter(
        f"{row['source']}/{row['format_stratum']}" for row in documents
    )
    provenance_manifest = json.loads(
        args.provenance_manifest.read_text(encoding="utf-8")
    )
    value_manifest = json.loads(args.value_manifest.read_text(encoding="utf-8"))
    strata_manifest = json.loads(args.strata_manifest.read_text(encoding="utf-8"))
    preparation_manifest = json.loads(
        args.preparation_manifest.read_text(encoding="utf-8")
    )
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "selection_version": SELECTION_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "candidate_pool_not_reader_exposed",
        "post_start": POST_START.isoformat(),
        "documents": len(documents),
        "documents_file": "documents.jsonl",
        "documents_sha256": file_sha256(documents_path),
        "texts_sha256": text_hashes,
        "period_counts": {"post": len(documents)},
        "source_counts": dict(sorted(sources.items())),
        "month_counts": dict(sorted(months.items())),
        "format_counts": dict(sorted(formats.items())),
        "topic_counts": dict(sorted(topics.items())),
        "source_format_counts": dict(sorted(source_formats.items())),
        "allocation_status": "unassigned_fresh_pool",
        "candidate_flow": {
            "acquisition_documents": preparation_manifest["input_documents"],
            "after_duplicate_exclusion": preparation_manifest[
                "prepared_documents"
            ],
            "provenance_status_counts": provenance_manifest["status_counts"],
            "value_status_counts": value_manifest["status_counts"],
            "strata_confidence_counts": strata_manifest["confidence_counts"],
            "admission_exclusion_counts": dict(sorted(exclusion_counts.items())),
            "eligible_before_balancing": len(eligible),
            "final_documents": len(documents),
        },
        "selection_policy": {
            "seed": args.seed,
            "required_sources": list(REQUIRED_SOURCES),
            "required_formats": list(REQUIRED_FORMATS),
            "minimum_documents_per_source": MIN_PER_SOURCE,
            "minimum_documents_per_format": MIN_PER_FORMAT,
            "minimum_topics": MIN_TOPICS,
            "minimum_documents_per_topic": MIN_PER_TOPIC,
            "infoq_min_source_quarter_view_percentile": (
                INFOQ_MIN_QUARTER_PERCENTILE
            ),
            "meituan_visibility_basis": (
                "official public history and JSON feed snapshot"
            ),
            "selection_diagnostics": selection_diagnostics,
        },
        "model_measurements": {
            "provenance": {
                "model": provenance_manifest["model"],
                "model_digest": provenance_manifest["model_digest"],
                "prompt_versions": provenance_manifest["prompt_versions"],
                "executed_profiles": provenance_manifest["executed_profiles"],
            },
            "value": {
                "model": value_manifest["model"],
                "model_digest": value_manifest["model_digest"],
                "prompt_versions": value_manifest["prompt_versions"],
            },
            "strata": {
                "model": strata_manifest["model"],
                "model_digest": strata_manifest["model_digest"],
                "prompt_version": strata_manifest["prompt_version"],
            },
            "restriction": "Model-assisted labels are measurements, not human gold.",
        },
        "input_sha256": {
            "candidate_files": input_identity(candidate_paths),
            "acquisition_manifests": input_identity(args.acquisition_manifest),
            "preparation_manifest": input_identity([args.preparation_manifest])[0],
            "provenance_results": input_identity([args.provenance_results])[0],
            "provenance_manifest": input_identity([args.provenance_manifest])[0],
            "value_results": input_identity([args.value_results])[0],
            "value_manifest": input_identity([args.value_manifest])[0],
            "strata_results": input_identity([args.strata_results])[0],
            "strata_manifest": input_identity([args.strata_manifest])[0],
        },
        "limitations": [
            "The pool is fresh reader-development material, not held-out validation.",
            "InfoQ visibility uses current page views ranked within publication quarter.",
            "Meituan visibility is source-level official editorial distribution without article view counts.",
            "Model-assisted provenance, value, format, and topic labels are measurements.",
            "Document-level development and reserve assignment remains unmade.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
