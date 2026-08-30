"""Calibrate and apply the frozen boundary-competition development gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from deaiodorant.analysis.boundary_competition import (
    BranchingReference,
    BoundaryCompetitionMeasurement,
    SubtlexLexicon,
    cjk_text,
    measure_boundary_competition,
)
from nominal_chain_integration_probe import complete_prose_passages


SCHEMA_VERSION = "deaiodorant-boundary-competition-probe-1.0"
PROTOCOL_VERSION = "boundary-competition-development-1.0"
SEED = 2026083101
MIN_CALIBRATION_WINDOWS = 100
CALIBRATION_LENGTH_RADIUS = 2
HIGH_ENTROPY_PERCENTILE = 0.90
HIGH_MARGIN_PERCENTILE = 0.10
HIGH_MIN_AMBIGUOUS_GAPS = 2
HIGH_MIN_UNRESOLVED_DISTANCE = 6
LOW_ENTROPY_PERCENTILE = 0.50
LOW_MARGIN_PERCENTILE = 0.50
LOW_MAX_AMBIGUOUS_GAPS = 1
LOW_MAX_UNRESOLVED_DISTANCE = 3
MATCH_SPAN_CJK_DIFFERENCE = 2
MATCH_LENGTH_RATIO_LOW = 0.80
MATCH_LENGTH_RATIO_HIGH = 1.25
MATCH_MAX_PER_SOURCE = 3
MATCH_REQUIRED_PAIRS = 8
MATCH_REQUIRED_SOURCES = 3
MATCH_REQUIRED_FORMATS = 2
POST_START = date(2025, 7, 1)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    output = 0
    for character in letters.upper():
        output = output * 26 + ord(character) - ord("A") + 1
    return output - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.iter(f"{{{XLSX_NS}}}t"))
        for item in root.findall(f"{{{XLSX_NS}}}si")
    ]


def _worksheet_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    relationship_id = None
    for sheet in workbook.findall(f".//{{{XLSX_NS}}}sheet"):
        if sheet.attrib.get("name") == sheet_name:
            relationship_id = sheet.attrib.get(f"{{{REL_NS}}}id")
            break
    if relationship_id is None:
        raise ValueError(f"Workbook has no sheet named {sheet_name!r}")
    relationships = ElementTree.fromstring(
        archive.read("xl/_rels/workbook.xml.rels")
    )
    for relationship in relationships.findall(f"{{{PACKAGE_REL_NS}}}Relationship"):
        if relationship.attrib.get("Id") == relationship_id:
            target = relationship.attrib["Target"].lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    raise ValueError(f"Workbook relationship is missing: {relationship_id}")


def read_xlsx_rows(path: Path, sheet_name: str) -> list[list[Any]]:
    """Read a small XLSX sheet with the standard library only."""

    with zipfile.ZipFile(path) as archive:
        shared = _shared_strings(archive)
        worksheet = ElementTree.fromstring(
            archive.read(_worksheet_path(archive, sheet_name))
        )
    output: list[list[Any]] = []
    for row in worksheet.findall(f".//{{{XLSX_NS}}}row"):
        cells: dict[int, Any] = {}
        for cell in row.findall(f"{{{XLSX_NS}}}c"):
            index = _column_index(cell.attrib.get("r", "A1"))
            cell_type = cell.attrib.get("t")
            value_node = cell.find(f"{{{XLSX_NS}}}v")
            if cell_type == "inlineStr":
                value = "".join(
                    node.text or "" for node in cell.iter(f"{{{XLSX_NS}}}t")
                )
            elif value_node is None:
                value = None
            elif cell_type == "s":
                value = shared[int(value_node.text or "0")]
            elif cell_type in {"str", "e"}:
                value = value_node.text
            else:
                raw = value_node.text or ""
                try:
                    numeric = float(raw)
                    value = int(numeric) if numeric.is_integer() else numeric
                except ValueError:
                    value = raw
            cells[index] = value
        if cells:
            output.append([cells.get(index) for index in range(max(cells) + 1)])
    return output


def bsc_sentences(path: Path) -> list[str]:
    rows = read_xlsx_rows(path, "word")
    if not rows:
        raise ValueError("The Beijing Sentence Corpus workbook has no rows")
    header = {str(value): index for index, value in enumerate(rows[0])}
    required = {"SN", "NW", "WORD"}
    if not required.issubset(header):
        raise ValueError(f"Missing Beijing Sentence Corpus columns: {required - set(header)}")
    grouped: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for row in rows[1:]:
        try:
            sentence_number = int(row[header["SN"]])
            word_number = int(row[header["NW"]])
            word = str(row[header["WORD"]])
        except (IndexError, TypeError, ValueError):
            continue
        grouped[sentence_number].append((word_number, word))
    return [
        "".join(word for _, word in sorted(grouped[number]))
        for number in sorted(grouped)
    ]


def calibration_windows(sentences: list[str], lengths: set[int]) -> dict[int, list[str]]:
    output: dict[int, list[str]] = {length: [] for length in sorted(lengths)}
    for raw_sentence in sentences:
        sentence = cjk_text(raw_sentence)
        for length in output:
            if len(sentence) < length:
                continue
            output[length].extend(
                sentence[start : start + length]
                for start in range(len(sentence) - length + 1)
            )
    return output


def percentile_midrank(value: float, reference: list[float]) -> float:
    if not reference:
        raise ValueError("Cannot compute a percentile against an empty reference")
    lower = sum(item < value for item in reference)
    equal = sum(item == value for item in reference)
    return (lower + (0.5 * equal)) / len(reference)


def _margin_value(measurement: BoundaryCompetitionMeasurement) -> float:
    value = measurement.normalized_best_second_margin
    return math.inf if value is None else value


def _measurement_dict(measurement: BoundaryCompetitionMeasurement) -> dict[str, Any]:
    return asdict(measurement)


def calibration_distributions(
    windows: dict[int, list[str]],
    lexicon: SubtlexLexicon,
    branching: BranchingReference,
) -> dict[int, dict[str, list[float]]]:
    output: dict[int, dict[str, list[float]]] = {}
    for length, values in windows.items():
        entropy: list[float] = []
        margin: list[float] = []
        for value in values:
            measurement = measure_boundary_competition(value, lexicon, branching)
            if measurement.abstention_reason is not None:
                continue
            entropy.append(measurement.normalized_path_entropy)
            margin.append(_margin_value(measurement))
        output[length] = {"entropy": entropy, "margin": margin}
    return output


def _nearby_reference(
    length: int,
    distributions: dict[int, dict[str, list[float]]],
    field: str,
) -> list[float]:
    return [
        value
        for candidate_length in range(
            max(2, length - CALIBRATION_LENGTH_RADIUS),
            length + CALIBRATION_LENGTH_RADIUS + 1,
        )
        for value in distributions.get(candidate_length, {}).get(field, [])
    ]


def collect_exposed_document_ids(annotation_dir: Path) -> set[str]:
    output: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            document_id = value.get("doc_id")
            if isinstance(document_id, str):
                output.add(document_id)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for path in sorted(annotation_dir.glob("*.json")):
        visit(json.loads(path.read_text(encoding="utf-8")))
    return output


def load_handoff_indexes(
    roots: list[Path],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    documents: dict[str, dict[str, Any]] = {}
    identities: list[dict[str, Any]] = []
    for root in roots:
        manifest_path = root / "manifest.json"
        documents_path = root / "documents.jsonl"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        identities.append(
            {
                "root": str(root),
                "manifest_sha256": sha256(manifest_path),
                "documents_sha256": sha256(documents_path),
                "declared_documents": manifest.get("documents"),
            }
        )
        for row in read_jsonl(documents_path):
            document_id = row["doc_id"]
            if document_id in documents:
                raise ValueError(f"Duplicate handoff document ID: {document_id}")
            row["_handoff_root"] = str(root)
            documents[document_id] = row
    return documents, identities


def _candidate_passages(
    candidates: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
) -> dict[tuple[str, int], str]:
    requested: dict[str, set[int]] = defaultdict(set)
    for row in candidates:
        requested[row["doc_id"]].add(int(row["line_number"]))
    output: dict[tuple[str, int], str] = {}
    for document_id, line_numbers in requested.items():
        metadata = documents.get(document_id)
        if metadata is None:
            raise ValueError(f"Candidate document is missing from handoffs: {document_id}")
        role = metadata.get("recommended_role")
        if role not in {"development", "discovery_reserve"}:
            raise ValueError(f"Forbidden candidate role for {document_id}: {role}")
        published_at = date.fromisoformat(str(metadata["published_at"])[:10])
        if published_at < POST_START:
            raise ValueError(f"Candidate predates the post boundary: {document_id}")
        root = Path(metadata["_handoff_root"])
        body_path = root / metadata["body_path"]
        body = body_path.read_text(encoding="utf-8", errors="strict")
        passages = dict(complete_prose_passages(body.splitlines()))
        for line_number in line_numbers:
            passage = passages.get(line_number)
            if passage is None:
                raise ValueError(
                    f"Cannot reconstruct passage {document_id}:{line_number}"
                )
            output[(document_id, line_number)] = passage
    return output


def score_candidates(
    candidates: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
    passages: dict[tuple[str, int], str],
    exposed_ids: set[str],
    lexicon: SubtlexLexicon,
    branching: BranchingReference,
    distributions: dict[int, dict[str, list[float]]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(candidates, start=1):
        measurement = measure_boundary_competition(
            row["prehead_text"], lexicon, branching
        )
        length = measurement.scored_characters
        entropy_reference = _nearby_reference(length, distributions, "entropy")
        margin_reference = _nearby_reference(length, distributions, "margin")
        calibration_count = min(len(entropy_reference), len(margin_reference))
        entropy_percentile = None
        margin_percentile = None
        if (
            measurement.abstention_reason is None
            and calibration_count >= MIN_CALIBRATION_WINDOWS
        ):
            entropy_percentile = percentile_midrank(
                measurement.normalized_path_entropy, entropy_reference
            )
            margin_percentile = percentile_midrank(
                _margin_value(measurement), margin_reference
            )
        high = bool(
            entropy_percentile is not None
            and entropy_percentile >= HIGH_ENTROPY_PERCENTILE
            and margin_percentile is not None
            and margin_percentile <= HIGH_MARGIN_PERCENTILE
            and measurement.ambiguous_gap_count >= HIGH_MIN_AMBIGUOUS_GAPS
            and measurement.unresolved_distance_to_head
            >= HIGH_MIN_UNRESOLVED_DISTANCE
        )
        low = bool(
            entropy_percentile is not None
            and entropy_percentile <= LOW_ENTROPY_PERCENTILE
            and margin_percentile is not None
            and margin_percentile >= LOW_MARGIN_PERCENTILE
            and measurement.ambiguous_gap_count <= LOW_MAX_AMBIGUOUS_GAPS
            and measurement.unresolved_distance_to_head
            <= LOW_MAX_UNRESOLVED_DISTANCE
        )
        metadata = documents[row["doc_id"]]
        passage = passages[(row["doc_id"], int(row["line_number"]))]
        if sha256_text(passage) != row["passage_sha256"]:
            raise ValueError(
                f"Passage hash changed for {row['doc_id']}:{row['line_number']}"
            )
        anchor_profile = {
            "proper": bool(row.get("proper_anchors")),
            "numeric": bool(row.get("numeric_anchors")),
            "ascii": measurement.ascii_anchor_count > 0,
        }
        scored = {
            **row,
            "candidate_id": f"bc-{index:03d}",
            "reader_exposed_document": row["doc_id"] in exposed_ids,
            "passage_cjk_chars": len(CJK_RE.findall(passage)),
            "sentence_cjk_chars": len(CJK_RE.findall(row["sentence"])),
            "span_cjk_chars": length,
            "anchor_profile": anchor_profile,
            "measurement": _measurement_dict(measurement),
            "calibration_window_count": calibration_count,
            "entropy_percentile": entropy_percentile,
            "margin_percentile": margin_percentile,
            "competition_stratum": (
                "high" if high else "low" if low else "middle_or_unscored"
            ),
            "handoff_role": metadata.get("recommended_role"),
        }
        output.append(scored)
    return output


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _month_index(value: str) -> int:
    parsed = date.fromisoformat(value[:10])
    return parsed.year * 12 + parsed.month


def _anchor_tuple(row: dict[str, Any]) -> tuple[bool, bool, bool]:
    profile = row["anchor_profile"]
    return profile["proper"], profile["numeric"], profile["ascii"]


def _ratio(left: int, right: int) -> float:
    return left / right if right else math.inf


def _match_cost(high: dict[str, Any], low: dict[str, Any]) -> float | None:
    if high["doc_id"] == low["doc_id"]:
        return None
    if high["source"] != low["source"]:
        return None
    if high["format_stratum"] != low["format_stratum"]:
        return None
    if _anchor_tuple(high) != _anchor_tuple(low):
        return None
    span_difference = abs(high["span_cjk_chars"] - low["span_cjk_chars"])
    if span_difference > MATCH_SPAN_CJK_DIFFERENCE:
        return None
    passage_ratio = _ratio(high["passage_cjk_chars"], low["passage_cjk_chars"])
    sentence_ratio = _ratio(
        high["sentence_cjk_chars"], low["sentence_cjk_chars"]
    )
    if not MATCH_LENGTH_RATIO_LOW <= passage_ratio <= MATCH_LENGTH_RATIO_HIGH:
        return None
    if not MATCH_LENGTH_RATIO_LOW <= sentence_ratio <= MATCH_LENGTH_RATIO_HIGH:
        return None
    span_cost = span_difference / MATCH_SPAN_CJK_DIFFERENCE
    ratio_scale = math.log(MATCH_LENGTH_RATIO_HIGH)
    passage_cost = abs(math.log(passage_ratio)) / ratio_scale
    sentence_cost = abs(math.log(sentence_ratio)) / ratio_scale
    month_difference = abs(
        _month_index(high["published_at"]) - _month_index(low["published_at"])
    )
    month_cost = min(1.0, month_difference / 24)
    return (
        0.35 * span_cost
        + 0.35 * passage_cost
        + 0.20 * sentence_cost
        + 0.10 * month_cost
    )


def _best_candidate_per_document(
    rows: list[dict[str, Any]],
    stratum: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["competition_stratum"] == stratum and not row["reader_exposed_document"]:
            grouped[row["doc_id"]].append(row)
    output: list[dict[str, Any]] = []
    for document_id in sorted(grouped):
        if stratum == "high":
            key = lambda row: (
                -float(row["entropy_percentile"]),
                float(row["margin_percentile"]),
                -int(row["measurement"]["unresolved_distance_to_head"]),
                row["candidate_id"],
            )
        else:
            key = lambda row: (
                float(row["entropy_percentile"]),
                -float(row["margin_percentile"]),
                int(row["measurement"]["unresolved_distance_to_head"]),
                row["candidate_id"],
            )
        output.append(sorted(grouped[document_id], key=key)[0])
    return output


def _tie_break(high: dict[str, Any], low: dict[str, Any]) -> str:
    value = f"{SEED}|{high['candidate_id']}|{low['candidate_id']}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def match_strata(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    high_rows = _best_candidate_per_document(rows, "high")
    low_rows = _best_candidate_per_document(rows, "low")
    edges: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    for high in high_rows:
        for low in low_rows:
            cost = _match_cost(high, low)
            if cost is not None:
                edges.append((cost, _tie_break(high, low), high, low))
    edges.sort(key=lambda item: (item[0], item[1]))

    selected: list[dict[str, Any]] = []
    used_high: set[str] = set()
    used_low: set[str] = set()
    source_counts: Counter[str] = Counter()
    for cost, _, high, low in edges:
        source = high["source"]
        if source_counts[source] >= MATCH_MAX_PER_SOURCE:
            continue
        if high["doc_id"] in used_high or low["doc_id"] in used_low:
            continue
        if high["doc_id"] in used_low or low["doc_id"] in used_high:
            continue
        selected.append(
            {
                "match_id": f"boundary-match-{len(selected) + 1:02d}",
                "cost": round(cost, 8),
                "source": source,
                "format_stratum": high["format_stratum"],
                "anchor_profile": high["anchor_profile"],
                "high_candidate_id": high["candidate_id"],
                "high_doc_id": high["doc_id"],
                "low_candidate_id": low["candidate_id"],
                "low_doc_id": low["doc_id"],
            }
        )
        used_high.add(high["doc_id"])
        used_low.add(low["doc_id"])
        source_counts[source] += 1
        if len(selected) >= MATCH_REQUIRED_PAIRS:
            break

    selected = selected[:MATCH_REQUIRED_PAIRS]
    selected_sources = {row["source"] for row in selected}
    selected_formats = {row["format_stratum"] for row in selected}
    audit = {
        "high_candidate_documents": len(high_rows),
        "low_candidate_documents": len(low_rows),
        "eligible_match_edges": len(edges),
        "selected_pairs": len(selected),
        "selected_sources": sorted(selected_sources),
        "selected_formats": sorted(selected_formats),
        "source_counts": dict(sorted(Counter(row["source"] for row in selected).items())),
        "format_counts": dict(
            sorted(Counter(row["format_stratum"] for row in selected).items())
        ),
        "passed": (
            len(selected) == MATCH_REQUIRED_PAIRS
            and len(selected_sources) >= MATCH_REQUIRED_SOURCES
            and len(selected_formats) >= MATCH_REQUIRED_FORMATS
        ),
    }
    return selected, audit


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen boundary-competition Stage 0 gate."
    )
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--nominal-summary", type=Path, required=True)
    parser.add_argument("--subtlex-word-file", type=Path, required=True)
    parser.add_argument("--subtlex-character-file", type=Path, required=True)
    parser.add_argument("--bsc-workbook", type=Path, required=True)
    parser.add_argument("--handoff-root", type=Path, action="append", required=True)
    parser.add_argument("--annotation-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    nominal_summary = json.loads(args.nominal_summary.read_text(encoding="utf-8"))
    candidates = read_jsonl(args.candidates)
    documents, handoff_identities = load_handoff_indexes(args.handoff_root)
    exposed_ids = collect_exposed_document_ids(args.annotation_dir)
    passages = _candidate_passages(candidates, documents)

    lexicon = SubtlexLexicon.from_subtlex_files(
        args.subtlex_word_file, args.subtlex_character_file
    )
    sentences = bsc_sentences(args.bsc_workbook)
    branching = BranchingReference(sentences)
    candidate_lengths = {
        len(cjk_text(row["prehead_text"])) for row in candidates
    }
    calibration_lengths = {
        candidate_length + offset
        for candidate_length in candidate_lengths
        for offset in range(-CALIBRATION_LENGTH_RADIUS, CALIBRATION_LENGTH_RADIUS + 1)
        if candidate_length + offset >= 2
    }
    windows = calibration_windows(sentences, calibration_lengths)
    distributions = calibration_distributions(windows, lexicon, branching)
    scored = score_candidates(
        candidates=candidates,
        documents=documents,
        passages=passages,
        exposed_ids=exposed_ids,
        lexicon=lexicon,
        branching=branching,
        distributions=distributions,
    )
    matched, matching_audit = match_strata(scored)

    example_text = nominal_summary["reader_example"]["candidates"][0][
        "prehead_text"
    ]
    example = measure_boundary_competition(example_text, lexicon, branching)
    example_entropy_reference = _nearby_reference(
        example.scored_characters, distributions, "entropy"
    )
    example_margin_reference = _nearby_reference(
        example.scored_characters, distributions, "margin"
    )
    example_scored = {
        "text": example_text,
        "measurement": _measurement_dict(example),
        "entropy_percentile": percentile_midrank(
            example.normalized_path_entropy, example_entropy_reference
        ),
        "margin_percentile": percentile_midrank(
            _margin_value(example), example_margin_reference
        ),
        "calibration_window_count": min(
            len(example_entropy_reference), len(example_margin_reference)
        ),
    }

    stratum_counts = Counter(row["competition_stratum"] for row in scored)
    high_component_checks = {
        "entropy_at_or_above_p90": lambda row: (
            row["entropy_percentile"] is not None
            and row["entropy_percentile"] >= HIGH_ENTROPY_PERCENTILE
        ),
        "margin_at_or_below_p10": lambda row: (
            row["margin_percentile"] is not None
            and row["margin_percentile"] <= HIGH_MARGIN_PERCENTILE
        ),
        "at_least_two_ambiguous_gaps": lambda row: (
            row["measurement"]["ambiguous_gap_count"] >= HIGH_MIN_AMBIGUOUS_GAPS
        ),
        "unresolved_distance_at_least_six": lambda row: (
            row["measurement"]["unresolved_distance_to_head"]
            >= HIGH_MIN_UNRESOLVED_DISTANCE
        ),
        "entropy_and_margin": lambda row: (
            row["entropy_percentile"] is not None
            and row["entropy_percentile"] >= HIGH_ENTROPY_PERCENTILE
            and row["margin_percentile"] is not None
            and row["margin_percentile"] <= HIGH_MARGIN_PERCENTILE
        ),
    }
    high_component_counts = {
        name: {
            "instances": sum(check(row) for row in scored),
            "documents": len({row["doc_id"] for row in scored if check(row)}),
        }
        for name, check in high_component_checks.items()
    }
    document_counts = {
        stratum: len(
            {
                row["doc_id"]
                for row in scored
                if row["competition_stratum"] == stratum
                and not row["reader_exposed_document"]
            }
        )
        for stratum in ("high", "low", "middle_or_unscored")
    }
    calibration_counts = {
        str(length): {
            "raw_windows": len(windows[length]),
            "scorable_entropy_windows": len(distributions[length]["entropy"]),
            "scorable_margin_windows": len(distributions[length]["margin"]),
        }
        for length in sorted(windows)
    }
    stage0_passed = bool(
        nominal_summary["reader_example"]["localized"]
        and example.abstention_reason is None
        and example_scored["calibration_window_count"] >= MIN_CALIBRATION_WINDOWS
        and matching_audit["passed"]
    )
    summary = {
        "artifact_type": "deterministic-boundary-competition-stage0-probe",
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "seed": SEED,
        "stage0_passed": stage0_passed,
        "candidate_count": len(scored),
        "stratum_instance_counts": dict(sorted(stratum_counts.items())),
        "stratum_document_counts": document_counts,
        "high_gate_component_counts": high_component_counts,
        "high_gate_extrema": {
            "maximum_entropy_percentile": max(
                float(row["entropy_percentile"])
                for row in scored
                if row["entropy_percentile"] is not None
            ),
            "minimum_margin_percentile": min(
                float(row["margin_percentile"])
                for row in scored
                if row["margin_percentile"] is not None
            ),
            "maximum_ambiguous_gap_count": max(
                int(row["measurement"]["ambiguous_gap_count"])
                for row in scored
            ),
            "maximum_unresolved_distance_to_head": max(
                int(row["measurement"]["unresolved_distance_to_head"])
                for row in scored
            ),
        },
        "exposed_candidate_documents": len(
            {row["doc_id"] for row in scored if row["reader_exposed_document"]}
        ),
        "reader_example": example_scored,
        "matching": matching_audit,
        "thresholds": {
            "minimum_calibration_windows": MIN_CALIBRATION_WINDOWS,
            "calibration_length_radius": CALIBRATION_LENGTH_RADIUS,
            "high_entropy_percentile": HIGH_ENTROPY_PERCENTILE,
            "high_margin_percentile": HIGH_MARGIN_PERCENTILE,
            "high_minimum_ambiguous_gaps": HIGH_MIN_AMBIGUOUS_GAPS,
            "high_minimum_unresolved_distance": HIGH_MIN_UNRESOLVED_DISTANCE,
            "low_entropy_percentile": LOW_ENTROPY_PERCENTILE,
            "low_margin_percentile": LOW_MARGIN_PERCENTILE,
            "low_maximum_ambiguous_gaps": LOW_MAX_AMBIGUOUS_GAPS,
            "low_maximum_unresolved_distance": LOW_MAX_UNRESOLVED_DISTANCE,
            "match_span_cjk_difference": MATCH_SPAN_CJK_DIFFERENCE,
            "match_length_ratio": [MATCH_LENGTH_RATIO_LOW, MATCH_LENGTH_RATIO_HIGH],
            "match_maximum_per_source": MATCH_MAX_PER_SOURCE,
            "required_pairs": MATCH_REQUIRED_PAIRS,
            "required_sources": MATCH_REQUIRED_SOURCES,
            "required_formats": MATCH_REQUIRED_FORMATS,
        },
        "matching_distance": {
            "span_cjk_difference": 0.35,
            "passage_cjk_log_ratio": 0.35,
            "sentence_cjk_log_ratio": 0.20,
            "publication_month_difference_capped_at_24": 0.10,
            "exact_gates": ["source", "format_stratum", "anchor_profile"],
            "selection": "greedy_global_minimum_with_unique_documents_and_source_cap",
            "tie_break": "sha256(seed|high_candidate_id|low_candidate_id)",
        },
        "calibration": {
            "sentence_count": len(sentences),
            "length_counts": calibration_counts,
            "subtlex_word_file": {
                "path": str(args.subtlex_word_file),
                "sha256": sha256(args.subtlex_word_file),
                "license": "CC BY 4.0",
                "source": "https://ndownloader.figshare.com/files/421463",
            },
            "subtlex_character_file": {
                "path": str(args.subtlex_character_file),
                "sha256": sha256(args.subtlex_character_file),
                "license": "CC BY 4.0",
                "source": "https://ndownloader.figshare.com/files/421463",
            },
            "beijing_sentence_corpus": {
                "path": str(args.bsc_workbook),
                "sha256": sha256(args.bsc_workbook),
                "public_project": "https://osf.io/vr3k8/",
                "download": "https://osf.io/download/t4vbg/",
                "license_metadata": "not specified by the OSF node or DataCite record",
            },
        },
        "inputs": {
            "candidates_sha256": sha256(args.candidates),
            "nominal_summary_sha256": sha256(args.nominal_summary),
            "annotation_files": {
                path.name: sha256(path)
                for path in sorted(args.annotation_dir.glob("*.json"))
            },
            "handoffs": handoff_identities,
        },
        "limits": [
            "The probe measures lexical segmentation competition, not authorship.",
            (
                "The Beijing Sentence Corpus has no explicit license in its OSF "
                "or DataCite metadata and is not redistributed."
            ),
            (
                "Branching entropy, accessor variety, tokenizer disagreement, "
                "and anchors are diagnostics only in version 1.0."
            ),
            (
                "The 30-document validation reserve is absent from the candidate "
                "input and no reserve body is opened."
            ),
            "Passing Stage 0 permits edit preparation but is not reader evidence.",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "candidate_measurements.jsonl", scored)
    write_jsonl(args.output_dir / "matched_pairs.jsonl", matched)
    write_csv(
        args.output_dir / "candidate_summary.csv",
        [
            {
                "candidate_id": row["candidate_id"],
                "doc_id": row["doc_id"],
                "source": row["source"],
                "format_stratum": row["format_stratum"],
                "published_at": row["published_at"],
                "line_number": row["line_number"],
                "head": row["head"],
                "prehead_text": row["prehead_text"],
                "span_cjk_chars": row["span_cjk_chars"],
                "entropy_percentile": row["entropy_percentile"],
                "margin_percentile": row["margin_percentile"],
                "ambiguous_gap_count": row["measurement"]["ambiguous_gap_count"],
                "unresolved_distance_to_head": row["measurement"][
                    "unresolved_distance_to_head"
                ],
                "known_character_coverage": row["measurement"][
                    "known_character_coverage"
                ],
                "competition_stratum": row["competition_stratum"],
                "reader_exposed_document": row["reader_exposed_document"],
            }
            for row in scored
        ],
    )
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if stage0_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
