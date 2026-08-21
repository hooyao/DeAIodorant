"""Build a deterministic document-level feature matrix from a prepared corpus."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from collections import Counter
from pathlib import Path
from typing import Any

from deaiodorant import __version__

from .catalog import build_feature_catalog
from .config import FeatureConfig, load_feature_config
from .corpus import CorpusDocument, CorpusLoadResult, load_monthly_corpus
from .sparse import extract_sparse_features
from .surface import discourse_features, surface_features, title_features
from .syntax import dependency_features, read_conllu


class FeaturePipelineError(ValueError):
    """Raised when inputs cannot produce a complete reproducible feature matrix."""


IDENTIFIER_COLUMNS = (
    "doc_id",
    "cohort",
    "source",
    "published_at",
    "published_month",
    "topic",
    "format",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_canonical_json_bytes(value))


def _prepare_output_directory(path: Path) -> Path:
    path = path.resolve()
    if path.exists() and any(path.iterdir()):
        raise FeaturePipelineError(
            f"Output directory is not empty; feature artifacts are immutable: {path}"
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_annotation_provenance(
    annotation_dir: Path,
    *,
    corpus_fingerprint: str,
    documents: tuple[CorpusDocument, ...],
) -> tuple[dict[str, Any], str]:
    """Validate annotation identity, parser provenance, file set, and hashes."""

    manifest_path = annotation_dir / "annotation_manifest.json"
    if not manifest_path.is_file():
        raise FeaturePipelineError(
            f"Syntax annotations require annotation_manifest.json: {annotation_dir}"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FeaturePipelineError("Invalid annotation manifest JSON") from exc
    if manifest.get("schema_version") != "deaiodorant-annotations-1.0":
        raise FeaturePipelineError("Unsupported annotation manifest schema")
    if manifest.get("corpus_fingerprint") != corpus_fingerprint:
        raise FeaturePipelineError(
            "Annotation manifest does not match the input corpus"
        )
    parser = manifest.get("parser")
    if not isinstance(parser, dict):
        raise FeaturePipelineError("Annotation manifest is missing parser provenance")
    required_parser_fields = {
        "device",
        "language",
        "model_fingerprint",
        "name",
        "version",
    }
    if not required_parser_fields.issubset(parser):
        raise FeaturePipelineError("Annotation parser provenance is incomplete")
    annotation_files = manifest.get("annotation_files")
    if not isinstance(annotation_files, dict):
        raise FeaturePipelineError("Annotation manifest is missing file hashes")
    expected_names = {f"{document.doc_id}.conllu" for document in documents}
    if set(annotation_files) != expected_names:
        raise FeaturePipelineError(
            "Annotation file set does not match corpus document IDs"
        )
    for filename, expected_hash in annotation_files.items():
        annotation_path = annotation_dir / filename
        if not annotation_path.is_file():
            raise FeaturePipelineError(f"Missing annotation file: {filename}")
        if _sha256_file(annotation_path) != expected_hash:
            raise FeaturePipelineError(f"Annotation hash mismatch: {filename}")
    return manifest, _sha256_file(manifest_path)


def _document_row(
    document: CorpusDocument,
    *,
    config: FeatureConfig,
    annotation_dir: Path | None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "cohort": document.cohort,
        "doc_id": document.doc_id,
        "format": document.stratum_value("format"),
        "published_at": document.published_at.isoformat(),
        "published_month": document.published_at.strftime("%Y-%m"),
        "source": document.source,
        "topic": document.stratum_value("topic"),
    }
    row.update(
        surface_features(
            document.text,
            char_ngram_size=config.char_ngram_size,
            char_mattr_window=config.char_mattr_window,
        )
    )
    row.update(discourse_features(document.text))
    title = document.metadata.get("title")
    row.update(title_features(title if isinstance(title, str) else "", document.text))
    if annotation_dir is not None:
        annotation_path = annotation_dir / f"{document.doc_id}.conllu"
        if not annotation_path.is_file():
            raise FeaturePipelineError(
                f"Missing syntax annotation for {document.doc_id}: {annotation_path}"
            )
        row.update(
            dependency_features(
                read_conllu(annotation_path),
                mattr_window=config.token_mattr_window,
            )
        )
    return row


def extract_feature_rows(
    corpus: CorpusLoadResult,
    *,
    config: FeatureConfig,
    annotation_dir: Path | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract a rectangular, document-level feature table in stable order."""

    if config.require_syntax and annotation_dir is None:
        raise FeaturePipelineError("The configuration requires syntax annotations")
    rows = [
        _document_row(
            document,
            config=config,
            annotation_dir=annotation_dir,
        )
        for document in corpus.documents
    ]
    feature_names = sorted(set(rows[0]) - set(IDENTIFIER_COLUMNS))
    expected_columns = set(rows[0])
    for row in rows:
        if set(row) != expected_columns:
            raise FeaturePipelineError(
                "Feature extraction produced a non-rectangular table"
            )
        for feature in feature_names:
            value = row[feature]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise FeaturePipelineError(f"Feature {feature!r} is not numeric")
    return rows, feature_names


