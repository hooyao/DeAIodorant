"""Prepare the third blinded development round from the read-only handoff."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

SCHEMA_VERSION = "deaiodorant-refinement-pairs-3.0"
PROTOCOL_VERSION = "conservative-reframing-development-3.0"
DEFAULT_SEED = 20260822


@dataclass(frozen=True)
class Operation:
    operation_id: str
    operator: str
    before: str
    after: str
    reason: str


@dataclass(frozen=True)
class ClaimCheck:
    claim_id: str
    description: str
    original_support: str
    revised_support: str


@dataclass(frozen=True)
class Pair:
    pair_id: str
    genre: str
    doc_id: str
    target_lines: tuple[int, int]
    original_sha256: str
    operations: tuple[Operation, ...]
    claim_checks: tuple[ClaimCheck, ...]
    locked_literals: tuple[str, ...]
    voice_anchors: tuple[str, ...]
    retained_contrasts: tuple[str, ...]


def operation(
    operation_id: str,
    operator: str,
    before: str,
    after: str,
    reason: str,
) -> Operation:
    return Operation(operation_id, operator, before, after, reason)


def claim(
    claim_id: str,
    description: str,
    original_support: str,
    revised_support: str | None = None,
) -> ClaimCheck:
    return ClaimCheck(
        claim_id,
        description,
        original_support,
        revised_support or original_support,
    )


PAIRS = (
    Pair(
        pair_id="contrast-v3-01",
        genre="technical_practice",
        doc_id="44ff5a1d8bda9c7b50f6290f",
        target_lines=(36, 36),
        original_sha256="00d282b280c26fbacc8eb2f9b21ba293c3f3ba0ec4e62d692d1af51bc257ef47",
        operations=(
            operation(
                "contrast-v3-01-op-01",
                "direct_contrast",
                "大模型对于技术方面的词汇，如字段、行列、表等无法理解，相反对于业务方面的词汇，如公司收入情况、日活跃用户数量等能够提供有效翻译与转换。",
                "大模型无法理解字段、行列、表等技术词汇，却能有效翻译和转换公司收入情况、日活跃用户数量等业务词汇。",
                "Keep the real capability contrast but remove a staged sentence-level reversal.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The model fails on technical vocabulary but can translate named business vocabulary.",
                "大模型对于技术方面的词汇，如字段、行列、表等无法理解，相反对于业务方面的词汇，如公司收入情况、日活跃用户数量等能够提供有效翻译与转换。",
                "大模型无法理解字段、行列、表等技术词汇，却能有效翻译和转换公司收入情况、日活跃用户数量等业务词汇。",
            ),
            claim(
                "c02",
                "The two stated challenges concern query scope and metric-definition consistency.",
                "挑战之一是需要思考如何引导用户进入指标范围内提问，挑战之二是当用户存在对多种指标、多类指标查询时，需要考虑如何保持指标维度口径的统一、如何有效生成对应的指标计算公式。",
            ),
        ),
        locked_literals=("大模型", "字段", "行列", "公司收入情况", "日活跃用户数量"),
        voice_anchors=("挑战之一", "挑战之二"),
        retained_contrasts=(
            "Technical vocabulary and business vocabulary remain explicitly contrasted.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-02",
        genre="technical_practice",
        doc_id="c4f3d04d7db01e65460fb2dd",
        target_lines=(14, 14),
        original_sha256="628595b309fb1b30b73945e212ff88b88f0770650e10abde4016c261814242ac",
        operations=(
            operation(
                "contrast-v3-02-op-01",
                "merge_repeated_reframing",
                "在知乎，我们不仅仅采取了诸如合理的分布式数据库选型、基于 FinOps 合理规划硬件资源、服务器机型替换、对象存储优化等传统措施。此外，我们还引入了天穹自动化运维平台，该平台能够实现业务数据库变更的自助管理，同时也让 DBA 对数据库的管理实现了自动化，从而大大提高了数据库管理的效率和稳定性。",
                "在知乎，我们采取了合理的分布式数据库选型、基于 FinOps 规划硬件资源、服务器机型替换、对象存储优化等传统措施，也引入了天穹自动化运维平台。该平台支持业务数据库变更的自助管理，也让 DBA 的数据库管理实现自动化，从而提高管理效率和稳定性。",
                "Convert stacked additive framing into two explicit sentences while preserving every measure and outcome.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Zhihu used the four named traditional cost-efficiency measures.",
                "合理的分布式数据库选型、基于 FinOps 合理规划硬件资源、服务器机型替换、对象存储优化等传统措施",
                "合理的分布式数据库选型、基于 FinOps 规划硬件资源、服务器机型替换、对象存储优化等传统措施",
            ),
            claim(
                "c02",
                "The Tianqiong platform supports self-service changes and DBA automation.",
                "天穹自动化运维平台，该平台能够实现业务数据库变更的自助管理，同时也让 DBA 对数据库的管理实现了自动化",
                "天穹自动化运维平台。该平台支持业务数据库变更的自助管理，也让 DBA 的数据库管理实现自动化",
            ),
            claim(
                "c03",
                "The combined measures improve efficiency, stability, and the broader management solution.",
                "通过这些创新措施的结合应用，我们在实践中不断探索和推进数据库降本增效的路径，为知乎的数据管理提供了更加全面和可靠的解决方案。",
            ),
        ),
        locked_literals=("知乎", "FinOps", "天穹自动化运维平台", "DBA", "对象存储"),
        voice_anchors=("在实践中不断探索和推进",),
        retained_contrasts=(),
    ),
    Pair(
        pair_id="contrast-v3-03",
        genre="technical_practice",
        doc_id="ed4b0601b5481ee4065a337a",
        target_lines=(26, 26),
        original_sha256="7ccf463fae930037c2c22f89d5ff32cce2dce213560e95d75490af04cc48c171",
        operations=(
            operation(
                "contrast-v3-03-op-01",
                "clarify_argument_structure",
                "在项目早期，基础架构团队就计划用一套调度系统管理在离线业务，真正做到统一调度。由于离线业务的调度需求比较复杂，与在线业务差别比较大，吞吐要求也很高；加上 Kubernetes 原生调度器是基于 Pod 调度，对更上一级 “Job” 级别的调度语义支持能力有限；同时由于原生调度器是单体调度器，性能优化的天花板也较低，比较难满足部分批式计算任务的需求——我们决定基于 Kubernetes 系统自研分布式调度器：",
                "项目早期，基础架构团队计划用一套调度系统管理在离线业务，实现统一调度。离线业务的调度需求复杂，与在线业务差别较大，吞吐要求也高；Kubernetes 原生调度器基于 Pod 调度，对更上一级“Job”调度语义的支持有限；原生调度器还是单体架构，性能优化空间较小，难以满足部分批式计算任务。基于这些约束，团队决定在 Kubernetes 上自研分布式调度器：",
                "Complete the causal chain in shorter clauses and remove repeated depth and importance framing.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The infrastructure team planned one system for unified online and offline scheduling.",
                "基础架构团队就计划用一套调度系统管理在离线业务，真正做到统一调度",
                "基础架构团队计划用一套调度系统管理在离线业务，实现统一调度",
            ),
            claim(
                "c02",
                "Offline complexity, throughput, Pod semantics, and monolithic architecture are all retained constraints.",
                "离线业务的调度需求比较复杂，与在线业务差别比较大，吞吐要求也很高",
                "离线业务的调度需求复杂，与在线业务差别较大，吞吐要求也高",
            ),
            claim(
                "c03",
                "The constraints led the team to build a distributed scheduler on Kubernetes.",
                "我们决定基于 Kubernetes 系统自研分布式调度器",
                "团队决定在 Kubernetes 上自研分布式调度器",
            ),
        ),
        locked_literals=("基础架构团队", "Kubernetes", "Pod", "Job", "批式计算任务"),
        voice_anchors=("性能优化",),
        retained_contrasts=(
            "Offline and online scheduling requirements remain contrasted.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-04",
        genre="technical_practice",
        doc_id="2e209708bce31c124797ce6c",
        target_lines=(63, 65),
        original_sha256="22e3c56bd09db5e08eaa07798e0c1fa6d472d2d1cba9418ef35c3e7ab0d7c1dc",
        operations=(
            operation(
                "contrast-v3-04-op-01",
                "clarify_argument_structure",
                "为了防止业务之间的相互影响，我们针对每个 EMR 集群，都设置了专属的存储桶，针对自身 EMR 可读写，针对其他 EMR 只可读。出于性能和成本的考虑，针对不是稳定性要求不是很高的业务，我们仍然将 state 存储在 HDFS 上。",
                "为了防止业务相互影响，我们为每个 EMR 集群设置了专属存储桶：自身 EMR 可读写，其他 EMR 只可读。对于稳定性要求不高的业务，考虑到性能和成本，我们仍将 state 存储在 HDFS 上。",
                "Repair a duplicated negation and make the subject, access rules, and qualification explicit.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Checkpoint times for all four state sizes are similar and acceptable.",
                "1M, 64M, 512M, 1G 状态在使用 HDFS OSS 作为 FsStateBackend 的性能区别，发现对应的 checkpoint 时间差别不大，都在可接受范围。",
            ),
            claim(
                "c02",
                "Switching state to object storage is feasible inside Zuoyebang.",
                "因此将 state 切换到对象存储，在作业帮内部是完全可行的。",
            ),
            claim(
                "c03",
                "Each EMR bucket has the stated own-cluster and other-cluster permissions.",
                "针对自身 EMR 可读写，针对其他 EMR 只可读",
                "自身 EMR 可读写，其他 EMR 只可读",
            ),
            claim(
                "c04",
                "Low-stability-requirement workloads may remain on HDFS for performance and cost reasons.",
                "出于性能和成本的考虑，针对不是稳定性要求不是很高的业务，我们仍然将 state 存储在 HDFS 上。",
                "对于稳定性要求不高的业务，考虑到性能和成本，我们仍将 state 存储在 HDFS 上。",
            ),
        ),
        locked_literals=(
            "EMR",
            "HDFS",
            "OSS",
            "FsStateBackend",
            "checkpoint",
            "state",
            "作业帮",
        ),
        voice_anchors=("完全可行",),
        retained_contrasts=("Read-write access and read-only access remain distinct.",),
    ),
    Pair(
        pair_id="contrast-v3-05",
        genre="research_summary",
        doc_id="10b4ff947e750938d62a417a",
        target_lines=(21, 21),
        original_sha256="5f5703aca8cac719220d5899aa652c8487cc16a134114cae6c8c101f687c44b6",
        operations=(
            operation(
                "contrast-v3-05-op-01",
                "remove_ornamental_emphasis",
                "值得注意的是，在上述情况下，与 OPED 得分较低的 pegRNA 相比，较高 OPED 编辑得分的 pegRNA 的编辑效率高得多（2.2-82.9 倍）。",
                "在上述情况下，与 OPED 得分较低的 pegRNA 相比，较高 OPED 编辑得分的 pegRNA 编辑效率高出 2.2-82.9 倍。",
                "State the measured comparison directly without an attention directive.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "OPED was tested across the full listed set of editing conditions.",
                "不同编辑类型、编辑位置、内源性位点、实验室环境、tevopreQ1 条件、错配修复（MMR）抑制条件、体外细胞系和体内小鼠肝细胞",
            ),
            claim(
                "c02",
                "Higher OPED scores correspond to a 2.2-82.9-fold efficiency increase.",
                "较高 OPED 编辑得分的 pegRNA 的编辑效率高得多（2.2-82.9 倍）",
                "较高 OPED 编辑得分的 pegRNA 编辑效率高出 2.2-82.9 倍",
            ),
        ),
        locked_literals=("OPED", "pegRNA", "tevopreQ1", "MMR"),
        voice_anchors=("研究证明",),
        retained_contrasts=("High and low OPED scores remain the comparison groups.",),
    ),
    Pair(
        pair_id="contrast-v3-06",
        genre="research_summary",
        doc_id="7103a1b4c0cb80218a653a03",
        target_lines=(46, 48),
        original_sha256="bcca196d27a87675b97892656a1d35d17f4f78722d413a6a96614496aad23542",
        operations=(
            operation(
                "contrast-v3-06-op-01",
                "remove_ornamental_emphasis",
                "值得注意的是，GPT-4V 会产生一些令人困惑的错觉，例如认为图片上有左转标志。",
                "GPT-4V 还会产生一些令人困惑的错觉，例如认为图片上有左转标志。",
                "Remove an attention directive while retaining the observed error.",
            ),
            operation(
                "contrast-v3-06-op-02",
                "remove_ornamental_emphasis",
                "显然，GPT-4V 在建立相邻图像之间的连接方面遇到了挑战。",
                "GPT-4V 在建立相邻图像之间的连接方面遇到了挑战。",
                "Remove an unnecessary certainty booster from the stated result.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "GPT-4V identifies several scene elements and two vehicle types but misses a crosswalk.",
                "其中一辆白色 SUV，一辆卡车。然而，GPT-4V 会错误地识别出人行横道。",
            ),
            claim(
                "c02",
                "The model makes vehicle-count and shape errors and hallucinates a left-turn sign.",
                "GPT-4V 会产生一些令人困惑的错觉，例如认为图片上有左转标志。",
                "GPT-4V 还会产生一些令人困惑的错觉，例如认为图片上有左转标志。",
            ),
            claim(
                "c03",
                "The research team gives spatial reasoning as a possible cause.",
                "研究团队推测这些问题可能是由于 GPT-4V 的空间推理能力有限。",
            ),
            claim(
                "c04",
                "The ordering experiment fails despite apparently meaningful reasoning.",
                "尽管模型进行了大量看似有意义的分析和推理，但最终仍然输出错误答案。",
            ),
        ),
        locked_literals=("GPT-4V", "SUV", "左转标志", "空间推理能力"),
        voice_anchors=("令人困惑的错觉",),
        retained_contrasts=(
            "Correct scene description and recognition errors remain contrasted.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-07",
        genre="research_summary",
        doc_id="646b73aae2b0dc8f311a9f0c",
        target_lines=(18, 20),
        original_sha256="09eb73dbf21936a457864073449863cfbcb1aceca0883d21a6768e6caab7594d",
        operations=(
            operation(
                "contrast-v3-07-op-01",
                "clarify_argument_structure",
                "要公平地比较在线和离线算法并非易事，因为它们存在许多实现和算法方面的差异。举个例子，在线算法所需的计算量往往大于离线算法，因为它需要采样和训练另一个模型。因此，为了比较公平，需要在衡量性能时对不同算法所耗费的预算进行一定的校准。",
                "在线和离线算法在实现与算法上存在多项差异，因此难以公平比较。在线算法需要采样和训练另一个模型，计算量往往大于离线算法。衡量性能时需要校准不同算法耗费的预算。",
                "State the comparison difficulty, example mechanism, and calibration requirement directly.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Offline RLHF is simpler and cheaper, and evidence about both approaches has the stated value.",
                "离线算法实现起来要简单得多，成本也低得多。",
            ),
            claim(
                "c02",
                "Implementation and algorithm differences make fair comparison difficult.",
                "要公平地比较在线和离线算法并非易事，因为它们存在许多实现和算法方面的差异。",
                "在线和离线算法在实现与算法上存在多项差异，因此难以公平比较。",
            ),
            claim(
                "c03",
                "Online algorithms require more compute because they sample and train another model.",
                "在线算法所需的计算量往往大于离线算法，因为它需要采样和训练另一个模型。",
                "在线算法需要采样和训练另一个模型，计算量往往大于离线算法。",
            ),
            claim(
                "c04",
                "Performance comparisons require budget calibration.",
                "需要在衡量性能时对不同算法所耗费的预算进行一定的校准。",
                "衡量性能时需要校准不同算法耗费的预算。",
            ),
        ),
        locked_literals=("RLHF", "在线算法", "离线算法", "预算"),
        voice_anchors=("另一方面",),
        retained_contrasts=(
            "Online and offline cost and implementation differences remain explicit.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-08",
        genre="research_summary",
        doc_id="a76e84a2a44062b098288efc",
        target_lines=(29, 32),
        original_sha256="7a8a0da23fdb6c2c13263251ebcbd673271dce58f56beba1bf219a2aa4feb6c4",
        operations=(
            operation(
                "contrast-v3-08-op-01",
                "direct_contrast",
                "需要强调的是，研究者的目的不是断言\n语言模型\n是否优于其他模型，而是促进 LLM 视觉 tokenization 方法的探索。",
                "研究者并不试图断言语言模型是否优于其他模型；他们希望促进 LLM 视觉 tokenization 方法的探索。",
                "Preserve the explicit non-claim and research purpose without staging them as a reveal.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The researchers do not claim language models are superior.",
                "研究者的目的不是断言\n语言模型\n是否优于其他模型",
                "研究者并不试图断言语言模型是否优于其他模型",
            ),
            claim(
                "c02",
                "The purpose is to promote LLM visual-tokenization research.",
                "而是促进 LLM 视觉 tokenization 方法的探索。",
                "他们希望促进 LLM 视觉 tokenization 方法的探索。",
            ),
            claim(
                "c03",
                "Discrete visual tokens have the stated compatibility and infrastructure benefits.",
                "通过相同的 token 空间统一视觉和语言可以为真正的多模态 LLM 奠定基础",
            ),
        ),
        locked_literals=("语言模型", "LLM", "tokenization", "GPU/TPU"),
        voice_anchors=("真正的多模态 LLM",),
        retained_contrasts=(
            "The non-superiority claim and the actual research purpose remain explicit.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-09",
        genre="industry_reporting",
        doc_id="d4407ed937d0f78f325c3fbd",
        target_lines=(5, 10),
        original_sha256="3e518bdf98a9d703240370d4cec2754dfe557b9fbebb97fb7f91866f8254766f",
        operations=(
            operation(
                "contrast-v3-09-op-01",
                "remove_ornamental_emphasis",
                "换句话说，AI 解决不了所有问题，也并非所有问题都需要用 AI 解决，Agent 同理。",
                "AI 解决不了所有问题，也不是所有问题都需要用 AI 解决；Agent 同样如此。",
                "Remove a clarification announcement while preserving both negations.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The attributed quotation about business value remains verbatim.",
                "“技术的本质要看它能不能解决企业真正的问题，尤其当它跟核心业务绑定起来，就要回归业务场景去看技术有没有真正产生价值。”",
            ),
            claim(
                "c02",
                "Neither AI nor Agent solves every problem or is needed for every problem.",
                "AI 解决不了所有问题，也并非所有问题都需要用 AI 解决，Agent 同理。",
                "AI 解决不了所有问题，也不是所有问题都需要用 AI 解决；Agent 同样如此。",
            ),
            claim(
                "c03",
                "Agent capabilities and the old-tool counterexample remain unchanged.",
                "虽然换上了 AI Agent 的包装，但内核仍然是传统的 AI 工具。",
            ),
        ),
        locked_literals=("IBM", "AI", "Agent", "翟峰"),
        voice_anchors=("不必过度“神化”AI", "“新瓶装旧酒”"),
        retained_contrasts=(
            "AI and Agent limitations remain explicit negated claims.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-10",
        genre="industry_reporting",
        doc_id="3c33241e2bb2fd68fb3c6147",
        target_lines=(1, 7),
        original_sha256="06d52631383e2f06332a0d4e3e3c9d0e80f00b75eae10fab079f319a11445c9d",
        operations=(
            operation(
                "contrast-v3-10-op-01",
                "remove_ornamental_emphasis",
                "也正因如此，蚂蚁开源最新发布的《2025 ⼤模型开源开发⽣态全景与趋势》报告才显得格外有意义。",
                "在这一背景下，蚂蚁开源最新发布的《2025 ⼤模型开源开发⽣态全景与趋势》报告显得格外有意义。",
                "Replace a staged causal reveal with an explicit context link.",
            ),
            operation(
                "contrast-v3-10-op-02",
                "direct_contrast",
                "与其说这是一份关乎大模型开发生态的报告，不如说是给所有 AI 从业者的生存指南——",
                "这份报告关乎大模型开发生态，但更像是给所有 AI 从业者的生存指南——",
                "Preserve the stronger guide interpretation without the paired formula.",
            ),
            operation(
                "contrast-v3-10-op-03",
                "direct_contrast",
                "这种全景式数据报告不仅揭示了生态位的博弈逻辑，更为企业架构升级提供了清晰的路径。",
                "这种全景式数据报告揭示了生态位的博弈逻辑，也为企业架构升级提供了清晰的路径。",
                "State two additive claims without escalating the second as a reveal.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The report covers 19 technical fields, 135 projects, and seven trends.",
                "⼀共 19 个技术领域的 135 个项⽬，又对大模型开发生态的七个趋势做了深度解读。",
            ),
            claim(
                "c02",
                "The report is characterized as more like a survival guide.",
                "不如说是给所有 AI 从业者的生存指南",
                "更像是给所有 AI 从业者的生存指南",
            ),
            claim(
                "c03",
                "The report reveals ecosystem competition and offers an architecture-upgrade path.",
                "不仅揭示了生态位的博弈逻辑，更为企业架构升级提供了清晰的路径",
                "揭示了生态位的博弈逻辑，也为企业架构升级提供了清晰的路径",
            ),
        ),
        locked_literals=("蚂蚁开源", "AI", "19", "135", "《合作的进化》"),
        voice_anchors=("“AI 一天，人间一年”", "生存指南", "技术罗盘"),
        retained_contrasts=(
            "The report-versus-guide prioritization remains explicit.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-11",
        genre="industry_reporting",
        doc_id="9f693cf901d640ffb7312bd9",
        target_lines=(52, 57),
        original_sha256="f34f5dce6c78d01cf46e3acc5998a86dd8df05c1cb2000ec1792048d45224388",
        operations=(
            operation(
                "contrast-v3-11-op-01",
                "remove_ornamental_emphasis",
                "投资人对 AI 厂商能真正将这项技术转化为盈利业务的能力保持怀疑",
                "投资人对 AI 厂商将这项技术转化为盈利业务的能力保持怀疑",
                "Remove an unneeded actuality booster from the attributed market judgment.",
            ),
            operation(
                "contrast-v3-11-op-02",
                "clarify_argument_structure",
                "应用实践中，在对模型能力要求不是那么高的场景，企业会选择使用大小模型协同的方式。在性能和成本之间做取舍是不可避免的。小模型成本低但效果会打些折扣，但大小模型混合使用就能得到可接受的性能，同时成本下降比较明显，像 Apple Intelligence 就是采用了大小模型相结合的方式。",
                "在对模型能力要求较低的应用场景，企业会采用大小模型协同，在性能和成本之间取舍。小模型成本低，效果会打折；大小模型混合使用能够获得可接受的性能，同时明显降低成本。Apple Intelligence 就采用了大小模型结合的方式。",
                "Repair stacked adversatives while preserving the cost-performance tradeoff and example.",
            ),
            operation(
                "contrast-v3-11-op-03",
                "remove_ornamental_emphasis",
                "值得注意的是，业内整体模型的部署运维的效率并不高，像应用侧企业在前期在要效果和要效率之间，优先选择效果，虽然也未真正找到最佳的大模型应用范式。但在明年，部分企业将开始重点投入到运维效率上。",
                "业内模型的部署运维效率整体不高。应用侧企业前期在效果和效率之间优先选择效果，尚未找到最佳的大模型应用范式；明年，部分企业将开始重点投入运维效率。",
                "Remove attention and actuality framing while retaining the current limitation and future plan.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Investors remain skeptical about profitable commercialization.",
                "投资人对 AI 厂商能真正将这项技术转化为盈利业务的能力保持怀疑",
                "投资人对 AI 厂商将这项技术转化为盈利业务的能力保持怀疑",
            ),
            claim(
                "c02",
                "The listed optimization methods and DeepSeek-V3 details remain unchanged.",
                "Prefix caching、PD 分离、Continuous Batching、量化压缩、投机解码",
            ),
            claim(
                "c03",
                "Small and mixed models retain the stated cost-performance tradeoff and Apple example.",
                "Apple Intelligence 就是采用了大小模型相结合的方式",
                "Apple Intelligence 就采用了大小模型结合的方式",
            ),
            claim(
                "c04",
                "Deployment efficiency is low, the best pattern is not found, and investment is expected next year.",
                "部分企业将开始重点投入到运维效率上",
                "部分企业将开始重点投入运维效率",
            ),
        ),
        locked_literals=(
            "AI",
            "API",
            "DeepSeek-V3",
            "FP8",
            "GPU",
            "Apple Intelligence",
        ),
        voice_anchors=("绕不过去的话题", "价格战"),
        retained_contrasts=(
            "The small-model quality and cost tradeoff remains explicit.",
        ),
    ),
    Pair(
        pair_id="contrast-v3-12",
        genre="industry_reporting",
        doc_id="51ad0427b938c45e289e9d1a",
        target_lines=(1, 8),
        original_sha256="1868b13a13f172d1f44d94b63dd3afdffcf8cabca704a1e164a839c9c4ec84c3",
        operations=(
            operation(
                "contrast-v3-12-op-01",
                "direct_contrast",
                "科大讯飞发布业界首个长文本、长图文、长语音大模型，不仅能够把各种信息来源的海量文本、图文资料、会议录音等进行快速学习，还能够在各种行业场景给出专业、准确回答。",
                "科大讯飞发布业界首个长文本、长图文、长语音大模型，可以快速学习各种来源的海量文本、图文资料和会议录音，并在各类行业场景给出专业、准确的回答。",
                "State the two capabilities directly without additive escalation.",
            ),
            operation(
                "contrast-v3-12-op-02",
                "direct_contrast",
                "用户使用的最高峰不是周末，而是工作日的上午 9:30 和下午 3:30。这意味着，大部分用户用讯飞星火来解决和工作相关的刚需问题。",
                "用户使用高峰出现在工作日上午 9:30 和下午 3:30，而非周末。大部分用户用讯飞星火解决与工作相关的刚需问题。",
                "Preserve the weekday-versus-weekend evidence and its stated interpretation in direct sentences.",
            ),
            operation(
                "contrast-v3-12-op-03",
                "direct_contrast",
                "广大用户能拿到的资料往往不仅是现成的长文本，还有随手可见的报刊书籍内容、各种研讨会的 PPT 内容，老师黑板上的板书、同学的笔记，以及各种会议录音、访谈，各种网上的发布会、培训教育视频等，能不能把这些文本、图片、语音等都上传到讯飞星火中，快速地获取知识？",
                "广大用户能拿到的资料往往包括现成的长文本、报刊书籍、研讨会 PPT、老师的板书、同学的笔记，以及会议录音、访谈、网上发布会和培训教育视频。这些文本、图片和语音能否上传到讯飞星火中，让用户快速获取知识？",
                "Replace a not-only list frame with an explicit inventory while preserving the rhetorical question.",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The model supports long text, image-text, and speech learning plus industry answers.",
                "长文本、长图文、长语音大模型",
            ),
            claim(
                "c02",
                "Downloads exceed 96 million and rank first in the stated category.",
                "下载量已经超过 9600 万次，在国内工具类通用大模型 APP 中排名第一。",
            ),
            claim(
                "c03",
                "Usage peaks on weekdays at 9:30 and 3:30 rather than weekends.",
                "最高峰不是周末，而是工作日的上午 9:30 和下午 3:30",
                "使用高峰出现在工作日上午 9:30 和下午 3:30，而非周末",
            ),
            claim(
                "c04",
                "The complete source inventory and upload question remain present.",
                "各种会议录音、访谈，各种网上的发布会、培训教育视频",
                "会议录音、访谈、网上发布会和培训教育视频",
            ),
        ),
        locked_literals=("科大讯飞", "讯飞星火", "APP", "PPT", "9600", "9:30", "3:30"),
        voice_anchors=("能否上传到讯飞星火中",),
        retained_contrasts=("Weekday and weekend usage remain explicitly contrasted.",),
    ),
)


ALLOWED_OPERATORS = {
    "clarify_argument_structure",
    "direct_contrast",
    "merge_repeated_reframing",
    "remove_ornamental_emphasis",
}
MARKERS = (
    "值得注意的是",
    "需要强调的是",
    "换句话说",
    "也正因如此",
    "相反",
    "这样一来",
    "不仅仅",
    "不仅",
    "真正",
    "本质上",
)
NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]+\d[\dA-Za-z.+:/%-]*|\d[\d.,:/–—-]*(?:\s*[%+]|[A-Za-z]+)?)(?![A-Za-z0-9])"
)


LABEL_CONFIG = """<View>
  <Header value="只比较阅读体验，不判断哪一版是 AI" />
  <View style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
    <View style="padding: 16px; border: 1px solid #d9d9d9; border-radius: 8px;">
      <Header value="版本 A" />
      <Text name="version_a" value="$version_a" style="white-space: pre-wrap;" />
    </View>
    <View style="padding: 16px; border: 1px solid #d9d9d9; border-radius: 8px;">
      <Header value="版本 B" />
      <Text name="version_b" value="$version_b" style="white-space: pre-wrap;" />
    </View>
  </View>
  <Header value="哪个版本让你更愿意继续读？" />
  <Choices name="preference" toName="version_a" choice="single" required="true" showInline="true">
    <Choice value="A，更愿意继续读" />
    <Choice value="B，更愿意继续读" />
    <Choice value="差不多或都不想继续读" />
  </Choices>
  <Header value="可选评论" />
  <TextArea name="optional_comment" toName="version_a" rows="3" placeholder="可以留空" />
