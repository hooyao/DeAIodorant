"""Relate blinded passage ratings to deterministic Chinese text features."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from deaiodorant.analysis.stanza_backend import (
    PROCESSORS,
    _configure_determinism,
    _load_stanza,
    _model_fingerprint,
)
from deaiodorant.analysis.discourse_graph import (
    build_discourse_graph,
    rhetorical_hypothesis_features,
)
from deaiodorant.analysis.surface import discourse_features, surface_features
from deaiodorant.analysis.syntax import DependencyToken, dependency_features


RATING_SCORES = {
    "顺畅，愿意继续读": 0,
    "有点卡，但还能读": 1,
    "很难读，不想继续": 2,
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
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left, right, strict=True)
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


def _exact_spearman_p(
    values: list[float],
    scores: list[int],
    permutations: list[list[int]],
) -> tuple[float, float]:
    observed = _spearman(values, [float(score) for score in scores])
    exceedances = sum(
        abs(_spearman(values, [float(score) for score in permutation]))
        >= abs(observed) - 1e-12
        for permutation in permutations
    )
    return observed, exceedances / len(permutations)


def _benjamini_hochberg(rows: list[dict[str, Any]]) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: item[1]["exact_p_value"])
    running = 1.0
    for rank_from_end, (index, row) in enumerate(reversed(ordered), start=1):
        rank = len(rows) - rank_from_end + 1
        adjusted = min(1.0, row["exact_p_value"] * len(rows) / rank)
        running = min(running, adjusted)
        rows[index]["bh_q_value"] = running


def _loo_sign_stability(values: list[float], scores: list[int], observed: float) -> float:
    if observed == 0:
        return 0.0
    sign = 1 if observed > 0 else -1
    stable = 0
    for held_out in range(len(values)):
        reduced_values = values[:held_out] + values[held_out + 1 :]
        reduced_scores = scores[:held_out] + scores[held_out + 1 :]
        correlation = _spearman(
            reduced_values,
            [float(score) for score in reduced_scores],
        )
        stable += correlation * sign > 0
    return stable / len(values)


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _correlation_rows(
    rows: list[dict[str, Any]],
    feature_names: list[str],
) -> tuple[list[dict[str, Any]], int]:
    scores = [int(row["friction_score"]) for row in rows]
    permutations = list(_unique_multiset_permutations(scores))
    correlations: list[dict[str, Any]] = []
    for feature in feature_names:
        values = [float(row[feature]) for row in rows]
        if len(set(values)) < 2:
            continue
        rho, p_value = _exact_spearman_p(values, scores, permutations)
        correlations.append(
            {
                "feature": feature,
                "spearman_rho": rho,
                "absolute_rho": abs(rho),
                "exact_p_value": p_value,
                "loo_direction_stability": _loo_sign_stability(values, scores, rho),
            }
        )
    _benjamini_hochberg(correlations)
    correlations.sort(
        key=lambda row: (
            -row["absolute_rho"],
            row["exact_p_value"],
            row["feature"],
        )
    )
    return correlations, len(permutations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--seed", type=int, default=20260821)
    args = parser.parse_args()

    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    rating_payload = json.loads(args.ratings.read_text(encoding="utf-8"))
    ratings = (
        rating_payload["ratings"]
        if isinstance(rating_payload, dict)
        else rating_payload
    )
    if len(tasks) != len(ratings):
        raise ValueError("Task and rating counts differ")
    ratings_by_number = {item["task_number"]: item for item in ratings}
    if len(ratings_by_number) != len(ratings):
        raise ValueError("Duplicate rating task numbers")

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

    rows: list[dict[str, Any]] = []
    graphs: list[dict[str, Any]] = []
    with torch.inference_mode():
        for task in sorted(tasks, key=lambda item: item["data"]["task_number"]):
            number = task["data"]["task_number"]
            rating = ratings_by_number[number]
            if any(
                rating[key] != task["meta"][key]
                for key in ("doc_id", "month", "target_lines")
            ):
                raise ValueError(f"Rating metadata mismatch for task {number}")
            target = task["data"]["target"]
            features: dict[str, float | int] = {}
            features.update(surface_features(target))
            features.update(discourse_features(target))
            features.update(rhetorical_hypothesis_features(target))
            parsed_sentences = _parsed_sentences(nlp(target))
            features.update(dependency_features(parsed_sentences, mattr_window=100))
            graph, graph_features = build_discourse_graph(target, parsed_sentences)
            features.update(graph_features)
            graphs.append(
                {
                    "doc_id": rating["doc_id"],
                    "graph": graph,
                    "month": rating["month"],
                    "target_lines": rating["target_lines"],
                    "task_number": number,
                }
            )
            rows.append(
                {
                    "task_number": number,
                    "doc_id": rating["doc_id"],
                    "month": rating["month"],
                    "period": (
                        "pre"
                        if rating["month"] < "2023-01"
                        else "post"
                        if rating["month"] >= "2025-07"
                        else "transition"
                    ),
                    "rating": rating["rating"],
                    "friction_score": RATING_SCORES[rating["rating"]],
                    **features,
                }
            )

    identity_columns = {
        "doc_id",
        "friction_score",
        "month",
        "period",
        "rating",
        "task_number",
    }
    feature_names = sorted(set(rows[0]) - identity_columns)
    all_correlations, all_permutation_count = _correlation_rows(rows, feature_names)
    post_rows = [row for row in rows if row["period"] == "post"]
    post_correlations, post_permutation_count = _correlation_rows(
        post_rows, feature_names
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_dir / "passage_features.csv",
        rows,
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
    (args.output_dir / "discourse_graphs.json").write_text(
        json.dumps(graphs, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_csv(
        args.output_dir / "feature_correlations_all_sensitivity.csv",
        all_correlations,
        [
            "feature",
            "spearman_rho",
            "absolute_rho",
            "exact_p_value",
            "bh_q_value",
            "loo_direction_stability",
        ],
    )
    _write_csv(
        args.output_dir / "feature_correlations_post.csv",
        post_correlations,
        [
            "feature",
            "spearman_rho",
            "absolute_rho",
            "exact_p_value",
            "bh_q_value",
            "loo_direction_stability",
        ],
    )
    result = {
        "artifact_type": "reader-friction-calibration",
        "caveats": [
            "The sample contains only ten purposively selected passages.",
            "The same reader supplied all ratings.",
            "Feature correlations are exploratory and not validation results.",
            "The hypothesis proxy list predates these ratings but remains weak by design.",
        ],
        "feature_count": len(post_correlations),
        "model": {
            "device": args.device,
            "file_count": model_file_count,
            "fingerprint": model_fingerprint,
            "language": "zh-hans",
            "package": "gsdsimp",
            "processors": PROCESSORS.split(","),
            "stanza_version": stanza.__version__,
        },
        "all_period_sensitivity": {
            "permutation_count": all_permutation_count,
            "task_count": len(rows),
            "top_features": all_correlations[:20],
        },
        "post_period_primary": {
            "permutation_count": post_permutation_count,
            "task_count": len(post_rows),
            "top_features": post_correlations[:20],
        },
        "python_version": platform.python_version(),
        "rating_counts": dict(
            sorted(Counter(int(row["friction_score"]) for row in rows).items())
        ),
        "rating_scale": RATING_SCORES,
        "ratings_sha256": _sha256(args.ratings),
        "seed": args.seed,
        "task_count": len(rows),
        "tasks_sha256": _sha256(args.tasks),
    }
    (args.output_dir / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir.resolve()),
                "post_feature_count": len(post_correlations),
                "post_task_count": len(post_rows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
