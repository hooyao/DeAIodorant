"""Acquire post-period InfoQ candidates without admitting them to a corpus."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from deaiodorant.corpus.benchmark import file_sha256
from pilot_collect import (
    POST_END,
    POST_START,
    HttpClient,
    collect_infoq_period,
    write_jsonl,
)


PROTOCOL_VERSION = "post-acquisition-staging-1.0"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire public post-period pages for later fail-closed review."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target", type=int, default=60)
    parser.add_argument("--max-attempts", type=int, default=300)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--http-timeout", type=float, default=45.0)
    args = parser.parse_args()
    if args.target < 1 or args.max_attempts < 1:
        raise SystemExit("Target and attempt limits must be positive")
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    client = HttpClient(delay=args.delay, timeout=args.http_timeout)
    records, stats = collect_infoq_period(
        client,
        "post",
        POST_START,
        POST_END,
        sitemap_indexes=[1, 2],
        target=args.target,
        max_attempts=args.max_attempts,
        translation_classifier=None,
        translation_verifier=None,
    )
    for record in records:
        record["corpus_stage"] = "acquisition_staging"
        record["admission_status"] = "unreviewed"
    candidates_path = output_dir / "infoq_post_candidates.jsonl"
    write_jsonl(candidates_path, records)
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "acquisition_staging_not_admitted",
        "source": "infoq",
        "post_window": [POST_START.isoformat(), POST_END.isoformat()],
        "configuration": {
            "target": args.target,
            "max_attempts": args.max_attempts,
            "delay_seconds": args.delay,
            "http_timeout_seconds": args.http_timeout,
            "sitemap_indexes": [1, 2],
            "translation_model": None,
        },
        "fetch_stats": dataclasses.asdict(stats),
        "documents": len(records),
        "candidates_file": str(candidates_path),
        "candidates_sha256": file_sha256(candidates_path),
        "limitations": [
            "This output is acquisition staging and cannot be used for reader tasks.",
            "Only deterministic translation evidence has been applied.",
            "Model provenance, research value, visibility, and duplicate review remain required.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if len(records) >= args.target else 1


if __name__ == "__main__":
    raise SystemExit(main())
