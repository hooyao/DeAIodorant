"""Save the assistant's source-anchored feasibility cases without new inference."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUN = BASE / "reproduction-02"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def span(body, quote):
    if body.count(quote) != 1:
        raise ValueError("Evidence must match exactly once")
    start = body.index(quote)
    return {"start_char": start, "end_char": start + len(quote), "evidence_quote": quote}


specifications = [
    {
        "case_id": "doc-03-awkward", "alias": "doc-03", "sentence_index": 12,
        "role": "awkward_construction", "word_ids": [11, 13, 14, 15, 16, 24],
        "focus": "无法确定不确定",
        "reading_observation": "The captured sentence stacks inability to determine and uncertainty with a repeated predicate; the relation between the two is difficult to interpret locally. This is a concrete wording concern, not a consequence of the article's technical topic or connector count.",
        "parser_observation": "Router is nsubj of 无法; the first 确定 is its xcomp, and the second 确定 is another xcomp under the first, with 不 as advmod. The parser supplies a complete dependency analysis for the awkward sequence.",
        "discrimination_limit": "The nested structure can navigate the repeated predicates but does not say whether they express an intended proposition, an accidental repetition, or an editorial/capture problem. Its grammatical-looking tree does not establish fluent wording.",
        "confidence": "high", "support": [],
    },
    {
        "case_id": "doc-03-control", "alias": "doc-03", "sentence_index": 26,
        "role": "ordinary_list_and_shared_actor", "word_ids": [1, 2, 7, 12, 13, 14, 29],
        "focus": "把路由当成一个集合预测问题",
        "reading_observation": "This is the second item in an explicitly announced two-part explanation. The team performing the actions is recoverable from the preceding first-person introduction; repeating that actor in every action would not be obligatory.",
        "parser_observation": "The parser treats the list ordinal 二 as nsubj of 是, tags 设计 as NOUN, and splits the technical word 路由 into 路 (NOUN, obl:patient) and 由 (VERB, advcl), with 当成 as xcomp of 由.",
        "discrimination_limit": "A coherent list contains a clear technical-token segmentation problem in the parser. Dependency anomalies or missing subjects on its action predicates cannot be equated with a source-language defect.",
        "confidence": "high", "support": ["我们做了两件比较特别的事情："],
    },
    {
        "case_id": "doc-05-awkward", "alias": "doc-05", "sentence_index": 74,
        "role": "awkward_reference_and_predication", "word_ids": [6, 8, 9, 17, 19, 21, 29, 39, 42],
        "focus": "有一些用户还是对\nAnthropic 近期产品策略与沟通的不满",
        "reading_observation": "The concessive construction shifts between comments, users, and a nominal expression of dissatisfaction. The final assertion of an indirectly related context does not clearly resolve which preceding material bears that relation. Extractor line breaks remain visible, but the concern also concerns predication and reference across the words themselves.",
        "parser_observation": "The parser labels 有些 as VERB, attaches 评论 as nsubj of 有, turns 用户 into nmod of 不满, and places 不满 as obj of 有. It independently attaches 具有 as ccomp of the sentence-level 是 and 语境 as its obj.",
        "discrimination_limit": "These attachments accommodate the awkward sequence without diagnosing the shifting referent or supplying the intended discourse link. The parser cannot establish what additional premise, if any, the author intended. No absent information is invented.",
        "confidence": "high", "support": [],
    },
    {
        "case_id": "doc-05-control", "alias": "doc-05", "sentence_index": 60,
        "role": "ordinary_nominal_list_item", "word_ids": [1, 2, 3, 7],
        "focus": "其次是新增的一系列技能\n。",
        "reading_observation": "This is a coherent second item in the explanation of ways to extend the product's capabilities. A nominal list item does not need an independently restated actor or a verb-object sequence.",
        "parser_observation": "技能 is the root, 是 is cop, and 其次 is represented as NOUN/nsubj. The newline before the punctuation is retained in the source slice and does not split this parser sentence.",
        "discrimination_limit": "A nominal root or an unconventional analysis of a discourse ordinal does not establish missing syntax. This control also shows that not every extractor line break creates a parser boundary failure.",
        "confidence": "high", "support": ["首先是连接器。"],
    },
    {
        "case_id": "doc-11-awkward", "alias": "doc-11", "sentence_index": 29,
        "role": "awkward_clause_boundary_in_captured_text", "word_ids": [5, 13, 15, 17, 20, 22, 23, 30, 34, 45],
        "focus": "其主要依赖计算组进行资源隔离通过将计算层与存储层解耦",
        "reading_observation": "The captured text runs the resource-isolation operation directly into a following means clause, leaving the boundary and attachment of 通过 unclear on first reading. This observation does not establish whether the source author or capture process caused the missing separation.",
        "parser_observation": "Stanza merges the preceding heading with the prose. Heading word 优势 becomes nsubj of root 模式. 进行 is parataxis under 模式, and 解耦 is ccomp of 进行 with 通过 as case. The rest of the passage receives ordinary dependency edges as well.",
        "discrimination_limit": "The parser offers one attachment without deciding whether a clause boundary is missing. Heading fusion changes the root and subject analysis before any prose-quality interpretation is attempted.",
        "confidence": "high", "support": [],
    },
    {
        "case_id": "doc-11-control", "alias": "doc-11", "sentence_index": 22,
        "role": "ordinary_discourse_ellipsis", "word_ids": [2, 3, 4, 13, 20],
        "focus": "最终采用后者作为临时方案，但仍未根本解决成本与可用性之间的矛盾。",
        "reading_observation": "The preceding paragraph names the team and evaluates two alternatives. The adopted latter alternative and the team's omitted actor are recoverable in context, so an overt subject is not obligatory here.",
        "parser_observation": "解决 is root and 采用 is its advcl; neither has an overt nsubj dependent. 后者 is instead attached as nsubj to 作 inside the analysis of 作为.",
        "discrimination_limit": "Absence of nsubj on the main action is compatible with coherent Chinese discourse ellipsis. Stanza supplies no discourse-resolution evidence that would distinguish this control from an actually unresolved reference.",
        "confidence": "high", "support": ["团队曾评估两种路径：", "跨可用区副本分布："],
    },
]

documents = {}
for alias in ("doc-03", "doc-05", "doc-11"):
    documents[alias] = {
        "body": (RUN / alias / "body.txt").read_bytes().decode("utf-8"),
        "annotations": json.loads((RUN / alias / "annotations.json").read_text(encoding="utf-8")),
    }

cases = []
for specification in specifications:
    row = dict(specification)
    document = documents[row["alias"]]
    sentence = document["annotations"]["sentences"][row.pop("sentence_index") - 1]
    word_ids = row.pop("word_ids")
    row["evidence"] = span(document["body"], row.pop("focus"))
    row["support_evidence"] = [span(document["body"], quote) for quote in row.pop("support")]
    row["sentence_id"] = sentence["sentence_id"]
    row["parser_sentence_source"] = {key: sentence[key] for key in ("start_char", "end_char", "source_text")}
    row["selected_word_records"] = [word for word in sentence["words"] if word["id"] in word_ids]
    row["human_gold"] = False
    cases.append(row)

segmentation = documents["doc-11"]["annotations"]["sentences"][44]
segmentation_case = {
    "alias": "doc-11", "sentence_id": segmentation["sentence_id"],
    "evidence": span(documents["doc-11"]["body"], ";\n复制代码\n04 自助化、精细化的资源管理\n为了优化资源管理与运维流程"),
    "source_start_char": segmentation["start_char"], "source_end_char": segmentation["end_char"],
    "observation": "One parser sentence spans the SQL introduction, the full code block, the copy-code label, the next heading, and the next prose sentence. Foreign-word tokens join source lines and the graph attaches the following prose to the code-introduction root. This is a capture/segmentation confound, not evidence that the prose has missing syntax.",
}

surface_cases = []
for alias, sentence_index, token_id in (("doc-03", 32, 6), ("doc-05", 77, 5),
                                         ("doc-11", 36, 15), ("doc-11", 45, 12)):
    sentence = documents[alias]["annotations"]["sentences"][sentence_index - 1]
    token = next(token for token in sentence["tokens"] if token["ids"] == [token_id])
    surface_cases.append({"alias": alias, "sentence_id": sentence["sentence_id"],
                          "token": token,
                          "interpretation": "Parser surface transformation retained alongside the exact source slice; not a source-language error label."})

write(BASE / "inspection.json", {
    "protocol": "contrast-syntax-feasibility-1.0", "reviewer": "context_metrics_check",
    "reviewer_kind": "assistant_case_inspection", "model_identity": None,
    "human_gold": False, "semantic_reviews_read": False,
    "parse_run": RUN.name, "whole_bodies_read": ["doc-03", "doc-05", "doc-11"],
    "selection": "Purposive full-document selection fixed before this parser run; cases selected after reading these bodies and annotations.",
    "cases": cases, "segmentation_case": segmentation_case,
    "token_surface_cases": surface_cases,
    "conclusion": "Useful for source-anchored navigation and inspection of proposed attachments; these six purposive cases do not establish reliable automatic distinction between reading defects and ordinary Chinese constructions.",
})

write(BASE / "monitoring.json", {
    "method": "Direct PID/process CPU inspection, completed annotation artifacts, run-state counts, and final exec completion; no watcher-only inference.",
    "observations": [
        {"attempt": "initial", "pid": 57480, "status": "loading_model", "cpu_seconds": 15.33, "working_set_bytes": 361005056},
        {"attempt": "initial", "pid": 57480, "status": "process_absent", "stale_state": "parsing doc-03, completed_documents 0"},
        {"attempt": "retry-01", "pid": 47880, "status": "loading_model", "completed_documents": 0},
        {"attempt": "retry-01", "pid": 47880, "status": "parsing doc-05", "completed_documents": 1, "cpu_seconds": 27.38, "working_set_bytes": 1366757376},
        {"attempt": "retry-01", "pid": 47880, "status": "parsing doc-11", "completed_documents": 2, "cpu_seconds": 55.70, "working_set_bytes": 1844023296},
        {"attempt": "retry-01", "pid": 47880, "status": "complete", "completed_documents": 3, "exec_exit_code": 0},
        {"attempt": "reproduction-02", "pid": 24076, "status": "loading_model", "completed_documents": 0},
        {"attempt": "reproduction-02", "pid": 24076, "status": "complete", "completed_documents": 3, "exec_exit_code": 0},
    ],
    "initial_failure": "The initial Windows os.execve seeded relaunch detached from the tool capture and its child stopped before producing document annotations. The exact exception was not captured. Replacing it with waited subprocess.run restored observable completion; this does not establish the unobserved original exception cause.",
})

write(BASE / "run-index.json", {
    "protocol": "contrast-syntax-feasibility-1.0", "ready_run": RUN.name,
    "manifest": f"{RUN.name}/manifest.json", "inspection": "inspection.json",
    "failed_initial_attempt_preserved": True, "successful_earlier_run_preserved": "retry-01",
})

print(json.dumps({"documents": len(documents), "inspected_cases": len(cases), "segmentation_cases": 1}))
