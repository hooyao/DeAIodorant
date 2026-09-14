import pytest

from deaiodorant.refine.records import literal_diagnostics, make_candidate, render_prompt, replay_operations


def test_prompt_content_is_not_recursively_interpreted():
    output = render_prompt("Input: {{input_text}}", {"input_text": "Keep {{secret}} literally."})
    assert output == "Input: Keep {{secret}} literally."
    with pytest.raises(ValueError, match="Missing prompt fields"):
        render_prompt("{{input_text}}", {})


def test_replay_uses_unicode_offsets_and_rejects_overlap_or_wrong_source():
    assert replay_operations("甲😀乙", [{"start_char": 1, "end_char": 2, "before": "😀", "after": "丙"}]) == "甲丙乙"
    with pytest.raises(ValueError, match="overlapping"):
        replay_operations("abc", [
            {"start_char": 0, "end_char": 2, "before": "ab", "after": "A"},
            {"start_char": 1, "end_char": 3, "before": "bc", "after": "B"},
        ])
    with pytest.raises(ValueError, match="match original"):
        replay_operations("abc", [{"start_char": 0, "end_char": 1, "before": "z", "after": "A"}])


def test_numeric_check_exposes_changes_but_never_certifies_semantics():
    check = literal_diagnostics("总量为１２台，不能超过20台。", "总量为12台，可以超过21台。", ["不能"])
    assert check["missing_numeric_occurrences"] == {"20": 1}
    assert check["added_numeric_occurrences"] == {"21": 1}
    assert check["missing_protected_literals"] == ["不能"]
    assert check["semantic_disposition"] == "unreviewed"
    units = literal_diagnostics("容量为8GB。", "容量为12GB。", [])
    assert units["missing_numeric_occurrences"] == {"8": 1}
    assert units["added_numeric_occurrences"] == {"12": 1}
    unchanged = literal_diagnostics("甲可能比乙快。", "甲肯定比乙快。", [])
    assert unchanged["missing_numeric_occurrences"] == {}
    assert unchanged["semantic_disposition"] == "unreviewed"


def test_unchanged_and_edited_candidates_remain_unreviewed():
    draft = {"draft_id": "d1", "task_group_id": "g1", "draft_text": "原文。"}
    unchanged = make_candidate(draft, "原文。", "unchanged")
    edited = make_candidate(draft, "修改文。", "compact_prompt")
    assert unchanged["operations"] == []
    assert replay_operations(draft["draft_text"], edited["operations"]) == "修改文。"
    assert edited["human_gold"] is False
    assert edited["eligibility_status"] == "awaiting_semantic_review"
