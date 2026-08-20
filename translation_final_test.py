from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from pilot_collect import LocalTranslationClassifier, strong_original_evidence, write_jsonl


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sanitized_for_blind_model(record: dict[str, Any]) -> dict[str, Any]:
    item = dict(record)
    # Explicit dataset labels and structured translator fields are hidden so the
    # final benchmark measures the local language classifier and frozen gate.
    item["is_translation"] = False
    item["translation_evidence"] = []
    item["translators"] = []
    return item


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen final translation gate test.")
    parser.add_argument("--dataset", type=Path, default=Path("data/translation_test/gold.jsonl"))
    parser.add_argument("--results", type=Path, default=Path("data/translation_test/final_results.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("data/translation_test/final_summary.json"))
    parser.add_argument("--model", default="qwen3.5:4b")
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    records = read_jsonl(args.dataset)
    strict = LocalTranslationClassifier(
        args.model,
        Path("data/translation_test/strict_cache.jsonl"),
        timeout=args.timeout,
        profile="strict",
    )
    verifier = LocalTranslationClassifier(
        args.model,
        Path("data/translation_test/verifier_cache.jsonl"),
        timeout=args.timeout,
        profile="verifier",
    )
    output = []
    verifier_calls = 0
    started = time.monotonic()
    for index, gold_record in enumerate(records, start=1):
        record = sanitized_for_blind_model(gold_record)
        item = dict(gold_record)
        try:
            strict_result = strict.classify(record)
            strict_error = None
        except Exception as exc:
            strict_result = {"label": "uncertain", "confidence": "low", "evidence": []}
            strict_error = f"{type(exc).__name__}: {exc}"

        strict_pass = (
            strict_result["label"] == "original"
            and strict_result["confidence"] == "high"
        )
        structured_evidence = strong_original_evidence(record)
        verifier_result = None
        verifier_error = None
        verifier_pass = False
        if not strict_pass and structured_evidence:
            verifier_calls += 1
            try:
                verifier_result = verifier.classify(record)
            except Exception as exc:
                verifier_result = {"label": "uncertain", "confidence": "low", "evidence": []}
                verifier_error = f"{type(exc).__name__}: {exc}"
            verifier_pass = (
                verifier_result["label"] == "original"
                and verifier_result["confidence"] == "high"
            )
        admitted = strict_pass or verifier_pass
        item["strict_prediction"] = strict_result
        item["strict_error"] = strict_error
        item["strong_original_evidence"] = structured_evidence
        item["verifier_prediction"] = verifier_result
        item["verifier_error"] = verifier_error
        item["admitted"] = admitted
        output.append(item)
        print(f"[final-test] {index}/{len(records)}", flush=True)

    write_jsonl(args.results, output)
    originals = [item for item in output if item["gold_label"] == "original"]
    translations = [item for item in output if item["gold_label"] == "translation"]
    admitted_originals = sum(item["admitted"] for item in originals)
    admitted_translations = sum(item["admitted"] for item in translations)
    summary = {
        "protocol": "translation-gate-1.0-frozen",
        "model": args.model,
        "documents": len(output),
        "original_total": len(originals),
        "original_admitted": admitted_originals,
        "original_retention_rate": admitted_originals / len(originals),
        "translation_total": len(translations),
        "translation_admitted": admitted_translations,
        "translation_leak_rate": admitted_translations / len(translations),
        "strict_calls": len(output),
        "verifier_calls": verifier_calls,
        "total_seconds": round(time.monotonic() - started, 3),
        "target_passed": admitted_originals / len(originals) >= 0.8
        and admitted_translations == 0,
        "results": str(args.results),
    }
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
