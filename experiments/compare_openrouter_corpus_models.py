"""Compare current OpenRouter models on a fixed corpus-admission panel."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from deaiodorant.corpus.review_triage import (
    ReviewTriageClassifier,
    TRIAGE_PROMPT_VERSIONS,
)
from deaiodorant.corpus.value_triage import (
    ResearchValueClassifier,
    VALUE_PROMPT_VERSIONS,
)


SCHEMA_VERSION = "deaiodorant-openrouter-corpus-model-comparison-0.1"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", model).strip("_")


def safe_classify(
    classifier: ReviewTriageClassifier | ResearchValueClassifier,
    record: dict[str, Any],
) -> dict[str, Any]:
    try:
        result = classifier.classify(record)
    except Exception as exc:  # Fail closed while preserving the remaining panel.
        return {
            "status": "request_error",
            "error_type": type(exc).__name__,
        }
    return {"status": "ok", **result}


def run_many(
    classifier: ReviewTriageClassifier | ResearchValueClassifier,
    records: list[dict[str, Any]],
    concurrency: int,
) -> list[dict[str, Any]]:
    function: Callable[[dict[str, Any]], dict[str, Any]] = lambda record: safe_classify(
        classifier, record
    )
    if concurrency <= 1:
        return [function(record) for record in records]
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        return list(executor.map(function, records))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--model-spec",
        action="append",
        nargs=3,
        metavar=("MODEL", "REASONING_MODE", "MAX_TOKENS"),
        required=True,
    )
    parser.add_argument("--endpoint", default="https://openrouter.ai/api/v1")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=240.0)
    args = parser.parse_args()

    records = [
        json.loads(line)
        for line in args.panel.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len({record["doc_id"] for record in records}) != len(records):
        raise ValueError("The comparison panel contains duplicate document IDs")
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    model_configs: list[dict[str, Any]] = []
    for raw_model, reasoning_mode, raw_max_tokens in args.model_spec:
        max_tokens = int(raw_max_tokens)
        model_configs.append(
            {
                "model": raw_model,
                "reasoning_mode": reasoning_mode,
                "max_tokens": max_tokens,
            }
        )
        model_dir = output_dir / safe_name(raw_model)
        provenance = ReviewTriageClassifier(
            raw_model,
            model_dir / "provenance_cache.jsonl",
            endpoint=args.endpoint,
            timeout=args.timeout,
            profile="safeguard",
            backend="openai",
            reasoning_mode=reasoning_mode,
            max_tokens=max_tokens,
        )
        value = ResearchValueClassifier(
            raw_model,
            model_dir / "value_cache.jsonl",
            endpoint=args.endpoint,
            timeout=args.timeout,
            profile="primary",
            backend="openai",
            reasoning_mode=reasoning_mode,
            max_tokens=max_tokens,
        )
        provenance_results = run_many(provenance, records, args.concurrency)
        value_results = run_many(value, records, args.concurrency)
        for record, provenance_result, value_result in zip(
            records,
            provenance_results,
            value_results,
            strict=True,
        ):
            rows.append(
                {
                    "doc_id": record["doc_id"],
                    "source": record.get("source"),
                    "content_hash": hashlib.sha256(
                        str(record["text"]).encode("utf-8")
                    ).hexdigest(),
                    "model": raw_model,
                    "reasoning_mode": reasoning_mode,
                    "max_tokens": max_tokens,
                    "provenance": provenance_result,
                    "value": value_result,
                }
            )

    results_path = output_dir / "results.jsonl"
    results_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )
    model_summary: list[dict[str, Any]] = []
    for config in model_configs:
        model_rows = [row for row in rows if row["model"] == config["model"]]
        model_summary.append(
            {
                **config,
                "documents": len(model_rows),
                "provenance_status_counts": dict(
                    sorted(Counter(row["provenance"]["status"] for row in model_rows).items())
                ),
                "provenance_label_counts": dict(
                    sorted(
                        Counter(
                            row["provenance"].get("label", "request_error")
                            for row in model_rows
                        ).items()
                    )
                ),
                "value_status_counts": dict(
                    sorted(Counter(row["value"]["status"] for row in model_rows).items())
                ),
                "value_label_counts": dict(
                    sorted(
                        Counter(
                            row["value"].get("label", "request_error")
                            for row in model_rows
                        ).items()
                    )
                ),
            }
        )

    summary = {
        "artifact_type": "current-openrouter-corpus-model-interface-comparison",
        "schema_version": SCHEMA_VERSION,
        "panel": str(args.panel.resolve()),
        "panel_sha256": file_sha256(args.panel),
        "documents": len(records),
        "endpoint": args.endpoint,
        "concurrency": args.concurrency,
        "prompt_versions": {
            "provenance": TRIAGE_PROMPT_VERSIONS["safeguard"],
            "value": VALUE_PROMPT_VERSIONS["primary"],
        },
        "models": model_summary,
        "results": str(results_path),
        "results_sha256": file_sha256(results_path),
        "interpretation": (
            "The panel tests interface reliability and cross-model measurement "
            "agreement. It contains no human gold and cannot rank model accuracy."
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
