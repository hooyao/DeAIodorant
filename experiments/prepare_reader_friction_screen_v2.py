"""Prepare within-document pairs for deterministic friction enrichment."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from prepare_reader_friction_screen_v1 import (
        CJK_RE,
        LENGTH_BANDS,
        PRIOR_EXPOSED_DOC_IDS,
        SOURCES,
        is_eligible_passage,
        read_jsonl,
    )
except ModuleNotFoundError:  # pragma: no cover - supports module-style execution
    from experiments.prepare_reader_friction_screen_v1 import (
        CJK_RE,
        LENGTH_BANDS,
        PRIOR_EXPOSED_DOC_IDS,
        SOURCES,
        is_eligible_passage,
        read_jsonl,
    )

from deaiodorant.analysis.discourse_graph import (
    ABSTRACT_SHELLS,
    CONTRAST_FRAME_RE,
    EMPHATIC_FRAMES,
    META_FRAMES,
    REFERENTIAL_OPENINGS,
    SENTENCE_RE,
)


SCHEMA_VERSION = "deaiodorant-reader-friction-screen-2.0"
PROTOCOL_VERSION = "within-document-friction-enrichment-development-2.0"
DEFAULT_SEED = 2026082203
PAIRS_BY_SOURCE = {"infoq": 8, "jiqizhixin": 2}

SCREEN_V1_LINES = {
    "043edbbdbc99db8af9111e6c": 21,
    "32820b09ec8dd3edac07c47f": 19,
    "3729e9b9209e427e19e16173": 18,
    "3d2cea36287cf278258bee81": 50,
    "44f7193de55b94460aa94c83": 19,
    "48a9230fe1ff0bc5832f1e7c": 48,
    "552a90a3f24cf3a0a56ae17b": 30,
    "6d28870921e2543cc882d1a0": 4,
    "6ef00b4fadbccbd00b6f011c": 6,
    "78c8f407c8d04f43bd8907f5": 3,
    "82ff13fc3eaf733f81673809": 15,
    "8edbbf17c05ba07ef9db5e86": 90,
    "9f1d90b6ac15dd29465af213": 26,
    "b22137fdaff3ca8dc1d72095": 86,
    "c43904af3434cd97a9c1c348": 7,
    "ca20838db88af51d53f9d94f": 30,
    "cf88120b3afa80da3fc4c302": 20,
    "e7bdd871f45cc11e19b00f02": 7,
    "e89331895381298c2efeba0b": 22,
    "e9d24bfa7ebff01c6a08c4fb": 60,
    "f1f34167984d5e508d20f41c": 31,
    "f58aa7e373f216c50420cc5b": 16,
    "fad56cf7dd43cacc459a9b91": 23,
    "ff33cd9163c1c6a848fa040f": 50,
}
ALL_EXPOSED_DOC_IDS = PRIOR_EXPOSED_DOC_IDS

TARGET_MARKERS = tuple(
    sorted(
        set(EMPHATIC_FRAMES)
        | set(META_FRAMES)
        | {
            "也就是说",
            "正因如此",
            "相反",
            "反而",
            "因此",
            "因而",
            "然而",
            "不过",
            "所以",
            "由此",
        }
    )
)
SEPARATOR_CHARS = frozenset("，,、；;：:")
COMPLETE_END_RE = re.compile(r"[。！][”」』]?$|[.!][\"']?$")
PROFILE_RE = re.compile(
    r"(?:董事长|首席执行官|CEO|副总裁).{0,160}(?:曾任|曾就职|毕业|学位|MBA)"
)
RANK_FEATURES = (
    "target_marker_count",
    "abstract_shell_density",
    "separator_density",
    "mean_sentence_cjk",
    "referential_opening_ratio",
)
AUXILIARY_FEATURES = RANK_FEATURES[1:]


@dataclass(frozen=True)
class PassageFeatures:
    doc_id: str
    source: str
    published_at: str
    line_number: int
    passage: str
    passage_sha256: str
    cjk_chars: int
    length_band: str
    sentence_count: int
    target_marker_count: int
    abstract_shell_density: float
    separator_density: float
    mean_sentence_cjk: float
    referential_opening_ratio: float


@dataclass(frozen=True)
class RankedPassage:
    passage: PassageFeatures
    percentile_ranks: dict[str, float]
    auxiliary_top_quartile_votes: int
    rank_sum: float


@dataclass(frozen=True)
class Pair:
    pair_id: str
    source: str
    doc_id: str
    candidate: RankedPassage
    control: RankedPassage
    rank_gap: float
    content_bigram_jaccard: float


LABEL_CONFIG = """<View>
  <Header value="同文档阅读阻力比较"/>
  <Text name="instruction" value="下面两段来自同一篇文章。哪一段让你更不愿意继续读？只按第一感受选择；没有明显差别时请直接选第三项，不需要分析语言特征。"/>
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


