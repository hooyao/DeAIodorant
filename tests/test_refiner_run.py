"""Offline regression checks for the frozen development run and resumptions."""

from argparse import Namespace
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from deaiodorant.refine.records import (
    append_jsonl,
    load_jsonl,
    make_candidate,
    text_hash,
    validate_saved_records,
    write_json,
)


@pytest.fixture
def prepared_run(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "experiments/compact_refiner_run.py"
    spec = importlib.util.spec_from_file_location("compact_refiner_run_under_test", source)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    root = tmp_path.resolve()
    route = root / "docs/routes/compact-refiner"
    (route / "prompts").mkdir(parents=True)
    (route / "prompts/draft-v1.txt").write_text("Draft: {{instruction_text}}", encoding="utf-8")
    (route / "prompts/editor-v1.txt").write_text("Edit: {{input_text}}", encoding="utf-8")
    fake_source = root / "experiments/compact_refiner_run.py"
    fake_source.parent.mkdir(parents=True)
    fake_source.write_text("# Frozen driver identity fixture.\n", encoding="utf-8")
    package = root / "src/deaiodorant/refine"
    package.mkdir(parents=True)
    for name in ("records.py", "openrouter.py"):
        (package / name).write_text("# Frozen dependency identity fixture.\n", encoding="utf-8")
    monkeypatch.setattr(driver, "ROOT", root)
    monkeypatch.setattr(driver, "ROUTE", route)
    monkeypatch.setattr(driver, "__file__", str(fake_source))
    monkeypatch.setattr(driver.subprocess, "check_output", lambda *args, **kwargs: "offline-commit\n" if kwargs.get("text") else b"offline-diff")
    briefs_path = root / "input-briefs.jsonl"
    briefs = [{
        "brief_id": f"brief-{index:02d}",
        "task_group_id": f"group-{index:02d}",
        "genre": f"genre-{index // 6}",
        "audience": "General readers",
        "intended_voice": "Clear and restrained",
        "requested_length": "300-600 Chinese characters",
        "instruction_text": f"Explain constructed task {index}.",
        "fact_packet": f"The constructed task ID is {index}.",
        "read_only_context": "",
        "locked_content": "",
        "contains_personal_data": False,
        "rights_status": "project_constructed",
        "required_facts": [{"fact_id": "f1", "statement": "A constructed task.", "protected_literals": []}],
    } for index in range(24)]
    for brief in briefs:
        append_jsonl(briefs_path, brief)
    catalog_path = root / "catalog.json"
    write_json(catalog_path, {"data": [{"id": model, "pricing": {"prompt": "0.0000001", "completion": "0.0000001"}} for model in (*driver.GENERATORS, driver.COMPACT)]})
    args = Namespace(
        run_root=root / "run", dataset_root=root / "data", briefs=briefs_path,
        catalog=catalog_path, phase="prepare", limit=None,
    )
    calls = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def complete(self, **kwargs):
            calls.append(kwargs)
            return {"text": "测试改写。", "metadata": {"requested_model": kwargs["model"]}}

    monkeypatch.setattr("deaiodorant.refine.openrouter.OpenRouterClient", FakeClient)
    driver.prepare(args)
    return SimpleNamespace(driver=driver, args=args, calls=calls)


def fill_sources(run, count=24, *, include_unchanged=True):
    briefs = load_jsonl(run.args.dataset_root / "briefs.jsonl")
    drafts = []
    reviews = []
    for brief in briefs[:count]:
        text = "原始测试文本。"
        draft = {
            "draft_id": brief["brief_id"] + "-draft",
            "brief_id": brief["brief_id"],
            "task_group_id": brief["task_group_id"],
            "draft_text": text,
            "draft_sha256": text_hash(text),
            "human_gold": False,
        }
        drafts.append(draft)
        append_jsonl(run.args.dataset_root / "drafts.jsonl", draft)
        if include_unchanged:
            append_jsonl(run.args.dataset_root / "candidates.jsonl", make_candidate(draft, text, "unchanged"))
        reviews.append({
            "draft_id": draft["draft_id"],
            "draft_sha256": draft["draft_sha256"],
            "fact_packet_sha256": brief["fact_packet_sha256"],
            "reviewer_kind": "model_assisted_agent",
            "human_gold": False,
            "source_fidelity": "pass",
        })
    return briefs, drafts, reviews


def save_reviews(run, reviews):
    for review in reviews:
        append_jsonl(run.args.dataset_root / "source_assessments.jsonl", review)


def test_prepare_balances_generators_and_freezes_materialized_identity(prepared_run):
    run = prepared_run
    manifest, _, briefs = run.driver.load_manifest(run.args)
    allocations = Counter((brief["genre"], manifest["generator_assignments"][brief["brief_id"]]) for brief in briefs)
    assert len(allocations) == 8
    assert set(allocations.values()) == {3}
    assert manifest["materialized_briefs_sha256"] == run.driver.sha_file(run.args.dataset_root / "briefs.jsonl")
    assert all(brief["split"] == "development" for brief in briefs)


def test_modified_manifest_settings_are_rejected(prepared_run):
    run = prepared_run
    path = run.args.run_root / "manifest.initial.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["settings"]["generator_temperature"] = 1.9
    write_json(path, manifest)
    with pytest.raises(ValueError, match="manifest identity"):
        run.driver.load_manifest(run.args)
    assert not run.calls


def test_materialized_brief_replacement_cannot_use_a_rewritten_dataset_hash(prepared_run):
    run = prepared_run
    path = run.args.dataset_root / "briefs.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace("General readers", "Different readers"), encoding="utf-8")
    manifest_path = run.args.dataset_root / "dataset_manifest.json"
    dataset_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_manifest["briefs_sha256"] = run.driver.sha_file(path)
    write_json(manifest_path, dataset_manifest)
    with pytest.raises(ValueError, match="frozen run manifest"):
        run.driver.load_manifest(run.args)


def test_resume_repairs_missing_unchanged_without_model_calls(prepared_run):
    run = prepared_run
    _, drafts, _ = fill_sources(run, include_unchanged=False)
    run.args.phase = "generate"
    run.driver.execute(run.args)
    candidates = load_jsonl(run.args.dataset_root / "candidates.jsonl")
    assert len(candidates) == len(drafts) == 24
    assert all(item["candidate_kind"] == "unchanged" and item["operations"] == [] and item["human_gold"] is False for item in candidates)
    assert not run.calls
    run.driver.execute(run.args)
    assert len(load_jsonl(run.args.dataset_root / "candidates.jsonl")) == 24


def test_partial_generation_cannot_freeze_source_gate(prepared_run):
    run = prepared_run
    _, _, reviews = fill_sources(run, count=1)
    save_reviews(run, reviews)
    run.args.phase = "edit"
    with pytest.raises(ValueError, match="generation must finish"):
        run.driver.execute(run.args)
    assert not (run.args.run_root / "source-gate.json").exists()
    assert not run.calls


@pytest.mark.parametrize("change", [
    {"draft_sha256": "0" * 64},
    {"fact_packet_sha256": "0" * 64},
    {"reviewer_kind": "human"},
    {"human_gold": True},
    {"source_fidelity": "accepted"},
])
def test_source_gate_rejects_stale_or_misattributed_reviews(prepared_run, change):
    run = prepared_run
    _, _, reviews = fill_sources(run)
    reviews[0].update(change)
    save_reviews(run, reviews)
    run.args.phase = "edit"
    with pytest.raises(ValueError, match="identity/provenance"):
        run.driver.execute(run.args)
    assert not run.calls


@pytest.mark.parametrize("change", ["missing", "duplicate", "extra"])
def test_source_gate_requires_exact_review_membership(prepared_run, change):
    run = prepared_run
    _, _, reviews = fill_sources(run)
    if change == "missing":
        reviews.pop()
    elif change == "duplicate":
        reviews.append(deepcopy(reviews[0]))
    else:
        extra = deepcopy(reviews[0])
        extra["draft_id"] = "unknown-draft"
        reviews.append(extra)
    save_reviews(run, reviews)
    run.args.phase = "edit"
    with pytest.raises(ValueError):
        run.driver.execute(run.args)
    assert not run.calls


def test_source_gate_excludes_uncertain_and_failed_sources_and_freezes_review_identity(prepared_run):
    run = prepared_run
    _, drafts, reviews = fill_sources(run)
    for index, review in enumerate(reviews):
        review["source_fidelity"] = "uncertain" if index % 2 else "fail"
    reviews[3]["source_fidelity"] = "pass"
    save_reviews(run, reviews)
    run.args.phase = "edit"
    run.driver.execute(run.args)
    assert len(run.calls) == 1
    assert run.calls[0]["purpose"] == "edit:" + drafts[3]["draft_id"]
    gate = json.loads((run.args.run_root / "source-gate.json").read_text(encoding="utf-8"))
    assert gate["eligible_draft_ids"] == [drafts[3]["draft_id"]]
    run.driver.execute(run.args)
    assert len(run.calls) == 1
    path = run.args.dataset_root / "source_assessments.jsonl"
    content = path.read_text(encoding="utf-8")
    path.write_text(content.replace('"source_fidelity": "uncertain"', '"source_fidelity": "pass"', 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Source gate changed"):
        run.driver.execute(run.args)
    assert len(run.calls) == 1


def saved_fixture():
    briefs = [{"brief_id": "b1", "task_group_id": "g1"}]
    draft = {"brief_id": "b1", "draft_id": "b1-draft", "task_group_id": "g1",
             "draft_text": "原文。", "draft_sha256": text_hash("原文。"), "human_gold": False}
    candidate = make_candidate(draft, "改写。", "compact_prompt")
    return briefs, [draft], [candidate]


@pytest.mark.parametrize("damage", [
    "duplicate_draft", "duplicate_candidate", "draft_hash", "draft_group", "draft_brief",
    "draft_id", "candidate_input", "candidate_output", "candidate_group", "candidate_reference",
    "operations", "candidate_id_kind", "draft_human_gold", "candidate_human_gold",
])
def test_resume_rejects_corrupt_or_ambiguous_saved_records(damage):
    briefs, drafts, candidates = saved_fixture()
    if damage == "duplicate_draft":
        drafts.append(deepcopy(drafts[0]))
    elif damage == "duplicate_candidate":
        candidates.append(deepcopy(candidates[0]))
    elif damage == "draft_hash":
        drafts[0]["draft_text"] = "已经变了。"
    elif damage == "draft_group":
        drafts[0]["task_group_id"] = "another-group"
    elif damage == "draft_brief":
        drafts[0]["brief_id"] = "missing"
    elif damage == "draft_id":
        drafts[0]["draft_id"] = "unexpected"
    elif damage == "candidate_input":
        candidates[0]["input_sha256"] = "0" * 64
    elif damage == "candidate_output":
        candidates[0]["output_text"] = "Changed without updating identity."
    elif damage == "candidate_group":
        candidates[0]["task_group_id"] = "another-group"
    elif damage == "candidate_reference":
        candidates[0]["draft_id"] = "missing"
    elif damage == "operations":
        candidates[0]["operations"][0]["after"] = "Another output."
    elif damage == "candidate_id_kind":
        candidates[0]["candidate_kind"] = "assistant_edit"
    elif damage == "draft_human_gold":
        drafts[0]["human_gold"] = True
    elif damage == "candidate_human_gold":
        candidates[0]["human_gold"] = True
    with pytest.raises(ValueError):
        validate_saved_records(drafts, candidates, briefs)
