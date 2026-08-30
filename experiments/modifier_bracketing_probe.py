"""Probe word-level modifier-bracketing competition with cross-fitted counts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from deaiodorant.analysis.stanza_backend import (
    PROCESSORS,
    _configure_determinism,
    _load_stanza,
    _model_fingerprint,
)
from deaiodorant.analysis.syntax import DependencyToken
from nominal_chain_integration_probe import (
    BOUNDARY_FORMS,
    complete_prose_passages,
    parsed_sentence,
    render_tokens,
    sentence_candidates,
)


SCHEMA_VERSION = "deaiodorant-modifier-bracketing-probe-0.2"
PROTOCOL_VERSION = "modifier-bracketing-probe-0.2"
SEED = 2026083102
CONTENT_POS = frozenset({"NOUN", "PROPN", "ADJ", "NUM", "X"})
COORDINATE_FORMS = frozenset({"、", "和", "与", "及", "或", "以及"})
GENERIC_ASCII_TERMS = frozenset({"ai", "agent", "aigc", "gpt", "llm"})
ASCII_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+_.\-/]*$")
ASCII_RUN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+_.\-/]*")
MIN_TARGET_TOKENS = 4
MAX_TARGET_TOKENS = 10
ASSOCIATION_WINDOW = 4
SMOOTHING = 0.1
FAMILIAR_DOCUMENTS = 5
FAMILIAR_SOURCES = 2
HIGH_ENTROPY_PERCENTILE = 0.80
HIGH_MARGIN_PERCENTILE = 0.20
HIGH_FAMILIAR_FRACTION = 0.80
HIGH_MIN_WEAK_ATTACHMENTS = 2
EXAMPLE_ENTROPY_PERCENTILE = 0.50
EXAMPLE_MARGIN_PERCENTILE = 0.50
REQUIRED_HIGH_DOCUMENTS = 8
REQUIRED_HIGH_SOURCES = 3
MAX_SELECTED_PER_SOURCE = 3
REQUIRED_UNANCHORED = 4
NUMERICAL_MARGIN_TOLERANCE = 1e-12


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def normalize_token(token: DependencyToken) -> str:
    value = token.lemma if token.lemma not in {"", "_"} else token.form
    return value.casefold()


def content_tokens(tokens: Iterable[DependencyToken]) -> list[DependencyToken]:
    return [token for token in tokens if token.upos in CONTENT_POS]


def percentile_midrank(value: float, reference: list[float]) -> float:
    lower = sum(item < value for item in reference)
    equal = sum(item == value for item in reference)
    return (lower + 0.5 * equal) / len(reference)


def nearest_rank_quantile(reference: list[float], probability: float) -> float:
    """Return the preregistered nearest-rank empirical quantile."""

    if not reference:
        raise ValueError("Cannot compute a quantile against an empty reference")
    ordered = sorted(reference)
    index = max(0, math.ceil(probability * len(ordered)) - 1)
    return ordered[index]


def logsumexp(values: Iterable[float]) -> float:
    materialized = list(values)
    maximum = max(materialized)
    return maximum + math.log(sum(math.exp(value - maximum) for value in materialized))


@dataclass(frozen=True)
class TargetToken:
    form: str
    lemma: str
    upos: str
    token_id: int


@dataclass(frozen=True)
class Bracketing:
    head_index: int
    score: float
    text: str
    attachments: tuple[tuple[int, int], ...]


class AssociationCorpus:
    """Per-document counts that support leave-one-document-out association."""

    def __init__(self) -> None:
        self.token_counts: Counter[str] = Counter()
        self.token_counts_by_document: dict[str, Counter[str]] = defaultdict(Counter)
        self.token_documents: dict[str, set[str]] = defaultdict(set)
        self.token_sources: dict[str, set[str]] = defaultdict(set)
        self.outgoing_counts: Counter[str] = Counter()
        self.outgoing_by_document: dict[str, Counter[str]] = defaultdict(Counter)
        self.pair_counts: Counter[tuple[str, str]] = Counter()
        self.pair_counts_by_document: dict[
            str, Counter[tuple[str, str]]
        ] = defaultdict(Counter)
        self.pair_documents: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.pair_sources: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.adjacent_counts: Counter[tuple[str, str]] = Counter()
        self.adjacent_by_document: dict[
            str, Counter[tuple[str, str]]
        ] = defaultdict(Counter)
        self.coordinate_counts: Counter[tuple[str, str]] = Counter()
        self.coordinate_by_document: dict[
            str, Counter[tuple[str, str]]
        ] = defaultdict(Counter)
        self.document_sources: dict[str, str] = {}
        self.sentence_sequences: list[tuple[str, str, tuple[str, ...]]] = []
        self._vocabulary_without_cache: dict[str | None, int] = {}
        self._pair_support_cache: dict[
            tuple[str, str, str | None], dict[str, float | int]
        ] = {}

    def add_sentence(
        self,
        document_id: str,
        source: str,
        tokens: list[DependencyToken],
    ) -> None:
        self.document_sources[document_id] = source
        filtered = content_tokens(tokens)
        sequence = tuple(normalize_token(token) for token in filtered)
        if not sequence:
            return
        self.sentence_sequences.append((document_id, source, sequence))
        for lemma in sequence:
            self.token_counts[lemma] += 1
            self.token_counts_by_document[document_id][lemma] += 1
            self.token_documents[lemma].add(document_id)
            self.token_sources[lemma].add(source)
        for left_index, modifier in enumerate(sequence):
            for right_index in range(
                left_index + 1,
                min(len(sequence), left_index + ASSOCIATION_WINDOW + 1),
            ):
                head = sequence[right_index]
                pair = (modifier, head)
                self.outgoing_counts[modifier] += 1
                self.outgoing_by_document[document_id][modifier] += 1
                self.pair_counts[pair] += 1
                self.pair_counts_by_document[document_id][pair] += 1
                self.pair_documents[pair].add(document_id)
                self.pair_sources[pair].add(source)
                if right_index == left_index + 1:
                    self.adjacent_counts[pair] += 1
                    self.adjacent_by_document[document_id][pair] += 1
        for index, token in enumerate(tokens):
            if token.form not in COORDINATE_FORMS and token.upos != "CCONJ":
                continue
            left = next(
                (
                    candidate
                    for candidate in reversed(tokens[:index])
                    if candidate.upos in CONTENT_POS
                ),
                None,
            )
            right = next(
                (
                    candidate
                    for candidate in tokens[index + 1 :]
                    if candidate.upos in CONTENT_POS
                ),
                None,
            )
            if left is not None and right is not None:
                pair = (normalize_token(left), normalize_token(right))
                self.coordinate_counts[pair] += 1
                self.coordinate_by_document[document_id][pair] += 1

    def vocabulary_size_without(self, document_id: str | None) -> int:
        cached = self._vocabulary_without_cache.get(document_id)
        if cached is not None:
            return cached
        if document_id is None:
            value = len(self.token_counts)
        else:
            value = sum(
                any(candidate != document_id for candidate in documents)
                for documents in self.token_documents.values()
            )
        self._vocabulary_without_cache[document_id] = value
        return value

    def token_support(self, lemma: str, document_id: str | None) -> dict[str, int]:
        documents = self.token_documents.get(lemma, set())
        filtered_documents = {
            candidate for candidate in documents if candidate != document_id
        }
        sources = {
            self.document_sources[candidate] for candidate in filtered_documents
        }
        return {
            "count": self.token_counts.get(lemma, 0)
            - (
                self.token_counts_by_document[document_id].get(lemma, 0)
                if document_id is not None
                else 0
            ),
            "document_frequency": len(filtered_documents),
            "source_frequency": len(sources),
        }

    def pair_support(
        self,
        modifier: str,
        head: str,
        document_id: str | None,
    ) -> dict[str, float | int]:
        cache_key = (modifier, head, document_id)
        cached = self._pair_support_cache.get(cache_key)
        if cached is not None:
            return cached
        pair = (modifier, head)
        pair_count = self.pair_counts.get(pair, 0)
        outgoing = self.outgoing_counts.get(modifier, 0)
        adjacent = self.adjacent_counts.get(pair, 0)
        coordinate = self.coordinate_counts.get(pair, 0)
        if document_id is not None:
            pair_count -= self.pair_counts_by_document[document_id].get(pair, 0)
            outgoing -= self.outgoing_by_document[document_id].get(modifier, 0)
            adjacent -= self.adjacent_by_document[document_id].get(pair, 0)
            coordinate -= self.coordinate_by_document[document_id].get(pair, 0)
        documents = {
            candidate
            for candidate in self.pair_documents.get(pair, set())
            if candidate != document_id
        }
        sources = {self.document_sources[candidate] for candidate in documents}
        vocabulary_size = max(1, self.vocabulary_size_without(document_id))
        probability = (pair_count + SMOOTHING) / (
            outgoing + SMOOTHING * vocabulary_size
        )
        output: dict[str, float | int] = {
            "ordered_pair_count": pair_count,
            "outgoing_pair_count": outgoing,
            "adjacent_pair_count": adjacent,
            "coordinate_count": coordinate,
            "document_frequency": len(documents),
            "source_frequency": len(sources),
            "conditional_probability": probability,
            "log_conditional_probability": math.log(probability),
        }
        self._pair_support_cache[cache_key] = output
        return output

    def exact_sequence_support(
        self,
        sequence: tuple[str, ...],
        document_id: str | None,
    ) -> dict[str, int]:
        documents: set[str] = set()
        sources: set[str] = set()
        count = 0
        width = len(sequence)
        for candidate_document, source, sentence in self.sentence_sequences:
            if candidate_document == document_id or len(sentence) < width:
                continue
            matched = False
            for start in range(len(sentence) - width + 1):
                if sentence[start : start + width] == sequence:
                    count += 1
                    matched = True
            if matched:
                documents.add(candidate_document)
                sources.add(source)
        return {
            "count": count,
            "document_frequency": len(documents),
            "source_frequency": len(sources),
        }


def enumerate_bracketings(
    tokens: tuple[TargetToken, ...],
    corpus: AssociationCorpus,
    document_id: str | None,
) -> list[Bracketing]:
    """Enumerate full binary right-headed bracketings and their scores."""

    @lru_cache(maxsize=None)
    def build(start: int, end: int) -> tuple[Bracketing, ...]:
        if end - start == 1:
            return (
                Bracketing(
                    head_index=start,
                    score=0.0,
                    text=tokens[start].form,
                    attachments=(),
                ),
            )
        output: list[Bracketing] = []
        for split in range(start + 1, end):
            for left in build(start, split):
                for right in build(split, end):
                    support = corpus.pair_support(
                        tokens[left.head_index].lemma,
                        tokens[right.head_index].lemma,
                        document_id,
                    )
                    output.append(
                        Bracketing(
                            head_index=right.head_index,
                            score=(
                                left.score
                                + right.score
                                + float(support["log_conditional_probability"])
                            ),
                            text=f"({left.text} {right.text})",
                            attachments=(
                                *left.attachments,
                                *right.attachments,
                                (left.head_index, right.head_index),
                            ),
                        )
                    )
        return tuple(output)

    return list(build(0, len(tokens)))


def measure_candidate(
    tokens: tuple[TargetToken, ...],
    corpus: AssociationCorpus,
    document_id: str | None,
) -> dict[str, Any]:
    if not MIN_TARGET_TOKENS <= len(tokens) <= MAX_TARGET_TOKENS:
        return {
            "abstention_reason": "target_token_count_outside_4_10",
            "target_token_count": len(tokens),
        }
    bracketings = enumerate_bracketings(tokens, corpus, document_id)
    bracketings.sort(key=lambda item: (-item.score, item.text))
    log_partition = logsumexp(item.score for item in bracketings)
    probabilities = [math.exp(item.score - log_partition) for item in bracketings]
    entropy = -sum(
        probability * math.log(probability)
        for probability in probabilities
        if probability > 0
    )
    normalized_entropy = (
        entropy / math.log(len(bracketings)) if len(bracketings) > 1 else 0.0
    )
    best = bracketings[0]
    second = bracketings[1] if len(bracketings) > 1 else None
    margin = None if second is None else (best.score - second.score) / (len(tokens) - 1)
    if margin is not None and abs(margin) < NUMERICAL_MARGIN_TOLERANCE:
        margin = 0.0

    attachment_posteriors: Counter[tuple[int, int]] = Counter()
    for bracketing, probability in zip(bracketings, probabilities, strict=True):
        for attachment in bracketing.attachments:
            attachment_posteriors[attachment] += probability
    best_attachment_rows: list[dict[str, Any]] = []
    weak_attachment_count = 0
    for modifier_index, head_index in best.attachments:
        support = corpus.pair_support(
            tokens[modifier_index].lemma,
            tokens[head_index].lemma,
            document_id,
        )
        weak = (
            int(support["document_frequency"]) <= 1
            and int(support["source_frequency"]) <= 1
        )
        weak_attachment_count += int(weak)
        best_attachment_rows.append(
            {
                "modifier_index": modifier_index,
                "modifier": tokens[modifier_index].form,
                "head_index": head_index,
                "head": tokens[head_index].form,
                "posterior": attachment_posteriors[(modifier_index, head_index)],
                "weak_cross_document_support": weak,
                **support,
            }
        )

    token_support_rows = [
        {
            "token": token.form,
            "lemma": token.lemma,
            **corpus.token_support(token.lemma, document_id),
        }
        for token in tokens
    ]
    familiar_count = sum(
        row["document_frequency"] >= FAMILIAR_DOCUMENTS
        and row["source_frequency"] >= FAMILIAR_SOURCES
        for row in token_support_rows
    )
    exact_support = corpus.exact_sequence_support(
        tuple(token.lemma for token in tokens), document_id
    )
    return {
        "abstention_reason": None,
        "target_token_count": len(tokens),
        "bracketing_count": len(bracketings),
        "tree_entropy": entropy,
        "normalized_tree_entropy": normalized_entropy,
        "best_second_margin_per_attachment": margin,
        "best_score": best.score,
        "second_score": None if second is None else second.score,
        "best_bracketing": best.text,
        "best_bracketing_probability": probabilities[0],
        "weak_best_attachment_count": weak_attachment_count,
        "familiar_token_fraction": familiar_count / len(tokens),
        "token_support": token_support_rows,
        "best_attachments": best_attachment_rows,
        "exact_sequence_support": exact_support,
    }


def candidate_key(row: dict[str, Any]) -> tuple[str, int, int, int, int]:
    return (
        row["doc_id"],
        int(row["line_number"]),
        int(row["sentence_index"]),
        int(row["left_boundary_token_id"]),
        int(row["head_token_id"]),
    )


def target_tokens(
    tokens: list[DependencyToken],
    candidate: dict[str, Any],
) -> tuple[tuple[TargetToken, ...] | None, str | None]:
    span = [
        token
        for token in tokens
        if int(candidate["left_boundary_token_id"])
        <= token.token_id
        <= int(candidate["head_token_id"])
        and token.upos not in {"PUNCT", "SYM"}
    ]
    if any(token.upos not in CONTENT_POS for token in span):
        return None, "noncontent_token_inside_target"
    if any(token.upos == "VERB" for token in span[:-1]):
        return None, "verb_inside_prehead_target"
    if any(token.form in BOUNDARY_FORMS or token.upos == "CCONJ" for token in span[:-1]):
        return None, "overt_boundary_inside_target"
    output = tuple(
        TargetToken(
            form=token.form,
            lemma=normalize_token(token),
            upos=token.upos,
            token_id=token.token_id,
        )
        for token in span
    )
    return output, None


def quoted_anchor(sentence: str, phrase: str) -> bool:
    compact_phrase = re.sub(r"\s+", "", phrase)
    for pattern in (r"《([^》]+)》", r"“([^”]+)”", r'"([^"]+)"'):
        for matched in re.findall(pattern, sentence):
            compact_match = re.sub(r"\s+", "", matched)
            if compact_phrase in compact_match or compact_match in compact_phrase:
                return True
    return False


def parse_corpus(
    nlp: Any,
    handoffs: list[tuple[str, str]],
    candidates: list[dict[str, Any]],
) -> tuple[
    AssociationCorpus,
    dict[tuple[str, int, int, int, int], tuple[TargetToken, ...]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    int,
    set[str],
]:
    lookup = {candidate_key(row): row for row in candidates}
    targets: dict[tuple[str, int, int, int, int], tuple[TargetToken, ...]] = {}
    failures: list[dict[str, Any]] = []
    corpus_identity: list[dict[str, Any]] = []
    association = AssociationCorpus()
    passage_count = 0
    covered_documents: set[str] = set()

    for raw_root, role in handoffs:
        root = Path(raw_root).resolve()
        index_path = root / "documents.jsonl"
        records = [
            json.loads(line)
            for line in index_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        selected = [row for row in records if row.get("recommended_role") == role]
        corpus_identity.append(
            {
                "root": str(root),
                "role": role,
                "documents": len(selected),
                "manifest_sha256": sha256(root / "manifest.json"),
                "documents_sha256": sha256(index_path),
            }
        )
        for document_index, record in enumerate(selected, start=1):
            document_id = record["doc_id"]
            body_path = root / record["body_path"]
            body = body_path.read_text(encoding="utf-8", errors="strict").rstrip("\n")
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != record["content_hash"]:
                raise ValueError(f"Body hash mismatch for {document_id}")
            print(
                f"[modifier-bracketing] {role} {document_index}/{len(selected)} "
                f"{document_id}",
                flush=True,
            )
            passages = complete_prose_passages(body.splitlines())
            if passages:
                covered_documents.add(document_id)
            for line_number, passage in passages:
                passage_count += 1
                parsed = nlp(passage)
                for sentence_index, sentence in enumerate(parsed.sentences, start=1):
                    tokens = parsed_sentence(sentence)
                    association.add_sentence(document_id, record["source"], tokens)
                    generated = {
                        (
                            int(row["left_boundary_token_id"]),
                            int(row["head_token_id"]),
                        ): row
                        for row in sentence_candidates(tokens)
                    }
                    requested_keys = [
                        key
                        for key in lookup
                        if key[0] == document_id
                        and key[1] == line_number
                        and key[2] == sentence_index
                    ]
                    for key in requested_keys:
                        original = lookup[key]
                        regenerated = generated.get((key[3], key[4]))
                        if regenerated is None:
                            failures.append(
                                {
                                    "candidate_key": key,
                                    "reason": "candidate_not_regenerated",
                                    "fatal_alignment_failure": True,
                                }
                            )
                            continue
                        exact_fields = (
                            "head",
                            "prehead_text",
                            "prehead_lexical_tokens",
                            "phrase",
                            "sentence",
                        )
                        mismatches = [
                            field
                            for field in exact_fields
                            if regenerated[field] != original[field]
                        ]
                        if mismatches:
                            failures.append(
                                {
                                    "candidate_key": key,
                                    "reason": "regenerated_fields_differ",
                                    "fields": mismatches,
                                    "fatal_alignment_failure": True,
                                }
                            )
                            continue
                        extracted, reason = target_tokens(tokens, original)
                        if reason is not None or extracted is None:
                            failures.append(
                                {
                                    "candidate_key": key,
                                    "reason": reason,
                                    "fatal_alignment_failure": False,
                                }
                            )
                            continue
                        targets[key] = extracted
    return (
        association,
        targets,
        failures,
        corpus_identity,
        passage_count,
        covered_documents,
    )


def anchor_profile(
    candidate: dict[str, Any],
    tokens: tuple[TargetToken, ...],
) -> dict[str, bool]:
    return {
        "proper_name": any(
            token.upos == "PROPN"
            and not (ASCII_RE.fullmatch(token.form) and token.lemma in GENERIC_ASCII_TERMS)
            for token in tokens
        ),
        "numeric": any(token.upos == "NUM" for token in tokens),
        "ascii": any(ASCII_RE.fullmatch(token.form) for token in tokens),
        "quoted_title": quoted_anchor(candidate["sentence"], candidate["phrase"]),
    }


def any_anchor(profile: dict[str, bool]) -> bool:
    return any(profile.values())


def score_rows(
    candidates: list[dict[str, Any]],
    targets: dict[tuple[str, int, int, int, int], tuple[TargetToken, ...]],
    failures: list[dict[str, Any]],
    corpus: AssociationCorpus,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    failure_reasons = {
        tuple(failure["candidate_key"]): failure["reason"] for failure in failures
    }
    output: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        key = candidate_key(candidate)
        tokens = targets.get(key)
        if tokens is None:
            measurement = {
                "abstention_reason": failure_reasons.get(
                    key, "target_not_found_after_parse"
                )
            }
            profile = {
                "proper_name": bool(candidate.get("proper_anchors")),
                "numeric": bool(candidate.get("numeric_anchors")),
                "ascii": bool(ASCII_RUN_RE.search(candidate["prehead_text"])),
                "quoted_title": quoted_anchor(
                    candidate["sentence"], candidate["phrase"]
                ),
            }
            token_rows: list[dict[str, Any]] = []
        else:
            measurement = measure_candidate(tokens, corpus, candidate["doc_id"])
            profile = anchor_profile(candidate, tokens)
            token_rows = [
                {
                    "form": token.form,
                    "lemma": token.lemma,
                    "upos": token.upos,
                    "token_id": token.token_id,
                }
                for token in tokens
            ]
        output.append(
            {
                **candidate,
                "bracketing_candidate_id": f"mb-{index:03d}",
                "target_tokens": token_rows,
                "anchor_profile": profile,
                "has_anchor": any_anchor(profile),
                "measurement": measurement,
            }
        )
    scorable = [
        row for row in output if row["measurement"].get("abstention_reason") is None
    ]
    entropy_reference = [
        float(row["measurement"]["normalized_tree_entropy"]) for row in scorable
    ]
    margin_reference = [
        float(row["measurement"]["best_second_margin_per_attachment"])
        for row in scorable
    ]
    cutoffs = {
        "high_entropy_p80": nearest_rank_quantile(
            entropy_reference, HIGH_ENTROPY_PERCENTILE
        ),
        "high_margin_p20": nearest_rank_quantile(
            margin_reference, HIGH_MARGIN_PERCENTILE
        ),
        "example_entropy_median": nearest_rank_quantile(
            entropy_reference, EXAMPLE_ENTROPY_PERCENTILE
        ),
        "example_margin_median": nearest_rank_quantile(
            margin_reference, EXAMPLE_MARGIN_PERCENTILE
        ),
    }
    for row in output:
        measurement = row["measurement"]
        if measurement.get("abstention_reason") is not None:
            row["entropy_percentile"] = None
            row["margin_percentile"] = None
            row["high_bracketing_competition"] = False
            continue
        entropy_percentile = percentile_midrank(
            float(measurement["normalized_tree_entropy"]), entropy_reference
        )
        margin_percentile = percentile_midrank(
            float(measurement["best_second_margin_per_attachment"]),
            margin_reference,
        )
        row["entropy_percentile"] = entropy_percentile
        row["margin_percentile"] = margin_percentile
        row["high_bracketing_competition"] = bool(
            measurement["normalized_tree_entropy"]
            >= cutoffs["high_entropy_p80"]
            and measurement["best_second_margin_per_attachment"]
            <= cutoffs["high_margin_p20"]
            and measurement["familiar_token_fraction"]
            >= HIGH_FAMILIAR_FRACTION
            and measurement["weak_best_attachment_count"]
            >= HIGH_MIN_WEAK_ATTACHMENTS
        )
    return output, cutoffs


def select_high_documents(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["high_bracketing_competition"]:
            grouped[row["doc_id"]].append(row)
    per_document = [
        sorted(
            grouped[document_id],
            key=lambda row: (
                -float(row["entropy_percentile"]),
                float(row["margin_percentile"]),
                -int(row["measurement"]["weak_best_attachment_count"]),
                hashlib.sha256(
                    f"{SEED}|{row['bracketing_candidate_id']}".encode("utf-8")
                ).hexdigest(),
            ),
        )[0]
        for document_id in sorted(grouped)
    ]
    ranked = sorted(
        per_document,
        key=lambda row: (
            -float(row["entropy_percentile"]),
            float(row["margin_percentile"]),
            -int(row["measurement"]["weak_best_attachment_count"]),
            hashlib.sha256(
                f"{SEED}|{row['bracketing_candidate_id']}".encode("utf-8")
            ).hexdigest(),
        ),
    )
    selected: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    for row in ranked:
        if source_counts[row["source"]] >= MAX_SELECTED_PER_SOURCE:
            continue
        selected.append(row)
        source_counts[row["source"]] += 1
        if len(selected) >= REQUIRED_HIGH_DOCUMENTS:
            break
    return selected


def example_measurement(nlp: Any, corpus: AssociationCorpus) -> dict[str, Any]:
    text = "这个 AI 算力池面向 AI 原生时代全新算力服务需求。"
    document = nlp(text)
    located: list[tuple[dict[str, Any], list[DependencyToken]]] = []
    for sentence in document.sentences:
        tokens = parsed_sentence(sentence)
        for candidate in sentence_candidates(tokens):
            located.append((candidate, tokens))
    if len(located) != 1:
        return {
            "text": text,
            "abstention_reason": "reader_example_not_uniquely_localized",
            "localized_candidates": len(located),
        }
    candidate, tokens = located[0]
    extracted, reason = target_tokens(tokens, candidate)
    if extracted is None or reason is not None:
        return {
            "text": text,
            "candidate": candidate,
            "abstention_reason": reason,
        }
    measurement = measure_candidate(extracted, corpus, None)
    return {
        "text": text,
        "candidate": candidate,
        "target_tokens": [
            {
                "form": token.form,
                "lemma": token.lemma,
                "upos": token.upos,
                "token_id": token.token_id,
            }
            for token in extracted
        ],
        "anchor_profile": anchor_profile(candidate, extracted),
        "measurement": measurement,
        "abstention_reason": measurement.get("abstention_reason"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen word-level modifier-bracketing probe."
    )
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument(
        "--handoff",
        nargs=2,
        action="append",
        metavar=("ROOT", "ROLE"),
        required=True,
    )
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    candidates = [
        json.loads(line)
        for line in args.candidates.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    stanza = _load_stanza()
    torch = _configure_determinism(args.seed, args.device)
    model_dir = args.model_dir.resolve()
    model_fingerprint, model_file_count = _model_fingerprint(model_dir, "zh-hans")
    options: dict[str, Any] = {
        "dir": str(model_dir),
        "lang": "zh-hans",
        "package": "gsdsimp",
        "processors": PROCESSORS,
        "use_gpu": args.device == "cuda",
        "verbose": False,
    }
    if hasattr(stanza, "DownloadMethod"):
        options["download_method"] = stanza.DownloadMethod.NONE
    nlp = stanza.Pipeline(**options)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with torch.inference_mode():
        (
            association,
            targets,
            failures,
            corpus_identity,
            passage_count,
            covered_documents,
        ) = parse_corpus(nlp, args.handoff, candidates)
        rows, empirical_cutoffs = score_rows(
            candidates, targets, failures, association
        )
        example = example_measurement(nlp, association)

    scorable = [
        row for row in rows if row["measurement"].get("abstention_reason") is None
    ]
    if scorable and example.get("abstention_reason") is None:
        entropy_reference = [
            float(row["measurement"]["normalized_tree_entropy"])
            for row in scorable
        ]
        margin_reference = [
            float(row["measurement"]["best_second_margin_per_attachment"])
            for row in scorable
        ]
        example_measure = example["measurement"]
        example["entropy_percentile"] = percentile_midrank(
            float(example_measure["normalized_tree_entropy"]), entropy_reference
        )
        example["margin_percentile"] = percentile_midrank(
            float(example_measure["best_second_margin_per_attachment"]),
            margin_reference,
        )
        example_passed = bool(
            example_measure["familiar_token_fraction"] >= HIGH_FAMILIAR_FRACTION
            and example_measure["normalized_tree_entropy"]
            >= empirical_cutoffs["example_entropy_median"]
            and example_measure["best_second_margin_per_attachment"]
            <= empirical_cutoffs["example_margin_median"]
            and example_measure["weak_best_attachment_count"]
            >= HIGH_MIN_WEAK_ATTACHMENTS
        )
    else:
        example_passed = False

    selected = select_high_documents(rows)
    fatal_alignment_failures = [
        row for row in failures if row.get("fatal_alignment_failure")
    ]
    high_gate_checks = {
        "entropy_at_or_above_p80": lambda row: (
            row["measurement"]["normalized_tree_entropy"]
            >= empirical_cutoffs["high_entropy_p80"]
        ),
        "margin_at_or_below_p20": lambda row: (
            row["measurement"]["best_second_margin_per_attachment"]
            <= empirical_cutoffs["high_margin_p20"]
        ),
        "familiar_fraction_at_least_0.80": lambda row: (
            row["measurement"]["familiar_token_fraction"]
            >= HIGH_FAMILIAR_FRACTION
        ),
        "at_least_two_weak_attachments": lambda row: (
            row["measurement"]["weak_best_attachment_count"]
            >= HIGH_MIN_WEAK_ATTACHMENTS
        ),
        "entropy_and_margin": lambda row: (
            row["measurement"]["normalized_tree_entropy"]
            >= empirical_cutoffs["high_entropy_p80"]
            and row["measurement"]["best_second_margin_per_attachment"]
            <= empirical_cutoffs["high_margin_p20"]
        ),
        "entropy_margin_and_familiarity": lambda row: (
            row["measurement"]["normalized_tree_entropy"]
            >= empirical_cutoffs["high_entropy_p80"]
            and row["measurement"]["best_second_margin_per_attachment"]
            <= empirical_cutoffs["high_margin_p20"]
            and row["measurement"]["familiar_token_fraction"]
            >= HIGH_FAMILIAR_FRACTION
        ),
    }
    high_gate_component_counts = {
        name: {
            "instances": sum(check(row) for row in scorable),
            "documents": len({row["doc_id"] for row in scorable if check(row)}),
            "sources": sorted(
                {row["source"] for row in scorable if check(row)}
            ),
        }
        for name, check in high_gate_checks.items()
    }
    selected_sources = {row["source"] for row in selected}
    selected_unanchored = sum(not row["has_anchor"] for row in selected)
    multi_source_passed = bool(
        len(selected) == REQUIRED_HIGH_DOCUMENTS
        and len(selected_sources) >= REQUIRED_HIGH_SOURCES
        and selected_unanchored >= REQUIRED_UNANCHORED
    )
    stage0_passed = (
        example_passed and multi_source_passed and not fatal_alignment_failures
    )

    summary = {
        "artifact_type": "deterministic-word-level-modifier-bracketing-probe",
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "seed": args.seed,
        "device": args.device,
        "stage0_passed": stage0_passed,
        "candidate_count": len(rows),
        "scorable_candidate_count": len(scorable),
        "alignment_failure_count": len(failures),
        "fatal_alignment_failure_count": len(fatal_alignment_failures),
        "high_candidate_count": sum(
            row["high_bracketing_competition"] for row in rows
        ),
        "high_document_count": len(
            {
                row["doc_id"]
                for row in rows
                if row["high_bracketing_competition"]
            }
        ),
        "high_gate_component_counts": high_gate_component_counts,
        "candidate_abstention_reasons": dict(
            sorted(Counter(row["reason"] for row in failures).items())
        ),
        "selected_high_count": len(selected),
        "selected_high_sources": sorted(selected_sources),
        "selected_high_source_counts": dict(
            sorted(Counter(row["source"] for row in selected).items())
        ),
        "selected_high_unanchored_count": selected_unanchored,
        "reader_example_gate_passed": example_passed,
        "multi_source_gate_passed": multi_source_passed,
        "reader_example": example,
        "association_corpus": {
            "passage_count": passage_count,
            "covered_document_count": len(covered_documents),
            "sentence_count": len(association.sentence_sequences),
            "vocabulary_size": len(association.token_counts),
            "ordered_pair_types": len(association.pair_counts),
            "handoffs": corpus_identity,
        },
        "parser": {
            "name": "stanza-universal-dependencies",
            "language": "zh-hans",
            "package": "gsdsimp",
            "processors": list(PROCESSORS),
            "model_fingerprint": model_fingerprint,
            "model_file_count": model_file_count,
        },
        "input": {
            "candidates_path": str(args.candidates),
            "candidates_sha256": sha256(args.candidates),
        },
        "thresholds": {
            "content_pos": sorted(CONTENT_POS),
            "minimum_target_tokens": MIN_TARGET_TOKENS,
            "maximum_target_tokens": MAX_TARGET_TOKENS,
            "association_window": ASSOCIATION_WINDOW,
            "smoothing": SMOOTHING,
            "familiar_documents": FAMILIAR_DOCUMENTS,
            "familiar_sources": FAMILIAR_SOURCES,
            "high_entropy_percentile": HIGH_ENTROPY_PERCENTILE,
            "high_margin_percentile": HIGH_MARGIN_PERCENTILE,
            "high_familiar_fraction": HIGH_FAMILIAR_FRACTION,
            "high_minimum_weak_attachments": HIGH_MIN_WEAK_ATTACHMENTS,
            "example_entropy_percentile": EXAMPLE_ENTROPY_PERCENTILE,
            "example_margin_percentile": EXAMPLE_MARGIN_PERCENTILE,
            "required_high_documents": REQUIRED_HIGH_DOCUMENTS,
            "required_high_sources": REQUIRED_HIGH_SOURCES,
            "maximum_selected_per_source": MAX_SELECTED_PER_SOURCE,
            "required_unanchored": REQUIRED_UNANCHORED,
            "numerical_margin_tolerance": NUMERICAL_MARGIN_TOLERANCE,
            "empirical_nearest_rank_cutoffs": empirical_cutoffs,
        },
        "limits": [
            (
                "The association corpus and candidate percentiles are development-"
                "exposed, not external validation."
            ),
            (
                "English noun-compound methods motivate the measurement but do not "
                "validate transfer to Chinese."
            ),
            (
                "Anchor variables and corpus familiarity remain rival explanations "
                "rather than manual exclusions."
            ),
            (
                "No body from the 30-document validation reserve is requested by "
                "this run."
            ),
            (
                "Passing this computational gate would not by itself authorize a "
                "reader project."
            ),
        ],
    }
    write_jsonl(args.output_dir / "candidate_measurements.jsonl", rows)
    write_jsonl(args.output_dir / "alignment_failures.jsonl", failures)
    write_jsonl(
        args.output_dir / "selected_high_candidates.jsonl",
        selected,
    )
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if stage0_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