def passage_features(
    *,
    doc_id: str,
    source: str,
    published_at: str,
    line_number: int,
    passage: str,
    cjk_chars: int,
    length_band: str,
) -> PassageFeatures:
    """Extract the frozen paragraph-level ranking features."""

    sentences = [item.strip() for item in SENTENCE_RE.findall(passage) if item.strip()]
    sentence_count = max(1, len(sentences))
    contrast_frames = sum(len(CONTRAST_FRAME_RE.findall(item)) for item in sentences)
    target_marker_count = contrast_frames + sum(
        passage.count(term) for term in TARGET_MARKERS
    )
    abstract_count = sum(passage.count(term) for term in ABSTRACT_SHELLS)
    separator_count = sum(char in SEPARATOR_CHARS for char in passage)
    referential_count = sum(
        sentence.startswith(REFERENTIAL_OPENINGS) for sentence in sentences
    )
    return PassageFeatures(
        doc_id=doc_id,
        source=source,
        published_at=published_at,
        line_number=line_number,
        passage=passage,
        passage_sha256=hashlib.sha256(passage.encode("utf-8")).hexdigest(),
        cjk_chars=cjk_chars,
        length_band=length_band,
        sentence_count=sentence_count,
        target_marker_count=target_marker_count,
        abstract_shell_density=abstract_count / cjk_chars,
        separator_density=separator_count / cjk_chars,
        mean_sentence_cjk=cjk_chars / sentence_count,
        referential_opening_ratio=referential_count / sentence_count,
    )


def collect_passages(pool_path: Path) -> dict[str, list[PassageFeatures]]:
    """Collect complete transition passages from previously unexposed documents."""

    by_document: dict[str, list[PassageFeatures]] = defaultdict(list)
    for record in read_jsonl(pool_path):
        doc_id = str(record["doc_id"])
        if record.get("period") != "transition" or doc_id in ALL_EXPOSED_DOC_IDS:
            continue
        source = str(record["source"])
        if source not in SOURCES:
            continue
        body_path = Path(str(record["body_path"]))
        body_bytes = body_path.read_bytes()
        observed_hash = hashlib.sha256(body_bytes).hexdigest()
        if observed_hash != record["content_hash"]:
            raise ValueError(f"Content hash mismatch for {doc_id}")
        body = body_bytes.decode("utf-8")
        for line_number, raw_line in enumerate(body.splitlines(), start=1):
            previous_screen_line = SCREEN_V1_LINES.get(doc_id)
            if (
                previous_screen_line is not None
                and abs(line_number - previous_screen_line) <= 1
            ):
                continue
            passage = raw_line.strip()
            eligible, cjk_chars, band = is_eligible_passage(passage)
            if not eligible or band is None:
                continue
            if not COMPLETE_END_RE.search(passage) or PROFILE_RE.search(passage):
                continue
            by_document[doc_id].append(
                passage_features(
                    doc_id=doc_id,
                    source=source,
                    published_at=str(record["published_at"]),
                    line_number=line_number,
                    passage=passage,
                    cjk_chars=cjk_chars,
                    length_band=band,
                )
            )
    return by_document


def percentile_ranks(values: list[float | int]) -> list[float]:
    """Return deterministic midranks scaled to the closed interval [0, 1]."""

    if len(values) <= 1:
        return [0.0] * len(values)
    ordered = sorted((value, index) for index, value in enumerate(values))
    output = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][0] == ordered[cursor][0]:
            end += 1
        midrank = (cursor + end - 1) / 2
        scaled = midrank / (len(values) - 1)
        for _, original_index in ordered[cursor:end]:
            output[original_index] = scaled
        cursor = end
    return output


