"""One-off GPU exploration of directions in the 30-document pilot corpus."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import torch

IDENTIFIERS = {
    "cohort",
    "doc_id",
    "format",
    "published_at",
    "published_month",
    "source",
    "topic",
}
KNOWN_TRANSLATION_IDS = {"b186cdd4f9004e0413395bf3"}
STYLE_SPARSE_FAMILIES = {
    "dependency_path",
    "dependency_treelet",
    "function_word",
    "pos_2gram",
    "pos_3gram",
    "pos_4gram",
    "punctuation_run",
    "root_pos",
    "sentence_opening",
}


def load_dense(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        feature_names = [
            name for name in reader.fieldnames or [] if name not in IDENTIFIERS
        ]
        rows: list[dict[str, Any]] = []
        for raw in reader:
            row: dict[str, Any] = {name: raw[name] for name in IDENTIFIERS}
            row.update({name: float(raw[name]) for name in feature_names})
            rows.append(row)
    return rows, feature_names


def load_dense_catalog(path: Path) -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in json.loads(path.read_text(encoding="utf-8"))}


def load_sparse(
    catalog_path: Path,
    values_path: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, float]]]:
    catalog = {
        item["feature_id"]: item
        for item in json.loads(catalog_path.read_text(encoding="utf-8"))
    }
    values: dict[str, dict[str, float]] = defaultdict(dict)
    with values_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            values[row["doc_id"]][row["feature_id"]] = float(
                row["rate_per_1000_opportunities"]
            )
    return catalog, dict(values)


def hedges_g(group_zero: list[float], group_one: list[float]) -> float | None:
    if len(group_zero) < 2 or len(group_one) < 2:
        return None
    degrees = len(group_zero) + len(group_one) - 2
    pooled_variance = (
        (len(group_zero) - 1) * statistics.variance(group_zero)
        + (len(group_one) - 1) * statistics.variance(group_one)
    ) / degrees
    mean_difference = statistics.fmean(group_one) - statistics.fmean(group_zero)
    if pooled_variance <= 1e-20:
        return 0.0 if abs(mean_difference) <= 1e-20 else None
    correction = 1.0 - 3.0 / (4.0 * degrees - 1.0)
    return correction * mean_difference / math.sqrt(pooled_variance)


def cliffs_delta(group_zero: list[float], group_one: list[float]) -> float:
    wins = sum(one > zero for one in group_one for zero in group_zero)
    losses = sum(one < zero for one in group_one for zero in group_zero)
    return (wins - losses) / (len(group_zero) * len(group_one))


def direction(value: float | None) -> int:
    if value is None or abs(value) < 1e-12:
        return 0
    return 1 if value > 0 else -1


def leave_one_out_direction_stability(
    group_zero: list[float],
    group_one: list[float],
) -> float:
    full_direction = direction(
        statistics.fmean(group_one) - statistics.fmean(group_zero)
    )
    if full_direction == 0:
        return 0.0
    directions: list[int] = []
    for index in range(len(group_zero)):
        reduced = group_zero[:index] + group_zero[index + 1 :]
        directions.append(
            direction(statistics.fmean(group_one) - statistics.fmean(reduced))
        )
    for index in range(len(group_one)):
        reduced = group_one[:index] + group_one[index + 1 :]
        directions.append(
            direction(statistics.fmean(reduced) - statistics.fmean(group_zero))
        )
    return sum(item == full_direction for item in directions) / len(directions)


def effect_record(
    group_zero: list[float],
    group_one: list[float],
) -> dict[str, float | None]:
    return {
        "cliffs_delta": cliffs_delta(group_zero, group_one),
        "hedges_g": hedges_g(group_zero, group_one),
        "loo_direction_stability": leave_one_out_direction_stability(
            group_zero,
            group_one,
        ),
        "mean_difference": statistics.fmean(group_one) - statistics.fmean(group_zero),
        "mean_group_one": statistics.fmean(group_one),
        "mean_group_zero": statistics.fmean(group_zero),
    }


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=lambda index: p_values[index])
    adjusted = [1.0] * len(p_values)
    running = 1.0
    for reversed_rank in range(len(order) - 1, -1, -1):
        index = order[reversed_rank]
        rank = reversed_rank + 1
        running = min(running, p_values[index] * len(p_values) / rank)
        adjusted[index] = min(1.0, running)
    return adjusted


def gpu_permutation_p_values(
    matrix: list[list[float]],
    labels: list[int],
    *,
    permutations: int,
    seed: int,
    device: torch.device,
) -> list[float]:
    torch.manual_seed(seed)
    data = torch.tensor(matrix, dtype=torch.float32, device=device)
    label_tensor = torch.tensor(labels, dtype=torch.bool, device=device)
    group_one_count = int(label_tensor.sum().item())
    group_zero_count = len(labels) - group_one_count
    total = data.sum(dim=0)
    observed_group_one = data[label_tensor].mean(dim=0)
    observed_group_zero = data[~label_tensor].mean(dim=0)
    observed = (observed_group_one - observed_group_zero).abs()
    extreme = torch.zeros(data.shape[1], dtype=torch.int64, device=device)
    remaining = permutations
    batch_size = min(512, permutations)
    while remaining:
        current = min(batch_size, remaining)
        random_scores = torch.rand((current, len(labels)), device=device)
        indices = random_scores.topk(group_one_count, dim=1).indices
        masks = torch.zeros(
            (current, len(labels)),
            dtype=torch.float32,
            device=device,
        )
        masks.scatter_(1, indices, 1.0)
        group_one_sum = masks @ data
        differences = (
            group_one_sum / group_one_count
            - (total.unsqueeze(0) - group_one_sum) / group_zero_count
        ).abs()
        extreme += (differences >= observed.unsqueeze(0) - 1e-7).sum(dim=0)
        remaining -= current
    return [float(value) for value in ((extreme + 1) / (permutations + 1)).cpu()]


def auc_score(labels: list[int], scores: list[float]) -> float:
    positives = [score for label, score in zip(labels, scores, strict=True) if label]
    negatives = [
        score for label, score in zip(labels, scores, strict=True) if not label
    ]
    wins = sum(positive > negative for positive in positives for negative in negatives)
    ties = sum(positive == negative for positive in positives for negative in negatives)
    return (wins + 0.5 * ties) / (len(positives) * len(negatives))


def ridge_loo(
    matrix: torch.Tensor,
    labels: list[int],
    *,
    top_k: int,
    regularization: float,
) -> dict[str, Any]:
    predictions: list[int] = []
    scores: list[float] = []
    selected_counts: Counter[int] = Counter()
    labels_tensor = torch.tensor(labels, dtype=torch.float32, device=matrix.device)
    for held_out in range(matrix.shape[0]):
        training_indices = [
            index for index in range(matrix.shape[0]) if index != held_out
        ]
        training = matrix[training_indices]
        training_labels = labels_tensor[training_indices]
        means = training.mean(dim=0)
        standard_deviations = training.std(dim=0, unbiased=False)
        valid = standard_deviations > 1e-6
        standardized = torch.zeros_like(training)
        standardized[:, valid] = (
            training[:, valid] - means[valid]
        ) / standard_deviations[valid]
        held_standardized = torch.zeros(matrix.shape[1], device=matrix.device)
        held_standardized[valid] = (
            matrix[held_out, valid] - means[valid]
        ) / standard_deviations[valid]
        group_zero = standardized[training_labels == 0]
        group_one = standardized[training_labels == 1]
        standardized_differences = (
            group_one.mean(dim=0) - group_zero.mean(dim=0)
        ).abs()
        standardized_differences[~valid] = -1
        selected = standardized_differences.topk(min(top_k, int(valid.sum()))).indices
        for index in selected.tolist():
            selected_counts[index] += 1
        design = torch.cat(
            [
                standardized[:, selected],
                torch.ones((len(training_indices), 1), device=matrix.device),
            ],
            dim=1,
        )
        target = training_labels * 2.0 - 1.0
        identity = torch.eye(design.shape[1], device=matrix.device)
        identity[-1, -1] = 0.0
        coefficients = torch.linalg.solve(
            design.T @ design + regularization * identity,
            design.T @ target,
        )
        held_design = torch.cat(
            [held_standardized[selected], torch.ones(1, device=matrix.device)]
        )
        score = float((held_design @ coefficients).item())
        scores.append(score)
        predictions.append(int(score > 0))
    accuracy = sum(
        prediction == label
        for prediction, label in zip(predictions, labels, strict=True)
    ) / len(labels)
    return {
        "accuracy": accuracy,
        "auc": auc_score(labels, scores),
        "predictions": predictions,
        "scores": scores,
        "selected_feature_counts": dict(selected_counts),
    }


def pca_diagnostic(
    matrix: torch.Tensor,
    labels: list[int],
) -> dict[str, Any]:
    means = matrix.mean(dim=0)
    standard_deviations = matrix.std(dim=0, unbiased=False)
    valid = standard_deviations > 1e-6
    standardized = (matrix[:, valid] - means[valid]) / standard_deviations[valid]
    _, singular_values, right = torch.linalg.svd(standardized, full_matrices=False)
    scores = standardized @ right.T
    variance = singular_values.square()
    explained = variance / variance.sum()
    label_tensor = torch.tensor(labels, dtype=torch.bool, device=matrix.device)
    first_components = scores[:, : min(5, scores.shape[1])]
    centroid_difference = first_components[label_tensor].mean(dim=0) - first_components[
        ~label_tensor
    ].mean(dim=0)
    pc1 = scores[:, 0]
    label_float = label_tensor.float()
    correlation = torch.corrcoef(torch.stack([pc1, label_float]))[0, 1]
    return {
        "cohort_centroid_distance_first_five_pcs": float(
            torch.linalg.vector_norm(centroid_difference).item()
        ),
        "explained_variance_first_five": [
            float(value) for value in explained[:5].cpu()
        ],
        "pc1_cohort_correlation": float(correlation.item()),
        "retained_feature_count": int(valid.sum().item()),
    }


def ridge_ablation_diagnostics(
    matrix: torch.Tensor,
    labels: list[int],
    feature_names: list[str],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    punctuation_aliases = {"deprel_punct_ratio", "upos_punct_ratio"}
    definitions = {
        "all_dense": list(range(len(feature_names))),
        "without_punctuation_or_title": [
            index
            for index, feature in enumerate(feature_names)
            if catalog[feature]["family"] not in {"punctuation", "title_form"}
            and feature not in punctuation_aliases
        ],
        "grammar_only": [
            index
            for index, feature in enumerate(feature_names)
            if catalog[feature]["family"]
            in {"dependency_relation", "dependency_syntax", "universal_pos"}
            and feature not in punctuation_aliases
            and not feature.endswith("_count")
        ],
        "discourse_and_repetition": [
            index
            for index, feature in enumerate(feature_names)
            if catalog[feature]["family"]
            in {"discourse_and_stance", "repetition_and_regularity"}
        ],
        "document_structure": [
            index
            for index, feature in enumerate(feature_names)
            if catalog[feature]["family"] == "document_structure"
        ],
        "lexical_and_character": [
            index
            for index, feature in enumerate(feature_names)
            if catalog[feature]["family"]
            in {"character_composition", "token_and_lexical"}
            and not feature.endswith("_count")
        ],
    }
    results: dict[str, Any] = {}
    for offset, (name, indices) in enumerate(definitions.items()):
        subset = matrix[:, indices]
        observed = ridge_loo(
            subset,
            labels,
            top_k=min(5, len(indices)),
            regularization=3.0,
        )
        random_generator = random.Random(20260830 + offset)
        permutation_accuracies: list[float] = []
        for _ in range(100):
            permuted = list(labels)
            random_generator.shuffle(permuted)
            permutation_accuracies.append(
                ridge_loo(
                    subset,
                    permuted,
                    top_k=min(5, len(indices)),
                    regularization=3.0,
                )["accuracy"]
            )
        results[name] = {
            "accuracy": observed["accuracy"],
            "auc": observed["auc"],
            "feature_count": len(indices),
            "label_permutation_p_value": (
                sum(value >= observed["accuracy"] for value in permutation_accuracies)
                + 1
            )
            / (len(permutation_accuracies) + 1),
            "permuted_accuracy_mean": statistics.fmean(permutation_accuracies),
        }
    return results


def dense_analysis(
    rows: list[dict[str, Any]],
    feature_names: list[str],
    catalog: dict[str, dict[str, Any]],
    *,
    permutations: int,
    device: torch.device,
) -> dict[str, Any]:
    infoq = [row for row in rows if row["source"] == "infoq"]
    infoq_clean = [row for row in infoq if row["doc_id"] not in KNOWN_TRANSLATION_IDS]
    infoq_pre = [row for row in infoq if row["cohort"] == "pre"]
    infoq_post = [row for row in infoq if row["cohort"] == "post"]
    clean_post = [row for row in infoq_clean if row["cohort"] == "post"]
    machine_heart_pre = [
        row for row in rows if row["source"] == "jiqizhixin" and row["cohort"] == "pre"
    ]

    matrix = [[row[name] for name in feature_names] for row in infoq]
    labels = [int(row["cohort"] == "post") for row in infoq]
    p_values = gpu_permutation_p_values(
        matrix,
        labels,
        permutations=permutations,
        seed=20260821,
        device=device,
    )
    q_values = benjamini_hochberg(p_values)
    ranked: list[dict[str, Any]] = []
    for feature_index, feature in enumerate(feature_names):
        pre_values = [row[feature] for row in infoq_pre]
        post_values = [row[feature] for row in infoq_post]
        clean_values = [row[feature] for row in clean_post]
        source_values = [row[feature] for row in machine_heart_pre]
        time_effect = effect_record(pre_values, post_values)
        clean_effect = effect_record(pre_values, clean_values)
        source_effect = effect_record(pre_values, source_values)
        time_g = time_effect["hedges_g"]
        clean_g = clean_effect["hedges_g"]
        source_g = source_effect["hedges_g"]
        if time_g is None:
            source_ratio = None
            score = 0.0
        else:
            source_ratio = (
                abs(source_g) / abs(time_g)
                if source_g is not None and abs(time_g) > 1e-12
                else 0.0
            )
            translation_consistent = direction(time_g) == direction(clean_g)
            score = (
                abs(time_g)
                * float(time_effect["loo_direction_stability"])
                / (1.0 + source_ratio)
                if translation_consistent
                else 0.0
            )
        ranked.append(
            {
                "feature": feature,
                "family": catalog[feature]["family"],
                "permutation_p_value": p_values[feature_index],
                "q_value": q_values[feature_index],
                "ranking_score": score,
                "source_effect_pre_machine_heart_minus_pre_infoq": source_effect,
                "source_to_time_abs_g_ratio": source_ratio,
                "time_effect_post_minus_pre": time_effect,
                "translation_removed_effect_post_minus_pre": clean_effect,
                "translation_sign_consistent": direction(time_g) == direction(clean_g),
            }
        )
    ranked.sort(key=lambda item: (-item["ranking_score"], item["feature"]))

    matrix_tensor = torch.tensor(matrix, dtype=torch.float32, device=device)
    ridge_results = {
        str(top_k): ridge_loo(
            matrix_tensor,
            labels,
            top_k=top_k,
            regularization=3.0,
        )
        for top_k in (3, 5, 10)
    }
    random_generator = random.Random(20260821)
    permutation_accuracies: list[float] = []
    for _ in range(100):
        permuted = list(labels)
        random_generator.shuffle(permuted)
        permutation_accuracies.append(
            ridge_loo(
                matrix_tensor,
                permuted,
                top_k=5,
                regularization=3.0,
            )["accuracy"]
        )
    observed_accuracy = ridge_results["5"]["accuracy"]
    ridge_results["5"]["label_permutation_p_value"] = (
        sum(value >= observed_accuracy for value in permutation_accuracies) + 1
    ) / (len(permutation_accuracies) + 1)
    ridge_results["5"]["permuted_accuracy_mean"] = statistics.fmean(
        permutation_accuracies
    )
    return {
        "ablation_ridge_loo": ridge_ablation_diagnostics(
            matrix_tensor,
            labels,
            feature_names,
            catalog,
        ),
        "pca": pca_diagnostic(matrix_tensor, labels),
        "ranked_features": ranked,
        "ridge_loo": ridge_results,
    }


def sparse_analysis(
    rows: list[dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    values: dict[str, dict[str, float]],
    *,
    permutations: int,
    device: torch.device,
) -> dict[str, Any]:
    infoq = sorted(
        (row for row in rows if row["source"] == "infoq"),
        key=lambda row: row["doc_id"],
    )
    infoq_pre = [row for row in infoq if row["cohort"] == "pre"]
    infoq_post = [row for row in infoq if row["cohort"] == "post"]
    clean_post = [
        row for row in infoq_post if row["doc_id"] not in KNOWN_TRANSLATION_IDS
    ]
    machine_heart_pre = [
        row for row in rows if row["source"] == "jiqizhixin" and row["cohort"] == "pre"
    ]
    feature_ids = sorted(catalog)
    matrix = [
        [
            values.get(row["doc_id"], {}).get(feature_id, 0.0)
            for feature_id in feature_ids
        ]
        for row in infoq
    ]
    labels = [int(row["cohort"] == "post") for row in infoq]
    p_values = gpu_permutation_p_values(
        matrix,
        labels,
        permutations=permutations,
        seed=20260822,
        device=device,
    )
    q_values = benjamini_hochberg(p_values)
    ranked: list[dict[str, Any]] = []
    for feature_index, feature_id in enumerate(feature_ids):
        pre_values = [
            values.get(row["doc_id"], {}).get(feature_id, 0.0) for row in infoq_pre
        ]
        post_values = [
            values.get(row["doc_id"], {}).get(feature_id, 0.0) for row in infoq_post
        ]
        clean_values = [
            values.get(row["doc_id"], {}).get(feature_id, 0.0) for row in clean_post
        ]
        source_values = [
            values.get(row["doc_id"], {}).get(feature_id, 0.0)
            for row in machine_heart_pre
        ]
        pre_presence = sum(value > 0 for value in pre_values)
        post_presence = sum(value > 0 for value in post_values)
        if pre_presence + post_presence < 4:
            continue
        time_effect = effect_record(pre_values, post_values)
        clean_effect = effect_record(pre_values, clean_values)
        source_effect = effect_record(pre_values, source_values)
        time_g = time_effect["hedges_g"]
        clean_g = clean_effect["hedges_g"]
        source_g = source_effect["hedges_g"]
        if time_g is None:
            source_ratio = None
            score = 0.0
        else:
            source_ratio = (
                abs(source_g) / abs(time_g)
                if source_g is not None and abs(time_g) > 1e-12
                else 0.0
            )
            score = (
                abs(time_g)
                * float(time_effect["loo_direction_stability"])
                / (1.0 + source_ratio)
                if direction(time_g) == direction(clean_g)
                else 0.0
            )
        metadata = catalog[feature_id]
        ranked.append(
            {
                "family": metadata["family"],
                "feature_id": feature_id,
                "pattern": metadata["pattern"],
                "permutation_p_value": p_values[feature_index],
                "post_presence": post_presence,
                "pre_presence": pre_presence,
                "q_value": q_values[feature_index],
                "ranking_score": score,
                "source_to_time_abs_g_ratio": source_ratio,
                "time_effect_post_minus_pre": time_effect,
                "translation_removed_effect_post_minus_pre": clean_effect,
                "translation_sign_consistent": direction(time_g) == direction(clean_g),
            }
        )
    ranked.sort(key=lambda item: (-item["ranking_score"], item["feature_id"]))
    style_ranked = [item for item in ranked if item["family"] in STYLE_SPARSE_FAMILIES]
    topic_ranked = [
        item
        for item in ranked
        if item["family"].startswith("char_") or item["family"] == "content_lemma"
    ]
    return {
        "ranked_style_patterns": style_ranked,
        "ranked_topic_sensitive_patterns": topic_ranked,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dense-permutations", type=int, default=20000)
    parser.add_argument("--sparse-permutations", type=int, default=5000)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this exploration")
    device = torch.device("cuda")
    rows, feature_names = load_dense(args.matrix_dir / "document_features.csv")
    dense_catalog = load_dense_catalog(args.matrix_dir / "feature_catalog.json")
    sparse_catalog, sparse_values = load_sparse(
        args.matrix_dir / "sparse_feature_catalog.json",
        args.matrix_dir / "sparse_feature_values.csv",
    )
    result = {
        "compute": {
            "cuda_version": torch.version.cuda,
            "device": torch.cuda.get_device_name(0),
            "torch_version": torch.__version__,
        },
        "known_translation_ids_removed_in_sensitivity": sorted(KNOWN_TRANSLATION_IDS),
        "sample_counts": {
            "all_documents": len(rows),
            "infoq_post": sum(
                row["source"] == "infoq" and row["cohort"] == "post" for row in rows
            ),
            "infoq_pre": sum(
                row["source"] == "infoq" and row["cohort"] == "pre" for row in rows
            ),
            "machine_heart_pre": sum(
                row["source"] == "jiqizhixin" and row["cohort"] == "pre" for row in rows
            ),
        },
        "dense": dense_analysis(
            rows,
            feature_names,
            dense_catalog,
            permutations=args.dense_permutations,
            device=device,
        ),
        "sparse": sparse_analysis(
            rows,
            sparse_catalog,
            sparse_values,
            permutations=args.sparse_permutations,
            device=device,
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dense_rows = result["dense"]["ranked_features"]
    write_csv(
        args.output_dir / "dense_ranked.csv",
        [
            {
                "feature": item["feature"],
                "family": item["family"],
                "hedges_g": item["time_effect_post_minus_pre"]["hedges_g"],
                "cliffs_delta": item["time_effect_post_minus_pre"]["cliffs_delta"],
                "loo_stability": item["time_effect_post_minus_pre"][
                    "loo_direction_stability"
                ],
                "translation_removed_g": item[
                    "translation_removed_effect_post_minus_pre"
                ]["hedges_g"],
                "source_to_time_abs_g_ratio": item["source_to_time_abs_g_ratio"],
                "permutation_p_value": item["permutation_p_value"],
                "q_value": item["q_value"],
                "ranking_score": item["ranking_score"],
            }
            for item in dense_rows
        ],
        [
            "feature",
            "family",
            "hedges_g",
            "cliffs_delta",
            "loo_stability",
            "translation_removed_g",
            "source_to_time_abs_g_ratio",
            "permutation_p_value",
            "q_value",
            "ranking_score",
        ],
    )
    sparse_rows = result["sparse"]["ranked_style_patterns"]
    write_csv(
        args.output_dir / "sparse_style_ranked.csv",
        [
            {
                "feature_id": item["feature_id"],
                "family": item["family"],
                "pattern": item["pattern"],
                "hedges_g": item["time_effect_post_minus_pre"]["hedges_g"],
                "loo_stability": item["time_effect_post_minus_pre"][
                    "loo_direction_stability"
                ],
                "translation_removed_g": item[
                    "translation_removed_effect_post_minus_pre"
                ]["hedges_g"],
                "source_to_time_abs_g_ratio": item["source_to_time_abs_g_ratio"],
                "pre_presence": item["pre_presence"],
                "post_presence": item["post_presence"],
                "permutation_p_value": item["permutation_p_value"],
                "q_value": item["q_value"],
                "ranking_score": item["ranking_score"],
            }
            for item in sparse_rows
        ],
        [
            "feature_id",
            "family",
            "pattern",
            "hedges_g",
            "loo_stability",
            "translation_removed_g",
            "source_to_time_abs_g_ratio",
            "pre_presence",
            "post_presence",
            "permutation_p_value",
            "q_value",
            "ranking_score",
        ],
    )
    print(
        json.dumps(
            {
                "dense_features": len(feature_names),
                "device": torch.cuda.get_device_name(0),
                "output_dir": str(args.output_dir),
                "sparse_features": len(sparse_catalog),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
