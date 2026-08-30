"""Deterministic lexical-lattice measurements for Chinese boundary competition."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ASCII_RUN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+_.-]*")
UNKNOWN_CHARACTER_PENALTY = 0.01
LEXICON_SMOOTHING = 0.1
MAX_LEXICON_WORD_LENGTH = 8
AMBIGUOUS_BOUNDARY_LOW = 0.25
AMBIGUOUS_BOUNDARY_HIGH = 0.75
STRONG_BOUNDARY_PROBABILITY = 0.80
MIN_BRANCH_CONTEXT_COUNT = 5
MAX_BRANCH_FRAGMENT_LENGTH = 4


def cjk_text(text: str) -> str:
    """Return CJK characters in source order."""

    return "".join(CJK_RE.findall(text))


def _logsumexp(values: Iterable[float]) -> float:
    materialized = list(values)
    if not materialized:
        return -math.inf
    maximum = max(materialized)
    if maximum == -math.inf:
        return maximum
    return maximum + math.log(sum(math.exp(value - maximum) for value in materialized))


def _entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    return -sum(
        (count / total) * math.log(count / total)
        for count in counter.values()
        if count > 0
    )


@dataclass(frozen=True)
class LatticeEdge:
    start: int
    end: int
    token: str
    log_weight: float
    known: bool


@dataclass(frozen=True)
class BoundaryGap:
    position: int
    left_character: str
    right_character: str
    boundary_probability: float
    single_character_word_probability: float
    multi_character_start_probability: float
    left_branching_entropy: float
    right_branching_entropy: float
    left_accessor_variety: int
    right_accessor_variety: int


@dataclass(frozen=True)
class BoundaryCompetitionMeasurement:
    sequence: str
    scored_characters: int
    path_entropy: float
    normalized_path_entropy: float
    best_path_log_probability: float
    second_path_log_probability: float | None
    best_second_margin: float | None
    normalized_best_second_margin: float | None
    path_count: int
    ambiguous_gap_count: int
    unresolved_distance_to_head: int
    known_character_coverage: float
    multicharacter_coverage: float
    ascii_anchor_count: int
    abstention_reason: str | None
    best_path: tuple[str, ...]
    gaps: tuple[BoundaryGap, ...]


class SubtlexLexicon:
    """SUBTLEX-CH counts and a unigram segmentation lattice."""

    def __init__(
        self,
        word_counts: dict[str, int],
        character_counts: dict[str, int],
        total_word_count: int,
        total_character_count: int,
    ) -> None:
        self.word_counts = word_counts
        self.character_counts = character_counts
        self.total_word_count = total_word_count
        self.total_character_count = total_character_count
        self.vocabulary_size = len(word_counts)
        self.max_word_length = min(
            MAX_LEXICON_WORD_LENGTH,
            max((len(word) for word in word_counts), default=1),
        )
        self._multi_start_counts: Counter[str] = Counter()
        for word, count in word_counts.items():
            if len(word) > 1:
                self._multi_start_counts[word[0]] += count

    @classmethod
    def from_subtlex_files(
        cls,
        word_path: Path,
        character_path: Path,
    ) -> "SubtlexLexicon":
        """Load the public GB18030-encoded SUBTLEX-CH tables."""

        word_counts: dict[str, int] = {}
        character_counts: dict[str, int] = {}
        with word_path.open("r", encoding="gb18030", newline="") as handle:
            next(handle)
            next(handle)
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                word = (row.get("Word") or "").strip()
                if not word or not CJK_RE.search(word):
                    continue
                try:
                    count = int(row["WCount"])
                except (KeyError, TypeError, ValueError):
                    continue
                if count > 0:
                    word_counts[word] = count
        with character_path.open("r", encoding="gb18030", newline="") as handle:
            next(handle)
            next(handle)
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                character = (row.get("Character") or "").strip()
                if len(character) != 1 or not CJK_RE.fullmatch(character):
                    continue
                try:
                    count = int(row["CHRCount"])
                except (KeyError, TypeError, ValueError):
                    continue
                if count > 0:
                    character_counts[character] = count
        return cls(
            word_counts=word_counts,
            character_counts=character_counts,
            total_word_count=sum(word_counts.values()),
            total_character_count=sum(character_counts.values()),
        )

    def word_start_probabilities(self, character: str) -> tuple[float, float]:
        """Estimate single-word and multi-character-start probabilities."""

        single = self.word_counts.get(character, 0)
        multiple = self._multi_start_counts.get(character, 0)
        denominator = single + multiple
        if denominator <= 0:
            return 0.0, 0.0
        return single / denominator, multiple / denominator

    def _known_log_weight(self, count: int) -> float:
        denominator = self.total_word_count + (
            LEXICON_SMOOTHING * self.vocabulary_size
        )
        return math.log((count + LEXICON_SMOOTHING) / denominator)

    def _unknown_log_weight(self, character: str) -> float:
        count = self.character_counts.get(character, 1)
        probability = count / max(1, self.total_character_count)
        return math.log(max(probability * UNKNOWN_CHARACTER_PENALTY, 1e-300))

    def lattice(self, sequence: str) -> list[list[LatticeEdge]]:
        """Return outgoing edges for every character position."""

        edges: list[list[LatticeEdge]] = [[] for _ in range(len(sequence) + 1)]
        for start in range(len(sequence)):
            maximum = min(len(sequence), start + self.max_word_length)
            for end in range(start + 1, maximum + 1):
                token = sequence[start:end]
                count = self.word_counts.get(token)
                if count is None:
                    continue
                edges[start].append(
                    LatticeEdge(
                        start=start,
                        end=end,
                        token=token,
                        log_weight=self._known_log_weight(count),
                        known=True,
                    )
                )
            if not any(edge.end == start + 1 for edge in edges[start]):
                character = sequence[start]
                edges[start].append(
                    LatticeEdge(
                        start=start,
                        end=start + 1,
                        token=character,
                        log_weight=self._unknown_log_weight(character),
                        known=False,
                    )
                )
        return edges


class BranchingReference:
    """Character-context branching diagnostics from a fixed reference corpus."""

    def __init__(self, sentences: Iterable[str]) -> None:
        self.left_contexts: dict[str, Counter[str]] = defaultdict(Counter)
        self.right_contexts: dict[str, Counter[str]] = defaultdict(Counter)
        for raw_sentence in sentences:
            sentence = cjk_text(raw_sentence)
            for start in range(len(sentence)):
                for length in range(1, MAX_BRANCH_FRAGMENT_LENGTH + 1):
                    end = start + length
                    if end > len(sentence):
                        break
                    fragment = sentence[start:end]
                    if start > 0:
                        self.left_contexts[fragment][sentence[start - 1]] += 1
                    if end < len(sentence):
                        self.right_contexts[fragment][sentence[end]] += 1

    @staticmethod
    def _select_context(
        fragments: Iterable[str],
        table: dict[str, Counter[str]],
    ) -> Counter[str]:
        for fragment in fragments:
            counter = table.get(fragment, Counter())
            if sum(counter.values()) >= MIN_BRANCH_CONTEXT_COUNT:
                return counter
        return Counter()

    def gap_values(self, sequence: str, position: int) -> tuple[float, float, int, int]:
        """Return left/right entropy and accessor variety around one gap."""

        left_fragments = (
            sequence[max(0, position - length) : position]
            for length in range(MAX_BRANCH_FRAGMENT_LENGTH, 0, -1)
            if position - length >= 0
        )
        right_fragments = (
            sequence[position : min(len(sequence), position + length)]
            for length in range(MAX_BRANCH_FRAGMENT_LENGTH, 0, -1)
            if position + length <= len(sequence)
        )
        right_counter = self._select_context(left_fragments, self.right_contexts)
        left_counter = self._select_context(right_fragments, self.left_contexts)
        return (
            _entropy(left_counter),
            _entropy(right_counter),
            len(left_counter),
            len(right_counter),
        )


def _top_two_paths(
    edges: list[list[LatticeEdge]],
    length: int,
) -> tuple[tuple[float, tuple[str, ...]], tuple[float, tuple[str, ...]] | None]:
    paths: list[list[tuple[float, tuple[str, ...]]]] = [[] for _ in range(length + 1)]
    paths[0] = [(0.0, ())]
    for start in range(length):
        for score, tokens in paths[start]:
            for edge in edges[start]:
                paths[edge.end].append((score + edge.log_weight, tokens + (edge.token,)))
        for end in {edge.end for edge in edges[start]}:
            paths[end] = sorted(paths[end], key=lambda item: (-item[0], item[1]))[:2]
    ranked = sorted(paths[length], key=lambda item: (-item[0], item[1]))
    if not ranked:
        raise ValueError("Segmentation lattice has no complete path")
    return ranked[0], ranked[1] if len(ranked) > 1 else None


def measure_boundary_competition(
    text: str,
    lexicon: SubtlexLexicon,
    branching: BranchingReference | None = None,
) -> BoundaryCompetitionMeasurement:
    """Measure deterministic segmentation competition in one pre-head string."""

    sequence = cjk_text(text)
    ascii_anchor_count = len(ASCII_RUN_RE.findall(text))
    if len(sequence) < 2:
        return BoundaryCompetitionMeasurement(
            sequence=sequence,
            scored_characters=len(sequence),
            path_entropy=0.0,
            normalized_path_entropy=0.0,
            best_path_log_probability=0.0,
            second_path_log_probability=None,
            best_second_margin=None,
            normalized_best_second_margin=None,
            path_count=1,
            ambiguous_gap_count=0,
            unresolved_distance_to_head=len(sequence),
            known_character_coverage=0.0,
            multicharacter_coverage=0.0,
            ascii_anchor_count=ascii_anchor_count,
            abstention_reason="fewer_than_two_cjk_characters",
            best_path=tuple(sequence),
            gaps=(),
        )

    edges = lexicon.lattice(sequence)
    forward = [-math.inf] * (len(sequence) + 1)
    forward[0] = 0.0
    path_counts = [0] * (len(sequence) + 1)
    path_counts[0] = 1
    for start in range(len(sequence)):
        for edge in edges[start]:
            forward[edge.end] = _logsumexp(
                (forward[edge.end], forward[start] + edge.log_weight)
            )
            path_counts[edge.end] += path_counts[start]
    backward = [-math.inf] * (len(sequence) + 1)
    backward[len(sequence)] = 0.0
    for start in range(len(sequence) - 1, -1, -1):
        backward[start] = _logsumexp(
            edge.log_weight + backward[edge.end] for edge in edges[start]
        )
    log_partition = forward[len(sequence)]
    edge_posteriors: list[tuple[LatticeEdge, float]] = []
    for outgoing in edges[:-1]:
        for edge in outgoing:
            log_posterior = (
                forward[edge.start]
                + edge.log_weight
                + backward[edge.end]
                - log_partition
            )
            edge_posteriors.append((edge, math.exp(log_posterior)))
    expected_log_weight = sum(
        posterior * edge.log_weight for edge, posterior in edge_posteriors
    )
    path_entropy = max(0.0, log_partition - expected_log_weight)

    boundary_probabilities = [0.0] * (len(sequence) + 1)
    known_positions: set[int] = set()
    multicharacter_positions: set[int] = set()
    for edge, posterior in edge_posteriors:
        boundary_probabilities[edge.end] += posterior
        if edge.known:
            known_positions.update(range(edge.start, edge.end))
            if edge.end - edge.start > 1:
                multicharacter_positions.update(range(edge.start, edge.end))

    gap_rows: list[BoundaryGap] = []
    for position in range(1, len(sequence)):
        single_probability, multi_probability = lexicon.word_start_probabilities(
            sequence[position]
        )
        branch_values = (
            branching.gap_values(sequence, position)
            if branching is not None
            else (0.0, 0.0, 0, 0)
        )
        gap_rows.append(
            BoundaryGap(
                position=position,
                left_character=sequence[position - 1],
                right_character=sequence[position],
                boundary_probability=min(1.0, boundary_probabilities[position]),
                single_character_word_probability=single_probability,
                multi_character_start_probability=multi_probability,
                left_branching_entropy=branch_values[0],
                right_branching_entropy=branch_values[1],
                left_accessor_variety=branch_values[2],
                right_accessor_variety=branch_values[3],
            )
        )

    ambiguous_count = sum(
        AMBIGUOUS_BOUNDARY_LOW
        <= gap.boundary_probability
        <= AMBIGUOUS_BOUNDARY_HIGH
        for gap in gap_rows
    )
    strong_boundaries = [
        gap.position
        for gap in gap_rows
        if gap.boundary_probability >= STRONG_BOUNDARY_PROBABILITY
    ]
    last_strong_boundary = max(strong_boundaries, default=0)
    best, second = _top_two_paths(edges, len(sequence))
    margin = None if second is None else best[0] - second[0]
    known_coverage = len(known_positions) / len(sequence)
    abstention_reason = None
    if known_coverage < 0.80:
        abstention_reason = "known_character_coverage_below_0.80"
    return BoundaryCompetitionMeasurement(
        sequence=sequence,
        scored_characters=len(sequence),
        path_entropy=path_entropy,
        normalized_path_entropy=path_entropy / len(sequence),
        best_path_log_probability=best[0],
        second_path_log_probability=None if second is None else second[0],
        best_second_margin=margin,
        normalized_best_second_margin=(
            None if margin is None else margin / len(sequence)
        ),
        path_count=path_counts[len(sequence)],
        ambiguous_gap_count=ambiguous_count,
        unresolved_distance_to_head=len(sequence) - last_strong_boundary,
        known_character_coverage=known_coverage,
        multicharacter_coverage=len(multicharacter_positions) / len(sequence),
        ascii_anchor_count=ascii_anchor_count,
        abstention_reason=abstention_reason,
        best_path=best[1],
        gaps=tuple(gap_rows),
    )