def rank_document(passages: list[PassageFeatures]) -> list[RankedPassage]:
    """Rank passages only against other eligible passages in the same document."""

    ranks_by_feature = {
        feature: percentile_ranks([getattr(item, feature) for item in passages])
        for feature in RANK_FEATURES
    }
    ranked: list[RankedPassage] = []
    for index, passage in enumerate(passages):
        ranks = {feature: ranks_by_feature[feature][index] for feature in RANK_FEATURES}
        votes = sum(ranks[feature] >= 0.75 for feature in AUXILIARY_FEATURES)
        ranked.append(
            RankedPassage(
                passage=passage,
                percentile_ranks=ranks,
                auxiliary_top_quartile_votes=votes,
                rank_sum=sum(ranks.values()),
            )
        )
    return ranked


def stable_tiebreak(seed: int, passage: PassageFeatures) -> str:
    """Return a stable opaque tiebreak key unrelated to paragraph text quality."""

    return hashlib.sha256(
        f"{seed}:{passage.doc_id}:{passage.line_number}".encode("ascii")
    ).hexdigest()


def content_bigram_jaccard(left: str, right: str) -> float:
    """Measure local topic overlap with deterministic CJK character bigrams."""

    def bigrams(text: str) -> set[str]:
        chars = CJK_RE.findall(text)
        return {"".join(chars[index : index + 2]) for index in range(len(chars) - 1)}

    left_bigrams = bigrams(left)
    right_bigrams = bigrams(right)
    union = left_bigrams | right_bigrams
    return len(left_bigrams & right_bigrams) / len(union) if union else 0.0


def choose_document_pair(
    passages: list[PassageFeatures], seed: int
) -> Pair | None:
    """Choose one ranked candidate and a matched low-ranked control."""

    if len(passages) < 4:
        return None
    ranked = rank_document(passages)
    candidate_options = [
        item
        for item in ranked
        if item.passage.target_marker_count > 0
        and item.percentile_ranks["target_marker_count"] >= 0.75
        and item.auxiliary_top_quartile_votes >= 1
    ]
    candidate_options.sort(
        key=lambda item: (
            -item.auxiliary_top_quartile_votes,
            -item.rank_sum,
            -item.passage.target_marker_count,
            stable_tiebreak(seed, item.passage),
        )
    )
    for candidate in candidate_options:
        controls = [
            (
                item,
                content_bigram_jaccard(
                    candidate.passage.passage, item.passage.passage
                ),
            )
            for item in ranked
            if item.passage.target_marker_count == 0
            and item.passage.length_band == candidate.passage.length_band
            and abs(
                item.passage.sentence_count - candidate.passage.sentence_count
            )
            <= 1
            and 0.8
            <= item.passage.cjk_chars / candidate.passage.cjk_chars
            <= 1.25
            and abs(item.passage.line_number - candidate.passage.line_number) >= 2
            and candidate.rank_sum - item.rank_sum >= 1.0
        ]
        controls = [item for item in controls if item[1] >= 0.02]
        controls.sort(
            key=lambda match: (
                -match[1],
                match[0].rank_sum,
                abs(
                    match[0].passage.cjk_chars - candidate.passage.cjk_chars
                ),
                abs(
                    match[0].passage.sentence_count
                    - candidate.passage.sentence_count
                ),
                stable_tiebreak(seed, match[0].passage),
            )
        )
        if not controls:
            continue
        control, similarity = controls[0]
        passage = candidate.passage
        return Pair(
            pair_id=f"friction-v2-{passage.doc_id[:8]}",
            source=passage.source,
            doc_id=passage.doc_id,
            candidate=candidate,
            control=control,
            rank_gap=candidate.rank_sum - control.rank_sum,
            content_bigram_jaccard=similarity,
        )
    return None


def select_pairs(
    passages_by_document: dict[str, list[PassageFeatures]], seed: int
) -> list[Pair]:
    """Select a source-balanced set of one pair per document."""

    eligible_pairs = [
        pair
        for passages in passages_by_document.values()
        if (pair := choose_document_pair(passages, seed)) is not None
    ]
    selected: list[Pair] = []
    for source in SOURCES:
        source_pairs = [pair for pair in eligible_pairs if pair.source == source]
        source_pairs.sort(
            key=lambda pair: (
                -pair.candidate.auxiliary_top_quartile_votes,
                -pair.rank_gap,
                -pair.candidate.passage.target_marker_count,
                stable_tiebreak(seed, pair.candidate.passage),
            )
        )
        required_pairs = PAIRS_BY_SOURCE[source]
        if len(source_pairs) < required_pairs:
            raise ValueError(
                f"Not enough within-document pairs for {source}: {len(source_pairs)}"
            )
        selected.extend(source_pairs[:required_pairs])
    return selected


