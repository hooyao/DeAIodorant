"""Prepare a low-burden raw-passage reader-friction screening round."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


SCHEMA_VERSION = "deaiodorant-reader-friction-screen-1.0"
PROTOCOL_VERSION = "raw-passage-friction-screen-development-1.0"
DEFAULT_SEED = 2026082202
PER_STRATUM = 4

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
SENTENCE_END_RE = re.compile(r"[。！？]")
URL_RE = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
QUESTION_PREFIX_RE = re.compile(
    r"^(?:InfoQ|机器之心|Q\d*|问|记者|采访者|主持人)[：:]",
    re.IGNORECASE,
)
CAPTION_PREFIX_RE = re.compile(
    r"^(?:图|表|代码|清单|公式|注)\s*(?:\d+|[一二三四五六七八九十]+)?[：:．.、\s]"
)
DEPENDENT_START_RE = re.compile(
    r"^(?:也|还)(?:提供|推出|提出|表示|认为|显示|说明|成为|有|是|可以|能够|会|将|让|使)"
)
EXTERNAL_REFERENCE_RE = re.compile(
    r"(?:上图|下图|如图|从图|"
    r"图\s*[0-9一二三四五六七八九十]+(?:[.．][A-Za-z0-9]+)?\s*(?:中|所示)|"
    r"算法\s*\d+\s*(?:给出|所示)|(?:图示|算法|结果)见下)"
)

LENGTH_BANDS = (
    ("short", 120, 159),
    ("medium", 160, 199),
    ("long", 200, 360),
)
SOURCES = ("infoq", "jiqizhixin")

# These documents have already been exposed through a reader rating,
# intervention, or explicit style observation. Some do not occur in the
# handoff, but retaining the complete exclusion list makes the boundary clear.
PRIOR_EXPOSED_DOC_IDS = frozenset(
    {
        "0431c592d5de8246cebcb8e2",
        "10b4ff947e750938d62a417a",
        "2e209708bce31c124797ce6c",
        "3c33241e2bb2fd68fb3c6147",
        "3c60dc0a981b686870095450",
        "44aa81958a6c585ee8c06847",
        "44ff5a1d8bda9c7b50f6290f",
        "48bda219eb0776f623161899",
        "51ad0427b938c45e289e9d1a",
        "55a8c05716103aaced6ecf7f",
        "646b73aae2b0dc8f311a9f0c",
        "7103a1b4c0cb80218a653a03",
        "9f693cf901d640ffb7312bd9",
        "a127f5baf364930a89fb4005",
        "a76e84a2a44062b098288efc",
        "b186cdd4f9004e0413395bf3",
        "b77b09a419c1631227112f0c",
        "c4f3d04d7db01e65460fb2dd",
        "d4407ed937d0f78f325c3fbd",
        "ed4b0601b5481ee4065a337a",
    }
)


@dataclass(frozen=True)
class Candidate:
    doc_id: str
    source: str
    published_at: str
    line_number: int
    passage: str
    cjk_chars: int
    length_band: str

    @property
    def passage_sha256(self) -> str:
        return hashlib.sha256(self.passage.encode("utf-8")).hexdigest()


LABEL_CONFIG = """<View>
  <Header value="原文阅读体验筛选"/>
  <Text name="instruction" value="请只按第一感受作答：读完这段原文后，你有多愿意继续往下读？不需要判断是不是 AI 写的，也不需要分析语言特征。"/>
  <Text name="passage" value="$passage"/>
  <Choices name="willingness" toName="passage" choice="single-radio" required="true" showInline="false">
    <Choice value="很愿意继续读"/>
    <Choice value="还算愿意继续读"/>
    <Choice value="不太愿意继续读"/>
    <Choice value="完全不愿意继续读"/>
  </Choices>
  <Header value="可选评论"/>
  <TextArea name="comment" toName="passage" placeholder="可以留空；若有特别影响阅读的地方，也可以随手写一句。" rows="2"/>
