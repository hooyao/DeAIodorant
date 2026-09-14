"""Audit two frozen InfoQ anchors without changing the preserved pilot corpus.

Network capture is opt-in, bounded to robots.txt and the two listed public
article URLs, and never follows redirects, retries, authenticates, or downloads
referenced media. Existing captures can be audited without network access.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
import time
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup, NavigableString, Tag
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pilot_collect import dereference, extract_infoq, normalize_text  # noqa: E402

VERSION = "media-source-completeness-v1"
USER_AGENT = "DeAIodorantSourceAudit/1.0 (bounded public article integrity check)"
ROBOTS_URL = "https://www.infoq.cn/robots.txt"
TARGETS = (
    ("3c60dc0a981b686870095450", "2026-06", "s6TAS5JMIW1miPSqIsk0"),
    ("44aa81958a6c585ee8c06847", "2026-01", "cYlRMETcNGxhDvBqCDII"),
)


def digest(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_once(url: str, destination: Path, limit: int) -> dict:
    """Make one unauthenticated GET and retain only non-sensitive headers."""
    result = {"url": url, "requested_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9"},
                timeout=(15, 45),
                allow_redirects=False,
                stream=True,
            ) as response:
                result.update({
                    "status": response.status_code,
                    "response_url": response.url,
                    "headers": {key: response.headers[key] for key in (
                        "Content-Type", "Content-Length", "Date", "ETag", "Last-Modified",
                        "Retry-After", "Location",
                    ) if key in response.headers},
                })
                parts = []
                length = 0
                for chunk in response.iter_content(65536):
                    length += len(chunk)
                    if length > limit:
                        result["error"] = "Response exceeded the capture size limit."
                        return result
                    parts.append(chunk)
                content = b"".join(parts)
                destination.write_bytes(content)
                result.update({"bytes": len(content), "sha256": digest(content),
                               "capture_file": destination.name})
    except requests.RequestException as exc:
        result["error"] = type(exc).__name__
    return result


def capture(output: Path) -> None:
    manifest_path = output / "capture-manifest.json"
    if manifest_path.exists():
        raise SystemExit("Refusing to overwrite a capture manifest; use a new version directory.")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"version": VERSION, "user_agent": USER_AGENT, "requests": [],
                "network_policy": "One robots GET and at most one public GET per allowed anchor; no retries."}
    robots = fetch_once(ROBOTS_URL, output / "robots.txt", 512 * 1024)
    manifest["requests"].append(robots)
    write_json(manifest_path, manifest)
    parser = RobotFileParser(ROBOTS_URL)
    if robots.get("status") == 200 and "error" not in robots:
        parser.parse((output / "robots.txt").read_text(encoding="utf-8", errors="replace").splitlines())
    elif robots.get("status") == 404:
        parser.allow_all = True
    else:
        manifest["stop_reason"] = "Robots access policy unavailable; article requests not attempted."
        write_json(manifest_path, manifest)
        return
    delay = max(2.0, float(parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*") or 0))
    rate = parser.request_rate(USER_AGENT) or parser.request_rate("*")
    if rate and rate.requests:
        delay = max(delay, rate.seconds / rate.requests)
    manifest["minimum_request_interval_seconds"] = delay
    for doc_id, _, slug in TARGETS:
        url = f"https://www.infoq.cn/article/{slug}"
        allowed = parser.can_fetch(USER_AGENT, url)
        manifest.setdefault("robots_decisions", []).append({"url": url, "allowed": allowed})
        if not allowed:
            continue
        if delay > 60:
            manifest["stop_reason"] = "Crawl interval exceeds this bounded capture session."
            break
        time.sleep(delay)
        result = fetch_once(url, output / f"{doc_id}.html", 5 * 1024 * 1024)
        manifest["requests"].append(result)
        write_json(manifest_path, manifest)
        if result.get("status") == 429 or result.get("headers", {}).get("Retry-After"):
            manifest["stop_reason"] = "Server requested delay; remaining requests not attempted."
            break
    write_json(manifest_path, manifest)


def preserved_record(doc_id: str, month: str) -> tuple[dict, str, bytes]:
    folder = ROOT / "data" / "pilot" / "monthly" / month
    rows = [json.loads(line) for line in (folder / "meta.jsonl").read_text(encoding="utf-8").splitlines()]
    records = [row for row in rows if row["doc_id"] == doc_id]
    if len(records) != 1:
        raise ValueError("Each anchor must have exactly one matching metadata record.")
    raw = (folder / f"{doc_id}.txt").read_bytes()
    return records[0], raw.decode("utf-8"), raw


def block_map(body: Tag) -> tuple[list[dict], str]:
    """Map text to its nearest paragraph/heading without changing source bytes.

    The collector's html.parser tree can nest nodes under self-closing image
    tags. Semantic text owners avoid treating an image and all later text as
    one paragraph. This mapping is a separately versioned presentation proposal.
    """
    owner_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote", "li"}
    blocks = []
    cursor = 0
    previous_owner = None
    list_ids = {id(node): f"list{index:02d}" for index, node in enumerate(body.select("ul,ol"), 1)}
    for text_node in body.strings:
        lines = [re.sub(r"\s+", " ", line).strip() for line in str(text_node).splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            continue
        owner = next((parent for parent in text_node.parents if parent.name in owner_tags), body)
        if owner is not previous_owner:
            item = next((parent for parent in [owner, *owner.parents] if parent.name == "li"), None)
            list_node = next((parent for parent in owner.parents if parent.name in {"ul", "ol"}), None)
            blocks.append({
                "block_id": f"b{len(blocks) + 1:03d}", "tag": owner.name,
                "source_line_start": cursor + 1, "source_line_end": cursor,
                "collector_lines": [], "dom_text_without_added_separators": "",
                "nonempty_text_nodes": 0,
                "in_list_item": item is not None,
                "list_id": list_ids.get(id(list_node)) if list_node is not None else None,
                "list_type": list_node.name if list_node is not None else None,
                "list_item_ordinal": len(item.find_previous_siblings("li")) + 1 if item is not None else None,
                "html": str(owner),
            })
            previous_owner = owner
        block = blocks[-1]
        block["collector_lines"].extend(lines)
        block["dom_text_without_added_separators"] += str(text_node)
        block["nonempty_text_nodes"] += 1
        cursor += len(lines)
        block["source_line_end"] = cursor
    for block in blocks:
        block["collector_text"] = "\n".join(block.pop("collector_lines"))
        block["collector_line_count"] = len(block["collector_text"].splitlines())
        block["presentation_text"] = re.sub(r"\s+", " ", block["dom_text_without_added_separators"]).strip()
    joined = "\n".join(block["collector_text"] for block in blocks)
    return blocks, joined


def media_map(body: Tag) -> list[dict]:
    """Locate referenced media between normalized source lines; never fetch it."""
    cursor = 0
    media = []
    for node in body.descendants:
        if isinstance(node, Tag) and node.name in {"img", "iframe", "video", "audio", "source"}:
            media.append({"media_id": f"media{len(media) + 1:02d}", "tag": node.name,
                          "src": node.get("src"), "data_src": node.get("data-src"),
                          "alt": node.get("alt"), "title": node.get("title"),
                          "preceding_collector_line": cursor,
                          "capture_status": "reference_only_not_downloaded_or_inspected"})
        elif isinstance(node, NavigableString):
            cursor += sum(bool(re.sub(r"\s+", " ", line).strip()) for line in str(node).splitlines())
    return media


def audit(output: Path) -> dict:
    manifest = json.loads((output / "capture-manifest.json").read_text(encoding="utf-8"))
    request_by_url = {item["url"]: item for item in manifest["requests"]}
    summary = {"version": VERSION, "capture_manifest_sha256": digest((output / "capture-manifest.json").read_bytes()),
               "collector_source_sha256": digest((ROOT / "pilot_collect.py").read_bytes()),
               "audit_script_sha256": digest(Path(__file__).read_bytes()),
               "runtime": {"python": sys.version.split()[0], "beautifulsoup4": importlib.metadata.version("beautifulsoup4"),
                           "requests": importlib.metadata.version("requests"), "html_parser": "html.parser"},
               "documents": []}
    for doc_id, month, slug in TARGETS:
        metadata, stored_text, stored_bytes = preserved_record(doc_id, month)
        url = f"https://www.infoq.cn/article/{slug}"
        row = {"doc_id": doc_id, "url": url, "preserved_file_sha256": digest(stored_bytes),
               "preserved_metadata_content_hash": metadata["content_hash"],
               "preserved_text_chars": len(stored_text), "preserved_lines": len(stored_text.splitlines()),
               "preserved_metadata": metadata}
        source_rows = [json.loads(line) for line in (ROOT / "data/pilot/infoq_post.jsonl").read_text(encoding="utf-8").splitlines()]
        source_text = next(item["text"] for item in source_rows if item["doc_id"] == doc_id)
        row.update({"jsonl_text_sha256": digest(source_text),
                    "jsonl_hash_matches_metadata": digest(source_text) == metadata["content_hash"],
                    "body_file_exactly_equals_jsonl_plus_terminal_lf": stored_text == source_text + "\n",
                    "body_file_equals_jsonl_with_crlf_and_terminal_newline": stored_text == source_text.replace("\n", "\r\n") + "\r\n",
                    "body_file_lf_normalized_equals_jsonl_plus_terminal_lf": stored_text.replace("\r\n", "\n") == source_text + "\n",
                    "body_file_crlf_count": stored_bytes.count(b"\r\n"),
                    "body_file_lf_count": stored_bytes.count(b"\n"),
                    "body_file_bare_cr_count": stored_bytes.count(b"\r") - stored_bytes.count(b"\r\n")})
        request = request_by_url.get(url, {})
        row["capture_response"] = request
        if request.get("status") != 200 or "error" in request:
            row["status"] = "public_capture_unavailable"
            summary["documents"].append(row)
            continue
        raw = (output / request["capture_file"]).read_bytes()
        if digest(raw) != request["sha256"]:
            raise ValueError("Capture bytes no longer match the manifest.")
        html = raw.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        body = soup.select_one("article .ProseMirror") or soup.select_one(".ProseMirror")
        extracted = extract_infoq(html, url, request["requested_at"])
        if body is None or extracted is None:
            row["status"] = "ordinary_page_not_extractable"
            row["page_title"] = soup.title.get_text(" ", strip=True) if soup.title else None
            summary["documents"].append(row)
            continue
        fresh_text = extracted.pop("text")
        (output / f"{doc_id}.fresh-collector.txt").write_text(fresh_text, encoding="utf-8")
        blocks, joined = block_map(body)
        write_json(output / f"{doc_id}.blocks.json", {"version": "media-source-presentation-v1", "source_html_sha256": digest(raw),
                   "collector_text_sha256": digest(fresh_text), "block_concatenation_matches_collector": joined == fresh_text,
                   "mapping_policy": "Nearest paragraph/heading/list-item ownership; source lines remain immutable. Presentation text joins original inline nodes and normalizes source whitespace only.",
                   "blocks": blocks})
        headings = [{"tag": node.name, "text": node.get_text("", strip=False)} for node in body.select("h1,h2,h3,h4,h5,h6")]
        links = [{"text": node.get_text("", strip=False), "href": node.get("href")} for node in body.select("a")]
        media = media_map(body)
        state_script = soup.select_one("#__NUXT_DATA__")
        state = json.loads(state_script.string) if state_script and state_script.string else []
        article_state = next((item for item in state if isinstance(item, dict) and
                              all(key in item for key in ("article_title", "publish_time", "content"))), {})
        state_content = dereference(state, article_state.get("content"))
        state_body = BeautifulSoup(state_content, "html.parser") if isinstance(state_content, str) else None
        row.update({
            "status": "exact_preserved_text_match" if fresh_text == source_text else "source_body_diverged",
            "fresh_collector_text_sha256": digest(fresh_text), "fresh_collector_text_chars": len(fresh_text),
            "fresh_metadata": extracted, "page_heading": soup.h1.get_text("", strip=False) if soup.h1 else None,
            "beginning_matches": fresh_text[:300] == source_text[:300],
            "ending_matches": fresh_text[-300:] == source_text[-300:],
            "block_concatenation_matches_collector": joined == fresh_text,
            "nonempty_semantic_text_blocks": len(blocks),
            "semantic_text_blocks_with_multiple_collector_lines": sum(block["collector_line_count"] > 1 for block in blocks),
            "added_collector_line_boundaries_within_semantic_text_blocks": sum(block["collector_line_count"] - 1 for block in blocks),
            "semantic_text_block_tag_counts": {tag: sum(block["tag"] == tag for block in blocks) for tag in sorted({block["tag"] for block in blocks})},
            "parser_image_nodes_with_paragraph_descendants": sum(bool(node.select("p")) for node in body.select("img")),
            "headings": headings, "links": links, "media": media,
            "element_counts": {tag: len(body.select(tag)) for tag in ("p", "h1", "h2", "h3", "ul", "ol", "li", "img", "figure", "figcaption", "table", "tr", "td", "th", "pre", "code", "blockquote", "a", "br", "strong", "em")},
            "zero_width_space_count": fresh_text.count("\u200b"),
            "state_content_is_string": isinstance(state_content, str),
            "embedded_content_normalized_matches_visible_body": normalize_text(state_body) == fresh_text if state_body is not None else None,
            "title_matches_preserved": extracted["title"] == metadata["title"],
            "authors_match_preserved": extracted["authors"] == metadata["authors"],
            "translators_match_preserved": extracted["translators"] == metadata["translators"],
            "publication_date_matches_preserved": extracted["published_at"] == metadata["published_at"],
        })
        if fresh_text != source_text:
            import difflib
            difference = difflib.unified_diff(source_text.splitlines(keepends=True), fresh_text.splitlines(keepends=True),
                                            fromfile="preserved-jsonl-text", tofile="fresh-public-page-text")
            (output / f"{doc_id}.source-divergence.diff").write_text("".join(difference), encoding="utf-8")
        write_json(output / f"{doc_id}.audit.json", row)
        summary["documents"].append(row)
    write_json(output / "audit-summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true", help="Opt in to the bounded public capture.")
    args = parser.parse_args()
    if args.fetch:
        capture(args.output_dir)
    summary = audit(args.output_dir)
    print(json.dumps({"version": VERSION, "documents": [{"doc_id": row["doc_id"], "status": row["status"],
                      "nonempty_semantic_text_blocks": row.get("nonempty_semantic_text_blocks"),
                      "preserved_lines": row["preserved_lines"]} for row in summary["documents"]]}))


if __name__ == "__main__":
    main()
