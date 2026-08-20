from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from pilot_collect import (
    HttpClient,
    LocalTranslationClassifier,
    extract_infoq,
    infoq_sitemap_urls,
    stable_order,
    write_jsonl,
)


CALIBRATION_DOC_IDS = {
    "b186cdd4f9004e0413395bf3",
    "3c60dc0a981b686870095450",
}
CALIBRATION_URLS = {
    "https://www.infoq.cn/article/rMYALGzjR1vRRPZgo0gP",
    "https://www.infoq.cn/article/E5KTYyzMBloFXA148vBB",
    "https://www.infoq.cn/article/F7cOsyYyhcBaHUYD5kYx",
    "https://www.infoq.cn/article/s6TAS5JMIW1miPSqIsk0",
}

# Manually reviewed strong negatives. These are Chinese reporting, interviews,
# domestic research summaries, event reports, or first-party technical writing;
# none is an external-language article/interview translation. Deliberately
# derivative or ambiguous foreign-source stories are excluded from this list.
GOLD_ORIGINAL_DOC_IDS = {
    "0dfc33ff7071975b48e12981",
    "9e271d7b118c949e83c9ff8d",
    "be3e4a9eccc5d3a7e69212c3",
    "d8917e9eedea037e2ed53511",
    "bf1abf6ca461ec0bbac14bd7",
    "81938af852e380b36bede22b",
    "7d5e92ccde58b3b78616293c",
    "2d8b8db77aefcdcbf86f23b4",
    "a05a8bb2f7fe7bfe85ba7e46",
    "44aa81958a6c585ee8c06847",
    "48bda219eb0776f623161899",
    "084c17f921cc74b858d04cdb",
    "b77b09a419c1631227112f0c",
    "48a7a6192771112323fd6820",
    "1a5bf7a3c811a61f24384560",
    "2046a00e2b504539234c6c70",
    "2176304c3523784c901e14e0",
    "34be1e39038614fec204e995",
    "728a99c83fb531b12cc55802",
    "9b964dd771030c4c78575a88",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_original_examples(corpus_path: Path, count: int) -> list[dict[str, Any]]:
    records = read_jsonl(corpus_path)
    by_id = {record["doc_id"]: record for record in records}
    missing = GOLD_ORIGINAL_DOC_IDS.difference(by_id)
    if missing:
        raise RuntimeError(f"Manually reviewed original documents are missing: {sorted(missing)}")
    ordered = [by_id[doc_id] for doc_id in sorted(GOLD_ORIGINAL_DOC_IDS)]
    if count > len(ordered):
        raise RuntimeError(f"Only {len(ordered)} manually reviewed originals are available")
    result = []
    for record in ordered[:count]:
        item = dict(record)
        item["gold_label"] = "original"
        item["gold_evidence"] = (
            ["article_type=原创"]
            if record.get("article_type") == "原创"
            else ["Chinese byline", "no translation/source marker"]
        )
        result.append(item)
    return result


def build_translation_examples(client: HttpClient, count: int) -> list[dict[str, Any]]:
    urls = stable_order(infoq_sitemap_urls(client, [1, 2, 3]), "translation-eval-positive")
    result = []
    for attempted, url in enumerate(urls, start=1):
        if attempted > 500 or len(result) >= count:
            break
        if url in CALIBRATION_URLS:
            continue
        try:
            response = client.get(url)
            record = extract_infoq(
                response.text,
                url,
                dt_now(),
            )
        except Exception:
            continue
        if not record or "explicit_translator_field" not in record.get("translation_evidence", []):
            continue
        record["gold_label"] = "translation"
        record["gold_evidence"] = [
            "explicit_translator_field",
            *record.get("translators", []),
        ]
        result.append(record)
        print(
            f"[build] translation {len(result)}/{count}: {record['title']}",
            flush=True,
        )
    if len(result) < count:
        raise RuntimeError(f"Only {len(result)} explicit translations were found")
    return result


def dt_now() -> str:
    import datetime as dt

    return dt.datetime.now(dt.timezone.utc).isoformat()


def build(args: argparse.Namespace) -> None:
    client = HttpClient(delay=args.delay)
    originals = build_original_examples(args.corpus, args.per_class)
    translations = build_translation_examples(client, args.per_class)
    records = sorted(
        originals + translations,
        key=lambda item: hashlib.sha256(
            f"translation-eval-order\0{item['doc_id']}".encode("utf-8")
        ).digest(),
    )
    write_jsonl(args.dataset, records)
    print(
        json.dumps(
            {
                "dataset": str(args.dataset),
                "documents": len(records),
                "original": len(originals),
                "translation": len(translations),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def evaluate(args: argparse.Namespace) -> None:
    records = read_jsonl(args.dataset)
    classifier = LocalTranslationClassifier(
        args.model,
        args.cache,
        timeout=args.timeout,
        profile=args.profile,
    )
    results = []
    started = time.monotonic()
    for index, record in enumerate(records, start=1):
        item = dict(record)
        before = time.monotonic()
        try:
            prediction = classifier.classify(record)
            error = None
        except Exception as exc:
            prediction = {"label": "uncertain", "confidence": "low", "evidence": []}
            error = f"{type(exc).__name__}: {exc}"
        item["model_prediction"] = prediction
        item["model_error"] = error
        item["elapsed_seconds"] = round(time.monotonic() - before, 3)
        item["retention_pass"] = (
            prediction["label"] == "original" and prediction["confidence"] == "high"
        )
        results.append(item)
        print(
            f"[eval] {index}/{len(records)} gold={record['gold_label']} "
            f"pred={prediction['label']}/{prediction['confidence']} {record['title']}",
            flush=True,
        )
    write_jsonl(args.results, results)

    labels = ["translation", "original", "uncertain"]
    confusion = {
        gold: {pred: 0 for pred in labels}
        for gold in ["translation", "original"]
    }
    exact = 0
    for item in results:
        gold = item["gold_label"]
        pred = item["model_prediction"]["label"]
        confusion[gold][pred] += 1
        exact += int(gold == pred)
    originals = [item for item in results if item["gold_label"] == "original"]
    translations = [item for item in results if item["gold_label"] == "translation"]
    summary = {
        "model": args.model,
        "profile": args.profile,
        "documents": len(results),
        "exact_label_accuracy": exact / len(results),
        "confusion": confusion,
        "translation_recall": sum(
            item["model_prediction"]["label"] == "translation" for item in translations
        ) / len(translations),
        "safe_original_retention_rate": sum(item["retention_pass"] for item in originals)
        / len(originals),
        "translation_leak_rate_under_fail_closed_policy": sum(
            item["retention_pass"] for item in translations
        ) / len(translations),
        "total_seconds": round(time.monotonic() - started, 3),
        "results": str(args.results),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and run a balanced translation test set.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--corpus", type=Path, default=Path("data/pilot/pilot_corpus.jsonl"))
    build_parser.add_argument("--dataset", type=Path, default=Path("data/translation_eval/gold.jsonl"))
    build_parser.add_argument("--per-class", type=int, default=20)
    build_parser.add_argument("--delay", type=float, default=0.2)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--dataset", type=Path, default=Path("data/translation_eval/gold.jsonl"))
    run_parser.add_argument("--results", type=Path, default=Path("data/translation_eval/results.jsonl"))
    run_parser.add_argument("--summary", type=Path, default=Path("data/translation_eval/summary.json"))
    run_parser.add_argument("--cache", type=Path, default=Path("data/translation_eval/cache.jsonl"))
    run_parser.add_argument("--model", default="qwen3.5:4b")
    run_parser.add_argument("--profile", choices=["strict", "verifier"], default="strict")
    run_parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    if args.command == "build":
        build(args)
    else:
        evaluate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