def _format_csv_value(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".15g")
    return value


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {column: _format_csv_value(row.get(column)) for column in columns}
            )


def _cohort_source_counts(
    documents: tuple[CorpusDocument, ...],
) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = {"post": Counter(), "pre": Counter()}
    for document in documents:
        counts[document.cohort][document.source] += 1
    return {
        cohort: dict(sorted(source_counts.items()))
        for cohort, source_counts in sorted(counts.items())
    }


def extract_feature_matrix(
    *,
    corpus_root: Path,
    config_path: Path,
    output_dir: Path,
    annotation_dir: Path | None = None,
) -> dict[str, Any]:
    """Write a self-describing feature matrix without statistical comparison."""

    config = load_feature_config(config_path)
    corpus = load_monthly_corpus(
        corpus_root,
        pre_end_exclusive=config.pre_end_exclusive,
        post_start_inclusive=config.post_start_inclusive,
    )
    resolved_annotations = (
        annotation_dir.resolve() if annotation_dir is not None else None
    )
    annotation_manifest = None
    annotation_manifest_hash = None
    if resolved_annotations is not None:
        annotation_manifest, annotation_manifest_hash = validate_annotation_provenance(
            resolved_annotations,
            corpus_fingerprint=corpus.corpus_fingerprint,
            documents=corpus.documents,
        )
    rows, feature_names = extract_feature_rows(
        corpus,
        config=config,
        annotation_dir=resolved_annotations,
    )
    catalog = build_feature_catalog(feature_names)
    sparse = None
    if config.sparse_enabled:
        if resolved_annotations is None:
            raise FeaturePipelineError(
                "Sparse syntax and stylometry features require syntax annotations"
            )
        sparse = extract_sparse_features(
            corpus,
            annotation_dir=resolved_annotations,
            config=config,
        )

    output_dir = _prepare_output_directory(output_dir)
    config_output_path = output_dir / "feature_config.json"
    features_path = output_dir / "document_features.csv"
    catalog_path = output_dir / "feature_catalog.json"
    summary_path = output_dir / "summary.json"
    manifest_path = output_dir / "feature_manifest.json"
    sparse_catalog_path = output_dir / "sparse_feature_catalog.json"
    sparse_values_path = output_dir / "sparse_feature_values.csv"

    _write_json(config_output_path, config.raw)
    _write_csv(
        features_path,
        rows,
        list(IDENTIFIER_COLUMNS) + feature_names,
    )
    _write_json(catalog_path, catalog)
    if sparse is not None:
        _write_json(sparse_catalog_path, sparse.catalog)
        _write_csv(
            sparse_values_path,
            sparse.values,
            ["doc_id", "feature_id", "count", "rate_per_1000_opportunities"],
        )
    cohort_counts = Counter(document.cohort for document in corpus.documents)
    summary = {
        "cohort_counts": dict(sorted(cohort_counts.items())),
        "cohort_source_counts": _cohort_source_counts(corpus.documents),
        "document_count": len(corpus.documents),
        "excluded_transition_documents": corpus.excluded_transition_documents,
        "feature_count": len(feature_names),
        "feature_family_counts": dict(
            sorted(Counter(item["family"] for item in catalog).items())
        ),
        "syntax_annotations_used": resolved_annotations is not None,
        "sparse_features": sparse.summary if sparse is not None else None,
    }
    _write_json(summary_path, summary)

    run_identity = {
        "annotation_manifest_hash": annotation_manifest_hash,
        "config_fingerprint": config.fingerprint,
        "corpus_fingerprint": corpus.corpus_fingerprint,
        "implementation_version": __version__,
    }
    run_id = hashlib.sha256(
        json.dumps(run_identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    artifact_paths: tuple[Path, ...] = (
        config_output_path,
        features_path,
        catalog_path,
        summary_path,
    )
    if sparse is not None:
        artifact_paths += (sparse_catalog_path, sparse_values_path)
    manifest = {
        "annotation_manifest_hash": annotation_manifest_hash,
        "annotation_parser": (
            annotation_manifest["parser"] if annotation_manifest is not None else None
        ),
        "artifact_type": "document-feature-matrix",
        "artifacts": {path.name: _sha256_file(path) for path in sorted(artifact_paths)},
        "config_fingerprint": config.fingerprint,
        "corpus_fingerprint": corpus.corpus_fingerprint,
        "document_count": len(corpus.documents),
        "feature_names": feature_names,
        "sparse_feature_count": len(sparse.catalog) if sparse is not None else 0,
        "implementation_version": __version__,
        "python_version": platform.python_version(),
        "run_id": run_id,
        "schema_version": "deaiodorant-feature-matrix-1.0",
    }
    _write_json(manifest_path, manifest)
    return manifest
