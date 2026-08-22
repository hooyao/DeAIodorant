"""Validate a fresh post-period corpus handoff before reader exposure."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from deaiodorant.corpus.benchmark import ExclusionIndex, read_jsonl


PROTOCOL_VERSION = "post-reader-corpus-handoff-1.1"
REPORT_VERSION = "post-reader-corpus-validation-1.1"
POST_START = dt.date(2025, 7, 1)
MIN_DOCUMENTS = 36
MIN_SOURCES = 2
MIN_DOCUMENTS_PER_SOURCE = 12
MIN_TOPICS = 3
MIN_DOCUMENTS_PER_TOPIC = 6
MIN_DOCUMENTS_PER_FORMAT = 6
MIN_MODEL_PROVENANCE_CONFIDENCE = 0.90
REQUIRED_FORMATS = (
    "technical_practice",
    "research_summary",
    "industry_reporting",
)
ALLOWED_PROVENANCE = {
    "human_reviewed_original",
    "model_assisted_original",
}
ALLOWED_VALUE_STATUS = {
    "human_kept",
    "model_assisted_substantive",
}
REQUIRED_DOCUMENT_FIELDS = {
    "doc_id",
    "source",
    "published_at",
    "collected_at",
    "title",
    "url",
    "body_path",
    "content_hash",
    "cjk_chars",
    "text_chars",
    "line_count",
    "quality_pass",
    "is_translation",
    "translation_evidence",
    "provenance_status",
    "provenance_basis",
    "value_status",
    "visibility_status",
    "visibility_evidence",
    "topic_stratum",
    "format_stratum",
}

DOC_ID_RE = re.compile(r"^[0-9a-f]{24}$")
DOC_ID_SEARCH_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{24}(?![0-9a-f])")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SCANNED_EXPOSURE_SUFFIXES = {".json", ".md", ".py"}


def add_issue(
    report: dict[str, Any], level: str, location: str, message: str
) -> None:
    """Append one structured validation issue."""

    report[level].append({"location": location, "message": message})


def parse_iso_timestamp(value: object) -> bool:
    """Return whether a value is a non-empty ISO timestamp."""

    if not isinstance(value, str) or not value:
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def file_sha256(path: Path) -> str:
    """Hash one file without changing it."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exposed_doc_ids(repository_root: Path) -> set[str]:
    """Collect document IDs already named by tracked research artifacts."""

    roots = (
        repository_root / "data" / "annotations",
        repository_root / "experiments",
        repository_root / "docs",
    )
    observed: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCANNED_EXPOSURE_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            observed.update(DOC_ID_SEARCH_RE.findall(text))
    return observed


def tracked_pilot_records(repository_root: Path) -> list[dict[str, object]]:
    """Load tracked pilot bodies for duplicate rejection only."""

    records: list[dict[str, object]] = []
    monthly_root = repository_root / "data" / "pilot" / "monthly"
    for meta_path in sorted(monthly_root.glob("*/meta.jsonl")):
        for record in read_jsonl(meta_path):
            text_name = str(record.get("text_file") or f"{record.get('doc_id')}.txt")
            text_path = meta_path.parent / text_name
            if not text_path.is_file():
                continue
            text = text_path.read_text(encoding="utf-8").rstrip("\n")
            records.append(
                {
                    "doc_id": record.get("doc_id"),
                    "url": record.get("url"),
                    "text": text,
                }
            )
    return records


def safe_body_path(handoff_root: Path, value: object) -> Path | None:
    """Resolve one required relative body path inside the handoff root."""

    if not isinstance(value, str) or not value:
        return None
    relative = Path(value)
    if relative.is_absolute():
        return None
    resolved = (handoff_root / relative).resolve()
    try:
        resolved.relative_to(handoff_root)
    except ValueError:
        return None
    return resolved


