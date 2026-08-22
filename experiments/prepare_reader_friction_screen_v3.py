"""Prepare a post-only within-document reader-friction calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_reader_friction_screen_v1 import CJK_RE, is_eligible_passage
from prepare_reader_friction_screen_v2 import (
    COMPLETE_END_RE,
    PROFILE_RE,
    Pair,
    PassageFeatures,
    content_bigram_jaccard,
    passage_features,
    rank_document,
    ranked_passage_manifest,
    stable_tiebreak,
)


SCHEMA_VERSION = "deaiodorant-reader-friction-screen-3.0"
PROTOCOL_VERSION = "post-only-friction-discrimination-development-3.0"
DEFAULT_SEED = 2026082204
CELL_QUOTAS = {
    ("infoq", "industry_reporting"): 4,
    ("meituan_tech", "research_summary"): 2,
    ("infoq", "technical_practice"): 2,
    ("meituan_tech", "technical_practice"): 4,
}
PROSE_METADATA_RE = re.compile(
    r"(?:作者介绍|作者简介|论文下载|请查阅|开源地址|项目主页|"
    r"(?:^|\n)\s*(?:PDF|原文|GitHub|HuggingFace|Case\s*\d+)[：:\s]*(?:\n|$))",
    re.IGNORECASE,
)


LABEL_CONFIG = """<View>
  <Header value="新 post 语料阅读阻力比较"/>
  <Text name="instruction" value="下面两段来自同一篇 2025 年 7 月之后的文章。哪一段让你更不愿意继续读？只按第一感受选择；没有明显差别时请直接选第三项，不需要分析语言特征。"/>
  <Header value="A"/>
  <Text name="passage_a" value="$passage_a"/>
  <Header value="B"/>
  <Text name="passage_b" value="$passage_b"/>
  <Choices name="friction_choice" toName="passage_a" choice="single-radio" required="true" showInline="false">
    <Choice value="A，让我更不愿意继续读"/>
    <Choice value="B，让我更不愿意继续读"/>
    <Choice value="没有明显差别（都还行或都不好）"/>
  </Choices>
  <Header value="可选评论"/>
  <TextArea name="comment" toName="passage_a" placeholder="可以留空；若某一句特别影响阅读，也可以随手写一句。" rows="2"/>
