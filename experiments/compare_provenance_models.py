"""Compare two provenance measurements and build a fail-closed intersection."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


STATUSES = (
    "model_assisted_original",
    "model_assisted_exclusion",
    "uncertain",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left-results", type=Path, required=True)
    parser.add_argument("--left-manifest", type=Path, required=True)
    parser.add_argument("--right-results", type=Path, required=True)
    parser.add_argument("--right-manifest", type=Path, required=True)
    parser.add_argument("--ranking-snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    left_manifest = json.loads(args.left_manifest.read_text(encoding="utf-8"))
    right_manifest = json.loads(args.right_manifest.read_text(encoding="utf-8"))
    left_rows = {row["doc_id"]: row for row in _read_jsonl(args.left_results)}
    right_rows = {row["doc_id"]: row for row in _read_jsonl(args.right_results)}
    if left_rows.keys() != right_rows.keys():
        raise ValueError("Model result document identities differ")

    matrix: Counter[tuple[str, str]] = Counter()
    source_matrix: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    consensus_rows: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for doc_id in sorted(left_rows):
        left = left_rows[doc_id]
        right = right_rows[doc_id]
        left_status = str(left["triage_status"])
        right_status = str(right["triage_status"])
        if left_status not in STATUSES or right_status not in STATUSES:
            raise ValueError(f"Unsupported triage status for {doc_id}")
        pair = (left_status, right_status)
        matrix[pair] += 1
        source_matrix[str(left["source"])][pair] += 1
        agreed_original = pair == (
            "model_assisted_original",
            "model_assisted_original",
        )
        consensus_rows.append(
            {
                "doc_id": doc_id,
                "source": left["source"],
                "published_at": left["published_at"],
                "title": left["title"],
                "url": left["url"],
                "triage_status": (
                    "model_assisted_original" if agreed_original else "uncertain"
                ),
                "provenance": "two_model_intersection_measurement",
                "left_model": left_manifest["model"],
                "left_status": left_status,
                "right_model": right_manifest["model"],
                "right_status": right_status,
            }
        )
        if left_status != right_status:
            disagreements.append(consensus_rows[-1])

    total = len(consensus_rows)
    exact_agreement = sum(
        count for (left, right), count in matrix.items() if left == right
    )
    agreed_original_count = sum(
        row["triage_status"] == "model_assisted_original"
        for row in consensus_rows
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    consensus_path = output_dir / "consensus_provenance.jsonl"
    disagreements_path = output_dir / "disagreements.jsonl"
    _write_jsonl(consensus_path, consensus_rows)
    _write_jsonl(disagreements_path, disagreements)

    def serialized(counter: Counter[tuple[str, str]]) -> dict[str, int]:
        return {
            f"{left}|{right}": counter[(left, right)]
            for left in STATUSES
            for right in STATUSES
            if counter[(left, right)]
        }

    comparison = {
        "schema_version": "deaiodorant-provenance-model-comparison-1.0",
        "decision_policy": (
            "Only documents that both current models classify as high-confidence "
            "original continue. Every disagreement and uncertainty fails closed."
        ),
        "left_model": left_manifest["model"],
        "right_model": right_manifest["model"],
        "documents": total,
        "exact_status_agreement": exact_agreement,
        "exact_status_agreement_rate": exact_agreement / total if total else 0.0,
        "consensus_original": agreed_original_count,
        "disagreements": len(disagreements),
        "status_matrix": serialized(matrix),
        "source_status_matrices": {
            source: serialized(counter)
            for source, counter in sorted(source_matrix.items())
        },
        "identity": {
            "left_results_sha256": _sha256(args.left_results),
            "left_manifest_sha256": _sha256(args.left_manifest),
            "right_results_sha256": _sha256(args.right_results),
            "right_manifest_sha256": _sha256(args.right_manifest),
            "ranking_snapshot_sha256": _sha256(args.ranking_snapshot),
        },
        "artifacts": {
            "consensus_provenance": str(consensus_path),
            "consensus_provenance_sha256": _sha256(consensus_path),
            "disagreements": str(disagreements_path),
            "disagreements_sha256": _sha256(disagreements_path),
        },
        "restriction": (
            "Both inputs are model-assisted measurements, not human gold. Agreement "
            "supports conservative routing only and does not establish accuracy."
        ),
    }
    (output_dir / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(comparison, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
