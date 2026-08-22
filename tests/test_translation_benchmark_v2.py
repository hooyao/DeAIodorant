import csv
import json

from deaiodorant.corpus.benchmark import ExclusionIndex, balanced_take
from deaiodorant.corpus.label_studio_review import (
    label_studio_export_to_review_csv,
    prepare_label_studio_workspace,
)
from deaiodorant.corpus.review_triage import (
    agreed_high_confidence_status,
    apply_foreign_source_safeguard,
)
from deaiodorant.corpus.value_triage import agreed_research_value_status
from translation_benchmark_v2 import lctt_metadata, markdown_to_text


def record(doc_id, url, text, source="example"):
    return {"doc_id": doc_id, "url": url, "text": text, "source": source}


def test_exclusion_index_rejects_exact_and_near_duplicates():
    index = ExclusionIndex()
    original = record(
        "a",
        "https://example.com/a",
        "这是一个包含大量稳定正文内容的中文技术文章。" * 40,
    )
    index.add(original)

    exact = record("b", "https://example.com/b", original["text"])
    near = record(
        "c",
        "https://example.com/c",
        original["text"] + "末尾增加一条编辑说明。",
    )

    assert index.match(exact).reason == "exact_content"
    assert index.match(near).reason == "near_duplicate"


def test_balanced_take_round_robins_sources():
    records = [
        record(f"a{index}", f"https://a/{index}", f"正文甲{index}", source="a")
        for index in range(4)
    ] + [
        record(f"b{index}", f"https://b/{index}", f"正文乙{index}", source="b")
        for index in range(4)
    ]

    selected, remaining = balanced_take(records, 4, seed="test")

    assert {item["source"] for item in selected} == {"a", "b"}
    assert sum(item["source"] == "a" for item in selected) == 2
    assert len(remaining) == 4


def test_lctt_metadata_and_markdown_body_are_extracted():
    markdown = """[#]: subject: "A translated article"
[#]: via: "https://example.com/original"
[#]: author: "Foreign Author"
[#]: translator: "Translator"
[#]: reviewer: "Reviewer"

中文标题
======

这是翻译后的中文正文。[链接文字](https://example.com/link)

![image][0]

[0]: https://example.com/image.png
"""

    metadata = lctt_metadata(markdown)
    body = markdown_to_text(markdown)

    assert metadata["translator"] == "Translator"
    assert metadata["via"] == "https://example.com/original"
    assert "这是翻译后的中文正文。链接文字" in body
    assert "example.com/image" not in body


def test_label_studio_workspace_materializes_only_pending_originals(tmp_path):
    candidate_path = tmp_path / "example_candidates.jsonl"
    candidates = [
        {
            "doc_id": "pending-1",
            "source": "example",
            "published_at": "2026-01-02",
            "title": "待复核文章",
            "url": "https://example.com/pending",
            "candidate_label": "original_pending_review",
            "label_evidence": ["original_candidate_signal"],
            "cjk_chars": 10,
            "text": "保留原始正文。\n\n第二段。",
        },
        {
            "doc_id": "translation-1",
            "source": "example",
            "published_at": "2026-01-03",
            "title": "Deterministic translation",
            "url": "https://example.com/translation",
            "candidate_label": "translation",
            "label_evidence": ["explicit_translator_field"],
            "cjk_chars": 0,
            "text": "This body does not need manual review.",
        },
    ]
    candidate_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in candidates),
        encoding="utf-8",
    )

    workspace = tmp_path / "review"
    manifest = prepare_label_studio_workspace(
        [candidate_path], workspace, reviewer="reviewer", port=8081
    )

    assert manifest["documents"] == 1
    assert manifest["service"]["binding"] == "127.0.0.1"
    assert (workspace / "texts/example/pending-1.txt").read_text(
        encoding="utf-8"
    ) == candidates[0]["text"]
    assert not (workspace / "texts/example/translation-1.txt").exists()
    tasks = json.loads((workspace / "label_studio_tasks.json").read_text("utf-8"))
    assert [task["data"]["doc_id"] for task in tasks] == ["pending-1"]
    assert "待复核文章" in tasks[0]["data"]["title"]
    assert (workspace / "OPEN_ME_credentials.txt").exists()


