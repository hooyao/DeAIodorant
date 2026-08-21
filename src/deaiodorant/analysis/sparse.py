"""Extract sparse, interpretable stylometric pattern features."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import FeatureConfig
from .corpus import CorpusLoadResult
from .syntax import DependencyToken, read_conllu

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？!?])\s*")
FUNCTION_POS = frozenset({"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "SCONJ"})
CONTENT_POS = frozenset({"ADJ", "ADV", "NOUN", "PROPN", "VERB"})


@dataclass(frozen=True)
class SparseExtraction:
    """Selected sparse vocabulary and non-zero document values."""

    catalog: list[dict[str, Any]]
    values: list[dict[str, Any]]
    summary: dict[str, Any]


@dataclass(frozen=True)
class _DocumentPatterns:
    doc_id: str
    counts: dict[str, Counter[str]]
    totals: dict[str, int]


def _sentences(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [
        part.strip() for part in SENTENCE_BOUNDARY_RE.split(normalized) if part.strip()
    ]


def _ngrams(items: list[str], size: int, separator: str) -> Counter[str]:
    if len(items) < size:
        return Counter()
    return Counter(
        separator.join(items[index : index + size])
        for index in range(len(items) - size + 1)
    )


def _punctuation_runs(text: str) -> Counter[str]:
    runs: Counter[str] = Counter()
    current: list[str] = []
    for character in text:
        if unicodedata.category(character).startswith("P"):
            current.append(character)
        elif current:
            runs["".join(current)] += 1
            current = []
    if current:
        runs["".join(current)] += 1
    return runs


def _syntax_patterns(
    sentences: list[list[DependencyToken]],
    *,
    pos_ngram_sizes: tuple[int, ...],
) -> dict[str, Counter[str]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for sentence in sentences:
        tags = [token.upos for token in sentence if token.upos != "PUNCT"]
        for size in pos_ngram_sizes:
            counters[f"pos_{size}gram"].update(_ngrams(tags, size, ">"))
        counters["function_word"].update(
            token.form for token in sentence if token.upos in FUNCTION_POS
        )
        counters["content_lemma"].update(
            token.lemma if token.lemma != "_" else token.form
            for token in sentence
            if token.upos in CONTENT_POS
        )
        by_id = {token.token_id: token for token in sentence}
        for token in sentence:
            relation = token.deprel.split(":", 1)[0]
            if token.head == 0:
                counters["root_pos"][token.upos] += 1
                continue
            head = by_id[token.head]
            head_relation = head.deprel.split(":", 1)[0]
            counters["dependency_treelet"][f"{head.upos}>{relation}>{token.upos}"] += 1
            counters["dependency_path"][f"{head_relation}>{relation}"] += 1
    return dict(counters)


def _document_patterns(
    *,
    doc_id: str,
    text: str,
    annotation_path: Path,
    config: FeatureConfig,
) -> _DocumentPatterns:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for sentence in _sentences(text):
        characters = CJK_RE.findall(sentence)
        for size in config.sparse_char_ngram_sizes:
            counters[f"char_{size}gram"].update(_ngrams(characters, size, ""))
        if len(characters) >= config.sparse_opening_cjk_chars:
            opening = "".join(characters[: config.sparse_opening_cjk_chars])
            counters["sentence_opening"][opening] += 1
    counters["punctuation_run"].update(_punctuation_runs(text))
    for family, counts in _syntax_patterns(
        read_conllu(annotation_path),
        pos_ngram_sizes=config.sparse_pos_ngram_sizes,
    ).items():
        counters[family].update(counts)
    return _DocumentPatterns(
        doc_id=doc_id,
        counts=dict(counters),
        totals={
            family: sum(family_counts.values())
            for family, family_counts in counters.items()
        },
    )


def _feature_id(family: str, pattern: str) -> str:
    return hashlib.sha256(f"{family}\0{pattern}".encode()).hexdigest()[:24]


def extract_sparse_features(
    corpus: CorpusLoadResult,
    *,
    annotation_dir: Path,
    config: FeatureConfig,
) -> SparseExtraction:
    """Select a cohort-blind vocabulary and emit non-zero normalized values."""

    documents: list[_DocumentPatterns] = []
    document_frequency: dict[str, Counter[str]] = defaultdict(Counter)
    total_frequency: dict[str, Counter[str]] = defaultdict(Counter)
    for document in corpus.documents:
        patterns = _document_patterns(
            doc_id=document.doc_id,
            text=document.text,
            annotation_path=annotation_dir / f"{document.doc_id}.conllu",
            config=config,
        )
        documents.append(patterns)
        for family, counts in patterns.counts.items():
            document_frequency[family].update(counts.keys())
            total_frequency[family].update(counts)

    selected: dict[str, list[str]] = {}
    for family in sorted(document_frequency):
        candidates = [
            pattern
            for pattern, frequency in document_frequency[family].items()
            if frequency >= config.sparse_minimum_document_frequency
        ]
        candidates.sort(
            key=lambda pattern: (
                -document_frequency[family][pattern],
                -total_frequency[family][pattern],
                pattern,
            )
        )
        selected[family] = candidates[: config.sparse_maximum_features_per_family]

    catalog: list[dict[str, Any]] = []
    selected_ids: dict[tuple[str, str], str] = {}
    seen_ids: set[str] = set()
    for family, patterns in selected.items():
        for pattern in patterns:
            feature_id = _feature_id(family, pattern)
            if feature_id in seen_ids:
                raise ValueError("Sparse feature ID collision")
            seen_ids.add(feature_id)
            selected_ids[(family, pattern)] = feature_id
            catalog.append(
                {
                    "document_frequency": document_frequency[family][pattern],
                    "family": family,
                    "feature_id": feature_id,
                    "pattern": pattern,
                    "selection": "combined_corpus_document_frequency",
                    "total_count": total_frequency[family][pattern],
                    "value_columns": ["count", "rate_per_1000_opportunities"],
                }
            )
    catalog.sort(key=lambda item: (item["family"], item["feature_id"]))

    values: list[dict[str, Any]] = []
    for document in documents:
        for family, patterns in selected.items():
            denominator = document.totals.get(family, 0)
            if denominator == 0:
                continue
            family_counts = document.counts.get(family, Counter())
            for pattern in patterns:
                count = family_counts[pattern]
                if count:
                    values.append(
                        {
                            "count": count,
                            "doc_id": document.doc_id,
                            "feature_id": selected_ids[(family, pattern)],
                            "rate_per_1000_opportunities": count / denominator * 1000,
                        }
                    )
    values.sort(key=lambda item: (item["doc_id"], item["feature_id"]))
    summary = {
        "family_vocabulary_sizes": {
            family: len(patterns) for family, patterns in selected.items()
        },
        "nonzero_value_count": len(values),
        "selection_uses_cohort_labels": False,
        "vocabulary_size": len(catalog),
    }
    return SparseExtraction(catalog=catalog, values=values, summary=summary)
