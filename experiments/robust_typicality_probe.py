"""Estimate typical pre/post feature shifts under cohort-wise contamination."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from deaiodorant.analysis.discourse_graph import (
    build_discourse_graph,
    rhetorical_hypothesis_features,
)
from deaiodorant.analysis.syntax import read_conllu


IDENTIFIER_COLUMNS = {
    "cohort",
    "doc_id",
    "format",
    "published_at",
    "published_month",
    "source",
    "topic",
}
KNOWN_TRANSLATION = "b186cdd4f9004e0413395bf3"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _median(values: list[float]) -> float:
    return statistics.median(values)


def _robust_scale(values: list[float], location: float | None = None) -> float:
    if not values:
        return 0.0
    center = _median(values) if location is None else location
    deviations = [abs(value - center) for value in values]
    mad_scale = 1.4826 * _median(deviations)
    if mad_scale > 0:
        return mad_scale
    mean_absolute_scale = 1.2533 * statistics.fmean(deviations)
    if mean_absolute_scale > 0:
        return mean_absolute_scale
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _huber_location_weights(
    values: list[float],
    *,
    tuning_constant: float,
) -> tuple[float, float, list[float]]:
    """Return a fixed-scale Huber location and per-observation weights."""

    location = _median(values)
    scale = _robust_scale(values, location)
    if scale == 0:
        return location, scale, [1.0] * len(values)
    weights = [1.0] * len(values)
    for _ in range(50):
        cutoff = tuning_constant * scale
        weights = [
            min(1.0, cutoff / abs(value - location))
            if value != location
            else 1.0
            for value in values
        ]
        updated = sum(weight * value for weight, value in zip(weights, values)) / sum(
            weights
        )
        if abs(updated - location) <= max(scale, 1.0) * 1e-10:
            location = updated
            break
        location = updated
    cutoff = tuning_constant * scale
    weights = [
        min(1.0, cutoff / abs(value - location))
        if value != location
        else 1.0
        for value in values
    ]
    return location, scale, weights


def _effective_sample_size(weights: list[float]) -> float:
    squared_sum = sum(weight * weight for weight in weights)
    return sum(weights) ** 2 / squared_sum if squared_sum else 0.0


def _robust_effect(
    pre: list[float],
    post: list[float],
    *,
    tuning_constant: float,
) -> dict[str, Any]:
    pre_location, pre_scale, pre_weights = _huber_location_weights(
        pre, tuning_constant=tuning_constant
    )
    post_location, post_scale, post_weights = _huber_location_weights(
        post, tuning_constant=tuning_constant
    )
    denominator = math.sqrt((pre_scale**2 + post_scale**2) / 2)
    if denominator == 0:
        denominator = _robust_scale(pre + post)
    effect = (
        (post_location - pre_location) / denominator if denominator else 0.0
    )
    return {
        "effect": effect,
        "post_effective_n": _effective_sample_size(post_weights),
        "post_location": post_location,
        "post_scale": post_scale,
        "post_weights": post_weights,
        "pre_effective_n": _effective_sample_size(pre_weights),
        "pre_location": pre_location,
        "pre_scale": pre_scale,
        "pre_weights": pre_weights,
    }


def _hedges_g(pre: list[float], post: list[float]) -> float:
    if len(pre) < 2 or len(post) < 2:
        return 0.0
    pre_variance = statistics.variance(pre)
    post_variance = statistics.variance(post)
    degrees = len(pre) + len(post) - 2
    pooled_variance = (
        (len(pre) - 1) * pre_variance + (len(post) - 1) * post_variance
    ) / degrees
    if pooled_variance == 0:
        return 0.0
    correction = 1 - 3 / (4 * (len(pre) + len(post)) - 9)
    return correction * (
        statistics.fmean(post) - statistics.fmean(pre)
    ) / math.sqrt(pooled_variance)


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def _loo_direction_stability(
    pre: list[float],
    post: list[float],
    observed: float,
    *,
    tuning_constant: float,
) -> float:
    observed_sign = _sign(observed)
    if observed_sign == 0:
        return 0.0
    directions: list[int] = []
    for index in range(len(pre)):
        effect = _robust_effect(
            pre[:index] + pre[index + 1 :],
            post,
            tuning_constant=tuning_constant,
        )["effect"]
        directions.append(_sign(effect))
    for index in range(len(post)):
        effect = _robust_effect(
            pre,
            post[:index] + post[index + 1 :],
            tuning_constant=tuning_constant,
        )["effect"]
        directions.append(_sign(effect))
    return sum(direction == observed_sign for direction in directions) / len(directions)


def _permutation_p_value(
    values: list[float],
    pre_count: int,
    observed: float,
    *,
    permutations: list[list[int]],
    tuning_constant: float,
) -> float:
    exceedances = 1
    for pre_indices in permutations:
        pre_set = set(pre_indices)
        pre = [value for index, value in enumerate(values) if index in pre_set]
        post = [value for index, value in enumerate(values) if index not in pre_set]
        effect = _robust_effect(
            pre,
            post,
            tuning_constant=tuning_constant,
        )["effect"]
        exceedances += abs(effect) >= abs(observed) - 1e-12
    return exceedances / (len(permutations) + 1)


def _benjamini_hochberg(rows: list[dict[str, Any]]) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: item[1]["permutation_p_value"])
    running = 1.0
    for reversed_rank, (index, row) in enumerate(reversed(ordered), start=1):
        rank = len(rows) - reversed_rank + 1
        adjusted = min(1.0, row["permutation_p_value"] * len(rows) / rank)
        running = min(running, adjusted)
        rows[index]["q_value"] = running


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260821)
    parser.add_argument("--tuning-constant", type=float, default=1.5)
    args = parser.parse_args()
    if args.permutations < 1:
        raise ValueError("permutations must be positive")
    if args.tuning_constant <= 0:
        raise ValueError("tuning-constant must be positive")

    with args.matrix.open("r", encoding="utf-8", newline="") as handle:
        input_rows = list(csv.DictReader(handle))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    family_by_feature = {item["name"]: item["family"] for item in catalog}
    primary = [
        row
        for row in input_rows
        if row["source"] == "infoq" and row["cohort"] in {"pre", "post"}
    ]
    primary.sort(key=lambda row: (row["cohort"], row["doc_id"]))
    for row in primary:
        text_path = (
            args.corpus_root / row["published_month"] / f"{row['doc_id']}.txt"
        )
        annotation_path = args.annotations / f"{row['doc_id']}.conllu"
        text = text_path.read_text(encoding="utf-8")
        graph, graph_features = build_discourse_graph(
            text,
            read_conllu(annotation_path),
        )
        del graph
        row.update(
            {
                key: str(value)
                for key, value in {
                    **rhetorical_hypothesis_features(text),
                    **graph_features,
                }.items()
            }
        )
    pre_rows = [row for row in primary if row["cohort"] == "pre"]
    post_rows = [row for row in primary if row["cohort"] == "post"]
    if len(pre_rows) != 10 or len(post_rows) != 10:
        raise ValueError("The pilot expects 10 pre and 10 post InfoQ documents")
    feature_names = sorted(set(primary[0]) - IDENTIFIER_COLUMNS)

    rng = random.Random(args.seed)
    all_indices = list(range(len(primary)))
    permutation_indices = [
        sorted(rng.sample(all_indices, len(pre_rows)))
        for _ in range(args.permutations)
    ]
    document_feature_weights: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    results: list[dict[str, Any]] = []
    for feature in feature_names:
        pre = [float(row[feature]) for row in pre_rows]
        post = [float(row[feature]) for row in post_rows]
        if len(set(pre + post)) < 2:
            continue
        robust = _robust_effect(
            pre,
            post,
            tuning_constant=args.tuning_constant,
        )
        unweighted_g = _hedges_g(pre, post)
        post_without_translation = [
            float(row[feature])
            for row in post_rows
            if row["doc_id"] != KNOWN_TRANSLATION
        ]
        translation_removed = _robust_effect(
            pre,
            post_without_translation,
            tuning_constant=args.tuning_constant,
        )["effect"]
        values = pre + post
        p_value = _permutation_p_value(
            values,
            len(pre),
            robust["effect"],
            permutations=permutation_indices,
            tuning_constant=args.tuning_constant,
        )
        family = family_by_feature.get(
            feature,
            "discourse_graph"
            if feature.startswith("graph_")
            else "rhetorical_hypothesis"
            if feature.startswith("hypothesis_")
            else "unknown",
        )
        for row, weight in zip(pre_rows, robust["pre_weights"], strict=True):
            document_feature_weights[row["doc_id"]][family].append(weight)
        for row, weight in zip(post_rows, robust["post_weights"], strict=True):
            document_feature_weights[row["doc_id"]][family].append(weight)
        minimum_effective_fraction = min(
            robust["pre_effective_n"] / len(pre),
            robust["post_effective_n"] / len(post),
        )
        loo_stability = _loo_direction_stability(
            pre,
            post,
            robust["effect"],
            tuning_constant=args.tuning_constant,
        )
        results.append(
            {
                "feature": feature,
                "family": family,
                "pre_huber_location": robust["pre_location"],
                "post_huber_location": robust["post_location"],
                "robust_effect_post_minus_pre": robust["effect"],
                "unweighted_hedges_g": unweighted_g,
                "direction_matches_unweighted": (
                    _sign(robust["effect"]) == _sign(unweighted_g)
                ),
                "translation_removed_robust_effect": translation_removed,
                "translation_removed_direction_consistent": (
                    _sign(translation_removed) == _sign(robust["effect"])
                ),
                "pre_effective_n": robust["pre_effective_n"],
                "post_effective_n": robust["post_effective_n"],
                "minimum_effective_fraction": minimum_effective_fraction,
                "loo_direction_stability": loo_stability,
                "permutation_p_value": p_value,
                "ranking_score": (
                    abs(robust["effect"])
                    * minimum_effective_fraction
                    * loo_stability
                    if _sign(robust["effect"]) == _sign(unweighted_g)
                    and _sign(translation_removed) == _sign(robust["effect"])
                    else 0.0
                ),
            }
        )
    _benjamini_hochberg(results)
    results.sort(
        key=lambda row: (
            -row["ranking_score"],
            row["permutation_p_value"],
            row["feature"],
        )
    )

    typicality_rows: list[dict[str, Any]] = []
    families = sorted({item["family"] for item in results})
    for row in primary:
        family_scores = {
            family: (
                statistics.fmean(document_feature_weights[row["doc_id"]][family])
                if document_feature_weights[row["doc_id"]][family]
                else 1.0
            )
            for family in families
        }
        typicality_rows.append(
            {
                "doc_id": row["doc_id"],
                "cohort": row["cohort"],
                "published_month": row["published_month"],
                "overall_typicality_weight": statistics.fmean(
                    family_scores.values()
                ),
                **{f"family_{key}": value for key, value in family_scores.items()},
            }
        )
    typicality_rows.sort(key=lambda row: (row["cohort"], row["overall_typicality_weight"]))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    feature_columns = [
        "feature",
        "family",
        "pre_huber_location",
        "post_huber_location",
        "robust_effect_post_minus_pre",
        "unweighted_hedges_g",
        "direction_matches_unweighted",
        "translation_removed_robust_effect",
        "translation_removed_direction_consistent",
        "pre_effective_n",
        "post_effective_n",
        "minimum_effective_fraction",
        "loo_direction_stability",
        "permutation_p_value",
        "q_value",
        "ranking_score",
    ]
    _write_csv(args.output_dir / "robust_feature_ranked.csv", results, feature_columns)
    typicality_columns = [
        "doc_id",
        "cohort",
        "published_month",
        "overall_typicality_weight",
    ] + [f"family_{family}" for family in families]
    _write_csv(
        args.output_dir / "document_typicality.csv",
        typicality_rows,
        typicality_columns,
    )
    summary = {
        "artifact_type": "robust-cohort-typicality-probe",
        "caveats": [
            "The pilot contains only ten documents per cohort.",
            "Feature-wise Huber weights estimate typical shifts but do not identify authorship.",
            "Overall document typicality is descriptive and must not become a hard admission rule.",
            "Topic and format are not matched in this pilot.",
        ],
        "cohort_counts": {"post": len(post_rows), "pre": len(pre_rows)},
        "feature_count": len(results),
        "known_translation_sensitivity_id": KNOWN_TRANSLATION,
        "matrix_sha256": _sha256(args.matrix),
        "method": {
            "location": "fixed-scale Huber M-estimator",
            "permutations": args.permutations,
            "scale": "MAD with mean-absolute-deviation fallback",
            "seed": args.seed,
            "tuning_constant": args.tuning_constant,
            "weighting_scope": "within cohort and feature",
        },
        "top_features": results[:20],
        "lowest_typicality_documents": typicality_rows[:5],
    }
    (args.output_dir / "results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "feature_count": len(results),
                "output_dir": str(args.output_dir.resolve()),
                "permutations": args.permutations,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
