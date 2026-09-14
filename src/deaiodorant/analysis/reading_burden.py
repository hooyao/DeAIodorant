"""Auditable lexical cues for reading-burden case studies.

This first version counts explicit replacement constructions. It does not
measure reading quality, infer authorship, resolve argument structure, or
diagnose logical coherence. Dependency annotations may accompany the input but
are deliberately unused. Chinese examples and matched literals are source data.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

SCHEMA_VERSION = "deaiodorant-reading-burden-0.1"

# Fixed lexical inventory, not a complete Chinese negation grammar. Family
# names are glosses for grouping surface variants, not semantic judgments.
NEGATIVE_PREFIX_FAMILIES = {
    "并不认为": "not_believe",
    "不认为": "not_believe",
    "并不意味着": "not_imply",
    "不意味着": "not_imply",
    "并不在于": "not_lie_in",
    "不在于": "not_lie_in",
    "不再只是": "no_longer_only_is",
    "并不只是": "not_only_is",
    "不只是": "not_only_is",
    "不仅仅是": "not_only_is",
    "不仅是": "not_only_is",
    "不单单是": "not_only_is",
    "不单是": "not_only_is",
    "不光是": "not_only_is",
    "不完全是": "not_entirely_is",
    "不一定是": "not_necessarily_is",
    "不应该是": "should_not_be",
    "不应是": "should_not_be",
    "不再是": "no_longer_is",
    "并不是": "not_is",
    "不是": "not_is",
    "并非": "not_be",
}

_PREFIX_RE = re.compile(
    "|".join(
        re.escape(prefix)
        for prefix in sorted(NEGATIVE_PREFIX_FAMILIES, key=lambda item: (-len(item), item))
    )
)
_CONNECTOR_RE = re.compile("而不是|而非|而是")
_LITERAL_ERSHI_RE = re.compile("而是")
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_TERMINATORS = "。！？!?"
_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6", "title", "heading"})


def _span(text: str, start: int, end: int) -> dict[str, Any]:
    return {"text": text[start:end], "start_char": start, "end_char": end}


def _context(record: Mapping[str, Any], index: int) -> dict[str, Any]:
    tag = record.get("block_tag")
    return {
        "sentence_id": record.get("sentence_id", index + 1),
        "block_id": record.get("block_id"),
        "block_tag": tag,
        "context_type": "heading" if str(tag).lower() in _HEADING_TAGS else "non_heading",
    }


def _window_start(text: str, connector_start: int, previous_end: int) -> int:
    """Do not pair across a terminal mark or an earlier explicit connector."""

    return max(
        previous_end,
        max((text.rfind(mark, 0, connector_start) + 1 for mark in _TERMINATORS), default=0),
    )


def _prefixes(text: str, start: int, end: int) -> list[dict[str, Any]]:
    matches = []
    for match in _PREFIX_RE.finditer(text, start, end):
        # A negative-alternative connector contains a negation, but is not the
        # left side of a replacement construction. Normally the window already
        # excludes it; the explicit check keeps this invariant independently.
        if match.group() == "不是" and match.start() > 0 and text[match.start() - 1] == "而":
            continue
        matches.append(_span(text, match.start(), match.end()))
    return matches


def analyze_sentences(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Count literal cues in source records without assigning a smell score.

    Each record requires ``text`` and may supply ``sentence_id``, ``block_id``,
    ``block_tag``, and ``words``. A record can also be a whole captured body;
    input record counts must not be described as linguistic sentence counts.
    Offsets are Unicode code-point offsets relative to each unmodified record.

    Every literal ``而是`` gets exactly one lexical family. The nearest matched
    negative prefix in its window is selected, with longest-first matching at
    the same position. The window starts after the previous explicit connector
    or ``。！？!?``, whichever is later. Newlines are retained and do not create
    a boundary because extraction can insert them inside a sentence. Quotes
    remain counted and can produce heuristic pairings that need human review.
    ``而不是`` and ``而非`` are counted separately, never as literal ``而是``.
    No family denotes a grammatical error or an automatically removable cue.
    """

    literal_instances: list[dict[str, Any]] = []
    replacement_instances: list[dict[str, Any]] = []
    alternative_instances: list[dict[str, Any]] = []
    prefix_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    alternative_counts: Counter[str] = Counter()
    context_counts: Counter[str] = Counter()
    literal_context_counts: Counter[str] = Counter()
    record_count = 0
    records_with_literal = 0
    cjk_character_count = 0

    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or not isinstance(record.get("text"), str):
            raise ValueError(f"Record {index + 1} must be a mapping with string text")
        text = record["text"]
        context = _context(record, index)
        record_count += 1
        context_counts[context["context_type"]] += 1
        cjk_character_count += len(_CJK_RE.findall(text))
        literal_matches = list(_LITERAL_ERSHI_RE.finditer(text))
        records_with_literal += bool(literal_matches)
        for match in literal_matches:
            literal_instances.append({**context, "match": _span(text, match.start(), match.end())})
            literal_context_counts[context["context_type"]] += 1

        previous_connector_end = 0
        for connector in _CONNECTOR_RE.finditer(text):
            match_span = _span(text, connector.start(), connector.end())
            if connector.group() != "而是":
                alternative_counts[connector.group()] += 1
                alternative_instances.append({**context, "match": match_span})
            else:
                start = _window_start(text, connector.start(), previous_connector_end)
                candidates = _prefixes(text, start, connector.start())
                prefix = candidates[-1] if candidates else None
                prefix_literal = prefix["text"] if prefix else "__unpaired__"
                family = NEGATIVE_PREFIX_FAMILIES[prefix_literal] if prefix else "unpaired"
                prefix_counts[prefix_literal] += 1
                family_counts[family] += 1
                replacement_instances.append(
                    {
                        **context,
                        "connector": match_span,
                        "left_prefix": prefix,
                        "family": family,
                        "pairing_status": "lexical_candidate" if prefix else "unknown",
                        "pairing_window": _span(text, start, connector.start()),
                        "preceding_prefix_candidates": candidates,
                    }
                )
            previous_connector_end = connector.end()

    literal_count = len(literal_instances)
    assert literal_count == len(replacement_instances)
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": {
            "input_record_count": record_count,
            "input_record_counts_by_context": dict(sorted(context_counts.items())),
            "cjk_character_count": cjk_character_count,
            "offset_unit": "unicode_code_points_relative_to_input_record",
        },
        "style_cues": {
            "literal_ershi": {
                "count": literal_count,
                "input_records_with_matches": records_with_literal,
                "counts_by_context": dict(sorted(literal_context_counts.items())),
                "per_1000_cjk_characters": (
                    1000 * literal_count / cjk_character_count if cjk_character_count else None
                ),
                "instances": literal_instances,
            },
            "counts_by_left_prefix": dict(sorted(prefix_counts.items())),
            "counts_by_family": dict(sorted(family_counts.items())),
            "replacement_frame_instances": replacement_instances,
            "negative_alternative_connectors": {
                "count": len(alternative_instances),
                "counts_by_literal": dict(sorted(alternative_counts.items())),
                "instances": alternative_instances,
            },
        },
        "structural_proxies": {
            "status": "not_evaluated",
            "reason": "This version does not analyze predicate arguments or reference continuity.",
        },
        "reading_quality": {"status": "unknown", "score": None},
        "method": {
            "negative_prefix_families": dict(NEGATIVE_PREFIX_FAMILIES),
            "terminal_boundaries": _TERMINATORS,
            "connector_inventory": ["而不是", "而非", "而是"],
            "pairing_rule": "Nearest catalog prefix after the last terminal or explicit connector.",
            "newlines": "Retained; not pairing boundaries.",
            "quotes": "Retained; not automatically attributed to the article author.",
        },
        "limitations": [
            "Literal counts are exact for supplied text; extraction scope can change them.",
            "Prefix pairing is lexical and may cross quoted or unrelated clauses.",
            "The prefix catalog is incomplete; unpaired means unknown, not malformed.",
            "Frequency alone does not establish reading difficulty, irritation, or authorship.",
            "No cue warrants deletion without preserving meaning and evaluating reader outcomes.",
            "Chinese allows zero subjects, shared arguments, intransitives, and nominal predicates.",
        ],
    }
