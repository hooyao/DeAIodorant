"""Prepare exact-body packets and concentration diagnostics for context review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ershi_cohort_statistics import CJK, digest, load_articles
from deaiodorant.refine.records import load_jsonl, write_json

VERSION = "contrast-context-audit-1.0"
SEED = 20260914


def concentration(text: str, width: int) -> dict:
    """Return the densest observed connector-start span in CJK coordinates."""
    if width <= 0:
        raise ValueError("Window width must be positive")
    starts = [m.start() for m in re.finditer("而是", text)]
    cjk_prefix = [0]
    for char in text:
        cjk_prefix.append(cjk_prefix[-1] + bool(CJK.fullmatch(char)))
    positions = [cjk_prefix[start] for start in starts]
    best_left = best_right = left = 0
    for right, position in enumerate(positions):
        while position - positions[left] >= width:
            left += 1
        if right - left + 1 > best_right - best_left:
            best_left, best_right = left, right + 1
    selected = starts[best_left:best_right]
    return {
        "window_cjk": width, "max_occurrences": len(selected),
        "body_shorter_than_window": cjk_prefix[-1] < width,
        "connector_start_chars": selected,
        "connector_start_cjk": positions[best_left:best_right],
    }


def context_span(text: str, start: int, end: int) -> dict:
    """Locate a punctuation-delimited navigation unit, retaining exact text."""
    terminators = "。！？!?"
    left = max(text.rfind(mark, 0, start) + 1 for mark in terminators)
    after = [text.find(mark, end) for mark in terminators]
    right = min((position + 1 for position in after if position >= 0), default=len(text))
    return {"start_char": left, "end_char": right, "text": text[left:right]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to((ROOT / "data/local").resolve())
    if output.exists():
        raise ValueError("Use a new output directory")
    articles, hashes, exclusions = load_articles()
    previous = ROOT / "feature_runs/ershi-cohort-v1"
    counts = {r["doc_id"]: r for r in load_jsonl(previous / "document_counts.jsonl")}
    events = load_jsonl(previous / "instances.jsonl")
    for name in ("document_counts.jsonl", "instances.jsonl", "manifest.json"):
        path = previous / name
        hashes[path.relative_to(ROOT).as_posix()] = digest(path)
    old_manifest = json.loads((previous / "manifest.json").read_text(encoding="utf-8"))
    for name in ("document_counts.jsonl", "instances.jsonl"):
        if digest(previous / name) != old_manifest["output_hashes"][name]:
            raise ValueError("Previous count artifact hash mismatch")
    for name, expected in old_manifest["input_hashes"].items():
        if hashes.get(name) != expected:
            raise ValueError("Source identity changed since the previous count run")
    retained = [r for r in articles if r["source"] == "infoq"
                and r["cohort"] in ("pre", "post") and not r["known_translation"]]
    positive = sorted([r for r in retained if "而是" in r["text"]], key=lambda r: r["doc_id"])
    random.Random(SEED).shuffle(positive)
    if len(retained) != 35 or len(positive) != 13 or sum(r["text"].count("而是") for r in positive) != 57:
        raise ValueError("Frozen audit population changed")
    output.mkdir(parents=True)
    mapping = []
    metrics = []
    for row in retained:
        old = counts[row["doc_id"]]
        if old["content_hash"] != row["content_hash"] or old["ershi_count"] != row["text"].count("而是"):
            raise ValueError("Body identity or count mismatch")
        metrics.append({"doc_id": row["doc_id"], "cohort": row["cohort"],
                        "content_hash": row["content_hash"], "cjk_chars": len(CJK.findall(row["text"])),
                        "ershi_count": old["ershi_count"],
                        "concentration": [concentration(row["text"], width) for width in (500, 1000)]})
    for index, row in enumerate(positive, 1):
        alias = f"doc-{index:02d}"
        directory = output / "packets" / alias
        directory.mkdir(parents=True)
        (directory / "body.txt").write_bytes(row["text"].encode("utf-8"))
        body_events = sorted([e for e in events if e["doc_id"] == row["doc_id"]], key=lambda e: e["connector"]["start_char"])
        expected_spans = [(match.start(), match.end()) for match in re.finditer("而是", row["text"])]
        actual_spans = [(event["connector"]["start_char"], event["connector"]["end_char"]) for event in body_events]
        if actual_spans != expected_spans:
            raise ValueError("Occurrence coverage mismatch")
        packet_events = []
        for ordinal, event in enumerate(body_events, 1):
            connector = event["connector"]
            if row["text"][connector["start_char"]:connector["end_char"]] != "而是":
                raise ValueError("Connector offset mismatch")
            packet_events.append({"occurrence_id": f"{alias}-e{ordinal:02d}", "connector": connector,
                                  "mechanical_context": context_span(row["text"], connector["start_char"], connector["end_char"])})
        write_json(directory / "occurrences.json", {"alias": alias, "content_hash": row["content_hash"], "occurrences": packet_events})
        mapping.append({key: row[key] for key in ("doc_id", "cohort", "dataset", "title", "url", "published_at", "content_hash", "admission_status")} | {"alias": alias})
    write_json(output / "identity-map.json", mapping)
    write_json(output / "document-metrics.json", metrics)
    write_json(output / "scope.json", {"protocol": VERSION, "all_documents": 35, "review_documents": 13,
                                      "occurrences": 57, "human_gold": False,
                                      "metadata_masking": "Metadata only; article content can reveal time and genre.",
                                      "zero_count_documents": 22, "acquisition_exclusions": exclusions})
    for name, expected in hashes.items():
        if digest(ROOT / name) != expected:
            raise ValueError("An input changed during packet preparation")
    implementation = [Path(__file__), ROOT / "docs/routes/compact-refiner/contrast-context-audit.md",
                      ROOT / "experiments/ershi_cohort_statistics.py"]
    write_json(output / "manifest.json", {"protocol": VERSION, "seed": SEED, "python": platform.python_version(),
                "command": f"python experiments/contrast_context_audit.py --output-dir {output.relative_to(ROOT).as_posix()}",
                "input_hashes": hashes, "implementation_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in implementation},
                "output_hashes": {p.relative_to(output).as_posix(): digest(p) for p in output.rglob("*") if p.is_file()},
                "external_api_calls": 0, "gpu_used": False})
    print(json.dumps({"protocol": VERSION, "documents": 35, "review_documents": 13, "occurrences": 57}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
