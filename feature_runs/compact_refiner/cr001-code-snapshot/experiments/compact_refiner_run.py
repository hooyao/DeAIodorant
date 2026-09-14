"""Run the bounded first development batch without training or human labels."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import subprocess

from deaiodorant.refine.records import (
    append_jsonl, literal_diagnostics, load_jsonl, make_candidate, object_hash,
    render_prompt, text_hash, validate_briefs, validate_saved_records, write_json,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / "docs/routes/compact-refiner"
GENERATORS = ("deepseek/deepseek-v4.1-flash", "qwen/qwen3.8-27b")
COMPACT = "mistralai/ministral-3b-2512"
SCHEMA = "compact-refiner-autonomous-preflight-1.0"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def prepare(args: argparse.Namespace) -> None:
    if args.run_root.exists() or args.dataset_root.exists():
        raise ValueError("Prepare requires new run and dataset directories")
    briefs = load_jsonl(args.briefs)
    validate_briefs(briefs)
    genres = Counter(item["genre"] for item in briefs)
    if len(genres) != 4 or set(genres.values()) != {6}:
        raise ValueError("Expected six briefs in each of four genres")
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    lookup = {model["id"]: model for model in catalog["data"]}
    selected = {name: lookup[name] for name in (*GENERATORS, COMPACT)}
    assignments = {}
    per_genre = Counter()
    for brief in briefs:
        assignments[brief["brief_id"]] = GENERATORS[per_genre[brief["genre"]] % 2]
        per_genre[brief["genre"]] += 1
    args.dataset_root.mkdir(parents=True)
    args.run_root.mkdir(parents=True)
    for brief in briefs:
        append_jsonl(args.dataset_root / "briefs.jsonl", {
            **brief, "split": "development", "brief_sha256": object_hash(brief),
            "fact_packet_sha256": text_hash(brief["fact_packet"]),
        })
    frozen = {}
    for path in (args.briefs, args.catalog, ROUTE / "prompts/draft-v1.txt", ROUTE / "prompts/editor-v1.txt",
                 Path(__file__), ROOT / "src/deaiodorant/refine/records.py",
                 ROOT / "src/deaiodorant/refine/openrouter.py"):
        frozen[relative(path)] = sha_file(path)
    manifest = {
        "schema_version": SCHEMA,
        "route_id": "compact-refiner-v1",
        "run_id": args.run_root.name,
        "state": "frozen_before_generation",
        "frozen_at_utc": utc_now(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "tracked_diff_sha256": hashlib.sha256(subprocess.check_output(["git", "diff"], cwd=ROOT)).hexdigest(),
        "python_version": platform.python_version(),
        "dataset_root": relative(args.dataset_root),
        "dataset_version": args.dataset_root.name,
        "role": "development_only",
        "brief_count": len(briefs),
        "materialized_briefs_sha256": sha_file(args.dataset_root / "briefs.jsonl"),
        "genre_counts": dict(genres),
        "generator_assignments": assignments,
        "models": selected,
        "frozen_files": frozen,
        "settings": {"max_tokens": 2048, "generator_temperature": 0.4,
                     "editor_temperature": 0.0, "seed": 20260914, "intensity": "medium",
                     "generator_reasoning": {"enabled": False}, "compact_reasoning": None,
                     "budget_usd": "4", "max_retries": 2, "timeout_seconds": 120},
        "human_review_count": 0,
        "training_export_count": 0,
        "limitations": ["Constructed fictional briefs do not estimate natural editing demand.",
                        "All independent agent reviews are model-assisted, not human gold.",
                        "Remote provider checkpoint revisions may be unavailable."],
    }
    write_json(args.run_root / "manifest.initial.json", manifest)
    write_json(args.dataset_root / "dataset_manifest.json", {
        "schema_version": "compact-refiner-development-1.0", "role": "development",
        "rights_status": "project_constructed", "group_count": len(briefs),
        "briefs_sha256": sha_file(args.dataset_root / "briefs.jsonl"),
        "run_manifest_sha256": sha_file(args.run_root / "manifest.initial.json"),
        "human_gold": False,
    })
    print(json.dumps({"event": "prepared", "groups": len(briefs), "run_id": args.run_root.name,
                      "manifest_sha256": sha_file(args.run_root / "manifest.initial.json")}), flush=True)


def load_manifest(args: argparse.Namespace) -> tuple[dict, Path, list[dict]]:
    manifest = json.loads((args.run_root / "manifest.initial.json").read_text(encoding="utf-8"))
    for name, expected in manifest["frozen_files"].items():
        if sha_file(ROOT / name) != expected:
            raise ValueError("Frozen input/code changed: " + name)
    data = ROOT / manifest["dataset_root"]
    dataset_manifest = json.loads((data / "dataset_manifest.json").read_text(encoding="utf-8"))
    if sha_file(args.run_root / "manifest.initial.json") != dataset_manifest["run_manifest_sha256"]:
        raise ValueError("Frozen run manifest identity changed")
    if sha_file(data / "briefs.jsonl") != dataset_manifest["briefs_sha256"]:
        raise ValueError("Materialized brief identity changed")
    if sha_file(data / "briefs.jsonl") != manifest["materialized_briefs_sha256"]:
        raise ValueError("Materialized briefs do not match frozen run manifest")
    return manifest, data, load_jsonl(data / "briefs.jsonl")


def execute(args: argparse.Namespace) -> None:
    from deaiodorant.refine.openrouter import OpenRouterClient

    manifest, data, briefs = load_manifest(args)
    settings = manifest["settings"]
    client = OpenRouterClient(ROOT / ".env", args.run_root / "api-cache", settings["budget_usd"],
                              timeout_seconds=settings["timeout_seconds"], max_retries=settings["max_retries"])
    draft_template = (ROUTE / "prompts/draft-v1.txt").read_text(encoding="utf-8")
    editor_template = (ROUTE / "prompts/editor-v1.txt").read_text(encoding="utf-8")
    draft_rows = load_jsonl(data / "drafts.jsonl")
    candidate_rows = load_jsonl(data / "candidates.jsonl")
    validate_saved_records(draft_rows, candidate_rows, briefs)
    drafts = {item["draft_id"]: item for item in draft_rows}
    candidates = {item["candidate_id"]: item for item in candidate_rows}
    review_rows = load_jsonl(data / "source_assessments.jsonl")
    if len({item["draft_id"] for item in review_rows}) != len(review_rows):
        raise ValueError("Duplicate source assessment")
    source_reviews = {item["draft_id"]: item for item in review_rows}
    if args.phase == "edit" and len(drafts) != manifest["brief_count"]:
        raise ValueError("Source generation must finish before the edit gate is frozen")
    if args.phase == "edit" and set(drafts) - source_reviews.keys():
        raise ValueError("All source drafts require a separate source-only assessment before editing")
    if args.phase == "edit":
        brief_index = {brief["brief_id"]: brief for brief in briefs}
        if source_reviews.keys() != drafts.keys():
            raise ValueError("Source assessment IDs differ from draft IDs")
        for draft_id, review in source_reviews.items():
            draft = drafts[draft_id]
            brief = brief_index[draft["brief_id"]]
            if (review["draft_sha256"] != draft["draft_sha256"] or
                review["fact_packet_sha256"] != brief["fact_packet_sha256"] or
                review.get("reviewer_kind") != "model_assisted_agent" or
                review.get("human_gold") is not False or
                review.get("source_fidelity") not in {"pass", "fail", "uncertain"}):
                raise ValueError("Source assessment identity/provenance mismatch")
        gate_path = args.run_root / "source-gate.json"
        source_gate = {"source_assessments_sha256": sha_file(data / "source_assessments.jsonl"),
                       "eligible_draft_ids": sorted(key for key, review in source_reviews.items()
                                                    if review["source_fidelity"] == "pass")}
        if gate_path.exists() and json.loads(gate_path.read_text(encoding="utf-8")) != source_gate:
            raise ValueError("Source gate changed after candidate generation began")
        if not gate_path.exists():
            write_json(gate_path, source_gate)
    attempted = 0
    for brief in briefs:
        draft_id = brief["brief_id"] + "-draft"
        if args.phase == "generate":
            if draft_id in drafts:
                if draft_id + "-unchanged" not in candidates:
                    repaired = make_candidate(drafts[draft_id], drafts[draft_id]["draft_text"], "unchanged")
                    protected = [literal for fact in brief["required_facts"] for literal in fact["protected_literals"]]
                    repaired["deterministic_checks"] = literal_diagnostics(drafts[draft_id]["draft_text"], repaired["output_text"], protected)
                    append_jsonl(data / "candidates.jsonl", repaired)
                    candidates[repaired["candidate_id"]] = repaired
                continue
            model = manifest["generator_assignments"][brief["brief_id"]]
            prompt = render_prompt(draft_template, brief)
            temperature, reasoning = settings["generator_temperature"], settings["generator_reasoning"]
        else:
            if draft_id not in drafts:
                continue
            if source_reviews[draft_id]["source_fidelity"] != "pass":
                continue
            if draft_id + "-compact_prompt" in candidates:
                continue
            model = COMPACT
            prompt = render_prompt(editor_template, {**brief, "intensity": "medium", "input_text": drafts[draft_id]["draft_text"]})
            temperature, reasoning = settings["editor_temperature"], settings["compact_reasoning"]
        prices = manifest["models"][model]["pricing"]
        print(json.dumps({"event": "request_start", "phase": args.phase, "draft_id": draft_id, "model": model, "time": utc_now()}), flush=True)
        try:
            result = client.complete(
                model=model, messages=[{"role": "user", "content": prompt}],
                prompt_price_per_token=prices["prompt"], completion_price_per_token=prices["completion"],
                max_tokens=settings["max_tokens"], temperature=temperature, reasoning=reasoning,
                seed=settings["seed"], purpose=args.phase + ":" + draft_id,
            )
        except Exception as exc:
            append_jsonl(data / "operational_failures.jsonl", {"draft_id": draft_id, "phase": args.phase,
                          "error_type": type(exc).__name__, "time": utc_now()})
            print(json.dumps({"event": "request_failed", "draft_id": draft_id, "error_type": type(exc).__name__}), flush=True)
            raise
        if args.phase == "generate":
            draft = {"schema_version": SCHEMA, "draft_id": draft_id, "brief_id": brief["brief_id"],
                     "task_group_id": brief["task_group_id"], "genre": brief["genre"], "split": "development",
                     "draft_text": result["text"], "draft_sha256": text_hash(result["text"]),
                     "prompt_sha256": text_hash(prompt), "generator": model, "inference": result["metadata"],
                     "generated_at_utc": utc_now(), "fact_packet_consistency": "awaiting_model_assisted_review",
                     "human_gold": False}
            append_jsonl(data / "drafts.jsonl", draft)
            drafts[draft_id] = draft
            candidate = make_candidate(draft, draft["draft_text"], "unchanged")
        else:
            draft = drafts[draft_id]
            candidate = make_candidate(draft, result["text"], "compact_prompt", result["metadata"])
            candidate["prompt_sha256"] = text_hash(prompt)
        protected = [literal for fact in brief["required_facts"] for literal in fact["protected_literals"]]
        candidate["deterministic_checks"] = literal_diagnostics(draft["draft_text"], candidate["output_text"], protected)
        append_jsonl(data / "candidates.jsonl", candidate)
        candidates[candidate["candidate_id"]] = candidate
        attempted += 1
        print(json.dumps({"event": "request_complete", "phase": args.phase, "draft_id": draft_id,
                          "draft_count": len(drafts), "candidate_count": len(candidates), "time": utc_now()}), flush=True)
        if args.limit and attempted >= args.limit:
            break
    summarize(args)


def summarize(args: argparse.Namespace) -> None:
    manifest, data, briefs = load_manifest(args)
    drafts = load_jsonl(data / "drafts.jsonl")
    candidates = load_jsonl(data / "candidates.jsonl")
    validate_saved_records(drafts, candidates, briefs)
    failures = load_jsonl(data / "operational_failures.jsonl")
    summary = {"schema_version": SCHEMA, "run_id": manifest["run_id"], "updated_at_utc": utc_now(),
               "planned_groups": len(briefs), "drafts": len(drafts),
               "independent_draft_groups": len({row["task_group_id"] for row in drafts}),
               "candidate_counts": dict(Counter(row["candidate_kind"] for row in candidates)),
               "operational_failure_records": len(failures), "human_review_count": 0,
               "training_export_count": 0, "state": "model_only_development",
               "artifact_hashes": {path.name: sha_file(path) for path in sorted(data.glob("*.jsonl"))}}
    write_json(args.run_root / "progress.json", summary)
    print(json.dumps(summary, ensure_ascii=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "generate", "edit", "summary"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--briefs", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.phase == "prepare":
        if not all((args.dataset_root, args.briefs, args.catalog)):
            parser.error("prepare requires --dataset-root, --briefs, and --catalog")
        prepare(args)
    elif args.phase == "summary":
        summarize(args)
    else:
        execute(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
