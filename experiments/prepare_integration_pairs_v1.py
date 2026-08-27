"""Prepare a post-only proposition-decompression reader intervention."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from prepare_reader_friction_screen_v3 import complete_segments


SCHEMA_VERSION = "deaiodorant-integration-pairs-1.0"
PROTOCOL_VERSION = "proposition-decompression-development-1.0"
DEFAULT_SEED = 2026082705
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?%?")
SENTENCE_END_RE = re.compile(r"[。！？!?]")


@dataclass(frozen=True)
class ClaimCheck:
    claim_id: str
    description: str
    original_support: str
    revised_support: str


@dataclass(frozen=True)
class PairSpec:
    pair_id: str
    doc_id: str
    target_line: int
    original_sha256: str
    revised: str
    claims: tuple[ClaimCheck, ...]
    locked_literals: tuple[str, ...]
    voice_anchors: tuple[str, ...]


def claim(
    claim_id: str,
    description: str,
    original_support: str,
    revised_support: str,
) -> ClaimCheck:
    """Create one explicit proposition-preservation check."""

    return ClaimCheck(claim_id, description, original_support, revised_support)


SPECS = (
    PairSpec(
        pair_id="integration-v1-01",
        doc_id="4e2108f7b04c3847a564bfd4",
        target_line=1,
        original_sha256="c8bcebf57c39bea4e94e072c354682dfd9ae6eb5597e087fcd8bc367c7ed5ac5",
        revised=(
            "9 月 25 日，奇富科技首席算法科学家费浩峻在云栖大会“新‘模’力 新点金：金融大模型技术峰会”上，"
            "基于公司丰富的落地实践经验，系统阐述了金融大模型的落地逻辑。他提出告别对参数规模的盲目"
            "追逐，转而采用“做小做强”的路径，推动金融 AI 从“堆人力、堆模型”的传统范式迈向“聚智能、"
            "见个体”的价值升级。这一实践为行业提供了金融大模型务实落地的清晰样本。\n"
            "费浩峻指出，传统机器学习阶段的金融 AI 面临两大核心制约。第一，它高度依赖人工特征工程，"
            "模型难以直接处理真实世界中复杂、非结构化的数据。第二，模型的泛化能力较差，不同业务需要"
            "定制不同模型，导致迭代成本高、响应慢。"
        ),
        claims=(
            claim(
                "c01",
                "The dated conference talk and speaker attribution are retained.",
                "9 月 25 日，在云栖大会",
                "9 月 25 日，奇富科技首席算法科学家费浩峻在云栖大会",
            ),
            claim(
                "c02",
                "The small-and-strong path replaces parameter-scale pursuit.",
                "告别参数规模的盲目追逐",
                "告别对参数规模的盲目追逐",
            ),
            claim(
                "c03",
                "Both traditional-machine-learning constraints are retained.",
                "一是高度依赖人工特征工程",
                "第一，它高度依赖人工特征工程",
            ),
        ),
        locked_literals=(
            "奇富科技",
            "费浩峻",
            "金融 AI",
            "堆人力、堆模型",
            "聚智能、见个体",
        ),
        voice_anchors=("做小做强", "清晰样本"),
    ),
    PairSpec(
        pair_id="integration-v1-02",
        doc_id="8873215c1410ad3babd84bbb",
        target_line=1,
        original_sha256="13c48e285248c4b391efb361155a4b4899a9f8216f0be36f0ca8ed44eb5bd107",
        revised=(
            "人工智能竞争持续升温，围绕 DeepMind、OpenAI 与 Anthropic 的讨论也在变化。人们关注的"
            "不再只有“谁的模型更强”，还包括一个更深层的问题：顶级 AI 实验室如何组织研究？它们怎样"
            "选择技术路线，又如何在算力、资本与安全之间做出长期取舍？\n"
            "近日，InfoQ 采访了《哈萨比斯：谷歌 AI 之脑》（TheInfinityMachine）的作者塞巴斯蒂安·马拉比"
            "（Sebastian Mallaby）。他是知名科技史学家和金融史学家。我们尝试借助他更接近“内部观察者”"
            "的视角，重新理解 DeepMind 的成长逻辑，以及它与 OpenAI、Anthropic 之间真正的结构性差异。"
        ),
        claims=(
            claim(
                "c01",
                "Discussion expands beyond model strength to laboratory organization.",
                "已经不再只是“谁的模型更强”的问题",
                "不再只有“谁的模型更强”",
            ),
            claim(
                "c02",
                "Research, technical-route, compute, capital, and safety choices remain.",
                "如何组织研究、选择技术路线",
                "如何组织研究",
            ),
            claim(
                "c03",
                "The interview source and comparative objective remain attributed.",
                "塞巴斯蒂安·马拉比（Sebastian Mallaby）的采访",
                "作者塞巴斯蒂安·马拉比（Sebastian Mallaby）",
            ),
        ),
        locked_literals=(
            "DeepMind",
            "OpenAI",
            "Anthropic",
            "TheInfinityMachine",
            "Sebastian Mallaby",
        ),
        voice_anchors=("内部观察者", "真正的结构性差异"),
    ),
    PairSpec(
        pair_id="integration-v1-03",
        doc_id="24fb6134577093ddcff37689",
        target_line=8,
        original_sha256="734fa3ee768083c4ab18d332a7b67ccbf94682b76a0baff3e72a32feec28681a",
        revised=(
            "围绕上述转变过程，项铁尧重点介绍了商汤大装置前瞻打造的核心产品——AI 算力池。\n"
            "据了解，AI 算力池采用“三明治”水平分层架构，以满足 AI 原生时代全新的算力服务需求。"
            "底层是经过高度优化的计算、网络和存储基础设施。中间层采用全新的虚拟集群技术。上层是一套"
            "完整的 PaaS 产品体系，涵盖开发机、训练平台、部署平台和 Agentic Engine。这套架构全面杜绝"
            "不同产品之间的资源孤岛问题。"
        ),
        claims=(
            claim(
                "c01",
                "The AI compute pool remains the named core product.",
                "核心产品——AI 算力池",
                "核心产品——AI 算力池",
            ),
            claim(
                "c02",
                "All three architecture layers and their components remain.",
                "从底层高度优化的计算网络存储基础设施",
                "底层是经过高度优化的计算、网络和存储基础设施",
            ),
            claim(
                "c03",
                "The architecture fully eliminates cross-product resource silos.",
                "全面杜绝不同产品之间的资源孤岛问题",
                "全面杜绝不同产品之间的资源孤岛问题",
            ),
        ),
        locked_literals=(
            "项铁尧",
            "商汤大装置",
            "AI 算力池",
            "PaaS",
            "Agentic Engine",
        ),
        voice_anchors=("三明治", "资源孤岛"),
    ),
    PairSpec(
        pair_id="integration-v1-04",
        doc_id="610ba7a9b468d78a3d59def1",
        target_line=18,
        original_sha256="9ba357d1fde037a756b4767f84a97d333ed7d03b86aa779280d0f4b68312a3c4",
        revised=(
            "为解决上述问题，论文提出了全新的理论框架 CoT-Flow。它把离散的推理步骤重新概念化为连续的"
            "概率流。\n"
            "CoT-Flow 受整流流（Rectified Flow）理论启发。它把推理过程看作一次连续传输：模型的信息状态"
            "从初始问题出发，平滑地抵达真实答案。在这一视角下，每个推理步骤都是推动过程接近目标的“速度"
            "向量”。该框架据此严格量化每一步为最终正确答案带来的瞬时信息增益。\n"
            "基于这一指标，论文实现了采用对比解码的贪心策略。该策略使回答长度平均减少 10% ~ 15%，并在 "
            "AIME24 上将准确率最高提高 15.9%。\n"
            "论文还从同一框架导出 RL loss。与 GRPO、VeriFree 等 baseline 相比，它在 AIME24、GPQA 等 "
            "benchmark 上取得接近或更高的准确率，同时将长度压缩 11% ~ 37%，并使训练加速 32%。"
        ),
        claims=(
            claim(
                "c01",
                "CoT-Flow maps discrete reasoning steps to a continuous probability flow.",
                "将离散的推理步骤重新概念化为连续的概率流",
                "把离散的推理步骤重新概念化为连续的概率流",
            ),
            claim(
                "c02",
                "Velocity vectors quantify instantaneous information gain.",
                "瞬时信息增益",
                "瞬时信息增益",
            ),
            claim(
                "c03",
                "All decoding and RL-loss outcome ranges are retained.",
                "回答长度平均减少 10% ~ 15%",
                "回答长度平均减少 10% ~ 15%",
            ),
        ),
        locked_literals=(
            "CoT-Flow",
            "Rectified Flow",
            "AIME24",
            "RL loss",
            "GRPO",
            "VeriFree",
            "GPQA",
        ),
        voice_anchors=("速度向量", "真实答案"),
    ),
    PairSpec(
        pair_id="integration-v1-05",
        doc_id="75583336dc40b896d68598d0",
        target_line=11,
        original_sha256="9a48caad6e53a5331608811e48050cbf9acf145a249bd6da264ced44dbd95bf9",
        revised=(
            "论文提出了 CoreCodeBench，用于细粒度评测大语言模型的编程能力。该基准利用 COREPIPE 框架，"
            "从 12 个 Python 开源库中自动生成 1,524 个结构化任务。这些任务覆盖开发、修复、测试驱动开发"
            "等多种软件工程场景，可以区分不同的认知负载，并动态调整任务复杂度。\n"
            "实验显示，CoreCodeBench 的有效性达到 78.55%，显著优于现有方法。结果还揭示了模型在不同任务"
            "类型上的能力错配。\n"
            "CoreCodeBench 也支持组合多个任务进行评测，以模拟真实开发环境。它具备高自动化、强鲁棒性和"
            "可复现性，为代码智能评测提供了更全面、精准的框架。"
        ),
        claims=(
            claim(
                "c01",
                "The benchmark generates the same task count from the same libraries.",
                "从 12 个 Python 开源库自动生成 1,524 个结构化任务",
                "从 12 个 Python 开源库中自动生成 1,524 个结构化任务",
            ),
            claim(
                "c02",
                "The effectiveness result and ability mismatch remain.",
                "其有效性达 78.55%",
                "有效性达到 78.55%",
            ),
            claim(
                "c03",
                "Multi-task evaluation and all three framework properties remain.",
                "支持多任务组合评测",
                "支持组合多个任务进行评测",
            ),
        ),
        locked_literals=("CoreCodeBench", "COREPIPE", "Python", "78.55%"),
        voice_anchors=("高自动化", "强鲁棒性", "可复现性"),
    ),
    PairSpec(
        pair_id="integration-v1-06",
        doc_id="69566776f457ecf4c98ecbe0",
        target_line=34,
        original_sha256="59998b2b72fedf084cb859f82ecf0f4b7a935f60b84abb99c9859e487f5cafd4",
        revised=(
            "美团指标平台是美团内部自建的元数据及模型管理平台，服务于数据研发和数据产品团队。它提供产品"
            "能力与方法论，覆盖业务全域下的数仓规划、指标维度统一管理、标准建模以及指标自动生产。\n"
            "美团 BI 平台是公司级一站式数据分析平台，面向数据产运营、研发、分析师和管理者等多种角色。"
            "用户可以便捷查询多种数据源，灵活开展数据可视化分析，并快速搭建数据报表和数据监控。该平台"
            "提供安全、高效、敏捷的数据分析服务。"
        ),
        claims=(
            claim(
                "c01",
                "The indicator platform retains its audience and four capabilities.",
                "面向数据研发、数据产品团队",
                "服务于数据研发和数据产品团队",
            ),
            claim(
                "c02",
                "The BI platform retains all named user roles and functions.",
                "面向数据产运营、研发、分析师、管理者等多种角色",
                "面向数据产运营、研发、分析师和管理者等多种角色",
            ),
            claim(
                "c03",
                "Safe, efficient, and agile analytics service remains.",
                "安全、高效、敏捷的数据分析服务",
                "安全、高效、敏捷的数据分析服务",
            ),
        ),
        locked_literals=("美团指标平台", "美团 BI 平台", "数据产运营"),
        voice_anchors=("安全、高效、敏捷",),
    ),
)

IDENTICAL_CONTROL = {
    "pair_id": "integration-v1-identical-control",
    "doc_id": "66ba5cd023c8f199f1601f59",
    "target_line": 9,
    "original_sha256": "b1b2fe8b62b5b21e5d5fffd6f32a3247a4389eb522d24f115fd53696582baae1",
}
TASK_ORDER = (
    "integration-v1-04",
    "integration-v1-01",
    "integration-v1-06",
    "integration-v1-identical-control",
    "integration-v1-02",
    "integration-v1-05",
    "integration-v1-03",
    "integration-v1-01-mirror",
)
ORIGINAL_SIDES = {
    "integration-v1-01": "A",
    "integration-v1-02": "B",
    "integration-v1-03": "A",
    "integration-v1-04": "B",
    "integration-v1-05": "A",
    "integration-v1-06": "B",
    "integration-v1-01-mirror": "B",
}

LABEL_CONFIG = """<View>
  <Header value="技术文本组合难度比较"/>
  <Text name="instruction" value="下面两个版本表达同一内容。哪个版本让你更愿意继续读？有些题两版可能完全相同；确实没有差别时请直接选第三项。不需要判断是不是 AI 写的，也不需要分析原因。"/>
  <Header value="A"/>
  <Text name="version_a" value="$version_a"/>
  <Header value="B"/>
  <Text name="version_b" value="$version_b"/>
  <Choices name="preference" toName="version_a" choice="single-radio" required="true" showInline="false">
    <Choice value="A，更愿意继续读"/>
    <Choice value="B，更愿意继续读"/>
    <Choice value="没有明显差别（都还行或都不好）"/>
  </Choices>
  <Header value="可选评论"/>
  <TextArea name="comment" toName="version_a" placeholder="可以留空；如果某一处特别像‘词拧在一起’，可以随手指出。" rows="2"/>
