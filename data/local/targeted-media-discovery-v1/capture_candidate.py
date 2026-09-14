"""Capture one UI-discovered public article and check protected overlap first."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from experiments import stage_media_contrast_candidates as capture
from experiments.audit_media_staging_overlap import PRIOR_DATASETS
from deaiodorant.corpus.benchmark import ExclusionIndex

URL = "https://www.infoq.cn/article/rDTKqBrlGD5R93NFDOI8"
DOC_ID = capture.sha(URL)[:24]
OUTPUT = Path(__file__).resolve().parent / "baidu-supply"
assert not OUTPUT.exists(), "Capture already exists"
OUTPUT.mkdir()
exclusion_path = ROOT / "data/local/media-provenance-extension-v1/identity-exclusions.json"
exclusions = json.loads(exclusion_path.read_text(encoding="utf-8"))
assert URL not in exclusions["urls"] and DOC_ID not in exclusions["doc_ids"]
for name in ("media-contrast-staging-v1", "media-provenance-extension-v1"):
    for line in (ROOT / "data/local" / name / "article-attempts.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        assert row["url"] != URL and row["doc_id"] != DOC_ID
capture.write_json(OUTPUT / "selection.json", {
    "version": "targeted-media-discovery-1.0", "selected_url": URL, "doc_id": DOC_ID,
    "discovery": "One Google UI query and the visible domestic-company analysis result; identity checked before body inspection.",
    "query": 'site:infoq.cn/article "不是" "而是" "2025" "本质"',
    "selection_bias": "Keyword-enriched development discovery, not frequency replication or a representative sample.",
    "publication_date_basis": "Pending embedded article metadata, not query terms or search snippet.",
    "article_get_cap": 1, "backfill": False, "source_hash": capture.sha(Path(__file__).read_bytes()),
    "identity_exclusions_sha256": capture.sha(exclusion_path.read_bytes()),
    "translation_is_global_exclusion": False, "human_label": None,
})
client = capture.BoundedClient(OUTPUT)
robots_request = client.get(capture.ROBOTS, "robots.txt", 512 * 1024)
assert not client.stop_reason
robots = capture.robot_parser(OUTPUT, robots_request)
assert robots.can_fetch(capture.USER_AGENT, URL), "Article disallowed"
client.delay = capture.robot_delay(robots)
response = client.get(URL, "source.html", 8 * 1024 * 1024)
if client.stop_reason or response.get("status") != 200 or not response.get("complete_response"):
    capture.write_json(OUTPUT / "result.json", {"status": "capture_not_usable", "response": response})
    raise SystemExit("Public capture unavailable; no retry")
record = capture.extract_candidate(OUTPUT, {"url": URL, "doc_id": DOC_ID,
    "intended_cohort": "post", "sitemap_lastmod": None, "selection_rank": 1}, response, exclusions)
capture.write_json(OUTPUT / "capture-record.json", record)
body_path = OUTPUT / "documents" / DOC_ID / "body.txt"
body = body_path.read_bytes().decode("utf-8")
assert body.strip(), "Empty body"
index = ExclusionIndex(near_duplicate_threshold=0.9)
indexed_inputs = {}
for name in PRIOR_DATASETS:
    path = ROOT / name
    if not path.exists():
        continue
    before = capture.sha(path.read_bytes())
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        # Protected labels and outcomes never enter the index or any report.
        item = {key: raw.get(key) for key in ("doc_id", "url", "canonical_url", "text")}
        if isinstance(item["text"], str) and item["text"].strip():
            index.add(item)
    assert before == capture.sha(path.read_bytes())
    indexed_inputs[name] = before
for name in ("media-contrast-staging-v1", "media-provenance-extension-v1"):
    stage = ROOT / "data/local" / name
    for line in (stage / "article-attempts.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = stage / "documents" / row["doc_id"] / "body.txt"
        if not path.exists():
            continue
        text = path.read_bytes().decode("utf-8")
        if text.strip():
            assert capture.sha(text) == row["content_hash"]
            index.add({"doc_id": row["doc_id"], "url": row["url"], "text": text})
            indexed_inputs[path.relative_to(ROOT).as_posix()] = capture.sha(path.read_bytes())
match = index.match({"doc_id": DOC_ID, "url": URL, "text": body})
result = {"version": "targeted-media-discovery-1.0", "doc_id": DOC_ID,
    "source_sha256": capture.sha(body), "body_unicode_characters": len(body),
    "metadata": record.get("metadata"), "actual_cohort": record.get("actual_cohort"),
    "known_overlap": {"reason": match.reason, "existing_doc_id": match.existing_doc_id} if match else None,
    "inspection_allowed": match is None, "target_coverage": "unreviewed", "human_label": None,
    "indexed_inputs": indexed_inputs, "no_protected_labels_exposed": True,
    "output_hashes": {p.relative_to(OUTPUT).as_posix(): capture.sha(p.read_bytes())
                      for p in OUTPUT.rglob("*") if p.is_file()},
    "network_budget": "One robots GET and one article GET; no retries or media fetches",
    "command": "python data/local/targeted-media-discovery-v1/capture_candidate.py"}
capture.write_json(OUTPUT / "result.json", result)
print(json.dumps({"doc_id": DOC_ID, "inspection_allowed": result["inspection_allowed"],
                  "body_unicode_characters": len(body), "actual_cohort": record.get("actual_cohort")}))
