from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from pilot_collect import (
    HttpClient,
    extract_infoq,
    infoq_sitemap_urls,
    stable_order,
    write_jsonl,
)


CALIBRATION_DOC_IDS = {
    "b186cdd4f9004e0413395bf3",
    "3c60dc0a981b686870095450",
}

ORIGINAL_SIGNAL_RE = re.compile(
    r"(?:采访|受访|现场|发布会|技术沙龙|分享嘉宾|本期邀请|项目复盘|建设历程|"
    r"中国|阿里|腾讯|百度|华为|美团|工商银行|研究组|实验室|作者[｜|：:]|我们团队)"
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def collect(args: argparse.Namespace) -> None:
    excluded_records = [
        item
        for dataset in args.exclude_dataset
        for item in read_jsonl(dataset)
    ]
    excluded_ids = {item["doc_id"] for item in excluded_records}.union(CALIBRATION_DOC_IDS)
    excluded_urls = {item["url"] for item in excluded_records}
    client = HttpClient(delay=args.delay)
    urls = stable_order(infoq_sitemap_urls(client, [1, 2, 3, 4]), "translation-holdout-v1")
    translations: list[dict[str, Any]] = []
    originals: list[dict[str, Any]] = []
    for attempt, url in enumerate(urls, start=1):
        if attempt > args.max_attempts:
            break
        if url in excluded_urls:
            continue
        try:
            response = client.get(url)
            record = extract_infoq(response.text, url, "holdout-candidate")
        except Exception:
            continue
        if not record or record["doc_id"] in excluded_ids or not record["quality_pass"]:
            continue
        if "explicit_translator_field" in record.get("translation_evidence", []):
            if len(translations) < args.translations:
                item = dict(record)
                item["gold_label"] = "translation"
                item["gold_evidence"] = [
                    "explicit_translator_field",
                    *record.get("translators", []),
                ]
                translations.append(item)
                print(
                    f"[holdout] translation {len(translations)}/{args.translations}: "
                    f"{record['title']}",
                    flush=True,
                )
        elif (
            len(originals) < args.original_candidates
            and record.get("authors")
            and not record.get("translation_evidence")
            and ORIGINAL_SIGNAL_RE.search(record["text"])
        ):
            item = dict(record)
            item["candidate_label"] = "original_pending_manual_review"
            originals.append(item)
            print(
                f"[holdout] original candidate {len(originals)}/{args.original_candidates}: "
                f"{record['title']}",
                flush=True,
            )
        if len(translations) >= args.translations and len(originals) >= args.original_candidates:
            break
    if len(translations) < args.translations or len(originals) < args.original_candidates:
        raise RuntimeError(
            f"Insufficient holdout candidates: translations={len(translations)}, "
            f"originals={len(originals)}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "translations.jsonl", translations)
    write_jsonl(args.output_dir / "original_candidates.jsonl", originals)
    print(
        json.dumps(
            {
                "translations": len(translations),
                "original_candidates": len(originals),
                "output_dir": str(args.output_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def finalize(args: argparse.Namespace) -> None:
    translations = read_jsonl(args.output_dir / "translations.jsonl")
    candidates = {
        item["doc_id"]: item
        for item in read_jsonl(args.output_dir / "original_candidates.jsonl")
    }
    selected_ids = [
        line.strip()
        for line in args.selected_ids.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(selected_ids) != args.originals or len(set(selected_ids)) != args.originals:
        raise RuntimeError(f"Expected exactly {args.originals} unique manually selected IDs")
    missing = set(selected_ids).difference(candidates)
    if missing:
        raise RuntimeError(f"Selected IDs are not in candidate pool: {sorted(missing)}")
    originals = []
    for doc_id in selected_ids:
        item = dict(candidates[doc_id])
        item.pop("candidate_label", None)
        item["gold_label"] = "original"
        item["gold_evidence"] = ["manual_reviewed_chinese_original"]
        originals.append(item)
    records = translations + originals
    records.sort(
        key=lambda item: hashlib.sha256(
            f"translation-holdout-order\0{item['doc_id']}".encode("utf-8")
        ).digest()
    )
    write_jsonl(args.output_dir / "gold.jsonl", records)
    print(
        json.dumps(
            {
                "documents": len(records),
                "translation": len(translations),
                "original": len(originals),
                "gold": str(args.output_dir / "gold.jsonl"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a disjoint translation holdout set.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument(
        "--exclude-dataset",
        type=Path,
        action="append",
        default=None,
        help="May be repeated. Defaults to both development and validation sets.",
    )
    collect_parser.add_argument(
        "--output-dir", type=Path, default=Path("data/translation_holdout")
    )
    collect_parser.add_argument("--translations", type=int, default=20)
    collect_parser.add_argument("--original-candidates", type=int, default=50)
    collect_parser.add_argument("--max-attempts", type=int, default=800)
    collect_parser.add_argument("--delay", type=float, default=0.12)

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument(
        "--output-dir", type=Path, default=Path("data/translation_holdout")
    )
    finalize_parser.add_argument(
        "--selected-ids",
        type=Path,
        default=Path("data/translation_holdout/selected_original_ids.txt"),
    )
    finalize_parser.add_argument("--originals", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    if args.command == "collect":
        if args.exclude_dataset is None:
            args.exclude_dataset = [
                Path("data/translation_eval/gold.jsonl"),
                Path("data/translation_holdout/gold.jsonl"),
            ]
        collect(args)
    else:
        finalize(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
