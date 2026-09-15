"""用微型合成文章检验冻结身份、结构契约和只读失败报告。"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "experiments/cognitive_move_contract_probe.py"
SPEC = importlib.util.spec_from_file_location("cognitive_move_contract_probe_under_test", SOURCE)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def fixture_run(root):
    run = root / "run"
    probe.write_new(run / "selections.json", {
        "articles": [{"id": f"n{index:02d}", "selection_reason": "不得进入标注 packet"}
                     for index in range(1, 5)]})
    for index in range(1, 5):
        folder = run / "documents" / f"n{index:02d}"
        first, second = "命中缓存时直接返回。", "未命中时请求上游。"
        body = first + "\n\n" + second + "\n"
        probe.write_new(folder / "metadata.json", {
            "title": f"缓存说明 {index}", "author": None, "published_at": "2020-01-01",
            "body_sha256": probe.digest(body.encode()), "full_text_status": "complete",
            "completeness_scope": "全文文字；图片与上游未核验。", "media_references": 2,
            "citation_records": 0,
        })
        (folder / "body.txt").write_bytes(body.encode())
        probe.write_new(folder / "blocks.json", [
            {"block_id": "b1", "text": first, "start_char": 0, "end_char": len(first), "kind": "p"},
            {"block_id": "b2", "text": second, "start_char": len(first) + 2,
             "end_char": len(first) + 2 + len(second), "kind": "p"},
        ])
    for path in (probe.PROTOCOL, probe.CONTRACT, probe.PROMPT, probe.GENERATOR):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("冻结的工程 fixture\n", encoding="utf-8")
    return run


def valid_response(packet, assignment):
    text = packet["document"]["blocks"][1]["text"]
    span = {"block_id": "b1", "quote": text}
    return {
        "assignment_id": assignment["assignment_id"], "packet_id": packet["packet_id"],
        "identity": {"agent_task": "fixture_agent", "model": "synthetic_fixture", "full_article_read": True,
                     "other_outputs_seen": False, "read_paths": [assignment["packet_path"]],
                     "inherited_guidance": [], "procedure_violations": []},
        "article_map": [{"move_id": "m1", "block_ids": ["b1"], "operation": ["解释条件分支"],
                         "description": "交代缓存命中的处理。", "recurrence_group": None}],
        "records": [{
            "move_id": "m1", "focal_spans": [copy.deepcopy(span)], "operation": ["解释条件分支"],
            "question_under_discussion": {"text": "命中缓存后如何处理？", "provenance": "analyst_reconstruction"},
            "prior_or_foil": None,
            "asserted_or_promised_content": [{"claim_id": "c1", "text": text, "source_spans": [copy.deepcopy(span)],
                                               "attribution": {"proposer": "not_stated", "reporting_layer": "author_assertion",
                                                               "epistemic_status": "assertion"}}],
            "relation": {"type": "conditional", "text": "说明运行条件。",
                         "comparands": [{"text": text, "role": "conditional_baseline", "source_spans": [copy.deepcopy(span)]}]},
            "grounds_and_warrant": [{"claim_ids": ["c1"], "evidence_spans": [], "stated_link": None,
                                    "unstated_assumption": None, "unknowns": ["未核实实际实现。"]}],
            "information_update": "说明条件性操作。", "stance_and_presentation": "直接说明。",
            "reader_belief_evidence": [], "preserved_usefulness": ["缓存命中行为。"],
            "possible_reader_cost": [], "uncertainties": [],
        }],
        "omitted_opportunities": ["另一分支没有单列详细动作。"],
    }


def prepared_fixture(root):
    run = fixture_run(root)
    manifest = probe.prepare(root, run)
    assignment_id = manifest["assignment_ids"][0]
    assignment = probe.read_json(run / "frozen" / "assignments" / f"{assignment_id}.json")
    packet = probe.read_json(run / "frozen" / assignment["packet_path"])
    return run, manifest, assignment, packet


def error_codes(result):
    return {error["code"] for error in result["errors"]}


def test_packets_preserve_complete_blocks_limits_and_two_single_article_assignments(tmp_path):
    run, manifest, _, _ = prepared_fixture(tmp_path)
    assert manifest["seed"] == 20260915
    assert manifest["readable_articles"] == 4
    assert manifest["expected_responses"] == 8
    key = probe.read_json(run / "frozen" / "key.json")["packets"]
    for packet_id, item in key.items():
        packet = probe.read_json(run / "frozen" / "packets" / f"{packet_id}.json")
        source = probe.read_json(run / "documents" / item["document_id"] / "blocks.json")
        assert packet["document"]["blocks"][1:] == source
        assert packet["document"]["blocks"][0]["block_id"] == "title"
        assert packet["document"]["metadata"]["media_references"] == 2
        assert packet["document"]["metadata"]["completeness_scope"] == "全文文字；图片与上游未核验。"
        assert "不得进入标注 packet" not in json.dumps(packet, ensure_ascii=False)
        assert item["assignment_a"] != item["assignment_b"]
        for name in ("assignment_a", "assignment_b"):
            assignment = probe.read_json(run / "frozen" / "assignments" / f"{item[name]}.json")
            assert assignment["packet_id"] == packet_id
            assert "packet_ids" not in assignment


def test_prepare_refuses_overwrite_and_source_drift_is_reported(tmp_path):
    run, _, _, _ = prepared_fixture(tmp_path)
    with pytest.raises(ValueError, match="output_already_exists"):
        probe.prepare(tmp_path, run)
    body = run / "documents" / "n01" / "body.txt"
    body.write_bytes(body.read_bytes() + b"changed")
    report = probe.verify(tmp_path, run)
    assert not report["complete"]
    assert report["frozen_inputs"] == "failed"
    assert report["integrity_errors"][0]["code"] == "frozen_source_changed"


@pytest.mark.parametrize("change", ["hash", "uncovered_text", "bad_offset"])
def test_source_identity_and_block_coverage_fail_before_freeze(tmp_path, change):
    run = fixture_run(tmp_path)
    folder = run / "documents" / "n01"
    if change == "hash":
        (folder / "body.txt").write_bytes(b"changed")
    elif change == "uncovered_text":
        body = (folder / "body.txt").read_bytes() + "未被覆盖的尾部".encode()
        (folder / "body.txt").write_bytes(body)
        meta = probe.read_json(folder / "metadata.json")
        meta["body_sha256"] = probe.digest(body)
        (folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    else:
        blocks = probe.read_json(folder / "blocks.json")
        blocks[1]["start_char"] -= 1
        (folder / "blocks.json").write_text(json.dumps(blocks), encoding="utf-8")
    with pytest.raises(ValueError, match="source_"):
        probe.prepare(tmp_path, run)
    assert not (run / "frozen").exists()


def test_null_foil_and_conditional_baseline_are_valid_without_semantic_certification(tmp_path):
    _, _, assignment, packet = prepared_fixture(tmp_path)
    response = valid_response(packet, assignment)
    result = probe.validate_response(response, packet, assignment)
    assert result["errors"] == []
    assert result["valid_quote_occurrences"] == 3
    assert result["semantic_validity"] == "requires_source_review"
    assert result["exposure_validity"] == "requires_root_audit"


def test_negated_proposition_does_not_require_a_known_prior_holder(tmp_path):
    _, _, assignment, packet = prepared_fixture(tmp_path)
    response = valid_response(packet, assignment)
    response["records"][0]["prior_or_foil"] = {
        "proposition": "仅测试结构，不声称来源真的含有否定。", "role": "negated_proposition",
        "source_spans": copy.deepcopy(response["records"][0]["focal_spans"]), "prior_holder": None,
    }
    result = probe.validate_response(response, packet, assignment)
    assert not result["errors"]
    assert result["semantic_validity"] == "requires_source_review"


@pytest.mark.parametrize("mutation,expected", [
    ("quote", "annotation_quote_mismatch"),
    ("claim", "unknown_claim_id"),
    ("focus", "focal_span_outside_mapped_move"),
    ("duplicate_record", "duplicate_detailed_move"),
    ("duplicate_map", "duplicate_move_id"),
    ("baseline_as_foil", "invalid_prior_role"),
    ("invalid_block_type", "unknown_source_block"),
])
def test_contract_rejects_structural_and_linkage_errors(tmp_path, mutation, expected):
    _, _, assignment, packet = prepared_fixture(tmp_path)
    response = valid_response(packet, assignment)
    record = response["records"][0]
    if mutation == "quote":
        record["asserted_or_promised_content"][0]["source_spans"][0]["quote"] = "原文没有的内容"
    elif mutation == "claim":
        record["grounds_and_warrant"][0]["claim_ids"] = ["absent"]
    elif mutation == "focus":
        record["focal_spans"] = [{"block_id": "b2", "quote": "未命中时请求上游。"}]
    elif mutation == "duplicate_record":
        response["records"].append(copy.deepcopy(record))
    elif mutation == "duplicate_map":
        response["article_map"].append(copy.deepcopy(response["article_map"][0]))
    elif mutation == "baseline_as_foil":
        record["prior_or_foil"] = {"proposition": "运行基线", "role": "conditional_baseline",
                                   "source_spans": copy.deepcopy(record["focal_spans"]), "prior_holder": None}
    else:
        record["focal_spans"][0]["block_id"] = []
    result = probe.validate_response(response, packet, assignment)
    assert expected in error_codes(result)


def test_no_opportunity_is_preserved_as_coverage_explanation(tmp_path):
    _, _, assignment, packet = prepared_fixture(tmp_path)
    response = valid_response(packet, assignment)
    response.update(records=[], article_map=[], omitted_opportunities=["没有选中可详细记录的动作。"])
    result = probe.validate_response(response, packet, assignment)
    assert result["errors"] == []
    assert result["records"] == 0
    assert result["semantic_validity"] == "requires_source_review"
    response["omitted_opportunities"] = []
    assert "empty_records_require_coverage_explanation" in error_codes(probe.validate_response(response, packet, assignment))


def test_invalid_response_does_not_stop_other_answers_and_verify_is_read_only(tmp_path):
    run, manifest, _, _ = prepared_fixture(tmp_path)
    for index, assignment_id in enumerate(manifest["assignment_ids"]):
        assignment = probe.read_json(run / "frozen" / "assignments" / f"{assignment_id}.json")
        packet = probe.read_json(run / "frozen" / assignment["packet_path"])
        path = run / "responses" / f"{assignment_id}.json"
        if index == 0:
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{not valid JSON")
        else:
            probe.write_new(path, valid_response(packet, assignment))
    before = {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()}
    report = probe.verify(tmp_path, run)
    after = {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()}
    assert after == before
    assert report["received_responses"] == 8
    assert report["mechanically_valid_responses"] == 7
    assert report["valid_quote_occurrences"] == 21
    assert not report["complete"]
    assert len(report["response_hashes"]) == 8


def test_missing_and_unexpected_responses_do_not_count_as_completion(tmp_path):
    run, _, assignment, packet = prepared_fixture(tmp_path)
    probe.write_new(run / "responses" / f"{assignment['assignment_id']}.json", valid_response(packet, assignment))
    probe.write_new(run / "responses" / "unassigned.json", {})
    result = probe.verify(tmp_path, run)
    assert len(result["missing_assignments"]) == 7
    assert result["unexpected_response_files"] == ["unassigned.json"]
    assert not result["complete"]
