"""Preserve v1 and revert the four non-passing interview substitutions."""

from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.records import replay_operations, text_hash, write_json

work = ROOT / "data/local/media-repair-development-v1"
old_dir = work / "candidates/doc-04"
output = work / "candidates-v2/doc-04"
assert not output.exists(), "Revision already exists"
record = json.loads((old_dir / "operations.json").read_text(encoding="utf-8"))
review_path = work / "preservation/review-long.json"
source = (ROOT / record["source_path"]).read_bytes().decode("utf-8")
old_text = (old_dir / "output.txt").read_bytes().decode("utf-8")
assert text_hash(source) == record["source_sha256"]
assert text_hash(old_text) == record["output_sha256"]
assert replay_operations(source, record["operations"]) == old_text
removed_ids = {f"doc-04-op-{i:03d}" for i in (8, 12, 34, 40)}
removed = [op for op in record["operations"] if op["operation_id"] in removed_ids]
assert len(removed) == 4
revision = deepcopy(record)
revision["operations"] = [op for op in record["operations"] if op["operation_id"] not in removed_ids]
text = replay_operations(source, revision["operations"])
revision.update({
    "candidate_id": record["candidate_id"] + "-preservation-v2",
    "parent_candidate_id": record["candidate_id"],
    "parent_output_sha256": record["output_sha256"],
    "parent_operations_sha256": text_hash((old_dir / "operations.json").read_bytes().decode("utf-8")),
    "review_sha256": text_hash(review_path.read_bytes().decode("utf-8")),
    "revision_author": "root-assistant-preservation-correction",
    "revision_reason": "Restore exact source at the failed extent/priority substitution and three uncertain interpretation/scope/addressee substitutions.",
    "removed_operation_ids": sorted(removed_ids),
    "output_sha256": text_hash(text), "output_char_count": len(text),
    "status": "awaiting_focused_revision_review", "human_gold": False,
    "human_acceptance": False, "training_eligible": False,
    "internal_validation": {"source_hash_matches": True, "full_replay_exact": True,
                            "unchanged_remaining_operations": True, "operation_count": len(revision["operations"])},
    "reproduction_command": "python data/local/media-repair-development-v1/create_interview_revision.py",
})
output.mkdir(parents=True)
(output / "output.txt").write_bytes(text.encode("utf-8"))
write_json(output / "operations.json", revision)
write_json(output / "revision-manifest.json", {"source_sha256": record["source_sha256"],
    "parent_output_sha256": record["output_sha256"], "output_sha256": text_hash(text),
    "operations_sha256": text_hash((output / "operations.json").read_bytes().decode("utf-8")),
    "implementation_sha256": text_hash(Path(__file__).read_bytes().decode("utf-8")),
    "reason": revision["revision_reason"], "human_gold": False})
print(json.dumps({"alias": "doc-04", "operations": len(revision["operations"]), "output_sha256": text_hash(text)}))
