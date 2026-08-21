"""Read and validate a prepared monthly corpus without modifying it."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class CorpusValidationError(ValueError):
    """Raised when prepared corpus data violates an analysis invariant."""


SAFE_DOC_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


@dataclass(frozen=True)
class CorpusDocument:
    """One immutable input document and its analysis metadata."""

    doc_id: str
    source: str
    cohort: str
    published_at: dt.date
    text_path: Path
    text: str
    content_hash: str
    metadata: dict[str, Any]

    def stratum_value(self, field: str) -> str:
        """Return a stable string value for a configured stratification field."""

        if field == "source":
            return self.source
        if field == "cohort":
            return self.cohort
        if field == "published_month":
            return self.published_at.strftime("%Y-%m")
        value = self.metadata.get(field)
        if value is None or value == "":
            return "__missing__"
        if isinstance(value, (dict, list)):
            return json.dumps(
                value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        return str(value)


@dataclass(frozen=True)
class CorpusLoadResult:
    """Validated documents plus deterministic provenance for the input set."""

    documents: tuple[CorpusDocument, ...]
    metadata_files: tuple[Path, ...]
    excluded_transition_documents: int
    corpus_fingerprint: str


def _parse_date(value: Any, *, doc_id: str) -> dt.date:
    if not isinstance(value, str):
        raise CorpusValidationError(
            f"{doc_id}: published_at must be an ISO date string"
        )
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError as exc:
        raise CorpusValidationError(
            f"{doc_id}: invalid published_at value {value!r}"
        ) from exc


def _cohort_for_date(
    published_at: dt.date,
    *,
    pre_end_exclusive: dt.date,
    post_start_inclusive: dt.date,
) -> str | None:
    if published_at < pre_end_exclusive:
        return "pre"
    if published_at >= post_start_inclusive:
        return "post"
    return None


def _validate_admission_metadata(record: dict[str, Any], *, doc_id: str) -> None:
    if record.get("quality_pass") is False:
        raise CorpusValidationError(f"{doc_id}: quality_pass is false")
    if record.get("is_translation") is True:
        raise CorpusValidationError(f"{doc_id}: translated content is not admissible")
    if record.get("admitted") is False:
        raise CorpusValidationError(f"{doc_id}: admitted is false")

    admission_status = record.get("admission_status")
    if admission_status is not None and admission_status != "admitted":
        raise CorpusValidationError(
            f"{doc_id}: admission_status must be 'admitted', got {admission_status!r}"
        )

    translation_status = record.get("translation_status")
    if translation_status in {"translation", "translated", "uncertain"}:
        raise CorpusValidationError(
            f"{doc_id}: translation_status is not admissible: {translation_status!r}"
        )


def _resolve_text_path(metadata_path: Path, text_file: Any, *, doc_id: str) -> Path:
    if not isinstance(text_file, str) or not text_file:
        raise CorpusValidationError(f"{doc_id}: text_file must be a non-empty string")
    month_dir = metadata_path.parent.resolve()
    text_path = (month_dir / text_file).resolve()
    try:
        text_path.relative_to(month_dir)
    except ValueError as exc:
        raise CorpusValidationError(
            f"{doc_id}: text_file escapes its monthly directory"
        ) from exc
    if not text_path.is_file():
        raise CorpusValidationError(f"{doc_id}: text file does not exist: {text_path}")
    return text_path


def _fingerprint_document(document: CorpusDocument) -> bytes:
    record = {
        "cohort": document.cohort,
        "content_hash": document.content_hash,
        "doc_id": document.doc_id,
        "metadata": document.metadata,
        "published_at": document.published_at.isoformat(),
        "source": document.source,
    }
    return json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def load_monthly_corpus(
    root: Path,
    *,
    pre_end_exclusive: dt.date = dt.date(2023, 1, 1),
    post_start_inclusive: dt.date = dt.date(2025, 7, 1),
) -> CorpusLoadResult:
    """Load a monthly corpus and validate all documents admitted to either cohort."""

    root = root.resolve()
    if not root.is_dir():
        raise CorpusValidationError(f"Corpus root is not a directory: {root}")
    if pre_end_exclusive > post_start_inclusive:
        raise CorpusValidationError(
            "The pre cohort cutoff must not follow the post cutoff"
        )

    metadata_files = tuple(sorted(root.rglob("meta.jsonl")))
    if not metadata_files:
        raise CorpusValidationError(f"No meta.jsonl files found under {root}")

    documents: list[CorpusDocument] = []
    seen_ids: set[str] = set()
    excluded_transition = 0

    for metadata_path in metadata_files:
        for line_number, line in enumerate(
            metadata_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CorpusValidationError(
                    f"{metadata_path}:{line_number}: invalid JSON"
                ) from exc
            if not isinstance(record, dict):
                raise CorpusValidationError(
                    f"{metadata_path}:{line_number}: metadata record must be an object"
                )

            doc_id = record.get("doc_id")
            if not isinstance(doc_id, str) or not doc_id:
                raise CorpusValidationError(
                    f"{metadata_path}:{line_number}: doc_id must be a non-empty string"
                )
            if not SAFE_DOC_ID_RE.fullmatch(doc_id):
                raise CorpusValidationError(
                    f"{metadata_path}:{line_number}: doc_id is not path-safe"
                )
            if doc_id in seen_ids:
                raise CorpusValidationError(f"Duplicate doc_id: {doc_id}")
            seen_ids.add(doc_id)

            published_at = _parse_date(record.get("published_at"), doc_id=doc_id)
            cohort = _cohort_for_date(
                published_at,
                pre_end_exclusive=pre_end_exclusive,
                post_start_inclusive=post_start_inclusive,
            )
            if cohort is None:
                excluded_transition += 1
                continue

            declared_period = record.get("period")
            if declared_period is not None and declared_period != cohort:
                raise CorpusValidationError(
                    f"{doc_id}: period {declared_period!r} contradicts publication date"
                )
            _validate_admission_metadata(record, doc_id=doc_id)

            source = record.get("source")
            if not isinstance(source, str) or not source:
                raise CorpusValidationError(
                    f"{doc_id}: source must be a non-empty string"
                )
            text_path = _resolve_text_path(
                metadata_path,
                record.get("text_file"),
                doc_id=doc_id,
            )
            text = text_path.read_text(encoding="utf-8")
            if not text.strip():
                raise CorpusValidationError(f"{doc_id}: text is empty")
            content_hash = hashlib.sha256(text.rstrip("\n").encode("utf-8")).hexdigest()
            declared_hash = record.get("content_hash")
            if declared_hash is not None and declared_hash != content_hash:
                raise CorpusValidationError(
                    f"{doc_id}: content_hash does not match {text_path.name}"
                )

            documents.append(
                CorpusDocument(
                    doc_id=doc_id,
                    source=source,
                    cohort=cohort,
                    published_at=published_at,
                    text_path=text_path,
                    text=text,
                    content_hash=content_hash,
                    metadata=record,
                )
            )

    documents.sort(key=lambda document: document.doc_id)
    if not documents:
        raise CorpusValidationError("No documents fall inside the configured cohorts")

    digest = hashlib.sha256()
    for document in documents:
        digest.update(_fingerprint_document(document))
        digest.update(b"\n")

    return CorpusLoadResult(
        documents=tuple(documents),
        metadata_files=metadata_files,
        excluded_transition_documents=excluded_transition,
        corpus_fingerprint=digest.hexdigest(),
    )
