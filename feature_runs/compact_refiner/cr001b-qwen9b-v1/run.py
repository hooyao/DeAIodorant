"""Run one frozen Qwen 9B development control without selecting outputs."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

import requests


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from deaiodorant.refine.openrouter import OpenRouterClient
from deaiodorant.refine.records import append_jsonl, load_jsonl, write_json


STAGE = Path(__file__).resolve().parent
INPUTS = ROOT / "data/local/compact_refiner/cr001-v1/teacher_inputs.jsonl"
OUTPUT = ROOT / "data/local/compact_refiner/cr001-v1/qwen9b_proposals.jsonl"
CATALOG = ROOT / "feature_runs/compact_refiner/cr001-catalog-20260914/models.json"
CACHE = ROOT / "feature_runs/compact_refiner/cr001-v1/api-cache"
MODEL = "qwen/qwen3.5-9b"
HF_URL = "https://huggingface.co/api/models/Qwen/Qwen3.5-9B"
SETTINGS = {
    "max_tokens": 2048,
    "temperature": 0,
    "reasoning": {"enabled": False},
    "seed": 20260914,
    "timeout_seconds": 120,
    "max_retries": 0,
    "shared_parent_budget_usd": "4",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def read_inputs():
    rows = load_jsonl(INPUTS)
    if len(rows) != 13 or len({row["case_id"] for row in rows}) != 13:
        raise ValueError("Unexpected input count or duplicate case ID")
    for row in rows:
        if hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest() != row["input_prompt_sha256"]:
            raise ValueError("Rendered input prompt hash mismatch")
    return rows


def prepare():
    if (STAGE / "manifest.initial.json").exists() or OUTPUT.exists():
        raise ValueError("Preparation requires a fresh arm")
    inputs = read_inputs()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    matches = [row for row in catalog["data"] if row["id"] == MODEL]
    if len(matches) != 1:
        raise ValueError("Catalog model identity is missing or ambiguous")
    model = matches[0]
    pricing = model["pricing"]
    if Decimal(pricing["prompt"]) != Decimal("0.0000001") or Decimal(pricing["completion"]) != Decimal("0.00000015"):
        raise ValueError("Catalog prices differ from the authorized arm")
    if any(Decimal(str(value)) != 0 for name, value in pricing.items() if name not in {"prompt", "completion"}):
        raise ValueError("Additional pricing fields require separate review")
    if not {"max_tokens", "temperature", "reasoning", "seed"} <= set(model["supported_parameters"]):
        raise ValueError("Required request parameters are not exposed by the catalog")
    with requests.Session() as session:
        session.trust_env = False
        response = session.get(HF_URL, timeout=60, allow_redirects=False)
        if response.status_code != 200:
            raise ValueError("Official public model metadata request failed")
        hf = response.json()
    if hf.get("id") != "Qwen/Qwen3.5-9B" or hf.get("cardData", {}).get("license") != "apache-2.0":
        raise ValueError("Official model identity or expected Apache-2.0 license was not verified")
    hf_snapshot = {
        "url": HF_URL,
        "fetched_at_utc": utc_now(),
        "response_sha256": hashlib.sha256(response.content).hexdigest(),
        "metadata": hf,
    }
    write_json(STAGE / "hf-model-metadata.json", hf_snapshot)
    with OpenRouterClient(ROOT / ".env", CACHE, "4", timeout_seconds=120, max_retries=0) as client:
        budget = client.budget_status()
    if budget["unfinished_reservations"] != 0:
        raise ValueError("The shared ledger contains an unresolved request reservation")
    write_json(STAGE / "budget-before.json", budget)
    frozen = [INPUTS, CATALOG, STAGE / "hf-model-metadata.json", Path(__file__),
              ROOT / "src/deaiodorant/refine/openrouter.py",
              ROOT / "src/deaiodorant/refine/records.py"]
    manifest = {
        "schema_version": "compact-refiner-capacity-control-1.0",
        "run_id": STAGE.name,
        "experiment_id": "CR-001B",
        "frozen_at_utc": utc_now(),
        "role": "exploratory_development_follow_up",
        "rationale": "After initial pipeline evidence, add a Chinese-capable 9B capacity control rather than inferring a general need for SFT from one weak 3B baseline. This arm adds evidence and does not replace or conceal the earlier arm.",
        "selection_timing": "After CR-001 model-assisted pipeline evidence and before observing this arm's outcomes.",
        "input_count": len(inputs),
        "input_order": [row["case_id"] for row in inputs],
        "input_prompt_hashes": {row["case_id"]: row["input_prompt_sha256"] for row in inputs},
        "model": model,
        "license": {
            "identifier": "apache-2.0",
            "evidence_url": HF_URL,
            "hugging_face_repository": hf["id"],
            "hugging_face_revision": hf.get("sha"),
            "limitation": "The repository license is verified; a hosted endpoint does not expose evidence that its exact checkpoint equals this repository revision. Hosted service terms still apply.",
        },
        "settings": SETTINGS,
        "budget_scope": "Shares the original CR-001 USD4 durable ledger; the separately capped USD1 smoke allowance keeps the combined ceilings within USD5.",
        "cache_directory": relative(CACHE),
        "output_path": relative(OUTPUT),
        "frozen_files": {relative(path): sha(path) for path in frozen},
        "protocol": {
            "requests_per_input": 1,
            "stop_on_any_api_failure": True,
            "prompt_retries": False,
            "selective_regeneration": False,
            "author_evaluates_own_outputs": False,
            "human_gold": False,
            "held_out_evaluation": False,
            "student_selection": False,
            "training": False,
        },
        "cost_note": "Frozen catalog prices are USD0.10 per million prompt tokens and USD0.15 per million completion tokens. The existing client enforces matching provider price ceilings and reserves each request before submission.",
    }
    write_json(STAGE / "manifest.initial.json", manifest)
    print(json.dumps({"event": "arm_frozen", "run_id": STAGE.name,
                      "manifest_sha256": sha(STAGE / "manifest.initial.json"),
                      "cases": len(inputs), "budget": budget}), flush=True)


def run(expected_manifest_sha256):
    manifest_path = STAGE / "manifest.initial.json"
    if sha(manifest_path) != expected_manifest_sha256:
        raise ValueError("Externally recorded arm manifest identity changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest["frozen_files"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("Frozen capacity-control input or code changed")
    inputs = read_inputs()
    if [row["case_id"] for row in inputs] != manifest["input_order"]:
        raise ValueError("Input order changed")
    if OUTPUT.exists() or (STAGE / "request-intents.jsonl").exists():
        raise ValueError("This single-attempt arm cannot be repeated or automatically resumed")
    prices = manifest["model"]["pricing"]
    completed = 0
    with OpenRouterClient(ROOT / ".env", CACHE, "4", timeout_seconds=120, max_retries=0) as client:
        for row in inputs:
            intent = {"case_id": row["case_id"], "input_prompt_sha256": row["input_prompt_sha256"],
                      "started_at_utc": utc_now(), "requested_model": MODEL}
            append_jsonl(STAGE / "request-intents.jsonl", intent)
            print(json.dumps({"event": "request_start", "case_id": row["case_id"]}), flush=True)
            try:
                result = client.complete(
                    MODEL, [{"role": "user", "content": row["prompt"]}],
                    prices["prompt"], prices["completion"],
                    max_tokens=2048, temperature=0, reasoning={"enabled": False},
                    seed=20260914, purpose="qwen9b_capacity:" + row["case_id"],
                )
                append_jsonl(OUTPUT, {
                    "case_id": row["case_id"],
                    "output_text": result["text"],
                    "input_prompt_sha256": row["input_prompt_sha256"],
                    "author_kind": "model_assisted_api",
                    "human_gold": False,
                    "inference": result["metadata"],
                    "arm_id": "qwen3.5-9b_capacity_control",
                })
            except Exception as error:
                failure = {
                    "state": "failed_no_further_requests",
                    "case_id": row["case_id"], "completed_cases": completed,
                    "error_type": type(error).__name__,
                    "safe_reason": getattr(error, "reason", "non_api_failure"),
                    "finished_at_utc": utc_now(),
                    "human_gold": False,
                }
                write_json(STAGE / "completion.json", failure)
                print(json.dumps({"event": "arm_stopped", "case_id": row["case_id"],
                                  "reason": failure["safe_reason"]}), flush=True)
                return 1
            completed += 1
            event = {"event": "request_complete", "case_id": row["case_id"],
                     "cost": result["metadata"]["cost"], "completed_at_utc": utc_now()}
            append_jsonl(STAGE / "events.jsonl", event)
            print(json.dumps({"event": "request_complete", "case_id": row["case_id"],
                              "cost": event["cost"]}), flush=True)
        budget = client.budget_status()
    write_json(STAGE / "budget-after.json", budget)
    proposals = load_jsonl(OUTPUT)
    if len(proposals) != 13 or Counter(row["case_id"] for row in proposals) != Counter(manifest["input_order"]):
        raise ValueError("Completed proposal IDs differ from the frozen arm")
    reported_cost = sum((Decimal(row["inference"]["cost"]["reported_usd"]) for row in proposals), Decimal(0))
    completion = {"state": "generated_awaiting_independent_review", "completed_cases": completed,
                  "output_sha256": sha(OUTPUT), "reported_arm_cost_usd": str(reported_cost),
                  "shared_budget": budget, "human_gold": False,
                  "finished_at_utc": utc_now()}
    write_json(STAGE / "completion.json", completion)
    print(json.dumps({"event": "arm_complete", "cases": completed, "reported_arm_cost_usd": str(reported_cost)}), flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run"))
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    else:
        if not args.expected_manifest_sha256:
            parser.error("run requires an externally recorded manifest SHA256")
        raise SystemExit(run(args.expected_manifest_sha256))
