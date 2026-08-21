"""Read CoNLL-U and extract Universal Dependencies document features."""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

UNIVERSAL_POS = (
    "ADJ",
    "ADP",
    "ADV",
    "AUX",
    "CCONJ",
    "DET",
    "INTJ",
    "NOUN",
    "NUM",
    "PART",
    "PRON",
    "PROPN",
    "PUNCT",
    "SCONJ",
    "SYM",
    "VERB",
    "X",
)

UNIVERSAL_DEPENDENCIES = (
    "acl",
    "advcl",
    "advmod",
    "amod",
    "appos",
    "aux",
    "case",
    "cc",
    "ccomp",
    "clf",
    "compound",
    "conj",
    "cop",
    "csubj",
    "dep",
    "det",
    "discourse",
    "dislocated",
    "expl",
    "fixed",
    "flat",
    "goeswith",
    "iobj",
    "list",
    "mark",
    "nmod",
    "nsubj",
    "nummod",
    "obj",
    "obl",
    "orphan",
    "parataxis",
    "punct",
    "reparandum",
    "root",
    "vocative",
    "xcomp",
)

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
FUNCTION_POS = frozenset({"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "SCONJ"})
CONTENT_POS = frozenset({"ADJ", "ADV", "NOUN", "PROPN", "VERB"})
FIRST_PERSON_PRONOUNS = frozenset({"我", "我们", "咱", "咱们", "本人", "笔者"})
SECOND_PERSON_PRONOUNS = frozenset({"你", "您", "你们", "诸位", "读者"})


class ConlluValidationError(ValueError):
    """Raised when dependency annotations are malformed or not tree-structured."""


@dataclass(frozen=True)
class DependencyToken:
    """One syntactic word from a CoNLL-U sentence."""

    token_id: int
    form: str
    lemma: str
    upos: str
    head: int
    deprel: str


def _parse_sentence(
    lines: list[str],
    *,
    source: str,
    sentence_number: int,
) -> list[DependencyToken]:
    tokens: list[DependencyToken] = []
    for line in lines:
        if line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 10:
            raise ConlluValidationError(
                f"{source}: sentence {sentence_number}: expected 10 CoNLL-U columns"
            )
        token_id_text = fields[0]
        if "-" in token_id_text or "." in token_id_text:
            continue
        try:
            token_id = int(token_id_text)
            head = int(fields[6])
        except ValueError as exc:
            raise ConlluValidationError(
                f"{source}: sentence {sentence_number}: invalid token ID or head"
            ) from exc
        tokens.append(
            DependencyToken(
                token_id=token_id,
                form=fields[1],
                lemma=fields[2],
                upos=fields[3],
                head=head,
                deprel=fields[7],
            )
        )
    if not tokens:
        raise ConlluValidationError(
            f"{source}: sentence {sentence_number}: no syntactic words"
        )
    _validate_tree(tokens, source=source, sentence_number=sentence_number)
    return tokens


def _validate_tree(
    tokens: list[DependencyToken],
    *,
    source: str,
    sentence_number: int,
) -> None:
    by_id = {token.token_id: token for token in tokens}
    if len(by_id) != len(tokens):
        raise ConlluValidationError(
            f"{source}: sentence {sentence_number}: duplicate token IDs"
        )
    roots = [token for token in tokens if token.head == 0]
    if len(roots) != 1:
        raise ConlluValidationError(
            f"{source}: sentence {sentence_number}: expected exactly one root"
        )
    for token in tokens:
        if token.head != 0 and token.head not in by_id:
            raise ConlluValidationError(
                f"{source}: sentence {sentence_number}: missing head {token.head}"
            )
        visited: set[int] = set()
        current = token
        while current.head != 0:
            if current.token_id in visited:
                raise ConlluValidationError(
                    f"{source}: sentence {sentence_number}: dependency cycle"
                )
            visited.add(current.token_id)
            current = by_id[current.head]


def read_conllu(path: Path) -> list[list[DependencyToken]]:
    """Read strict CoNLL-U sentences from one document annotation file."""

    sentences: list[list[DependencyToken]] = []
    current_lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            if current_lines:
                sentences.append(
                    _parse_sentence(
                        current_lines,
                        source=str(path),
                        sentence_number=len(sentences) + 1,
                    )
                )
                current_lines = []
            continue
        current_lines.append(line)
    if current_lines:
        sentences.append(
            _parse_sentence(
                current_lines,
                source=str(path),
                sentence_number=len(sentences) + 1,
            )
        )
    if not sentences:
        raise ConlluValidationError(f"{path}: no sentences")
    return sentences


def _mean(values: list[float | int]) -> float:
    return statistics.fmean(values) if values else 0.0


def _coefficient_of_variation(values: list[float | int]) -> float:
    if not values:
        return 0.0
    mean = statistics.fmean(values)
    return statistics.pstdev(values) / mean if len(values) > 1 and mean else 0.0


def _entropy(symbols: list[str]) -> float:
    if not symbols:
        return 0.0
    counts = Counter(symbols)
    total = len(symbols)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _moving_average_type_token_ratio(tokens: list[str], window: int) -> float:
    if window <= 1:
        raise ValueError("MATTR window must be greater than one")
    if not tokens:
        return 0.0
    if len(tokens) <= window:
        return len(set(tokens)) / len(tokens)
    ratios = [
        len(set(tokens[index : index + window])) / window
        for index in range(len(tokens) - window + 1)
    ]
    return statistics.fmean(ratios)


def _token_depths(sentence: list[DependencyToken]) -> list[int]:
    by_id = {token.token_id: token for token in sentence}
    depths: list[int] = []
    for token in sentence:
        depth = 0
        current = token
        while current.head != 0:
            depth += 1
            current = by_id[current.head]
        depths.append(depth)
    return depths


def _crossing_arc_ratio(sentence: list[DependencyToken]) -> float:
    arcs = [
        (min(token.token_id, token.head), max(token.token_id, token.head))
        for token in sentence
        if token.head != 0
    ]
    possible_pairs = len(arcs) * (len(arcs) - 1) // 2
    if possible_pairs == 0:
        return 0.0
    crossings = 0
    for first_index, (first_left, first_right) in enumerate(arcs):
        for second_left, second_right in arcs[first_index + 1 :]:
            if (
                first_left < second_left < first_right < second_right
                or second_left < first_left < second_right < first_right
            ):
                crossings += 1
    return crossings / possible_pairs


def _sequence_ngrams(items: list[str], size: int) -> list[str]:
    return [
        ">".join(items[index : index + size]) for index in range(len(items) - size + 1)
    ]


def _adjacent_jaccard_mean(sets: list[set[str]]) -> float:
    if len(sets) < 2:
        return 0.0
    values: list[float] = []
    for left, right in pairwise(sets):
        union = left.union(right)
        values.append(len(left.intersection(right)) / len(union) if union else 0.0)
    return statistics.fmean(values)


def dependency_features(
    sentences: list[list[DependencyToken]],
    *,
    mattr_window: int = 100,
) -> dict[str, float | int]:
    """Extract document-level lexical, POS, and dependency-tree features."""

    all_tokens = [token for sentence in sentences for token in sentence]
    lexical_word_tokens = [
        token for token in all_tokens if token.upos not in {"PUNCT", "SYM"}
    ]
    lexical_tokens = [token.form.casefold() for token in lexical_word_tokens]
    lexical_token_lengths = [
        len(CJK_RE.findall(token.form)) for token in lexical_word_tokens
    ]
    sentence_lengths = [len(sentence) for sentence in sentences]
    dependency_distances = [
        abs(token.token_id - token.head) for token in all_tokens if token.head != 0
    ]
    left_dependencies = sum(
        token.token_id < token.head for token in all_tokens if token.head != 0
    )
    depths = [depth for sentence in sentences for depth in _token_depths(sentence)]
    root_relative_positions = [
        next(token.token_id for token in sentence if token.head == 0) / len(sentence)
        for sentence in sentences
    ]
    crossing_arc_ratios = [_crossing_arc_ratio(sentence) for sentence in sentences]
    child_counts: list[int] = []
    for sentence in sentences:
        children: defaultdict[int, int] = defaultdict(int)
        for token in sentence:
            if token.head != 0:
                children[token.head] += 1
        child_counts.extend(children.values())

    upos_counts = Counter(token.upos for token in all_tokens)
    dependency_counts = Counter(token.deprel.split(":", 1)[0] for token in all_tokens)
    full_dependency_counts = Counter(token.deprel for token in all_tokens)
    pos_bigrams: list[str] = []
    pos_trigrams: list[str] = []
    treelets: list[str] = []
    sentence_content_sets: list[set[str]] = []
    sentence_noun_sets: list[set[str]] = []
    for sentence in sentences:
        tags = [token.upos for token in sentence if token.upos != "PUNCT"]
        sentence_content_sets.append(
            {
                (token.lemma if token.lemma != "_" else token.form).casefold()
                for token in sentence
                if token.upos in CONTENT_POS
            }
        )
        sentence_noun_sets.append(
            {
                (token.lemma if token.lemma != "_" else token.form).casefold()
                for token in sentence
                if token.upos in {"NOUN", "PROPN"}
            }
        )
        pos_bigrams.extend(_sequence_ngrams(tags, 2))
        pos_trigrams.extend(_sequence_ngrams(tags, 3))
        by_id = {token.token_id: token for token in sentence}
        for token in sentence:
            if token.head:
                head = by_id[token.head]
                relation = token.deprel.split(":", 1)[0]
                treelets.append(f"{head.upos}>{relation}>{token.upos}")

    token_total = len(all_tokens)
    lexical_total = len(lexical_word_tokens)
    non_root_dependencies = len(dependency_distances)
    subordinate_count = sum(
        dependency_counts[relation]
        for relation in ("acl", "advcl", "ccomp", "csubj", "xcomp")
    )
    features: dict[str, float | int] = {
        "syntax_adjacent_content_jaccard_mean": _adjacent_jaccard_mean(
            sentence_content_sets
        ),
        "syntax_adjacent_noun_jaccard_mean": _adjacent_jaccard_mean(sentence_noun_sets),
        "syntax_clause_relations_per_sentence": subordinate_count / len(sentences),
        "syntax_content_word_ratio": (
            sum(token.upos in CONTENT_POS for token in lexical_word_tokens)
            / lexical_total
            if lexical_total
            else 0.0
        ),
        "syntax_coordinate_relation_ratio": (
            (dependency_counts["cc"] + dependency_counts["conj"]) / token_total
        ),
        "syntax_crossing_arc_ratio_mean": _mean(crossing_arc_ratios),
        "syntax_dependency_distance_cv": _coefficient_of_variation(
            dependency_distances
        ),
        "syntax_dependency_distance_max": max(dependency_distances, default=0),
        "syntax_dependency_distance_mean": _mean(dependency_distances),
        "syntax_dependency_distance_median": (
            statistics.median(dependency_distances) if dependency_distances else 0.0
        ),
        "syntax_dependency_relation_entropy_bits": _entropy(
            [token.deprel.split(":", 1)[0] for token in all_tokens]
        ),
        "syntax_first_person_pronoun_ratio": (
            sum(token.form in FIRST_PERSON_PRONOUNS for token in lexical_word_tokens)
            / lexical_total
            if lexical_total
            else 0.0
        ),
        "syntax_function_word_ratio": (
            sum(token.upos in FUNCTION_POS for token in lexical_word_tokens)
            / lexical_total
            if lexical_total
            else 0.0
        ),
        "syntax_left_dependency_ratio": (
            left_dependencies / non_root_dependencies if non_root_dependencies else 0.0
        ),
        "syntax_lexical_hapax_ratio": (
            sum(count == 1 for count in Counter(lexical_tokens).values())
            / lexical_total
            if lexical_total
            else 0.0
        ),
        "syntax_lexical_mattr": _moving_average_type_token_ratio(
            lexical_tokens,
            mattr_window,
        ),
        "syntax_lexical_token_count": lexical_total,
        "syntax_lexical_token_entropy_bits": _entropy(lexical_tokens),
        "syntax_lexical_type_token_ratio": (
            len(set(lexical_tokens)) / lexical_total if lexical_total else 0.0
        ),
        "syntax_max_nonleaf_branching": max(child_counts, default=0),
        "syntax_max_tree_depth": max(depths, default=0),
        "syntax_mean_lexical_token_cjk_chars": _mean(lexical_token_lengths),
        "syntax_mean_nonleaf_branching": _mean(child_counts),
        "syntax_mean_root_relative_position": _mean(root_relative_positions),
        "syntax_mean_sentence_tokens": _mean(sentence_lengths),
        "syntax_mean_tree_depth": _mean(depths),
        "syntax_median_sentence_tokens": (
            statistics.median(sentence_lengths) if sentence_lengths else 0.0
        ),
        "syntax_nominal_modifier_relation_ratio": (
            sum(
                dependency_counts[relation]
                for relation in ("acl", "amod", "compound", "nmod")
            )
            / token_total
        ),
        "syntax_passive_relation_ratio": (
            sum(
                count
                for relation, count in full_dependency_counts.items()
                if ":pass" in relation
            )
            / token_total
        ),
        "syntax_pos_bigram_entropy_bits": _entropy(pos_bigrams),
        "syntax_pos_trigram_entropy_bits": _entropy(pos_trigrams),
        "syntax_second_person_pronoun_ratio": (
            sum(token.form in SECOND_PERSON_PRONOUNS for token in lexical_word_tokens)
            / lexical_total
            if lexical_total
            else 0.0
        ),
        "syntax_sentence_count": len(sentences),
        "syntax_sentence_length_cv": _coefficient_of_variation(sentence_lengths),
        "syntax_subordinate_relation_ratio": subordinate_count / token_total,
        "syntax_token_count": token_total,
        "syntax_token_length_cv": _coefficient_of_variation(lexical_token_lengths),
        "syntax_treelet_entropy_bits": _entropy(treelets),
    }

    for tag in UNIVERSAL_POS:
        features[f"upos_{tag.lower()}_ratio"] = upos_counts[tag] / token_total
    for relation in UNIVERSAL_DEPENDENCIES:
        features[f"deprel_{relation}_ratio"] = dependency_counts[relation] / token_total
    return features
