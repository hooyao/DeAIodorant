"""Structural integrity checks for the monthly corpus layout."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


REQUIRED_METADATA_FIELDS = {
    "doc_id",
    "source",
    "period",
    "url",
    "published_at",
    "collected_at",
    "quality_pass",
    "is_translation",
    "translation_evidence",
    "visibility_evidence",
    "content_hash",
    "text_file",
}
MONTH_RE = re.compile(r"\d{4}-\d{2}")


def _parse_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _add_error(report: dict[str, Any], location: str, message: str) -> None:
    report["errors"].append({"location": location, "message": message})


def validate_monthly_corpus(
    root: Path, *, required_translation_model: str | None = None
) -> dict[str, Any]:
    """Validate corpus storage invariants without changing corpus files."""
    root = root.resolve()
    report: dict[str, Any] = {
        "schema_version": "corpus-integrity-1",
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root),
        "valid": False,
        "months": 0,
        "documents": 0,
        "required_translation_model": required_translation_model,
        "model_gated_documents": 0,
        "unverified_visibility_documents": 0,
        "errors": [],
        "warnings": [],
    }
    if not root.is_dir():
        _add_error(report, str(root), "Monthly corpus directory does not exist")
        return report

    month_dirs = sorted(
        path for path in root.iterdir() if path.is_dir() and MONTH_RE.fullmatch(path.name)
    )
    report["months"] = len(month_dirs)
    if not month_dirs:
        _add_error(report, str(root), "Monthly corpus contains no month directories")
        return report

    seen_doc_ids: dict[str, str] = {}
    seen_urls: dict[str, str] = {}
    seen_hashes: dict[str, str] = {}

    for month_dir in month_dirs:
        meta_path = month_dir / "meta.jsonl"
        if not meta_path.is_file():
            _add_error(report, str(month_dir), "Month is missing meta.jsonl")
            continue
        try:
            metadata_lines = meta_path.read_text(encoding="utf-8").splitlines()
        except UnicodeError:
            _add_error(report, str(meta_path), "Metadata is not valid UTF-8")
            continue
        if not metadata_lines:
            _add_error(report, str(meta_path), "Metadata file is empty")
            continue

        referenced_text_files: set[str] = set()
        for line_number, line in enumerate(metadata_lines, start=1):
            location = f"{meta_path}:{line_number}"
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                _add_error(report, location, f"Invalid JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                _add_error(report, location, "Metadata record is not a JSON object")
                continue
            missing = sorted(REQUIRED_METADATA_FIELDS.difference(record))
            if missing:
                _add_error(report, location, f"Missing fields: {', '.join(missing)}")
                continue

            report["documents"] += 1
            doc_id = record["doc_id"]
            if not isinstance(doc_id, str) or not doc_id:
                _add_error(report, location, "doc_id must be a non-empty string")
            elif doc_id in seen_doc_ids:
                _add_error(
                    report,
                    location,
                    f"Duplicate doc_id also appears at {seen_doc_ids[doc_id]}",
                )
            else:
                seen_doc_ids[doc_id] = location

            text_file = record["text_file"]
            if (
                not isinstance(text_file, str)
                or Path(text_file).name != text_file
                or text_file != f"{doc_id}.txt"
            ):
                _add_error(report, location, "text_file must equal <doc_id>.txt")
                continue
            referenced_text_files.add(text_file)

            try:
                published = dt.date.fromisoformat(str(record["published_at"]))
            except ValueError:
                _add_error(report, location, "published_at is not an ISO calendar date")
                published = None
            if published is not None:
                if published.strftime("%Y-%m") != month_dir.name:
                    _add_error(report, location, "published_at does not match its month directory")
                expected_period = (
                    "pre"
                    if published < dt.date(2023, 1, 1)
                    else "post"
                    if published >= dt.date(2025, 7, 1)
                    else None
                )
                if expected_period is None:
                    _add_error(report, location, "Document falls inside the excluded transition period")
                elif record["period"] != expected_period:
                    _add_error(report, location, "period conflicts with published_at")

            if not _parse_datetime(record["collected_at"]):
                _add_error(report, location, "collected_at is not an ISO timestamp")
            if not isinstance(record["source"], str) or not record["source"]:
                _add_error(report, location, "source must be a non-empty string")
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
                _add_error(report, location, "url must be an absolute HTTP(S) URL")
            elif url in seen_urls:
                _add_error(report, location, f"Duplicate URL also appears at {seen_urls[url]}")
            else:
                seen_urls[url] = location

            if record["quality_pass"] is not True:
                _add_error(report, location, "Admitted document did not pass the quality gate")
            if record["is_translation"] is not False:
                _add_error(report, location, "Admitted document is marked as translated")
            if not isinstance(record["translation_evidence"], list):
                _add_error(report, location, "translation_evidence must be a list")
            if required_translation_model:
                if record.get("translation_model") != required_translation_model:
                    _add_error(report, location, "Document lacks the configured model gate")
                elif record.get("translation_filter_pass") is not True:
                    _add_error(report, location, "Configured model gate did not pass")
                else:
                    report["model_gated_documents"] += 1
            if not isinstance(record["visibility_evidence"], str) or not record["visibility_evidence"]:
                _add_error(report, location, "visibility_evidence must be a non-empty string")
            elif "unverified" in record["visibility_evidence"]:
                report["unverified_visibility_documents"] += 1

            text_path = month_dir / text_file
            if not text_path.is_file():
                _add_error(report, location, f"Missing body file: {text_file}")
                continue
            try:
                stored_text = text_path.read_text(encoding="utf-8")
            except UnicodeError:
                _add_error(report, str(text_path), "Body is not valid UTF-8")
                continue
            if stored_text.startswith("\ufeff"):
                _add_error(report, str(text_path), "Body must not contain a UTF-8 BOM")
            if "\r" in stored_text:
                _add_error(report, str(text_path), "Body must use normalized LF line endings")
            if not stored_text.endswith("\n") or stored_text.endswith("\n\n"):
                _add_error(report, str(text_path), "Body must end with exactly one newline")
            body = stored_text[:-1] if stored_text.endswith("\n") else stored_text
            if not body:
                _add_error(report, str(text_path), "Body is empty")
            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if record["content_hash"] != content_hash:
                _add_error(report, location, "content_hash does not match the body file")
            elif content_hash in seen_hashes:
                _add_error(
                    report,
                    location,
                    f"Exact duplicate body also appears at {seen_hashes[content_hash]}",
                )
            else:
                seen_hashes[content_hash] = location

        actual_text_files = {path.name for path in month_dir.glob("*.txt")}
        for orphan in sorted(actual_text_files.difference(referenced_text_files)):
            _add_error(report, str(month_dir / orphan), "Body file has no metadata record")

    if report["unverified_visibility_documents"]:
        report["warnings"].append(
            {
                "message": (
                    f"{report['unverified_visibility_documents']} document(s) lack article-level "
                    "visibility verification; structural validity does not make this a final corpus"
                )
            }
        )
    report["valid"] = not report["errors"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a monthly corpus directory.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--require-translation-model")
    args = parser.parse_args()
    report = validate_monthly_corpus(
        args.root, required_translation_model=args.require_translation_model
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
