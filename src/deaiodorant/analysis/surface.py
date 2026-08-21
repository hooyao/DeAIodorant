"""Deterministic surface, discourse, and title features for Chinese documents."""

from __future__ import annotations

import math
import re
import statistics
import unicodedata
import zlib
from collections import Counter
from collections.abc import Sequence
from itertools import pairwise

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？!?])\s*")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
LIST_ITEM_RE = re.compile(
    r"^(?:[-*•·]|[（(]?(?:\d+|[一二三四五六七八九十百]+)[.)、）])\s*"
)
QUOTE_CHARS = frozenset("“”‘’「」『』《》")
PARENTHESIS_CHARS = frozenset("()（）[]【】{}")
COMMA_CHARS = frozenset("，,、")
PERIOD_CHARS = frozenset("。.!！？?")
COLON_CHARS = frozenset("：:")
SEMICOLON_CHARS = frozenset("；;")
DASH_CHARS = frozenset("—–-")

DISCOURSE_MARKERS = {
    "causal": ("因此", "因而", "所以", "由此", "这意味着", "正因如此"),
    "contrast": ("然而", "但是", "不过", "与此同时", "相较之下", "反过来"),
    "enumeration": (
        "首先",
        "其次",
        "再次",
        "最后",
        "第一",
        "第二",
        "第三",
        "一方面",
        "另一方面",
    ),
    "framing": ("在当今", "随着", "如今", "在这个", "从本质上讲"),
    "metadiscourse": (
        "需要指出的是",
        "不难发现",
        "可以看出",
        "显而易见",
        "毋庸置疑",
        "值得一提的是",
        "值得注意的是",
    ),
    "summary": ("总而言之", "综上所述", "总的来说", "简而言之", "总体来看", "归根结底"),
}

EPISTEMIC_MARKERS = {
    "booster": ("显然", "无疑", "必然", "一定", "毫无疑问", "毋庸置疑"),
    "directive": ("应该", "应当", "需要", "建议", "必须", "值得"),
    "hedge": ("可能", "或许", "似乎", "大概", "通常", "往往", "一定程度", "有望"),
}


def _mean(values: Sequence[float | int]) -> float:
    return statistics.fmean(values) if values else 0.0


