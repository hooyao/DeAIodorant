"""Shared utilities for translation-gate benchmark construction."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


BENCHMARK_PROTOCOL_VERSION = "translation-gate-2.0-development"
_CONTENT_CHAR_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fffA-Za-z0-9]")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a UTF-8 JSONL file."""
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Write records as deterministic UTF-8 JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized_content(text: str) -> str:
    return "".join(_CONTENT_CHAR_RE.findall(text)).lower()


def _shingles(normalized: str, width: int = 5) -> frozenset[str]:
    if len(normalized) <= width:
        return frozenset({normalized}) if normalized else frozenset()
    return frozenset(
        normalized[index : index + width]
        for index in range(len(normalized) - width + 1)
    )


def _simhash(shingles: frozenset[str]) -> int:
    if not shingles:
        return 0
    weights = [0] * 64
    for shingle in shingles:
        value = int.from_bytes(
            hashlib.blake2b(shingle.encode("utf-8"), digest_size=8).digest(), "big"
        )
        for bit in range(64):
            weights[bit] += 1 if value & (1 << bit) else -1
    result = 0
    for bit, weight in enumerate(weights):
        if weight >= 0:
            result |= 1 << bit
    return result


@dataclasses.dataclass(frozen=True)
class DuplicateEntry:
    doc_id: str
    canonical_url: str
    exact_hash: str
    normalized_text: str
    normalized_length: int
    simhash: int
    shingles: frozenset[str]


@dataclasses.dataclass(frozen=True)
class DuplicateMatch:
    reason: str
    existing_doc_id: str


class ExclusionIndex:
    """Reject exact and high-similarity documents across benchmark versions."""

    def __init__(self, near_duplicate_threshold: float = 0.9) -> None:
        self.near_duplicate_threshold = near_duplicate_threshold
        self._doc_ids: dict[str, DuplicateEntry] = {}
        self._urls: dict[str, DuplicateEntry] = {}
        self._hashes: dict[str, DuplicateEntry] = {}
        self._entries: list[DuplicateEntry] = []

    @staticmethod
    def entry(record: dict[str, Any]) -> DuplicateEntry:
        text = str(record.get("text") or "")
        normalized = normalized_content(text)
        shingles = _shingles(normalized)
        return DuplicateEntry(
            doc_id=str(record.get("doc_id") or ""),
            canonical_url=str(record.get("url") or record.get("canonical_url") or ""),
            exact_hash=content_hash(text),
            normalized_text=normalized,
            normalized_length=len(normalized),
            simhash=_simhash(shingles),
            shingles=shingles,
        )

    def add(self, record: dict[str, Any]) -> None:
        entry = self.entry(record)
        if entry.doc_id:
            self._doc_ids[entry.doc_id] = entry
        if entry.canonical_url:
            self._urls[entry.canonical_url] = entry
        if entry.exact_hash:
            self._hashes[entry.exact_hash] = entry
        self._entries.append(entry)

    def match(self, record: dict[str, Any]) -> DuplicateMatch | None:
        candidate = self.entry(record)
        if candidate.doc_id and candidate.doc_id in self._doc_ids:
            return DuplicateMatch("doc_id", self._doc_ids[candidate.doc_id].doc_id)
        if candidate.canonical_url and candidate.canonical_url in self._urls:
            return DuplicateMatch("canonical_url", self._urls[candidate.canonical_url].doc_id)
        if candidate.exact_hash in self._hashes:
            return DuplicateMatch("exact_content", self._hashes[candidate.exact_hash].doc_id)
        if not candidate.shingles:
            return None
        for existing in self._entries:
            longer = max(candidate.normalized_length, existing.normalized_length)
            shorter = min(candidate.normalized_length, existing.normalized_length)
            if not longer or shorter / longer < 0.8:
                continue
            if (
                candidate.normalized_text in existing.normalized_text
                or existing.normalized_text in candidate.normalized_text
            ):
                return DuplicateMatch("near_duplicate", existing.doc_id)
            if (candidate.simhash ^ existing.simhash).bit_count() > 8:
                continue
            union = len(candidate.shingles | existing.shingles)
            similarity = (
                len(candidate.shingles & existing.shingles) / union if union else 0.0
            )
            if similarity >= self.near_duplicate_threshold:
                return DuplicateMatch("near_duplicate", existing.doc_id)
        return None

    @classmethod
    def from_paths(cls, paths: Iterable[Path]) -> "ExclusionIndex":
        index = cls()
        for path in paths:
            for record in read_jsonl(path):
                index.add(record)
        return index


REVIEW_FIELDS = [
    "doc_id",
    "source",
    "published_at",
    "title",
    "url",
    "candidate_label",
    "label_evidence",
    "cjk_chars",
    "review_include",
    "review_gold_label",
    "reviewer",
    "reviewed_at",
    "review_notes",
]


def write_review_queue(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["label_evidence"] = json.dumps(
                record.get("label_evidence") or [], ensure_ascii=False
            )
            row.update(
                {
                    "review_include": "",
                    "review_gold_label": "",
                    "reviewer": "",
                    "reviewed_at": "",
                    "review_notes": "",
                }
            )
            writer.writerow(row)


def read_review_decisions(path: Path) -> dict[str, dict[str, str]]:
    decisions: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            include = row.get("review_include", "").strip().lower()
            if include not in {"yes", "no"}:
                continue
            doc_id = row.get("doc_id", "").strip()
            if not doc_id:
                continue
            decisions[doc_id] = row
    return decisions


def stable_order(records: Iterable[dict[str, Any]], seed: str) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda record: hashlib.sha256(
            f"{seed}\0{record['doc_id']}".encode("utf-8")
        ).digest(),
    )


def balanced_take(
    records: list[dict[str, Any]], count: int, *, seed: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Take records round-robin by source after stable per-source ordering."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in stable_order(records, seed):
        grouped[str(record["source"])].append(record)
    sources = sorted(grouped)
    selected: list[dict[str, Any]] = []
    while len(selected) < count:
        progressed = False
        for source in sources:
            if grouped[source] and len(selected) < count:
                selected.append(grouped[source].pop(0))
                progressed = True
        if not progressed:
            raise RuntimeError(f"Only {len(selected)} records available; need {count}")
    selected_ids = {record["doc_id"] for record in selected}
    remaining = [record for record in records if record["doc_id"] not in selected_ids]
    return selected, remaining


def assert_disjoint(splits: dict[str, list[dict[str, Any]]]) -> None:
    names = sorted(splits)
    for index, left_name in enumerate(names):
        left = splits[left_name]
        left_ids = {record["doc_id"] for record in left}
        left_urls = {record["url"] for record in left}
        left_hashes = {content_hash(record["text"]) for record in left}
        for right_name in names[index + 1 :]:
            right = splits[right_name]
            if left_ids.intersection(record["doc_id"] for record in right):
                raise RuntimeError(f"doc_id overlap: {left_name}/{right_name}")
            if left_urls.intersection(record["url"] for record in right):
                raise RuntimeError(f"URL overlap: {left_name}/{right_name}")
            if left_hashes.intersection(content_hash(record["text"]) for record in right):
                raise RuntimeError(f"content overlap: {left_name}/{right_name}")
