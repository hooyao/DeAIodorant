"""Offline checks for context metrics and immutable review-packet preparation."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def audit(monkeypatch):
    experiments = Path(__file__).resolve().parents[1] / "experiments"
    monkeypatch.syspath_prepend(str(experiments))
    spec = importlib.util.spec_from_file_location(
        "contrast_context_audit_under_test", experiments / "contrast_context_audit.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("width", [0, -1])
def test_concentration_rejects_nonpositive_width(audit, width):
    with pytest.raises(ValueError, match="positive"):
        audit.concentration("而是", width)


@pytest.mark.parametrize("width", [500, 1000])
def test_concentration_uses_strict_start_distance(audit, width):
    within = "而是" + "甲" * (width - 3) + "而是"
    boundary = "而是" + "甲" * (width - 2) + "而是"
    assert audit.concentration(within, width)["connector_start_cjk"] == [0, width - 1]
    assert audit.concentration(boundary, width)["max_occurrences"] == 1


def test_concentration_ignores_noncjk_runs_but_exposes_unicode_positions(audit):
    text = "㐀A😀而是" + " latin 123\n!? " * 100 + "而是"
    result = audit.concentration(text, 3)
    assert result["max_occurrences"] == 2
    assert result["connector_start_cjk"] == [1, 3]
    assert result["connector_start_chars"] == [3, text.rindex("而是")]
    assert result["body_shorter_than_window"] is False


@pytest.mark.parametrize(
    ("text", "width", "expected_count", "short"),
    [("", 500, 0, True), ("Latin 😀!?", 500, 0, True),
     ("甲" * 500, 500, 0, False), ("而是", 500, 1, True),
     ("而是", 2, 1, False)],
)
def test_concentration_keeps_empty_zero_count_and_short_documents(
    audit, text, width, expected_count, short
):
    result = audit.concentration(text, width)
    assert result["max_occurrences"] == expected_count
    assert result["body_shorter_than_window"] is short
    assert len(result["connector_start_chars"]) == expected_count
    assert len(result["connector_start_cjk"]) == expected_count


def test_concentration_finds_later_overlapping_maximum(audit):
    text = "而是甲甲甲甲而是甲而是而是"
    result = audit.concentration(text, 6)
    assert result["connector_start_cjk"] == [6, 9, 11]
    assert result["max_occurrences"] == 3


def test_concentration_ties_select_the_first_observed_span(audit):
    text = "而是而是甲甲甲甲而是而是"
    assert audit.concentration(text, 3)["connector_start_chars"] == [0, 2]


@pytest.mark.parametrize("terminator", list("。！？!?"))
def test_context_units_use_exact_punctuation_offsets(audit, terminator):
    prefix = "😀前文" + terminator
    expected = "\n甲\n而是\n乙" + terminator
    text = prefix + expected + "末尾"
    start = text.index("而是")
    result = audit.context_span(text, start, start + 2)
    assert result == {
        "start_char": len(prefix), "end_char": len(prefix + expected), "text": expected
    }
    assert text[result["start_char"]:result["end_char"]] == expected


@pytest.mark.parametrize("text", ["而是", "前文\n而是\n末尾", "甲，而是乙；丙.丁"])
def test_context_without_terminators_preserves_whole_body(audit, text):
    start = text.index("而是")
    assert audit.context_span(text, start, start + 2) == {
        "start_char": 0, "end_char": len(text), "text": text
    }


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8", newline="\n")


@pytest.fixture
def prepared_audit(audit, tmp_path, monkeypatch):
    root = tmp_path.resolve()
    audit_source = root / "experiments/contrast_context_audit.py"
    implementation_paths = [audit_source, root / "experiments/ershi_cohort_statistics.py",
                            root / "docs/routes/compact-refiner/contrast-context-audit.md"]
    for path in implementation_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Immutable implementation fixture.\n", encoding="utf-8")
    monkeypatch.setattr(audit, "ROOT", root)
    monkeypatch.setattr(audit, "__file__", str(audit_source))
    source = root / "source-metadata.json"
    source.write_text('{"version": 1}\n', encoding="utf-8")
    hashes = {source.relative_to(root).as_posix(): audit.digest(source)}
    articles = []
    for index in range(38):
        count = 9 if index == 0 else 4 if index < 13 else 0 if index < 35 else 1
        text = f"Fixture {index}. " + ("甲😀\n而是乙。" * count or "甲乙。")
        articles.append({
            "doc_id": f"fixture-{index:02d}", "source": "infoq", "dataset": "fixture",
            "title": f"Fixture {index}", "url": f"https://example.invalid/{index}",
            "published_at": "2022-12-31" if index < 17 else "2025-07-01",
            "text": text, "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "known_translation": False, "cohort": "pre" if index < 17 else "post",
            "admission_status": "synthetic_test_fixture",
        })
    articles[35]["source"] = "other"
    articles[36]["cohort"] = "transition"
    articles[37]["known_translation"] = True
    counts = [{"doc_id": row["doc_id"], "content_hash": row["content_hash"],
               "ershi_count": row["text"].count("而是")} for row in articles]
    events = [{"doc_id": row["doc_id"], "connector": {
        "start_char": match.start(), "end_char": match.end(), "literal": "而是"
    }} for row in articles for match in re.finditer("而是", row["text"])]
    previous = root / "feature_runs/ershi-cohort-v1"

    def save_previous():
        _write_jsonl(previous / "document_counts.jsonl", counts)
        _write_jsonl(previous / "instances.jsonl", events)
        audit.write_json(previous / "manifest.json", {
            "input_hashes": dict(hashes),
            "output_hashes": {name: audit.digest(previous / name) for name in
                              ("document_counts.jsonl", "instances.jsonl")},
        })

    save_previous()
    monkeypatch.setattr(audit, "load_articles", lambda: (deepcopy(articles), dict(hashes), []))
    output = root / "data/local/audit-fixture"
    monkeypatch.setattr(sys, "argv", [str(audit_source), "--output-dir", str(output)])
    return SimpleNamespace(audit=audit, root=root, output=output, articles=articles,
                           counts=counts, events=events, previous=previous,
                           source=source, hashes=hashes, save_previous=save_previous)


def test_preparation_retains_zero_counts_and_emits_exact_complete_packets(prepared_audit):
    run = prepared_audit
    assert run.audit.main() == 0
    metrics = json.loads((run.output / "document-metrics.json").read_text(encoding="utf-8"))
    assert len(metrics) == len({row["doc_id"] for row in metrics}) == 35
    assert sum(row["ershi_count"] == 0 for row in metrics) == 22
    assert sum(row["ershi_count"] for row in metrics) == 57
    assert {row["doc_id"] for row in metrics} == {row["doc_id"] for row in run.articles[:35]}
    mapping = json.loads((run.output / "identity-map.json").read_text(encoding="utf-8"))
    assert len(mapping) == 13
    by_id = {row["doc_id"]: row for row in run.articles}
    for row in mapping:
        directory = run.output / "packets" / row["alias"]
        text = by_id[row["doc_id"]]["text"]
        assert (directory / "body.txt").read_bytes() == text.encode("utf-8")
        packet = json.loads((directory / "occurrences.json").read_text(encoding="utf-8"))
        assert set(packet) == {"alias", "content_hash", "occurrences"}
        assert packet["content_hash"] == row["content_hash"]
        assert [item["connector"]["start_char"] for item in packet["occurrences"]] == [
            match.start() for match in re.finditer("而是", text)
        ]
        assert len({item["occurrence_id"] for item in packet["occurrences"]}) == len(packet["occurrences"])
        for item in packet["occurrences"]:
            unit = item["mechanical_context"]
            assert unit["text"] == text[unit["start_char"]:unit["end_char"]]
    manifest = json.loads((run.output / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["output_hashes"]) == 29
    for group, base in [("input_hashes", run.root), ("implementation_hashes", run.root),
                        ("output_hashes", run.output)]:
        assert all(run.audit.digest(base / name) == expected for name, expected in manifest[group].items())


@pytest.mark.parametrize("name", ["document_counts.jsonl", "instances.jsonl"])
def test_preparation_rejects_changed_previous_artifact(prepared_audit, name):
    run = prepared_audit
    with (run.previous / name).open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        run.audit.main()
    assert not run.output.exists()


def test_preparation_rejects_changed_body_identity(prepared_audit):
    run = prepared_audit
    run.articles[0]["content_hash"] = "0" * 64
    with pytest.raises(ValueError, match="identity or count mismatch"):
        run.audit.main()


def test_preparation_rejects_removed_zero_count_document(prepared_audit):
    run = prepared_audit
    del run.articles[34]
    with pytest.raises(ValueError, match="population changed"):
        run.audit.main()
    assert not run.output.exists()


def test_preparation_rejects_duplicate_offsets_even_with_correct_total(prepared_audit):
    run = prepared_audit
    run.events[1] = deepcopy(run.events[0])
    run.save_previous()
    with pytest.raises(ValueError):
        run.audit.main()


def test_preparation_rejects_input_identity_changed_since_previous_run(prepared_audit):
    run = prepared_audit
    run.source.write_text('{"version": 2}\n', encoding="utf-8")
    run.hashes[run.source.relative_to(run.root).as_posix()] = run.audit.digest(run.source)
    with pytest.raises(ValueError):
        run.audit.main()


def test_preparation_rejects_input_changed_during_run(prepared_audit, monkeypatch):
    run = prepared_audit
    write_json = run.audit.write_json

    def change_source_after_metrics(path, value):
        write_json(path, value)
        if path.name == "document-metrics.json":
            run.source.write_text("Changed during preparation.\n", encoding="utf-8")

    monkeypatch.setattr(run.audit, "write_json", change_source_after_metrics)
    with pytest.raises(ValueError, match="input changed"):
        run.audit.main()
    assert not (run.output / "manifest.json").exists()