def validate_document(
    *,
    record: dict[str, object],
    location: str,
    handoff_root: Path,
    exposure_ids: set[str],
    exclusion_index: ExclusionIndex,
    report: dict[str, Any],
) -> dict[str, object] | None:
    """Validate one index record and its materialized body."""

    initial_error_count = len(report["errors"])
    missing = sorted(REQUIRED_DOCUMENT_FIELDS.difference(record))
    if missing:
        add_issue(report, "errors", location, f"Missing fields: {', '.join(missing)}")
        return None

    doc_id = record["doc_id"]
    if not isinstance(doc_id, str) or not DOC_ID_RE.fullmatch(doc_id):
        add_issue(report, "errors", location, "doc_id must be 24 lowercase hex characters")
        return None
    if doc_id in exposure_ids:
        add_issue(report, "errors", location, "doc_id already appears in research artifacts")

    try:
        published_at = dt.date.fromisoformat(str(record["published_at"]))
    except ValueError:
        add_issue(report, "errors", location, "published_at is not an ISO date")
        published_at = None
    if published_at is not None and published_at < POST_START:
        add_issue(
            report,
            "errors",
            location,
            f"published_at precedes the fixed post boundary {POST_START.isoformat()}",
        )
    if not parse_iso_timestamp(record["collected_at"]):
        add_issue(report, "errors", location, "collected_at is not an ISO timestamp")

    source = record["source"]
    topic = record["topic_stratum"]
    format_stratum = record["format_stratum"]
    for name, value in (
        ("source", source),
        ("title", record["title"]),
        ("topic_stratum", topic),
    ):
        if not isinstance(value, str) or not value.strip():
            add_issue(report, "errors", location, f"{name} must be a non-empty string")
    if format_stratum not in REQUIRED_FORMATS:
        add_issue(
            report,
            "errors",
            location,
            f"format_stratum must be one of: {', '.join(REQUIRED_FORMATS)}",
        )

    url = record["url"]
    try:
        parsed_url = urlsplit(url) if isinstance(url, str) else None
    except ValueError:
        parsed_url = None
    if (
        parsed_url is None
        or parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
    ):
        add_issue(report, "errors", location, "url must be an absolute HTTP(S) URL")

    if record["quality_pass"] is not True:
        add_issue(report, "errors", location, "quality_pass must be true")
    if record["is_translation"] is not False:
        add_issue(report, "errors", location, "is_translation must be false")
    if not isinstance(record["translation_evidence"], list):
        add_issue(report, "errors", location, "translation_evidence must be a list")

    provenance = record["provenance_status"]
    if provenance not in ALLOWED_PROVENANCE:
        add_issue(report, "errors", location, "provenance_status does not admit the document")
    if not isinstance(record["provenance_basis"], str) or not record["provenance_basis"]:
        add_issue(report, "errors", location, "provenance_basis must be non-empty")
    if provenance == "model_assisted_original":
        confidence = record.get("provenance_confidence")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or confidence < MIN_MODEL_PROVENANCE_CONFIDENCE
        ):
            add_issue(
                report,
                "errors",
                location,
                "model-assisted provenance requires confidence >= 0.90",
            )
        if not isinstance(record.get("provenance_model"), str) or not record.get(
            "provenance_model"
        ):
            add_issue(
                report,
                "errors",
                location,
                "model-assisted provenance requires provenance_model",
            )
        if not isinstance(record.get("provenance_prompt_version"), str) or not record.get(
            "provenance_prompt_version"
        ):
            add_issue(
                report,
                "errors",
                location,
                "model-assisted provenance requires provenance_prompt_version",
            )
    if record["value_status"] not in ALLOWED_VALUE_STATUS:
        add_issue(report, "errors", location, "value_status does not admit the document")
    elif record["value_status"] == "model_assisted_substantive":
        for field in ("value_model", "value_prompt_version"):
            if not isinstance(record.get(field), str) or not record.get(field):
                add_issue(
                    report,
                    "errors",
                    location,
                    f"model-assisted value status requires {field}",
                )

    if record["visibility_status"] != "verified_high_visibility":
        add_issue(
            report,
            "errors",
            location,
            "visibility_status must be verified_high_visibility",
        )
    visibility_evidence = record["visibility_evidence"]
    if not isinstance(visibility_evidence, dict) or not visibility_evidence:
        add_issue(report, "errors", location, "visibility_evidence must be a non-empty object")

    body_path = safe_body_path(handoff_root, record["body_path"])
    if body_path is None:
        add_issue(report, "errors", location, "body_path must stay inside the handoff root")
        return None
    if not body_path.is_file():
        add_issue(report, "errors", location, f"Missing body file: {record['body_path']}")
        return None
    try:
        stored_text = body_path.read_text(encoding="utf-8")
    except UnicodeError:
        add_issue(report, "errors", str(body_path), "Body is not strict UTF-8")
        return None
    if stored_text.startswith("\ufeff"):
        add_issue(report, "errors", str(body_path), "Body must not contain a BOM")
    if "\r" in stored_text:
        add_issue(report, "errors", str(body_path), "Body must use LF line endings")
    if not stored_text.endswith("\n") or stored_text.endswith("\n\n"):
        add_issue(report, "errors", str(body_path), "Body must end with exactly one LF")
    body = stored_text[:-1] if stored_text.endswith("\n") else stored_text
    if not body:
        add_issue(report, "errors", str(body_path), "Body is empty")
        return None

    observed_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    expected_hash = record["content_hash"]
    if not isinstance(expected_hash, str) or not HASH_RE.fullmatch(expected_hash):
        add_issue(report, "errors", location, "content_hash must be lowercase SHA-256")
    elif expected_hash != observed_hash:
        add_issue(report, "errors", location, "content_hash does not match body")
    observed_cjk = len(CJK_RE.findall(body))
    observed_lines = len(body.splitlines())
    for field, observed in (
        ("cjk_chars", observed_cjk),
        ("text_chars", len(body)),
        ("line_count", observed_lines),
    ):
        if record[field] != observed:
            add_issue(report, "errors", location, f"{field} does not match body")

    duplicate = exclusion_index.match({"doc_id": doc_id, "url": url, "text": body})
    if duplicate is not None:
        add_issue(
            report,
            "errors",
            location,
            f"Duplicate ({duplicate.reason}) of {duplicate.existing_doc_id}",
        )
    else:
        exclusion_index.add({"doc_id": doc_id, "url": url, "text": body})

    if len(report["errors"]) > initial_error_count:
        return None
    return {
        "doc_id": doc_id,
        "source": source,
        "topic_stratum": topic,
        "format_stratum": format_stratum,
        "published_at": published_at.isoformat() if published_at else None,
        "cjk_chars": observed_cjk,
    }