def _population_sd(values: Sequence[float | int]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _coefficient_of_variation(values: Sequence[float | int]) -> float:
    mean = _mean(values)
    return _population_sd(values) / mean if mean else 0.0


def _entropy(symbols: Sequence[str]) -> float:
    if not symbols:
        return 0.0
    counts = Counter(symbols)
    total = len(symbols)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _mattr(symbols: Sequence[str], window: int) -> float:
    if window <= 1:
        raise ValueError("MATTR window must be greater than one")
    if not symbols:
        return 0.0
    if len(symbols) <= window:
        return len(set(symbols)) / len(symbols)
    ratios = [
        len(set(symbols[index : index + window])) / window
        for index in range(len(symbols) - window + 1)
    ]
    return statistics.fmean(ratios)


def _split_sentences(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [
        part.strip() for part in SENTENCE_BOUNDARY_RE.split(normalized) if part.strip()
    ]


def _cjk_only(text: str) -> list[str]:
    return CJK_RE.findall(text)


def _repeated_ngram_ratio(symbols: Sequence[str], size: int) -> float:
    if size <= 0:
        raise ValueError("N-gram size must be positive")
    total = len(symbols) - size + 1
    if total <= 0:
        return 0.0
    ngrams = [tuple(symbols[index : index + size]) for index in range(total)]
    return (total - len(set(ngrams))) / total


def _opening_repeat_ratio(items: Sequence[str], size: int = 4) -> float:
    openings: list[tuple[str, ...]] = []
    for item in items:
        chars = _cjk_only(item)
        if len(chars) >= size:
            openings.append(tuple(chars[:size]))
    if not openings:
        return 0.0
    return (len(openings) - len(set(openings))) / len(openings)


def _exact_repeat_ratio(items: Sequence[str]) -> float:
    normalized = [re.sub(r"\s+", "", item) for item in items if item.strip()]
    if not normalized:
        return 0.0
    return (len(normalized) - len(set(normalized))) / len(normalized)


def _lag_one_autocorrelation(values: Sequence[float | int]) -> float:
    if len(values) < 3:
        return 0.0
    left = list(values[:-1])
    right = list(values[1:])
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((value - left_mean) ** 2 for value in left)
        * sum((value - right_mean) ** 2 for value in right)
    )
    return numerator / denominator if denominator else 0.0


def _adjacent_length_change(values: Sequence[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = statistics.fmean(values)
    if mean == 0:
        return 0.0
    differences = [abs(right - left) for left, right in pairwise(values)]
    return statistics.fmean(differences) / mean


def _compression_ratio(text: str) -> float:
    encoded = text.encode("utf-8")
    if not encoded:
        return 0.0
    return len(zlib.compress(encoded, level=9)) / len(encoded)


def _density(count: int, denominator: int, scale: int = 1) -> float:
    return count / denominator * scale if denominator else 0.0


def surface_features(
    text: str,
    *,
    char_ngram_size: int = 4,
    char_mattr_window: int = 500,
) -> dict[str, float | int]:
    """Extract model-free document-level surface and regularity features."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    non_whitespace = [char for char in normalized if not char.isspace()]
    cjk_chars = _cjk_only(normalized)
    paragraphs = [line.strip() for line in normalized.split("\n") if line.strip()]
    sentences = _split_sentences(normalized)
    paragraph_lengths = [len(_cjk_only(paragraph)) for paragraph in paragraphs]
    sentence_lengths = [len(_cjk_only(sentence)) for sentence in sentences]
    punctuation = [
        char for char in non_whitespace if unicodedata.category(char).startswith("P")
    ]
    denominator = len(non_whitespace)
    cjk_count = len(cjk_chars)
    sentence_count = len(sentences)
    paragraph_count = len(paragraphs)
    sentence_counts_per_paragraph = [
        max(1, len(_split_sentences(paragraph))) for paragraph in paragraphs
    ]

    return {
        "surface_adjacent_sentence_length_change": _adjacent_length_change(
            sentence_lengths
        ),
        "surface_ascii_letter_ratio": _density(
            sum(char.isascii() and char.isalpha() for char in non_whitespace),
            denominator,
        ),
        "surface_char_count": len(normalized),
        "surface_cjk_char_count": cjk_count,
        "surface_cjk_char_entropy_bits": _entropy(cjk_chars),
        "surface_cjk_char_mattr": _mattr(cjk_chars, char_mattr_window),
        "surface_cjk_char_type_token_ratio": (
            len(set(cjk_chars)) / cjk_count if cjk_count else 0.0
        ),
        "surface_cjk_ratio": _density(cjk_count, denominator),
        "surface_colon_density": _density(
            sum(char in COLON_CHARS for char in non_whitespace),
            denominator,
        ),
        "surface_comma_density": _density(
            sum(char in COMMA_CHARS for char in non_whitespace),
            denominator,
        ),
        "surface_compression_ratio": _compression_ratio(normalized),
        "surface_dash_density": _density(
            sum(char in DASH_CHARS for char in non_whitespace),
            denominator,
        ),
        "surface_digit_ratio": _density(
            sum(char.isdigit() for char in non_whitespace),
            denominator,
        ),
        "surface_exact_paragraph_repeat_ratio": _exact_repeat_ratio(paragraphs),
        "surface_exact_sentence_repeat_ratio": _exact_repeat_ratio(sentences),
        "surface_exclamatory_sentence_ratio": _density(
            sum(sentence.rstrip().endswith(("！", "!")) for sentence in sentences),
            sentence_count,
        ),
        "surface_list_item_ratio": _density(
            sum(bool(LIST_ITEM_RE.match(paragraph)) for paragraph in paragraphs),
            paragraph_count,
        ),
        "surface_long_paragraph_ratio": _density(
            sum(length > 200 for length in paragraph_lengths),
            paragraph_count,
        ),
        "surface_mean_paragraph_cjk_chars": _mean(paragraph_lengths),
        "surface_mean_sentence_cjk_chars": _mean(sentence_lengths),
        "surface_mean_sentences_per_paragraph": _mean(sentence_counts_per_paragraph),
        "surface_non_whitespace_char_count": denominator,
        "surface_paragraph_count": paragraph_count,
        "surface_paragraph_length_cv": _coefficient_of_variation(paragraph_lengths),
        "surface_paragraph_opening_repeat_ratio": _opening_repeat_ratio(paragraphs),
        "surface_parenthesis_density": _density(
            sum(char in PARENTHESIS_CHARS for char in non_whitespace),
            denominator,
        ),
        "surface_period_density": _density(
            sum(char in PERIOD_CHARS for char in non_whitespace),
            denominator,
        ),
        "surface_punctuation_density": _density(len(punctuation), denominator),
        "surface_punctuation_entropy_bits": _entropy(punctuation),
        "surface_question_sentence_ratio": _density(
            sum(sentence.rstrip().endswith(("？", "?")) for sentence in sentences),
            sentence_count,
        ),
        "surface_quote_mark_density": _density(
            sum(char in QUOTE_CHARS for char in non_whitespace),
            denominator,
        ),
        "surface_repeated_char_ngram_ratio": _repeated_ngram_ratio(
            cjk_chars,
            char_ngram_size,
        ),
        "surface_semicolon_density": _density(
            sum(char in SEMICOLON_CHARS for char in non_whitespace),
            denominator,
        ),
        "surface_sentence_count": sentence_count,
        "surface_sentence_length_autocorrelation": _lag_one_autocorrelation(
            sentence_lengths
        ),
        "surface_sentence_length_cv": _coefficient_of_variation(sentence_lengths),
        "surface_sentence_opening_repeat_ratio": _opening_repeat_ratio(sentences),
        "surface_short_paragraph_ratio": _density(
            sum(0 < length < 20 for length in paragraph_lengths),
            paragraph_count,
        ),
        "surface_url_count_per_1000_cjk": _density(
            len(URL_RE.findall(normalized)),
            cjk_count,
            1000,
        ),
    }


def discourse_features(text: str) -> dict[str, float]:
    """Count fixed discourse and epistemic markers per 10,000 CJK characters."""

    cjk_count = len(_cjk_only(text))
    output: dict[str, float] = {}
    total = 0
    observed_types = 0
    vocabulary_size = 0
    for category, markers in DISCOURSE_MARKERS.items():
        category_count = 0
        for marker in markers:
            count = text.count(marker)
            category_count += count
            observed_types += count > 0
            vocabulary_size += 1
        total += category_count
        output[f"discourse_{category}_markers_per_10k_cjk"] = _density(
            category_count,
            cjk_count,
            10000,
        )
    output["discourse_all_markers_per_10k_cjk"] = _density(
        total,
        cjk_count,
        10000,
    )
    output["discourse_marker_type_coverage"] = (
        observed_types / vocabulary_size if vocabulary_size else 0.0
    )
    for category, markers in EPISTEMIC_MARKERS.items():
        count = sum(text.count(marker) for marker in markers)
        output[f"discourse_{category}_markers_per_10k_cjk"] = _density(
            count,
            cjk_count,
            10000,
        )
    return output


def title_features(title: str, body: str) -> dict[str, float | int]:
    """Extract title-only form features without adding the raw title to output."""

    title = title.strip()
    title_cjk = _cjk_only(title)
    body_cjk_types = set(_cjk_only(body))
    title_cjk_types = set(title_cjk)
    return {
        "title_ascii_letter_ratio": _density(
            sum(char.isascii() and char.isalpha() for char in title),
            len(title),
        ),
        "title_body_cjk_type_overlap": (
            len(title_cjk_types.intersection(body_cjk_types)) / len(title_cjk_types)
            if title_cjk_types
            else 0.0
        ),
        "title_cjk_char_count": len(title_cjk),
        "title_colon_present": float(any(char in COLON_CHARS for char in title)),
        "title_digit_present": float(any(char.isdigit() for char in title)),
        "title_exclamation_present": float(any(char in "！!" for char in title)),
        "title_question_present": float(any(char in "？?" for char in title)),
        "title_quote_present": float(any(char in QUOTE_CHARS for char in title)),
    }
