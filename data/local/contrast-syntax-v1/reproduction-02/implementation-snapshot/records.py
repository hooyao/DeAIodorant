"""Deterministic development records; no semantic acceptance is inferred."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import unicodedata


PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")
NUMBER = re.compile(r"(?<![A-Za-z0-9_.])\d+(?:[.,]\d+)*(?:%)?(?![0-9.])", re.ASCII)
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def object_hash(value: Any) -> str:
    return text_hash(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    import os

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def validate_briefs(briefs: list[dict[str, Any]], expected_count: int = 24) -> None:
    if len(briefs) != expected_count:
        raise ValueError("Unexpected brief count")
    for field in ("brief_id", "task_group_id"):
        if len({item[field] for item in briefs}) != len(briefs):
            raise ValueError(f"Duplicate {field}")
    for item in briefs:
        for field in ("brief_id", "task_group_id", "genre", "audience", "intended_voice",
                      "requested_length", "instruction_text", "fact_packet"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Missing or invalid {field}")
        if item.get("contains_personal_data") is not False:
            raise ValueError("First-batch briefs must exclude personal data")
        if item.get("rights_status") != "project_constructed":
            raise ValueError("Unexpected first-batch rights status")
        facts = item.get("required_facts")
        if not isinstance(facts, list) or not facts:
            raise ValueError("Missing fact inventory")
        if len({fact["fact_id"] for fact in facts}) != len(facts):
            raise ValueError("Duplicate fact ID")
        for fact in facts:
            if not fact.get("statement") or not isinstance(fact.get("protected_literals"), list):
                raise ValueError("Invalid fact inventory")


def render_prompt(template: str, values: dict[str, Any]) -> str:
    """Substitute once, so template-like text in source data is not executed."""
    names = set(PLACEHOLDER.findall(template))
    missing = names - values.keys()
    if missing:
        raise ValueError("Missing prompt fields: " + ", ".join(sorted(missing)))
    for name in names:
        if not isinstance(values[name], str):
            raise ValueError(f"Prompt field must be text: {name}")
    return PLACEHOLDER.sub(lambda match: values[match.group(1)], template)


def replay_operations(original: str, operations: list[dict[str, Any]]) -> str:
    ordered = sorted(operations, key=lambda item: (item["start_char"], item["end_char"]))
    last_end = -1
    for item in ordered:
        start, end = item["start_char"], item["end_char"]
        if not (0 <= start <= end <= len(original)) or start < last_end:
            raise ValueError("Invalid or overlapping operation offsets")
        if original[start:end] != item["before"]:
            raise ValueError("Operation does not match original text")
        last_end = end
    result = original
    for item in reversed(ordered):
        result = result[:item["start_char"]] + item["after"] + result[item["end_char"]:]
    return result


def literal_diagnostics(original: str, output: str, protected: list[str]) -> dict[str, Any]:
    """Return warnings only: neither equality nor a warning is a semantic verdict."""
    source_numbers = Counter(NUMBER.findall(unicodedata.normalize("NFKC", original)))
    output_numbers = Counter(NUMBER.findall(unicodedata.normalize("NFKC", output)))
    present = sorted({literal for literal in protected if literal and literal in original})
    return {
        "schema_version": "compact-refiner-literal-diagnostics-1.0",
        "original_cjk_chars": len(CJK.findall(original)),
        "output_cjk_chars": len(CJK.findall(output)),
        "unchanged": original == output,
        "missing_numeric_occurrences": dict(source_numbers - output_numbers),
        "added_numeric_occurrences": dict(output_numbers - source_numbers),
        "missing_protected_literals": [literal for literal in present if literal not in output],
        "semantic_disposition": "unreviewed",
        "limitation": "Literal warnings require contextual review; no entailment or acceptance is inferred.",
    }


def make_candidate(draft: dict[str, Any], output: str, kind: str,
                   inference: dict[str, Any] | None = None) -> dict[str, Any]:
    original = draft["draft_text"]
    operations = [] if original == output else [{
        "operation_id": draft["draft_id"] + "-rewrite",
        "type": "unclassified_rewrite",
        "start_char": 0,
        "end_char": len(original),
        "before": original,
        "after": output,
        "reason": "Bounded passage rewrite awaiting semantic intent review.",
        "claim_ids": [],
    }]
    if replay_operations(original, operations) != output:
        raise ValueError("Operation replay failed")
    return {
        "candidate_id": draft["draft_id"] + "-" + kind,
        "task_group_id": draft["task_group_id"],
        "draft_id": draft["draft_id"],
        "candidate_kind": kind,
        "intensity": "medium",
        "input_sha256": text_hash(original),
        "output_text": output,
        "output_sha256": text_hash(output),
        "operations": operations,
        "inference": inference,
        "eligibility_status": "awaiting_semantic_review",
        "human_gold": False,
    }


def validate_saved_records(drafts: list[dict[str, Any]], candidates: list[dict[str, Any]],
                           briefs: list[dict[str, Any]]) -> None:
    """Reject damaged or ambiguous checkpoints before any API resumption."""
    for rows, field in ((briefs, "brief_id"), (drafts, "draft_id"), (candidates, "candidate_id")):
        if len({row[field] for row in rows}) != len(rows):
            raise ValueError(f"Duplicate {field} in saved records")
    brief_index = {item["brief_id"]: item for item in briefs}
    draft_index = {item["draft_id"]: item for item in drafts}
    for draft in drafts:
        brief = brief_index.get(draft["brief_id"])
        if brief is None or draft["task_group_id"] != brief["task_group_id"]:
            raise ValueError("Draft brief/group mismatch")
        if draft["draft_sha256"] != text_hash(draft["draft_text"]):
            raise ValueError("Draft content hash mismatch")
        if draft["draft_id"] != draft["brief_id"] + "-draft":
            raise ValueError("Unexpected draft ID")
        if draft.get("human_gold") is not False:
            raise ValueError("Draft provenance is not model-only development")
    for candidate in candidates:
        draft = draft_index.get(candidate["draft_id"])
        if draft is None or candidate["task_group_id"] != draft["task_group_id"]:
            raise ValueError("Candidate draft/group mismatch")
        if candidate["input_sha256"] != draft["draft_sha256"]:
            raise ValueError("Candidate input hash mismatch")
        if candidate["candidate_id"] != candidate["draft_id"] + "-" + candidate["candidate_kind"]:
            raise ValueError("Candidate ID does not match kind")
        if candidate.get("human_gold") is not False:
            raise ValueError("Candidate provenance is not model-only development")
        if candidate["output_sha256"] != text_hash(candidate["output_text"]):
            raise ValueError("Candidate output hash mismatch")
        if replay_operations(draft["draft_text"], candidate["operations"]) != candidate["output_text"]:
            raise ValueError("Candidate operation replay mismatch")
        if candidate["candidate_kind"] == "unchanged" and (
            candidate["operations"] or candidate["output_text"] != draft["draft_text"]
        ):
            raise ValueError("Unchanged candidate differs from draft")