def test_label_studio_export_converts_review_decisions(tmp_path):
    tasks = [
        {
            "data": {
                "doc_id": "accepted-1",
                "source": "example",
                "published_at": "2026-01-02",
                "title": "Accepted article",
                "url": "https://example.com/accepted",
                "candidate_label": "original_pending_review",
                "label_evidence": ["original_candidate_signal"],
                "cjk_chars": 100,
            },
            "annotations": [
                {
                    "created_at": "2026-08-21T01:02:03Z",
                    "updated_at": "2026-08-21T01:04:05Z",
                    "result": [
                        {
                            "from_name": "decision",
                            "value": {"choices": ["Reviewed original"]},
                        },
                        {
                            "from_name": "original_rationale",
                            "value": {"choices": ["Original reporting or interview"]},
                        },
                        {
                            "from_name": "review_notes",
                            "value": {"text": ["Interview quotations checked."]},
                        },
                    ],
                }
            ],
        },
        {
            "data": {
                "doc_id": "unreviewed-1",
                "source": "example",
                "published_at": "2026-01-03",
                "title": "Unreviewed article",
                "url": "https://example.com/unreviewed",
                "candidate_label": "original_pending_review",
                "label_evidence": [],
                "cjk_chars": 100,
            },
            "annotations": [],
        },
    ]
    output = tmp_path / "review.csv"

    summary = label_studio_export_to_review_csv(
        tasks, output, reviewer="human-reviewer"
    )

    assert summary == {
        "documents": 2,
        "accepted": 1,
        "excluded": 0,
        "unreviewed": 1,
    }
    with output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["review_include"] == "yes"
    assert rows[0]["review_gold_label"] == "original"
    assert rows[0]["reviewer"] == "human-reviewer"
    assert "Interview quotations checked." in rows[0]["review_notes"]
    assert rows[1]["review_include"] == ""


def test_model_triage_requires_matching_high_confidence_results():
    original = {"label": "original", "confidence": "high", "evidence": ["采访"]}
    compiled = {
        "label": "translated_or_compiled",
        "confidence": "high",
        "evidence": ["单一外媒来源"],
    }

    assert agreed_high_confidence_status(original, original) == "model_assisted_original"
    assert (
        agreed_high_confidence_status(compiled, compiled)
        == "model_assisted_exclusion"
    )
    assert agreed_high_confidence_status(original, compiled) == "uncertain"
    assert (
        agreed_high_confidence_status(
            original, {**original, "confidence": "medium"}
        )
        == "uncertain"
    )
    assert agreed_high_confidence_status(original, None) == "uncertain"
    assert (
        apply_foreign_source_safeguard("model_assisted_original", original)
        == "model_assisted_original"
    )
    assert (
        apply_foreign_source_safeguard("model_assisted_exclusion", compiled)
        == "model_assisted_exclusion"
    )
    assert (
        apply_foreign_source_safeguard("model_assisted_exclusion", original)
        == "model_assisted_original"
    )


def test_value_triage_requires_matching_high_confidence_results():
    substantive = {
        "label": "substantive",
        "confidence": "high",
        "evidence": ["architecture details"],
    }
    low_value = {
        "label": "low_value",
        "confidence": "high",
        "evidence": ["registration promotion"],
    }

    assert (
        agreed_research_value_status(substantive, substantive)
        == "model_assisted_substantive"
    )
    assert (
        agreed_research_value_status(low_value, low_value)
        == "model_assisted_low_value"
    )
    assert agreed_research_value_status(substantive, low_value) == "value_uncertain"
