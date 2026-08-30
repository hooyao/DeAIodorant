"""Generate the frozen allocation and power sensitivity for the boundary experiment."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = "deaiodorant-boundary-competition-design-1.0"
PROTOCOL_VERSION = "boundary-competition-development-1.0"
SEED = 2026083101
STRATA = ("high_competition", "low_competition")
ITEMS_PER_STRATUM = 8
SESSION_COUNT = 2
MIN_MIRROR_SEPARATION = 8
ALTERNATIVE_PROBABILITIES = (0.65, 0.70, 0.75, 0.80)
ALPHA = 0.05
TARGET_POWER = 0.80


@dataclass(frozen=True)
class AllocationRow:
    task_number: int
    session_block: int
    slot_id: str
    stratum: str
    control_role: str
    original_side: str
    mirror_of_slot: str


def _null_probability(n: int, successes: int) -> float:
    return math.comb(n, successes) / (2**n)


def exact_two_sided_rejection_set(n: int, alpha: float) -> set[int]:
    """Return exact-binomial rejection counts for a 0.5 null probability."""

    null_probabilities = [_null_probability(n, count) for count in range(n + 1)]
    rejected: set[int] = set()
    for observed, observed_probability in enumerate(null_probabilities):
        p_value = sum(
            probability
            for probability in null_probabilities
            if probability <= observed_probability + 1e-15
        )
        if p_value <= alpha:
            rejected.add(observed)
    return rejected


def exact_binomial_power(n: int, alternative_probability: float, alpha: float) -> float:
    """Compute power for the exact two-sided binomial test against p=0.5."""

    rejected = exact_two_sided_rejection_set(n, alpha)
    return sum(
        math.comb(n, successes)
        * alternative_probability**successes
        * (1.0 - alternative_probability) ** (n - successes)
        for successes in rejected
    )


def minimum_decisive_count(
    alternative_probability: float,
    alpha: float = ALPHA,
    target_power: float = TARGET_POWER,
) -> int:
    """Find the first decisive-pair count reaching the requested exact power."""

    for n in range(2, 501):
        if exact_binomial_power(n, alternative_probability, alpha) >= target_power:
            return n
    raise RuntimeError("Required decisive count exceeds the search limit")


def power_rows() -> list[dict[str, float | int]]:
    """Return the preregistered sensitivity table."""

    output: list[dict[str, float | int]] = []
    for probability in ALTERNATIVE_PROBABILITIES:
        decisive_count = minimum_decisive_count(probability)
        output.append(
            {
                "true_revised_preference_probability": probability,
                "minimum_decisive_pairs": decisive_count,
                "exact_power": round(
                    exact_binomial_power(decisive_count, probability, ALPHA), 6
                ),
                "tasks_if_tie_rate_0_20": math.ceil(decisive_count / 0.80),
            }
        )
    return output


def _intervention_slots(rng: random.Random) -> list[dict[str, str | int]]:
    slots: list[dict[str, str | int]] = []
    for stratum in STRATA:
        prefix = "high" if stratum == "high_competition" else "low"
        for session in range(1, SESSION_COUNT + 1):
            sides = ["A", "A", "B", "B"]
            rng.shuffle(sides)
            start = (session - 1) * 4 + 1
            for offset, side in enumerate(sides):
                index = start + offset
                slots.append(
                    {
                        "session_block": session,
                        "slot_id": f"{prefix}_{index:02d}",
                        "stratum": stratum,
                        "control_role": "intervention",
                        "original_side": side,
                        "mirror_of_slot": "",
                    }
                )
    return slots


def _valid_order(rows: list[dict[str, str | int]], mirror_base: str) -> bool:
    positions = {str(row["slot_id"]): index + 1 for index, row in enumerate(rows)}
    if rows[0]["control_role"] != "intervention":
        return False
    if (
        positions["mirror_control"] - positions[mirror_base]
        < MIN_MIRROR_SEPARATION
    ):
        return False
    return True


def allocation_rows(seed: int = SEED) -> list[AllocationRow]:
    """Generate the constrained, balanced placeholder allocation."""

    rng = random.Random(seed)
    base_slots = _intervention_slots(rng)
    first_session_high = [
        row
        for row in base_slots
        if row["session_block"] == 1 and row["stratum"] == "high_competition"
    ]
    mirror_base = str(rng.choice(first_session_high)["slot_id"])
    mirror_base_side = next(
        str(row["original_side"])
        for row in base_slots
        if row["slot_id"] == mirror_base
    )
    mirror_side = "B" if mirror_base_side == "A" else "A"

    by_session: dict[int, list[dict[str, str | int]]] = {
        1: [row for row in base_slots if row["session_block"] == 1],
        2: [row for row in base_slots if row["session_block"] == 2],
    }
    by_session[1].append(
        {
            "session_block": 1,
            "slot_id": "identical_control",
            "stratum": "diagnostic",
            "control_role": "identical",
            "original_side": "identical",
            "mirror_of_slot": "",
        }
    )
    by_session[2].append(
        {
            "session_block": 2,
            "slot_id": "mirror_control",
            "stratum": "diagnostic",
            "control_role": "mirrored",
            "original_side": mirror_side,
            "mirror_of_slot": mirror_base,
        }
    )

    for _ in range(100_000):
        session_one = list(by_session[1])
        session_two = list(by_session[2])
        rng.shuffle(session_one)
        rng.shuffle(session_two)
        candidate = session_one + session_two
        if _valid_order(candidate, mirror_base):
            return [
                AllocationRow(task_number=index, **row)
                for index, row in enumerate(candidate, start=1)
            ]
    raise RuntimeError("Unable to satisfy the frozen allocation constraints")


def _write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    materialized = list(rows)
    if not materialized:
        raise ValueError(f"No rows available for {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)


def validate_allocation(rows: list[AllocationRow]) -> None:
    """Fail if the placeholder layout violates a frozen design invariant."""

    interventions = [row for row in rows if row.control_role == "intervention"]
    if len(rows) != 18 or len(interventions) != 16:
        raise ValueError("The design must contain 16 interventions and two controls")
    for stratum in STRATA:
        stratum_rows = [row for row in interventions if row.stratum == stratum]
        if len(stratum_rows) != ITEMS_PER_STRATUM:
            raise ValueError(f"Unbalanced stratum: {stratum}")
        side_counts = {
            side: sum(row.original_side == side for row in stratum_rows)
            for side in ("A", "B")
        }
        if side_counts != {"A": 4, "B": 4}:
            raise ValueError(f"Unbalanced original placement: {stratum}")
        for session in range(1, SESSION_COUNT + 1):
            if sum(row.session_block == session for row in stratum_rows) != 4:
                raise ValueError(f"Unbalanced session assignment: {stratum}")
    controls = {row.control_role: row for row in rows if row.control_role != "intervention"}
    if set(controls) != {"identical", "mirrored"}:
        raise ValueError("Missing identical or mirrored diagnostic")
    mirror_base = controls["mirrored"].mirror_of_slot
    base = next(row for row in interventions if row.slot_id == mirror_base)
    if controls["mirrored"].original_side == base.original_side:
        raise ValueError("The mirrored diagnostic did not reverse display side")
    if controls["mirrored"].task_number - base.task_number < MIN_MIRROR_SEPARATION:
        raise ValueError("The mirrored diagnostic is too close to its first presentation")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the frozen boundary-competition development design."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    rows = allocation_rows(args.seed)
    validate_allocation(rows)
    power = power_rows()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "allocation.csv", [asdict(row) for row in rows])
    _write_csv(args.output_dir / "power_sensitivity.csv", power)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "seed": args.seed,
        "role": "single_reader_development_not_validation",
        "intervention_units": 16,
        "high_competition_units": ITEMS_PER_STRATUM,
        "low_competition_units": ITEMS_PER_STRATUM,
        "diagnostic_tasks": 2,
        "session_blocks": SESSION_COUNT,
        "minimum_mirror_separation": MIN_MIRROR_SEPARATION,
        "power_sensitivity": {
            "test": "exact_two_sided_binomial_against_0.5",
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "ties_excluded_from_decisive_count": True,
            "rows": power,
            "warning": (
                "These calculations are an optimistic independent-comparison floor. "
                "They do not turn repeated responses from one reader into "
                "reader-level replication."
            ),
        },
    }
    (args.output_dir / "design.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
