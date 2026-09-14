"""Protect source-evidence anchoring from plausible but mislocated quotations."""

import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture
def validation(monkeypatch):
    directory = Path(__file__).resolve().parents[1] / "experiments"
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location("context_review_validation_under_test", directory / "summarize_contrast_context_reviews.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_identical_quotes_resolve_to_the_assigned_occurrence(validation):
    text = "甲而是乙。甲而是乙。"
    assert validation.quote_spans(text, "甲而是乙", (6, 8)) == [{"start_char": 5, "end_char": 9}]
    assert len(validation.quote_spans(text, "甲而是乙")) == 2


def test_valid_quote_at_wrong_occurrence_is_rejected(validation):
    with pytest.raises(ValueError, match="required location"):
        validation.quote_spans("甲而是乙。丙而是丁。", "甲而是乙", (6, 8))


@pytest.mark.parametrize("quote", ["", None, "改写后的句子"])
def test_empty_or_rewritten_evidence_is_rejected(validation, quote):
    with pytest.raises(ValueError):
        validation.quote_spans("原始句子。", quote)


def test_duplicate_documents_cannot_count_as_full_coverage(validation):
    with pytest.raises(ValueError, match="Document coverage"):
        validation.validate_review({"reviewer": "test", "human_gold": False,
                                    "documents": [{"alias": "doc-01"}, {"alias": "doc-01"}]}, {"doc-01": {}})


def test_assistant_result_cannot_claim_human_gold(validation):
    with pytest.raises(ValueError, match="human gold"):
        validation.validate_review({"human_gold": True}, {})
