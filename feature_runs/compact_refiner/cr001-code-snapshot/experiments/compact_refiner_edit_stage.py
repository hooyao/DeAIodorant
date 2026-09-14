"""Freeze and run editing after explicitly accounted source-request attrition."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from deaiodorant.refine.openrouter import OpenRouterClient
from deaiodorant.refine.records import (
    append_jsonl, load_jsonl, literal_diagnostics, make_candidate, render_prompt,
    text_hash, validate_saved_records, write_json,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN = ROOT / "feature_runs/compact_refiner/cr001-v1"
DATA = ROOT / "data/local/compact_refiner/cr001-v1"
STAGE = ROOT / "feature_runs/compact_refiner/cr001-edit-v1"
MODEL = "mistralai/ministral-3b-2512"
PROMPT = ROOT / "docs/routes/compact-refiner/prompts/editor-v1.txt"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare() -> None:
    if STAGE.exists():
        raise ValueError("Editing-stage directory already exists")
    briefs = load_jsonl(DATA / "briefs.jsonl")
    drafts = load_jsonl(DATA / "drafts.jsonl")
    reviews = load_jsonl(DATA / "source_assessments.jsonl")
    validate_saved_records(drafts, load_jsonl(DATA / "candidates.jsonl"), briefs)
    if len({row["draft_id"] for row in reviews}) != len(reviews):
        raise ValueError("Duplicate source review")
    lookup = {row["draft_id"]: row for row in reviews}
    if set(lookup) != {row["draft_id"] for row in drafts}:
        raise ValueError("Source reviews do not cover the actual drafts")
    by_brief = {row["brief_id"]: row for row in briefs}
    for draft in drafts:
        review = lookup[draft["draft_id"]]
        if (review["draft_sha256"] != draft["draft_sha256"] or
            review["fact_packet_sha256"] != by_brief[draft["brief_id"]]["fact_packet_sha256"] or
            review.get("reviewer_kind") != "model_assisted_agent" or
            review.get("human_gold") is not False or
            review["source_fidelity"] not in {"pass", "fail", "uncertain"}):
            raise ValueError("Invalid source review identity or provenance")
    missing = {brief["brief_id"] + "-draft" for brief in briefs} - set(lookup)
    disposition_path = SOURCE_RUN / "source-disposition-23.json"
    disposition = json.loads(disposition_path.read_text(encoding="utf-8"))
    if missing != {disposition["draft_id"]} or disposition["status"] != "operationally_unavailable":
        raise ValueError("Unaccounted source attrition")
    parent = json.loads((SOURCE_RUN / "manifest.initial.json").read_text(encoding="utf-8"))
    dataset = json.loads((DATA / "dataset_manifest.json").read_text(encoding="utf-8"))
    if sha(SOURCE_RUN / "manifest.initial.json") != dataset["run_manifest_sha256"]:
        raise ValueError("Parent manifest identity mismatch")
    for path, expected in parent["frozen_files"].items():
        if sha(ROOT / path) != expected:
            raise ValueError("Parent frozen file changed")
    files = (DATA / "briefs.jsonl", DATA / "drafts.jsonl", DATA / "source_assessments.jsonl",
             disposition_path, SOURCE_RUN / "manifest.initial.json", PROMPT, Path(__file__),
             ROOT / "src/deaiodorant/refine/records.py", ROOT / "src/deaiodorant/refine/openrouter.py")
    manifest = {
        "schema_version": "compact-refiner-edit-stage-1.0",
        "frozen_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "parent_run_id": "cr001-v1",
        "planned_source_groups": len(briefs), "actual_drafts": len(drafts),
        "operationally_unavailable": sorted(missing),
        "eligible_draft_ids": sorted(row["draft_id"] for row in reviews if row["source_fidelity"] == "pass"),
        "model": MODEL, "pricing": parent["models"][MODEL]["pricing"],
        "settings": {"temperature": 0.0, "max_tokens": 2048, "seed": 20260914,
                     "reasoning": None, "max_retries": 0, "shared_parent_budget_usd": "4"},
        "frozen_files": {path.relative_to(ROOT).as_posix(): sha(path) for path in files},
        "amendment": "All 24 planned sources are accounted: 23 outputs and one unavailable API request. Editing is confined to separately source-reviewed passes. This is a development-stage operational amendment after source inspection and before P outcomes, not a confirmatory study.",
        "human_review_count": 0, "training_export_count": 0,
    }
    write_json(STAGE / "manifest.initial.json", manifest)
    print(json.dumps({"event": "edit_stage_frozen", "eligible": len(manifest["eligible_draft_ids"]),
                      "manifest_sha256": sha(STAGE / "manifest.initial.json")}), flush=True)


def run() -> None:
    manifest = json.loads((STAGE / "manifest.initial.json").read_text(encoding="utf-8"))
    for path, expected in manifest["frozen_files"].items():
        if sha(ROOT / path) != expected:
            raise ValueError("Frozen editing-stage identity changed")
    briefs = load_jsonl(DATA / "briefs.jsonl")
    draft_rows = load_jsonl(DATA / "drafts.jsonl")
    candidate_rows = load_jsonl(DATA / "candidates.jsonl")
    validate_saved_records(draft_rows, candidate_rows, briefs)
    by_brief = {row["brief_id"]: row for row in briefs}
    drafts = {row["draft_id"]: row for row in draft_rows}
    existing = {row["candidate_id"] for row in candidate_rows}
    client = OpenRouterClient(ROOT / ".env", SOURCE_RUN / "api-cache", "4", timeout_seconds=120, max_retries=0)
    template = PROMPT.read_text(encoding="utf-8")
    for draft_id in manifest["eligible_draft_ids"]:
        if draft_id + "-compact_prompt" in existing:
            continue
        draft = drafts[draft_id]
        brief = by_brief[draft["brief_id"]]
        prompt = render_prompt(template, {**brief, "intensity": "medium", "input_text": draft["draft_text"]})
        print(json.dumps({"event": "edit_request_start", "draft_id": draft_id, "time": dt.datetime.now(dt.timezone.utc).isoformat()}), flush=True)
        result = client.complete(MODEL, [{"role": "user", "content": prompt}],
                                 manifest["pricing"]["prompt"], manifest["pricing"]["completion"],
                                 max_tokens=2048, temperature=0.0, reasoning=None,
                                 seed=20260914, purpose="compact_edit:" + draft_id)
        candidate = make_candidate(draft, result["text"], "compact_prompt", result["metadata"])
        candidate["prompt_sha256"] = text_hash(prompt)
        protected = [literal for fact in brief["required_facts"] for literal in fact["protected_literals"]]
        candidate["deterministic_checks"] = literal_diagnostics(draft["draft_text"], result["text"], protected)
        append_jsonl(DATA / "candidates.jsonl", candidate)
        append_jsonl(STAGE / "events.jsonl", {"event": "edit_complete", "draft_id": draft_id,
                     "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                     "output_sha256": candidate["output_sha256"]})
        print(json.dumps({"event": "edit_complete", "draft_id": draft_id,
                          "unchanged": candidate["deterministic_checks"]["unchanged"]}), flush=True)
    write_json(STAGE / "budget-status.json", client.budget_status())
    print(json.dumps({"event": "edit_stage_complete", "budget": client.budget_status()}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run"))
    args = parser.parse_args()
    prepare() if args.phase == "prepare" else run()
