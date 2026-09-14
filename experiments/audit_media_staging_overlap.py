"""Mechanically exclude prior dataset content without exposing benchmark labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from deaiodorant.corpus.benchmark import ExclusionIndex, file_sha256
from deaiodorant.refine.records import append_jsonl, load_jsonl, write_json

VERSION = "media-staging-overlap-audit-1.0"
PRIOR_DATASETS = (
    "data/pilot/pilot_corpus.jsonl",
    "data/smoke/pilot_corpus.jsonl",
    "data/translation_eval/gold.jsonl",
    "data/translation_holdout/gold.jsonl",
    "data/translation_test/gold.jsonl",
    "data/translation_v2/candidates/infoq_candidates.jsonl",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to((ROOT / "data/local").resolve())
    if output.exists():
        raise ValueError("Use a new output directory; do not overwrite an audit")
    output.mkdir(parents=True)
    index = ExclusionIndex(near_duplicate_threshold=0.9)
    source_log = []
    for name in PRIOR_DATASETS:
        path = ROOT / name
        if not path.exists():
            source_log.append({"path": name, "status": "missing"})
            continue
        count = with_text = 0
        before = file_sha256(path)
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                raw = json.loads(line)
                # This is a leakage guard, not benchmark evaluation. Only the
                # existing index's identity/content fields are consumed; labels,
                # scores, decisions, and outcomes never enter any model/report.
                record = {key: raw.get(key) for key in ("doc_id", "url", "canonical_url", "text")}
                count += 1
                if isinstance(record.get("text"), str) and record["text"]:
                    with_text += 1
                    index.add(record)
        if file_sha256(path) != before:
            raise ValueError("A protected input changed during the read-only audit")
        source_log.append({"path": name, "sha256": before, "records": count,
                           "body_indexed": with_text, "missing_body": count - with_text})
        write_json(output / "progress.json", {"stage": "indexing", "source_files_completed": len(source_log)})
        print(json.dumps({"event": "indexed", "path": name, "records": count, "with_body": with_text}), flush=True)
    attempts = load_jsonl(args.staging_root / "article-attempts.jsonl")
    results = []
    within = ExclusionIndex(near_duplicate_threshold=0.9)
    for attempt in attempts:
        item = {"doc_id": attempt["doc_id"], "source_cohort": attempt.get("actual_cohort"),
                "body_available": bool(attempt.get("body_path")), "known_match": None,
                "within_staging_match": None, "inspection_eligible": False}
        path = args.staging_root / "documents" / attempt["doc_id"] / "body.txt"
        if not path.exists():
            item["reason"] = "body_unavailable"
        else:
            text = path.read_bytes().decode("utf-8")
            if hashlib.sha256(text.encode("utf-8")).hexdigest() != attempt["content_hash"]:
                raise ValueError("Staged body hash mismatch")
            if not text.strip():
                item["reason"] = "empty_extraction"
            else:
                record = {"doc_id": item["doc_id"], "url": attempt["url"], "text": text}
                match = index.match(record)
                internal = within.match(record)
                if match:
                    item["known_match"] = {"reason": match.reason, "existing_doc_id": match.existing_doc_id}
                if internal:
                    item["within_staging_match"] = {"reason": internal.reason, "existing_doc_id": internal.existing_doc_id}
                within.add(record)
                explicit_exclusion = bool(attempt.get("exclusions_found"))
                item["prior_exclusions"] = attempt.get("exclusions_found", [])
                item["inspection_eligible"] = not match and not internal and not explicit_exclusion
                item["reason"] = "inspection_only_not_admitted" if item["inspection_eligible"] else "exclusion_or_overlap"
        results.append(item)
        append_jsonl(output / "results.jsonl", item)
    report = {"version": VERSION, "source_datasets": source_log,
              "staging_attempts_sha256": file_sha256(args.staging_root / "article-attempts.jsonl"),
              "candidates": len(results), "inspection_eligible": sum(r["inspection_eligible"] for r in results),
              "known_overlap_count": sum(r["known_match"] is not None for r in results),
              "internal_overlap_count": sum(r["within_staging_match"] is not None for r in results),
              "admitted_documents": 0, "human_smell_labels": 0,
              "method": "Existing exact/normalized/simhash-prefiltered shingle guard at fixed threshold0.9; not a guarantee of semantic non-overlap.",
              "privacy": "No benchmark body, label, score, or outcome is emitted or used for prompt/rule tuning."}
    write_json(output / "summary.json", report)
    write_json(output / "progress.json", {"stage": "complete", "candidates": len(results)})
    print(json.dumps({key: value for key, value in report.items() if key != "source_datasets"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
