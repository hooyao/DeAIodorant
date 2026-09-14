"""Present source and candidate in shared DOM paragraphs, neutralizing line artifacts."""

from __future__ import annotations

import argparse
import bisect
from html import escape
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.records import replay_operations, text_hash, write_json

VERSION = "media-repair-shared-presentation-1.0"
BLOCK_PATHS = {
    "doc-03": "data/local/compact_refiner/media-source-captures-v1/44aa81958a6c585ee8c06847.blocks.json",
    "doc-04": "data/local/media-contrast-staging-v1/documents/0be079018045fbf1f2d47d7f/blocks.json",
    "doc-05": "data/local/media-contrast-staging-v1/documents/c526ed941b8de39a5388df3d/blocks.json",
}


def compact(text: str) -> str:
    return "".join(char for char in text if not char.isspace())


def project_block(raw: str, presentation: str, operations: list[dict]) -> tuple[str, list[str]]:
    """Map non-whitespace edits to DOM text; whitespace-only fixes receive no gain."""
    if compact(raw) != compact(presentation):
        raise ValueError("DOM presentation differs in non-whitespace source content")
    source_positions = [i for i, char in enumerate(raw) if not char.isspace()]
    display_positions = [i for i, char in enumerate(presentation) if not char.isspace()]
    projected = []
    layout_only = []
    for operation in operations:
        if compact(operation["before"]) == compact(operation["after"]):
            layout_only.append(operation["operation_id"])
            continue
        left = bisect.bisect_left(source_positions, operation["start_char"])
        right = bisect.bisect_left(source_positions, operation["end_char"])
        start = display_positions[left] if left < len(display_positions) else len(presentation)
        end = display_positions[right - 1] + 1 if right > left else start
        after = re.sub(r"\s+", " ", operation["after"]).strip()
        projected.append({"start_char": start, "end_char": end,
                          "before": presentation[start:end], "after": after})
    result = replay_operations(presentation, projected)
    if compact(result) != compact(replay_operations(raw, operations)):
        raise ValueError("Presentation lost or changed non-whitespace candidate content")
    return result, layout_only


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alias", choices=tuple(BLOCK_PATHS), required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    candidate_dir, output = args.candidate_dir.resolve(), args.output_dir.resolve()
    for path in (candidate_dir, output):
        path.relative_to((ROOT / "data/local").resolve())
    if output.exists():
        raise ValueError("Use a new presentation directory")
    alias = args.alias
    source_path = ROOT / "data/local/contrast-context-v1/packets" / alias / "body.txt"
    source = source_path.read_bytes().decode("utf-8")
    candidate = (candidate_dir / "output.txt").read_bytes().decode("utf-8")
    record = json.loads((candidate_dir / "operations.json").read_text(encoding="utf-8"))
    if text_hash(source) != record["source_sha256"] or text_hash(candidate) != record["output_sha256"]:
        raise ValueError("Candidate source/output hash mismatch")
    if replay_operations(source, record["operations"]) != candidate:
        raise ValueError("Candidate replay mismatch")
    blocks_path = ROOT / BLOCK_PATHS[alias]
    blocks = json.loads(blocks_path.read_text(encoding="utf-8"))["blocks"]
    if "\n".join(b["collector_text"] for b in blocks) != source:
        raise ValueError("DOM block identity mismatch")
    rows = []
    cursor = 0
    consumed = []
    layout_only = []
    for block in blocks:
        raw = block["collector_text"]
        end = cursor + len(raw)
        local = []
        for operation in record["operations"]:
            if cursor <= operation["start_char"] <= operation["end_char"] <= end:
                local.append({**operation, "start_char": operation["start_char"] - cursor,
                              "end_char": operation["end_char"] - cursor})
                consumed.append(operation["operation_id"])
        revised, neutralized = project_block(raw, block["presentation_text"], local)
        layout_only.extend(neutralized)
        rows.append({"block_id": block["block_id"], "tag": block["tag"],
                     "source_start_char": cursor, "source_end_char": end,
                     "original": block["presentation_text"], "candidate": revised,
                     "changed": revised != block["presentation_text"],
                     "operation_ids": [op["operation_id"] for op in local]})
        cursor = end + 1
    if sorted(consumed) != sorted(op["operation_id"] for op in record["operations"]):
        raise ValueError("An operation crosses a source DOM paragraph boundary")
    if compact("".join(r["candidate"] for r in rows)) != compact(candidate):
        raise ValueError("Full candidate presentation coverage mismatch")
    article = []
    for row in rows:
        tag = row["tag"] if row["tag"] in {"h1", "h2", "h3", "h4", "h5", "h6"} else "p"
        article.append(f'<section class="pair {"changed" if row["changed"] else ""}" id="{row["block_id"]}"><small>{row["block_id"]}</small>'
                       f'<div class="columns"><{tag}>{escape(row["original"])}</{tag}><{tag}>{escape(row["candidate"])}</{tag}></div></section>')
    html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Media repair review</title><style>' \
           'body{font:17px/1.8 system-ui,sans-serif;max-width:1500px;margin:32px auto;padding:0 24px;color:#20252b;background:#fbfbfa}' \
           'header{position:sticky;top:0;background:#fbfbfa;border-bottom:1px solid #ccc;padding:12px 0;z-index:1}' \
           '.columns{display:grid;grid-template-columns:1fr 1fr;gap:40px}.columns>*{margin:8px 0;overflow-wrap:anywhere;font-size:inherit}' \
           '.pair{padding:10px 16px;border-bottom:1px solid #eee}.changed{background:#f1f5fa}small{color:#68717c}' \
           'a{color:#275584;margin-right:12px}@media(max-width:800px){.columns{gap:18px}body{padding:0 8px;font-size:15px}}' \
           '</style><body><header><strong>Development review: ' + escape(alias) + '</strong>' \
           '<p>Original and candidate share source DOM paragraphs. Extractor line breaks are neutralized on both sides. ' \
           'Referenced images are not displayed. This is an identified qualitative review, not a blinded preference trial.</p>' \
           '<nav>' + ''.join(f'<a href="#{r["block_id"]}">{r["block_id"]}</a>' for r in rows if r["changed"]) + '</nav>' \
           '<div class="columns"><strong>Original</strong><strong>Candidate</strong></div></header>' + ''.join(article) + '</body></html>'
    output.mkdir(parents=True)
    (output / "review.html").write_text(html, encoding="utf-8", newline="\n")
    write_json(output / "paragraphs.json", rows)
    write_json(output / "manifest.json", {"version": VERSION, "alias": alias,
        "source_sha256": text_hash(source), "candidate_sha256": text_hash(candidate),
        "operations_sha256": text_hash((candidate_dir / "operations.json").read_bytes().decode("utf-8")),
        "blocks_sha256": text_hash(blocks_path.read_bytes().decode("utf-8")),
        "implementation_sha256": text_hash(Path(__file__).read_bytes().decode("utf-8")),
        "paragraphs": len(rows), "changed_paragraphs": sum(row["changed"] for row in rows),
        "layout_only_operations_neutralized": layout_only,
        "all_non_whitespace_content_preserved": True, "human_gold": False,
        "purpose": "identified qualitative review; no preference outcome collected",
        "command": f"python experiments/render_media_repair_review.py --alias {alias} --candidate-dir {candidate_dir.relative_to(ROOT).as_posix()} --output-dir {output.relative_to(ROOT).as_posix()}",
        "output_hashes": {p.name: text_hash(p.read_bytes().decode("utf-8")) for p in output.iterdir() if p.is_file()}})
    print(json.dumps({"alias": alias, "paragraphs": len(rows), "changed_paragraphs": sum(r["changed"] for r in rows),
                      "neutralized_layout_operations": len(layout_only)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
