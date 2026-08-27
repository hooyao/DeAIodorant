"""Prepare a fresh post-only original-versus-revision intervention."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import random
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_reader_friction_screen_v2 import TARGET_MARKERS
from prepare_reader_friction_screen_v3 import complete_segments


SCHEMA_VERSION = "deaiodorant-refinement-pairs-4.0"
PROTOCOL_VERSION = "post-only-conservative-reframing-development-4.0"
DEFAULT_SEED = 2026082702
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?%?")
PROJECT5_DOC_IDS = frozenset(
    {
        "061767be12418dbf53feaf1d",
        "0a3e603aa9a9ad420334a890",
        "1b1059627ccd253b4042aa60",
        "4121a1ef99d626111ffe59c6",
        "4e5a10869cabea3263bb576e",
        "7f94b33a5bd4833a79204e52",
        "86acdf6932b6036ea979c084",
        "886c72b909098cc5ec646704",
        "b67f13dfff28e0d399f298b1",
        "f8ecc915a65b4a79429f9fce",
        "fbed7012bab78d329a4a523f",
        "0480ba19736016aeaa0c7d93",
    }
)


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
    operator: str
    reason: str
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
        pair_id="refinement-v4-01",
        doc_id="ddb4214a54ff80efa0f5b210",
        target_line=19,
        operator="merge_repeated_reframing",
        reason=(
            "Retain the four-layer argument and uncertainty while removing repeated "
            "true-divide and not-only staging."
        ),
        revised=(
            "模型层决定上限，负责理解、推理和生成；Tool 决定模型是否真的“能做事”，而不只“会说话”；"
            "IDE 交互层决定人能否高效表达意图、修正方向；上下文层承载历史决策、工程约束与连续性，"
            "把这些部分粘合起来，是长期可靠性的基础。\n"
            "未来 AI 编程的分水岭，或许不只在“谁的模型更强”，还在于谁能持续、准确地把工程世界中"
            "原本隐性的约束、记忆和共识，转化为模型可理解、可执行、可反复验证的上下文结构。"
            "AI 编程由工程体系与模型能力共同作用，开发者和 AI 的协作方式也决定能否用好它并产出好结果。"
        ),
        claims=(
            claim(
                "c01",
                "Model, tool, IDE, and context layers retain their distinct functions.",
                "模型层决定了上限",
                "模型层决定上限",
            ),
            claim(
                "c02",
                "The future divide depends on converting implicit engineering context.",
                "转化为模型可理解、可执行、并可被反复验证的上下文结构",
                "转化为模型可理解、可执行、可反复验证的上下文结构",
            ),
            claim(
                "c03",
                "Engineering, model ability, and collaboration jointly affect outcomes.",
                "工程体系与模型能力共同作用",
                "工程体系与模型能力共同作用",
            ),
        ),
        locked_literals=("Tool", "IDE", "AI 编程", "上下文"),
        voice_anchors=("或许", "谁的模型更强"),
    ),
    PairSpec(
        pair_id="refinement-v4-02",
        doc_id="e6b904412ae6774c9ee56964",
        target_line=16,
        operator="clarify_argument_structure",
        reason=(
            "Keep the reward-signal critique and self-verification conclusion while "
            "removing stacked breakthrough and key-point emphasis."
        ),
        revised=(
            "论文指出，过去一年，强化学习以“最终答案正确率”为奖励信号，使大语言模型在数学推理任务上的"
            "表现快速提升，从较低水平跃升至接近占满 AIME、HMMT 等高中难度竞赛榜单。\n"
            "这类方法的根本缺陷也逐渐暴露：正确答案不等于正确推理。定理证明等数学核心任务依赖严谨的"
            "逐步逻辑推导，无法用“答案对错”简单衡量；没有标准答案的开放问题同样无法据此奖励模型。"
            "要推动数学推理能力实现突破，就需要验证推理链条的完整性与严谨性，自验证机制因此成为一个"
            "关键方向。"
        ),
        claims=(
            claim(
                "c01",
                "Answer-accuracy rewards drove rapid gains on the named competitions.",
                "接近占满 AIME、HMMT 等高中难度竞赛榜单",
                "接近占满 AIME、HMMT 等高中难度竞赛榜单",
            ),
            claim(
                "c02",
                "Correct answers do not establish correct theorem-proof reasoning.",
                "正确答案并不等同于正确推理",
                "正确答案不等于正确推理",
            ),
            claim(
                "c03",
                "Open problems require chain verification and motivate self-verification.",
                "自验证机制”成为关键",
                "自验证机制因此成为一个关键方向",
            ),
        ),
        locked_literals=("AIME", "HMMT", "自验证机制", "定理证明"),
        voice_anchors=("根本缺陷",),
    ),
    PairSpec(
        pair_id="refinement-v4-03",
        doc_id="da81d4c0f5b616b43f9e1472",
        target_line=93,
        operator="remove_ornamental_emphasis",
        reason=(
            "State the industry and globalization claims directly while preserving "
            "the dated examples and source attribution."
        ),
        revised=(
            "阿里云希望让 AI 深入各行各业，以提升生产效率。\n"
            "中国 AI 原生企业在海外遍地开花，中国第一、第二及第三产业客户也纷纷出海，这推动阿里云"
            "加快全球化。刘伟光表示，2024–2025 年，中国企业出海已不只是把供应链优势搬出去，也把 "
            "AI 能力作为产品溢价的一部分：\n"
            "新能源车出海：没有智能化能力就很难维持差异化；\n"
            "家电、照明、厨具等传统硬件出海：正在被“自然语言对话 + 多模态理解”重新定义交互方式；\n"
            "机器人、安防、摄像头等品类出海：都需要端云协同的模型能力。"
        ),
        claims=(
            claim(
                "c01",
                "Alibaba Cloud seeks productivity gains through industry AI adoption.",
                "让 AI 深入到各行各业，用 AI 提升生产效率",
                "让 AI 深入各行各业，以提升生产效率",
            ),
            claim(
                "c02",
                "Chinese company expansion motivates Alibaba Cloud globalization.",
                "使得阿里云加速剑指全球化",
                "这推动阿里云加快全球化",
            ),
            claim(
                "c03",
                "All three sector examples and their AI requirements are retained.",
                "2024–2025",
                "2024–2025",
            ),
        ),
        locked_literals=("阿里云", "刘伟光", "2024–2025", "端云协同"),
        voice_anchors=("遍地开花",),
    ),
    PairSpec(
        pair_id="refinement-v4-04",
        doc_id="21129f35e0f1ae2b265bb287",
        target_line=27,
        operator="clarify_argument_structure",
        reason=(
            "Replace a spoken sequence of summary announcements with an explicit "
            "data-control, unstructured-data, and interaction chain."
        ),
        revised=(
            "从数据角度看，互联网时代与 Agent 时代的第一个区别是：前者的数据由应用生成，因而可控；"
            "AI 时代会引入大量外部数据，来源不完全可控，规模也可能很大。AI 时代还会产生大量非结构化"
            "数据，使搜索更加重要，几乎所有数据库都需要发展向量能力。Agent 还会相互交互并与外部交互，"
            "同时记录交互内容，数据量会迅速积累。"
        ),
        claims=(
            claim(
                "c01",
                "Application-generated Internet data is contrasted with external AI data.",
                "前者的数据是由应用生成的，意味着数据是可控的",
                "前者的数据由应用生成，因而可控",
            ),
            claim(
                "c02",
                "Unstructured data raises the importance of vector search.",
                "几乎所有的数据库都要发展向量的能力",
                "几乎所有数据库都需要发展向量能力",
            ),
            claim(
                "c03",
                "Agent interactions and recording rapidly accumulate data.",
                "所以数据量很快就会积累起来",
                "数据量会迅速积累",
            ),
        ),
        locked_literals=("Agent", "AI", "非结构化数据", "向量"),
        voice_anchors=("从数据角度看",),
    ),
    PairSpec(
        pair_id="refinement-v4-05",
        doc_id="7c1423cab64a9a1b24d75243",
        target_line=41,
        operator="merge_repeated_reframing",
        reason=(
            "Keep the personal-software trend and price criticism while replacing "
            "two staged pivots with a direct transition."
        ),
        revised=(
            "这类案例也显示了“个人软件”的趋势：无论是做一个熟悉工具的轻量替代品，还是改造现有工作流，"
            "门槛都在快速降低。他认为，个人软件时代已经到来，接下来只会变得更容易、更快、更好、更便宜。\n"
            "不过，Fable 5 的价格也确实很高。早期用户最集中的抱怨很明确：它更强，但也更贵、更容易"
            "烧穿额度。"
        ),
        claims=(
            claim(
                "c01",
                "Lower barriers support the personal-software trend.",
                "门槛都在快速降低",
                "门槛都在快速降低",
            ),
            claim(
                "c02",
                "The future trend remains easier, faster, better, and cheaper.",
                "更容易、更快、更好、更便宜",
                "更容易、更快、更好、更便宜",
            ),
            claim(
                "c03",
                "Fable 5 remains stronger, expensive, and prone to exhausting quotas.",
                "更强，但也确实更贵、更容易烧穿额度",
                "更强，但也更贵、更容易烧穿额度",
            ),
        ),
        locked_literals=("个人软件", "Fable 5", "额度"),
        voice_anchors=("更容易、更快、更好、更便宜", "确实很高"),
    ),
    PairSpec(
        pair_id="refinement-v4-06",
        doc_id="398d56824414e91464ffc3d8",
        target_line=78,
        operator="direct_contrast",
        reason=(
            "Preserve the real deliverables and evaluative stance while removing "
            "not-only, not-this-but-that, and exactly-this revelation framing."
        ),
        revised=(
            "我们提供了评测，也开源了自动合成任务的方法和训练环境。MineExplorer 不是一套静态题库，"
            "还包含一整套自动合成长程任务的流程，以及可直接用于训练的 Minecraft 环境；评测、造题和训练"
            "使用同一套基础设施。\n"
            "这并不是给具身智能泼冷水。把瓶颈定位清楚，比盲目乐观更有价值；MineExplorer 提供了一条"
            "诚实、可量化的能力基线。"
        ),
        claims=(
            claim(
                "c01",
                "Evaluation, task synthesis, and a training environment are all provided.",
                "还开源了自动合成任务的方法和训练环境",
                "也开源了自动合成任务的方法和训练环境",
            ),
            claim(
                "c02",
                "The benchmark is not a static question set and shares infrastructure.",
                "不是一套静态题库",
                "不是一套静态题库",
            ),
            claim(
                "c03",
                "Locating bottlenecks supports an honest quantitative capability baseline.",
                "诚实、可量化的能力基线",
                "诚实、可量化的能力基线",
            ),
        ),
        locked_literals=("MineExplorer", "Minecraft", "评测", "训练环境"),
        voice_anchors=("给具身智能泼冷水", "盲目乐观"),
    ),
    PairSpec(
        pair_id="refinement-v4-07",
        doc_id="fdbd90f96ec1d4752373dcf1",
        target_line=1,
        operator="remove_ornamental_emphasis",
        reason=(
            "Retain the competition and car-wash examples while stating the common-"
            "sense evaluation gap without dead-point and strongest-brain staging."
        ),
        revised=(
            "大模型在 AIME、IMO 等高难度竞赛中频频获奖，仿佛已经进化出了“人类最强大脑”。可是，如果"
            "你问大模型：“离洗车店只有 50 米，我是开车去还是走路去？”，这些号称满分推理的模型依然会"
            "一本正经地规划导航路线。\n"
            "这种知识丰富却缺乏常识的现象，暴露了当前大模型评测的死穴：模型擅长记忆复杂公式，却常常"
            "连一道简单的逻辑题都答不对。"
        ),
        claims=(
            claim(
                "c01",
                "Models perform strongly on AIME and IMO competitions.",
                "AIME、IMO 等高难度竞赛中拿奖",
                "AIME、IMO 等高难度竞赛中频频获奖",
            ),
            claim(
                "c02",
                "The 50-meter car-wash example remains a common-sense failure.",
                "离洗车店只有 50 米",
                "离洗车店只有 50 米",
            ),
            claim(
                "c03",
                "Formula knowledge can coexist with failure on simple logic.",
                "擅长记忆复杂的公式，却常常连一道简单的逻辑题都答不对",
                "擅长记忆复杂公式，却常常连一道简单的逻辑题都答不对",
            ),
        ),
        locked_literals=("AIME", "IMO", "50 米", "洗车店"),
        voice_anchors=("仿佛", "人类最强大脑", "一本正经", "死穴"),
    ),
    PairSpec(
        pair_id="refinement-v4-08",
        doc_id="ee642b95d3e1e32aea9e8ccf",
        target_line=1,
        operator="clarify_argument_structure",
        reason=(
            "Keep the benchmark saturation and annotation-limit argument while "
            "removing a staged possibility reveal."
        ),
        revised=(
            "过去一年，Search Agent 能力显著提升。在 BrowseComp 等评测上，顶尖模型准确率从最初的 30% "
            "区间迅速升至 90% 以上；随着基准快速饱和，它区分模型能力的价值也随之下降。\n"
            "BrowseComp 的题目由人工设计，只能基于标注者已知的实体和关系构思，无法从全局知识网络判断"
            "哪些条件确实难以检索、哪些约束拥有足够大的候选空间。这一局限促使我们思考：能否让机器自己"
            "出题？美团 LongCat 团队在最新论文中提出 LoHoSearch 基准，把这一设想变成了现实。"
        ),
        claims=(
            claim(
                "c01",
                "BrowseComp accuracy rose from the 30% range to above 90%.",
                "从最初的30%区间迅速攀升至90%以上",
                "从最初的 30% 区间迅速升至 90% 以上",
            ),
            claim(
                "c02",
                "Human-authored questions lack a global knowledge-network view.",
                "无法站在全局知识网络视角判断",
                "无法从全局知识网络判断",
            ),
            claim(
                "c03",
                "LoHoSearch realizes machine-generated question construction.",
                "把这种可能性变成了现实",
                "把这一设想变成了现实",
            ),
        ),
        locked_literals=("Search Agent", "BrowseComp", "30%", "90%", "LoHoSearch"),
        voice_anchors=("能否让机器自己出题",),
    ),
    PairSpec(
        pair_id="refinement-v4-09",
        doc_id="a174fe26e705b96c18acb00e",
        target_line=105,
        operator="direct_contrast",
        reason=(
            "Preserve the four first-phase limitations and the complete second-phase "
            "scope while replacing a staged not-X-but-Y contrast."
        ),
        revised=(
            "一期验证了 LLM 表征在精排中的可行性，但四个短板制约了后续迭代：只覆盖 Query-商家两端，"
            "缺失商品语义；全参数微调成本高；点击率分类目标对排序优化不够全面；三次 Forward Pass "
            "效率低。\n"
            "二期系统性重构表征生产全流程，涵盖训练数据、基座模型、微调方式、表征提取、降维方式和"
            "损失函数，逐一对应一期短板，并将下挂商品（Deal）纳入建模，构建 Query-POI-Deal 三元语义"
            "表征体系。"
        ),
        claims=(
            claim(
                "c01",
                "Phase one established feasibility but retained four named limitations.",
                "但四个短板制约了进一步迭代",
                "但四个短板制约了后续迭代",
            ),
            claim(
                "c02",
                "Phase two rebuilds all six named production stages.",
                "从训练数据、基座模型、微调方式、表征提取、降维方式到损失函数",
                "涵盖训练数据、基座模型、微调方式、表征提取、降维方式和损失函数",
            ),
            claim(
                "c03",
                "Deal is added to the Query-POI-Deal representation system.",
                "构建 Query-POI-Deal 三元语义表征体系",
                "构建 Query-POI-Deal 三元语义表征体系",
            ),
        ),
        locked_literals=("LLM", "Query", "Forward Pass", "Deal", "Query-POI-Deal"),
        voice_anchors=("一期", "二期"),
    ),
    PairSpec(
        pair_id="refinement-v4-10",
        doc_id="4c4d1156bf248a78ba057cb3",
        target_line=1,
        operator="clarify_argument_structure",
        reason=(
            "Keep the mathematical-proof distinction and uncertainty while replacing "
            "a rhetorical question and stacked contrast with a direct problem statement."
        ),
        revised=(
            "大语言模型已经能流畅地写文章、写代码，甚至执行复杂的 Agent 工作流，但面对严谨的数学定理"
            "证明时，仍往往显得力不从心。\n"
            "常规数学解题只要求“答对最终数值”；数学定理证明则要求极其严谨的逻辑链条，任何一句自然语言"
            "的模棱两可都可能使整个证明崩塌。要让 AI 从“猜答案”走向“严谨证明”，仍需解决这一复杂推理"
            "难题。"
        ),
        claims=(
            claim(
                "c01",
                "Models handle writing, coding, and Agent workflows but struggle with proofs.",
                "面对严谨的数学定理证明时，却往往显得力不从心",
                "面对严谨的数学定理证明时，仍往往显得力不从心",
            ),
            claim(
                "c02",
                "Proof requires a stricter logical chain than final-value math problems.",
                "它要求极度严苛的逻辑链条",
                "数学定理证明则要求极其严谨的逻辑链条",
            ),
            claim(
                "c03",
                "Ambiguous natural language can collapse the proof.",
                "任何一句自然语言的模棱两可，都可能导致整个证明的崩塌",
                "任何一句自然语言的模棱两可都可能使整个证明崩塌",
            ),
        ),
        locked_literals=("Agent", "数学定理证明", "AI", "猜答案", "严谨证明"),
        voice_anchors=("力不从心",),
    ),
)


LABEL_CONFIG = """<View>
  <Header value="同一段内容的保守改写盲测"/>
  <Text name="instruction" value="下面是同一段内容的两个版本。哪个版本让你更愿意继续读？只按第一感受选择；没有明显差别时请选第三项，不需要分析原因。"/>
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
  <TextArea name="comment" toName="version_a" placeholder="可以留空；若有明显遗漏、变冷或仍然别扭，可以随手写一句。" rows="2"/>
