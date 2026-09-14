"""Retain translated media and report provenance-stratified cue diagnostics."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ershi_cohort_statistics import digest, load_articles, summarize
from deaiodorant.refine.records import load_jsonl, write_json

VERSION = "provenance-stratified-contrast-1.0"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to((ROOT / "feature_runs").resolve())
    if output.exists():
        raise ValueError("Use a new result directory")
    path = ROOT / "data/local/contrast-context-v1/provenance-addendum.json"
    audit = json.loads(path.read_text(encoding="utf-8"))
    articles, input_hashes, _ = load_articles()
    bodies = {r["doc_id"]: r for r in articles}
    source = ROOT / "feature_runs/ershi-cohort-v1"
    prior = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    count_path = source / "document_counts.jsonl"
    if digest(count_path) != prior["output_hashes"][count_path.name]:
        raise ValueError("Prior count artifact changed")
    for name, expected in prior["input_hashes"].items():
        if input_hashes.get(name) != expected:
            raise ValueError("Prior source identity changed")
    expected_ids = {r["doc_id"] for r in articles if r["source"] == "infoq"
                    and r["cohort"] in ("pre", "post") and not r["known_translation"]}
    audited_ids = [r["doc_id"] for r in audit["documents"]]
    if len(set(audited_ids)) != len(audited_ids) or set(audited_ids) != expected_ids:
        raise ValueError("Provenance audit coverage mismatch")
    new_translations = set()
    evidence_count = 0
    for row in audit["documents"]:
        if bodies[row["doc_id"]]["content_hash"] != row["source_body_sha256"]:
            raise ValueError("Provenance audit body mismatch")
        for evidence in row["evidence"]:
            source_path = (ROOT / evidence["source_path"]).resolve()
            source_path.relative_to(ROOT.resolve())
            text = source_path.read_bytes().decode("utf-8")
            if text[evidence["start_char"]:evidence["end_char"]] != evidence["evidence_quote"]:
                raise ValueError("Provenance quotation mismatch")
            input_hashes[source_path.relative_to(ROOT).as_posix()] = digest(source_path)
            evidence_count += 1
        if row["current_provenance_status"] == "confirmed_translation":
            new_translations.add(row["doc_id"])
    rows = []
    for row in load_jsonl(count_path):
        if row["source"] != "infoq" or row["cohort"] not in {"pre", "post"}:
            continue
        parsed = date.fromisoformat(row["published_at"][:10])
        expected_period = "pre" if parsed < date(2023, 1, 1) else "post" if parsed >= date(2025, 7, 1) else "transition"
        if row["cohort"] != expected_period or row["content_hash"] != bodies[row["doc_id"]]["content_hash"]:
            raise ValueError("Source identity or temporal assignment mismatch")
        translated = row["known_translation"] or row["doc_id"] in new_translations
        rows.append({**row, "legacy_known_translation": row["known_translation"],
                     "known_translation": translated,
                     "provenance_stratum": "documented_translation_or_adaptation" if translated else "unresolved",
                     "research_retained": True,
                     "translation_evidence_basis": "new_explicit_body_disclosure" if row["doc_id"] in new_translations
                         else "retained_legacy_evidence" if row["known_translation"] else "no_originality_certification"})
    if len(rows) != 40 or len({r["doc_id"] for r in rows}) != 40:
        raise ValueError("All-media population changed")
    groups = []
    for view in ("all_available_media", "documented_translation_or_adaptation", "unresolved",
                 "legacy_known_translation_filtered_before_addendum"):
        for period in ("pre", "post"):
            selected = [r for r in rows if r["cohort"] == period and (
                view == "all_available_media" or r["provenance_stratum"] == view or
                view == "legacy_known_translation_filtered_before_addendum" and not r["legacy_known_translation"])]
            groups.append({"view": view, "cohort": period, **summarize(selected)})
    result = {"protocol": VERSION, "status": "descriptive_unmatched_available_media",
              "research_documents_retained": len(rows), "new_translation_ids": sorted(new_translations),
              "validated_provenance_quotes": evidence_count, "certified_original_documents": 0,
              "groups": groups,
              "interpretation": ["Translation is a provenance stratum, not a global research rejection.",
                                 "The unresolved stratum is not certified direct-Chinese writing.",
                                 "Original-only intent remains a control, and the old 8.3 ratio is preserved with its earlier incomplete evidence.",
                                 "Counts do not identify inherited versus translation-added defects or authorship.",
                                 "Source/topic/format/visibility matching is incomplete; rates are not causal or population estimates."]}
    output.mkdir(parents=True)
    write_json(output / "document-provenance.json", rows)
    write_json(output / "summary.json", result)
    for name in (path, count_path, source / "manifest.json"):
        input_hashes[name.relative_to(ROOT).as_posix()] = digest(name)
    for name, expected in input_hashes.items():
        if digest(ROOT / name) != expected:
            raise ValueError("Input changed during reporting")
    write_json(output / "manifest.json", {"protocol": VERSION, "input_hashes": input_hashes,
        "implementation_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in
                                  (Path(__file__), ROOT / "experiments/ershi_cohort_statistics.py")},
        "output_hashes": {p.name: digest(p) for p in output.iterdir() if p.is_file()},
        "command": f"python experiments/provenance_stratified_contrast_statistics.py --output-dir {output.relative_to(ROOT).as_posix()}",
        "external_api_calls": 0, "gpu_used": False})
    print(json.dumps({"documents": len(rows), "provenance_quotes": evidence_count,
                      "groups": [{k: g[k] for k in ("view", "cohort", "documents", "cjk_chars", "ershi_occurrences", "pooled_per_10000_cjk")} for g in groups]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
