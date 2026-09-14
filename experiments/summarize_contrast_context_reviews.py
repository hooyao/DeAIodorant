"""Validate exact-source review evidence and report assistant consistency."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ershi_cohort_statistics import digest
from deaiodorant.refine.records import write_json

VERSION = "contrast-context-review-validation-1.0"
RELATIONS = {"correction", "scope_extension", "temporal_change", "procedural_alternative",
             "evaluative_reframing", "unclear_or_malformed", "mixed"}
VOICES = {"reporter", "attributed_quote_or_paraphrase", "mixed", "uncertain"}
PACKAGING = {"ordinary", "repetition_candidate", "uncertain"}
CONFIDENCES = {"high", "medium", "low"}
KINDS = {"argument_or_reference", "relation_or_support", "attachment_or_density",
         "lexical_or_translationese", "possible_capture_issue", "other"}
REPAIRS = {"local_reexpression", "article_supported", "requires_missing_information", "uncertain"}


def quote_spans(text: str, quote: str, anchor: tuple[int, int] | None = None) -> list[dict]:
    """Resolve exact quotes, retaining repeated matches and requiring an anchor."""
    if not isinstance(quote, str) or not quote:
        raise ValueError("Evidence must be a nonempty exact source string")
    spans = []
    cursor = 0
    while (start := text.find(quote, cursor)) >= 0:
        end = start + len(quote)
        if anchor is None or start <= anchor[0] < anchor[1] <= end:
            spans.append({"start_char": start, "end_char": end})
        cursor = start + 1
    if not spans:
        raise ValueError("Evidence does not match the source at the required location")
    return spans


def required_text(record: dict, fields: tuple[str, ...]) -> None:
    for field in fields:
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"Missing nonempty review field: {field}")


def validate_review(review: dict, packets: dict) -> dict:
    if review.get("human_gold") is not False:
        raise ValueError("Assistant review cannot be human gold")
    required_text(review, ("reviewer",))
    documents = review["documents"]
    aliases = [d["alias"] for d in documents]
    if len(aliases) != len(set(aliases)) or set(aliases) != set(packets):
        raise ValueError("Document coverage mismatch")
    resolved = []
    total = defects = counterexamples = 0
    for document in documents:
        alias = document["alias"]
        packet = packets[alias]
        text = packet["text"]
        if document.get("whole_body_read") is not True:
            raise ValueError("Full-body review is not attested")
        required_text(document, ("genre_observation", "document_note"))
        expected = {e["occurrence_id"]: e for e in packet["occurrences"]}
        observed = [e["occurrence_id"] for e in document["occurrences"]]
        if len(observed) != len(set(observed)) or set(observed) != set(expected):
            raise ValueError("Occurrence coverage mismatch")
        for occurrence in document["occurrences"]:
            required_text(occurrence, ("contrast_contribution", "packaging_reason", "preservation_risk"))
            for field, allowed in (("relation", RELATIONS), ("voice", VOICES),
                                   ("packaging", PACKAGING), ("confidence", CONFIDENCES)):
                if occurrence.get(field) not in allowed:
                    raise ValueError(f"Unknown review category: {field}")
            connector = expected[occurrence["occurrence_id"]]["connector"]
            spans = quote_spans(text, occurrence["evidence_quote"], (connector["start_char"], connector["end_char"]))
            resolved.append({"alias": alias, "record_type": "occurrence", "record_id": occurrence["occurrence_id"], "spans": spans})
            total += 1
        defect_ids = [d["defect_id"] for d in document["reading_defects"]]
        if len(defect_ids) != len(set(defect_ids)):
            raise ValueError("Duplicate localized defect ID")
        for defect in document["reading_defects"]:
            required_text(defect, ("defect_id", "explanation"))
            if defect.get("kind") not in KINDS or defect.get("repairability") not in REPAIRS or defect.get("confidence") not in CONFIDENCES:
                raise ValueError("Unknown localized-defect category")
            spans = quote_spans(text, defect["evidence_quote"])
            support = [quote_spans(text, quote) for quote in defect["support_quotes"]]
            resolved.append({"alias": alias, "record_type": "reading_defect", "record_id": defect["defect_id"], "spans": spans, "support_spans": support})
            defects += 1
        for index, counterexample in enumerate(document["counterexamples"], 1):
            required_text(counterexample, ("explanation",))
            spans = quote_spans(text, counterexample["evidence_quote"])
            resolved.append({"alias": alias, "record_type": "counterexample", "record_id": index, "spans": spans})
            counterexamples += 1
    return {"reviewer": review["reviewer"], "model_identity": review.get("model_identity", "unknown"),
            "human_gold": False, "full_body_review_attested_not_independently_provable": True,
            "documents": len(documents), "occurrences": total, "localized_defect_proposals": defects,
            "counterexamples": counterexamples, "resolved_evidence": resolved}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source, output = args.input_dir.resolve(), args.output_dir.resolve()
    source.relative_to((ROOT / "data/local").resolve())
    output.relative_to((ROOT / "data/local").resolve())
    if output.exists():
        raise ValueError("Use a new summary directory")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["output_hashes"].items():
        if digest(source / name) != expected:
            raise ValueError("Prepared input artifact changed")
    packets = {}
    for path in sorted((source / "packets").glob("doc-*/occurrences.json")):
        packet = json.loads(path.read_text(encoding="utf-8"))
        text = (path.parent / "body.txt").read_bytes().decode("utf-8")
        packets[packet["alias"]] = {**packet, "text": text}
    mapping = {r["alias"]: r for r in json.loads((source / "identity-map.json").read_text(encoding="utf-8"))}
    raw, validated, review_hashes = {}, {}, {}
    for name in ("a", "b"):
        path = source / f"review-{name}.json"
        review_hashes[path.name] = digest(path)
        raw[name] = json.loads(path.read_text(encoding="utf-8"))
        validated[name] = validate_review(raw[name], packets)
    comparisons = []
    by_reviewer = {}
    for name, review in raw.items():
        by_reviewer[name] = {e["occurrence_id"]: {**e, "alias": d["alias"]}
                             for d in review["documents"] for e in d["occurrences"]}
    for key, left in sorted(by_reviewer["a"].items()):
        right = by_reviewer["b"][key]
        comparisons.append({"occurrence_id": key, "alias": left["alias"],
            "cohort": mapping[left["alias"]]["cohort"],
            **{field: {"a": left[field], "b": right[field], "agree": left[field] == right[field]}
               for field in ("relation", "voice", "packaging")}})
    summary = {"protocol": VERSION, "status": "assistant_consistency_and_exact_source_validation_only",
               "human_gold": False, "occurrences": len(comparisons),
               "review_coverage": {name: {k: v for k, v in value.items() if k != "resolved_evidence"} for name, value in validated.items()},
               "agreement": {field: {"agree": sum(r[field]["agree"] for r in comparisons), "total": len(comparisons)}
                             for field in ("relation", "voice", "packaging")},
               "reviewer_category_counts": {name: {field: dict(sorted(Counter(e[field] for e in values.values()).items()))
                                                    for field in ("relation", "voice", "packaging")}
                                             for name, values in by_reviewer.items()},
               "comparisons": comparisons,
               "limitations": ["All semantic judgments are assistant proposals, not reader labels or measured reading harm.",
                               "Positive-count documents were selected by the nominated cue; no population prevalence follows.",
                               "Reviewers share a model family; agreement is not independent human validation.",
                               "Exact quotes establish source linkage, not correctness of interpretation.",
                               "Metadata masking cannot conceal dates or genres revealed inside articles."]}
    output.mkdir(parents=True)
    for name, value in validated.items():
        write_json(output / f"validated-review-{name}.json", value)
    write_json(output / "summary.json", summary)
    write_json(output / "manifest.json", {"protocol": VERSION,
        "input_manifest_hash": digest(source / "manifest.json"), "review_hashes": review_hashes,
        "implementation_hash": digest(Path(__file__)),
        "command": f"python experiments/summarize_contrast_context_reviews.py --input-dir {source.relative_to(ROOT).as_posix()} --output-dir {output.relative_to(ROOT).as_posix()}",
        "output_hashes": {p.name: digest(p) for p in output.iterdir() if p.is_file()}})
    print(json.dumps({"occurrences": len(comparisons), "agreement": summary["agreement"], "human_gold": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
