"""冻结文章隔离标注输入，并只读检查首次回答的结构与原文引文。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[1]
SEED = 20260915
PROTOCOL = Path("docs/routes/compact-refiner/cognitive-move-contract-probe-v1.1.md")
CONTRACT = Path("docs/routes/compact-refiner/cognitive-move-record-contract-v1.1.md")
PROMPT = Path("experiments/fixtures/cognitive_move_contract_v11/annotation-instructions.md")
GENERATOR = Path("experiments/cognitive_move_contract_probe.py")
FIELDS = (
    "operation", "question_under_discussion", "prior_or_foil",
    "asserted_or_promised_content", "relation", "grounds_and_warrant",
    "information_update", "stance_and_presentation",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"))


def write_new(path: Path, value) -> None:
    """独占创建，保留已有输入和首次输出。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def source_document(folder: Path) -> dict:
    """检查提取覆盖与正文身份；不判断正文中的主张。"""
    metadata = read_json(folder / "metadata.json")
    for field in ("title", "published_at", "author", "body_sha256", "full_text_status"):
        if field not in metadata:
            raise ValueError(f"source_metadata_missing:{field}")
    if not isinstance(metadata["title"], str) or not metadata["title"]:
        raise ValueError("invalid_source_title")
    if metadata["author"] is not None and not isinstance(metadata["author"], str):
        raise ValueError("invalid_source_author")
    body_bytes = (folder / "body.txt").read_bytes()
    if digest(body_bytes) != metadata["body_sha256"]:
        raise ValueError("source_body_hash_mismatch")
    body = body_bytes.decode("utf-8")
    blocks = read_json(folder / "blocks.json")
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("source_blocks_required")
    identifiers, previous_end = set(), 0
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError("invalid_source_block")
        block_id, text = block.get("block_id"), block.get("text")
        start, end = block.get("start_char"), block.get("end_char")
        if not isinstance(block_id, str) or not block_id or block_id == "title" or block_id in identifiers:
            raise ValueError("invalid_source_block_id")
        if not isinstance(text, str) or not text:
            raise ValueError("invalid_source_block_text")
        if type(start) is not int or type(end) is not int or not previous_end <= start < end <= len(body):
            raise ValueError("invalid_source_block_bounds")
        if body[start:end] != text or body[previous_end:start].strip():
            raise ValueError("source_block_coverage_mismatch")
        identifiers.add(block_id)
        previous_end = end
    if body[previous_end:].strip():
        raise ValueError("source_block_coverage_mismatch")
    packet_metadata = {key: metadata[key] for key in (
        "title", "published_at", "author", "body_sha256", "full_text_status")}
    for key in ("completeness_scope", "media_references", "citation_records"):
        if key in metadata:
            packet_metadata[key] = metadata[key]
    return {
        "metadata": packet_metadata,
        "blocks": [{"block_id": "title", "text": metadata["title"]}] + blocks,
    }


