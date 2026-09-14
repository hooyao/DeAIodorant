"""Verify frozen research source linkage without modifying research artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
WORK = "data/local/cognitive-move-analysis-v1"
SMZDM = "data/local/reader-style-anchors-v1/smzdm"
BAIDU = "data/local/targeted-media-discovery-v1/baidu-supply/documents/92ade4253c08a43329164bf5"
PROTOCOL = "docs/routes/compact-refiner/cognitive-move-analysis.md"
ORIGINALS = "data/local/documentation-zh-migration-v1/originals"
EXPECTED_HASHES = {
    f"{WORK}/units-v1.1.json": "2045ab168946ff08b96e7fe524ddccf683fc007b465731be928bbd18059140f2",
    f"{SMZDM}/analysis-body.txt": "6a07bf687b9a91ee7eedaad1d0a8d71b26defcdd9f246b8b8af78dad30180451",
    f"{BAIDU}/body.txt": "2977deaed4317dd195716a9bd051e69a81d45fc2ffba94db7086aa0418a126e2",
    f"{WORK}/validate_units_v1_1.py": "aa219b7a7ae454585f00731c016a639185ae7013e3d404e819fa6c97c8f5981b",
}
SEMANTIC_FIELDS = (
    "operation", "question_under_discussion", "prior_or_foil",
    "asserted_or_promised_content", "relation", "grounds_and_warrant",
    "information_update", "stance_and_presentation",
)
SPAN_FIELDS = {"view", "block_id", "start_char", "end_char", "quote"}


class VerificationError(ValueError):
    """A concise failure that never includes source text."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise VerificationError(f"missing_file: {path.name}") from None
    except OSError:
        raise VerificationError(f"unreadable_file: {path.name}") from None


