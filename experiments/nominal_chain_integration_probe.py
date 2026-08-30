"""Locate long boundary-free pre-head nominal chains with frozen UD rules."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from deaiodorant.analysis.stanza_backend import (
    PROCESSORS,
    _configure_determinism,
    _load_stanza,
    _model_fingerprint,
)
from deaiodorant.analysis.syntax import DependencyToken


SCHEMA_VERSION = "deaiodorant-nominal-chain-integration-probe-0.2"
SEED = 2026083001
NOMINAL_POS = frozenset({"NOUN", "PROPN"})
NOMINAL_MODIFIER_RELATIONS = frozenset({"acl", "amod", "compound", "nmod"})
BOUNDARY_FORMS = frozenset({"的", "之", "及", "与", "和", "或", "、", "以及"})
GENERIC_ASCII_TERMS = frozenset({"ai", "agent", "aigc", "gpt", "llm"})
MIN_PREHEAD_LEXICAL_TOKENS = 5
MIN_PREHEAD_VISIBLE_CHARS = 10
MIN_NOMINAL_RELATIONS = 3
MIN_DOCUMENTS = 6
MIN_SOURCES = 3
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ASCII_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+_.-]*$")
CODE_OR_URL_RE = re.compile(r"https?://|(?:^|\s)(?:pip|npm|curl|git)\s|[{}<>]=?|```", re.I)
SENTENCE_END_RE = re.compile(r"[。！？]")
QUESTION_PREFIX_RE = re.compile(
    r"^(?:InfoQ|机器之心|Q\d*|问|记者|采访者|主持人)[：:]",
    re.I,
)
CAPTION_PREFIX_RE = re.compile(
    r"^(?:图|表|代码|清单|公式|注)\s*(?:\d+|[一二三四五六七八九十]+)?[：:．.、\s]"
)
DEPENDENT_START_RE = re.compile(
    r"^(?:也|还)(?:提供|推出|提出|表示|认为|显示|说明|成为|有|是|可以|能够|会|将|让|使)"
)
EXTERNAL_REFERENCE_RE = re.compile(
    r"(?:上图|下图|如图|从图|图\s*[0-9一二三四五六七八九十]+(?:[.．][A-Za-z0-9]+)?\s*(?:中|所示)|"
    r"算法\s*\d+\s*(?:给出|所示)|(?:图示|算法|结果)见下)"
)
PROSE_METADATA_RE = re.compile(
    r"(?:作者介绍|作者简介|论文下载|请查阅|开源地址|项目主页|"
    r"(?:^|\n)\s*(?:PDF|原文|GitHub|HuggingFace|Case\s*\d+)[：:\s]*(?:\n|$))",
    re.I,
)
MIN_PASSAGE_CJK = 120
MAX_PASSAGE_CJK = 360
MAX_PASSAGE_CHARS = 520


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relation(token: DependencyToken) -> str:
    return token.deprel.split(":", 1)[0]


def visible_chars(text: str) -> int:
    return sum(not char.isspace() for char in text)


def eligible_prose_passage(text: str) -> bool:
    """Apply the frozen content-agnostic complete-prose gate before parsing."""

    passage = text.strip()
    cjk_chars = len(CJK_RE.findall(passage))
    if not MIN_PASSAGE_CJK <= cjk_chars <= MAX_PASSAGE_CJK:
        return False
    if len(passage) > MAX_PASSAGE_CHARS or len(SENTENCE_END_RE.findall(passage)) < 2:
        return False
    if CODE_OR_URL_RE.search(passage) or QUESTION_PREFIX_RE.search(passage):
        return False
    if DEPENDENT_START_RE.search(passage) or PROSE_METADATA_RE.search(passage):
        return False
    if passage.startswith(("，", ",", "：", ":", "；", ";", "。", "、")):
        return False
    if passage.endswith(("？", "?", "：", ":")):
        return False
    if CAPTION_PREFIX_RE.search(passage) or EXTERNAL_REFERENCE_RE.search(passage):
        return False
    short_lines = sum(0 < len(CJK_RE.findall(line)) < 16 for line in passage.splitlines())
    if short_lines > 1:
        return False
    visible = visible_chars(passage)
    return bool(visible and cjk_chars / visible >= 0.5)


def complete_prose_passages(lines: list[str]) -> list[tuple[int, str]]:
    """Rejoin short DOM-split lines into non-overlapping complete prose."""

    output: list[tuple[int, str]] = []
    buffer: list[str] = []
    buffer_start = 0
    for line_number, raw_line in enumerate(lines, start=1):
        passage = raw_line.strip()
        if not passage:
            continue
        if eligible_prose_passage(passage):
            buffer.clear()
            output.append((line_number, passage))
            continue
        if CODE_OR_URL_RE.search(passage):
            buffer.clear()
            continue
        if not buffer:
            buffer_start = line_number
        buffer.append(passage)
        combined = "\n".join(buffer)
        if len(combined) > MAX_PASSAGE_CHARS:
            buffer.clear()
            continue
        if eligible_prose_passage(combined):
            output.append((buffer_start, combined))
            buffer.clear()
    return output


def render_tokens(tokens: list[DependencyToken]) -> str:
    parts: list[str] = []
    previous_ascii = False
    for token in tokens:
        current_ascii = bool(ASCII_RE.fullmatch(token.form))
        if parts and previous_ascii and current_ascii:
            parts.append(" ")
        parts.append(token.form)
        previous_ascii = current_ascii
    return "".join(parts)


def parsed_sentence(sentence: Any) -> list[DependencyToken]:
    return [
        DependencyToken(
            token_id=int(word.id),
            form=word.text,
            lemma=word.lemma or "_",
            upos=word.upos or "X",
            head=int(word.head),
            deprel=word.deprel or "dep",
        )
        for word in sentence.words
    ]


def descendants(
    token_id: int,
    children: dict[int, list[DependencyToken]],
) -> set[int]:
    output = {token_id}
    stack = [token_id]
    while stack:
        current = stack.pop()
        for child in children.get(current, []):
            if child.token_id not in output:
                output.add(child.token_id)
                stack.append(child.token_id)
    return output


def nominal_chain_depth(
    token: DependencyToken,
    by_id: dict[int, DependencyToken],
) -> int:
    depth = 0
    current = token
    while (
        current.head in by_id
        and relation(current) in NOMINAL_MODIFIER_RELATIONS
        and by_id[current.head].upos in NOMINAL_POS
    ):
        depth += 1
        current = by_id[current.head]
    return depth


def sentence_candidates(tokens: list[DependencyToken]) -> list[dict[str, Any]]:
    """Return strict candidates from one parsed sentence."""

    by_id = {token.token_id: token for token in tokens}
    children: dict[int, list[DependencyToken]] = defaultdict(list)
    for token in tokens:
        children[token.head].append(token)
    sentence_text = render_tokens(tokens)
    if CODE_OR_URL_RE.search(sentence_text):
        return []
    lexical_sentence_tokens = [
        token for token in tokens if token.upos not in {"PUNCT", "SYM"}
    ]
    sentence_has_predicate = any(token.upos == "VERB" for token in tokens)
    if not sentence_has_predicate:
        return []

    output: list[dict[str, Any]] = []
    emitted: set[tuple[int, int]] = set()
    for head in tokens:
        if head.upos not in NOMINAL_POS:
            continue
        left_modifiers = [
            child
            for child in children.get(head.token_id, [])
            if child.token_id < head.token_id
            and relation(child) in NOMINAL_MODIFIER_RELATIONS
        ]
        if not left_modifiers:
            continue
        modifier_ids: set[int] = set()
        for modifier in left_modifiers:
            modifier_ids.update(descendants(modifier.token_id, children))
        left_boundary = min(modifier_ids)
        if (left_boundary, head.token_id) in emitted:
            continue
        span_tokens = [
            token
            for token in tokens
            if left_boundary <= token.token_id <= head.token_id
        ]
        prehead_tokens = [
            token
            for token in span_tokens
            if token.token_id < head.token_id
            and token.upos not in {"PUNCT", "SYM"}
        ]
        prehead_text = render_tokens(prehead_tokens)
        punctuation_count = sum(
            token.upos in {"PUNCT", "SYM"} for token in span_tokens[:-1]
        )
        boundary_count = sum(
            token.form in BOUNDARY_FORMS or token.upos == "CCONJ"
            for token in prehead_tokens
        )
        verb_count = sum(token.upos == "VERB" for token in prehead_tokens)
        nominal_relations = [
            token
            for token in span_tokens[:-1]
            if token.head in by_id
            and left_boundary <= token.head <= head.token_id
            and relation(token) in NOMINAL_MODIFIER_RELATIONS
        ]
        sentence_context_tokens = [
            token
            for token in lexical_sentence_tokens
            if token.token_id < left_boundary or token.token_id > head.token_id
        ]
        if not (
            len(prehead_tokens) >= MIN_PREHEAD_LEXICAL_TOKENS
            and visible_chars(prehead_text) >= MIN_PREHEAD_VISIBLE_CHARS
            and len(nominal_relations) >= MIN_NOMINAL_RELATIONS
            and punctuation_count == 0
            and boundary_count == 0
            and verb_count == 0
            and sentence_context_tokens
        ):
            continue
        proper_anchors = [
            token.form
            for token in prehead_tokens
            if token.upos == "PROPN"
            and token.form.casefold() not in GENERIC_ASCII_TERMS
        ]
        numeric_anchors = [token.form for token in prehead_tokens if token.upos == "NUM"]
        output.append(
            {
                "head": head.form,
                "head_token_id": head.token_id,
                "left_boundary_token_id": left_boundary,
                "phrase": render_tokens(span_tokens),
                "prehead_text": prehead_text,
                "prehead_lexical_tokens": len(prehead_tokens),
                "prehead_visible_chars": visible_chars(prehead_text),
                "prehead_cjk_chars": len(CJK_RE.findall(prehead_text)),
                "nominal_relation_count": len(nominal_relations),
                "max_nominal_chain_depth": max(
                    (nominal_chain_depth(token, by_id) for token in nominal_relations),
                    default=0,
                ),
                "boundary_count": boundary_count,
                "punctuation_count": punctuation_count,
                "prehead_verb_count": verb_count,
                "proper_anchors": proper_anchors,
                "numeric_anchors": numeric_anchors,
                "sentence": sentence_text,
            }
        )
        emitted.add((left_boundary, head.token_id))
    return output


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--handoff",
        nargs=2,
        action="append",
        metavar=("ROOT", "ROLE"),
        required=True,
    )
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    stanza = _load_stanza()
    torch = _configure_determinism(args.seed, args.device)
    model_dir = args.model_dir.resolve()
    model_fingerprint, model_file_count = _model_fingerprint(model_dir, "zh-hans")
    options: dict[str, Any] = {
        "dir": str(model_dir),
        "lang": "zh-hans",
        "package": "gsdsimp",
        "processors": PROCESSORS,
        "use_gpu": args.device == "cuda",
        "verbose": False,
    }
    if hasattr(stanza, "DownloadMethod"):
        options["download_method"] = stanza.DownloadMethod.NONE
    nlp = stanza.Pipeline(**options)

    candidates: list[dict[str, Any]] = []
    corpus_identity: list[dict[str, Any]] = []
    document_count = 0
    covered_document_ids: set[str] = set()
    passage_count = 0
    example_text = "这个 AI 算力池面向 AI 原生时代全新算力服务需求。"
    with torch.inference_mode():
        example_document = nlp(example_text)
        example_candidates = [
            candidate
            for sentence in example_document.sentences
            for candidate in sentence_candidates(parsed_sentence(sentence))
        ]
        for raw_root, role in args.handoff:
            root = Path(raw_root).resolve()
            index_path = root / "documents.jsonl"
            records = [
                json.loads(line)
                for line in index_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            selected = [
                record for record in records if record.get("recommended_role") == role
            ]
            document_count += len(selected)
            corpus_identity.append(
                {
                    "root": str(root),
                    "role": role,
                    "documents": len(selected),
                    "manifest_sha256": sha256(root / "manifest.json"),
                    "documents_sha256": sha256(index_path),
                }
            )
            for document_index, record in enumerate(selected, start=1):
                body_path = root / str(record["body_path"])
                body = body_path.read_text(encoding="utf-8").rstrip("\n")
                content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
                if content_hash != record["content_hash"]:
                    raise ValueError(f"Body hash mismatch for {record['doc_id']}")
                print(
                    f"[nominal-chain] {role} {document_index}/{len(selected)} "
                    f"{record['doc_id']}",
                    flush=True,
                )
                passages = complete_prose_passages(body.splitlines())
                if passages:
                    covered_document_ids.add(record["doc_id"])
                for line_number, passage in passages:
                    passage_count += 1
                    parsed = nlp(passage)
                    for sentence_index, sentence in enumerate(parsed.sentences, start=1):
                        for candidate in sentence_candidates(parsed_sentence(sentence)):
                            candidates.append(
                                {
                                    "doc_id": record["doc_id"],
                                    "source": record["source"],
                                    "published_at": record["published_at"],
                                    "format_stratum": record["format_stratum"],
                                    "topic_stratum": record["topic_stratum"],
                                    "input_role": role,
                                    "line_number": line_number,
                                    "passage_sha256": hashlib.sha256(
                                        passage.encode("utf-8")
                                    ).hexdigest(),
                                    "sentence_index": sentence_index,
                                    **candidate,
                                }
                            )

    write_jsonl(output_dir / "candidates.jsonl", candidates)
    document_ids = {row["doc_id"] for row in candidates}
    sources = {row["source"] for row in candidates}
    summary = {
        "artifact_type": "deterministic-nominal-chain-integration-probe",
        "schema_version": SCHEMA_VERSION,
        "seed": args.seed,
        "device": args.device,
        "document_count": document_count,
        "covered_document_count": len(covered_document_ids),
        "passage_count": passage_count,
        "candidate_count": len(candidates),
        "candidate_document_count": len(document_ids),
        "candidate_source_count": len(sources),
        "source_instance_counts": dict(
            sorted(Counter(row["source"] for row in candidates).items())
        ),
        "source_document_counts": dict(
            sorted(
                Counter(
                    source
                    for source, _ in {
                        (row["source"], row["doc_id"]) for row in candidates
                    }
                ).items()
            )
        ),
        "frequency_gate": {
            "minimum_independent_documents": MIN_DOCUMENTS,
            "minimum_sources": MIN_SOURCES,
            "passed": len(document_ids) >= MIN_DOCUMENTS and len(sources) >= MIN_SOURCES,
        },
        "thresholds": {
            "minimum_prehead_lexical_tokens": MIN_PREHEAD_LEXICAL_TOKENS,
            "minimum_prehead_visible_chars": MIN_PREHEAD_VISIBLE_CHARS,
            "minimum_nominal_modifier_relations": MIN_NOMINAL_RELATIONS,
            "maximum_boundaries": 0,
            "maximum_prehead_verbs": 0,
            "maximum_internal_punctuation": 0,
            "requires_sentence_predicate": True,
            "requires_outside_phrase_context": True,
            "minimum_passage_cjk_chars": MIN_PASSAGE_CJK,
            "maximum_passage_cjk_chars": MAX_PASSAGE_CJK,
            "maximum_passage_characters": MAX_PASSAGE_CHARS,
            "minimum_sentence_end_marks": 2,
        },
        "reader_example": {
            "text": example_text,
            "localized": bool(example_candidates),
            "candidate_count": len(example_candidates),
            "candidates": example_candidates,
        },
        "parser": {
            "name": "stanza-universal-dependencies",
            "language": "zh-hans",
            "package": "gsdsimp",
            "processors": PROCESSORS.split(","),
            "model_fingerprint": model_fingerprint,
            "model_file_count": model_file_count,
        },
        "corpora": corpus_identity,
        "limits": [
            "The rule measures parser-derived packaging and does not judge authorship or reader dislike.",
            "Passing the frequency gate is necessary but not sufficient for an intervention.",
            "Universal Dependencies parses contain model error and are not linguistic gold labels.",
            "No body outside the requested roles is opened.",
            "Thresholds and boundary forms are frozen before corpus outcomes are inspected.",
            "Only non-overlapping complete prose passages pass to Stanza; code and long formatting noise are filtered before parsing.",
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