def prepare(root: Path, run: Path) -> dict:
    """从固定四篇选择建立八项单文章任务；不调用模型或网络。"""
    root, run = root.resolve(), run.resolve()
    run.relative_to(root)
    frozen = run / "frozen"
    if frozen.exists() or (run / "responses").exists():
        raise ValueError("output_already_exists")
    selection_path = run / "selections.json"
    selections = read_json(selection_path)
    articles = selections.get("articles")
    if not isinstance(articles, list) or len(articles) != 4:
        raise ValueError("four_fixed_articles_required")
    ids = [item.get("id") if isinstance(item, dict) else None for item in articles]
    if any(not isinstance(item, str) or not item or Path(item).name != item or item in (".", "..")
           or "/" in item or "\\" in item for item in ids) or len(set(ids)) != 4:
        raise ValueError("invalid_selected_document_ids")

    sources = {selection_path.relative_to(root).as_posix(): digest(selection_path.read_bytes())}
    documents, excluded = {}, []
    for doc_id in ids:
        folder = run / "documents" / doc_id
        metadata = read_json(folder / "metadata.json")
        for name in ("metadata.json", "body.txt", "blocks.json"):
            path = folder / name
            if path.exists():
                sources[path.relative_to(root).as_posix()] = digest(path.read_bytes())
        if metadata.get("full_text_status") != "complete":
            excluded.append({"document_id": doc_id, "full_text_status": metadata.get("full_text_status"),
                             "reason": "full_text_not_complete"})
            continue
        documents[doc_id] = source_document(folder)

    instruction_sources = {
        "protocol.md": PROTOCOL, "record-contract.md": CONTRACT,
        "annotation-instructions.md": PROMPT, "generator.py": GENERATOR,
    }
    instruction_bytes = {name: (root / path).read_bytes() for name, path in instruction_sources.items()}
    sources.update({path.as_posix(): digest(instruction_bytes[name])
                    for name, path in instruction_sources.items()})
    rng = random.Random(SEED)
    opaque_ids = rng.sample(range(0x100000000000, 0xFFFFFFFFFFFF), len(documents) * 3)
    packets, key, assignments = {}, {}, {}
    for doc_id, document in documents.items():
        packet_id = f"p{opaque_ids.pop():012x}"
        packets[packet_id] = {"version": "cognitive-move-contract-packet-1.1", "packet_id": packet_id,
                              "document": document}
        key[packet_id] = {"document_id": doc_id}
        for replicate in ("a", "b"):
            assignment_id = f"a{opaque_ids.pop():012x}"
            assignments[assignment_id] = {
                "version": "cognitive-move-contract-assignment-1.1", "assignment_id": assignment_id,
                "packet_id": packet_id, "packet_path": f"packets/{packet_id}.json",
                "instructions_path": "annotation-instructions.md",
                "response_path": f"../responses/{assignment_id}.json",
            }
            key[packet_id][f"assignment_{replicate}"] = assignment_id

    frozen.mkdir(parents=True)
    for name, data in instruction_bytes.items():
        with (frozen / name).open("xb") as stream:
            stream.write(data)
    write_new(frozen / "key.json", {"packets": key, "excluded": excluded})
    for packet_id, packet in packets.items():
        write_new(frozen / "packets" / f"{packet_id}.json", packet)
    for assignment_id, assignment in assignments.items():
        write_new(frozen / "assignments" / f"{assignment_id}.json", assignment)
    files = {path.relative_to(frozen).as_posix(): digest(path.read_bytes())
             for path in sorted(frozen.rglob("*")) if path.is_file()}
    manifest = {
        "version": "cognitive-move-contract-freeze-1.1", "seed": SEED,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "python_version": sys.version,
        "source_files": sources, "files": files, "selected_articles": len(ids),
        "readable_articles": len(documents), "expected_responses": len(assignments),
        "assignment_ids": sorted(assignments), "maximum_records_per_response": 4,
        "isolation": "one_article_per_assignment; shared_filesystem_not_enforced; root_exposure_audit_required",
        "semantic_validity": "requires_source_review",
    }
    write_new(frozen / "freeze.json", manifest)
    return manifest