def read_json(path: Path) -> dict:
    try:
        value = json.loads(read_bytes(path).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise VerificationError(f"invalid_json: {path.name}") from None
    require(isinstance(value, dict), f"invalid_object: {path.name}")
    return value


def verify_hash(path: Path, expected: str) -> str:
    actual = hashlib.sha256(read_bytes(path)).hexdigest()
    require(actual == expected, f"hash_mismatch: {path.name}")
    return actual


def build_blocks(text: str, records: list, text_key: str,
                 offset_keys: tuple[str, str] | None = None) -> dict:
    """Require complete ordered coverage, including saved newline separators."""
    bounds = {}
    cursor = 0
    pieces = []
    for record in records:
        block_id = record["block_id"]
        piece = record[text_key]
        require(isinstance(piece, str) and bool(piece), "invalid_block_text")
        require(isinstance(block_id, str) and block_id not in bounds, "invalid_block_id")
        end = cursor + len(piece)
        if offset_keys is not None:
            start_saved, end_saved = (record[key] for key in offset_keys)
            require(type(start_saved) is int and type(end_saved) is int,
                    "invalid_block_offset")
            require((start_saved, end_saved) == (cursor, end), "block_offset_mismatch")
        require(text[cursor:end] == piece, "block_source_mismatch")
        bounds[block_id] = (cursor, end)
        pieces.append(piece)
        cursor = end + 1
    require(bool(records) and "\n".join(pieces) == text, "block_coverage_mismatch")
    return bounds


def validate_spans(value, texts: dict, blocks: dict) -> tuple[int, int]:
    """Validate nested evidence references and count occurrences and identities."""
    spans = []

    def visit(item):
        if isinstance(item, dict):
            if SPAN_FIELDS <= item.keys():
                view, block_id = item["view"], item["block_id"]
                require(isinstance(view, str) and view in texts, "unknown_span_view")
                require(isinstance(block_id, str) and block_id in blocks[view],
                        "unknown_span_block")
                start, end, quote = item["start_char"], item["end_char"], item["quote"]
                require(type(start) is int and type(end) is int and
                        0 <= start < end <= len(texts[view]), "invalid_span_offset")
                require(isinstance(quote, str) and texts[view][start:end] == quote,
                        "span_source_mismatch")
                left, right = blocks[view][block_id]
                require(left <= start < end <= right, "span_outside_block")
                spans.append((view, block_id, start, end, quote))
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return len(spans), len(set(spans))


def verify_handover(root: Path) -> dict:
    checked = {name: verify_hash(root / name, digest)
               for name, digest in EXPECTED_HASHES.items()}
    record = read_json(root / WORK / "units-v1.1.json")
    require(record["version"] == "cognitive-move-analysis-1.1", "unit_version_mismatch")
    source_hashes = record["source_hashes"]
    require(len(source_hashes) == 16, "source_manifest_count_mismatch")
    for name, digest in source_hashes.items():
        actual_path = f"{ORIGINALS}/{name}" if name == PROTOCOL else name
        verify_hash(root / actual_path, digest)

    texts = {
        "smzdm_analysis_body": read_bytes(root / SMZDM / "analysis-body.txt").decode("utf-8"),
        "baidu_body": read_bytes(root / BAIDU / "body.txt").decode("utf-8"),
        "smzdm_title": read_json(root / SMZDM / "metadata.json")["title"],
    }
    require(isinstance(texts["smzdm_title"], str), "invalid_metadata_title")
    view_hashes = {key: hashlib.sha256(text.encode("utf-8")).hexdigest()
                   for key, text in texts.items()}
    require(view_hashes["smzdm_title"] == record["views"]["smzdm_title"]["sha256_utf8_value"],
            "title_hash_mismatch")
    blocks = {
        "smzdm_title": {"title": (0, len(texts["smzdm_title"]))},
        "smzdm_analysis_body": build_blocks(
            texts["smzdm_analysis_body"], read_json(root / SMZDM / "blocks.json")["blocks"],
            "analysis_text", ("analysis_start_char", "analysis_end_char")),
        "baidu_body": build_blocks(
            texts["baidu_body"], read_json(root / BAIDU / "blocks.json")["blocks"], "collector_text"),
    }
    units = record["units"]
    require([unit["id"] for unit in units] == [f"M{i:02d}" for i in range(1, 7)],
            "unit_ids_mismatch")
    for unit in units:
        require(all(field in unit for field in SEMANTIC_FIELDS), "missing_semantic_field")
        require(bool(unit["source_spans"]), "missing_source_spans")
        require(unit["question_under_discussion"]["provenance"] in
                {"explicit", "analyst_reconstruction", "unknown"}, "invalid_question_provenance")
    occurrences, unique = validate_spans(units, texts, blocks)
    require((occurrences, unique) == (80, 58), "span_counts_mismatch")

    validation = read_json(root / WORK / "validation-v1.1.json")
    require(validation["version"] == "cognitive-move-linkage-validation-1.1",
            "validation_version_mismatch")
    require(validation["units"] == len(units) and validation["evidence_spans"] == occurrences,
            "validation_counts_mismatch")
    require(validation["view_sha256"] == view_hashes, "validation_view_hashes_mismatch")
    require(validation["unit_file_sha256"] == checked[f"{WORK}/units-v1.1.json"],
            "validation_units_hash_mismatch")
    require(validation["validator_sha256"] == checked[f"{WORK}/validate_units_v1_1.py"],
            "validation_validator_hash_mismatch")
    require(validation["protocol_sha256"] == source_hashes[PROTOCOL],
            "validation_protocol_hash_mismatch")
    require(validation["coverage_and_source_linkage"] == "passed" and
            validation["semantic_validity"] == "not_established_by_this_check" and
            validation["human_unit_labels"] is False and validation["quality_score"] is None,
            "validation_scope_mismatch")
    return {
        "version": "research-handover-verification-1.0",
        "source_linkage": "passed",
        "semantic_validity": "not_established_by_this_check",
        "human_unit_labels": False,
        "units": len(units),
        "semantic_fields_per_unit": len(SEMANTIC_FIELDS),
        "evidence_span_occurrences": occurrences,
        "unique_evidence_spans": unique,
        "source_manifest_files_verified": len(source_hashes),
        "block_counts": {key: len(value) for key, value in blocks.items()},
        "unit_file_sha256": checked[f"{WORK}/units-v1.1.json"],
        "view_sha256": view_hashes,
        "historical_protocol_path": f"{ORIGINALS}/{PROTOCOL}",
        "historical_protocol_sha256": source_hashes[PROTOCOL],
        "historical_validator_sha256": checked[f"{WORK}/validate_units_v1_1.py"],
    }


def verify_inventory(root: Path, inventory_path: Path) -> dict:
    """Check listed raw bytes without following paths outside the project root."""
    inventory = read_json(inventory_path)
    require(inventory.get("schema_version") == "research-handover-artifacts-1.0",
            "inventory_version_mismatch")
    require(inventory.get("roots") == ["data", "feature_runs"], "inventory_roots_mismatch")
    records = inventory.get("files")
    require(isinstance(records, list), "invalid_inventory_files")
    project_root = root.resolve()
    seen = set()
    total_bytes = 0
    for record in records:
        require(isinstance(record, dict), "invalid_inventory_record")
        relative = record.get("path")
        require(isinstance(relative, str) and bool(relative), "invalid_inventory_path")
        windows_path = PureWindowsPath(relative)
        portable_path = PurePosixPath(relative.replace("\\", "/"))
        require(not windows_path.drive and not windows_path.root and
                not portable_path.is_absolute() and ".." not in portable_path.parts,
                "unsafe_inventory_path")
        require(bool(portable_path.parts) and portable_path.parts[0] in inventory["roots"],
                "inventory_path_outside_declared_roots")
        normalized = portable_path.as_posix()
        require(normalized not in seen, "duplicate_inventory_path")
        seen.add(normalized)
        artifact_path = (project_root / portable_path).resolve()
        require(artifact_path.is_relative_to(project_root), "inventory_path_outside_project")
        expected_size, expected_hash = record.get("bytes"), record.get("sha256")
        require(type(expected_size) is int and expected_size >= 0, "invalid_inventory_size")
        require(isinstance(expected_hash, str) and len(expected_hash) == 64 and
                all(character in "0123456789abcdef" for character in expected_hash),
                "invalid_inventory_hash")
        actual_size = 0
        digest = hashlib.sha256()
        try:
            with artifact_path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    actual_size += len(chunk)
                    digest.update(chunk)
        except FileNotFoundError:
            raise VerificationError("inventory_missing_file") from None
        except OSError:
            raise VerificationError("inventory_unreadable_file") from None
        require(actual_size == expected_size, "inventory_size_mismatch")
        require(digest.hexdigest() == expected_hash, "inventory_hash_mismatch")
        total_bytes += actual_size
    return {"status": "passed", "files_verified": len(records), "bytes_verified": total_bytes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="只读核验续研材料的来源关联，不评价语义准确性。")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="项目根目录；默认使用此脚本所在仓库。")
    parser.add_argument("--output", type=Path,
                        help="将摘要另存为新的 JSON 文件；拒绝覆盖，默认仅打印。")
    parser.add_argument("--inventory", type=Path,
                        help="另外核验产物清单；相对路径以项目根目录为基准，默认不启用。")
    args = parser.parse_args(argv)
    try:
        if args.output is not None and args.output.exists():
            raise VerificationError("output_already_exists")
        result = verify_handover(args.root)
        if args.inventory is not None:
            inventory_path = args.inventory if args.inventory.is_absolute() else args.root / args.inventory
            result["inventory"] = verify_inventory(args.root, inventory_path)
        summary = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output is not None:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(summary)
    except VerificationError as exc:
        print(f"检查失败：{exc}", file=sys.stderr)
        return 1
    except (KeyError, TypeError, UnicodeError):
        print("检查失败：invalid_artifact_structure", file=sys.stderr)
        return 1
    except OSError:
        print("检查失败：output_write_failed", file=sys.stderr)
        return 1
    print(summary, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
