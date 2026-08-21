"""Probe typed support for explicit discourse relations in existing pilot data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import random
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from deaiodorant.analysis.config import load_feature_config
from deaiodorant.analysis.corpus import load_monthly_corpus
from deaiodorant.analysis.discourse_relations import (
    SCHEMA_VERSION,
    analyze_relation_support,
)
from deaiodorant.analysis.pipeline import validate_annotation_provenance
from deaiodorant.analysis.stanza_backend import (
    PROCESSORS,
    _configure_determinism,
    _load_stanza,
    _model_fingerprint,
)
from deaiodorant.analysis.syntax import DependencyToken, read_conllu

KNOWN_TRANSLATION = "b186cdd4f9004e0413395bf3"
RATING_SCORES = {
    "顺畅，愿意继续读": 0,
    "有点卡，但还能读": 1,
    "很难读，不想继续": 2,
}
IDENTITY_COLUMNS = {
    "cohort",
    "doc_id",
    "friction_score",
    "month",
    "outcome",
    "period",
    "published_month",
    "rating",
    "task_number",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _prepare_output_directory(path: Path) -> Path:
    path = path.resolve()
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Output directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {column: row.get(column) for column in columns} for row in rows
        )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def _median(values: list[float]) -> float:
    return statistics.median(values)


def _robust_scale(values: list[float], location: float | None = None) -> float:
    center = _median(values) if location is None else location
    deviations = [abs(value - center) for value in values]
    mad_scale = 1.4826 * _median(deviations)
    if mad_scale > 0:
        return mad_scale
    mean_absolute_scale = 1.2533 * statistics.fmean(deviations)
    if mean_absolute_scale > 0:
        return mean_absolute_scale
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _huber_location(
    values: list[float], *, tuning_constant: float
) -> tuple[float, float]:
    location = _median(values)
    scale = _robust_scale(values, location)
    if scale == 0:
        return location, scale
    for _ in range(50):
        cutoff = tuning_constant * scale
        weights = [
            min(1.0, cutoff / abs(value - location)) if value != location else 1.0
            for value in values
        ]
        updated = sum(weight * value for weight, value in zip(weights, values)) / sum(
            weights
        )
        if abs(updated - location) <= max(scale, 1.0) * 1e-10:
            location = updated
            break
        location = updated
    return location, scale


def _robust_effect(
    pre: list[float],
    post: list[float],
    *,
    tuning_constant: float,
) -> float:
    pre_location, pre_scale = _huber_location(pre, tuning_constant=tuning_constant)
    post_location, post_scale = _huber_location(post, tuning_constant=tuning_constant)
    denominator = math.sqrt((pre_scale**2 + post_scale**2) / 2)
    if denominator == 0:
        denominator = _robust_scale(pre + post)
    return (post_location - pre_location) / denominator if denominator else 0.0


def _hedges_g(pre: list[float], post: list[float]) -> float:
    pre_variance = statistics.variance(pre)
    post_variance = statistics.variance(post)
    degrees = len(pre) + len(post) - 2
    pooled_variance = (
        (len(pre) - 1) * pre_variance + (len(post) - 1) * post_variance
    ) / degrees
    if pooled_variance == 0:
        return 0.0
    correction = 1 - 3 / (4 * (len(pre) + len(post)) - 9)
    return (
        correction
        * (statistics.fmean(post) - statistics.fmean(pre))
        / math.sqrt(pooled_variance)
    )


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def _time_loo_stability(
    pre: list[float],
    post: list[float],
    observed: float,
    *,
    tuning_constant: float,
) -> float:
    observed_sign = _sign(observed)
    if observed_sign == 0:
        return 0.0
    effects = [
        _robust_effect(
            pre[:index] + pre[index + 1 :],
            post,
            tuning_constant=tuning_constant,
        )
        for index in range(len(pre))
    ]
    effects.extend(
        _robust_effect(
            pre,
            post[:index] + post[index + 1 :],
            tuning_constant=tuning_constant,
        )
        for index in range(len(post))
    )
    return sum(_sign(effect) == observed_sign for effect in effects) / len(effects)


def _benjamini_hochberg(rows: list[dict[str, Any]], p_field: str) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: item[1][p_field])
    running = 1.0
    for reversed_rank, (index, row) in enumerate(reversed(ordered), start=1):
        rank = len(rows) - reversed_rank + 1
        adjusted = min(1.0, row[p_field] * len(rows) / rank)
        running = min(running, adjusted)
        rows[index]["bh_q_value"] = running


def _time_comparison(
    rows: list[dict[str, Any]],
    feature_names: list[str],
    *,
    permutations: int,
    seed: int,
    tuning_constant: float,
) -> list[dict[str, Any]]:
    pre_rows = [row for row in rows if row["cohort"] == "pre"]
    post_rows = [row for row in rows if row["cohort"] == "post"]
    if len(pre_rows) != 10 or len(post_rows) != 10:
        raise ValueError("The time comparison requires 10 pre and 10 post documents")
    rng = random.Random(seed)
    values_indices = list(range(len(rows)))
    shuffled_pre_indices = [
        set(rng.sample(values_indices, len(pre_rows))) for _ in range(permutations)
    ]
    output: list[dict[str, Any]] = []
    for feature in feature_names:
        pre = [float(row[feature]) for row in pre_rows]
        post = [float(row[feature]) for row in post_rows]
        if len(set(pre + post)) < 2:
            continue
        observed = _robust_effect(pre, post, tuning_constant=tuning_constant)
        all_values = pre + post
        exceedances = 1
        for selected in shuffled_pre_indices:
            shuffled_pre = [
                value for index, value in enumerate(all_values) if index in selected
            ]
            shuffled_post = [
                value for index, value in enumerate(all_values) if index not in selected
            ]
            permuted = _robust_effect(
                shuffled_pre,
                shuffled_post,
                tuning_constant=tuning_constant,
            )
            exceedances += abs(permuted) >= abs(observed) - 1e-12
        post_without_translation = [
            float(row[feature])
            for row in post_rows
            if row["doc_id"] != KNOWN_TRANSLATION
        ]
        translation_removed = _robust_effect(
            pre,
            post_without_translation,
            tuning_constant=tuning_constant,
        )
        unweighted = _hedges_g(pre, post)
        output.append(
            {
                "feature": feature,
                "pre_mean": statistics.fmean(pre),
                "post_mean": statistics.fmean(post),
                "robust_effect_post_minus_pre": observed,
                "unweighted_hedges_g": unweighted,
                "direction_matches_unweighted": _sign(observed) == _sign(unweighted),
                "translation_removed_robust_effect": translation_removed,
                "translation_removed_direction_consistent": (
                    _sign(translation_removed) == _sign(observed)
                ),
                "loo_direction_stability": _time_loo_stability(
                    pre,
                    post,
                    observed,
                    tuning_constant=tuning_constant,
                ),
                "permutation_p_value": exceedances / (permutations + 1),
            }
        )
    _benjamini_hochberg(output, "permutation_p_value")
    output.sort(
        key=lambda row: (
            -abs(row["robust_effect_post_minus_pre"]),
            row["permutation_p_value"],
            row["feature"],
        )
    )
    return output


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        average_rank = (cursor + 1 + end) / 2
        for index in order[cursor:end]:
            ranks[index] = average_rank
        cursor = end
    return ranks


def _pearson(left: list[float], right: list[float]) -> float:
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((x - left_mean) ** 2 for x in left)
        * sum((y - right_mean) ** 2 for y in right)
    )
    return numerator / denominator if denominator else 0.0


def _spearman(left: list[float], right: list[float]) -> float:
    return _pearson(_average_ranks(left), _average_ranks(right))


def _unique_multiset_permutations(values: list[int]) -> Iterable[list[int]]:
    counts = Counter(values)
    keys = sorted(counts)
    output = [0] * len(values)

    def visit(index: int) -> Iterable[list[int]]:
        if index == len(output):
            yield list(output)
            return
        for key in keys:
            if counts[key] == 0:
                continue
            counts[key] -= 1
            output[index] = key
            yield from visit(index + 1)
            counts[key] += 1

    yield from visit(0)


def _reader_loo_stability(
    values: list[float], scores: list[float], observed: float
) -> float:
    observed_sign = _sign(observed)
    if observed_sign == 0:
        return 0.0
    correlations = [
        _spearman(
            values[:index] + values[index + 1 :],
            scores[:index] + scores[index + 1 :],
        )
        for index in range(len(values))
    ]
    return sum(_sign(value) == observed_sign for value in correlations) / len(
        correlations
    )


def _reader_comparison(
    rows: list[dict[str, Any]], feature_names: list[str]
) -> tuple[list[dict[str, Any]], int]:
    scores = [int(row["friction_score"]) for row in rows]
    permutations = list(_unique_multiset_permutations(scores))
    output: list[dict[str, Any]] = []
    for feature in feature_names:
        values = [float(row[feature]) for row in rows]
        if len(set(values)) < 2:
            continue
        observed = _spearman(values, [float(score) for score in scores])
        exceedances = sum(
            abs(_spearman(values, [float(score) for score in permuted]))
            >= abs(observed) - 1e-12
            for permuted in permutations
        )
        output.append(
            {
                "feature": feature,
                "spearman_rho": observed,
                "exact_p_value": exceedances / len(permutations),
                "loo_direction_stability": _reader_loo_stability(
                    values,
                    [float(score) for score in scores],
                    observed,
                ),
            }
        )
    _benjamini_hochberg(output, "exact_p_value")
    output.sort(
        key=lambda row: (
            -abs(row["spearman_rho"]),
            row["exact_p_value"],
            row["feature"],
        )
    )
    return output, len(permutations)


def _analyze_text(
    nlp: Any, text: str
) -> tuple[list[dict[str, Any]], dict[str, float | int]]:
    return analyze_relation_support(_parsed_sentences(nlp(text)))


def _intervention_summary(
    rows: list[dict[str, Any]], feature_names: list[str]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for feature in feature_names:
        deltas = [float(row[f"delta__{feature}"]) for row in rows]
        revised_wins = [
            float(row[f"delta__{feature}"])
            for row in rows
            if row["outcome"] == "revised_preferred"
        ]
        ties = [
            float(row[f"delta__{feature}"])
            for row in rows
            if row["outcome"] == "tie_or_neither"
        ]
        output.append(
            {
                "feature": feature,
                "mean_delta_revised_minus_original": statistics.fmean(deltas),
                "median_delta_revised_minus_original": statistics.median(deltas),
                "decrease_count": sum(value < 0 for value in deltas),
                "unchanged_count": sum(value == 0 for value in deltas),
                "increase_count": sum(value > 0 for value in deltas),
                "revised_win_mean_delta": (
                    statistics.fmean(revised_wins) if revised_wins else 0.0
                ),
                "tie_mean_delta": statistics.fmean(ties) if ties else 0.0,
            }
        )
    output.sort(
        key=lambda row: (
            row["mean_delta_revised_minus_original"],
            row["feature"],
        )
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--reader-tasks", type=Path, required=True)
    parser.add_argument("--reader-ratings", type=Path, required=True)
    parser.add_argument("--refinement-answer-key", type=Path, required=True)
    parser.add_argument("--refinement-results", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260822)
    parser.add_argument("--tuning-constant", type=float, default=1.5)
    args = parser.parse_args()
    if args.permutations < 1:
        raise ValueError("permutations must be positive")
    if args.tuning_constant <= 0:
        raise ValueError("tuning-constant must be positive")

    output_dir = _prepare_output_directory(args.output_dir)
    config = load_feature_config(args.config)
    corpus = load_monthly_corpus(
        args.corpus_root,
        pre_end_exclusive=config.pre_end_exclusive,
        post_start_inclusive=config.post_start_inclusive,
    )
    annotation_manifest, annotation_manifest_hash = validate_annotation_provenance(
        args.annotations,
        corpus_fingerprint=corpus.corpus_fingerprint,
        documents=corpus.documents,
    )
    documents = [
        document
        for document in corpus.documents
        if document.source == "infoq" and document.cohort in {"pre", "post"}
    ]
    documents.sort(key=lambda item: (item.cohort, item.doc_id))

    all_instances: list[dict[str, Any]] = []
    document_rows: list[dict[str, Any]] = []
    for document in documents:
        parsed = read_conllu(args.annotations / f"{document.doc_id}.conllu")
        instances, features = analyze_relation_support(parsed)
        document_rows.append(
            {
                "doc_id": document.doc_id,
                "cohort": document.cohort,
                "published_month": document.published_at.strftime("%Y-%m"),
                **features,
            }
        )
        all_instances.extend(
            {
                "scope": "document",
                "doc_id": document.doc_id,
                "cohort": document.cohort,
                **instance,
            }
            for instance in instances
        )
    feature_names = sorted(set(document_rows[0]) - IDENTITY_COLUMNS)
    time_rows = _time_comparison(
        document_rows,
        feature_names,
        permutations=args.permutations,
        seed=args.seed,
        tuning_constant=args.tuning_constant,
    )

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

    reader_tasks = json.loads(args.reader_tasks.read_text(encoding="utf-8"))
    rating_payload = json.loads(args.reader_ratings.read_text(encoding="utf-8"))
    ratings = rating_payload["ratings"]
    ratings_by_number = {item["task_number"]: item for item in ratings}
    reader_rows: list[dict[str, Any]] = []
    with torch.inference_mode():
        for task in sorted(reader_tasks, key=lambda item: item["data"]["task_number"]):
            task_number = task["data"]["task_number"]
            rating = ratings_by_number[task_number]
            if any(
                task["meta"][field] != rating[field]
                for field in ("doc_id", "month", "target_lines")
            ):
                raise ValueError(f"Reader metadata mismatch for task {task_number}")
            instances, features = _analyze_text(nlp, task["data"]["target"])
            period = (
                "pre"
                if rating["month"] < "2023-01"
                else "post" if rating["month"] >= "2025-07" else "transition"
            )
            reader_rows.append(
                {
                    "task_number": task_number,
                    "doc_id": rating["doc_id"],
                    "month": rating["month"],
                    "period": period,
                    "rating": rating["rating"],
                    "friction_score": RATING_SCORES[rating["rating"]],
                    **features,
                }
            )
            all_instances.extend(
                {
                    "scope": "reader_passage",
                    "doc_id": rating["doc_id"],
                    "task_number": task_number,
                    **instance,
                }
                for instance in instances
            )
    post_reader_rows = [row for row in reader_rows if row["period"] == "post"]
    reader_rows_stats, reader_permutation_count = _reader_comparison(
        post_reader_rows, feature_names
    )

    answer_key = json.loads(args.refinement_answer_key.read_text(encoding="utf-8"))
    refinement_payload = json.loads(args.refinement_results.read_text(encoding="utf-8"))
    outcomes_by_pair = {item["pair_id"]: item for item in refinement_payload["pairs"]}
    intervention_rows: list[dict[str, Any]] = []
    with torch.inference_mode():
        for pair in sorted(answer_key, key=lambda item: item["task_number"]):
            outcome = outcomes_by_pair[pair["pair_id"]]
            if outcome["task_number"] != pair["task_number"]:
                raise ValueError(f"Refinement metadata mismatch for {pair['pair_id']}")
            original_instances, original_features = _analyze_text(nlp, pair["original"])
            revised_instances, revised_features = _analyze_text(nlp, pair["revised"])
            row: dict[str, Any] = {
                "task_number": pair["task_number"],
                "pair_id": pair["pair_id"],
                "outcome": outcome["outcome"],
            }
            for feature in feature_names:
                original_value = float(original_features[feature])
                revised_value = float(revised_features[feature])
                row[f"original__{feature}"] = original_value
                row[f"revised__{feature}"] = revised_value
                row[f"delta__{feature}"] = revised_value - original_value
            intervention_rows.append(row)
            all_instances.extend(
                {
                    "scope": "refinement_original",
                    "pair_id": pair["pair_id"],
                    "task_number": pair["task_number"],
                    **instance,
                }
                for instance in original_instances
            )
            all_instances.extend(
                {
                    "scope": "refinement_revised",
                    "pair_id": pair["pair_id"],
                    "task_number": pair["task_number"],
                    **instance,
                }
                for instance in revised_instances
            )
    intervention_stats = _intervention_summary(intervention_rows, feature_names)

    time_by_feature = {row["feature"]: row for row in time_rows}
    reader_by_feature = {row["feature"]: row for row in reader_rows_stats}
    intervention_by_feature = {row["feature"]: row for row in intervention_stats}
    intersection: list[dict[str, Any]] = []
    for feature in sorted(
        set(time_by_feature) & set(reader_by_feature) & set(intervention_by_feature)
    ):
        time_item = time_by_feature[feature]
        reader_item = reader_by_feature[feature]
        intervention_item = intervention_by_feature[feature]
        intersection.append(
            {
                "feature": feature,
                "time_robust_effect_post_minus_pre": time_item[
                    "robust_effect_post_minus_pre"
                ],
                "time_permutation_p_value": time_item["permutation_p_value"],
                "time_bh_q_value": time_item["bh_q_value"],
                "time_loo_direction_stability": time_item["loo_direction_stability"],
                "reader_spearman_rho": reader_item["spearman_rho"],
                "reader_exact_p_value": reader_item["exact_p_value"],
                "reader_bh_q_value": reader_item["bh_q_value"],
                "reader_loo_direction_stability": reader_item[
                    "loo_direction_stability"
                ],
                "intervention_mean_delta_revised_minus_original": intervention_item[
                    "mean_delta_revised_minus_original"
                ],
                "intervention_decrease_count": intervention_item["decrease_count"],
                "direction_aligned": (
                    time_item["robust_effect_post_minus_pre"] > 0
                    and reader_item["spearman_rho"] > 0
                    and intervention_item["mean_delta_revised_minus_original"] < 0
                ),
            }
        )
    intersection.sort(
        key=lambda row: (
            not row["direction_aligned"],
            -abs(row["time_robust_effect_post_minus_pre"]),
            -abs(row["reader_spearman_rho"]),
            row["feature"],
        )
    )

    _write_csv(
        output_dir / "document_relation_features.csv",
        document_rows,
        ["doc_id", "cohort", "published_month"] + feature_names,
    )
    _write_csv(
        output_dir / "time_comparison.csv",
        time_rows,
        [
            "feature",
            "pre_mean",
            "post_mean",
            "robust_effect_post_minus_pre",
            "unweighted_hedges_g",
            "direction_matches_unweighted",
            "translation_removed_robust_effect",
            "translation_removed_direction_consistent",
            "loo_direction_stability",
            "permutation_p_value",
            "bh_q_value",
        ],
    )
    _write_csv(
        output_dir / "reader_passage_features.csv",
        reader_rows,
        [
            "task_number",
            "doc_id",
            "month",
            "period",
            "rating",
            "friction_score",
        ]
        + feature_names,
    )
    _write_csv(
        output_dir / "reader_correlations_post.csv",
        reader_rows_stats,
        [
            "feature",
            "spearman_rho",
            "exact_p_value",
            "bh_q_value",
            "loo_direction_stability",
        ],
    )
    intervention_columns = ["task_number", "pair_id", "outcome"]
    for feature in feature_names:
        intervention_columns.extend(
            [f"original__{feature}", f"revised__{feature}", f"delta__{feature}"]
        )
    _write_csv(
        output_dir / "refinement_feature_deltas.csv",
        intervention_rows,
        intervention_columns,
    )
    _write_csv(
        output_dir / "refinement_summary.csv",
        intervention_stats,
        [
            "feature",
            "mean_delta_revised_minus_original",
            "median_delta_revised_minus_original",
            "decrease_count",
            "unchanged_count",
            "increase_count",
            "revised_win_mean_delta",
            "tie_mean_delta",
        ],
    )
    _write_jsonl(output_dir / "relation_instances.jsonl", all_instances)

    result = {
        "artifact_type": "deterministic-discourse-relation-support-probe",
        "annotation_manifest_sha256": annotation_manifest_hash,
        "annotation_parser": annotation_manifest["parser"],
        "caveats": [
            "The evidence rules are lexical and syntactic; indeterminate is not unsupported.",
            "The time comparison contains only ten InfoQ documents per cohort.",
            "The reader analysis contains eight post-period passages and one reader.",
            "The refinement variants were selected to change these constructions, so feature reduction is a manipulation check.",
            "No result is a general semantic entailment or causal-validity judgment.",
        ],
        "config_sha256": _sha256(args.config),
        "corpus_fingerprint": corpus.corpus_fingerprint,
        "document_count": len(document_rows),
        "feature_count": len(feature_names),
        "instance_claimed_type_counts": dict(
            sorted(Counter(item["claimed_type"] for item in all_instances).items())
        ),
        "instance_decision_counts": dict(
            sorted(Counter(item["decision"] for item in all_instances).items())
        ),
        "instance_scope_counts": dict(
            sorted(Counter(item["scope"] for item in all_instances).items())
        ),
        "intersection": intersection,
        "model": {
            "device": args.device,
            "file_count": model_file_count,
            "fingerprint": model_fingerprint,
            "language": "zh-hans",
            "package": "gsdsimp",
            "processors": PROCESSORS.split(","),
            "stanza_version": stanza.__version__,
        },
        "permutations": args.permutations,
        "python_version": platform.python_version(),
        "reader": {
            "post_task_count": len(post_reader_rows),
            "exact_permutation_count": reader_permutation_count,
            "ratings_sha256": _sha256(args.reader_ratings),
            "tasks_sha256": _sha256(args.reader_tasks),
            "top_features": reader_rows_stats[:10],
        },
        "refinement": {
            "answer_key_sha256": _sha256(args.refinement_answer_key),
            "pair_count": len(intervention_rows),
            "results_sha256": _sha256(args.refinement_results),
            "top_feature_deltas": intervention_stats[:10],
        },
        "relation_schema_version": SCHEMA_VERSION,
        "seed": args.seed,
        "time": {
            "known_translation_sensitivity_id": KNOWN_TRANSLATION,
            "post_count": sum(row["cohort"] == "post" for row in document_rows),
            "pre_count": sum(row["cohort"] == "pre" for row in document_rows),
            "top_features": time_rows[:10],
        },
        "tuning_constant": args.tuning_constant,
    }
    _write_json(output_dir / "results.json", result)
    print(
        json.dumps(
            {
                "document_count": len(document_rows),
                "feature_count": len(feature_names),
                "instance_count": len(all_instances),
                "output_dir": str(output_dir),
                "post_reader_count": len(post_reader_rows),
                "refinement_pair_count": len(intervention_rows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
