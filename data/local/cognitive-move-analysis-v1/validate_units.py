"""Validate source linkage of worked discourse annotations, not their semantics."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).resolve().parent
smzdm = ROOT / "data/local/reader-style-anchors-v1/smzdm"
baidu = ROOT / "data/local/targeted-media-discovery-v1/baidu-supply/documents/92ade4253c08a43329164bf5"
paths = {"smzdm_analysis_body": smzdm / "analysis-body.txt", "baidu_body": baidu / "body.txt"}
texts = {key: path.read_bytes().decode("utf-8") for key, path in paths.items()}
texts["smzdm_title"] = json.loads((smzdm / "metadata.json").read_text(encoding="utf-8"))["title"]
blocks = {"smzdm_title": {"title": (0, len(texts["smzdm_title"]))}}
blocks["smzdm_analysis_body"] = {b["block_id"]: (b["analysis_start_char"], b["analysis_end_char"])
    for b in json.loads((smzdm / "blocks.json").read_text(encoding="utf-8"))["blocks"]}
blocks["baidu_body"] = {}
cursor = 0
for block in json.loads((baidu / "blocks.json").read_text(encoding="utf-8"))["blocks"]:
    end = cursor + len(block["collector_text"])
    assert texts["baidu_body"][cursor:end] == block["collector_text"]
    blocks["baidu_body"][block["block_id"]] = (cursor, end)
    cursor = end + 1
record_path = WORK / "units.json"
raw = json.loads(record_path.read_text(encoding="utf-8"))
units = raw["units"]
assert [unit["id"] for unit in units] == [f"M{i:02d}" for i in range(1, 7)]
fields = ("operation", "question_under_discussion", "prior_or_foil", "asserted_or_promised_content",
          "relation", "grounds_and_warrant", "information_update", "stance_and_presentation")
evidence_count = 0


def inspect(value):
    global evidence_count
    if isinstance(value, dict):
        if {"view", "block_id", "start_char", "end_char", "quote"} <= value.keys():
            view = value["view"]
            start, end = value["start_char"], value["end_char"]
            assert type(start) is int and type(end) is int and 0 <= start < end <= len(texts[view])
            assert texts[view][start:end] == value["quote"]
            left, right = blocks[view][value["block_id"]]
            assert left <= start < end <= right
            evidence_count += 1
        for child in value.values():
            inspect(child)
    elif isinstance(value, list):
        for child in value:
            inspect(child)


for unit in units:
    assert all(field in unit for field in fields)
    assert unit["source_spans"]
    assert unit["question_under_discussion"]["provenance"] in {"explicit", "analyst_reconstruction", "unknown"}
    inspect(unit)
result = {"version": "cognitive-move-linkage-validation-1.0", "units": len(units),
    "evidence_spans": evidence_count,
    "unit_file_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
    "view_sha256": {view: hashlib.sha256(text.encode("utf-8")).hexdigest() for view, text in texts.items()},
    "protocol_sha256": hashlib.sha256((ROOT / "docs/routes/compact-refiner/cognitive-move-analysis.md").read_bytes()).hexdigest(),
    "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "coverage_and_source_linkage": "passed", "semantic_validity": "not_established_by_this_check",
    "human_unit_labels": False, "quality_score": None,
    "command": "python data/local/cognitive-move-analysis-v1/validate_units.py"}
path = WORK / "validation.json"
assert not path.exists(), "Validation record already exists"
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"units": len(units), "exact_evidence_spans": evidence_count,
                  "semantic_validity": result["semantic_validity"]}))
