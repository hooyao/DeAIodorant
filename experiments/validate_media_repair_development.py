"""Verify full-article proposal replay and emit literal-change diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
import difflib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.records import literal_diagnostics, replay_operations, text_hash, write_json

VERSION = "media-repair-development-validation-1.0"
ALIASES = ("doc-03", "doc-04", "doc-05")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to((ROOT / "data/local").resolve())
    if output.exists():
        raise ValueError("Use a new validation directory")
    root = ROOT / "data/local/media-repair-development-v1"
    manifest_path = root / "preparation-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    protocol = ROOT / "docs/routes/compact-refiner/media-repair-development.md"
    if text_hash(protocol.read_bytes().decode("utf-8")) != manifest["protocol_hash"]:
        raise ValueError("Prepared repair protocol changed")
    results = []
    diffs = {}
    input_hashes = {manifest_path.relative_to(ROOT).as_posix(): text_hash(manifest_path.read_bytes().decode("utf-8"))}
    for alias in ALIASES:
        source_path = ROOT / "data/local/contrast-context-v1/packets" / alias / "body.txt"
        variant_path = root / "candidates" / alias / "output.txt"
        operations_path = variant_path.with_name("operations.json")
        source = source_path.read_bytes().decode("utf-8")
        variant = variant_path.read_bytes().decode("utf-8")
        record = json.loads(operations_path.read_text(encoding="utf-8"))
        source_hash, output_hash = text_hash(source), text_hash(variant)
        if source_hash != manifest["source_hashes"][alias]:
            raise ValueError("Prepared source changed")
        # Editor records use explicit hashes; accept the equivalent names used
        # by existing development utilities without treating a missing hash as valid.
        supplied_source = record.get("source_sha256", record.get("input_sha256"))
        supplied_output = record.get("output_sha256")
        if supplied_source != source_hash or supplied_output != output_hash:
            raise ValueError("Candidate content identity mismatch")
        operations = record["operations"]
        if len({r["operation_id"] for r in operations}) != len(operations):
            raise ValueError("Duplicate operation IDs")
        for operation in operations:
            if type(operation["start_char"]) is not int or type(operation["end_char"]) is not int:
                raise ValueError("Operation offsets must be integers")
            for field in ("before", "after", "operation_type", "reason", "preservation_notes"):
                if not isinstance(operation.get(field), str):
                    raise ValueError("Missing operation contract field")
        if replay_operations(source, operations) != variant:
            raise ValueError("Full-article replay mismatch")
        urls = lambda text: Counter(re.findall(r"https?://[^\s]+", text))
        terms = sorted(set(re.findall(r"[A-Za-z][A-Za-z0-9_.+-]{2,}", source)))
        diagnostics = literal_diagnostics(source, variant, terms)
        diagnostics.update({"missing_url_tokens": dict(urls(source) - urls(variant)),
                            "added_url_tokens": dict(urls(variant) - urls(source)),
                            "source_ershi": source.count("而是"), "output_ershi": variant.count("而是"),
                            "source_unicode_chars": len(source), "output_unicode_chars": len(variant)})
        results.append({"alias": alias, "source_sha256": source_hash, "output_sha256": output_hash,
                        "operations_sha256": text_hash(operations_path.read_bytes().decode("utf-8")),
                        "operation_count": len(operations), "replay_exact": True, "human_gold": False,
                        "semantic_preservation": "pending_independent_review", "diagnostics": diagnostics})
        diffs[alias] = "".join(difflib.unified_diff(source.splitlines(keepends=True), variant.splitlines(keepends=True),
                               fromfile=f"{alias}/source", tofile=f"{alias}/candidate"))
        for path in (source_path, variant_path, operations_path):
            input_hashes[path.relative_to(ROOT).as_posix()] = text_hash(path.read_bytes().decode("utf-8"))
    output.mkdir(parents=True)
    for alias, diff in diffs.items():
        (output / f"{alias}.diff").write_text(diff, encoding="utf-8", newline="\n")
    write_json(output / "summary.json", {"version": VERSION, "documents": results, "human_gold": False,
                                         "status": "mechanical_replay_and_literal_diagnostics_only"})
    for name, expected in input_hashes.items():
        if text_hash((ROOT / name).read_bytes().decode("utf-8")) != expected:
            raise ValueError("Input changed during validation")
    write_json(output / "manifest.json", {"version": VERSION, "input_hashes": input_hashes,
        "implementation_sha256": text_hash(Path(__file__).read_bytes().decode("utf-8")),
        "command": f"python experiments/validate_media_repair_development.py --output-dir {output.relative_to(ROOT).as_posix()}",
        "output_hashes": {p.name: text_hash(p.read_bytes().decode("utf-8")) for p in output.iterdir() if p.is_file()}})
    print(json.dumps({"documents": len(results), "operation_counts": {r["alias"]: r["operation_count"] for r in results},
                      "semantic_preservation": "pending_independent_review"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
