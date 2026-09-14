"""Ensure a reading comparison cannot credit extraction whitespace repair."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def renderer():
    path = Path(__file__).resolve().parents[1] / "experiments/render_media_repair_review.py"
    spec = importlib.util.spec_from_file_location("media_repair_presentation_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_whitespace_only_candidate_cannot_make_original_look_fragmented(renderer):
    raw = "甲\nAgent\n乙。"
    presentation = "甲Agent 乙。"
    operation = {"operation_id": "layout", "start_char": 0, "end_char": len(raw),
                 "before": raw, "after": "甲Agent乙。"}
    assert renderer.project_block(raw, presentation, [operation]) == (presentation, ["layout"])


def test_semantic_change_projects_after_inline_separator_without_losing_context(renderer):
    raw = "前文\nAgent\n，后文错了。"
    presentation = "前文Agent，后文错了。"
    start = raw.index("错了")
    operation = {"operation_id": "repair", "start_char": start, "end_char": start + 2,
                 "before": "错了", "after": "改好了"}
    assert renderer.project_block(raw, presentation, [operation]) == ("前文Agent，后文改好了。", [])


def test_presentation_cannot_silently_correct_source_words(renderer):
    with pytest.raises(ValueError, match="non-whitespace"):
        renderer.project_block("原始文本", "改过的文本", [])
