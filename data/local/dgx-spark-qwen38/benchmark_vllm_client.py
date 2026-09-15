from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import sys
import threading
import time
from pathlib import Path
from typing import Any

import requests

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from pilot_collect import (
    LocalTranslationClassifier,
    TRANSLATION_OUTPUT_SCHEMA,
    strong_original_evidence,
)
from translation_final_test import sanitized_for_blind_model


def read_records(path: Path) -> list[dict[str, Any]]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return sorted(records, key=lambda item: (item["gold_label"], item["doc_id"]))


def parse_prediction(content: str) -> dict[str, Any] | None:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    if value.get("label") not in {"translation", "original", "uncertain"}:
        return None
    if value.get("confidence") not in {"high", "medium", "low"}:
        return None
    if not isinstance(value.get("evidence"), list):
        return None
    return value


def request_prediction(
    *,
    endpoint: str,
    model: str,
    prompt: str,
    barrier: threading.Barrier,
    timeout: float,
    max_tokens: int,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": 42,
        "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "translation_decision",
                "strict": True,
                "schema": TRANSLATION_OUTPUT_SCHEMA,
            },
        },
    }
    barrier.wait()
    started = time.perf_counter()
    response = requests.post(endpoint, json=payload, timeout=timeout)
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    body = response.json()
    content = body["choices"][0]["message"]["content"]
    usage = body.get("usage") or {}
    return {
        "prediction": parse_prediction(content),
        "latency_seconds": elapsed,
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "invalid_output_chars": 0 if parse_prediction(content) else len(content),
    }


def run_profile(
    *,
    endpoint: str,
    model: str,
    records: list[dict[str, Any]],
    profile: str,
    batch_size: int,
    timeout: float,
    max_tokens: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not records:
        return [], {
            "calls": 0,
            "valid_json": 0,
            "wall_seconds": 0.0,
            "completion_tokens": 0,
            "completion_tokens_per_second": None,
            "median_request_latency_seconds": None,
            "p95_request_latency_seconds": None,
        }
    classifier = LocalTranslationClassifier(
        model, Path("data/local/unused.jsonl"), profile=profile
    )
    outputs: list[dict[str, Any]] = []
    profile_started = time.perf_counter()

    for batch_start in range(0, len(records), batch_size):
        batch = records[batch_start : batch_start + batch_size]
        barrier = threading.Barrier(len(batch))
        batch_started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = [
                executor.submit(
                    request_prediction,
                    endpoint=endpoint,
                    model=model,
                    prompt=classifier.prompt(record),
                    barrier=barrier,
                    timeout=timeout,
                    max_tokens=max_tokens,
                )
                for record in batch
            ]
            batch_outputs = [future.result() for future in futures]
        batch_elapsed = time.perf_counter() - batch_started
        outputs.extend(batch_outputs)
        completion_tokens = sum(item["completion_tokens"] for item in batch_outputs)
        print(
            json.dumps(
                {
                    "event": "batch",
                    "profile": profile,
                    "batch_index": batch_start // batch_size,
                    "batch_size": len(batch),
                    "valid_json": sum(
                        item["prediction"] is not None for item in batch_outputs
                    ),
                    "wall_seconds": round(batch_elapsed, 3),
                    "completion_tokens": completion_tokens,
                    "completion_tokens_per_second": round(
                        completion_tokens / batch_elapsed, 3
                    ),
                }
            ),
            flush=True,
        )

    wall_seconds = time.perf_counter() - profile_started
    completion_tokens = sum(item["completion_tokens"] for item in outputs)
    latencies = sorted(item["latency_seconds"] for item in outputs)
    p95_index = max(0, min(len(latencies) - 1, round(0.95 * len(latencies) + 0.5) - 1))
    return outputs, {
        "calls": len(outputs),
        "valid_json": sum(item["prediction"] is not None for item in outputs),
        "wall_seconds": round(wall_seconds, 3),
        "prompt_tokens": sum(item["prompt_tokens"] for item in outputs),
        "completion_tokens": completion_tokens,
        "completion_tokens_per_second": round(completion_tokens / wall_seconds, 3),
        "median_request_latency_seconds": round(statistics.median(latencies), 3),
        "p95_request_latency_seconds": round(latencies[p95_index], 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--endpoint",
        default="http://192.168.1.200:8000/v1/chat/completions",
    )
    parser.add_argument("--model", default="qwen3.8-27b")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=160)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    gold_records = read_records(args.dataset)
    records = [sanitized_for_blind_model(record) for record in gold_records]
    started = time.perf_counter()
    strict_outputs, strict_performance = run_profile(
        endpoint=args.endpoint,
        model=args.model,
        records=records,
        profile="strict",
        batch_size=args.batch_size,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
    )
    verifier_indices = [
        index
        for index, (record, output) in enumerate(zip(records, strict_outputs))
        if not (
            output["prediction"] is not None
            and output["prediction"]["label"] == "original"
            and output["prediction"]["confidence"] == "high"
        )
        and strong_original_evidence(record)
    ]
    verifier_records = [records[index] for index in verifier_indices]
    verifier_outputs, verifier_performance = run_profile(
        endpoint=args.endpoint,
        model=args.model,
        records=verifier_records,
        profile="verifier",
        batch_size=args.batch_size,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
    )
    verifier_by_index = dict(zip(verifier_indices, verifier_outputs))

    result_records: list[dict[str, Any]] = []
    for index, (gold, strict_output) in enumerate(zip(gold_records, strict_outputs)):
        strict_prediction = strict_output["prediction"]
        strict_pass = bool(
            strict_prediction
            and strict_prediction["label"] == "original"
            and strict_prediction["confidence"] == "high"
        )
        verifier_output = verifier_by_index.get(index)
        verifier_prediction = verifier_output["prediction"] if verifier_output else None
        verifier_pass = bool(
            verifier_prediction
            and verifier_prediction["label"] == "original"
            and verifier_prediction["confidence"] == "high"
        )
        result_records.append(
            {
                "doc_id": gold["doc_id"],
                "gold_label": gold["gold_label"],
                "strict_prediction": strict_prediction,
                "strict_latency_seconds": round(strict_output["latency_seconds"], 3),
                "strong_original_evidence": strong_original_evidence(records[index]),
                "verifier_prediction": verifier_prediction,
                "verifier_latency_seconds": (
                    round(verifier_output["latency_seconds"], 3)
                    if verifier_output
                    else None
                ),
                "admitted": strict_pass or verifier_pass,
            }
        )

    originals = [item for item in result_records if item["gold_label"] == "original"]
    translations = [
        item for item in result_records if item["gold_label"] == "translation"
    ]
    original_admitted = sum(item["admitted"] for item in originals)
    translation_admitted = sum(item["admitted"] for item in translations)
    summary = {
        "protocol": "translation-gate-1.0-frozen-validation",
        "dataset": str(args.dataset),
        "model": args.model,
        "backend": "nvidia-vllm-0.19.0-bf16",
        "batch_size": args.batch_size,
        "documents": len(result_records),
        "strict_performance": strict_performance,
        "verifier_performance": verifier_performance,
        "total_wall_seconds": round(time.perf_counter() - started, 3),
        "original_total": len(originals),
        "original_admitted": original_admitted,
        "original_retention_rate": original_admitted / len(originals),
        "translation_total": len(translations),
        "translation_admitted": translation_admitted,
        "translation_leak_rate": translation_admitted / len(translations),
        "target_passed": (
            original_admitted / len(originals) >= 0.8 and translation_admitted == 0
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"summary": summary, "records": result_records},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"event": "summary", **summary}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
