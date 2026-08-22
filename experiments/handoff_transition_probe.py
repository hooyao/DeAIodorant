"""Explore transition-period surface features from a read-only corpus handoff."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from deaiodorant.analysis.discourse_graph import rhetorical_hypothesis_features
from deaiodorant.analysis.surface import (
    discourse_features,
    surface_features,
    title_features,
)

PROTOCOL_VERSION = "handoff-transition-exploration-1.0"
TRANSITION_START = dt.date(2023, 1, 1)
POST_START = dt.date(2025, 7, 1)
PRE_END = dt.date(2023, 1, 1)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


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


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {column: row.get(column) for column in columns} for row in rows
        )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
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
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((value - left_mean) ** 2 for value in left)
        * sum((value - right_mean) ** 2 for value in right)
    )
    return numerator / denominator if denominator else 0.0


def _spearman(left: list[float], right: list[float]) -> float:
    return _pearson(_average_ranks(left), _average_ranks(right))


def _partial_correlation(
    feature_ranks: list[float],
    date_ranks: list[float],
    length_ranks: list[float],
) -> float:
    feature_date = _pearson(feature_ranks, date_ranks)
    feature_length = _pearson(feature_ranks, length_ranks)
    date_length = _pearson(date_ranks, length_ranks)
    denominator = math.sqrt(max(0.0, (1 - feature_length**2) * (1 - date_length**2)))
    return (
        (feature_date - feature_length * date_length) / denominator
        if denominator
        else 0.0
    )


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def _combined_source_partial(
    rows_by_source: dict[str, list[dict[str, Any]]],
    feature: str,
) -> tuple[float, dict[str, float], float]:
    source_values: dict[str, float] = {}
    length_values: dict[str, float] = {}
    total = sum(len(rows) for rows in rows_by_source.values())
    combined = 0.0
    combined_length = 0.0
    for source, rows in sorted(rows_by_source.items()):
        values = [float(row[feature]) for row in rows]
        dates = [float(row["days_into_transition"]) for row in rows]
        lengths = [math.log1p(float(row["indexed_cjk_chars"])) for row in rows]
        partial = _partial_correlation(
            _average_ranks(values),
            _average_ranks(dates),
            _average_ranks(lengths),
        )
        length_rho = _spearman(values, lengths)
        source_values[source] = partial
        length_values[source] = length_rho
        combined += len(rows) / total * partial
        combined_length += len(rows) / total * length_rho
    return combined, source_values, combined_length


def _transition_permutations(
    rows_by_source: dict[str, list[dict[str, Any]]],
    *,
    count: int,
    seed: int,
) -> dict[str, list[list[int]]]:
    rng = random.Random(seed)
    output: dict[str, list[list[int]]] = {}
    for source, rows in sorted(rows_by_source.items()):
        indices = list(range(len(rows)))
        output[source] = []
        for _ in range(count):
            shuffled = list(indices)
            rng.shuffle(shuffled)
            output[source].append(shuffled)
    return output


def _permutation_p_value(
    rows_by_source: dict[str, list[dict[str, Any]]],
    feature: str,
    observed: float,
    permutations: dict[str, list[list[int]]],
) -> float:
    source_state: dict[str, dict[str, Any]] = {}
    total = sum(len(rows) for rows in rows_by_source.values())
    for source, rows in sorted(rows_by_source.items()):
        source_state[source] = {
            "feature_ranks": _average_ranks([float(row[feature]) for row in rows]),
            "date_ranks": _average_ranks(
                [float(row["days_into_transition"]) for row in rows]
            ),
            "length_ranks": _average_ranks(
                [math.log1p(float(row["indexed_cjk_chars"])) for row in rows]
            ),
            "weight": len(rows) / total,
        }
    permutation_count = len(next(iter(permutations.values())))
    exceedances = 1
    for permutation_index in range(permutation_count):
        combined = 0.0
        for source, state in sorted(source_state.items()):
            shuffled_date = [
                state["date_ranks"][index]
                for index in permutations[source][permutation_index]
            ]
            combined += state["weight"] * _partial_correlation(
                state["feature_ranks"],
                shuffled_date,
                state["length_ranks"],
            )
        exceedances += abs(combined) >= abs(observed) - 1e-12
    return exceedances / (permutation_count + 1)


def _loo_stability(rows: list[dict[str, Any]], feature: str, observed: float) -> float:
    observed_sign = _sign(observed)
    if observed_sign == 0:
        return 0.0
    directions: list[int] = []
    for held_out in range(len(rows)):
        reduced = rows[:held_out] + rows[held_out + 1 :]
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in reduced:
            grouped[row["source"]].append(row)
        combined, _, _ = _combined_source_partial(dict(grouped), feature)
        directions.append(_sign(combined))
    return sum(direction == observed_sign for direction in directions) / len(directions)


def _benjamini_hochberg(rows: list[dict[str, Any]]) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: item[1]["permutation_p_value"])
    running = 1.0
    for reversed_rank, (index, row) in enumerate(reversed(ordered), start=1):
        rank = len(rows) - reversed_rank + 1
        adjusted = min(1.0, row["permutation_p_value"] * len(rows) / rank)
        running = min(running, adjusted)
        rows[index]["bh_q_value"] = running


def _robust_scale(values: list[float], location: float) -> float:
    deviations = [abs(value - location) for value in values]
    mad_scale = 1.4826 * statistics.median(deviations)
    if mad_scale > 0:
        return mad_scale
    mean_absolute_scale = 1.2533 * statistics.fmean(deviations)
    if mean_absolute_scale > 0:
        return mean_absolute_scale
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _huber_weights(
    values: list[float], *, tuning_constant: float
) -> tuple[float, float, list[float]]:
    location = statistics.median(values)
    scale = _robust_scale(values, location)
    if scale == 0:
        return location, scale, [1.0] * len(values)
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
    cutoff = tuning_constant * scale
    weights = [
        min(1.0, cutoff / abs(value - location)) if value != location else 1.0
        for value in values
    ]
    return location, scale, weights


def _eligible_feature(name: str) -> bool:
    if name in {
        "surface_char_count",
        "surface_cjk_char_count",
        "surface_non_whitespace_char_count",
        "surface_paragraph_count",
        "surface_sentence_count",
        "title_cjk_char_count",
    }:
        return False
    if name.endswith(("_entropy_bits", "_mattr", "_type_token_ratio")):
        return False
    return not name.endswith("_count")


def _validate_handoff(
    manifest_path: Path,
    pool_path: Path,
    observations_path: Path,
    pilot_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pool = _load_jsonl(pool_path)
    observations = _load_jsonl(observations_path)
    if manifest.get("protocol_version") != "analysis-corpus-handoff-1.0":
        raise ValueError("Unsupported handoff protocol")
    if manifest.get("status") != "exploratory_pool_not_final_corpus":
        raise ValueError("Handoff is not marked as an exploratory pool")
    if _sha256(pool_path) != manifest.get("analysis_pool_sha256"):
        raise ValueError("Analysis-pool fingerprint mismatch")
    if len(pool) != manifest.get("documents") or len(pool) != 119:
        raise ValueError("Unexpected analysis-pool size")
    if len({item["doc_id"] for item in pool}) != len(pool):
        raise ValueError("Duplicate handoff document IDs")

    pilot_ids = {path.stem for path in pilot_root.rglob("*.txt")}
    pool_ids = {item["doc_id"] for item in pool}
    overlap = sorted(pilot_ids & pool_ids)
    if overlap:
        raise ValueError(f"Handoff overlaps pilot IDs: {overlap[:3]}")

    body_hash_matches = 0
    cjk_metadata_matches = 0
    line_count_matches = 0
    text_char_matches = 0
    for item in pool:
        body_path = Path(item["body_path"])
        raw = body_path.read_bytes()
        text = raw.decode("utf-8", errors="strict")
        if hashlib.sha256(raw).hexdigest() != item["content_hash"]:
            raise ValueError(f"Body hash mismatch: {item['doc_id']}")
        body_hash_matches += 1
        if len(CJK_RE.findall(text)) != item["cjk_chars"]:
            raise ValueError(f"CJK metadata mismatch: {item['doc_id']}")
        cjk_metadata_matches += 1
        if len(text.splitlines()) != item["line_count"]:
            raise ValueError(f"Line-count metadata mismatch: {item['doc_id']}")
        line_count_matches += 1
        if len(text) != item["text_chars"]:
            raise ValueError(f"Text-length metadata mismatch: {item['doc_id']}")
        text_char_matches += 1
        published = dt.date.fromisoformat(item["published_at"])
        if item["period"] == "pre":
            if published >= PRE_END:
                raise ValueError(f"Invalid pre date: {item['doc_id']}")
        elif item["period"] == "transition":
            if not TRANSITION_START <= published < POST_START:
                raise ValueError(f"Invalid transition date: {item['doc_id']}")
        else:
            raise ValueError(f"Unexpected period: {item['period']}")
    if any(item["period"] == "post" for item in pool):
        raise ValueError("This exploratory handoff must not contain post documents")
    if any(item["doc_id"] not in pool_ids for item in observations):
        raise ValueError("Reader observation is not in the handoff pool")
    if any(item.get("authorship_claim") for item in observations):
        raise ValueError("Reader observation must not be an authorship claim")

    audit = {
        "body_hash_matches": body_hash_matches,
        "cjk_metadata_matches": cjk_metadata_matches,
        "document_count": len(pool),
        "line_count_matches": line_count_matches,
        "period_counts": dict(sorted(Counter(item["period"] for item in pool).items())),
        "pilot_overlap_count": 0,
        "post_document_count": 0,
        "provenance_counts": dict(
            sorted(Counter(item["provenance_status"] for item in pool).items())
        ),
        "reader_observation_count": len(observations),
        "source_period_counts": dict(
            sorted(
                Counter(f"{item['source']},{item['period']}" for item in pool).items()
            )
        ),
        "strict_utf8_count": len(pool),
        "text_char_matches": text_char_matches,
        "value_counts": dict(
            sorted(Counter(item["value_status"] for item in pool).items())
        ),
    }
    return manifest, pool, observations, audit


def _extract_rows(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in sorted(
        pool,
        key=lambda value: (value["period"], value["published_at"], value["doc_id"]),
    ):
        body = Path(item["body_path"]).read_text(encoding="utf-8")
        published = dt.date.fromisoformat(item["published_at"])
        features: dict[str, float | int] = {}
        features.update(
            surface_features(body, char_ngram_size=4, char_mattr_window=500)
        )
        features.update(discourse_features(body))
        features.update(rhetorical_hypothesis_features(body))
        features.update(title_features(item["title"], body))
        rows.append(
            {
                "doc_id": item["doc_id"],
                "source": item["source"],
                "period": item["period"],
                "published_at": item["published_at"],
                "published_month": item["published_at"][:7],
                "days_into_transition": (
                    (published - TRANSITION_START).days
                    if item["period"] == "transition"
                    else ""
                ),
                "indexed_cjk_chars": item["cjk_chars"],
                "visibility_evidence": item["visibility_evidence"],
                "provenance_status": item["provenance_status"],
                "value_status": item["value_status"],
                "recommended_role": item["recommended_role"],
                **features,
            }
        )
    return rows


def _transition_trends(
    rows: list[dict[str, Any]],
    feature_names: list[str],
    *,
    permutation_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["source"]].append(row)
    grouped = dict(grouped)
    permutations = _transition_permutations(grouped, count=permutation_count, seed=seed)
    output: list[dict[str, Any]] = []
    for feature in feature_names:
        values = [float(row[feature]) for row in rows]
        if len(set(values)) < 2:
            continue
        combined, source_partials, length_rho = _combined_source_partial(
            grouped, feature
        )
        source_consistent = all(
            _sign(value) == _sign(combined) and _sign(value) != 0
            for value in source_partials.values()
        )
        output.append(
            {
                "feature": feature,
                "combined_partial_spearman": combined,
                "infoq_partial_spearman": source_partials.get("infoq", 0.0),
                "jiqizhixin_partial_spearman": source_partials.get("jiqizhixin", 0.0),
                "source_direction_consistent": source_consistent,
                "combined_feature_length_spearman": length_rho,
                "loo_direction_stability": _loo_stability(rows, feature, combined),
                "permutation_p_value": _permutation_p_value(
                    grouped,
                    feature,
                    combined,
                    permutations,
                ),
            }
        )
    _benjamini_hochberg(output)
    for row in output:
        row["ranking_score"] = (
            abs(row["combined_partial_spearman"]) * row["loo_direction_stability"]
            if row["source_direction_consistent"]
            else 0.0
        )
    output.sort(
        key=lambda row: (
            -row["ranking_score"],
            row["permutation_p_value"],
            row["feature"],
        )
    )
    return output


def _pre_typicality(
    rows: list[dict[str, Any]],
    feature_names: list[str],
    *,
    tuning_constant: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    weights_by_doc: dict[str, list[float]] = defaultdict(list)
    z_by_doc: dict[str, list[float]] = defaultdict(list)
    feature_rows: list[dict[str, Any]] = []
    distribution_rows: list[dict[str, Any]] = []
    for feature in feature_names:
        values = [float(row[feature]) for row in rows]
        location, scale, weights = _huber_weights(
            values, tuning_constant=tuning_constant
        )
        distribution_rows.append(
            {
                "feature": feature,
                "minimum": min(values),
                "q1": statistics.quantiles(values, n=4)[0],
                "median": statistics.median(values),
                "q3": statistics.quantiles(values, n=4)[2],
                "maximum": max(values),
                "huber_location": location,
                "robust_scale": scale,
            }
        )
        for row, value, weight in zip(rows, values, weights, strict=True):
            robust_z = (value - location) / scale if scale else 0.0
            weights_by_doc[row["doc_id"]].append(weight)
            z_by_doc[row["doc_id"]].append(robust_z)
            feature_rows.append(
                {
                    "doc_id": row["doc_id"],
                    "feature": feature,
                    "value": value,
                    "huber_location": location,
                    "robust_scale": scale,
                    "robust_z": robust_z,
                    "huber_weight": weight,
                }
            )
    summaries: list[dict[str, Any]] = []
    for row in rows:
        weights = weights_by_doc[row["doc_id"]]
        robust_z = z_by_doc[row["doc_id"]]
        summaries.append(
            {
                "doc_id": row["doc_id"],
                "published_at": row["published_at"],
                "indexed_cjk_chars": row["indexed_cjk_chars"],
                "visibility_evidence": row["visibility_evidence"],
                "overall_typicality_weight": statistics.fmean(weights),
                "median_feature_weight": statistics.median(weights),
                "minimum_feature_weight": min(weights),
                "downweighted_feature_count": sum(weight < 1.0 for weight in weights),
                "strongly_downweighted_feature_count": sum(
                    weight < 0.5 for weight in weights
                ),
                "maximum_absolute_robust_z": max(abs(value) for value in robust_z),
            }
        )
    summaries.sort(
        key=lambda row: (
            row["overall_typicality_weight"],
            row["doc_id"],
        )
    )
    feature_rows.sort(key=lambda row: (row["doc_id"], row["feature"]))
    distribution_rows.sort(key=lambda row: row["feature"])
    return summaries, feature_rows, distribution_rows


def _reader_case_profile(
    observations: list[dict[str, Any]],
    transition_rows: list[dict[str, Any]],
    feature_names: list[str],
) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    rows_by_id = {row["doc_id"]: row for row in transition_rows}
    for observation in observations:
        target = rows_by_id[observation["doc_id"]]
        peers = [row for row in transition_rows if row["source"] == target["source"]]
        feature_profiles: list[dict[str, Any]] = []
        for feature in feature_names:
            peer_values = [float(row[feature]) for row in peers]
            target_value = float(target[feature])
            location = statistics.median(peer_values)
            scale = _robust_scale(peer_values, location)
            robust_z = (target_value - location) / scale if scale else 0.0
            percentile = sum(value <= target_value for value in peer_values) / len(
                peer_values
            )
            feature_profiles.append(
                {
                    "feature": feature,
                    "value": target_value,
                    "same_source_percentile": percentile,
                    "same_source_robust_z": robust_z,
                }
            )
        feature_profiles.sort(
            key=lambda row: (-abs(row["same_source_robust_z"]), row["feature"])
        )
        profiles.append(
            {
                "doc_id": observation["doc_id"],
                "observation_status": observation["status"],
                "authorship_claim": observation["authorship_claim"],
                "role": "development_case_profile_only",
                "top_feature_deviations": feature_profiles[:15],
            }
        )
    return profiles


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--reader-observations", type=Path, required=True)
    parser.add_argument("--pilot-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260822)
    parser.add_argument("--tuning-constant", type=float, default=1.5)
    args = parser.parse_args()
    if args.permutations < 1:
        raise ValueError("permutations must be positive")
    if args.tuning_constant <= 0:
        raise ValueError("tuning-constant must be positive")

    output_dir = _prepare_output_directory(args.output_dir)
    manifest, pool, observations, audit = _validate_handoff(
        args.manifest,
        args.pool,
        args.reader_observations,
        args.pilot_root,
    )
    rows = _extract_rows(pool)
    identity_columns = {
        "days_into_transition",
        "doc_id",
        "indexed_cjk_chars",
        "period",
        "provenance_status",
        "published_at",
        "published_month",
        "recommended_role",
        "source",
        "value_status",
        "visibility_evidence",
    }
    all_feature_names = sorted(set(rows[0]) - identity_columns)
    feature_names = [name for name in all_feature_names if _eligible_feature(name)]
    transition_rows = [row for row in rows if row["period"] == "transition"]
    pre_rows = [row for row in rows if row["period"] == "pre"]
    trends = _transition_trends(
        transition_rows,
        feature_names,
        permutation_count=args.permutations,
        seed=args.seed,
    )
    pre_summary, pre_weights, pre_distributions = _pre_typicality(
        pre_rows,
        feature_names,
        tuning_constant=args.tuning_constant,
    )
    reader_profiles = _reader_case_profile(
        observations,
        transition_rows,
        feature_names,
    )

    row_columns = sorted(identity_columns) + all_feature_names
    _write_csv(output_dir / "document_features.csv", rows, row_columns)
    _write_csv(
        output_dir / "transition_trends.csv",
        trends,
        [
            "feature",
            "combined_partial_spearman",
            "infoq_partial_spearman",
            "jiqizhixin_partial_spearman",
            "source_direction_consistent",
            "combined_feature_length_spearman",
            "loo_direction_stability",
            "permutation_p_value",
            "bh_q_value",
            "ranking_score",
        ],
    )
    _write_csv(
        output_dir / "pre_document_typicality.csv",
        pre_summary,
        [
            "doc_id",
            "published_at",
            "indexed_cjk_chars",
            "visibility_evidence",
            "overall_typicality_weight",
            "median_feature_weight",
            "minimum_feature_weight",
            "downweighted_feature_count",
            "strongly_downweighted_feature_count",
            "maximum_absolute_robust_z",
        ],
    )
    _write_csv(
        output_dir / "pre_feature_weights.csv",
        pre_weights,
        [
            "doc_id",
            "feature",
            "value",
            "huber_location",
            "robust_scale",
            "robust_z",
            "huber_weight",
        ],
    )
    _write_csv(
        output_dir / "pre_feature_distributions.csv",
        pre_distributions,
        [
            "feature",
            "minimum",
            "q1",
            "median",
            "q3",
            "maximum",
            "huber_location",
            "robust_scale",
        ],
    )
    _write_json(output_dir / "reader_case_profiles.json", reader_profiles)

    result = {
        "artifact_type": "handoff-transition-feature-exploration",
        "audit": audit,
        "caveats": [
            "The handoff contains no post-period documents and cannot estimate the primary pre/post effect.",
            "Transition trends are exploratory discovery signals, not cohort effects.",
            "The pre-period documents are unmatched Machine Heart candidates with unverified visibility.",
            "Model-assisted provenance and value labels are measurements, not human gold.",
            "The single reader observation is a development case profile, not an authorship or validation label.",
            "No document is manually deleted; pre-period outlier summaries are descriptive robust weights.",
        ],
        "eligible_feature_count": len(feature_names),
        "excluded_length_sensitive_feature_count": len(all_feature_names)
        - len(feature_names),
        "handoff_generated_at": manifest["generated_at"],
        "handoff_protocol_version": manifest["protocol_version"],
        "input_fingerprints": {
            "manifest": _sha256(args.manifest),
            "pool": _sha256(args.pool),
            "reader_observations": _sha256(args.reader_observations),
        },
        "permutations": args.permutations,
        "pre": {
            "document_count": len(pre_rows),
            "lowest_typicality_candidates": pre_summary[:10],
        },
        "protocol_version": PROTOCOL_VERSION,
        "reader_case_profiles": reader_profiles,
        "seed": args.seed,
        "transition": {
            "document_count": len(transition_rows),
            "source_counts": dict(
                sorted(Counter(row["source"] for row in transition_rows).items())
            ),
            "top_trends": trends[:20],
        },
        "tuning_constant": args.tuning_constant,
    }
    _write_json(output_dir / "results.json", result)

    artifact_paths = sorted(
        path for path in output_dir.iterdir() if path.name != "run_manifest.json"
    )
    run_manifest = {
        "artifacts": {path.name: _sha256(path) for path in artifact_paths},
        "input_fingerprints": result["input_fingerprints"],
        "protocol_version": PROTOCOL_VERSION,
        "seed": args.seed,
    }
    _write_json(output_dir / "run_manifest.json", run_manifest)
    print(
        json.dumps(
            {
                "eligible_feature_count": len(feature_names),
                "output_dir": str(output_dir),
                "pre_count": len(pre_rows),
                "transition_count": len(transition_rows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
