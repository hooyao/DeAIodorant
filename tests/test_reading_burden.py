import json

import pytest

from deaiodorant.analysis.reading_burden import analyze_sentences


def analyze(text, **metadata):
    return analyze_sentences([{"sentence_id": "s1", "block_id": "b1", "block_tag": "p", "text": text, **metadata}])


def test_literal_count_does_not_count_negative_alternative_connectors():
    result = analyze("我们选甲而不是乙，选丙而非丁。这不是速度问题，而是成本问题。")
    cues = result["style_cues"]
    assert cues["literal_ershi"]["count"] == 1
    assert cues["negative_alternative_connectors"]["counts_by_literal"] == {"而不是": 1, "而非": 1}
    assert cues["counts_by_left_prefix"] == {"不是": 1}


def test_longest_prefix_wins_and_each_connector_has_one_family():
    result = analyze("这并不是甲，而是乙。这不再只是甲，而是乙。这并不认为甲合适，而是主张乙。")
    cues = result["style_cues"]
    assert cues["literal_ershi"]["count"] == 3
    assert cues["counts_by_left_prefix"] == {"并不是": 1, "不再只是": 1, "并不认为": 1}
    assert sum(cues["counts_by_family"].values()) == 3


def test_inline_newlines_and_quoted_source_remain_in_counting_scope():
    source = "作者引用：‘这并非\n甲，\n而是乙。’"
    result = analyze(source)
    event = result["style_cues"]["replacement_frame_instances"][0]
    assert event["left_prefix"]["text"] == "并非"
    assert event["pairing_status"] == "lexical_candidate"
    assert "\n" in event["pairing_window"]["text"]
    for key in ("left_prefix", "connector", "pairing_window"):
        span = event[key]
        assert source[span["start_char"]:span["end_char"]] == span["text"]


@pytest.mark.parametrize("boundary", list("。！？!?"))
def test_no_pairing_across_terminal_boundary(boundary):
    result = analyze(f"这不是甲{boundary}而是乙。")
    assert result["style_cues"]["counts_by_left_prefix"] == {"__unpaired__": 1}


def test_multiple_negatives_use_nearest_without_reusing_previous_connector():
    result = analyze("这不是甲，并非乙，而是丙，而是丁。")
    cues = result["style_cues"]
    assert cues["counts_by_left_prefix"] == {"并非": 1, "__unpaired__": 1}
    first, second = cues["replacement_frame_instances"]
    assert [item["text"] for item in first["preceding_prefix_candidates"]] == ["不是", "并非"]
    assert second["left_prefix"] is None
    assert second["pairing_window"]["start_char"] == first["connector"]["end_char"]


def test_negative_alternative_cannot_supply_a_prefix_to_next_replacement():
    result = analyze("使用甲而不是乙，而是丙。")
    assert result["style_cues"]["counts_by_left_prefix"] == {"__unpaired__": 1}


def test_heading_is_counted_but_identified_separately():
    result = analyze_sentences([
        {"text": "并非甲，而是乙", "block_tag": "h2", "sentence_id": "heading"},
        {"text": "不是甲，而是乙。", "block_tag": "p", "sentence_id": "body"},
    ])
    assert result["style_cues"]["literal_ershi"]["counts_by_context"] == {"heading": 1, "non_heading": 1}
    assert result["scope"]["input_record_count"] == 2


@pytest.mark.parametrize("text", ["请保存。", "今天星期一。", "系统启动并加载配置。", "服务恢复了。"])
def test_ellipsis_nominal_predicates_and_shared_subjects_get_no_error_claim(text):
    result = analyze(text)
    assert result["structural_proxies"]["status"] == "not_evaluated"
    assert result["reading_quality"] == {"status": "unknown", "score": None}


def test_empty_input_abstains_on_zero_denominator_and_is_json_serializable():
    result = analyze_sentences([])
    assert result["style_cues"]["literal_ershi"]["count"] == 0
    assert result["style_cues"]["literal_ershi"]["per_1000_cjk_characters"] is None
    assert result["style_cues"]["counts_by_family"] == {}
    json.dumps(result, ensure_ascii=False)


def test_invalid_record_fails_clearly():
    with pytest.raises(ValueError, match="string text"):
        analyze_sentences([{"text": None}])
