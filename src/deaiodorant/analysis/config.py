"""Versioned configuration for reproducible document-feature extraction."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FeatureConfigError(ValueError):
    """Raised when a feature configuration is incomplete or inconsistent."""


@dataclass(frozen=True)
class FeatureConfig:
    """Validated settings that can change extracted feature values."""

    schema_version: str
    pre_end_exclusive: dt.date
    post_start_inclusive: dt.date
    char_ngram_size: int
    char_mattr_window: int
    token_mattr_window: int
    require_syntax: bool
    annotation_seed: int
    sparse_enabled: bool
    sparse_char_ngram_sizes: tuple[int, ...]
    sparse_pos_ngram_sizes: tuple[int, ...]
    sparse_opening_cjk_chars: int
    sparse_minimum_document_frequency: int
    sparse_maximum_features_per_family: int
    raw: dict[str, Any]
    fingerprint: str


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FeatureConfigError(f"{name} must be a JSON object")
    return value


def _require_int(value: Any, name: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise FeatureConfigError(
            f"{name} must be an integer greater than or equal to {minimum}"
        )
    return value


def _require_sizes(value: Any, name: str) -> tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise FeatureConfigError(f"{name} must be a non-empty list")
    sizes = tuple(_require_int(item, name, minimum=1) for item in value)
    if len(set(sizes)) != len(sizes):
        raise FeatureConfigError(f"{name} contains duplicate values")
    return sizes


def _parse_date(value: Any, name: str) -> dt.date:
    if not isinstance(value, str):
        raise FeatureConfigError(f"{name} must be an ISO date string")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise FeatureConfigError(f"{name} is not a valid ISO date") from exc


def load_feature_config(path: Path) -> FeatureConfig:
    """Load and strictly validate a versioned JSON feature configuration."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FeatureConfigError(f"Invalid JSON configuration: {path}") from exc
    raw = _require_mapping(raw, "configuration")
    expected_top_level = {
        "annotation",
        "cohorts",
        "features",
        "schema_version",
        "sparse_features",
    }
    if set(raw) != expected_top_level:
        raise FeatureConfigError("Configuration has missing or unknown top-level keys")
    if raw["schema_version"] != "deaiodorant-features-1.0":
        raise FeatureConfigError(
            f"Unsupported schema_version: {raw['schema_version']!r}"
        )

    cohorts = _require_mapping(raw["cohorts"], "cohorts")
    features = _require_mapping(raw["features"], "features")
    annotation = _require_mapping(raw["annotation"], "annotation")
    sparse = _require_mapping(raw["sparse_features"], "sparse_features")
    if set(cohorts) != {"post_start_inclusive", "pre_end_exclusive"}:
        raise FeatureConfigError("cohorts has missing or unknown keys")
    expected_features = {
        "char_mattr_window",
        "char_ngram_size",
        "require_syntax",
        "token_mattr_window",
    }
    if set(features) != expected_features:
        raise FeatureConfigError("features has missing or unknown keys")
    if set(annotation) != {"seed"}:
        raise FeatureConfigError("annotation has missing or unknown keys")
    expected_sparse = {
        "char_ngram_sizes",
        "enabled",
        "maximum_features_per_family",
        "minimum_document_frequency",
        "opening_cjk_chars",
        "pos_ngram_sizes",
    }
    if set(sparse) != expected_sparse:
        raise FeatureConfigError("sparse_features has missing or unknown keys")

    pre_end = _parse_date(cohorts["pre_end_exclusive"], "pre_end_exclusive")
    post_start = _parse_date(
        cohorts["post_start_inclusive"],
        "post_start_inclusive",
    )
    if pre_end > post_start:
        raise FeatureConfigError(
            "pre_end_exclusive must not follow post_start_inclusive"
        )
    require_syntax = features["require_syntax"]
    if not isinstance(require_syntax, bool):
        raise FeatureConfigError("require_syntax must be a boolean")
    sparse_enabled = sparse["enabled"]
    if not isinstance(sparse_enabled, bool):
        raise FeatureConfigError("sparse_features.enabled must be a boolean")

    canonical = json.dumps(
        raw,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return FeatureConfig(
        schema_version=raw["schema_version"],
        pre_end_exclusive=pre_end,
        post_start_inclusive=post_start,
        char_ngram_size=_require_int(
            features["char_ngram_size"],
            "char_ngram_size",
            minimum=1,
        ),
        char_mattr_window=_require_int(
            features["char_mattr_window"],
            "char_mattr_window",
            minimum=2,
        ),
        token_mattr_window=_require_int(
            features["token_mattr_window"],
            "token_mattr_window",
            minimum=2,
        ),
        require_syntax=require_syntax,
        annotation_seed=_require_int(annotation["seed"], "seed", minimum=0),
        sparse_enabled=sparse_enabled,
        sparse_char_ngram_sizes=_require_sizes(
            sparse["char_ngram_sizes"],
            "char_ngram_sizes",
        ),
        sparse_pos_ngram_sizes=_require_sizes(
            sparse["pos_ngram_sizes"],
            "pos_ngram_sizes",
        ),
        sparse_opening_cjk_chars=_require_int(
            sparse["opening_cjk_chars"],
            "opening_cjk_chars",
            minimum=1,
        ),
        sparse_minimum_document_frequency=_require_int(
            sparse["minimum_document_frequency"],
            "minimum_document_frequency",
            minimum=1,
        ),
        sparse_maximum_features_per_family=_require_int(
            sparse["maximum_features_per_family"],
            "maximum_features_per_family",
            minimum=1,
        ),
        raw=raw,
        fingerprint=hashlib.sha256(canonical).hexdigest(),
    )
