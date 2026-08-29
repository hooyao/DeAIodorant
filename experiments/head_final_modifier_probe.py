"""Find long, low-anchor pre-head modifier spans without model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from prepare_reader_friction_screen_v3 import complete_segments


SCHEMA_VERSION = "deaiodorant-head-final-modifier-probe-0.1"
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CLAUSE_RE = re.compile(r"[^。！？!?；;，,：:\n]+")
ASCII_TERM_RE = re.compile(r"[A-Za-z][A-Za-z0-9+_.-]*")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?%?")
QUOTED_RE = re.compile(r"[“\"]([^”\"]+)[”\"]")

CUE_TERMS = (
    "服务于",
    "适用于",
    "面向",
    "针对",
    "围绕",
    "满足",
    "适应",
    "支撑",
    "支持",
    "聚焦",
)
HEAD_NOUNS = (
    "需求",
    "能力",
    "体系",
    "架构",
    "机制",
    "方案",
    "目标",
    "问题",
    "场景",
    "路径",
    "逻辑",
    "模式",
    "流程",
    "服务",
    "平台",
)
GENERIC_MODIFIERS = (
    "人工智能时代",
    "大模型时代",
    "智能时代",
    "数字化时代",
    "AI 原生时代",
    "AI原生时代",
    "Agent 时代",
    "Agent时代",
    "全新",
    "新一代",
    "核心",
    "关键",
    "深度",
    "全面",
    "系统性",
    "一体化",
    "智能化",
    "高效",
    "原生",
    "时代",
)
NONCONCRETE_ASCII_TERMS = frozenset({"ai", "agent"})
LONG_DELAY_CJK = 8
LONG_DELAY_VISIBLE = 12
LOW_ANCHOR_GENERIC_COUNT = 2


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _visible_length(text: str) -> int:
    return sum(not char.isspace() for char in text)


def _concrete_anchors(text: str) -> list[str]:
    anchors = NUMBER_RE.findall(text)
    anchors.extend(
        term
        for term in ASCII_TERM_RE.findall(text)
        if term.casefold() not in NONCONCRETE_ASCII_TERMS
    )
    anchors.extend(
        quoted.strip()
        for quoted in QUOTED_RE.findall(text)
        if quoted.strip()
    )
    return anchors


def _nonoverlapping_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    """Count longest lexical concepts without double-counting their substrings."""

    occupied: set[int] = set()
    selected: list[tuple[int, str]] = []
    for term in sorted(terms, key=lambda item: (-len(item), item)):
        start = text.find(term)
        while start >= 0:
            span = set(range(start, start + len(term)))
            if not span.intersection(occupied):
                occupied.update(span)
                selected.append((start, term))
            start = text.find(term, start + len(term))
    return [term for _, term in sorted(selected)]


def find_instances(text: str) -> list[dict[str, Any]]:
    """Return longest delayed-head candidates for each cue in each clause."""

    instances: list[dict[str, Any]] = []
    for clause_match in CLAUSE_RE.finditer(text):
        clause = clause_match.group(0).strip()
        if not clause:
            continue
        for cue in CUE_TERMS:
            search_start = 0
            while True:
                cue_index = clause.find(cue, search_start)
                if cue_index < 0:
                    break
                after_cue = cue_index + len(cue)
                head_matches: list[tuple[int, str]] = []
                for head in HEAD_NOUNS:
                    head_index = clause.find(head, after_cue)
                    while head_index >= 0:
                        if _visible_length(clause[after_cue:head_index]) <= 36:
                            head_matches.append((head_index, head))
                        head_index = clause.find(head, head_index + len(head))
                if head_matches:
                    head_index, head = max(
                        head_matches,
                        key=lambda item: (item[0], len(item[1])),
                    )
                    modifier = clause[after_cue:head_index].strip()
                    cjk_delay = len(CJK_RE.findall(modifier))
                    visible_delay = _visible_length(modifier)
                    generic_terms = _nonoverlapping_terms(
                        modifier,
                        GENERIC_MODIFIERS,
                    )
                    anchors = _concrete_anchors(modifier)
                    long_delay = (
                        cjk_delay >= LONG_DELAY_CJK
                        or visible_delay >= LONG_DELAY_VISIBLE
                    )
                    instances.append(
                        {
                            "cue": cue,
                            "head": head,
                            "modifier": modifier,
                            "clause": clause,
                            "cjk_delay": cjk_delay,
                            "visible_delay": visible_delay,
                            "generic_modifier_terms": generic_terms,
                            "generic_modifier_count": len(generic_terms),
                            "concrete_anchors": anchors,
                            "concrete_anchor_count": len(anchors),
                            "long_head_delay": long_delay,
                            "low_anchor_abstract_stack_candidate": (
                                long_delay
                                and len(generic_terms) >= LOW_ANCHOR_GENERIC_COUNT
                                and not anchors
                            ),
                            "start": clause_match.start() + cue_index,
                            "end": clause_match.start() + head_index + len(head),
                        }
                    )
                search_start = after_cue
    return instances


def _read_handoff(
    handoff_root: Path,
    recommended_role: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = [
        json.loads(line)
        for line in (handoff_root / "documents.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    instances: list[dict[str, Any]] = []
    for record in records:
        if (
            recommended_role is not None
            and record.get("recommended_role") != recommended_role
        ):
            continue
        body_path = handoff_root / str(record["body_path"])
        body = body_path.read_text(encoding="utf-8").rstrip("\n")
        if hashlib.sha256(body.encode("utf-8")).hexdigest() != record["content_hash"]:
            raise ValueError(f"Body hash mismatch for {record['doc_id']}")
        for line_number, passage in complete_segments(body.splitlines()):
            for instance in find_instances(passage):
                instances.append(
                    {
                        "doc_id": record["doc_id"],
                        "source": record["source"],
                        "format": record["format_stratum"],
                        "published_at": record["published_at"],
                        "line_number": line_number,
                        "passage_sha256": hashlib.sha256(
                            passage.encode("utf-8")
                        ).hexdigest(),
                        **instance,
                    }
                )
    selected_records = [
        record
        for record in records
        if recommended_role is None
        or record.get("recommended_role") == recommended_role
    ]
    return selected_records, instances


def _variant_instances(answer_key_path: Path) -> list[dict[str, Any]]:
    answer_key = json.loads(answer_key_path.read_text(encoding="utf-8"))
    instances: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pair in answer_key["pairs"]:
        base_pair_id = pair.get("base_pair_id")
        operation = pair.get("operation")
        if not base_pair_id or not operation or base_pair_id in seen:
            continue
        seen.add(base_pair_id)
        for variant, text in (
            ("original", operation["before"]),
            ("revised", operation["after"]),
        ):
            for instance in find_instances(text):
                instances.append(
                    {
                        "base_pair_id": base_pair_id,
                        "doc_id": pair["doc_id"],
                        "variant": variant,
                        **instance,
                    }
                )
    return instances


def _read_discovery_pool(
    pool_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Read the verified pre/transition handoff without changing its files."""

    records = [
        json.loads(line)
        for line in pool_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    instances: list[dict[str, Any]] = []
    for record in records:
        body_path = Path(str(record["body_path"]))
        body = body_path.read_text(encoding="utf-8").rstrip("\n")
        if hashlib.sha256(body.encode("utf-8")).hexdigest() != record["content_hash"]:
            raise ValueError(f"Discovery body hash mismatch for {record['doc_id']}")
        for line_number, passage in complete_segments(body.splitlines()):
            for instance in find_instances(passage):
                instances.append(
                    {
                        "doc_id": record["doc_id"],
                        "source": record["source"],
                        "period": record["period"],
                        "published_at": record["published_at"],
                        "line_number": line_number,
                        "passage_sha256": hashlib.sha256(
                            passage.encode("utf-8")
                        ).hexdigest(),
                        **instance,
                    }
                )
    return records, instances


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument("--recommended-role")
    parser.add_argument("--discovery-pool", type=Path)
    parser.add_argument("--integration-answer-key", type=Path, required=True)
    parser.add_argument("--integration-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    handoff_root = args.handoff_root.resolve()
    records, instances = _read_handoff(
        handoff_root,
        recommended_role=args.recommended_role,
    )
    discovery_records: list[dict[str, Any]] = []
    discovery_instances: list[dict[str, Any]] = []
    if args.discovery_pool is not None:
        discovery_records, discovery_instances = _read_discovery_pool(
            args.discovery_pool.resolve()
        )
    variant_instances = _variant_instances(args.integration_answer_key)
    results = json.loads(args.integration_results.read_text(encoding="utf-8"))
    result_by_pair = {
        item["base_pair_id"]: item["outcome"]
        for item in results["pairs"]
        if item.get("control_role") == "intervention"
    }
    for instance in variant_instances:
        instance["outcome"] = result_by_pair.get(instance["base_pair_id"])

    example_text = "AI 算力池面向 AI 原生时代全新算力服务需求，采用分层架构。"
    example_instances = find_instances(example_text)
    if not any(
        item["cue"] == "面向"
        and item["head"] == "需求"
        and item["low_anchor_abstract_stack_candidate"]
        for item in example_instances
    ):
        raise ValueError("Frozen reader example is not localized by the probe")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(args.output_dir / "corpus_instances.jsonl", instances)
    _write_jsonl(args.output_dir / "integration_variant_instances.jsonl", variant_instances)
    if args.discovery_pool is not None:
        _write_jsonl(
            args.output_dir / "discovery_instances.jsonl",
            discovery_instances,
        )
    long_instances = [item for item in instances if item["long_head_delay"]]
    abstract_instances = [
        item for item in instances if item["low_anchor_abstract_stack_candidate"]
    ]
    discovery_long = [
        item for item in discovery_instances if item["long_head_delay"]
    ]
    discovery_abstract = [
        item
        for item in discovery_instances
        if item["low_anchor_abstract_stack_candidate"]
    ]
    summary = {
        "artifact_type": "deterministic-head-final-modifier-development-probe",
        "schema_version": SCHEMA_VERSION,
        "thresholds": {
            "long_delay_cjk_chars": LONG_DELAY_CJK,
            "long_delay_visible_chars": LONG_DELAY_VISIBLE,
            "low_anchor_generic_modifier_count": LOW_ANCHOR_GENERIC_COUNT,
        },
        "lexicons": {
            "cue_terms": list(CUE_TERMS),
            "head_nouns": list(HEAD_NOUNS),
            "generic_modifiers": list(GENERIC_MODIFIERS),
        },
        "corpus": {
            "document_count": len(records),
            "recommended_role_filter": args.recommended_role,
            "instance_count": len(instances),
            "long_head_delay_count": len(long_instances),
            "long_head_delay_document_count": len(
                {item["doc_id"] for item in long_instances}
            ),
            "low_anchor_abstract_stack_count": len(abstract_instances),
            "low_anchor_abstract_stack_document_count": len(
                {item["doc_id"] for item in abstract_instances}
            ),
            "cue_counts": dict(sorted(Counter(item["cue"] for item in long_instances).items())),
            "head_counts": dict(sorted(Counter(item["head"] for item in long_instances).items())),
        },
        "integration_variants": {
            "instance_count": len(variant_instances),
            "long_head_delay_count": sum(
                item["long_head_delay"] for item in variant_instances
            ),
            "low_anchor_abstract_stack_count": sum(
                item["low_anchor_abstract_stack_candidate"]
                for item in variant_instances
            ),
        },
        "discovery_pool": {
            "document_count": len(discovery_records),
            "period_counts": dict(
                sorted(Counter(str(item["period"]) for item in discovery_records).items())
            ),
            "instance_count": len(discovery_instances),
            "long_head_delay_count": len(discovery_long),
            "long_head_delay_document_count": len(
                {item["doc_id"] for item in discovery_long}
            ),
            "low_anchor_abstract_stack_count": len(discovery_abstract),
            "low_anchor_abstract_stack_document_count": len(
                {item["doc_id"] for item in discovery_abstract}
            ),
            "strict_period_counts": dict(
                sorted(Counter(str(item["period"]) for item in discovery_abstract).items())
            ),
            "strict_source_counts": dict(
                sorted(Counter(str(item["source"]) for item in discovery_abstract).items())
            ),
        },
        "identity": {
            "handoff_manifest_sha256": _sha256(handoff_root / "manifest.json"),
            "handoff_documents_sha256": _sha256(handoff_root / "documents.jsonl"),
            "integration_answer_key_sha256": _sha256(args.integration_answer_key),
            "integration_results_sha256": _sha256(args.integration_results),
            "discovery_pool_sha256": (
                _sha256(args.discovery_pool.resolve())
                if args.discovery_pool is not None
                else None
            ),
        },
        "limits": [
            "The probe is a high-precision lexical candidate generator, not a parser or semantic judge.",
            "A low-anchor abstract stack candidate is not automatically meaningless or undesirable.",
            "Concrete-anchor detection is intentionally narrow and misses many domain-specific anchors.",
            "Lexicon and thresholds were defined after the reader example and require independent intervention evidence.",
            "The pre/transition discovery pool cannot estimate or validate a post-period effect.",
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
