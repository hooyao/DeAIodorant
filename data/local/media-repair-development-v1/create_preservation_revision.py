"""Retain v1 and revert its sole uncertain same-problem scope replacement."""

from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.records import replay_operations, text_hash, write_json

work = ROOT / "data/local/media-repair-development-v1"
old_dir = work / "candidates/doc-03"
output = work / "candidates-v2/doc-03"
assert not output.exists(), "Revision already exists"
record = json.loads((old_dir / "operations.json").read_text(encoding="utf-8"))
review_path = work / "preservation/review-short.json"
source = (ROOT / record["source_path"]).read_bytes().decode("utf-8")
old_text = (old_dir / "output.txt").read_bytes().decode("utf-8")
assert text_hash(source) == record["source_sha256"]
assert text_hash(old_text) == record["output_sha256"]
assert replay_operations(source, record["operations"]) == old_text
removed = [op for op in record["operations"] if op["operation_id"] == "doc-03-op-005"]
assert len(removed) == 1 and removed[0]["before"] == "不同 agent 可能能解决一样的问题"
revision = deepcopy(record)
revision["operations"] = [op for op in record["operations"] if op["operation_id"] != "doc-03-op-005"]
text = replay_operations(source, revision["operations"])
revision.update({
    "candidate_id": record["candidate_id"] + "-preservation-v2",
    "parent_candidate_id": record["candidate_id"],
    "parent_output_sha256": record["output_sha256"],
    "parent_operations_sha256": text_hash((old_dir / "operations.json").read_bytes().decode("utf-8")),
    "review_sha256": text_hash(review_path.read_bytes().decode("utf-8")),
    "revision_author": "root-assistant-preservation-correction",
    "revision_reason": "Revert the uncertain same-problem to same-class substitution; all other operations unchanged.",
    "removed_operation_ids": ["doc-03-op-005"],
    "output_sha256": text_hash(text), "output_char_count": len(text),
    "status": "awaiting_focused_revision_review", "human_gold": False,
    "human_acceptance": False, "training_eligible": False,
    "internal_validation": {"source_hash_matches": True, "full_replay_exact": True,
                            "unchanged_remaining_operations": True, "operation_count": len(revision["operations"])},
    "reproduction_command": "python data/local/media-repair-development-v1/create_preservation_revision.py",
})
output.mkdir(parents=True)
(output / "output.txt").write_bytes(text.encode("utf-8"))
write_json(output / "operations.json", revision)
write_json(output / "revision-manifest.json", {"source_sha256": record["source_sha256"],
    "parent_output_sha256": record["output_sha256"], "output_sha256": text_hash(text),
    "operations_sha256": text_hash((output / "operations.json").read_bytes().decode("utf-8")),
    "implementation_sha256": text_hash(Path(__file__).read_bytes().decode("utf-8")),
    "reason": revision["revision_reason"], "human_gold": False})
print(json.dumps({"alias": "doc-03", "operations": len(revision["operations"]), "output_sha256": text_hash(text)}))
