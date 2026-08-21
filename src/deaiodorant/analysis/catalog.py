"""Machine-readable metadata for every emitted document feature."""

from __future__ import annotations

from typing import Any


def _family(name: str) -> str:
    if name.startswith("title_"):
        return "title_form"
    if name.startswith("discourse_"):
        return "discourse_and_stance"
    if name.startswith("upos_"):
        return "universal_pos"
    if name.startswith("deprel_"):
        return "dependency_relation"
    if name.startswith("syntax_lexical") or name in {
        "syntax_content_word_ratio",
        "syntax_first_person_pronoun_ratio",
        "syntax_function_word_ratio",
        "syntax_mean_lexical_token_cjk_chars",
        "syntax_second_person_pronoun_ratio",
        "syntax_token_length_cv",
    }:
        return "token_and_lexical"
    if name.startswith("syntax_"):
        return "dependency_syntax"
    if any(
        marker in name
        for marker in (
            "punctuation",
            "comma",
            "colon",
            "dash",
            "parenthesis",
            "period",
            "quote",
            "semicolon",
        )
    ):
        return "punctuation"
    if any(
        marker in name
        for marker in (
            "repeat",
            "compression",
            "autocorrelation",
            "adjacent_sentence",
        )
    ):
        return "repetition_and_regularity"
    if any(marker in name for marker in ("paragraph", "sentence", "list_item")):
        return "document_structure"
    return "character_composition"


def _unit(name: str) -> str:
    if name.endswith("_per_10k_cjk"):
        return "occurrences per 10,000 CJK characters"
    if name.endswith("_per_1000_cjk"):
        return "occurrences per 1,000 CJK characters"
    if name.endswith("_entropy_bits"):
        return "bits"
    if name.endswith("_cjk_chars"):
        return "CJK characters"
    if name.endswith("_sentence_tokens"):
        return "tokens per sentence"
    if name.endswith(("_distance_max", "_distance_mean")):
        return "token positions"
    if name.endswith("_distance_median"):
        return "token positions"
    if name.endswith("_count"):
        return "count"
    if name.endswith(("_ratio", "_coverage")):
        return "proportion"
    if name.endswith("_density"):
        return "occurrences per non-whitespace character"
    if name.endswith("_cv"):
        return "dimensionless coefficient of variation"
    if name.endswith("_autocorrelation"):
        return "correlation coefficient"
    if name.endswith(("_mattr", "_type_token_ratio")):
        return "proportion"
    if name.endswith("_depth"):
        return "dependency edges"
    if name.endswith("_branching"):
        return "dependents per non-leaf token"
    return "dimensionless"


def _definition(name: str) -> str:
    if name.startswith("upos_"):
        tag = name.removeprefix("upos_").removesuffix("_ratio").upper()
        return f"Parsed tokens tagged {tag} divided by all parsed tokens."
    if name.startswith("deprel_"):
        relation = name.removeprefix("deprel_").removesuffix("_ratio")
        return (
            f"Parsed dependencies with the Universal Dependencies relation "
            f"{relation} divided by all parsed tokens."
        )
    if name.startswith("discourse_") and name.endswith("_per_10k_cjk"):
        category = (
            name.removeprefix("discourse_")
            .removesuffix("_markers_per_10k_cjk")
            .replace("_", " ")
        )
        return (
            f"Occurrences of fixed {category} marker phrases divided by CJK "
            f"character count and multiplied by 10,000."
        )
    humanized = name.replace("_", " ")
    return (
        f"Document-level {humanized}. The exact deterministic formula and "
        f"normalization are specified in docs/feature-catalog.md."
    )


def _sensitivity(name: str) -> list[str]:
    sensitivities: list[str] = []
    if name.endswith("_count"):
        sensitivities.append("document_length")
    if name.startswith(("syntax_", "upos_", "deprel_")):
        sensitivities.extend(["parser_model", "tokenization"])
    if name.startswith("discourse_"):
        sensitivities.extend(["marker_lexicon", "topic", "genre"])
    if name.startswith("title_"):
        sensitivities.extend(["platform_title_policy", "genre"])
    if name.startswith("surface_"):
        sensitivities.extend(["text_normalization", "genre"])
    return sorted(set(sensitivities))


def build_feature_catalog(feature_names: list[str]) -> list[dict[str, Any]]:
    """Return stable metadata for a sorted list of numeric feature columns."""

    return [
        {
            "definition": _definition(name),
            "family": _family(name),
            "known_sensitivities": _sensitivity(name),
            "name": name,
            "requires_syntax_annotation": name.startswith(
                ("deprel_", "syntax_", "upos_")
            ),
            "unit": _unit(name),
        }
        for name in sorted(feature_names)
    ]