</View>
"""


def select_lines(lines: list[str], start: int, end: int) -> str:
    return "\n".join(line.strip() for line in lines[start - 1 : end] if line.strip())


def apply_operations(original: str, operations: tuple[Operation, ...]) -> str:
    revised = original
    for item in operations:
        count = revised.count(item.before)
        if count != 1:
            raise ValueError(
                f"{item.operation_id}: expected one source span, found {count}"
            )
        revised = revised.replace(item.before, item.after, 1)
    return revised


def number_literals(text: str) -> list[str]:
    return sorted(set(NUMBER_PATTERN.findall(text)))


def marker_count(text: str) -> int:
    return sum(text.count(marker) for marker in MARKERS)


def load_pool(path: Path) -> dict[str, dict[str, object]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {str(row["doc_id"]): row for row in rows}


def validate_pair(
    pair: Pair,
    metadata: dict[str, object],
    original: str,
    revised: str,
) -> dict[str, object]:
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
    if digest != pair.original_sha256:
        raise ValueError(f"{pair.pair_id}: source hash changed")
    if metadata.get("period") != "transition":
        raise ValueError(f"{pair.pair_id}: source is not transition material")
    if metadata.get("provenance_status") not in {
        "human_reviewed_original",
        "model_assisted_original",
    }:
        raise ValueError(f"{pair.pair_id}: source provenance is not admitted")
    if pair.doc_id == "55a8c05716103aaced6ecf7f":
        raise ValueError(
            f"{pair.pair_id}: reader-observed development case is excluded"
        )
    if original == revised:
        raise ValueError(f"{pair.pair_id}: revision is unchanged")
    unknown = {item.operator for item in pair.operations} - ALLOWED_OPERATORS
    if unknown:
        raise ValueError(f"{pair.pair_id}: unknown operators {unknown}")
    if number_literals(original) != number_literals(revised):
        raise ValueError(
            f"{pair.pair_id}: numeric literals changed: "
            f"{number_literals(original)} != {number_literals(revised)}"
        )
    for literal in pair.locked_literals:
        if literal not in original or literal not in revised:
            raise ValueError(f"{pair.pair_id}: locked literal missing: {literal}")
    for check in pair.claim_checks:
        if check.original_support not in original:
            raise ValueError(
                f"{pair.pair_id}/{check.claim_id}: original support missing"
            )
        if check.revised_support not in revised:
            raise ValueError(
                f"{pair.pair_id}/{check.claim_id}: revised support missing"
            )
    for anchor in pair.voice_anchors:
        if anchor not in revised:
            raise ValueError(f"{pair.pair_id}: voice anchor missing: {anchor}")
    matcher = difflib.SequenceMatcher(a=original, b=revised, autojunk=False)
    return {
        "claim_checks_passed": len(pair.claim_checks),
        "locked_literals_passed": len(pair.locked_literals),
        "numeric_literals": number_literals(original),
        "numeric_preservation_passed": True,
        "original_marker_count": marker_count(original),
        "revised_marker_count": marker_count(revised),
        "source_hash_passed": True,
        "unchanged_character_ratio": round(matcher.ratio(), 6),
        "voice_anchors_passed": len(pair.voice_anchors),
    }


def build_artifacts(
    pool_path: Path,
    seed: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    if len(PAIRS) != 12 or len({pair.doc_id for pair in PAIRS}) != 12:
        raise ValueError("Round three requires 12 pairs from 12 distinct documents")
    genre_counts = Counter(pair.genre for pair in PAIRS)
    if genre_counts != {
        "industry_reporting": 4,
        "research_summary": 4,
        "technical_practice": 4,
    }:
        raise ValueError(f"Unexpected genre balance: {genre_counts}")
    pool = load_pool(pool_path)
    prepared: list[tuple[Pair, str, str, dict[str, object]]] = []
    for pair in PAIRS:
        metadata = pool[pair.doc_id]
        lines = (
            Path(str(metadata["body_path"])).read_text(encoding="utf-8").splitlines()
        )
        original = select_lines(lines, *pair.target_lines)
        revised = apply_operations(original, pair.operations)
        validation = validate_pair(pair, metadata, original, revised)
        prepared.append((pair, original, revised, validation))

    rng = random.Random(seed)
    rng.shuffle(prepared)
    sides = [True] * 6 + [False] * 6
    rng.shuffle(sides)
    tasks: list[dict[str, object]] = []
    answer_key: list[dict[str, object]] = []
    side_counts = Counter()
    for task_number, (
        (pair, original, revised, validation),
        original_is_a,
    ) in enumerate(zip(prepared, sides, strict=True), start=1):
        original_side = "A" if original_is_a else "B"
        side_counts[original_side] += 1
        tasks.append(
            {
                "data": {
                    "task_number": task_number,
                    "version_a": original if original_is_a else revised,
                    "version_b": revised if original_is_a else original,
                },
                "meta": {"pair_id": pair.pair_id},
            }
        )
        answer_key.append(
            {
                "pair_id": pair.pair_id,
                "task_number": task_number,
                "doc_id": pair.doc_id,
                "genre": pair.genre,
                "target_lines": list(pair.target_lines),
                "original_side": original_side,
                "original": original,
                "revised": revised,
                "operations": [asdict(item) for item in pair.operations],
                "claim_checks": [asdict(item) for item in pair.claim_checks],
                "locked_literals": list(pair.locked_literals),
                "retained_contrasts": list(pair.retained_contrasts),
                "voice_anchors": list(pair.voice_anchors),
                "validation": validation,
            }
        )
    diagnostics = {
        "pair_count": len(PAIRS),
        "distinct_document_count": len({pair.doc_id for pair in PAIRS}),
        "genre_counts": dict(sorted(genre_counts.items())),
        "operation_count": sum(len(pair.operations) for pair in PAIRS),
        "claim_check_count": sum(len(pair.claim_checks) for pair in PAIRS),
        "original_side_counts": dict(sorted(side_counts.items())),
        "original_marker_count": sum(
            item[3]["original_marker_count"] for item in prepared
        ),
        "revised_marker_count": sum(
            item[3]["revised_marker_count"] for item in prepared
        ),
        "all_preservation_gates_passed": True,
    }
    return tasks, answer_key, diagnostics


def write_json(path: Path, value: object) -> None:
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
    tasks, answer_key, diagnostics = build_artifacts(args.pool, args.seed)
    protocol = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "status": "frozen_before_outcomes",
        "frozen_at": "2026-08-22",
        "seed": args.seed,
        "role": "development_intervention_not_validation",
        "reader_question": "Which version makes the reader more willing to continue?",
        "source_policy": {
            "period": "transition",
            "discovery_exposed": True,
            "reader_observed_case_excluded": True,
            "prior_intervention_documents_excluded": True,
        },
        "operator_policy": [
            "Reduce ornamental contrast, clarification, and emphasis framing.",
            "Retain necessary contrasts, negation, modality, attribution, and uncertainty.",
            "Preserve explicit subjects, predicates, objects, and referents.",
            "Preserve propositions, entities, numbers, technical terms, and authorial voice.",
            "Do not maximize compression or turn the passage into uniformly flat prose.",
        ],
        "generation_diagnostics": diagnostics,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "tasks.json", tasks)
    write_json(args.output_dir / "answer_key.json", answer_key)
    write_json(args.output_dir / "protocol.json", protocol)
    (args.output_dir / "label_config.xml").write_text(
        LABEL_CONFIG, encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir.resolve()),
                "protocol_version": PROTOCOL_VERSION,
                **diagnostics,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