def ranked_passage_manifest(item: RankedPassage) -> dict[str, object]:
    """Serialize features and within-document ranks without duplicating text."""

    passage = asdict(item.passage)
    passage.pop("passage")
    return {
        **passage,
        "percentile_ranks": item.percentile_ranks,
        "auxiliary_top_quartile_votes": item.auxiliary_top_quartile_votes,
        "rank_sum": item.rank_sum,
    }


def build_artifacts(
    pool_path: Path, seed: int
) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object]]:
    """Build blinded Label Studio tasks, answer key, and frozen protocol."""

    passages_by_document = collect_passages(pool_path)
    eligible_pairs = [
        pair
        for passages in passages_by_document.values()
        if (pair := choose_document_pair(passages, seed)) is not None
    ]
    selected = select_pairs(passages_by_document, seed)

    rng = random.Random(seed)
    rng.shuffle(selected)
    candidate_sides = ["A"] * (len(selected) // 2) + ["B"] * (
        len(selected) - len(selected) // 2
    )
    rng.shuffle(candidate_sides)

    tasks: list[dict[str, object]] = []
    answer_pairs: list[dict[str, object]] = []
    manifest_pairs: list[dict[str, object]] = []
    for task_number, (pair, candidate_side) in enumerate(
        zip(selected, candidate_sides, strict=True), start=1
    ):
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
                    "published_at": pair.candidate.passage.published_at,
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
                "doc_id": pair.doc_id,
                "candidate": ranked_passage_manifest(pair.candidate),
                "control": ranked_passage_manifest(pair.control),
                "rank_gap": pair.rank_gap,
                "content_bigram_jaccard": pair.content_bigram_jaccard,
            }
        )

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
        "role": "development_enrichment_test_not_validation",
        "reader_question": (
            "Which passage from the same document makes the reader less willing "
            "to continue?"
        ),
        "source_policy": {
            "period": "transition",
            "sources": list(SOURCES),
            "all_prior_reader_exposed_passages_excluded": True,
            "prior_screen_documents_may_contribute_unseen_passages": True,
            "one_pair_per_document": True,
        },
        "ranking_policy": {
            "scope": "within_document",
            "features": list(RANK_FEATURES),
            "target_markers": list(TARGET_MARKERS),
            "complete_contrast_pattern": CONTRAST_FRAME_RE.pattern,
            "candidate_requires_target_marker": True,
            "candidate_requires_auxiliary_top_quartile_votes": 1,
            "control_target_marker_count": 0,
            "minimum_rank_sum_gap": 1.0,
            "same_length_band": True,
            "cjk_length_ratio": [0.8, 1.25],
            "maximum_sentence_count_difference": 1,
            "minimum_line_distance": 2,
            "minimum_content_bigram_jaccard": 0.02,
        },
        "decision_policy": {
            "candidate_intervention_eligibility": (
                "The candidate is explicitly chosen as more discouraging to read."
            ),
            "minimum_candidate_wins_for_intervention": 4,
            "intervention_requires_directional_enrichment_threshold": True,
            "directional_enrichment_threshold": {
                "minimum_decisive_pairs": 8,
                "minimum_candidate_share_among_decisive": 0.75,
            },
            "no_difference_is_not_a_win": True,
            "comments_used_for_selection": False,
        },
        "generation_diagnostics": {
            "eligible_document_count": len(passages_by_document),
            "eligible_passage_count": sum(
                len(items) for items in passages_by_document.values()
            ),
            "pairable_document_count": len(eligible_pairs),
            "pairable_by_source": dict(
                sorted(Counter(pair.source for pair in eligible_pairs).items())
            ),
            "selected_pair_count": len(selected),
            "selected_by_source": dict(
                sorted(Counter(pair.source for pair in selected).items())
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {args.output_dir}")
    tasks, answer_key, protocol = build_artifacts(args.pool, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "tasks.json", tasks)
    write_json(args.output_dir / "answer_key.json", answer_key)
    write_json(args.output_dir / "protocol.json", protocol)
    (args.output_dir / "label_config.xml").write_text(
        LABEL_CONFIG, encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir.resolve()),
                "protocol_version": PROTOCOL_VERSION,
                **protocol["generation_diagnostics"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