def validate_response(response, packet: dict, assignment: dict) -> dict:
    """累计机械错误；空 foil 不失败，引文正确不代表语义正确。"""
    errors, quote_count = [], 0
    lookup = {block["block_id"]: block["text"] for block in packet["document"]["blocks"]}

    def fail(path, code):
        errors.append({"path": path, "code": code})

    def obj(value, path):
        if not isinstance(value, dict):
            fail(path, "expected_object")
            return {}
        return value

    def sequence(value, path, nonempty=False):
        if not isinstance(value, list):
            fail(path, "expected_list")
            return []
        if nonempty and not value:
            fail(path, "empty_list")
        return value

    def string(value, path, nullable=False):
        if value is None and nullable:
            return True
        if not isinstance(value, str) or not value.strip():
            fail(path, "expected_nonempty_string")
            return False
        return True

    def strings(value, path, nonempty=False):
        items = sequence(value, path, nonempty)
        for index, item in enumerate(items):
            string(item, f"{path}[{index}]")
        return items

    def span(value, path, allowed=None):
        nonlocal quote_count
        value = obj(value, path)
        block_id, quote = value.get("block_id"), value.get("quote")
        if not isinstance(block_id, str) or block_id not in lookup:
            fail(path, "unknown_source_block")
        elif not isinstance(quote, str) or not quote or quote not in lookup[block_id]:
            fail(path, "annotation_quote_mismatch")
        else:
            quote_count += 1
        if allowed is not None and (not isinstance(block_id, str) or block_id not in allowed):
            fail(path, "focal_span_outside_mapped_move")

    def spans(value, path, nonempty=False, allowed=None):
        for index, item in enumerate(sequence(value, path, nonempty)):
            span(item, f"{path}[{index}]", allowed)

    response = obj(response, "response")
    for field in ("assignment_id", "packet_id"):
        if response.get(field) != assignment.get(field):
            fail(field, "response_identity_mismatch")
    identity = obj(response.get("identity"), "identity")
    for field in ("agent_task", "model"):
        string(identity.get(field), f"identity.{field}")
    for field in ("full_article_read", "other_outputs_seen"):
        if type(identity.get(field)) is not bool:
            fail(f"identity.{field}", "expected_boolean")
    for field in ("read_paths", "inherited_guidance", "procedure_violations"):
        strings(identity.get(field), f"identity.{field}")

    move_map = {}
    for index, item in enumerate(sequence(response.get("article_map"), "article_map")):
        path = f"article_map[{index}]"
        item = obj(item, path)
        move_id = item.get("move_id")
        valid_id = string(move_id, f"{path}.move_id")
        block_ids = strings(item.get("block_ids"), f"{path}.block_ids", True)
        allowed = {block_id for block_id in block_ids if isinstance(block_id, str)}
        if not allowed <= lookup.keys():
            fail(f"{path}.block_ids", "unknown_source_block")
        strings(item.get("operation"), f"{path}.operation", True)
        string(item.get("description"), f"{path}.description")
        if "recurrence_group" not in item:
            fail(f"{path}.recurrence_group", "missing_field")
        else:
            string(item["recurrence_group"], f"{path}.recurrence_group", True)
        if valid_id:
            if move_id in move_map:
                fail(f"{path}.move_id", "duplicate_move_id")
            else:
                move_map[move_id] = allowed

    records = sequence(response.get("records"), "records")
    if len(records) > 4:
        fail("records", "record_limit_exceeded")
    omitted = strings(response.get("omitted_opportunities"), "omitted_opportunities")
    if not records and not omitted:
        fail("omitted_opportunities", "empty_records_require_coverage_explanation")
    detailed_moves = set()
    for index, record in enumerate(records):
        path = f"records[{index}]"
        record = obj(record, path)
        move_id = record.get("move_id")
        valid_id = string(move_id, f"{path}.move_id")
        allowed = set()
        if valid_id:
            if move_id not in move_map:
                fail(f"{path}.move_id", "record_move_not_in_map")
            else:
                allowed = move_map[move_id]
            if move_id in detailed_moves:
                fail(f"{path}.move_id", "duplicate_detailed_move")
            detailed_moves.add(move_id)
        spans(record.get("focal_spans"), f"{path}.focal_spans", True, allowed)
        strings(record.get("operation"), f"{path}.operation", True)
        question = obj(record.get("question_under_discussion"), f"{path}.question_under_discussion")
        string(question.get("text"), f"{path}.question_under_discussion.text")
        if question.get("provenance") not in ("explicit", "analyst_reconstruction", "unknown"):
            fail(f"{path}.question_under_discussion.provenance", "invalid_question_provenance")
        if "prior_or_foil" not in record:
            fail(f"{path}.prior_or_foil", "missing_field")
        elif record["prior_or_foil"] is not None:
            foil_path = f"{path}.prior_or_foil"
            foil = obj(record["prior_or_foil"], foil_path)
            string(foil.get("proposition"), f"{foil_path}.proposition")
            if foil.get("role") not in ("negated_proposition", "questioned_proposition", "reframed_priority"):
                fail(f"{foil_path}.role", "invalid_prior_role")
            spans(foil.get("source_spans"), f"{foil_path}.source_spans", True)
            if "prior_holder" not in foil:
                fail(f"{foil_path}.prior_holder", "missing_field")
            else:
                string(foil["prior_holder"], f"{foil_path}.prior_holder", True)
        claim_ids = set()
        for claim_index, claim in enumerate(sequence(record.get("asserted_or_promised_content"), f"{path}.asserted_or_promised_content")):
            claim_path = f"{path}.asserted_or_promised_content[{claim_index}]"
            claim = obj(claim, claim_path)
            claim_id = claim.get("claim_id")
            if string(claim_id, f"{claim_path}.claim_id"):
                if claim_id in claim_ids:
                    fail(f"{claim_path}.claim_id", "duplicate_claim_id")
                claim_ids.add(claim_id)
            string(claim.get("text"), f"{claim_path}.text")
            spans(claim.get("source_spans"), f"{claim_path}.source_spans", True)
            attribution = obj(claim.get("attribution"), f"{claim_path}.attribution")
            for field in ("proposer", "reporting_layer", "epistemic_status"):
                string(attribution.get(field), f"{claim_path}.attribution.{field}")
        relation = obj(record.get("relation"), f"{path}.relation")
        for field in ("type", "text"):
            string(relation.get(field), f"{path}.relation.{field}")
        for comp_index, comparand in enumerate(sequence(relation.get("comparands"), f"{path}.relation.comparands")):
            comp_path = f"{path}.relation.comparands[{comp_index}]"
            comparand = obj(comparand, comp_path)
            for field in ("text", "role"):
                string(comparand.get(field), f"{comp_path}.{field}")
            spans(comparand.get("source_spans"), f"{comp_path}.source_spans", True)
        for ground_index, ground in enumerate(sequence(record.get("grounds_and_warrant"), f"{path}.grounds_and_warrant")):
            ground_path = f"{path}.grounds_and_warrant[{ground_index}]"
            ground = obj(ground, ground_path)
            references = strings(ground.get("claim_ids"), f"{ground_path}.claim_ids", True)
            for claim_id in references:
                if not isinstance(claim_id, str) or claim_id not in claim_ids:
                    fail(f"{ground_path}.claim_ids", "unknown_claim_id")
            spans(ground.get("evidence_spans"), f"{ground_path}.evidence_spans")
            for field in ("stated_link", "unstated_assumption"):
                if field not in ground:
                    fail(f"{ground_path}.{field}", "missing_field")
                else:
                    string(ground[field], f"{ground_path}.{field}", True)
            strings(ground.get("unknowns"), f"{ground_path}.unknowns")
        for field in ("information_update", "stance_and_presentation"):
            string(record.get(field), f"{path}.{field}")
        for belief_index, belief in enumerate(sequence(record.get("reader_belief_evidence"), f"{path}.reader_belief_evidence")):
            belief_path = f"{path}.reader_belief_evidence[{belief_index}]"
            belief = obj(belief, belief_path)
            for field in ("proposition", "holder", "reporting_layer"):
                string(belief.get(field), f"{belief_path}.{field}")
            span(belief.get("source_span"), f"{belief_path}.source_span")
        for field in ("preserved_usefulness", "possible_reader_cost", "uncertainties"):
            strings(record.get(field), f"{path}.{field}")
    return {"errors": errors, "records": len(records), "mapped_moves": len(move_map),
            "valid_quote_occurrences": quote_count, "identity_self_report": identity,
            "mechanical_validity": "passed" if not errors else "failed",
            "semantic_validity": "requires_source_review", "exposure_validity": "requires_root_audit"}


