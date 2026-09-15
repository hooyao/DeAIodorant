import copy
import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "experiments/cognitive_move_pilot.py"
SPEC = importlib.util.spec_from_file_location("cognitive_move_pilot_under_test", SOURCE)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def small_design():
    documents = {"source": {"blocks": [
        {"block_id": "title", "text": "A title"},
        {"block_id": "b001", "text": "A claim, a reason."},
        {"block_id": "b002", "text": "Unedited context."},
    ]}}
    cases = [{
        "id": f"M{i:02d}", "document": "source", "focus_blocks": ["b001"],
        "equivalent_edits": [{"block_id": "b001", "old": "A claim", "new": "An assertion"}],
        "changed_edits": [{"block_id": "b001", "old": "A claim", "new": "No claim"}],
        "expected_after": "This answer must never reach the annotator",
    } for i in range(1, 7)]
    return {"cases": cases}, documents


def test_packets_preserve_context_hide_answer_keys_and_keep_sources_immutable():
    design, documents = small_design()
    original = copy.deepcopy(documents)
    packets, key, assignments = pilot.make_packets(design, documents, 20260914)
    assert documents == original
    assert len(packets) == 18
    for packet in packets.values():
        assert set(packet) == {"version", "packet_id", "focus_blocks", "document"}
        assert packet["document"]["blocks"][0] == original["source"]["blocks"][0]
        assert packet["document"]["blocks"][2] == original["source"]["blocks"][2]
        assert "This answer must never reach" not in pilot.canonical(packet).decode()
    assert pilot.make_packets(design, documents, 20260914) == (packets, key, assignments)


def test_cyclic_assignment_has_one_version_per_case_and_two_reads_per_packet():
    design, documents = small_design()
    packets, key, assignments = pilot.make_packets(design, documents, 19)
    seen = []
    for ids in assignments.values():
        assert len(ids) == 6
        assert len({key[packet_id]["case_id"] for packet_id in ids}) == 6
        assert {key[packet_id]["condition"] for packet_id in ids} == set(pilot.CONDITIONS)
        seen.extend(ids)
    assert all(seen.count(packet_id) == 2 for packet_id in packets)


def test_ambiguous_or_out_of_focus_edits_fail_without_modifying_input():
    document = {"blocks": [{"block_id": "b1", "text": "A A"},
                            {"block_id": "b2", "text": "B"}]}
    original = copy.deepcopy(document)
    with pytest.raises(ValueError, match="not_unique"):
        pilot.modify_document(document, [{"block_id": "b1", "old": "A", "new": "C"}], ["b1"])
    with pytest.raises(ValueError, match="outside_focus"):
        pilot.modify_document(document, [{"block_id": "b2", "old": "B", "new": "C"}], ["b1"])
    assert document == original


def test_annotation_must_quote_current_packet_and_respect_focus():
    packet = {"packet_id": "p1", "focus_blocks": ["b1"], "document": {"blocks": [
        {"block_id": "b1", "text": "Changed assertion."},
        {"block_id": "b2", "text": "Context."},
    ]}}
    record = {field: "description" for field in pilot.FIELDS}
    record.update(packet_id="p1", full_context_read=True,
                  focal_spans=[{"block_id": "b1", "quote": "Changed assertion."}])
    assert pilot.validate_record(record, packet) == 1
    record["focal_spans"][0]["quote"] = "Original assertion."
    with pytest.raises(ValueError, match="quote_mismatch"):
        pilot.validate_record(record, packet)
    record["focal_spans"] = [{"block_id": "b2", "quote": "Context."}]
    with pytest.raises(ValueError, match="outside_assigned_focus"):
        pilot.validate_record(record, packet)


def test_frozen_outputs_refuse_overwrite(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "response.json"
    marker.write_bytes(b"untouched")
    with pytest.raises(ValueError, match="output_already_exists"):
        pilot.prepare(tmp_path, tmp_path / "absent-design", output, 1)
    with pytest.raises(FileExistsError):
        pilot.write_new(marker, {"overwrite": True})
    assert marker.read_bytes() == b"untouched"
