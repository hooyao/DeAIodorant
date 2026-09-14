"""Count the reader-nominated contrast family in available real-media cohorts."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from deaiodorant.analysis.reading_burden import analyze_sentences
from deaiodorant.refine.records import append_jsonl, load_jsonl, write_json

VERSION = "ershi-cohort-statistics-1.0"
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
KNOWN_TRANSLATED_PILOT = {"b186cdd4f9004e0413395bf3"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cohort(date: str) -> str:
    if date[:10] < "2023-01-01":
        return "pre"
    if date[:10] >= "2025-07-01":
        return "post"
    return "transition"


def load_articles() -> tuple[list[dict], dict[str, str], list[dict]]:
    files = {}
    rows = []
    exclusions = []
    pilot = ROOT / "data/pilot/pilot_corpus.jsonl"
    files[pilot.relative_to(ROOT).as_posix()] = digest(pilot)
    for record in load_jsonl(pilot):
        text = record["text"]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != record["content_hash"]:
            raise ValueError("Pilot content hash mismatch")
        rows.append({"doc_id": record["doc_id"], "source": record["source"], "dataset": "pilot",
                     "title": record["title"], "url": record["url"], "published_at": record["published_at"],
                     "text": text, "content_hash": record["content_hash"],
                     "known_translation": bool(record.get("is_translation")) or record["doc_id"] in KNOWN_TRANSLATED_PILOT,
                     "translation_evidence": record.get("translation_evidence", []),
                     "admission_status": "diagnostic_pilot_not_clean_corpus"})
    stage = ROOT / "data/local/media-contrast-staging-v1"
    path = stage / "article-attempts.jsonl"
    files[path.relative_to(ROOT).as_posix()] = digest(path)
    for attempt in load_jsonl(path):
        body = stage / "documents" / attempt["doc_id"] / "body.txt"
        if not body.exists():
            exclusions.append({"doc_id": attempt["doc_id"], "reason": "body_unavailable"})
            continue
        text = body.read_bytes().decode("utf-8")
        files[body.relative_to(ROOT).as_posix()] = digest(body)
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != attempt["content_hash"]:
            raise ValueError("Staged content hash mismatch")
        if not text.strip():
            exclusions.append({"doc_id": attempt["doc_id"], "reason": "empty_body"})
            continue
        record = attempt["metadata"]
        rows.append({"doc_id": record["doc_id"], "source": record["source"], "dataset": "staging",
                     "title": record["title"], "url": record["url"], "published_at": record["published_at"],
                     "text": text, "content_hash": attempt["content_hash"],
                     "known_translation": bool(record.get("is_translation")) or "deterministic_translation_evidence" in attempt.get("exclusions_found", []),
                     "translation_evidence": record.get("translation_evidence", []),
                     "admission_status": "unreviewed_staging_not_admitted"})
    seen_ids, seen_urls, seen_content = set(), set(), set()
    unique = []
    for row in rows:
        normalized = re.sub(r"\s+", "", row["text"]).casefold()
        key = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        reason = ("duplicate_id" if row["doc_id"] in seen_ids else
                  "duplicate_url" if row["url"] in seen_urls else
                  "duplicate_normalized_body" if key in seen_content else None)
        if reason:
            exclusions.append({"doc_id": row["doc_id"], "reason": reason})
            continue
        seen_ids.add(row["doc_id"]); seen_urls.add(row["url"]); seen_content.add(key)
        row["cohort"] = cohort(row["published_at"])
        unique.append(row)
    return unique, files, exclusions


def summarize(rows: list[dict]) -> dict:
    total = sum(r["ershi_count"] for r in rows)
    cjk = sum(r["cjk_chars"] for r in rows)
    counts = [r["ershi_count"] for r in rows]
    rates = [r["ershi_per_10000_cjk"] for r in rows if r["ershi_per_10000_cjk"] is not None]
    positive = [value for value in counts if value]
    prefixes, families = Counter(), Counter()
    for row in rows:
        prefixes.update(row["counts_by_left_prefix"])
        families.update(row["counts_by_family"])
    return {
        "documents": len(rows), "cjk_chars": cjk, "ershi_occurrences": total,
        "pooled_per_10000_cjk": total * 10000 / cjk if cjk else None,
        "documents_with_ershi": len(positive),
        "document_coverage": len(positive) / len(rows) if rows else None,
        "mean_per_document": statistics.fmean(counts) if counts else None,
        "median_per_document": statistics.median(counts) if counts else None,
        "median_per_positive_document": statistics.median(positive) if positive else None,
        "mean_document_rate_per_10000_cjk": statistics.fmean(rates) if rates else None,
        "median_document_rate_per_10000_cjk": statistics.median(rates) if rates else None,
        "count_histogram": dict(sorted(Counter(counts).items())),
        "counts_by_left_prefix": dict(sorted(prefixes.items())),
        "counts_by_family": dict(sorted(families.items())),
        "known_translation_documents": sum(r["known_translation"] for r in rows),
        "title_ershi_occurrences": sum(r["title_ershi_count"] for r in rows),
        "publication_year_counts": dict(sorted(Counter(r["published_at"][:4] for r in rows).items())),
        "top_contributors": [{"doc_id": r["doc_id"], "dataset": r["dataset"], "published_at": r["published_at"],
                               "count": r["ershi_count"], "per_10000_cjk": r["ershi_per_10000_cjk"]}
                              for r in sorted(rows, key=lambda r: (-r["ershi_count"], r["doc_id"]))[:5]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to((ROOT / "feature_runs").resolve())
    if output.exists():
        raise ValueError("Use a new output directory; do not overwrite a result")
    articles, input_hashes, exclusions = load_articles()
    output.mkdir(parents=True)
    measured = []
    for row in articles:
        text = row.pop("text")
        analysis = analyze_sentences([{"sentence_id": row["doc_id"], "block_id": "whole_body",
                                       "block_tag": "article_body", "text": text}])
        cue = analysis["style_cues"]
        if cue["literal_ershi"]["count"] != text.count("而是"):
            raise ValueError("Literal count disagreement")
        cjk = len(CJK.findall(text))
        result = {**row, "cjk_chars": cjk, "ershi_count": text.count("而是"),
                  "ershi_per_10000_cjk": text.count("而是") * 10000 / cjk if cjk else None,
                  "title_ershi_count": str(row["title"]).count("而是"),
                  "counts_by_left_prefix": cue["counts_by_left_prefix"],
                  "counts_by_family": cue["counts_by_family"],
                  "negative_alternatives": cue["negative_alternative_connectors"]["counts_by_literal"]}
        measured.append(result)
        append_jsonl(output / "document_counts.jsonl", result)
        for event in cue["replacement_frame_instances"]:
            append_jsonl(output / "instances.jsonl", {"doc_id": row["doc_id"], "cohort": row["cohort"], **event})
    groups = []
    for source in sorted({r["source"] for r in measured}):
        for dataset in ("combined", "pilot", "staging"):
            for exclude in (False, True):
                for minimum in (0, 1000):
                    for period in ("pre", "post", "transition"):
                        selected = [r for r in measured if r["source"] == source and r["cohort"] == period
                                    and (dataset == "combined" or r["dataset"] == dataset)
                                    and (not exclude or not r["known_translation"])
                                    and r["cjk_chars"] >= minimum]
                        if not selected:
                            continue
                        groups.append({"source": source, "dataset": dataset,
                                       "exclude_known_translations": exclude, "minimum_cjk": minimum,
                                       "cohort": period, **summarize(selected)})
    summary = {"protocol": VERSION, "status": "descriptive_available_corpus_not_validation",
               "cohort_boundaries": {"pre_end_exclusive": "2023-01-01", "post_start_inclusive": "2025-07-01"},
               "measurement": "literal body occurrences of 而是; lexical variant categories are secondary heuristics",
               "groups": groups, "exclusions": exclusions,
               "limitations": ["Unmatched small datasets; pilot selection differs from seeded sitemap staging.",
                               "Known-translation exclusion does not establish that every retained article is original or high quality.",
                               "Quoted material and article-body headings remain counted; titles are separate.",
                               "Frequency differences do not establish authorship, reader harm, or a safe rewrite rule.",
                               "No primary temporal comparison pools Machine Heart with InfoQ."]}
    write_json(output / "summary.json", summary)
    columns = ["doc_id", "source", "dataset", "cohort", "published_at", "title", "url", "cjk_chars",
               "ershi_count", "ershi_per_10000_cjk", "known_translation", "title_ershi_count", "admission_status"]
    with (output / "document_counts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(measured)
    for name, expected in input_hashes.items():
        if digest(ROOT / name) != expected:
            raise ValueError("An input changed during measurement")
    files = (Path(__file__), ROOT / "src/deaiodorant/analysis/reading_burden.py",
             ROOT / "docs/routes/compact-refiner/ershi-cohort-statistics.md")
    write_json(output / "manifest.json", {
        "protocol": VERSION, "python": platform.python_version(), "input_hashes": input_hashes,
        "implementation_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in files},
        "output_hashes": {p.name: digest(p) for p in output.iterdir() if p.is_file()},
        "external_model_calls": 0, "gpu_used": False,
        "command": f"python experiments/ershi_cohort_statistics.py --output-dir {output.relative_to(ROOT).as_posix()}",
    })
    for group in groups:
        if group["source"] == "infoq" and group["dataset"] == "combined" and group["exclude_known_translations"] and group["minimum_cjk"] == 0:
            print(json.dumps(group, ensure_ascii=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
