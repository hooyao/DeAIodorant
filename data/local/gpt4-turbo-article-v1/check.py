"""只读检查本次输入、原始输出与反馈关联；不调用 API。"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]

def read(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

request = read("request.json")
response = read("response.json")
feedback = read("reader-feedback-on-v1.json")
for linked in [request, feedback["reviewed_article"], feedback["source_article"]]:
    path_key = "source_path" if "source_path" in linked else "path"
    hash_key = "source_sha256" if "source_sha256" in linked else "sha256"
    assert digest(ROOT / linked[path_key]) == linked[hash_key]
assert digest(ROOT / feedback["reviewed_article"]["body_path"]) == feedback["reviewed_article"]["body_sha256"]
source = (ROOT / request["source_path"]).read_bytes().decode("utf-8")
assert request["messages"][0]["content"].endswith(source)
draft = (RUN / "rewritten-article.md").read_bytes().decode("utf-8")
assert draft == response["text"]
v1 = (ROOT / feedback["reviewed_article"]["path"]).read_text(encoding="utf-8")
spans = []
for quote in feedback["exact_source_spans_to_locate"]:
    assert v1.count(quote) == 1
    start = v1.index(quote)
    spans.append({"start_char": start, "end_char": start + len(quote), "quote": quote})
metadata = response["metadata"]
ledger = read("api-cache/ledger.json")
assert metadata["requested_model"] == metadata["returned_model"] == "openai/gpt-4-turbo"
assert metadata["attempt_count"] == 1 and metadata["finish_reason"] == "stop"
assert len(ledger["transactions"]) == 1
single_ledger = json.loads((ROOT / "data/local/gpt4-sentence-probe-v1/api-cache/ledger.json").read_text(encoding="utf-8"))
assert single_ledger["transactions"] == []
numbers = re.compile(r"\d+(?:[.~–-]\d+)*(?:[xX])?")
quotes = re.compile(r"“[^”]*”")
report = {
    "source_sha256": digest(ROOT / request["source_path"]),
    "output_sha256": digest(RUN / "rewritten-article.md"),
    "source_characters_including_markdown": len(source),
    "output_characters": len(draft),
    "character_ratio": len(draft) / len(source),
    "output_matches_unedited_response": True,
    "input_contains_complete_original": True,
    "feedback_source_spans": spans,
    "feedback_offsets_definition": "相对第一版 Markdown 经 universal newline 解码后的 Unicode 字符，从零开始，左闭右开。",
    "missing_numeric_occurrences": dict(Counter(numbers.findall(source)) - Counter(numbers.findall(draft))),
    "added_numeric_occurrences": dict(Counter(numbers.findall(draft)) - Counter(numbers.findall(source))),
    "missing_exact_quotations": list((Counter(quotes.findall(source)) - Counter(quotes.findall(draft))).elements()),
    "requested_stability_sentence_omitted": "2.7.x" not in draft and "不知道今年过年能不能玩到亡灵遗产稳定版" not in draft,
    "paid_attempt_count": 1,
    "single_sentence_paid_attempt_count": 0,
    "reported_cost_usd": metadata["cost"]["reported_usd"],
    "mechanical_identity_checks": "passed",
    "meaning_preservation": "不能依据这些机械检查通过；另见独立复核。",
    "reader_benefit": None,
    "training_eligible": False,
}
if "--record" in sys.argv:
    with (RUN / "mechanical-check.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
print(json.dumps({key: value for key, value in report.items() if key not in {
    "feedback_source_spans", "missing_exact_quotations", "missing_numeric_occurrences", "added_numeric_occurrences"
}}, ensure_ascii=False, indent=2))
