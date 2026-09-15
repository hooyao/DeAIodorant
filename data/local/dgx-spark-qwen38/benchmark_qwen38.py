from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration

from pilot_collect import LocalTranslationClassifier, strong_original_evidence
from translation_final_test import sanitized_for_blind_model


def gibibytes(value: int) -> float:
    return round(value / 1024**3, 3)


def load_records(path: Path, per_label: int) -> list[dict]:
    by_label: dict[str, list[dict]] = {"original": [], "translation": []}
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        label = record.get("gold_label")
        if label in by_label:
            by_label[label].append(record)
    selected: list[dict] = []
    for label in ("original", "translation"):
        selected.extend(sorted(by_label[label], key=lambda item: item["doc_id"])[:per_label])
    return selected


def parse_result(text: str) -> dict | None:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    try:
        value = json.loads(cleaned.strip())
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


def run_profile(
    *,
    model,
    processor,
    records: list[dict],
    profile: str,
    batch_size: int,
    max_new_tokens: int,
) -> tuple[list[dict | None], dict]:
    if not records:
        return [], {
            "calls": 0,
            "valid_json": 0,
            "payload_tokens": 0,
            "generated_token_slots": 0,
            "seconds": 0.0,
            "payload_tokens_per_second": None,
            "generated_token_slots_per_second": None,
        }
    classifier = LocalTranslationClassifier(
        "qwen3.8-27b", Path("/tmp/unused.jsonl"), profile=profile
    )
    predictions: list[dict | None] = []
    payload_tokens = 0
    generated_token_slots = 0
    total_seconds = 0.0

    for batch_start in range(0, len(records), batch_size):
        batch_records = records[batch_start : batch_start + batch_size]
        prompts = [classifier.prompt(record) for record in batch_records]
        texts = [
            processor.apply_chat_template(
                [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            for prompt in prompts
        ]
        inputs = processor(
            text=texts,
            padding=True,
            return_tensors="pt",
        ).to("cuda")
        input_tokens = [int(value) for value in inputs["attention_mask"].sum(dim=1)]
        input_width = int(inputs["input_ids"].shape[-1])
        torch.cuda.synchronize()
        batch_started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                use_cache=True,
            )
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - batch_started
        output_ids = generated[:, input_width:]
        output_texts = processor.batch_decode(output_ids, skip_special_tokens=True)
        output_tokens = [
            len(processor.tokenizer.encode(text, add_special_tokens=False))
            for text in output_texts
        ]
        parsed = [parse_result(text) for text in output_texts]
        predictions.extend(parsed)
        payload_tokens += sum(output_tokens)
        generated_token_slots += int(output_ids.numel())
        total_seconds += elapsed
        print(
            json.dumps(
                {
                    "event": "batch",
                    "profile": profile,
                    "batch_index": batch_start // batch_size,
                    "batch_size": len(batch_records),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "valid_json": sum(item is not None for item in parsed),
                    "seconds": round(elapsed, 3),
                    "payload_tokens_per_second": round(sum(output_tokens) / elapsed, 3),
                    "generated_token_slots_per_second": round(
                        output_ids.numel() / elapsed, 3
                    ),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    return predictions, {
        "calls": len(records),
        "valid_json": sum(item is not None for item in predictions),
        "payload_tokens": payload_tokens,
        "generated_token_slots": generated_token_slots,
        "seconds": round(total_seconds, 3),
        "payload_tokens_per_second": round(payload_tokens / total_seconds, 3),
        "generated_token_slots_per_second": round(
            generated_token_slots / total_seconds, 3
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--per-label", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    args = parser.parse_args()

    torch.manual_seed(42)
    before_free, total_memory = torch.cuda.mem_get_info()
    started = time.perf_counter()
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True)
    processor.tokenizer.padding_side = "left"
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        args.model,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        low_cpu_mem_usage=True,
        local_files_only=True,
    ).eval()
    torch.cuda.synchronize()
    load_seconds = time.perf_counter() - started
    after_free, _ = torch.cuda.mem_get_info()
    print(
        json.dumps(
            {
                "event": "model_loaded",
                "model": str(args.model),
                "dtype": "bfloat16",
                "load_seconds": round(load_seconds, 3),
                "cuda_total_gib": gibibytes(total_memory),
                "cuda_free_before_gib": gibibytes(before_free),
                "cuda_free_after_gib": gibibytes(after_free),
                "cuda_allocated_gib": gibibytes(torch.cuda.memory_allocated()),
                "cuda_reserved_gib": gibibytes(torch.cuda.memory_reserved()),
                "cuda_peak_allocated_gib": gibibytes(torch.cuda.max_memory_allocated()),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    gold_records = load_records(args.dataset, args.per_label)
    records = [sanitized_for_blind_model(record) for record in gold_records]
    strict_predictions, strict_performance = run_profile(
        model=model,
        processor=processor,
        records=records,
        profile="strict",
        batch_size=args.batch_size,
        max_new_tokens=args.max_new_tokens,
    )
    verifier_indices = [
        index
        for index, (record, prediction) in enumerate(zip(records, strict_predictions))
        if not (
            prediction is not None
            and prediction["label"] == "original"
            and prediction["confidence"] == "high"
        )
        and strong_original_evidence(record)
    ]
    verifier_records = [records[index] for index in verifier_indices]
    verifier_predictions, verifier_performance = run_profile(
        model=model,
        processor=processor,
        records=verifier_records,
        profile="verifier",
        batch_size=args.batch_size,
        max_new_tokens=args.max_new_tokens,
    )
    verifier_by_index = dict(zip(verifier_indices, verifier_predictions))
    admitted: list[bool] = []
    correct_labels = 0
    for index, (gold_record, strict_prediction) in enumerate(
        zip(gold_records, strict_predictions)
    ):
        strict_pass = bool(
            strict_prediction
            and strict_prediction["label"] == "original"
            and strict_prediction["confidence"] == "high"
        )
        verifier_prediction = verifier_by_index.get(index)
        verifier_pass = bool(
            verifier_prediction
            and verifier_prediction["label"] == "original"
            and verifier_prediction["confidence"] == "high"
        )
        admitted.append(strict_pass or verifier_pass)
        correct_labels += int(
            strict_prediction is not None
            and strict_prediction["label"] == gold_record["gold_label"]
        )

    original_indices = [
        index
        for index, record in enumerate(gold_records)
        if record["gold_label"] == "original"
    ]
    translation_indices = [
        index
        for index, record in enumerate(gold_records)
        if record["gold_label"] == "translation"
    ]
    original_admitted = sum(admitted[index] for index in original_indices)
    translation_admitted = sum(admitted[index] for index in translation_indices)
    print(
        json.dumps(
            {
                "event": "summary",
                "batch_size": args.batch_size,
                "documents": len(records),
                "strict_performance": strict_performance,
                "verifier_performance": verifier_performance,
                "strict_correct_labels": correct_labels,
                "original_total": len(original_indices),
                "original_admitted": original_admitted,
                "original_retention_rate": original_admitted / len(original_indices),
                "translation_total": len(translation_indices),
                "translation_admitted": translation_admitted,
                "translation_leak_rate": translation_admitted
                / len(translation_indices),
                "target_passed": (
                    original_admitted / len(original_indices) >= 0.8
                    and translation_admitted == 0
                ),
                "cuda_peak_allocated_gib": gibibytes(torch.cuda.max_memory_allocated()),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
