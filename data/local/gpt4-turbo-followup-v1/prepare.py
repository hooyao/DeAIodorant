"""回放三处局部补充，保存新稿、差异和原文定位；不访问网络。"""
import difflib
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
plan = json.loads((RUN / "edit-plan.json").read_text(encoding="utf-8"))
feedback = json.loads((RUN / "reader-feedback.json").read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert digest(ROOT / plan["base_path"]) == plan["base_sha256"]
assert digest(ROOT / plan["source_path"]) == plan["source_sha256"]
assert feedback["evaluated_text"]["sha256"] == plan["base_sha256"]
base = (ROOT / plan["base_path"]).read_bytes().decode("utf-8")
source = (ROOT / plan["source_path"]).read_bytes().decode("utf-8")
candidate = base
operations = []
for edit in plan["edits"]:
    assert candidate.count(edit["old"]) == 1
    spans = []
    for quote in edit["source_spans"]:
        assert source.count(quote) == 1
        start = source.index(quote)
        spans.append({"start_char": start, "end_char": start + len(quote), "quote": quote})
    operations.append({"id": edit["id"], "base_start_char": base.index(edit["old"]),
                       "old": edit["old"], "new": edit["new"], "source_spans": spans})
    candidate = candidate.replace(edit["old"], edit["new"], 1)
reversed_text = candidate
for edit in reversed(plan["edits"]):
    assert reversed_text.count(edit["new"]) == 1
    reversed_text = reversed_text.replace(edit["new"], edit["old"], 1)
assert reversed_text == base
paths = [RUN / name for name in ("partial-restoration.md", "changes.diff", "edit-record.json")]
if any(path.exists() for path in paths):
    raise SystemExit("输出已存在，不覆盖局部试稿。")
with paths[0].open("x", encoding="utf-8", newline="\n") as handle:
    handle.write(candidate)
with paths[1].open("x", encoding="utf-8", newline="\n") as handle:
    handle.write("".join(difflib.unified_diff(base.splitlines(keepends=True), candidate.splitlines(keepends=True), fromfile=plan["base_path"], tofile=paths[0].relative_to(ROOT).as_posix())))
record = {
    "source_sha256": plan["source_sha256"], "base_sha256": plan["base_sha256"],
    "plan_sha256": digest(RUN / "edit-plan.json"), "candidate_sha256": digest(paths[0]),
    "base_characters": len(base), "candidate_characters": len(candidate),
    "operations": operations, "reverse_replay_matches_base": True,
    "outside_three_edits_unchanged": True, "source_spans_match": True,
    "offset_definition": "源文件按原始 UTF-8 字节解码后的 Unicode 字符位置，零基，左闭右开。",
    "overall_content_preservation": "未通过；其余段落的已知遗漏或改变仍在。",
    "reader_benefit_for_this_new_draft": None, "training_eligible": False,
}
with paths[2].open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(record, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
assert digest(ROOT / plan["base_path"]) == plan["base_sha256"]
print(json.dumps({key: record[key] for key in ("base_characters", "candidate_characters", "candidate_sha256", "outside_three_edits_unchanged")}, ensure_ascii=False))
