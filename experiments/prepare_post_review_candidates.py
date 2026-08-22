"""Normalize and deduplicate post acquisition staging for model review."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from deaiodorant.corpus.benchmark import (
    ExclusionIndex,
    file_sha256,
    read_jsonl,
    write_jsonl,
)
from deaiodorant.corpus.benchmark import REVIEW_FIELDS
from pilot_collect import POST_START, strong_original_evidence


PROTOCOL_VERSION = "post-review-candidate-preparation-1.0"


def materialized_record(record: dict[str, object], index_path: Path) -> dict[str, object] | None:
    """Load text for an exclusion-index record when it is stored separately."""

    if isinstance(record.get("text"), str):
        return record
    body_value = record.get("body_path")
    if not isinstance(body_value, str) or not body_value:
        return None
    body_path = Path(body_value)
    if not body_path.is_absolute():
        body_path = index_path.parent / body_path
    if not body_path.is_file():
        return None
    item = dict(record)
    item["text"] = body_path.read_text(encoding="utf-8").rstrip("\n")
    return item


def tracked_pilot_records(repository_root: Path) -> list[dict[str, object]]:
    """Materialize the tracked pilot for cross-version duplicate rejection."""

    output: list[dict[str, object]] = []
    for meta_path in sorted((repository_root / "data/pilot/monthly").glob("*/meta.jsonl")):
        for record in read_jsonl(meta_path):
            text_name = str(record.get("text_file") or f"{record['doc_id']}.txt")
            text_path = meta_path.parent / text_name
            if not text_path.is_file():
                continue
            output.append(
                {
                    "doc_id": record["doc_id"],
                    "url": record["url"],
                    "text": text_path.read_text(encoding="utf-8").rstrip("\n"),
                }
            )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare fresh post candidates for fail-closed model review."
    )
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--exclude-index", type=Path, action="append", default=[])
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repository_root = args.repository_root.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    exclusion = ExclusionIndex()
    for record in tracked_pilot_records(repository_root):
        exclusion.add(record)
    exclusion_inputs: list[dict[str, object]] = []
    for path in args.exclude_index:
        resolved = path.resolve()
        for record in read_jsonl(resolved):
            item = materialized_record(record, resolved)
            if item is not None:
                exclusion.add(item)
        exclusion_inputs.append(
            {"path": str(resolved), "sha256": file_sha256(resolved)}
        )

    prepared_by_source: dict[str, list[dict[str, object]]] = defaultdict(list)
    exclusions: list[dict[str, object]] = []
    input_rows = 0
    for input_path in args.input:
        resolved = input_path.resolve()
        for record in read_jsonl(resolved):
            input_rows += 1
            reason: str | None = None
            try:
                published = dt.date.fromisoformat(str(record.get("published_at")))
            except ValueError:
                published = None
            if published is None or published < POST_START:
                reason = "outside_post_period"
            elif record.get("quality_pass") is not True:
                reason = "deterministic_quality_gate"
            elif record.get("is_translation") is not False:
                reason = "deterministic_translation_evidence"
            elif not isinstance(record.get("text"), str) or not record["text"].strip():
                reason = "missing_text"
            else:
                duplicate = exclusion.match(record)
                if duplicate is not None:
                    reason = f"duplicate_{duplicate.reason}:{duplicate.existing_doc_id}"
            if reason is not None:
                exclusions.append(
                    {
                        "doc_id": record.get("doc_id"),
                        "source": record.get("source"),
                        "reason": reason,
                    }
                )
                continue
            exclusion.add(record)
            item = dict(record)
            evidence = strong_original_evidence(item)
            item["candidate_label"] = "original_pending_review"
            item["label_evidence"] = evidence or [
                "post_candidate_pending_model_review"
            ]
            prepared_by_source[str(item["source"])].append(item)

    candidate_files: list[dict[str, object]] = []
    for source, records in sorted(prepared_by_source.items()):
        path = output_dir / f"{source}_candidates.jsonl"
        write_jsonl(path, records)
        candidate_files.append(
            {
                "source": source,
                "path": str(path),
                "sha256": file_sha256(path),
                "documents": len(records),
            }
        )
    exclusions_path = output_dir / "exclusions.jsonl"
    write_jsonl(exclusions_path, exclusions)
    decisions_path = output_dir / "no_human_decisions.csv"
    with decisions_path.open("w", encoding="utf-8-sig", newline="") as handle:
        csv.DictWriter(handle, fieldnames=REVIEW_FIELDS).writeheader()

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "pending_model_review",
        "post_start": POST_START.isoformat(),
        "input_files": [
            {"path": str(path.resolve()), "sha256": file_sha256(path.resolve())}
            for path in args.input
        ],
        "exclusion_indexes": exclusion_inputs,
        "tracked_pilot_exclusion_documents": len(
            tracked_pilot_records(repository_root)
        ),
        "input_documents": input_rows,
        "prepared_documents": sum(len(rows) for rows in prepared_by_source.values()),
        "prepared_by_source": {
            source: len(rows) for source, rows in sorted(prepared_by_source.items())
        },
        "exclusion_counts": dict(
            sorted(Counter(str(item["reason"]).split(":", 1)[0] for item in exclusions).items())
        ),
        "candidate_files": candidate_files,
        "exclusions_file": {
            "path": str(exclusions_path),
            "sha256": file_sha256(exclusions_path),
        },
        "empty_human_decisions": {
            "path": str(decisions_path),
            "sha256": file_sha256(decisions_path),
        },
        "restriction": (
            "Prepared records remain acquisition staging. Model review is a "
            "measurement and only high-confidence original routing may continue."
        ),
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
