"""Inventory frozen surface motifs in the post development partition."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from head_final_modifier_probe import find_instances as find_head_final_instances

from deaiodorant.analysis.discourse_graph import (
    ABSTRACT_SHELLS,
    CONTRAST_FRAME_RE,
    EMPHATIC_FRAMES,
)


SCHEMA_VERSION = "deaiodorant-post-development-motif-inventory-0.1"
ROLE = "development"
MIN_DOCUMENTS = 6
MIN_SOURCES = 3
SENTENCE_RE = re.compile(r"[^。！？!?\n]+[。！？!?]?")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ASCII_TERM_RE = re.compile(r"[A-Za-z][A-Za-z0-9+_.-]*")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?%?")
QUOTED_RE = re.compile(r"[“\"]([^”\"]+)[”\"]")
CLAUSE_SEPARATOR_RE = re.compile(r"[，,；;：:]")
NONCONCRETE_ASCII = frozenset({"ai", "agent"})
CONNECTIVE_TERMS = (
    "因此",
    "所以",
    "因而",
    "由此",
    "但是",
    "然而",
    "不过",
    "同时",
    "此外",
    "这意味着",
    "换句话说",
    "也就是说",
    "不仅",
    "而且",
)
EMPHATIC_PAYLOAD_VISIBLE = 28
EMPHATIC_PAYLOAD_MIN_SHELLS = 2
ABSTRACT_CLUSTER_MIN_SHELLS = 3
ABSTRACT_CLUSTER_MAX_VISIBLE = 24
DENSE_MIN_CJK = 55
DENSE_MIN_SEPARATORS = 4
DENSE_MIN_SHELLS = 2
DENSE_MIN_CONNECTIVES = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def visible_length(text: str) -> int:
    return sum(not char.isspace() for char in text)


def concrete_anchors(text: str) -> list[str]:
    anchors = NUMBER_RE.findall(text)
    anchors.extend(
        term
        for term in ASCII_TERM_RE.findall(text)
        if term.casefold() not in NONCONCRETE_ASCII
    )
    anchors.extend(value.strip() for value in QUOTED_RE.findall(text) if value.strip())
    return anchors


def term_occurrences(text: str, terms: Iterable[str]) -> list[tuple[int, int, str]]:
    occurrences: list[tuple[int, int, str]] = []
    for term in sorted(terms, key=lambda value: (-len(value), value)):
        for match in re.finditer(re.escape(term), text):
            start, end = match.span()
            if any(start < prior_end and end > prior_start for prior_start, prior_end, _ in occurrences):
                continue
            occurrences.append((start, end, term))
    return sorted(occurrences)


def add_candidate(
    rows: list[dict[str, Any]],
    motif: str,
    sentence: str,
    sentence_index: int,
    span: str,
    details: dict[str, Any],
) -> None:
    rows.append(
        {
            "motif": motif,
            "sentence_index": sentence_index,
            "sentence_sha256": hashlib.sha256(sentence.encode("utf-8")).hexdigest(),
            "span": span,
            "sentence": sentence,
            "details": details,
        }
    )


def find_surface_candidates(text: str) -> list[dict[str, Any]]:
    """Apply frozen lexical and punctuation rules without semantic judgment."""

    rows: list[dict[str, Any]] = []
    sentences = [match.group(0).strip() for match in SENTENCE_RE.finditer(text)]
    for sentence_index, sentence in enumerate(sentences):
        if not sentence:
            continue

        for match in CONTRAST_FRAME_RE.finditer(sentence):
            add_candidate(
                rows,
                "complete_contrast_frame",
                sentence,
                sentence_index,
                match.group(0),
                {"pattern": CONTRAST_FRAME_RE.pattern},
            )

        for marker in EMPHATIC_FRAMES:
            start = sentence.find(marker)
            while start >= 0:
                payload_start = start + len(marker)
                payload = sentence[payload_start:]
                separator = CLAUSE_SEPARATOR_RE.search(payload)
                if separator is not None:
                    payload = payload[: separator.start()]
                if visible_length(payload) <= EMPHATIC_PAYLOAD_VISIBLE:
                    shells = [item[2] for item in term_occurrences(payload, ABSTRACT_SHELLS)]
                    anchors = concrete_anchors(payload)
                    if len(shells) >= EMPHATIC_PAYLOAD_MIN_SHELLS and not anchors:
                        add_candidate(
                            rows,
                            "emphatic_abstract_payload",
                            sentence,
                            sentence_index,
                            sentence[start : payload_start + len(payload)],
                            {
                                "marker": marker,
                                "abstract_shells": shells,
                                "concrete_anchors": anchors,
                            },
                        )
                start = sentence.find(marker, payload_start)

        shell_occurrences = term_occurrences(sentence, ABSTRACT_SHELLS)
        emitted_cluster_ends: set[int] = set()
        for offset in range(len(shell_occurrences) - ABSTRACT_CLUSTER_MIN_SHELLS + 1):
            window = shell_occurrences[offset : offset + ABSTRACT_CLUSTER_MIN_SHELLS]
            start = window[0][0]
            end = window[-1][1]
            span = sentence[start:end]
            if end in emitted_cluster_ends:
                continue
            if (
                visible_length(span) <= ABSTRACT_CLUSTER_MAX_VISIBLE
                and not concrete_anchors(span)
            ):
                emitted_cluster_ends.add(end)
                add_candidate(
                    rows,
                    "abstract_shell_cluster",
                    sentence,
                    sentence_index,
                    span,
                    {
                        "abstract_shells": [item[2] for item in window],
                        "visible_chars": visible_length(span),
                    },
                )

        cjk_count = len(CJK_RE.findall(sentence))
        separator_count = len(CLAUSE_SEPARATOR_RE.findall(sentence))
        shell_terms = [item[2] for item in shell_occurrences]
        connective_count = sum(sentence.count(term) for term in CONNECTIVE_TERMS)
        if (
            cjk_count >= DENSE_MIN_CJK
            and separator_count >= DENSE_MIN_SEPARATORS
            and len(shell_terms) >= DENSE_MIN_SHELLS
            and connective_count >= DENSE_MIN_CONNECTIVES
        ):
            add_candidate(
                rows,
                "dense_clause_surface",
                sentence,
                sentence_index,
                sentence,
                {
                    "cjk_chars": cjk_count,
                    "clause_separators": separator_count,
                    "abstract_shells": shell_terms,
                    "connective_count": connective_count,
                },
            )

        for instance in find_head_final_instances(sentence):
            if instance["low_anchor_abstract_stack_candidate"]:
                add_candidate(
                    rows,
                    "delayed_head_low_anchor",
                    sentence,
                    sentence_index,
                    instance["clause"],
                    {
                        key: value
                        for key, value in instance.items()
                        if key not in {"clause", "start", "end"}
                    },
                )
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--role", default=ROLE)
    args = parser.parse_args()

    handoff_root = args.handoff_root.resolve()
    document_index = handoff_root / "documents.jsonl"
    records = [
        json.loads(line)
        for line in document_index.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selected = [
        record
        for record in records
        if record.get("recommended_role") == args.role
    ]
    candidates: list[dict[str, Any]] = []
    for record in selected:
        body_path = handoff_root / str(record["body_path"])
        body = body_path.read_text(encoding="utf-8").rstrip("\n")
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if content_hash != record["content_hash"]:
            raise ValueError(f"Body hash mismatch for {record['doc_id']}")
        for candidate in find_surface_candidates(body):
            candidates.append(
                {
                    "doc_id": record["doc_id"],
                    "source": record["source"],
                    "published_at": record["published_at"],
                    "format_stratum": record["format_stratum"],
                    "topic_stratum": record["topic_stratum"],
                    **candidate,
                }
            )

    motif_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        motif_rows[row["motif"]].append(row)
    motifs = sorted(
        set(motif_rows)
        | {
            "complete_contrast_frame",
            "emphatic_abstract_payload",
            "abstract_shell_cluster",
            "dense_clause_surface",
            "delayed_head_low_anchor",
        }
    )
    inventory: list[dict[str, Any]] = []
    for motif in motifs:
        rows = motif_rows[motif]
        document_ids = {row["doc_id"] for row in rows}
        sources = {row["source"] for row in rows}
        inventory.append(
            {
                "motif": motif,
                "instance_count": len(rows),
                "document_count": len(document_ids),
                "source_count": len(sources),
                "source_document_counts": dict(
                    sorted(
                        Counter(
                            source
                            for source, _ in {
                                (row["source"], row["doc_id"]) for row in rows
                            }
                        ).items()
                    )
                ),
                "source_counts": dict(sorted(Counter(row["source"] for row in rows).items())),
                "frequency_gate_passed": (
                    len(document_ids) >= MIN_DOCUMENTS and len(sources) >= MIN_SOURCES
                ),
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "candidates.jsonl", candidates)
    summary = {
        "artifact_type": "post-development-deterministic-motif-inventory",
        "schema_version": SCHEMA_VERSION,
        "partition": args.role,
        "document_count": len(selected),
        "source_counts": dict(sorted(Counter(row["source"] for row in selected).items())),
        "candidate_count": len(candidates),
        "frequency_gate": {
            "minimum_independent_documents": MIN_DOCUMENTS,
            "minimum_sources": MIN_SOURCES,
            "interpretation": (
                "Passing is necessary but not sufficient for an intervention. "
                "Candidate coherence and a frozen meaning-preserving operator are still required."
            ),
        },
        "thresholds": {
            "emphatic_payload_max_visible_chars": EMPHATIC_PAYLOAD_VISIBLE,
            "emphatic_payload_min_abstract_shells": EMPHATIC_PAYLOAD_MIN_SHELLS,
            "abstract_cluster_min_shells": ABSTRACT_CLUSTER_MIN_SHELLS,
            "abstract_cluster_max_visible_chars": ABSTRACT_CLUSTER_MAX_VISIBLE,
            "dense_min_cjk_chars": DENSE_MIN_CJK,
            "dense_min_clause_separators": DENSE_MIN_SEPARATORS,
            "dense_min_abstract_shells": DENSE_MIN_SHELLS,
            "dense_min_connectives": DENSE_MIN_CONNECTIVES,
        },
        "inventory": inventory,
        "identity": {
            "handoff_manifest_sha256": sha256(handoff_root / "manifest.json"),
            "handoff_documents_sha256": sha256(document_index),
        },
        "limits": [
            "No body outside the requested role is opened by this script.",
            "The rules localize surface candidates and do not judge authorship or reader dislike.",
            "The dense-clause rule is a punctuation and lexicon proxy, not a proposition parser.",
            "Frequency-gate passage does not authorize a reader intervention without manual coherence audit.",
        ],
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