</View>
"""


def load_sources(handoff_root: Path) -> tuple[dict[str, dict], dict[str, str]]:
    """Load handoff metadata and exact complete segments by document and line."""

    records = [
        json.loads(line)
        for line in (handoff_root / "documents.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    metadata = {str(record["doc_id"]): record for record in records}
    segments: dict[str, str] = {}
    for spec in SPECS:
        record = metadata[spec.doc_id]
        body_path = handoff_root / str(record["body_path"])
        body = body_path.read_text(encoding="utf-8").rstrip("\n")
        segment_map = dict(complete_segments(body.splitlines()))
        if spec.target_line not in segment_map:
            raise ValueError(
                f"Missing complete segment for {spec.doc_id}:{spec.target_line}"
            )
        original = segment_map[spec.target_line]
        observed_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if observed_hash != record["content_hash"]:
            raise ValueError(f"Source hash mismatch for {spec.doc_id}")
        segments[spec.pair_id] = original
    return metadata, segments


def validate_pair(spec: PairSpec, original: str) -> dict[str, object]:
    """Apply frozen deterministic preservation and manipulation checks."""

    if original == spec.revised:
        raise ValueError(f"No intervention for {spec.pair_id}")
    original_numbers = NUMBER_RE.findall(original)
    revised_numbers = NUMBER_RE.findall(spec.revised)
    if original_numbers != revised_numbers:
        raise ValueError(
            f"Numeric literal mismatch for {spec.pair_id}: "
            f"{original_numbers} != {revised_numbers}"
        )
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
    original_markers = sum(original.count(marker) for marker in TARGET_MARKERS)
    revised_markers = sum(spec.revised.count(marker) for marker in TARGET_MARKERS)
    diff = list(
        difflib.unified_diff(
            original.splitlines(),
            spec.revised.splitlines(),
            fromfile="original",
            tofile="revised",
            lineterm="",
        )
    )
    return {
        "original_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        "revised_sha256": hashlib.sha256(spec.revised.encode("utf-8")).hexdigest(),
        "original_numbers": original_numbers,
        "revised_numbers": revised_numbers,
        "original_marker_count": original_markers,
        "revised_marker_count": revised_markers,
        "unified_diff": diff,
    }


def build_artifacts(
    handoff_root: Path, seed: int
) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object]]:
    """Build blinded tasks, structured operations, and a frozen protocol."""

    overlap = PROJECT5_DOC_IDS.intersection(spec.doc_id for spec in SPECS)
    if overlap:
        raise ValueError(f"Project 5 document reuse: {sorted(overlap)}")
    metadata, originals = load_sources(handoff_root)
    prepared: list[tuple[PairSpec, str, dict[str, object]]] = []
    for spec in SPECS:
        original = originals[spec.pair_id]
        prepared.append((spec, original, validate_pair(spec, original)))

    rng = random.Random(seed)
    rng.shuffle(prepared)
    original_sides = ["A"] * 5 + ["B"] * 5
    rng.shuffle(original_sides)
    tasks: list[dict[str, object]] = []
    answer_pairs: list[dict[str, object]] = []
    protocol_pairs: list[dict[str, object]] = []
    for task_number, ((spec, original, audit), original_side) in enumerate(
        zip(prepared, original_sides, strict=True), start=1
    ):
        record = metadata[spec.doc_id]
        version_a, version_b = (
            (original, spec.revised)
            if original_side == "A"
            else (spec.revised, original)
        )
        tasks.append(
            {
                "data": {
                    "task_number": task_number,
                    "version_a": version_a,
                    "version_b": version_b,
                },
                "meta": {
                    "pair_id": spec.pair_id,
                    "source": record["source"],
                    "format_stratum": record["format_stratum"],
                    "published_at": record["published_at"],
                },
            }
        )
        operation = {
            "operation_id": f"{spec.pair_id}-op-01",
            "operator": spec.operator,
            "before": original,
            "after": spec.revised,
            "reason": spec.reason,
        }
        answer_pairs.append(
            {
                "task_number": task_number,
                "pair_id": spec.pair_id,
                "doc_id": spec.doc_id,
                "target_line": spec.target_line,
                "original_side": original_side,
                "operation": operation,
                "claims": [asdict(item) for item in spec.claims],
                "locked_literals": list(spec.locked_literals),
                "voice_anchors": list(spec.voice_anchors),
                "audit": audit,
            }
        )
        protocol_pairs.append(
            {
                "task_number": task_number,
                "pair_id": spec.pair_id,
                "doc_id": spec.doc_id,
                "source": record["source"],
                "format_stratum": record["format_stratum"],
                "published_at": record["published_at"],
                "target_line": spec.target_line,
                "operator": spec.operator,
                "claim_check_count": len(spec.claims),
                "locked_literal_count": len(spec.locked_literals),
                "voice_anchor_count": len(spec.voice_anchors),
                "original_sha256": audit["original_sha256"],
                "revised_sha256": audit["revised_sha256"],
                "original_marker_count": audit["original_marker_count"],
                "revised_marker_count": audit["revised_marker_count"],
            }
        )

    handoff_manifest = handoff_root / "manifest.json"
    answer_key = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "seed": seed,
        "pairs": answer_pairs,
    }
    protocol = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "status": "frozen_before_outcomes",
        "frozen_at": "2026-08-27",
        "seed": seed,
        "role": "post_only_development_intervention_not_validation",
        "handoff": {
            "root": str(handoff_root),
            "manifest_sha256": hashlib.sha256(handoff_manifest.read_bytes()).hexdigest(),
        },
        "source_policy": {
            "post_start": "2025-07-01",
            "all_project_5_documents_excluded": True,
            "one_passage_per_document": True,
            "source_counts": dict(
                sorted(Counter(metadata[spec.doc_id]["source"] for spec in SPECS).items())
            ),
        },
        "operator_policy": [
            "Reduce ornamental contrast, clarification, and emphasis framing.",
            "Retain necessary contrasts, negation, modality, attribution, and uncertainty.",
            "Preserve explicit subjects, predicates, objects, and referents.",
            "Preserve propositions, entities, numbers, technical terms, rhythm, and authorial voice.",
            "Do not maximize compression or turn passages into uniformly flat prose.",
        ],
        "decision_policy": {
            "primary_outcome": "revised_version_preferred_for_continued_reading",
            "no_difference_is_not_a_win": True,
            "comments_used_for_selection": False,
        },
        "generation_diagnostics": {
            "pair_count": len(SPECS),
            "document_count": len({spec.doc_id for spec in SPECS}),
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
            "operation_count": len(SPECS),
            "claim_check_count": sum(len(spec.claims) for spec in SPECS),
            "original_side_counts": dict(sorted(Counter(original_sides).items())),
            "original_marker_count": sum(
                int(audit["original_marker_count"])
                for _, _, audit in prepared
            ),
            "revised_marker_count": sum(
                int(audit["revised_marker_count"])
                for _, _, audit in prepared
            ),
            "all_preservation_gates_passed": True,
        },
        "pairs": protocol_pairs,
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
        description="Prepare the fresh post-only conservative intervention."
    )
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    handoff_root = args.handoff_root.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {output_dir}")
    tasks, answer_key, protocol = build_artifacts(handoff_root, args.seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "tasks.json", tasks)
    write_json(output_dir / "answer_key.json", answer_key)
    write_json(output_dir / "protocol.json", protocol)
    (output_dir / "label_config.xml").write_text(
        LABEL_CONFIG, encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "protocol_version": PROTOCOL_VERSION,
                **protocol["generation_diagnostics"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
