"""Prepare a small blinded Label Studio calibration set from pilot articles."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Selection:
    doc_id: str
    month: str
    target_start: int
    target_end: int
    context_before_start: int
    context_before_end: int
    context_after_start: int
    context_after_end: int


SELECTIONS = (
    Selection("3c60dc0a981b686870095450", "2026-06", 36, 42, 34, 35, 43, 44),
    Selection("3c60dc0a981b686870095450", "2026-06", 79, 81, 77, 78, 82, 83),
    Selection("44aa81958a6c585ee8c06847", "2026-01", 15, 22, 14, 14, 23, 24),
    Selection("0431c592d5de8246cebcb8e2", "2025-10", 7, 10, 6, 6, 11, 12),
    Selection("213dcab213f816c7c548fc09", "2026-04", 270, 275, 267, 269, 276, 277),
    Selection("b77b09a419c1631227112f0c", "2026-03", 19, 22, 17, 18, 23, 24),
    Selection("48a7a6192771112323fd6820", "2026-02", 119, 125, 116, 118, 126, 128),
    Selection("48bda219eb0776f623161899", "2026-01", 67, 71, 64, 66, 72, 72),
    Selection("bf1abf6ca461ec0bbac14bd7", "2022-01", 28, 32, 27, 27, 33, 34),
    Selection("9e271d7b118c949e83c9ff8d", "2022-06", 10, 12, 8, 9, 13, 14),
)


def select_lines(lines: list[str], start: int, end: int) -> str:
    """Return an inclusive one-based line range."""

    selected = lines[start - 1 : end]
    return "\n".join(line.strip() for line in selected if line.strip())


def build_tasks(corpus_root: Path) -> list[dict[str, object]]:
    """Build and deterministically shuffle blinded annotation tasks."""

    tasks: list[dict[str, object]] = []
    for selection in SELECTIONS:
        path = corpus_root / selection.month / f"{selection.doc_id}.txt"
        lines = path.read_text(encoding="utf-8").splitlines()
        tasks.append(
            {
                "data": {
                    "context_after": select_lines(
                        lines,
                        selection.context_after_start,
                        selection.context_after_end,
                    ),
                    "context_before": select_lines(
                        lines,
                        selection.context_before_start,
                        selection.context_before_end,
                    ),
                    "target": select_lines(
                        lines,
                        selection.target_start,
                        selection.target_end,
                    ),
                    "task_number": 0,
                },
                "meta": {
                    "doc_id": selection.doc_id,
                    "month": selection.month,
                    "target_lines": [
                        selection.target_start,
                        selection.target_end,
                    ],
                },
            }
        )
    random.Random(20260821).shuffle(tasks)
    for index, task in enumerate(tasks, start=1):
        task["data"]["task_number"] = index
    return tasks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=Path("data/pilot/monthly"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tasks = build_tasks(args.corpus_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "task_count": len(tasks),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
