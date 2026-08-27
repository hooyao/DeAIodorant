"""Rank fresh post passages by transparent compositional-load signals."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from compositional_burden_probe import (
    FEATURE_DIRECTIONS,
    _parsed_sentences,
    integration_features,
)
from prepare_reader_friction_screen_v3 import collect_passages
from deaiodorant.analysis.stanza_backend import (
    PROCESSORS,
    _configure_determinism,
    _load_stanza,
    _model_fingerprint,
)


SELECTION_FEATURES = (
    "argument_anchored_clause_ratio",
    "content_tokens_per_clause_head",
    "distinct_content_lemmas_per_sentence",
    "function_to_content_ratio",
    "long_dependency_arc_ratio",
    "mean_nominal_modifier_span",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _percentile_ranks(values: list[float]) -> list[float]:
    if len(values) == 1:
        return [0.5]
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        average_index = (cursor + end - 1) / 2
        percentile = average_index / (len(values) - 1)
        for index in order[cursor:end]:
            ranks[index] = percentile
        cursor = end
    return ranks


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _excluded_doc_ids(paths: list[Path]) -> set[str]:
    excluded: set[str] = set()
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        excluded.update(str(item["doc_id"]) for item in payload["pairs"])
    return excluded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument(
        "--exclude-answer-key",
        type=Path,
        action="append",
        default=[],
    )
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--seed", type=int, default=2026082704)
    args = parser.parse_args()

    excluded = _excluded_doc_ids(args.exclude_answer_key)
    passages_by_document, metadata = collect_passages(args.handoff_root.resolve())
    candidates = [
        passage
        for doc_id, passages in passages_by_document.items()
        if doc_id not in excluded
        for passage in passages
    ]
    if not candidates:
        raise ValueError("No unexposed eligible passages remain")

    stanza = _load_stanza()
    torch = _configure_determinism(args.seed, args.device)
    model_fingerprint, model_file_count = _model_fingerprint(
        args.model_dir.resolve(), "zh-hans"
    )
    options: dict[str, Any] = {
        "dir": str(args.model_dir.resolve()),
        "lang": "zh-hans",
        "package": "gsdsimp",
        "processors": PROCESSORS,
        "use_gpu": args.device == "cuda",
        "verbose": False,
    }
    if hasattr(stanza, "DownloadMethod"):
        options["download_method"] = stanza.DownloadMethod.NONE
    nlp = stanza.Pipeline(**options)

    rows: list[dict[str, Any]] = []
    with torch.inference_mode():
        for passage in sorted(
            candidates,
            key=lambda item: (item.doc_id, item.line_number),
        ):
            parsed = _parsed_sentences(nlp(passage.passage))
            record = metadata[passage.doc_id]
            rows.append(
                {
                    "doc_id": passage.doc_id,
                    "source": passage.source,
                    "format": record["format_stratum"],
                    "topic": record["topic_stratum"],
                    "published_at": passage.published_at,
                    "line_number": passage.line_number,
                    "passage_sha256": passage.passage_sha256,
                    "text": passage.passage,
                    **integration_features(passage.passage, parsed),
                }
            )

    strata: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        strata[(str(row["source"]), str(row["format"]))].append(index)
    for indices in strata.values():
        for feature in SELECTION_FEATURES:
            values = [float(rows[index][feature]) for index in indices]
            percentiles = _percentile_ranks(values)
            for index, percentile in zip(indices, percentiles, strict=True):
                burden_percentile = (
                    percentile
                    if FEATURE_DIRECTIONS[feature] == "higher"
                    else 1.0 - percentile
                )
                rows[index][f"burden_percentile__{feature}"] = burden_percentile
        for index in indices:
            rows[index]["top_quartile_signal_count"] = sum(
                float(rows[index][f"burden_percentile__{feature}"]) >= 0.75
                for feature in SELECTION_FEATURES
            )

    shortlist: list[dict[str, Any]] = []
    for stratum, indices in sorted(strata.items()):
        ordered = sorted(
            (rows[index] for index in indices),
            key=lambda row: (
                -int(row["top_quartile_signal_count"]),
                -float(row["burden_percentile__content_tokens_per_clause_head"]),
                -float(row["burden_percentile__distinct_content_lemmas_per_sentence"]),
                str(row["doc_id"]),
                int(row["line_number"]),
            ),
        )
        seen_documents: set[str] = set()
        for row in ordered:
            if str(row["doc_id"]) in seen_documents:
                continue
            seen_documents.add(str(row["doc_id"]))
            shortlist.append(row)
            if len(seen_documents) == 5:
                break

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "passage_features.csv", rows)
    manifest = {
        "artifact_type": "fresh-post-compositional-burden-development-scan",
        "schema_version": "deaiodorant-compositional-burden-scan-0.1",
        "seed": args.seed,
        "candidate_document_count": len({row["doc_id"] for row in rows}),
        "candidate_passage_count": len(rows),
        "excluded_document_count": len(excluded),
        "selection_features": list(SELECTION_FEATURES),
        "selection_rule": (
            "Within each source-format stratum, count putative burden signals "
            "at or above the 75th percentile; retain up to five passages from "
            "distinct documents for manual preservation review."
        ),
        "identity": {
            "handoff_manifest_sha256": _sha256(args.handoff_root / "manifest.json"),
            "handoff_documents_sha256": _sha256(args.handoff_root / "documents.jsonl"),
            "excluded_answer_keys": {
                str(path): _sha256(path) for path in args.exclude_answer_key
            },
            "model_fingerprint": model_fingerprint,
            "model_file_count": model_file_count,
        },
        "shortlist": shortlist,
        "limits": [
            "The top-quartile signal count is a transparent discovery ranking, not a validated burden score.",
            "No reader outcome is used in candidate ranking.",
            "Parser outputs are deterministic measurements with error, not linguistic gold labels.",
            "Shortlisted passages require manual completeness and proposition-preservation review before intervention use.",
        ],
    }
    (args.output_dir / "shortlist.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
