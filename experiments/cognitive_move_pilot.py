"""Prepare and verify a frozen, source-linked discourse-move engineering pilot."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[1]
WORK = Path("data/local/cognitive-move-pilot-v1")
PROTOCOL = Path("docs/routes/compact-refiner/cognitive-move-pilot-v1.md")
PROMPT = Path("experiments/fixtures/cognitive_move_pilot_v1/annotation-instructions.md")
SMZDM = Path("data/local/reader-style-anchors-v1/smzdm")
BAIDU = Path("data/local/targeted-media-discovery-v1/baidu-supply/documents/92ade4253c08a43329164bf5")
CONDITIONS = ("original", "equivalent", "meaning_changed")
FIELDS = (
    "operation", "question_under_discussion", "prior_or_foil",
    "asserted_or_promised_content", "relation", "grounds_and_warrant",
    "information_update", "stance_and_presentation",
)


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"))


def write_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def load_documents(root: Path) -> tuple[dict, dict]:
    inputs = [SMZDM / name for name in ("metadata.json", "blocks.json", "analysis-body.txt")]
    inputs += [BAIDU / name for name in ("metadata.json", "blocks.json", "body.txt")]
    hashes = {path.as_posix(): digest((root / path).read_bytes()) for path in inputs}
    documents = {}
    for key, folder, text_key, body_file in (
        ("smzdm", SMZDM, "analysis_text", "analysis-body.txt"),
        ("baidu", BAIDU, "collector_text", "body.txt"),
    ):
        metadata = read_json(root / folder / "metadata.json")
        title = metadata["title"] if key == "smzdm" else metadata["metadata"]["title"]
        blocks = [{"block_id": block["block_id"], "text": block[text_key]}
                  for block in read_json(root / folder / "blocks.json")["blocks"]]
        body = (root / folder / body_file).read_bytes().decode("utf-8")
        if "\n".join(block["text"] for block in blocks) != body:
            raise ValueError("source_block_coverage_mismatch")
        documents[key] = {"blocks": [{"block_id": "title", "text": title}] + blocks}
    return documents, hashes


def modify_document(document: dict, edits: list, focus_blocks: list[str]) -> dict:
    result = copy.deepcopy(document)
    lookup = {block["block_id"]: block for block in result["blocks"]}
    if not focus_blocks or not set(focus_blocks) <= lookup.keys():
        raise ValueError("invalid_focus_blocks")
    for edit in edits:
        block_id, old, new = edit["block_id"], edit["old"], edit["new"]
        if block_id not in focus_blocks:
            raise ValueError("edit_outside_focus")
        if not old or old == new or not isinstance(new, str):
            raise ValueError("invalid_edit")
        if lookup[block_id]["text"].count(old) != 1:
            raise ValueError("edit_source_not_unique")
        lookup[block_id]["text"] = lookup[block_id]["text"].replace(old, new, 1)
    return result


def make_packets(design: dict, documents: dict, seed: int) -> tuple[dict, dict, dict]:
    cases = design["cases"]
    if [case["id"] for case in cases] != [f"M{i:02d}" for i in range(1, 7)]:
        raise ValueError("six_fixed_cases_required")
    rng = random.Random(seed)
    identifiers = rng.sample(range(0x10000000, 0xFFFFFFFF), 18)
    packets, key, by_case = {}, {}, {}
    for case in cases:
        by_case[case["id"]] = {}
        for condition in CONDITIONS:
            edits = [] if condition == "original" else case[
                "equivalent_edits" if condition == "equivalent" else "changed_edits"]
            if condition != "original" and not edits:
                raise ValueError("missing_probe_edit")
            document = modify_document(documents[case["document"]], edits, case["focus_blocks"])
            packet_id = f"p{identifiers.pop():08x}"
            # Only these fields are allowed to cross the annotation boundary.
            packets[packet_id] = {
                "version": "cognitive-move-blind-packet-1.0", "packet_id": packet_id,
                "focus_blocks": case["focus_blocks"], "document": document,
            }
            key[packet_id] = {"case_id": case["id"], "condition": condition,
                              "document": case["document"], "edits": edits}
            by_case[case["id"]][condition] = packet_id
    assignments = {}
    for replicate in ("a", "b"):
        for batch in range(3):
            ids = [by_case[case["id"]][CONDITIONS[(i + batch) % 3]]
                   for i, case in enumerate(cases)]
            rng.shuffle(ids)
            assignments[f"{replicate}{batch + 1}"] = ids
    return packets, key, assignments


def prepare(root: Path, design_path: Path, output: Path, seed: int) -> dict:
    output.relative_to(root)
    if output.exists():
        raise ValueError("output_already_exists")
    design = read_json(design_path)
    if design.get("status") != "reviewed_by_root":
        raise ValueError("design_not_reviewed")
    documents, source_hashes = load_documents(root)
    packets, key, assignments = make_packets(design, documents, seed)
    protocol_bytes = (root / PROTOCOL).read_bytes()
    prompt_bytes = (root / PROMPT).read_bytes()
    generator = Path("experiments/cognitive_move_pilot.py")
    generator_bytes = (root / generator).read_bytes()
    # Complete validation and construction before creating the output directory.
    output.mkdir(parents=True)
    write_new(output / "design.json", design)
    write_new(output / "key.json", key)
    for packet_id, packet in packets.items():
        write_new(output / "packets" / f"{packet_id}.json", packet)
    for session, packet_ids in assignments.items():
        write_new(output / "assignments" / f"{session}.json", {
            "session_id": session, "packet_ids": packet_ids,
            "prompt_path": PROMPT.as_posix(),
            "packet_directory": (output / "packets").relative_to(root).as_posix(),
        })
    files = {path.relative_to(output).as_posix(): digest(path.read_bytes())
             for path in sorted(output.rglob("*.json"))}
    manifest = {
        "version": "cognitive-move-pilot-freeze-1.0",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "seed": seed,
        "source_files": source_hashes,
        "protocol": {"path": PROTOCOL.as_posix(), "sha256": digest(protocol_bytes)},
        "prompt": {"path": PROMPT.as_posix(), "sha256": digest(prompt_bytes)},
        "generator": {"path": generator.as_posix(), "sha256": digest(generator_bytes)},
        "python_version": sys.version,
        "files": files, "packets": 18, "sessions": 6, "expected_annotations": 36,
        "unique_source_articles": 2, "independent_human_labels": False,
        "allocation": "two_replicates_of_cyclic_three_condition_assignment",
        "blinding_limit": "One version per focal case per session; other focal cases share full source articles, allowing contextual carryover. Same-model tasks are not independent human raters.",
    }
    write_new(output / "freeze.json", manifest)
    return manifest


def validate_record(record: dict, packet: dict) -> int:
    if record.get("packet_id") != packet["packet_id"] or record.get("full_context_read") is not True:
        raise ValueError("record_identity_or_context_mismatch")
    if not all(isinstance(record.get(field), (dict, list, str)) and record[field] for field in FIELDS):
        raise ValueError("missing_semantic_field")
    if not record.get("focal_spans"):
        raise ValueError("missing_focal_spans")
    lookup = {block["block_id"]: block["text"] for block in packet["document"]["blocks"]}
    for span in record["focal_spans"]:
        if span["block_id"] not in packet["focus_blocks"]:
            raise ValueError("focal_span_outside_assigned_focus")
    count = 0

    def visit(value):
        nonlocal count
        if isinstance(value, dict):
            if {"block_id", "quote"} <= value.keys():
                block_id, quote = value["block_id"], value["quote"]
                if block_id not in lookup or not isinstance(quote, str) or not quote or quote not in lookup[block_id]:
                    raise ValueError("annotation_quote_mismatch")
                count += 1
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(record)
    return count


def verify(root: Path, run: Path) -> dict:
    manifest = read_json(run / "freeze.json")
    for relative, expected in manifest["source_files"].items():
        if digest((root / relative).read_bytes()) != expected:
            raise ValueError("frozen_source_changed")
    for kind in ("protocol", "prompt", "generator"):
        item = manifest[kind]
        if digest((root / item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("frozen_instructions_changed")
    for relative, expected in manifest["files"].items():
        if digest((run / relative).read_bytes()) != expected:
            raise ValueError("frozen_run_file_changed")
    count = quotes = 0
    completed = []
    response_hashes = {}
    for assignment_path in sorted((run / "assignments").glob("*.json")):
        assignment = read_json(assignment_path)
        response_path = run / "responses" / assignment_path.name
        if not response_path.exists():
            continue
        response = read_json(response_path)
        records = response["records"]
        if response.get("session_id") != assignment["session_id"] or [r["packet_id"] for r in records] != assignment["packet_ids"]:
            raise ValueError("assignment_response_mismatch")
        for record in records:
            packet = read_json(run / "packets" / f"{record['packet_id']}.json")
            quotes += validate_record(record, packet)
        completed.append(assignment["session_id"])
        response_hashes[response_path.relative_to(run).as_posix()] = digest(response_path.read_bytes())
        count += len(records)
    return {"frozen_inputs": "passed", "completed_sessions": completed,
            "annotations": count, "quote_occurrences": quotes,
            "response_hashes": response_hashes, "semantic_validity": "requires_source_review",
            "complete": count == manifest["expected_annotations"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="准备或只读核验篇章动作工程实验；不调用模型。")
    subparsers = parser.add_subparsers(dest="command", required=True)
    builder = subparsers.add_parser("prepare")
    builder.add_argument("--design", type=Path, required=True)
    builder.add_argument("--output", type=Path, required=True)
    builder.add_argument("--seed", type=int, default=20260914)
    checker = subparsers.add_parser("verify")
    checker.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(ROOT, args.design.resolve(), args.output.resolve(), args.seed)
        result = {key: result[key] for key in ("frozen_at_utc", "packets", "sessions", "expected_annotations")}
    else:
        result = verify(ROOT, args.run.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