def verify(root: Path, run: Path) -> dict:
    """只读核验，单项格式失败不阻断其余回答的报告。"""
    root, run = root.resolve(), run.resolve()
    frozen = run / "frozen"
    manifest = read_json(frozen / "freeze.json")
    integrity_errors = []
    for base, items, code in ((root, manifest["source_files"], "frozen_source_changed"),
                              (frozen, manifest["files"], "frozen_run_file_changed")):
        for relative, expected in items.items():
            path = base / relative
            try:
                actual = digest(path.read_bytes())
            except OSError:
                actual = None
            if actual != expected:
                integrity_errors.append({"path": relative, "code": code})
    results, response_hashes, missing = {}, {}, []
    for assignment_id in manifest["assignment_ids"]:
        response_path = run / "responses" / f"{assignment_id}.json"
        if not response_path.exists():
            missing.append(assignment_id)
            continue
        try:
            raw = response_path.read_bytes()
            response_hashes[response_path.relative_to(run).as_posix()] = digest(raw)
            response = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            results[assignment_id] = {"mechanical_validity": "failed", "valid_quote_occurrences": 0,
                                      "records": 0, "errors": [{"path": "response", "code": "unreadable_response",
                                                                  "exception": type(error).__name__}]}
            continue
        try:
            assignment = read_json(frozen / "assignments" / f"{assignment_id}.json")
            packet = read_json(frozen / assignment["packet_path"])
            results[assignment_id] = validate_response(response, packet, assignment)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            results[assignment_id] = {"mechanical_validity": "failed", "valid_quote_occurrences": 0,
                                      "records": 0, "errors": [{"path": "frozen_assignment_or_packet",
                                                                  "code": "validation_unavailable",
                                                                  "exception": type(error).__name__}]}
    completed = [key for key, value in results.items() if value["mechanical_validity"] == "passed"]
    known_names = {f"{item}.json" for item in manifest["assignment_ids"]}
    unexpected = sorted(path.name for path in (run / "responses").glob("*.json") if path.name not in known_names)
    return {
        "frozen_inputs": "failed" if integrity_errors else "passed", "integrity_errors": integrity_errors,
        "expected_responses": manifest["expected_responses"], "received_responses": len(results),
        "mechanically_valid_responses": len(completed), "completed_assignments": completed,
        "missing_assignments": missing, "unexpected_response_files": unexpected,
        "records": sum(value["records"] for value in results.values()),
        "valid_quote_occurrences": sum(value["valid_quote_occurrences"] for value in results.values()),
        "responses": results, "response_hashes": response_hashes,
        "semantic_validity": "requires_source_review", "exposure_validity": "requires_root_audit",
        "complete": bool(manifest["expected_responses"]) and not integrity_errors and not missing
                    and len(completed) == manifest["expected_responses"] and not unexpected,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="准备或只读核验篇章动作契约 1.1；不调用模型或网络。")
    parser.add_argument("command", choices=("prepare", "verify"))
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(ROOT, args.run) if args.command == "prepare" else verify(ROOT, args.run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