</View>
"""


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_sources(handoff_root: Path) -> tuple[dict[str, dict], dict[str, str]]:
    """Load exact selected passages and validate handoff body hashes."""

    records = [
        json.loads(line)
        for line in (handoff_root / "documents.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    metadata = {str(record["doc_id"]): record for record in records}
    requests = [
        (spec.doc_id, spec.target_line, spec.original_sha256, spec.pair_id)
        for spec in SPECS
    ] + [
        (
            IDENTICAL_CONTROL["doc_id"],
            IDENTICAL_CONTROL["target_line"],
            IDENTICAL_CONTROL["original_sha256"],
            IDENTICAL_CONTROL["pair_id"],
        )
    ]
    passages: dict[str, str] = {}
    for doc_id, line_number, expected_hash, pair_id in requests:
        record = metadata[str(doc_id)]
        if str(record["published_at"]) < "2025-07-01":
            raise ValueError(f"Non-post source document: {doc_id}")
        body_path = handoff_root / str(record["body_path"])
        body = body_path.read_text(encoding="utf-8").rstrip("\n")
        if _sha256_text(body) != record["content_hash"]:
            raise ValueError(f"Source body hash mismatch for {doc_id}")
        segments = dict(complete_segments(body.splitlines()))
        passage = segments[int(line_number)]
        if _sha256_text(passage) != expected_hash:
            raise ValueError(f"Passage hash mismatch for {pair_id}")
        passages[str(pair_id)] = passage
    return metadata, passages


def validate_pair(spec: PairSpec, original: str) -> dict[str, object]:
    """Apply deterministic preservation and bounded-decompression gates."""

    if original == spec.revised:
        raise ValueError(f"No intervention for {spec.pair_id}")
    original_numbers = NUMBER_RE.findall(original)
    revised_numbers = NUMBER_RE.findall(spec.revised)
    if original_numbers != revised_numbers:
        raise ValueError(
            f"Numeric literal mismatch for {spec.pair_id}: "
            f"{original_numbers} != {revised_numbers}"
        )
    original_cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", original))
    revised_cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", spec.revised))
    expansion_ratio = revised_cjk / original_cjk
    if not 0.95 <= expansion_ratio <= 1.25:
        raise ValueError(
            f"CJK expansion outside [0.95, 1.25] for {spec.pair_id}: "
            f"{expansion_ratio:.3f}"
        )
    original_sentences = len(SENTENCE_END_RE.findall(original))
    revised_sentences = len(SENTENCE_END_RE.findall(spec.revised))
    if revised_sentences <= original_sentences:
        raise ValueError(f"Sentence count did not increase for {spec.pair_id}")
    for literal in spec.locked_literals:
        if literal not in original or literal not in spec.revised:
            raise ValueError(f"Locked literal missing in {spec.pair_id}: {literal}")
    for anchor in spec.voice_anchors:
        if anchor not in spec.revised:
            raise ValueError(f"Voice anchor missing in {spec.pair_id}: {anchor}")
    for item in spec.claims:
        if item.original_support not in original:
            raise ValueError(
                f"Original claim support missing in {spec.pair_id}: {item.claim_id}"
            )
        if item.revised_support not in spec.revised:
            raise ValueError(
                f"Revised claim support missing in {spec.pair_id}: {item.claim_id}"
            )
    return {
        "original_sha256": _sha256_text(original),
        "revised_sha256": _sha256_text(spec.revised),
        "original_numbers": original_numbers,
        "revised_numbers": revised_numbers,
        "original_cjk_chars": original_cjk,
        "revised_cjk_chars": revised_cjk,
        "cjk_expansion_ratio": expansion_ratio,
        "original_sentence_count": original_sentences,
        "revised_sentence_count": revised_sentences,
        "unified_diff": list(
            difflib.unified_diff(
                original.splitlines(),
                spec.revised.splitlines(),
                fromfile="original",
                tofile="revised",
                lineterm="",
            )
        ),
    }


def build_artifacts(
    handoff_root: Path,
    seed: int,
) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object]]:
    """Build intervention tasks plus identical and mirrored position controls."""

    metadata, originals = load_sources(handoff_root)
    specs = {spec.pair_id: spec for spec in SPECS}
    audits = {
        spec.pair_id: validate_pair(spec, originals[spec.pair_id]) for spec in SPECS
    }
    tasks: list[dict[str, object]] = []
    answer_pairs: list[dict[str, object]] = []
    protocol_pairs: list[dict[str, object]] = []
    for task_number, task_id in enumerate(TASK_ORDER, start=1):
        if task_id == IDENTICAL_CONTROL["pair_id"]:
            text = originals[task_id]
            record = metadata[str(IDENTICAL_CONTROL["doc_id"])]
            tasks.append(
                {
                    "data": {
                        "task_number": task_number,
                        "version_a": text,
                        "version_b": text,
                    },
                    "meta": {"pair_id": task_id, "control_role": "identical"},
                }
            )
            answer_pairs.append(
                {
                    "task_number": task_number,
                    "pair_id": task_id,
                    "doc_id": IDENTICAL_CONTROL["doc_id"],
                    "target_line": IDENTICAL_CONTROL["target_line"],
                    "control_role": "identical",
                    "expected_outcome": "tie_or_neither",
                    "text_sha256": _sha256_text(text),
                }
            )
            protocol_pairs.append(
                {
                    "task_number": task_number,
                    "pair_id": task_id,
                    "doc_id": IDENTICAL_CONTROL["doc_id"],
                    "source": record["source"],
                    "format_stratum": record["format_stratum"],
                    "control_role": "identical",
                }
            )
            continue

        mirrored = task_id.endswith("-mirror")
        base_id = task_id.removesuffix("-mirror") if mirrored else task_id
        spec = specs[base_id]
        original = originals[base_id]
        original_side = ORIGINAL_SIDES[task_id]
        version_a, version_b = (
            (original, spec.revised)
            if original_side == "A"
            else (spec.revised, original)
        )
        record = metadata[spec.doc_id]
        tasks.append(
            {
                "data": {
                    "task_number": task_number,
                    "version_a": version_a,
                    "version_b": version_b,
                },
                "meta": {
                    "pair_id": task_id,
                    "control_role": "mirrored" if mirrored else "intervention",
                },
            }
        )
        answer_pairs.append(
            {
                "task_number": task_number,
                "pair_id": task_id,
                "base_pair_id": base_id,
                "doc_id": spec.doc_id,
                "target_line": spec.target_line,
                "original_side": original_side,
                "control_role": "mirrored" if mirrored else "intervention",
                "mirror_of": base_id if mirrored else None,
                "operation": {
                    "operation_id": f"{base_id}-op-01",
                    "operator": "decompress_proposition_chain",
                    "before": original,
                    "after": spec.revised,
                    "reason": (
                        "Distribute preserved propositions across shorter integration "
                        "units while retaining explicit actors, relations, and voice."
                    ),
                },
                "claims": [asdict(item) for item in spec.claims],
                "locked_literals": list(spec.locked_literals),
                "voice_anchors": list(spec.voice_anchors),
                "audit": audits[base_id],
            }
        )
        protocol_pairs.append(
            {
                "task_number": task_number,
                "pair_id": task_id,
                "base_pair_id": base_id,
                "doc_id": spec.doc_id,
                "source": record["source"],
                "format_stratum": record["format_stratum"],
                "published_at": record["published_at"],
                "target_line": spec.target_line,
                "original_side": original_side,
                "control_role": "mirrored" if mirrored else "intervention",
                "claim_check_count": len(spec.claims),
                "cjk_expansion_ratio": audits[base_id]["cjk_expansion_ratio"],
                "sentence_count_change": (
                    int(audits[base_id]["revised_sentence_count"])
                    - int(audits[base_id]["original_sentence_count"])
                ),
            }
        )

    protocol = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "status": "frozen_before_outcomes",
        "frozen_at": "2026-08-27",
        "seed": seed,
        "role": "post_only_development_intervention_not_validation",
        "handoff": {
            "root": str(handoff_root),
            "manifest_sha256": hashlib.sha256(
                (handoff_root / "manifest.json").read_bytes()
            ).hexdigest(),
        },
        "selection_policy": {
            "reader_outcomes_used": False,
            "source_format_stratified": True,
            "distinct_intervention_documents": True,
            "selection_signal_count": 6,
            "manual_exclusions": [
                "question-and-answer fragments",
                "speaker profiles",
                "navigation and section-heading fragments",
                "image-generation prompts",
            ],
        },
        "operator_policy": [
            "Split dense proposition chains at existing semantic boundaries.",
            "Restore an explicit repeated referent only when coreference is already fixed.",
            "Preserve propositions, entities, numbers, negation, modality, attribution, uncertainty, and technical terms.",
            "Keep revised CJK length between 95% and 125% of the source.",
            "Increase sentence count rather than optimize for compression.",
            "Do not add anecdotes, evidence, mechanisms, or causal relations.",
            "Do not target formulaic markers unless a split mechanically changes their scope.",
        ],
        "position_diagnostics": {
            "task_order_fixed_for_control_separation": True,
            "identical_pair_count": 1,
            "mirrored_pair_count": 1,
            "mirrored_base_pair_id": "integration-v1-01",
            "mirror_task_distance": 6,
            "interpret_treatment_only_if_controls_pass": True,
        },
        "decision_policy": {
            "primary_outcome": "revised_version_preferred_for_continued_reading",
            "no_difference_is_not_a_win": True,
            "comments_used_for_selection": False,
            "position_gate": (
                "The identical pair must be rated no-difference and mirrored choices "
                "must agree by content rather than by side before aggregate treatment "
                "preference is interpreted."
            ),
        },
        "generation_diagnostics": {
            "task_count": len(tasks),
            "unique_intervention_pair_count": len(SPECS),
            "unique_document_count": len(SPECS) + 1,
            "source_counts": dict(
                sorted(Counter(metadata[spec.doc_id]["source"] for spec in SPECS).items())
            ),
            "format_counts": dict(
                sorted(
                    Counter(
                        metadata[spec.doc_id]["format_stratum"] for spec in SPECS
                    ).items()
                )
            ),
            "claim_check_count": sum(len(spec.claims) for spec in SPECS),
            "intervention_original_side_counts": dict(
                sorted(
                    Counter(
                        ORIGINAL_SIDES[spec.pair_id] for spec in SPECS
                    ).items()
                )
            ),
            "all_preservation_gates_passed": True,
        },
        "pairs": protocol_pairs,
    }
    answer_key = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "seed": seed,
        "pairs": answer_pairs,
    }
    return tasks, answer_key, protocol


def write_json(path: Path, value: object) -> None:
    """Write stable pretty-printed UTF-8 JSON."""

    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the fresh-post proposition-decompression intervention."
    )
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    tasks, answer_key, protocol = build_artifacts(
        args.handoff_root.resolve(), args.seed
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "tasks.json", tasks)
    write_json(args.output_dir / "answer_key.json", answer_key)
    write_json(args.output_dir / "protocol.json", protocol)
    (args.output_dir / "label_config.xml").write_text(
        LABEL_CONFIG,
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
