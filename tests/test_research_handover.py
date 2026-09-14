import importlib.util
import hashlib
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "experiments/verify_research_handover.py"
SPEC = importlib.util.spec_from_file_location("research_handover_under_test", SOURCE)
handover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handover)


def test_hash_mismatch_does_not_expose_file_content(tmp_path):
    path = tmp_path / "fixture.txt"
    path.write_text("private fixture content", encoding="utf-8")
    with pytest.raises(handover.VerificationError, match="hash_mismatch") as failure:
        handover.verify_hash(path, "0" * 64)
    assert "private fixture content" not in str(failure.value)


def test_span_linkage_counts_duplicate_references_without_duplicate_cases():
    texts = {"body": "甲在此。\n乙在彼。"}
    records = [
        {"block_id": "b1", "text": "甲在此。", "start": 0, "end": 4},
        {"block_id": "b2", "text": "乙在彼。", "start": 5, "end": 9},
    ]
    bounds = handover.build_blocks(texts["body"], records, "text", ("start", "end"))
    span = {"view": "body", "block_id": "b1", "start_char": 0, "end_char": 1, "quote": "甲"}
    assert handover.validate_spans({"source": [span], "context": [span]}, texts,
                                   {"body": bounds}) == (2, 1)


@pytest.mark.parametrize("change,reason", [
    ({"quote": "丙"}, "span_source_mismatch"),
    ({"block_id": "b2"}, "span_outside_block"),
    ({"start_char": False}, "invalid_span_offset"),
    ({"end_char": 10}, "invalid_span_offset"),
])
def test_invalid_spans_fail_without_printing_source(change, reason):
    span = {"view": "body", "block_id": "b1", "start_char": 0, "end_char": 1, "quote": "甲"}
    span.update(change)
    with pytest.raises(handover.VerificationError, match=reason):
        handover.validate_spans(span, {"body": "甲\n乙"}, {"body": {"b1": (0, 1), "b2": (2, 3)}})


def test_blocks_reject_hidden_gaps_and_bad_saved_offsets():
    with pytest.raises(handover.VerificationError, match="block_coverage_mismatch"):
        handover.build_blocks("甲\n乙", [{"block_id": "b1", "text": "甲"}], "text")
    with pytest.raises(handover.VerificationError, match="block_offset_mismatch"):
        handover.build_blocks("甲", [{"block_id": "b1", "text": "甲", "start": 1, "end": 2}],
                              "text", ("start", "end"))


def test_default_missing_private_data_fails_without_writes(tmp_path, capsys):
    assert handover.main(["--root", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "missing_file" in captured.err
    assert not captured.out
    assert list(tmp_path.iterdir()) == []


def test_output_is_opt_in_and_never_overwrites(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(handover, "verify_handover", lambda root: {"source_linkage": "passed"})
    assert handover.main(["--root", str(tmp_path)]) == 0
    assert list(tmp_path.iterdir()) == []
    capsys.readouterr()
    output = tmp_path / "summary.json"
    arguments = ["--root", str(tmp_path), "--output", str(output)]
    assert handover.main(arguments) == 0
    original = output.read_bytes()
    assert json.loads(original) == {"source_linkage": "passed"}
    assert handover.main(arguments) == 1
    assert output.read_bytes() == original
    assert "output_already_exists" in capsys.readouterr().err


def test_inventory_rejects_absolute_parent_and_resolved_external_paths(tmp_path, monkeypatch):
    inventory = tmp_path / "inventory.json"
    record = {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()}

    def save(path):
        inventory.write_text(json.dumps({
            "schema_version": "research-handover-artifacts-1.0",
            "roots": ["data", "feature_runs"], "files": [{**record, "path": path}],
        }), encoding="utf-8")

    for path in ("/data/file", "C:/data/file", "C:relative", "\\\\host\\share\\file",
                 "../file", "data/../../file", "data\\..\\file"):
        save(path)
        with pytest.raises(handover.VerificationError, match="unsafe_inventory_path"):
            handover.verify_inventory(tmp_path, inventory)

    saved_resolve = Path.resolve
    linked_path = tmp_path / "data" / "escape.txt"
    outside_path = tmp_path.parent / "outside.txt"

    def resolve_with_external_link(path, *args, **kwargs):
        if path == linked_path:
            return outside_path
        return saved_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_with_external_link)
    save("data/escape.txt")
    with pytest.raises(handover.VerificationError, match="inventory_path_outside_project"):
        handover.verify_inventory(tmp_path, inventory)


def test_inventory_checks_raw_bytes_and_detects_tampering_or_missing_file(tmp_path):
    directory = tmp_path / "data"
    directory.mkdir()
    artifact = directory / "fixture.bin"
    original = b"original\r\nbytes\x00"
    artifact.write_bytes(original)
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({
        "schema_version": "research-handover-artifacts-1.0",
        "roots": ["data", "feature_runs"],
        "files": [{"path": "data/fixture.bin", "bytes": len(original),
                   "sha256": hashlib.sha256(original).hexdigest()}],
    }), encoding="utf-8")
    assert handover.verify_inventory(tmp_path, inventory) == {
        "status": "passed", "files_verified": 1, "bytes_verified": len(original),
    }
    artifact.write_bytes(original.replace(b"original", b"modified"))
    with pytest.raises(handover.VerificationError, match="inventory_hash_mismatch"):
        handover.verify_inventory(tmp_path, inventory)
    artifact.write_bytes(original + b"extra")
    with pytest.raises(handover.VerificationError, match="inventory_size_mismatch"):
        handover.verify_inventory(tmp_path, inventory)
    artifact.unlink()
    with pytest.raises(handover.VerificationError, match="inventory_missing_file"):
        handover.verify_inventory(tmp_path, inventory)