</View>
"""


def read_jsonl(path: Path) -> list[dict[str, object]]:
    """Read a UTF-8 JSON Lines file."""

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def length_band(cjk_chars: int) -> str | None:
    """Return the frozen passage-length stratum for a CJK character count."""

    for name, lower, upper in LENGTH_BANDS:
        if lower <= cjk_chars <= upper:
            return name
    return None


def is_eligible_passage(text: str) -> tuple[bool, int, str | None]:
    """Apply content-agnostic completeness and formatting gates."""

    passage = text.strip()
    cjk_chars = len(CJK_RE.findall(passage))
    band = length_band(cjk_chars)
    if band is None:
        return False, cjk_chars, None
    if len(passage) > 520 or len(SENTENCE_END_RE.findall(passage)) < 2:
        return False, cjk_chars, band
    if URL_RE.search(passage) or QUESTION_PREFIX_RE.search(passage):
        return False, cjk_chars, band
    if DEPENDENT_START_RE.search(passage):
        return False, cjk_chars, band
    if passage.startswith(("，", ",", "：", ":", "；", ";", "。", "、")):
        return False, cjk_chars, band
    if passage.endswith(("？", "?", "：", ":")):
        return False, cjk_chars, band
    if CAPTION_PREFIX_RE.search(passage) or EXTERNAL_REFERENCE_RE.search(passage):
        return False, cjk_chars, band
    visible_chars = sum(not char.isspace() for char in passage)
    if not visible_chars or cjk_chars / visible_chars < 0.5:
        return False, cjk_chars, band
    return True, cjk_chars, band


def collect_candidates(pool_path: Path) -> list[Candidate]:
    """Collect eligible passages without scoring their linguistic style."""

    candidates: list[Candidate] = []
    for record in read_jsonl(pool_path):
        doc_id = str(record["doc_id"])
        if record.get("period") != "transition":
            continue
        if doc_id in PRIOR_EXPOSED_DOC_IDS:
            continue
        source = str(record["source"])
        if source not in SOURCES:
            continue
        body_path = Path(str(record["body_path"]))
        body_bytes = body_path.read_bytes()
        observed_hash = hashlib.sha256(body_bytes).hexdigest()
        if observed_hash != record["content_hash"]:
            raise ValueError(f"Content hash mismatch for {doc_id}")
        body = body_bytes.decode("utf-8")
        for line_number, raw_line in enumerate(body.splitlines(), start=1):
            passage = raw_line.strip()
            eligible, cjk_chars, band = is_eligible_passage(passage)
            if not eligible or band is None:
                continue
            candidates.append(
                Candidate(
                    doc_id=doc_id,
                    source=source,
                    published_at=str(record["published_at"]),
                    line_number=line_number,
                    passage=passage,
                    cjk_chars=cjk_chars,
                    length_band=band,
                )
            )
    return candidates


def select_candidates(candidates: list[Candidate], seed: int) -> list[Candidate]:
    """Select a source- and length-balanced set with one passage per document."""

    grouped: dict[tuple[str, str], list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[(candidate.source, candidate.length_band)].append(candidate)

    rng = random.Random(seed)
    for stratum in grouped.values():
        rng.shuffle(stratum)

    selected: list[Candidate] = []
    selected_docs: set[str] = set()
    for source in SOURCES:
        # Fill the rare longest stratum first so the one-document rule cannot
        # consume its eligible documents through a shorter stratum.
        for band, _, _ in reversed(LENGTH_BANDS):
            chosen: list[Candidate] = []
            stratum_docs: set[str] = set()
            for candidate in grouped[(source, band)]:
                if candidate.doc_id in selected_docs | stratum_docs:
                    continue
                chosen.append(candidate)
                stratum_docs.add(candidate.doc_id)
                if len(chosen) == PER_STRATUM:
                    break
            if len(chosen) < PER_STRATUM:
                raise ValueError(
                    f"Not enough documents for {source}/{band}: {len(chosen)}"
                )
            selected.extend(chosen)
            selected_docs.update(candidate.doc_id for candidate in chosen)

    rng.shuffle(selected)
    return selected


def build_artifacts(
    pool_path: Path, seed: int
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build Label Studio tasks and a frozen protocol manifest."""

    candidates = collect_candidates(pool_path)
    selected = select_candidates(candidates, seed)
    priority_order = sorted(
        selected,
        key=lambda candidate: hashlib.sha256(
            f"{seed}:{candidate.doc_id}:{candidate.line_number}".encode("ascii")
        ).hexdigest(),
    )
    priority_by_passage = {
        (candidate.doc_id, candidate.line_number): rank
        for rank, candidate in enumerate(priority_order, start=1)
    }

    tasks: list[dict[str, object]] = []
    passages: list[dict[str, object]] = []
    for task_number, candidate in enumerate(selected, start=1):
        followup_priority = priority_by_passage[
            (candidate.doc_id, candidate.line_number)
        ]
        tasks.append(
            {
                "data": {
                    "task_number": task_number,
                    "passage": candidate.passage,
                },
                "meta": {
                    "doc_id": candidate.doc_id,
                    "source": candidate.source,
                    "published_at": candidate.published_at,
                    "line_number": candidate.line_number,
                    "length_band": candidate.length_band,
                    "cjk_chars": candidate.cjk_chars,
                    "passage_sha256": candidate.passage_sha256,
                    "followup_priority": followup_priority,
                },
            }
        )
        passages.append(
            {
                "task_number": task_number,
                "doc_id": candidate.doc_id,
                "source": candidate.source,
                "published_at": candidate.published_at,
                "line_number": candidate.line_number,
                "length_band": candidate.length_band,
                "cjk_chars": candidate.cjk_chars,
                "passage_sha256": candidate.passage_sha256,
                "followup_priority": followup_priority,
            }
        )

    protocol = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "status": "frozen_before_outcomes",
        "frozen_at": "2026-08-22",
        "seed": seed,
        "role": "development_screen_not_validation",
        "reader_question": (
            "After reading this original passage, how willing are you to continue?"
        ),
        "source_policy": {
            "period": "transition",
            "sources": list(SOURCES),
            "prior_reader_exposed_documents_excluded": True,
            "style_feature_scores_used_for_selection": False,
            "one_passage_per_document": True,
        },
        "sampling_policy": {
            "per_source_and_length_stratum": PER_STRATUM,
            "length_bands_cjk_chars": {
                name: [lower, upper] for name, lower, upper in LENGTH_BANDS
            },
            "passage_count": len(selected),
        },
        "followup_gate": {
            "eligible_ratings": ["不太愿意继续读", "完全不愿意继续读"],
            "minimum_eligible_for_intervention": 4,
            "maximum_intervention_passages": 8,
            "if_fewer_than_minimum": (
                "Run another fresh raw-passage screen; do not intensify edits "
                "on acceptable passages."
            ),
            "if_more_than_maximum": (
                "Take the lowest rating first, then use the frozen follow-up "
                "priority; do not use comments for selection."
            ),
            "comments_used_for_selection": False,
        },
        "candidate_diagnostics": {
            "eligible_passage_count": len(candidates),
            "eligible_document_count": len({item.doc_id for item in candidates}),
            "eligible_by_stratum": dict(
                sorted(
                    Counter(
                        f"{item.source}/{item.length_band}" for item in candidates
                    ).items()
                )
            ),
        },
        "passages": passages,
    }
    return tasks, protocol


def write_json(path: Path, value: object) -> None:
    """Write stable pretty-printed UTF-8 JSON."""

    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {args.output_dir}")
    tasks, protocol = build_artifacts(args.pool, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "tasks.json", tasks)
    write_json(args.output_dir / "protocol.json", protocol)
    (args.output_dir / "label_config.xml").write_text(
        LABEL_CONFIG, encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir.resolve()),
                "protocol_version": PROTOCOL_VERSION,
                "task_count": len(tasks),
                "candidate_diagnostics": protocol["candidate_diagnostics"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
