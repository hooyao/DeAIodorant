import json

from deaiodorant.corpus.pipeline import _collection_completeness


def test_collection_completeness_requires_each_available_source_time_cell(tmp_path):
    report = {
        "cells": {
            "infoq_pre": {"documents": 2},
            "infoq_post": {"documents": 1},
            "jiqizhixin_pre": {"documents": 2},
            "jiqizhixin_post": {"documents": 0},
        }
    }
    (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")

    result = _collection_completeness(tmp_path, target=2)

    assert result["valid"] is False
    assert result["document_counts"]["infoq_post"] == 1
    assert result["errors"] == [
        "infoq_post produced 1 documents; expected at least 2"
    ]
