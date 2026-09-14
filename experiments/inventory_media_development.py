"""Inventory existing pilot exports and exposed reader records without rewriting them.

This offline preparation tool neither admits a clean corpus nor evaluates authorship.
It reads only the monthly pilot export, persisted annotations, and two named prior
evidence files. Bodies are measured and hashed but never rendered or copied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "deaiodorant-media-development-inventory-1.0"
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
KNOWN_TRANSLATION_ID = "b186cdd4f9004e0413395bf3"
HISTORICAL_READER_UNEXPOSED_ID = "084c17f921cc74b858d04cdb"
PRIOR_EVIDENCE_PATHS = (
    "experiments/pilot-direction-probe.md",
    "experiments/reader-friction-screen-v2.md",
)
# These are explicit preparation roles, not measured quality or admission labels.
PREPARATION_ROLES = {
    "3c60dc0a981b686870095450": "leading_whole_article_development_candidate",
    "44aa81958a6c585ee8c06847": "leading_whole_article_development_candidate",
    "0431c592d5de8246cebcb8e2": "challenge_candidate_pending_compilation_review",
    "48bda219eb0776f623161899": "secondary_reader_friction_candidate",
    "48a7a6192771112323fd6820": "secondary_candidate_pending_translation_review",
    "b77b09a419c1631227112f0c": "lower_smell_passage_observations",
    "bf1abf6ca461ec0bbac14bd7": "pre_period_lower_smell_passage_observation",
    "213dcab213f816c7c548fc09": "lower_smell_observation_with_provenance_flag",
    KNOWN_TRANSLATION_ID: "excluded_known_translation_historical_feedback_retained",
    "a127f5baf364930a89fb4005": "pairwise_no_difference_not_a_clean_control",
    HISTORICAL_READER_UNEXPOSED_ID: "feature_exposed_no_persisted_reader_observation",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def period_for(published_at: Any) -> str:
    try:
        value = date.fromisoformat(str(published_at))
    except ValueError:
        return "unresolved"
    if value < date(2023, 1, 1):
        return "pre"
    if value >= date(2025, 7, 1):
        return "post"
    return "transition"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def inventory(root: Path, output_dir: Path) -> dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    private_root = (root / "data/local").resolve()
    if output_dir == private_root or not output_dir.is_relative_to(private_root):
        raise ValueError("Output must be a child directory of the repository data/local directory.")
    if output_dir.exists():
        raise FileExistsError("Output already exists; choose a new versioned output directory.")

    monthly = root / "data/pilot/monthly"
    meta_paths = sorted(monthly.glob("*/meta.jsonl"))
    body_paths = sorted(monthly.glob("*/*.txt"))
    annotation_paths = sorted((root / "data/annotations").glob("*.json"))
    evidence_paths = [root / name for name in PRIOR_EVIDENCE_PATHS]
    source_paths = meta_paths + body_paths + annotation_paths + evidence_paths
    snapshots = {path: path.read_bytes() for path in source_paths}
    input_hashes = {relative(path, root): sha256_bytes(raw) for path, raw in snapshots.items()}

    observations: list[dict[str, Any]] = []
    annotation_summaries: list[dict[str, Any]] = []
    feedback_by_doc: dict[str, list[str]] = defaultdict(list)
    for path in annotation_paths:
        annotation = json.loads(snapshots[path].decode("utf-8-sig"))
        row_key = next(key for key in ("ratings", "pairs", "responses") if key in annotation)
        rows = annotation[row_key]
        ids = set()
        for index, row in enumerate(rows):
            observation_id = f"{path.stem}:{row_key}:{index}"
            doc_id = row.get("doc_id")
            if doc_id:
                ids.add(doc_id)
                feedback_by_doc[doc_id].append(observation_id)
            observations.append({
                "observation_id": observation_id,
                "annotation_path": relative(path, root),
                "annotation_sha256": input_hashes[relative(path, root)],
                "json_pointer": f"/{row_key}/{index}",
                "document_link_status": "exact_persisted_doc_id" if doc_id else "unresolved_no_doc_id",
                "record_verbatim": row,
            })
        annotation_summaries.append({
            "annotation_path": relative(path, root),
            "annotation_sha256": input_hashes[relative(path, root)],
            "persisted_row_count": len(rows),
            "distinct_explicit_doc_ids": len(ids),
            "rows_without_doc_id": sum(not row.get("doc_id") for row in rows),
            "context_verbatim": {key: value for key, value in annotation.items() if key != row_key},
        })

    documents: list[dict[str, Any]] = []
    referenced_paths: list[Path] = []
    for path in meta_paths:
        for line_number, line in enumerate(snapshots[path].decode("utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            metadata = json.loads(line)
            doc_id = metadata["doc_id"]
            text_file = metadata["text_file"]
            if not re.fullmatch(r"[0-9a-f]{24}\.txt", text_file):
                raise ValueError(f"Unexpected pilot body filename in {relative(path, root)}.")
            body_path = path.parent / text_file
            referenced_paths.append(body_path)
            raw = snapshots[body_path]
            # Match the exporter: universal newline decoding, then remove exactly
            # its one appended newline. Keep file identity separate from text identity.
            exported = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            body = exported[:-1] if exported.endswith("\n") else exported
            lines = [value for value in body.splitlines() if value]
            content_hash = sha256_bytes(body.encode("utf-8"))
            counts = {
                "file_bytes": len(raw),
                "text_chars": len(body),
                "cjk_chars": len(CJK_RE.findall(body)),
                "nonempty_line_count": len(lines),
            }
            computed_period = period_for(metadata.get("published_at"))
            checks = {
                "body_filename_matches_doc_id": text_file == f"{doc_id}.txt",
                "body_content_hash_matches_metadata": content_hash == metadata.get("content_hash"),
                "text_chars_match_metadata": counts["text_chars"] == metadata.get("text_chars"),
                "cjk_chars_match_metadata": counts["cjk_chars"] == metadata.get("cjk_chars"),
                "nonempty_lines_match_metadata": len(lines) == metadata.get("line_count"),
                "month_matches_publication_date": path.parent.name == str(metadata.get("published_at"))[:7],
                "period_matches_publication_date": computed_period == metadata.get("period"),
                "doc_id_matches_recorded_url_sha256": doc_id == sha256_bytes(metadata["url"].encode("utf-8"))[:24],
                "exporter_terminal_newline_present": exported.endswith("\n"),
            }
            recorded_flags = bool(metadata.get("translators") or metadata.get("translation_evidence") or metadata.get("is_translation"))
            translation_status = "unresolved_no_recorded_exclusion"
            if recorded_flags:
                translation_status = "unresolved_recorded_provenance_flag"
            if metadata.get("translators") or metadata.get("is_translation") or doc_id == KNOWN_TRANSLATION_ID:
                translation_status = "excluded_known_translation"
            documents.append({
                "schema_version": SCHEMA_VERSION,
                "doc_id": doc_id,
                "metadata_path": relative(path, root),
                "metadata_line_number": line_number,
                "metadata_file_sha256": input_hashes[relative(path, root)],
                "body_path": relative(body_path, root),
                "body_file_sha256": sha256_bytes(raw),
                "body_content_sha256": content_hash,
                "body_metrics": counts,
                "metadata_agreement": checks,
                "metadata_verbatim": metadata,
                "body_scope": "entire_stored_article_export_completeness_not_reverified_against_source",
                "body_rendered_or_copied": False,
                "corpus_feature_exposure": "previous_pilot_discovery_not_independent_validation",
                "reader_observation_ids": feedback_by_doc.get(doc_id, []),
                "reader_exposure_status": "persisted_reader_observation" if doc_id in feedback_by_doc else "no_linked_persisted_reader_observation",
                "historical_reader_unexposed_note": {
                    "reported_unexposed_on": "2026-08-22",
                    "evidence": "data/annotations/reader-friction-screen-v2.json#/corpus_audit",
                    "interpretation": "Reader exposure is distinct from feature exposure; this is not a sealed reserve.",
                } if doc_id == HISTORICAL_READER_UNEXPOSED_ID else None,
                "preparation_role": PREPARATION_ROLES.get(doc_id, "existing_pilot_feature_development_asset"),
                "translation_status": translation_status,
                "known_translation_report": "experiments/pilot-direction-probe.md:21-22" if doc_id == KNOWN_TRANSLATION_ID else None,
                "translation_metadata_conflict": doc_id == KNOWN_TRANSLATION_ID and not recorded_flags,
                "provenance_admission": "not_admitted_by_this_inventory",
                "training_rights": "unverified",
                "visibility_status": "historical_snapshot_not_age_matched_or_reverified",
            })

    doc_ids = {row["doc_id"] for row in documents}
    for row in observations:
        doc_id = row["record_verbatim"].get("doc_id")
        row["body_available_in_monthly_inventory"] = doc_id in doc_ids if doc_id else None
    id_counts = Counter(row["doc_id"] for row in documents)
    url_counts = Counter(row["metadata_verbatim"]["url"] for row in documents)
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for row in documents:
        hash_groups[row["body_content_sha256"]].append(row["doc_id"])
    source_unchanged = all(path.read_bytes() == raw for path, raw in snapshots.items())
    if not source_unchanged:
        raise RuntimeError("An inventoried input changed during the run; no output was written.")
    all_feedback_ids = {row["record_verbatim"].get("doc_id") for row in observations} - {None}
    failed_checks = [
        {"doc_id": row["doc_id"], "check": key}
        for row in documents for key, value in row["metadata_agreement"].items() if not value
    ]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "role": "existing_asset_development_inventory_not_validation_or_admission",
        "command": f'python experiments/inventory_media_development.py --repo-root "{root}" --output-dir "{output_dir}"',
        "script_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "python_version": platform.python_version(),
        "model_calls": 0,
        "network_calls": 0,
        "source_inputs_unchanged": source_unchanged,
        "metadata_file_count": len(meta_paths),
        "metadata_record_count": len(documents),
        "body_file_count": len(body_paths),
        "distinct_document_ids": len(doc_ids),
        "source_period_counts": dict(sorted(Counter(f"{row['metadata_verbatim']['source']}:{row['metadata_verbatim']['period']}" for row in documents).items())),
        "body_chars_total": sum(row["body_metrics"]["text_chars"] for row in documents),
        "body_cjk_chars_total": sum(row["body_metrics"]["cjk_chars"] for row in documents),
        "body_text_chars_min": min(row["body_metrics"]["text_chars"] for row in documents),
        "body_text_chars_max": max(row["body_metrics"]["text_chars"] for row in documents),
        "duplicate_doc_ids": [key for key, count in id_counts.items() if count > 1],
        "duplicate_recorded_urls": [key for key, count in url_counts.items() if count > 1],
        "exact_duplicate_content_groups": [ids for ids in hash_groups.values() if len(ids) > 1],
        "near_duplicate_status": "not_evaluated_by_this_inventory",
        "unreferenced_body_paths": [relative(path, root) for path in body_paths if path not in referenced_paths],
        "multiply_referenced_body_paths": [relative(path, root) for path, count in Counter(referenced_paths).items() if count > 1],
        "failed_metadata_checks": failed_checks,
        "annotation_file_count": len(annotation_paths),
        "persisted_observation_count": len(observations),
        "distinct_explicit_feedback_doc_ids": len(all_feedback_ids),
        "feedback_doc_ids_with_monthly_bodies": len(all_feedback_ids & doc_ids),
        "feedback_doc_ids_without_monthly_bodies": len(all_feedback_ids - doc_ids),
        "observations_with_monthly_bodies": sum(row["body_available_in_monthly_inventory"] is True for row in observations),
        "observations_without_monthly_bodies": sum(row["body_available_in_monthly_inventory"] is False for row in observations),
        "observations_without_explicit_doc_id": sum(row["body_available_in_monthly_inventory"] is None for row in observations),
        "translation_status_counts": dict(sorted(Counter(row["translation_status"] for row in documents).items())),
        "training_rights": "unverified_for_all_documents",
        "body_texts_written_or_rendered": 0,
        "limitations": [
            "The pilot is diagnostic and is not a clean, representative, or final corpus.",
            "All pilot documents have feature-discovery exposure; reader exposure is tracked separately.",
            "Persisted passage preferences are not full-article preferences or independent validation.",
            "No evidence of recorded translation is not evidence of original Chinese authorship.",
            "Stored article completeness and source license were not reverified on live pages.",
            "Full-document rendering, provenance review, and preservation review remain separate steps.",
            "No authorship inference, clean-admission decision, or training-data admission is made.",
        ],
    }
    output_dir.mkdir(parents=True)
    write_jsonl(output_dir / "documents.jsonl", documents)
    write_jsonl(output_dir / "reader-observations.jsonl", observations)
    write_json(output_dir / "annotation-summaries.json", annotation_summaries)
    write_json(output_dir / "source-hashes.json", input_hashes)
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=Path("data/local/compact_refiner/media-inventory-v1"))
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else args.repo_root / args.output_dir
    result = inventory(args.repo_root, output_dir)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
