"""Probe deterministic integration-load features on controlled text variants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from deaiodorant.analysis.stanza_backend import (
    PROCESSORS,
    _configure_determinism,
    _load_stanza,
    _model_fingerprint,
)
from deaiodorant.analysis.syntax import DependencyToken


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CONTENT_POS = frozenset({"ADJ", "ADV", "NOUN", "PROPN", "VERB"})
FUNCTION_POS = frozenset({"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "SCONJ"})
PREDICATE_POS = frozenset({"ADJ", "NOUN", "VERB"})
ARGUMENT_RELATIONS = frozenset({"csubj", "iobj", "nsubj", "obj", "obl"})
SUBORDINATE_RELATIONS = frozenset({"acl", "advcl", "ccomp", "csubj", "xcomp"})
NOMINAL_MODIFIER_RELATIONS = frozenset({"acl", "amod", "compound", "nmod"})
LONG_DEPENDENCY_THRESHOLD = 5
LONG_NOMINAL_MODIFIER_THRESHOLD = 4

FEATURE_DIRECTIONS = {
    "argument_anchored_clause_ratio": "lower",
    "cjk_chars_per_sentence": "higher",
    "clause_heads_per_sentence": "higher",
    "content_tokens_per_clause_head": "higher",
    "content_tokens_per_sentence": "higher",
    "coordination_relations_per_sentence": "higher",
    "distinct_content_lemmas_per_sentence": "higher",
    "function_to_content_ratio": "lower",
    "long_dependency_arc_ratio": "higher",
    "long_nominal_modifier_ratio": "higher",
    "max_clause_heads_in_sentence": "higher",
    "max_dependency_distance": "higher",
    "max_nominal_modifier_chain": "higher",
    "mean_dependency_distance": "higher",
    "mean_nominal_modifier_span": "higher",
    "mean_tree_depth": "higher",
    "subordinate_relations_per_sentence": "higher",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parsed_sentences(document: Any) -> list[list[DependencyToken]]:
    return [
        [
            DependencyToken(
                token_id=int(word.id),
                form=word.text,
                lemma=word.lemma or "_",
                upos=word.upos or "X",
                head=int(word.head),
                deprel=word.deprel or "dep",
            )
            for word in sentence.words
        ]
        for sentence in document.sentences
    ]


def _relation(token: DependencyToken) -> str:
    return token.deprel.split(":", 1)[0]


def _lemma(token: DependencyToken) -> str:
    return (token.lemma if token.lemma != "_" else token.form).casefold()


def _mean(values: list[float | int]) -> float:
    return statistics.fmean(values) if values else 0.0


def _tree_depths(sentence: list[DependencyToken]) -> list[int]:
    by_id = {token.token_id: token for token in sentence}
    depths: list[int] = []
    for token in sentence:
        depth = 0
        current = token
        while current.head:
            depth += 1
            current = by_id[current.head]
        depths.append(depth)
    return depths


def _clause_heads(sentence: list[DependencyToken]) -> list[DependencyToken]:
    predicates = [token for token in sentence if token.upos == "VERB"]
    if predicates:
        return predicates
    root = next(token for token in sentence if token.head == 0)
    return [root] if root.upos in PREDICATE_POS else []


def _nominal_modifier_chain(token: DependencyToken, by_id: dict[int, DependencyToken]) -> int:
    depth = 0
    current = token
    while current.head and _relation(current) in NOMINAL_MODIFIER_RELATIONS:
        head = by_id[current.head]
        if head.upos not in {"NOUN", "PROPN"}:
            break
        depth += 1
        current = head
    return depth


def integration_features(
    text: str,
    sentences: list[list[DependencyToken]],
) -> dict[str, float | int]:
    """Return an interpretable feature vector without a composite burden score."""

    all_tokens = [token for sentence in sentences for token in sentence]
    lexical_tokens = [
        token for token in all_tokens if token.upos not in {"PUNCT", "SYM"}
    ]
    content_tokens = [token for token in lexical_tokens if token.upos in CONTENT_POS]
    function_tokens = [token for token in lexical_tokens if token.upos in FUNCTION_POS]
    clause_heads_by_sentence = [_clause_heads(sentence) for sentence in sentences]
    clause_heads = [token for items in clause_heads_by_sentence for token in items]

    dependency_distances: list[int] = []
    nominal_modifier_spans: list[int] = []
    nominal_chains: list[int] = []
    tree_depths: list[int] = []
    anchored_clause_count = 0
    subordinate_count = 0
    coordination_count = 0
    distinct_content_counts: list[int] = []
    content_counts: list[int] = []

    for sentence, sentence_clause_heads in zip(
        sentences, clause_heads_by_sentence, strict=True
    ):
        by_id = {token.token_id: token for token in sentence}
        by_head: dict[int, list[DependencyToken]] = defaultdict(list)
        for token in sentence:
            by_head[token.head].append(token)
            relation = _relation(token)
            subordinate_count += relation in SUBORDINATE_RELATIONS
            coordination_count += relation in {"cc", "conj"}
            if token.head and token.upos not in {"PUNCT", "SYM"}:
                dependency_distances.append(abs(token.token_id - token.head))
            if (
                token.head
                and relation in NOMINAL_MODIFIER_RELATIONS
                and by_id[token.head].upos in {"NOUN", "PROPN"}
            ):
                nominal_modifier_spans.append(abs(token.token_id - token.head))
                nominal_chains.append(_nominal_modifier_chain(token, by_id))
        for predicate in sentence_clause_heads:
            anchored_clause_count += any(
                _relation(child) in ARGUMENT_RELATIONS
                for child in by_head[predicate.token_id]
            )
        sentence_content = [
            token for token in sentence if token.upos in CONTENT_POS
        ]
        content_counts.append(len(sentence_content))
        distinct_content_counts.append(
            len({_lemma(token) for token in sentence_content})
        )
        tree_depths.extend(_tree_depths(sentence))

    sentence_count = len(sentences)
    clause_count = len(clause_heads)
    content_count = len(content_tokens)
    return {
        "argument_anchored_clause_ratio": (
            anchored_clause_count / clause_count if clause_count else 0.0
        ),
        "cjk_char_count": len(CJK_RE.findall(text)),
        "cjk_chars_per_sentence": (
            len(CJK_RE.findall(text)) / sentence_count if sentence_count else 0.0
        ),
        "clause_head_count": clause_count,
        "clause_heads_per_sentence": (
            clause_count / sentence_count if sentence_count else 0.0
        ),
        "content_token_count": content_count,
        "content_tokens_per_clause_head": (
            content_count / clause_count if clause_count else 0.0
        ),
        "content_tokens_per_sentence": _mean(content_counts),
        "coordination_relations_per_sentence": (
            coordination_count / sentence_count if sentence_count else 0.0
        ),
        "distinct_content_lemmas_per_sentence": _mean(distinct_content_counts),
        "function_to_content_ratio": (
            len(function_tokens) / content_count if content_count else 0.0
        ),
        "long_dependency_arc_ratio": (
            sum(value >= LONG_DEPENDENCY_THRESHOLD for value in dependency_distances)
            / len(dependency_distances)
            if dependency_distances
            else 0.0
        ),
        "long_nominal_modifier_ratio": (
            sum(
                value >= LONG_NOMINAL_MODIFIER_THRESHOLD
                for value in nominal_modifier_spans
            )
            / len(nominal_modifier_spans)
            if nominal_modifier_spans
            else 0.0
        ),
        "max_clause_heads_in_sentence": max(
            (len(items) for items in clause_heads_by_sentence), default=0
        ),
        "max_dependency_distance": max(dependency_distances, default=0),
        "max_nominal_modifier_chain": max(nominal_chains, default=0),
        "mean_dependency_distance": _mean(dependency_distances),
        "mean_nominal_modifier_span": _mean(nominal_modifier_spans),
        "mean_tree_depth": _mean(tree_depths),
        "sentence_count": sentence_count,
        "subordinate_relations_per_sentence": (
            subordinate_count / sentence_count if sentence_count else 0.0
        ),
        "token_count": len(lexical_tokens),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _preferred_variant(result: dict[str, Any]) -> str | None:
    outcome = result["outcome"]
    if outcome == "original_preferred":
        return "original"
    if outcome == "revised_preferred":
        return "revised"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer-key", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--seed", type=int, default=2026082703)
    args = parser.parse_args()

    answer_key = json.loads(args.answer_key.read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text(encoding="utf-8"))
    keyed_results = {item["pair_id"]: item for item in results["pairs"]}
    if set(keyed_results) != {item["pair_id"] for item in answer_key["pairs"]}:
        raise ValueError("Answer key and result pair identities differ")
    if results["source"]["answer_key_sha256"] != _sha256(args.answer_key):
        raise ValueError("Answer-key fingerprint differs from the blinded result record")

    stanza = _load_stanza()
    torch = _configure_determinism(args.seed, args.device)
    model_fingerprint, model_file_count = _model_fingerprint(
        args.model_dir.resolve(), "zh-hans"
    )
    options: dict[str, Any] = {
        "dir": str(args.model_dir.resolve()),
        "lang": "zh-hans",
        "package": "gsdsimp",
        "processors": PROCESSORS,
        "use_gpu": args.device == "cuda",
        "verbose": False,
    }
    if hasattr(stanza, "DownloadMethod"):
        options["download_method"] = stanza.DownloadMethod.NONE
    nlp = stanza.Pipeline(**options)

    variant_rows: list[dict[str, Any]] = []
    with torch.inference_mode():
        for pair in sorted(answer_key["pairs"], key=lambda item: item["task_number"]):
            result = keyed_results[pair["pair_id"]]
            for variant, text in (
                ("original", pair["operation"]["before"]),
                ("revised", pair["operation"]["after"]),
            ):
                parsed = _parsed_sentences(nlp(text))
                variant_rows.append(
                    {
                        "task_number": pair["task_number"],
                        "pair_id": pair["pair_id"],
                        "doc_id": pair["doc_id"],
                        "variant": variant,
                        "side": (
                            pair["original_side"]
                            if variant == "original"
                            else ("B" if pair["original_side"] == "A" else "A")
                        ),
                        "outcome": result["outcome"],
                        "preferred_variant": _preferred_variant(result),
                        **integration_features(text, parsed),
                    }
                )

    by_pair: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in variant_rows:
        by_pair[row["pair_id"]][row["variant"]] = row

    pair_rows: list[dict[str, Any]] = []
    for pair in sorted(answer_key["pairs"], key=lambda item: item["task_number"]):
        original = by_pair[pair["pair_id"]]["original"]
        revised = by_pair[pair["pair_id"]]["revised"]
        pair_rows.append(
            {
                "task_number": pair["task_number"],
                "pair_id": pair["pair_id"],
                "doc_id": pair["doc_id"],
                "original_side": pair["original_side"],
                "outcome": keyed_results[pair["pair_id"]]["outcome"],
                **{
                    f"revision_minus_original__{feature}": (
                        float(revised[feature]) - float(original[feature])
                    )
                    for feature in FEATURE_DIRECTIONS
                },
            }
        )

    metric_summaries: list[dict[str, Any]] = []
    decisive = [
        row for row in pair_rows if row["outcome"] != "tie_or_neither"
    ]
    for feature, burden_direction in FEATURE_DIRECTIONS.items():
        original_values = [
            float(by_pair[row["pair_id"]]["original"][feature])
            for row in pair_rows
        ]
        revised_values = [
            float(by_pair[row["pair_id"]]["revised"][feature])
            for row in pair_rows
        ]
        deltas = [
            float(row[f"revision_minus_original__{feature}"]) for row in pair_rows
        ]
        preferred_lower_burden = 0
        preferred_higher_burden = 0
        preferred_equal = 0
        for row in decisive:
            variants = by_pair[row["pair_id"]]
            preferred = _preferred_variant(keyed_results[row["pair_id"]])
            other = "revised" if preferred == "original" else "original"
            preferred_value = float(variants[preferred][feature])
            other_value = float(variants[other][feature])
            if preferred_value == other_value:
                preferred_equal += 1
            else:
                lower_is_better = burden_direction == "higher"
                preferred_is_lower = preferred_value < other_value
                preferred_lower_burden += preferred_is_lower == lower_is_better
                preferred_higher_burden += preferred_is_lower != lower_is_better
        metric_summaries.append(
            {
                "feature": feature,
                "putative_burden_direction": burden_direction,
                "original_median": statistics.median(original_values),
                "revised_median": statistics.median(revised_values),
                "revision_minus_original_median": statistics.median(deltas),
                "revision_increases_raw_value_count": sum(value > 0 for value in deltas),
                "revision_decreases_raw_value_count": sum(value < 0 for value in deltas),
                "preferred_side_has_lower_putative_burden": preferred_lower_burden,
                "preferred_side_has_higher_putative_burden": preferred_higher_burden,
                "preferred_side_equal": preferred_equal,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "variant_features.csv", variant_rows)
    _write_csv(args.output_dir / "pair_deltas.csv", pair_rows)
    summary = {
        "artifact_type": "deterministic-compositional-burden-development-probe",
        "schema_version": "deaiodorant-compositional-burden-probe-0.1",
        "seed": args.seed,
        "scope": {
            "pair_count": len(pair_rows),
            "decisive_pair_count": len(decisive),
            "result_role": results["role"],
            "all_decisive_choices_selected_side_b": all(
                item["preference"].startswith("B")
                for item in results["pairs"]
                if item["outcome"] != "tie_or_neither"
            ),
        },
        "identity": {
            "answer_key_sha256": _sha256(args.answer_key),
            "results_sha256": _sha256(args.results),
            "model_fingerprint": model_fingerprint,
            "model_file_count": model_file_count,
        },
        "thresholds": {
            "long_dependency_arc_tokens": LONG_DEPENDENCY_THRESHOLD,
            "long_nominal_modifier_tokens": LONG_NOMINAL_MODIFIER_THRESHOLD,
        },
        "metrics": metric_summaries,
        "interpretation_limits": [
            "The feature vector is exploratory and has no validated composite score.",
            "All decisive responses selected side B, so treatment-preference associations are position-confounded.",
            "Preference-alignment counts are descriptive diagnostics and must not tune thresholds or promote a smell.",
            "Universal Dependencies parses are deterministic measurements with parser error, not linguistic gold labels.",
        ],
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