</View>
"""


def read_jsonl(path: Path) -> list[dict[str, object]]:
    """Read strict UTF-8 JSON Lines."""

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def complete_segments(lines: list[str]) -> list[tuple[int, str]]:
    """Rejoin short DOM-split lines into non-overlapping complete passages."""

    output: list[tuple[int, str]] = []
    buffer: list[str] = []
    buffer_start = 0
    for line_number, raw_line in enumerate(lines, start=1):
        passage = raw_line.strip()
        if not passage:
            continue
        eligible, _, band = is_eligible_passage(passage)
        if (
            eligible
            and band is not None
            and COMPLETE_END_RE.search(passage)
            and not PROFILE_RE.search(passage)
            and is_prose_segment(passage)
        ):
            buffer.clear()
            output.append((line_number, passage))
            continue
        if "http://" in passage or "https://" in passage or PROFILE_RE.search(passage):
            buffer.clear()
            continue
        if not buffer:
            buffer_start = line_number
        buffer.append(passage)
        combined = "\n".join(buffer)
        if len(combined) > 520:
            buffer.clear()
            continue
        eligible, _, band = is_eligible_passage(combined)
        if (
            eligible
            and band is not None
            and COMPLETE_END_RE.search(combined)
            and not PROFILE_RE.search(combined)
            and is_prose_segment(combined)
        ):
            output.append((buffer_start, combined))
            buffer.clear()
    return output


def is_prose_segment(passage: str) -> bool:
    """Reject navigation metadata and list-heavy reconstructed fragments."""

    if PROSE_METADATA_RE.search(passage):
        return False
    short_lines = sum(
        0 < len(CJK_RE.findall(line)) < 16 for line in passage.splitlines()
    )
    return short_lines <= 1


def collect_passages(
    handoff_root: Path,
) -> tuple[dict[str, list[PassageFeatures]], dict[str, dict[str, object]]]:
    """Collect complete paragraphs from the validated fresh post handoff."""

    records = read_jsonl(handoff_root / "documents.jsonl")
    passages_by_document: dict[str, list[PassageFeatures]] = defaultdict(list)
    metadata: dict[str, dict[str, object]] = {}
    for record in records:
        doc_id = str(record["doc_id"])
        published_at = str(record["published_at"])
        if published_at < "2025-07-01":
            raise ValueError(f"Non-post document in handoff: {doc_id}")
        body_path = (handoff_root / str(record["body_path"])).resolve()
        body_path.relative_to(handoff_root)
        stored = body_path.read_text(encoding="utf-8")
        body = stored[:-1] if stored.endswith("\n") else stored
        observed_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if observed_hash != record["content_hash"]:
            raise ValueError(f"Content hash mismatch for {doc_id}")
        metadata[doc_id] = record
        for line_number, passage in complete_segments(body.splitlines()):
            eligible, cjk_chars, band = is_eligible_passage(passage)
            if not eligible or band is None:
                continue
            if not COMPLETE_END_RE.search(passage) or PROFILE_RE.search(passage):
                continue
            passages_by_document[doc_id].append(
                passage_features(
                    doc_id=doc_id,
                    source=str(record["source"]),
                    published_at=published_at,
                    line_number=line_number,
                    passage=passage,
                    cjk_chars=cjk_chars,
                    length_band=band,
                )
            )
    return passages_by_document, metadata


def choose_post_pair(passages: list[PassageFeatures], seed: int) -> Pair | None:
    """Choose a marker-plus-structure candidate and a locally matched control."""

    if len(passages) < 4:
        return None
    ranked = rank_document(passages)
    candidates = [
        item
        for item in ranked
        if item.passage.target_marker_count > 0
        and item.auxiliary_top_quartile_votes >= 1
    ]
    candidates.sort(
        key=lambda item: (
            -item.auxiliary_top_quartile_votes,
            -item.rank_sum,
            -item.passage.target_marker_count,
            stable_tiebreak(seed, item.passage),
        )
    )
    for candidate in candidates:
        controls = []
        for item in ranked:
            if item.passage.target_marker_count != 0:
                continue
            if abs(item.passage.sentence_count - candidate.passage.sentence_count) > 2:
                continue
            length_ratio = item.passage.cjk_chars / candidate.passage.cjk_chars
            if not 0.7 <= length_ratio <= 1.4:
                continue
            if abs(item.passage.line_number - candidate.passage.line_number) < 2:
                continue
            if candidate.rank_sum - item.rank_sum < 0.75:
                continue
            similarity = content_bigram_jaccard(
                candidate.passage.passage, item.passage.passage
            )
            if similarity < 0.015:
                continue
            controls.append((item, similarity))
        controls.sort(
            key=lambda match: (
                -match[1],
                match[0].rank_sum,
                abs(
                    match[0].passage.cjk_chars - candidate.passage.cjk_chars
                ),
                stable_tiebreak(seed, match[0].passage),
            )
        )
        if not controls:
            continue
        control, similarity = controls[0]
        passage = candidate.passage
        return Pair(
            pair_id=f"friction-v3-{passage.doc_id[:8]}",
            source=passage.source,
            doc_id=passage.doc_id,
            candidate=candidate,
            control=control,
            rank_gap=candidate.rank_sum - control.rank_sum,
            content_bigram_jaccard=similarity,
        )
    return None


def select_pairs(
    passages_by_document: dict[str, list[PassageFeatures]],
    metadata: dict[str, dict[str, object]],
    seed: int,
) -> tuple[list[Pair], list[Pair]]:
    """Select the frozen source-format quotas from pairable documents."""

    pairable = [
        replace(pair, pair_id=f"friction-v3-{pair.doc_id[:8]}")
        for passages in passages_by_document.values()
        if (pair := choose_post_pair(passages, seed)) is not None
    ]
    selected: list[Pair] = []
    for (source, format_name), quota in CELL_QUOTAS.items():
        candidates = [
            pair
            for pair in pairable
            if pair.source == source
            and metadata[pair.doc_id]["format_stratum"] == format_name
        ]
        candidates.sort(
            key=lambda pair: (
                -pair.candidate.auxiliary_top_quartile_votes,
                -pair.rank_gap,
                -pair.candidate.passage.target_marker_count,
                stable_tiebreak(seed, pair.candidate.passage),
            )
        )
        if len(candidates) < quota:
            raise ValueError(
                f"Not enough pairs for {source}/{format_name}: "
                f"{len(candidates)} < {quota}"
            )
        selected.extend(candidates[:quota])
    if len({pair.doc_id for pair in selected}) != len(selected):
        raise ValueError("A document was selected more than once")
    return selected, pairable


def build_artifacts(
    handoff_root: Path, seed: int
) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object]]:
    """Build blinded tasks, answer key, and the frozen protocol."""

    passages_by_document, metadata = collect_passages(handoff_root)
    selected, pairable = select_pairs(passages_by_document, metadata, seed)
    rng = random.Random(seed)
    rng.shuffle(selected)
    candidate_sides = ["A"] * 6 + ["B"] * 6
    rng.shuffle(candidate_sides)

    tasks: list[dict[str, object]] = []
    answer_pairs: list[dict[str, object]] = []
    manifest_pairs: list[dict[str, object]] = []
    for task_number, (pair, candidate_side) in enumerate(
        zip(selected, candidate_sides, strict=True), start=1
    ):
        record = metadata[pair.doc_id]
        candidate = pair.candidate.passage.passage
        control = pair.control.passage.passage
        passage_a, passage_b = (
            (candidate, control) if candidate_side == "A" else (control, candidate)
        )
        tasks.append(
            {
                "data": {
                    "task_number": task_number,
                    "passage_a": passage_a,
                    "passage_b": passage_b,
                },
                "meta": {
                    "pair_id": pair.pair_id,
                    "source": pair.source,
                    "format_stratum": record["format_stratum"],
                    "topic_stratum": record["topic_stratum"],
                    "published_at": record["published_at"],
                },
            }
        )
        answer_pairs.append(
            {
                "task_number": task_number,
                "pair_id": pair.pair_id,
                "doc_id": pair.doc_id,
                "candidate_side": candidate_side,
                "candidate_line": pair.candidate.passage.line_number,
                "control_line": pair.control.passage.line_number,
            }
        )
        manifest_pairs.append(
            {
                "task_number": task_number,
                "pair_id": pair.pair_id,
                "source": pair.source,
                "format_stratum": record["format_stratum"],
                "topic_stratum": record["topic_stratum"],
                "doc_id": pair.doc_id,
                "published_at": record["published_at"],
                "candidate": ranked_passage_manifest(pair.candidate),
                "control": ranked_passage_manifest(pair.control),
                "rank_gap": pair.rank_gap,
                "content_bigram_jaccard": pair.content_bigram_jaccard,
            }
        )

    handoff_manifest = handoff_root / "manifest.json"
    answer_key = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "seed": seed,
        "pairs": answer_pairs,
    }
    protocol = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "status": "frozen_before_outcomes",
        "frozen_at": "2026-08-22",
        "seed": seed,
        "role": "post_only_development_discrimination_not_validation",
        "handoff": {
            "root": str(handoff_root),
            "manifest_sha256": hashlib.sha256(handoff_manifest.read_bytes()).hexdigest(),
            "documents": len(metadata),
        },
        "sampling_policy": {
            "post_start": "2025-07-01",
            "one_pair_per_document": True,
            "cell_quotas": {
                f"{source}/{format_name}": count
                for (source, format_name), count in CELL_QUOTAS.items()
            },
            "candidate_placement": "balanced_6_A_6_B",
        },
        "ranking_policy": {
            "scope": "within_document",
            "candidate_requires_target_marker": True,
            "candidate_requires_auxiliary_top_quartile_vote": True,
            "control_target_marker_count": 0,
            "same_length_band": False,
            "cjk_length_ratio": [0.7, 1.4],
            "maximum_sentence_count_difference": 2,
            "minimum_rank_sum_gap": 0.75,
            "minimum_content_bigram_jaccard": 0.015,
        },
        "decision_policy": {
            "minimum_decisive_pairs_for_discrimination": 4,
            "directional_enrichment_threshold": {
                "minimum_decisive_pairs": 8,
                "minimum_candidate_share_among_decisive": 0.75,
            },
            "minimum_candidate_wins_for_intervention": 4,
            "intervention_requires_directional_enrichment_threshold": True,
            "no_difference_is_not_a_win": True,
            "comments_used_for_selection": False,
        },
        "generation_diagnostics": {
            "handoff_document_count": len(metadata),
            "eligible_passage_count": sum(
                len(items) for items in passages_by_document.values()
            ),
            "pairable_document_count": len(pairable),
            "pairable_by_source_format": dict(
                sorted(
                    Counter(
                        f"{pair.source}/{metadata[pair.doc_id]['format_stratum']}"
                        for pair in pairable
                    ).items()
                )
            ),
            "selected_pair_count": len(selected),
            "selected_by_source": dict(
                sorted(Counter(pair.source for pair in selected).items())
            ),
            "selected_by_format": dict(
                sorted(
                    Counter(
                        str(metadata[pair.doc_id]["format_stratum"])
                        for pair in selected
                    ).items()
                )
            ),
            "candidate_side_counts": dict(sorted(Counter(candidate_sides).items())),
        },
        "pairs": manifest_pairs,
    }
    return tasks, answer_key, protocol


def write_json(path: Path, value: object) -> None:
    """Write stable pretty-printed UTF-8 JSON."""

    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the fresh-post reader-friction calibration."
    )
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    handoff_root = args.handoff_root.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {output_dir}")
    tasks, answer_key, protocol = build_artifacts(handoff_root, args.seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "tasks.json", tasks)
    write_json(output_dir / "answer_key.json", answer_key)
    write_json(output_dir / "protocol.json", protocol)
    (output_dir / "label_config.xml").write_text(
        LABEL_CONFIG, encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "protocol_version": PROTOCOL_VERSION,
                **protocol["generation_diagnostics"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