def validate_handoff(handoff_root: Path, repository_root: Path) -> dict[str, Any]:
    """Validate structural admission and minimum reader-development coverage."""

    handoff_root = handoff_root.resolve()
    repository_root = repository_root.resolve()
    report: dict[str, Any] = {
        "schema_version": REPORT_VERSION,
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "handoff_root": str(handoff_root),
        "repository_root": str(repository_root),
        "valid": False,
        "reader_development_ready": False,
        "errors": [],
        "warnings": [],
        "counts": {},
        "coverage": {},
        "limits": {
            "post_start": POST_START.isoformat(),
            "minimum_documents": MIN_DOCUMENTS,
            "minimum_sources": MIN_SOURCES,
            "minimum_documents_per_source": MIN_DOCUMENTS_PER_SOURCE,
            "minimum_topics": MIN_TOPICS,
            "minimum_documents_per_topic": MIN_DOCUMENTS_PER_TOPIC,
            "required_formats": list(REQUIRED_FORMATS),
            "minimum_documents_per_format": MIN_DOCUMENTS_PER_FORMAT,
        },
    }
    manifest_path = handoff_root / "manifest.json"
    if not manifest_path.is_file():
        add_issue(report, "errors", str(manifest_path), "Missing manifest.json")
        return report
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        add_issue(report, "errors", str(manifest_path), f"Invalid manifest: {exc}")
        return report
    if manifest.get("protocol_version") != PROTOCOL_VERSION:
        add_issue(report, "errors", str(manifest_path), "Unexpected protocol_version")
    if manifest.get("status") != "candidate_pool_not_reader_exposed":
        add_issue(report, "errors", str(manifest_path), "Unexpected handoff status")
    if not parse_iso_timestamp(manifest.get("generated_at")):
        add_issue(report, "errors", str(manifest_path), "generated_at is invalid")
    if manifest.get("post_start") != POST_START.isoformat():
        add_issue(report, "errors", str(manifest_path), "post_start conflicts with protocol")

    documents_name = manifest.get("documents_file")
    documents_path = safe_body_path(handoff_root, documents_name)
    if documents_path is None or not documents_path.is_file():
        add_issue(report, "errors", str(manifest_path), "documents_file is missing or unsafe")
        return report
    expected_index_hash = manifest.get("documents_sha256")
    observed_index_hash = file_sha256(documents_path)
    if expected_index_hash != observed_index_hash:
        add_issue(report, "errors", str(documents_path), "documents_sha256 mismatch")

    try:
        records = read_jsonl(documents_path)
    except (UnicodeError, json.JSONDecodeError) as exc:
        add_issue(report, "errors", str(documents_path), f"Invalid documents file: {exc}")
        return report
    if manifest.get("documents") != len(records):
        add_issue(report, "errors", str(manifest_path), "documents count mismatch")

    exposure_ids = exposed_doc_ids(repository_root)
    exclusion_index = ExclusionIndex()
    for record in tracked_pilot_records(repository_root):
        exclusion_index.add(record)

    admitted: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for line_number, record in enumerate(records, start=1):
        location = f"{documents_path}:{line_number}"
        if not isinstance(record, dict):
            add_issue(report, "errors", location, "Record is not a JSON object")
            continue
        doc_id = record.get("doc_id")
        url = record.get("url")
        if isinstance(doc_id, str) and doc_id in seen_ids:
            add_issue(report, "errors", location, "Duplicate doc_id inside handoff")
        elif isinstance(doc_id, str):
            seen_ids.add(doc_id)
        if isinstance(url, str) and url in seen_urls:
            add_issue(report, "errors", location, "Duplicate URL inside handoff")
        elif isinstance(url, str):
            seen_urls.add(url)
        validated = validate_document(
            record=record,
            location=location,
            handoff_root=handoff_root,
            exposure_ids=exposure_ids,
            exclusion_index=exclusion_index,
            report=report,
        )
        if validated is not None:
            admitted.append(validated)

    source_counts = Counter(str(item["source"]) for item in admitted)
    topic_counts = Counter(str(item["topic_stratum"]) for item in admitted)
    format_counts = Counter(str(item["format_stratum"]) for item in admitted)
    source_format_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for item in admitted:
        source_format_counts[str(item["source"])][str(item["format_stratum"])] += 1

    report["counts"] = {
        "indexed_documents": len(records),
        "structurally_readable_documents": len(admitted),
        "sources": dict(sorted(source_counts.items())),
        "topics": dict(sorted(topic_counts.items())),
        "formats": dict(sorted(format_counts.items())),
    }
    eligible_topics = sorted(
        topic for topic, count in topic_counts.items() if count >= MIN_DOCUMENTS_PER_TOPIC
    )
    eligible_sources = sorted(
        source for source, count in source_counts.items() if count >= MIN_DOCUMENTS_PER_SOURCE
    )
    report["coverage"] = {
        "eligible_topics": eligible_topics,
        "eligible_sources": eligible_sources,
        "source_format_counts": {
            source: {name: counts[name] for name in REQUIRED_FORMATS}
            for source, counts in sorted(source_format_counts.items())
        },
    }
    if len(admitted) < MIN_DOCUMENTS:
        add_issue(report, "errors", str(documents_path), "Fewer than 36 documents")
    if len(eligible_topics) < MIN_TOPICS:
        add_issue(
            report,
            "errors",
            str(documents_path),
            "Fewer than three topics have at least six documents",
        )
    if len(eligible_sources) < MIN_SOURCES:
        add_issue(
            report,
            "errors",
            str(documents_path),
            "Fewer than two sources have at least 12 documents",
        )
    for format_name in REQUIRED_FORMATS:
        if format_counts[format_name] < MIN_DOCUMENTS_PER_FORMAT:
            add_issue(
                report,
                "errors",
                str(documents_path),
                f"Format {format_name} has fewer than six documents",
            )

    report["valid"] = not report["errors"]
    report["reader_development_ready"] = report["valid"]
    if report["valid"] and len(admitted) < 60:
        add_issue(
            report,
            "warnings",
            str(documents_path),
            "Development can start, but an independent validation reserve is not yet available",
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a fresh post-period reader-corpus handoff."
    )
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate_handoff(args.handoff_root, args.repository_root)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if report["reader_development_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
