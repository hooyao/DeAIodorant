"""Prepare exact article blocks and citation-aware views of one reader anchor."""

from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.analysis.reading_burden import analyze_sentences
from deaiodorant.refine.records import write_json

VERSION = "smzdm-reader-anchor-1.0"
DIRECTORY = ROOT / "data/local/reader-style-anchors-v1"
URL = "https://post.smzdm.com/p/a70dm4ll/"


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    output = DIRECTORY / "smzdm"
    if output.exists():
        raise ValueError("Use a new anchor version; do not overwrite evidence")
    raw = (DIRECTORY / "source.html").read_bytes()
    request = json.loads((DIRECTORY / "article-request.json").read_text(encoding="utf-8"))
    if request.get("status") != 200 or sha(raw) != request["sha256"]:
        raise ValueError("Source capture identity mismatch")
    soup = BeautifulSoup(raw, "html.parser")
    article = soup.select_one("article#articleId")
    title = soup.select_one("h1.aigc-head-img-title")
    published = soup.select_one('meta[property="article:published_time"]')
    if article is None or title is None or published is None:
        raise ValueError("Expected article structure is unavailable")
    published_at = datetime.fromisoformat(published["content"])
    page_text = soup.get_text(" ", strip=True)
    if "内容由AI生成" not in page_text:
        raise ValueError("Previously observed disclosure missing from capture")
    author_label = next((normalize(x.get_text()) for x in soup.select("span.text")
                         if "源自183位全网作者" in x.get_text()), None)
    blocks, citations, media = [], [], []
    for element in article.select("h1,h2,h3,h4,h5,h6,p,li"):
        # A list item is a single block even if its publisher adds nested p tags.
        if element.find_parent("li") is not None:
            continue
        for node in element.select("img,video,iframe"):
            media.append({"tag": node.name, "src": node.get("src"), "data_src": node.get("data-src"),
                          "alt": node.get("alt"), "status": "reference_only_not_inspected"})
        full = normalize(element.get_text("", strip=False))
        if not full:
            continue
        alias = f"b{len(blocks) + 1:03d}"
        clone = copy.deepcopy(element)
        block_citations = []
        for ordinal, node in enumerate(clone.select("span.referer-link"), 1):
            citation_id = f"{alias}-c{ordinal:02d}"
            citations.append({"citation_id": citation_id, "block_id": alias,
                "publisher_label": node.get_text("", strip=False),
                "source_url": node.get("data-referer-link"),
                "publisher_highlight_text": node.get("data-highlight-text"),
                "publisher_quote_text": node.get("data-quote-text"),
                "evidence_status": "publisher_embedded_attribution_not_independently_verified",
                "dom_html": str(node)})
            block_citations.append(citation_id)
            node.decompose()
        prose = normalize(clone.get_text("", strip=False))
        blocks.append({"block_id": alias, "tag": element.name,
                       "source_dom_html": str(element), "text_with_citation_labels": full,
                       "analysis_text": prose, "citation_ids": block_citations})
    if len(blocks) < 10:
        raise ValueError("Unexpectedly incomplete article extraction")
    source_body = "\n".join(block["text_with_citation_labels"] for block in blocks)
    analysis_body = "\n".join(block["analysis_text"] for block in blocks)
    source_cursor = analysis_cursor = 0
    for block in blocks:
        block["source_start_char"] = source_cursor
        block["source_end_char"] = source_cursor + len(block["text_with_citation_labels"])
        block["analysis_start_char"] = analysis_cursor
        block["analysis_end_char"] = analysis_cursor + len(block["analysis_text"])
        source_cursor = block["source_end_char"] + 1
        analysis_cursor = block["analysis_end_char"] + 1
    for block in blocks:
        assert source_body[block["source_start_char"]:block["source_end_char"]] == block["text_with_citation_labels"]
        assert analysis_body[block["analysis_start_char"]:block["analysis_end_char"]] == block["analysis_text"]
    output.mkdir()
    (output / "article.dom.html").write_text(str(article), encoding="utf-8", newline="\n")
    (output / "body-with-citations.txt").write_bytes(source_body.encode("utf-8"))
    (output / "analysis-body.txt").write_bytes(analysis_body.encode("utf-8"))
    write_json(output / "blocks.json", {"version": VERSION, "blocks": blocks})
    write_json(output / "citations.json", {"citations": citations,
        "upstream_sources_fetched": False,
        "limit": "Embedded quote and highlight attributes are publisher assertions, not source-fidelity gold."})
    write_json(output / "media.json", {"references": media, "media_inspected": False})
    source_measurement = analyze_sentences([{"text": source_body}])
    analysis_measurement = analyze_sentences([{"text": analysis_body}])
    write_json(output / "literal-measurements.json", {"source_view": source_measurement,
        "analysis_view": analysis_measurement,
        "interpretation": "Existing literal counter only; zero counts do not override the human strong-smell label."})
    write_json(output / "metadata.json", {"version": VERSION, "url": URL,
        "doc_id": sha(URL.encode())[:24], "platform": "smzdm", "title": normalize(title.get_text()),
        "published_at": published_at.isoformat(), "publication_evidence": 'meta[property="article:published_time"]',
        "collected_at_utc": request["requested_at"], "source_html_sha256": sha(raw),
        "publisher_ai_disclosure": "内容由AI生成", "publisher_attribution_claim": author_label,
        "generation_model": "unknown", "generation_pipeline": "unknown",
        "translation_status": "unresolved", "reader_severity_source": "maintainer_spontaneous_feedback",
        "reader_term": "恶臭", "reader_label_is_generation_proof": False,
        "corpus_role": "development_strong_positive_anchor_not_validation_or_training",
        "body_with_citations_sha256": sha(source_body.encode()), "analysis_body_sha256": sha(analysis_body.encode()),
        "text_blocks": len(blocks), "citation_markers": len(citations), "media_references": len(media),
        "analytical_transformation": "Retain DOM paragraph/list/heading boundaries; normalize whitespace; remove only span.referer-link nodes in a separately hashed analytical view.",
        "rights_status": "research_inspection_only_training_rights_unverified"})
    inputs = [DIRECTORY / name for name in ("source.html", "article-request.json", "robots.txt", "robots-request.json", "reader-feedback.json")]
    write_json(output / "manifest.json", {"version": VERSION,
        "input_hashes": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in inputs},
        "implementation_hashes": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
            (Path(__file__), ROOT / "src/deaiodorant/analysis/reading_burden.py")},
        "output_hashes": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
        "command": "python experiments/prepare_smzdm_reader_anchor.py", "external_model_api_calls": 0,
        "gpu_used": False, "network_in_preparation": False})
    print(json.dumps({"blocks": len(blocks), "citation_markers": len(citations), "media_references": len(media),
                      "literal_ershi": analysis_body.count("而是"), "literal_not_is": analysis_body.count("不是")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
