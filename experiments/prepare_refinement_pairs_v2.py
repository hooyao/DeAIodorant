"""Prepare the frozen second-round blinded refinement experiment."""

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


SCHEMA_VERSION = "deaiodorant-refinement-pairs-2.0"
PROTOCOL_VERSION = "conservative-contrast-reduction-2.0"
DEFAULT_SEED = 20260821


@dataclass(frozen=True)
class Operation:
    operation_id: str
    operator: str
    before: str
    after: str
    reason: str
    preserved_claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClaimCheck:
    claim_id: str
    description: str
    original_support: str
    revised_support: str


@dataclass(frozen=True)
class Pair:
    pair_id: str
    doc_id: str
    month: str
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
    *preserved_claim_ids: str,
) -> Operation:
    return Operation(
        operation_id=operation_id,
        operator=operator,
        before=before,
        after=after,
        reason=reason,
        preserved_claim_ids=tuple(preserved_claim_ids),
    )


def claim(
    claim_id: str,
    description: str,
    original_support: str,
    revised_support: str | None = None,
) -> ClaimCheck:
    return ClaimCheck(
        claim_id=claim_id,
        description=description,
        original_support=original_support,
        revised_support=revised_support or original_support,
    )


PAIRS = (
    Pair(
        pair_id="contrast-v2-01",
        doc_id="b77b09a419c1631227112f0c",
        month="2026-03",
        target_lines=(7, 10),
        original_sha256=(
            "37fb319e9d82276eb2f92187cb88a647006ebf859c7ddafa385929b285c88fc8"
        ),
        operations=(
            operation(
                "contrast-v2-01-op-01",
                "remove_ornamental_emphasis",
                "当多智能体协作成为常态，如何控制算力成本成为企业面临的核心挑战之一。",
                "多智能体协作成为常态后，企业必须控制算力成本。",
                "State the operational constraint without importance framing.",
                "c02",
            ),
            operation(
                "contrast-v2-01-op-02",
                "remove_ornamental_emphasis",
                "是行业亟待解决的核心问题。",
                "是行业亟须解决的算力配置问题。",
                "Replace generic importance language with the named problem.",
                "c04",
            ),
            operation(
                "contrast-v2-01-op-03",
                "clarify_argument_structure",
                (
                    "正是在这样的行业背景下，aiXcoder 推出更适合企业私有化部署的 "
                    "aiX-apply-4B 轻量级模型，服务于代码变更应用场景。这一场景的核心"
                    "挑战在于，需要将模型生成的不规整、碎片化的代码片段，精准、无损地"
                    "应用到原始文件中，同时严格保持缩进、空白符、上下文的一致性，不牵动"
                    "其他代码、避免引入新问题。"
                ),
                (
                    "为应对这一行业背景，aiXcoder 推出了更适合企业私有化部署的 "
                    "aiX-apply-4B 轻量级模型，服务于代码变更应用场景。这个场景要求模型"
                    "把生成的不规整、碎片化代码片段精准、无损地应用到原始文件中，同时"
                    "严格保持缩进、空白符和上下文一致，不牵动其他代码，避免引入新问题。"
                ),
                "Name the actor and requirement directly while retaining every constraint.",
                "c05",
                "c06",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Multi-agent work raises model-call and token demand.",
                "一个复杂任务的完成往往需要 10 到 50 次模型调用，并发场景下的 Token 消耗更是达到传统模式的数倍甚至数十倍。",
            ),
            claim(
                "c02",
                "Extra calls consume scarce private capacity, raise latency, and reduce concurrency.",
                "每一次额外的模型调用，都在消耗本就紧张的算力资源，推高延迟的同时挤占并发能力。",
            ),
            claim(
                "c03",
                "Public-cloud and very large private deployments have stated security and cost limits.",
                "公有云“烧”Token 的模式无法满足企业数据安全需求，私有化部署千亿级、万亿级大模型成本高昂且容易导致算力空转浪费。",
            ),
            claim(
                "c04",
                "The industry needs to allocate finite compute to the highest-need development tasks.",
                "如何将有限算力实现最优配置，让每一份算力都能落到最需要的研发场景中去",
            ),
            claim(
                "c05",
                "aiXcoder introduced aiX-apply-4B for private code-change application.",
                "aiXcoder 推出更适合企业私有化部署的 aiX-apply-4B 轻量级模型，服务于代码变更应用场景",
                "aiXcoder 推出了更适合企业私有化部署的 aiX-apply-4B 轻量级模型，服务于代码变更应用场景",
            ),
            claim(
                "c06",
                "Applying fragments must preserve formatting and avoid collateral code changes.",
                "严格保持缩进、空白符、上下文的一致性，不牵动其他代码、避免引入新问题",
                "严格保持缩进、空白符和上下文一致，不牵动其他代码，避免引入新问题",
            ),
        ),
        locked_literals=(
            "OpenClaw",
            "Token",
            "金融",
            "通信",
            "能源",
            "航天",
            "公有云",
            "私有化部署",
            "aiXcoder",
            "aiX-apply-4B",
        ),
        voice_anchors=("算力“就这么多”",),
        retained_contrasts=(
            "The public-cloud security limitation and private-deployment cost limitation remain explicit.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-02",
        doc_id="a127f5baf364930a89fb4005",
        month="2025-10",
        target_lines=(8, 15),
        original_sha256=(
            "460a453441e0cd40ff816ebcbba231f1dd9ef98c7fc772beaa14e7ef0df6c962"
        ),
        operations=(
            operation(
                "contrast-v2-02-op-01",
                "remove_ornamental_emphasis",
                "这正是我们希望解决的难题。",
                "我们希望解决这个性能问题。",
                "Replace an emphatic reveal with an explicit referent.",
                "c06",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The first N JSON paths are dynamic subcolumns and the remaining paths share a Map column.",
                "前 N 个路径作为“动态路径”被存储为子列。其余 K – N 个路径则被存储在一个共享的数据结构中",
            ),
            claim(
                "c02",
                "A dynamic key can be read directly and efficiently.",
                "key1 属于动态路径，因此其值被存储在独立的数据文件中，能够被高效、直接地读取。",
            ),
            claim(
                "c03",
                "A shared key requires reading and filtering the full Map column.",
                "ClickHouse 需要读取整个 Map(String, String) 列并在内存中进行过滤处理，效率显著下降。",
            ),
            claim(
                "c04",
                "Raising the 1024 path limit can increase file count, memory, and read complexity, especially on S3.",
                "贸然提高该限制并不可取，因为每个分区可能生成成千上万的文件，这会在数据合并过程中显著增加内存使用量，并加剧读取复杂度。",
            ),
            claim(
                "c05",
                "Very high JSON path cardinality reduces performance.",
                "对于包含成千上万乃至数万个唯一 JSON 路径的工作负载，系统性能会明显下降。",
            ),
            claim(
                "c06",
                "ClickHouse intends to solve the described performance problem.",
                "这正是我们希望解决的难题。",
                "我们希望解决这个性能问题。",
            ),
            claim(
                "c07",
                "v25.8 introduced two shared-data serialization formats for more efficient path reads.",
                "ClickHouse v25.8 推出了两种新的共享数据序列化格式，显著提升了读取特定路径时的效率。",
            ),
        ),
        locked_literals=(
            "ClickHouse",
            "JSON",
            "Map(String, String)",
            "S3",
            "key1",
            "key_n+1",
            "v25.8",
        ),
        voice_anchors=("我们希望解决",),
        retained_contrasts=(
            "The dynamic-path versus shared-data distinction remains unchanged.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-03",
        doc_id="3c60dc0a981b686870095450",
        month="2026-06",
        target_lines=(3, 7),
        original_sha256=(
            "321eae8d3048f67acede2dc77ba901d48b3ca98d487f8722d96ec1ed13d28a09"
        ),
        operations=(
            operation(
                "contrast-v2-03-op-01",
                "direct_contrast",
                "这意味着 Agent 不再只出现在客服、运营、研发等业务系统里，也正被嵌入云运维、架构设计与资源治理的工作流。",
                "Agent 的应用已不再局限于客服、运营、研发等业务系统，也进入了云运维、架构设计与资源治理的工作流。",
                "Remove conclusion-announcement framing but preserve the expansion and negation.",
                "c02",
            ),
            operation(
                "contrast-v2-03-op-02",
                "remove_ornamental_emphasis",
                "值得注意的是，这些加速落地的 Agent，几乎都离不开云。",
                "这些加速落地的 Agent 几乎都离不开云。",
                "Remove an attention directive while preserving the qualifier.",
                "c03",
            ),
            operation(
                "contrast-v2-03-op-03",
                "direct_contrast",
                (
                    "于是一个新问题出现：当云资源被越来越多的 Agent 调用，云平台本身需"
                    "不需要改变？\nAgent 自主规划、高批量、长任务的特性，让这个问题不言而喻"
                    "——不仅需要改变，甚至需要重构。而阿里云正围绕这一需求加快演进。"
                ),
                (
                    "这也带来一个新问题：当云资源被越来越多的 Agent 调用，云平台本身需"
                    "不需要改变？\nAgent 自主规划、高批量、长任务的特性给出了答案：云平台"
                    "需要改变，甚至需要重构。阿里云正围绕这一需求加快演进。"
                ),
                "Keep the question and escalation while removing a staged not-only reveal.",
                "c04",
                "c05",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The survey reports 79% current or planned Agent adoption and nearly 74% expected Agentic AI use within two years.",
                "79% 的企业在内部采用或正规划采用 AI Agent，近 74% 的企业预计两年内会用上 Agentic AI。",
            ),
            claim(
                "c02",
                "Agent use is no longer limited to business systems and now includes cloud workflows.",
                "Agent 不再只出现在客服、运营、研发等业务系统里，也正被嵌入云运维、架构设计与资源治理的工作流。",
                "Agent 的应用已不再局限于客服、运营、研发等业务系统，也进入了云运维、架构设计与资源治理的工作流。",
            ),
            claim(
                "c03",
                "Nearly all of the described Agent workloads depend on named cloud resources.",
                "这些加速落地的 Agent，几乎都离不开云。大模型推理、向量检索、任务调度、复杂业务的编排与集成，背后都要依托云端的算力、存储、网络与安全。",
                "这些加速落地的 Agent 几乎都离不开云。大模型推理、向量检索、任务调度、复杂业务的编排与集成，背后都要依托云端的算力、存储、网络与安全。",
            ),
            claim(
                "c04",
                "Increasing Agent use raises the question of cloud-platform change.",
                "当云资源被越来越多的 Agent 调用，云平台本身需不需要改变？",
            ),
            claim(
                "c05",
                "Agent autonomy, scale, and duration require change or reconstruction, and Alibaba Cloud is evolving accordingly.",
                "不仅需要改变，甚至需要重构。而阿里云正围绕这一需求加快演进。",
                "云平台需要改变，甚至需要重构。阿里云正围绕这一需求加快演进。",
            ),
        ),
        locked_literals=(
            "AI Agent",
            "Agentic AI",
            "客服",
            "运营",
            "研发",
            "云运维",
            "架构设计",
            "资源治理",
            "阿里云",
        ),
        voice_anchors=("云平台本身需不需要改变？",),
        retained_contrasts=(
            "The text still states that Agent use is not limited to business systems.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-04",
        doc_id="3c60dc0a981b686870095450",
        month="2026-06",
        target_lines=(51, 58),
        original_sha256=(
            "ba6ec10acecbd44ba1a7822ac2cd4b7b08285e3ab2d286553a477beda8edb491"
        ),
        operations=(
            operation(
                "contrast-v2-04-op-01",
                "merge_repeated_reframing",
                (
                    "这里的关键在于，阿里云没有让 Agent 绕过既有工程体系，直接裸调 API。\n"
                    "相反，它让 Agent 沿着成熟工具链进入云：CLI 负责命令执行，SDK 负责程序"
                    "化接入，Terraform 承接 IaC 编排和状态管理，MCP Server 则把云能力以标准"
                    "方式暴露给 Agent。\n这样一来，Agent 的能力不再悬浮在自然语言上，而是"
                    "落进一条可校验、可审计、可回滚的工程链路里。"
                ),
                (
                    "阿里云没有让 Agent 绕过既有工程体系、直接裸调 API，而是让它沿着成熟"
                    "工具链进入云：CLI 负责命令执行，SDK 负责程序化接入，Terraform 承接 "
                    "IaC 编排和状态管理，MCP Server 把云能力以标准方式暴露给 Agent。\n这样，"
                    "Agent 的能力进入一条可校验、可审计、可回滚的工程链路，不再悬浮在自然"
                    "语言上。"
                ),
                "Combine three repeated frames while retaining the necessary bypass contrast and every tool role.",
                "c02",
                "c03",
            ),
            operation(
                "contrast-v2-04-op-02",
                "direct_contrast",
                "它真正解决的，不只是让 Agent 更容易调云，而是让企业敢把一部分云操作交给 Agent。",
                "这套体系让 Agent 更容易调云，也让企业敢把一部分云操作交给 Agent。",
                "State both additive outcomes without presenting the second as a revelation.",
                "c05",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Skills organize more than 300 products and 20,000 APIs, while Toolkit provides engineering access.",
                "Agentic Skills 的作用，是把 300 多个云产品、2 万多个 API，重新组织成 Agent 能理解、能选择、能组合、能安全调用的 Skills。Agent Toolkit 则负责工程接入",
            ),
            claim(
                "c02",
                "Alibaba Cloud does not let Agent bypass the engineering system and directly call raw APIs.",
                "阿里云没有让 Agent 绕过既有工程体系，直接裸调 API。",
                "阿里云没有让 Agent 绕过既有工程体系、直接裸调 API",
            ),
            claim(
                "c03",
                "CLI, SDK, Terraform, and MCP Server retain their stated roles in a verifiable, auditable, reversible chain.",
                "CLI 负责命令执行，SDK 负责程序化接入，Terraform 承接 IaC 编排和状态管理，MCP Server 则把云能力以标准方式暴露给 Agent。",
                "CLI 负责命令执行，SDK 负责程序化接入，Terraform 承接 IaC 编排和状态管理，MCP Server 把云能力以标准方式暴露给 Agent。",
            ),
            claim(
                "c04",
                "The three layers assign entry, identity, capability, consumption, intervention, and observability responsibilities.",
                "Gateway 管入口和行为，3A 管身份和权限，Skills 管能力表达，Toolkit 管工具消费，HITL 管高危介入，可观测体系管全程追踪。",
            ),
            claim(
                "c05",
                "The system makes cloud use easier and gives enterprises confidence to delegate some operations.",
                "不只是让 Agent 更容易调云，而是让企业敢把一部分云操作交给 Agent。",
                "让 Agent 更容易调云，也让企业敢把一部分云操作交给 Agent。",
            ),
            claim(
                "c06",
                "Manageability precedes trust, usability, and automation.",
                "先可管，再可信；先可信，再可用；最后才谈自动化。",
            ),
        ),
        locked_literals=(
            "Agentic Skills",
            "Agent Toolkit",
            "API",
            "CLI",
            "SDK",
            "Terraform",
            "IaC",
            "MCP Server",
            "Gateway",
            "3A",
            "HITL",
        ),
        voice_anchors=("先可管，再可信；先可信，再可用；最后才谈自动化。",),
        retained_contrasts=(
            "The no-bypass requirement remains an explicit negative contrast.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-05",
        doc_id="3c60dc0a981b686870095450",
        month="2026-06",
        target_lines=(59, 68),
        original_sha256=(
            "a5dd3e119a0b4ec0225932e400be9880bdac2abfc453f428fcd574b51fbbcd55"
        ),
        operations=(
            operation(
                "contrast-v2-05-op-01",
                "clarify_argument_structure",
                "在 Agent 调云的链路里，最容易失控的一步，是从自然语言直接跳到执行。",
                "在 Agent 调云的链路里，从自然语言直接跳到执行最容易失控。",
                "Remove a cleft frame without changing the risk claim.",
                "c01",
            ),
            operation(
                "contrast-v2-05-op-02",
                "remove_ornamental_emphasis",
                "它的核心约束很简单：Agent 不能从自然语言直接进入执行，必须先从意图进入规格。",
                "这套约束要求 Agent 不能从自然语言直接进入执行，必须先从意图进入规格。",
                "Keep both modal constraints and remove generic importance framing.",
                "c04",
            ),
            operation(
                "contrast-v2-05-op-03",
                "direct_contrast",
                "这里的关键在于：Agent 不是绕开现有工程体系，而是进入 IaC 路径。",
                "Agent 由此沿现有工程体系进入 IaC 路径，而不会绕开它。",
                "Preserve the real engineering-path contrast in a direct causal sentence.",
                "c07",
            ),
            operation(
                "contrast-v2-05-op-04",
                "remove_ornamental_emphasis",
                "IaC 的价值正在这里：它让云资源的变化有记录、有版本、有边界，也有恢复路径。",
                "IaC 因此让云资源的变化有记录、有版本、有边界，也有恢复路径。",
                "Replace value-announcement framing with the explicit consequence.",
                "c08",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Directly moving from natural language to execution is the most failure-prone step.",
                "最容易失控的一步，是从自然语言直接跳到执行。",
                "从自然语言直接跳到执行最容易失控。",
            ),
            claim(
                "c02",
                "Immediate website provisioning can be risky because language is vague and cloud operations are precise.",
                "自然语言是模糊的，云操作却是精确的。中间如果没有一个可确认、可校验的方案，模型的推理结果就会直接变成基础设施变更。",
            ),
            claim(
                "c03",
                "Enterprises have difficulty accepting that path.",
                "企业很难接受这种路径。",
            ),
            claim(
                "c04",
                "SDD requires a specification between intent and execution.",
                "Agent 不能从自然语言直接进入执行，必须先从意图进入规格。",
            ),
            claim(
                "c05",
                "Spec stabilizes the transition from intent to execution.",
                "Spec 是意图与执行之间的稳定器。",
            ),
            claim(
                "c06",
                "The website example lists resource, disk, network, port, cost, alternative, and best-practice questions.",
                "部署在哪类资源上？实例规格是什么？磁盘多大？网络如何隔离？安全组开放哪些端口？预计费用是多少？有没有更低成本的版本？是否符合最佳实践？",
            ),
            claim(
                "c07",
                "After confirmation, Agent converts Spec to Terraform or IaC without bypassing the engineering system.",
                "Agent 不是绕开现有工程体系，而是进入 IaC 路径。",
                "Agent 由此沿现有工程体系进入 IaC 路径，而不会绕开它。",
            ),
            claim(
                "c08",
                "One ECS and ten thousand ECS instances require different handling, and IaC preserves operational controls.",
                "创建一台 ECS，和批量创建一万台 ECS，不是同一件事。前者可以是一次操作，后者必须是可声明、可复用、可审计、可回滚的基础设施管理。",
            ),
        ),
        locked_literals=(
            "Agent",
            "ECS",
            "SDD",
            "Spec-Driven Development",
            "Spec",
            "Terraform",
            "IaC",
        ),
        voice_anchors=("帮我搭一个网站", "稳定器"),
        retained_contrasts=(
            "The ban on direct execution and the one-versus-ten-thousand ECS distinction remain explicit.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-06",
        doc_id="3c60dc0a981b686870095450",
        month="2026-06",
        target_lines=(82, 90),
        original_sha256=(
            "cb7bdee990667950fbb68a43636d8fd62e3abe71fe1f480aa4470335c5101a23"
        ),
        operations=(
            operation(
                "contrast-v2-06-op-01",
                "direct_contrast",
                "事实上，Skills 改变的不只是接口体系，还有“云能力”的流通方式。",
                "Skills 同时改变了接口体系和“云能力”的流通方式。",
                "State the two effects as additive claims without a staged not-only frame.",
                "c01",
            ),
            operation(
                "contrast-v2-06-op-02",
                "merge_repeated_reframing",
                (
                    "Skills 平台的价值就在这里。\n它不是简单把 API 包一层，而是把稳定的 "
                    "API、场景化 SOP、权限边界和调用规则，打包成一个 Agent 能理解、能调用、"
                    "能组合的能力单元。\n云 Skills 门户也不是传统产品目录，而是面向 Agent 的云"
                    "能力入口。"
                ),
                (
                    "Skills 平台并非只给 API 加一层包装；它把稳定的 API、场景化 SOP、权限"
                    "边界和调用规则打包成一个 Agent 能理解、能调用、能组合的能力单元。\n云 "
                    "Skills 门户面向 Agent 提供云能力入口，不沿用传统产品目录的定位。"
                ),
                "Remove value and repeated reversal announcements while retaining both substantive distinctions.",
                "c05",
                "c06",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Skills changes both the interface system and cloud-capability circulation.",
                "Skills 改变的不只是接口体系，还有“云能力”的流通方式。",
                "Skills 同时改变了接口体系和“云能力”的流通方式。",
            ),
            claim(
                "c02",
                "Cloud capabilities were distributed across documents, tools, and experience, creating repeated work.",
                "它们散落在 API 文档、SDK、脚本和工程师经验里。开发者要先读文档，再写代码；企业要自己补权限、审计和风控；平台每做一次集成，也要重复大量基础工作。",
            ),
            claim(
                "c03",
                "Agent amplifies API quality problems because it lacks engineer experience.",
                "但 Agent 没有这样的经验，它只能依赖结构化、明确、稳定的能力描述。",
            ),
            claim(
                "c04",
                "Real cloud operations are multi-step procedures that need SOPs.",
                "真实的云操作也很少只是调用一个 API。它通常是一串动作：先做什么、再做什么，失败后怎么办，哪些步骤需要确认。这些都需要沉淀成 SOP。",
            ),
            claim(
                "c05",
                "Skills packages APIs, SOPs, permissions, and invocation rules rather than merely wrapping APIs.",
                "它不是简单把 API 包一层，而是把稳定的 API、场景化 SOP、权限边界和调用规则，打包成一个 Agent 能理解、能调用、能组合的能力单元。",
                "Skills 平台并非只给 API 加一层包装；它把稳定的 API、场景化 SOP、权限边界和调用规则打包成一个 Agent 能理解、能调用、能组合的能力单元。",
            ),
            claim(
                "c06",
                "The portal is an Agent-facing capability entry, with external co-development and internal reuse.",
                "云 Skills 门户也不是传统产品目录，而是面向 Agent 的云能力入口。",
                "云 Skills 门户面向 Agent 提供云能力入口，不沿用传统产品目录的定位。",
            ),
        ),
        locked_literals=(
            "Skills",
            "API",
            "SDK",
            "SOP",
            "Agent",
            "Skill Forge",
            "Workflow",
        ),
        voice_anchors=("云能力是“重”的",),
        retained_contrasts=(
            "The API-wrapper and traditional-product-catalog exclusions remain explicit because both are substantive.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-07",
        doc_id="44aa81958a6c585ee8c06847",
        month="2026-01",
        target_lines=(1, 6),
        original_sha256=(
            "df43bd6e7b3328ff92434300f1c871d29ec505fc6571750973cb95b7ee95b597"
        ),
        operations=(
            operation(
                "contrast-v2-07-op-01",
                "merge_repeated_reframing",
                (
                    "企业级多智能体（Multi-Agent）系统最大的瓶颈，往往不是 Agent 不够强，"
                    "而是负责分发任务的 Router（路由器）太“傻”。传统 Router 只会做简单的"
                    "单选分类，面对复杂的企业级故障经常“瞎指挥”，在企业运维的十字路口，"
                    "我们需要一个更聪明的“交警”。"
                ),
                (
                    "企业级多智能体（Multi-Agent）系统最大的瓶颈，往往不在 Agent 的能力，"
                    "而在负责分发任务的 Router（路由器）。传统 Router 只会做简单的单选分类，"
                    "面对复杂的企业级故障经常“瞎指挥”，企业运维因此需要更聪明的路由决策。"
                ),
                "Retain the real component contrast and one voice cue while removing stacked personification.",
                "c01",
            ),
            operation(
                "contrast-v2-07-op-02",
                "clarify_argument_structure",
                (
                    "过去一年里，Multi-Agent 架构正在成为企业 AI 的新基建。我们忙着造更强"
                    "的 SQLAgent、更快的检索 Agent，但却发现运维系统的十字路口却越来越拥堵了。"
                ),
                (
                    "过去一年里，Multi-Agent 架构正在成为企业 AI 的新基建。SQLAgent 和检索 "
                    "Agent 越来越强，运维系统的“十字路口”却越来越拥堵。"
                ),
                "Remove duplicated adversative wording and keep the traffic metaphor for rhythm.",
                "c02",
            ),
            operation(
                "contrast-v2-07-op-03",
                "clarify_argument_structure",
                (
                    "和想象中的 Agent 们“游刃有余”的自动协同、分工协作不同，因为传统 "
                    "Router 的上限太低、智能程度有限，很难跟上 Agent 们“匆匆忙忙”的脚步。"
                ),
                (
                    "现实中的自动协同和分工协作并不像想象中那样“游刃有余”：传统 Router "
                    "的上限太低、智能程度有限，很难跟上 Agent 的变化。"
                ),
                "Restore an explicit main clause and preserve the contrast and limitation.",
                "c03",
            ),
            operation(
                "contrast-v2-07-op-04",
                "clarify_argument_structure",
                (
                    "今天，腾讯云正式开源 TCAR（Tencent Cloud Andon Router）——\n一个只有 "
                    "4B 参数，但学会了“先想清楚，再选择”的智能路由模型\n，它专为解决跨域、"
                    "冲突和模糊问题而生，为企业 AI 应用提供 Reasoning-centric Routing+Multi-"
                    "Agent Collaboration 的基础形态。"
                ),
                (
                    "今天，腾讯云正式开源 TCAR（Tencent Cloud Andon Router）。这个只有 4B "
                    "参数的智能路由模型学会了“先想清楚，再选择”，专门解决跨域、冲突和模糊"
                    "问题，并为企业 AI 应用提供 Reasoning-centric Routing+Multi-Agent "
                    "Collaboration 的基础形态。"
                ),
                "Repair interrupted subject-predicate structure without compressing the product claims.",
                "c05",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The claimed bottleneck lies in Router rather than Agent capability, and simple classification misroutes complex faults.",
                "往往不是 Agent 不够强，而是负责分发任务的 Router（路由器）太“傻”",
                "往往不在 Agent 的能力，而在负责分发任务的 Router（路由器）",
            ),
            claim(
                "c02",
                "Multi-Agent is becoming infrastructure while stronger specialized agents increase routing congestion.",
                "Multi-Agent 架构正在成为企业 AI 的新基建",
            ),
            claim(
                "c03",
                "Traditional Router limits automatic coordination and division of work.",
                "传统 Router 的上限太低、智能程度有限，很难跟上 Agent 们“匆匆忙忙”的脚步。",
                "传统 Router 的上限太低、智能程度有限，很难跟上 Agent 的变化。",
            ),
            claim(
                "c04",
                "Future systems must acknowledge uncertainty and resolve it collaboratively.",
                "系统必须具备“承认不确定性并协作解决”的能力。",
            ),
            claim(
                "c05",
                "Tencent Cloud open-sourced the 4B TCAR model for cross-domain, conflict, and ambiguity problems.",
                "腾讯云正式开源 TCAR（Tencent Cloud Andon Router）",
            ),
        ),
        locked_literals=(
            "Multi-Agent",
            "Agent",
            "Router",
            "SQLAgent",
            "腾讯云",
            "TCAR",
            "Tencent Cloud Andon Router",
            "Reasoning-centric Routing+Multi-Agent Collaboration",
        ),
        voice_anchors=("“十字路口”", "“先想清楚，再选择”"),
        retained_contrasts=(
            "The Agent-capability versus Router-bottleneck distinction remains explicit.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-08",
        doc_id="48bda219eb0776f623161899",
        month="2026-01",
        target_lines=(17, 21),
        original_sha256=(
            "4f9ad653da6ace7292ed1955e037d9660cad499334b2ba731a28f44bb0917d32"
        ),
        operations=(
            operation(
                "contrast-v2-08-op-01",
                "direct_contrast",
                (
                    "在 VBench 测试中，LingBot-World 全面领先于 Yume-1.5 和 HY World-1.5 等先进"
                    "开源模型，证明了自己不仅是一个视频生成器，更是一个强大的交互式模拟器。"
                ),
                (
                    "在 VBench 测试中，LingBot-World 全面领先于 Yume-1.5 和 HY World-1.5 等先进"
                    "开源模型。这一结果证明，LingBot-World 既能生成视频，也是一个强大的交互式"
                    "模拟器。"
                ),
                "Separate the benchmark result from the two capability claims without weakening certainty.",
                "c05",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The visual state changes inconsistently at 7:00, 7:31, and 8:30.",
                "在 7:00，新古典主义建筑和复原式古希腊建筑群是连接在一起的；但 7:31，从复原式古希腊建筑群望向新古典主义建筑时，新古典主义建筑消失了。8:30 回到新古典主义建筑时，它成为了一栋孤立的房子。",
            ),
            claim(
                "c02",
                "Despite flaws, nearly ten minutes of coherent generation is likely a length record.",
                "单次生成接近 10 分钟的连贯视频，很可能刷新了当前视频/世界模型的长度纪录。",
            ),
            claim(
                "c03",
                "The named competing video systems have the stated generation limits.",
                "Veo 3 和 Sora 2 的单次生成上限分别为 8 秒和 25 秒，Runway Gen-3 Alpha 为 40 秒，Kling 最长支持 2 分钟。",
            ),
            claim(
                "c04",
                "LingBot-World combines open source, 720p, high motion, and long generation.",
                "LingBot-World 在开源、提供 720p 分辨率的情况下，还保证了高动态程度和长生成跨度。",
            ),
            claim(
                "c05",
                "VBench leadership supports both video-generation and interactive-simulation capabilities.",
                "证明了自己不仅是一个视频生成器，更是一个强大的交互式模拟器。",
                "这一结果证明，LingBot-World 既能生成视频，也是一个强大的交互式模拟器。",
            ),
            claim(
                "c06",
                "Action input yields dynamic, physically consistent, prompt-consistent output.",
                "它能够生成高度动态且物理一致的视觉反馈，保持在高动态度下的整体一致性，使视频内容在长时间段内始终与最初的提示保持一致。",
            ),
        ),
        locked_literals=(
            "LingBot-World",
            "Veo 3",
            "Sora 2",
            "Runway Gen-3 Alpha",
            "Kling",
            "VBench",
            "Yume-1.5",
            "HY World-1.5",
        ),
        voice_anchors=("刷新了当前视频/世界模型的长度纪录",),
        retained_contrasts=(
            "The detail flaws versus overall progress qualification remains unchanged.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-09",
        doc_id="0431c592d5de8246cebcb8e2",
        month="2025-10",
        target_lines=(21, 23),
        original_sha256=(
            "351572cb00747cdb88e07ae5d45502abbf5fbc3d54129c9bf945dd6dfa63aa68"
        ),
        operations=(
            operation(
                "contrast-v2-09-op-01",
                "direct_contrast",
                (
                    "对于 Candle 而言，其核心判断是：下一代规模化社交产品的重点，将不再是 "
                    "“向陌生人传播信息”，而是 “让人们更容易每天与身边少数亲密的人保持互动”。"
                ),
                (
                    "Candle 团队判断，下一代规模化社交产品将不再以“向陌生人传播信息”为重点，"
                    "重心会转向“让人们更容易每天与身边少数亲密的人保持互动”。"
                ),
                "Keep the negative and new focus while removing core-judgment reveal framing.",
                "c02",
            ),
            operation(
                "contrast-v2-09-op-02",
                "remove_ornamental_emphasis",
                (
                    "鲁伯与首席技术官（CTO）乔普拉表示，这正是他们未来的规划方向：增加更多"
                    "获取 “火花”（Sparks，应用内的积分体系）的方式，覆盖更广泛的互动场景；"
                    "同时推出更丰富的功能，进一步提升用户的长期互动频率。"
                ),
                (
                    "鲁伯与首席技术官（CTO）乔普拉表示，他们未来计划增加更多获取“火花”"
                    "（Sparks，应用内的积分体系）的方式，覆盖更广泛的互动场景；同时推出更"
                    "丰富的功能，进一步提升用户的长期互动频率。"
                ),
                "Replace emphatic plan-announcement framing with an explicit subject and action.",
                "c05",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "Candle and named peers target relationship enjoyment amid factors that weaken deep connection and increase loneliness.",
                "与 Paired、Couple Joy 等产品一道，成为少数专注于 “让亲密关系更有趣” 的应用之一。",
            ),
            claim(
                "c02",
                "Candle predicts a shift away from broadcasting to strangers toward daily close-contact interaction.",
                "将不再是 “向陌生人传播信息”，而是 “让人们更容易每天与身边少数亲密的人保持互动”",
                "将不再以“向陌生人传播信息”为重点，重心会转向“让人们更容易每天与身边少数亲密的人保持互动”",
            ),
            claim(
                "c03",
                "The team hopes its insight and founder-led TikTok and Instagram distribution prevent short-lived growth.",
                "依托 TikTok 和 Instagram 搭建的传播体系，能够避免重蹈许多消费级社交应用的覆辙",
            ),
            claim(
                "c04",
                "Candle faces retention and feature-depth challenges over 12, 24, and 36 months.",
                "Candle 仍面临两大关键挑战：“用户留存的持久性” 与 “功能体验的深度”。",
            ),
            claim(
                "c05",
                "Ruber and Chopra plan more Sparks acquisition paths and richer functionality.",
                "这正是他们未来的规划方向：增加更多获取 “火花”",
                "他们未来计划增加更多获取“火花”",
            ),
        ),
        locked_literals=(
            "Candle",
            "Paired",
            "Couple Joy",
            "TikTok",
            "Instagram",
            "鲁伯",
            "首席技术官",
            "CTO",
            "乔普拉",
            "Sparks",
        ),
        voice_anchors=("能否实现 12 个月、24 个月甚至 36 个月的长期用户留存？",),
        retained_contrasts=(
            "The future product focus explicitly remains not broadcasting to strangers.",
        ),
    ),
    Pair(
        pair_id="contrast-v2-10",
        doc_id="b186cdd4f9004e0413395bf3",
        month="2026-05",
        target_lines=(169, 174),
        original_sha256=(
            "ac5a3ebed1963b36a703ac740c747162ec7bdf27c9f3325de82c1e11a0c29d0a"
        ),
        operations=(
            operation(
                "contrast-v2-10-op-01",
                "direct_contrast",
                "当你有一个像 OpenClaw 这样的 agent 在运行时，最好的监控方式不是让人类盯着，而是让另一个 LLM 来盯。",
                "当你有一个像 OpenClaw 这样的 agent 在运行时，我们认为最好的监控方式是让另一个 LLM 监督，人类无需持续盯着。",
                "Preserve the monitoring choice and negation while avoiding a staged reversal.",
                "c01",
            ),
            operation(
                "contrast-v2-10-op-02",
                "remove_ornamental_emphasis",
                (
                    "而这里真正很酷的一点在于，这种机制其实是可以大规模运行的。我们认为，"
                    "未来唯一能够有效监控 agents 的技术，实际上就是 agents 自己。于是你就形成"
                    "了一种“对抗式结构”：一个 agent 监督另一个 agent。"
                ),
                (
                    "更酷的是，这种机制可以大规模运行。我们认为，未来唯一能有效监控 agents "
                    "的技术就是 agents 自己，由此形成一种“对抗式结构”：一个 agent 监督另一个 "
                    "agent。"
                ),
                "Reduce stacked importance markers while retaining first-person enthusiasm and the mechanism.",
                "c04",
            ),
            operation(
                "contrast-v2-10-op-03",
                "merge_repeated_reframing",
                (
                    "当然，这并不意味着我们已经把 OpenClaw 的虚拟员工部署到公司最核心的工作"
                    "流里，我们只是在部分场景中尝试。但真正有意思的地方在于，我们没有因为"
                    "前沿模型的安全问题尚未完全解决，就选择暂缓部署。我们的态度是：与其因为"
                    "安全问题停下来，不如直接把安全问题解决掉。因为这本质上并不是模型能力的"
                    "问题，而是一个系统问题，更具体地说，是一个分布式系统层面的工程问题。"
                ),
                (
                    "当然，我们尚未把 OpenClaw 的虚拟员工部署到公司最核心的工作流，只在部分"
                    "场景中尝试。即使前沿模型的安全问题还没有完全解决，我们也没有暂缓部署；"
                    "我们的态度是先解决安全问题，再在内部部署并探索技术边界。我们判断，瓶颈"
                    "不在模型能力，而在系统；更具体地说，这是分布式系统层面的工程问题。"
                ),
                "Keep the deployment limitation, safety stance, and system diagnosis while removing repeated reveals.",
                "c05",
                "c06",
                "c07",
            ),
            operation(
                "contrast-v2-10-op-04",
                "remove_ornamental_emphasis",
                (
                    "换句话说，真正阻碍部署的，更多是外围系统与安全机制，而不是模型本身。"
                    "所以，对我们来说，这一点特别令人兴奋。"
                ),
                (
                    "当前阻碍部署的主要是外围系统与安全机制，不是模型本身。这一点让我们特别"
                    "兴奋。"
                ),
                "Remove restatement announcements while retaining the diagnosis and emotional stance.",
                "c08",
            ),
        ),
        claim_checks=(
            claim(
                "c01",
                "The speaker prefers another LLM over continuous human monitoring for OpenClaw agents.",
                "最好的监控方式不是让人类盯着，而是让另一个 LLM 来盯。",
                "最好的监控方式是让另一个 LLM 监督，人类无需持续盯着。",
            ),
            claim(
                "c02",
                "The system intercepts all traffic through an HTTP proxy for LLM review.",
                "会拦截一个 OpenClaw 实例发出的所有流量，然后通过一个 HTTP 代理，把这些流量路由到另一个 LLM",
            ),
            claim(
                "c03",
                "The network layer can block harmful recruiter-agent requests without the agent knowing.",
                "这套系统就可以直接在网络层拦截并阻止这类请求，而 agent 本身甚至都不知道这件事正在发生。",
            ),
            claim(
                "c04",
                "The mechanism scales and creates an adversarial agent-monitoring-agent structure.",
                "这种机制其实是可以大规模运行的",
                "这种机制可以大规模运行",
            ),
            claim(
                "c05",
                "OpenClaw virtual employees have not reached the core workflow and are limited to some scenarios.",
                "我们已经把 OpenClaw 的虚拟员工部署到公司最核心的工作流里，我们只是在部分场景中尝试",
                "我们尚未把 OpenClaw 的虚拟员工部署到公司最核心的工作流，只在部分场景中尝试",
            ),
            claim(
                "c06",
                "The team did not pause deployment despite unresolved frontier-model safety issues.",
                "我们没有因为前沿模型的安全问题尚未完全解决，就选择暂缓部署。",
                "即使前沿模型的安全问题还没有完全解决，我们也没有暂缓部署",
            ),
            claim(
                "c07",
                "The speaker treats the bottleneck as a distributed-systems engineering problem rather than model capability.",
                "这本质上并不是模型能力的问题，而是一个系统问题，更具体地说，是一个分布式系统层面的工程问题。",
                "瓶颈不在模型能力，而在系统；更具体地说，这是分布式系统层面的工程问题。",
            ),
            claim(
                "c08",
                "Advanced LLM capability is impressive; peripheral systems and safety mechanisms are the main deployment barrier and source of excitement.",
                "真正阻碍部署的，更多是外围系统与安全机制，而不是模型本身。所以，对我们来说，这一点特别令人兴奋。",
                "当前阻碍部署的主要是外围系统与安全机制，不是模型本身。这一点让我们特别兴奋。",
            ),
        ),
        locked_literals=(
            "OpenClaw",
            "agent",
            "agents",
            "LLM",
            "HTTP",
            "招聘 agent",
            "分布式系统",
        ),
        voice_anchors=("更酷的是", "强大得惊人", "特别兴奋"),
        retained_contrasts=(
            "The limited deployment, unresolved safety, and system-versus-model distinctions remain explicit.",
        ),
    ),
)


DEVELOPMENT_RANGES = {
    "3c60dc0a981b686870095450": ((36, 42), (79, 81)),
    "44aa81958a6c585ee8c06847": ((15, 22),),
    "0431c592d5de8246cebcb8e2": ((7, 10),),
    "213dcab213f816c7c548fc09": ((270, 275),),
    "b77b09a419c1631227112f0c": ((19, 22),),
    "48a7a6192771112323fd6820": ((119, 125),),
    "48bda219eb0776f623161899": ((67, 71),),
    "bf1abf6ca461ec0bbac14bd7": ((28, 32),),
    "9e271d7b118c949e83c9ff8d": ((10, 12),),
}


ALLOWED_OPERATORS = {
    "clarify_argument_structure",
    "direct_contrast",
    "merge_repeated_reframing",
    "remove_ornamental_emphasis",
}


CONTRAST_PATTERNS = (
    re.compile(r"(?:不是|并非|不只是|不仅是|不再是).{0,80}?而是"),
    re.compile(r"不仅.{0,80}?(?:更是|而且|还)"),
    re.compile(r"不是.{0,80}?而在"),
)
EMPHASIS_MARKERS = (
    "正是",
    "关键在于",
    "核心挑战在于",
    "核心问题",
    "核心判断",
    "真正解决的",
    "真正阻碍",
    "真正很酷",
    "真正有意思",
    "价值就在这里",
    "价值正在这里",
    "值得注意的是",
    "换句话说",
)
NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]+\d[\dA-Za-z.+:/%-]*|\d[\d.,:/-]*(?:\s*[%+]|[A-Za-z]+)?)(?![A-Za-z0-9])"
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
    """Return non-empty lines from an inclusive one-based range."""

    return "\n".join(line.strip() for line in lines[start - 1 : end] if line.strip())


def apply_operations(original: str, operations: tuple[Operation, ...]) -> str:
    """Apply exact, ordered replacements and reject ambiguous edit logs."""

    revised = original
    for item in operations:
        occurrence_count = revised.count(item.before)
        if occurrence_count != 1:
            raise ValueError(
                f"{item.operation_id}: expected one source span, found {occurrence_count}"
            )
        revised = revised.replace(item.before, item.after, 1)
    return revised


def frame_counts(text: str) -> dict[str, int]:
    """Count frozen surface diagnostics without treating them as quality scores."""

    return {
        "complete_contrast_frames": sum(
            len(pattern.findall(text)) for pattern in CONTRAST_PATTERNS
        ),
        "emphasis_markers": sum(text.count(marker) for marker in EMPHASIS_MARKERS),
    }


def number_literals(text: str) -> list[str]:
    """Extract reproducible numeric tokens for a strict preservation gate."""

    return sorted(set(NUMBER_PATTERN.findall(text)))


def ranges_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] <= right[1] and right[0] <= left[1]


def load_metadata(month_dir: Path, doc_id: str) -> dict[str, object]:
    """Load one exact document record from a monthly metadata file."""

    records = [
        json.loads(line)
        for line in (month_dir / "meta.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [record for record in records if record.get("doc_id") == doc_id]
    if len(matches) != 1:
        raise ValueError(f"{doc_id}: expected one metadata record, found {len(matches)}")
    return matches[0]


def validate_metadata(pair: Pair, metadata: dict[str, object]) -> None:
    """Enforce post-period and recorded translation-exclusion rules."""

    published_at = str(metadata.get("published_at", ""))
    if metadata.get("period") != "post" or published_at < "2025-07-01":
        raise ValueError(f"{pair.pair_id}: source metadata is outside the post period")
    if metadata.get("is_translation") or metadata.get("translation_evidence"):
        raise ValueError(f"{pair.pair_id}: source has recorded translation evidence")


def validate_pair(pair: Pair, original: str, revised: str) -> dict[str, object]:
    """Run deterministic and manifest-backed preservation checks."""

    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
    if digest != pair.original_sha256:
        raise ValueError(
            f"{pair.pair_id}: source hash changed: {digest} != {pair.original_sha256}"
        )
    if original == revised:
        raise ValueError(f"{pair.pair_id}: revised passage is unchanged")
    if pair.month < "2025-07":
        raise ValueError(f"{pair.pair_id}: passage is outside the post period")
    for excluded in DEVELOPMENT_RANGES.get(pair.doc_id, ()):
        if ranges_overlap(pair.target_lines, excluded):
            raise ValueError(
                f"{pair.pair_id}: range {pair.target_lines} overlaps development range {excluded}"
            )
    unknown_operators = {
        item.operator for item in pair.operations if item.operator not in ALLOWED_OPERATORS
    }
    if unknown_operators:
        raise ValueError(f"{pair.pair_id}: unknown operators {unknown_operators}")
    operation_ids = [item.operation_id for item in pair.operations]
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError(f"{pair.pair_id}: duplicate operation IDs")
    claim_ids = {item.claim_id for item in pair.claim_checks}
    for item in pair.operations:
        missing_claim_ids = set(item.preserved_claim_ids) - claim_ids
        if missing_claim_ids:
            raise ValueError(
                f"{item.operation_id}: unknown preserved claim IDs {missing_claim_ids}"
            )
    original_numbers = number_literals(original)
    revised_numbers = number_literals(revised)
    if original_numbers != revised_numbers:
        raise ValueError(
            f"{pair.pair_id}: numeric literals changed: "
            f"{original_numbers} != {revised_numbers}"
        )
    for literal in pair.locked_literals:
        if literal not in original or literal not in revised:
            raise ValueError(f"{pair.pair_id}: locked literal missing: {literal}")
    for check in pair.claim_checks:
        if check.original_support not in original:
            raise ValueError(
                f"{pair.pair_id}/{check.claim_id}: original support not found"
            )
        if check.revised_support not in revised:
            raise ValueError(
                f"{pair.pair_id}/{check.claim_id}: revised support not found"
            )
    for anchor in pair.voice_anchors:
        if anchor not in revised:
            raise ValueError(f"{pair.pair_id}: voice anchor missing: {anchor}")
    original_frames = frame_counts(original)
    revised_frames = frame_counts(revised)
    matcher = difflib.SequenceMatcher(a=original, b=revised, autojunk=False)
    return {
        "claim_checks_passed": len(pair.claim_checks),
        "locked_literals_passed": len(pair.locked_literals),
        "numeric_literals": original_numbers,
        "numeric_preservation_passed": True,
        "original_frame_diagnostics": original_frames,
        "revised_frame_diagnostics": revised_frames,
        "source_hash_passed": True,
        "unchanged_character_ratio": round(matcher.ratio(), 6),
        "voice_anchors_passed": len(pair.voice_anchors),
    }


def build_protocol(seed: int) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "status": "frozen_before_outcomes",
        "frozen_at": "2026-08-21",
        "seed": seed,
        "primary_question": "Which version makes the reader more willing to continue?",
        "outcomes_available_when_frozen": False,
        "development_data_policy": (
            "The ten reader-friction ratings and three first-round pairs were used only "
            "to set operator constraints. Every selected line range is disjoint from them."
        ),
        "selection_policy": {
            "period": "published on or after 2025-07-01",
            "pair_count": 10,
            "distinct_document_count": len({pair.doc_id for pair in PAIRS}),
            "exclude_first_round_ranges": True,
            "exclude_all_reader_friction_ranges": True,
            "exclude_known_translation_evidence": True,
        },
        "allowed_operators": [
            {
                "code": "remove_ornamental_emphasis",
                "rule": (
                    "Remove attention, importance, or revelation framing only when its "
                    "payload is stated directly in the same passage."
                ),
            },
            {
                "code": "direct_contrast",
                "rule": (
                    "Restate an ornamental contrast directly while retaining both sides, "
                    "negation, direction of change, and modality."
                ),
            },
            {
                "code": "merge_repeated_reframing",
                "rule": (
                    "Combine adjacent frames that repeat one relation; retain every unique "
                    "proposition and every necessary logical contrast."
                ),
            },
            {
                "code": "clarify_argument_structure",
                "rule": (
                    "Repair an interrupted or implicit grammatical argument using only an "
                    "actor or object already explicit in the source passage."
                ),
            },
        ],
        "forbidden_edits": [
            "Delete or weaken a proposition, entity, number, negation, qualifier, uncertainty, or attribution.",
            "Invent a fact, example, causal link, opinion, anecdote, or authority.",
            "Remove a necessary logical contrast merely because it matches a surface pattern.",
            "Maximize compression or normalize the passage into uniformly flat prose.",
            "Drop explicit subjects, predicates, objects, or cross-sentence referents.",
        ],
        "preservation_gates": [
            "Exact source SHA-256",
            "Exact set of numeric literals",
            "Pair-specific entities and technical literals",
            "Pair-specific proposition support spans",
            "Pair-specific voice anchors",
            "Disjointness from all development ranges",
        ],
    }


def build_artifacts(
    corpus_root: Path, seed: int
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    """Build blinded tasks, answer key, and aggregate validation diagnostics."""

    if len(PAIRS) != 10:
        raise ValueError(f"Expected 10 pairs, found {len(PAIRS)}")
    pair_ids = [pair.pair_id for pair in PAIRS]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("Pair IDs must be unique")

    prepared: list[tuple[Pair, str, str, dict[str, object]]] = []
    aggregate_original = Counter()
    aggregate_revised = Counter()
    for pair in PAIRS:
        month_dir = corpus_root / pair.month
        validate_metadata(pair, load_metadata(month_dir, pair.doc_id))
        path = month_dir / f"{pair.doc_id}.txt"
        lines = path.read_text(encoding="utf-8").splitlines()
        original = select_lines(lines, *pair.target_lines)
        revised = apply_operations(original, pair.operations)
        checks = validate_pair(pair, original, revised)
        aggregate_original.update(checks["original_frame_diagnostics"])
        aggregate_revised.update(checks["revised_frame_diagnostics"])
        prepared.append((pair, original, revised, checks))

    if sum(aggregate_revised.values()) >= sum(aggregate_original.values()):
        raise ValueError(
            "Frozen surface diagnostics did not decrease across the intervention batch"
        )

    rng = random.Random(seed)
    rng.shuffle(prepared)
    original_side_assignments = [True] * (len(prepared) // 2)
    original_side_assignments += [False] * (
        len(prepared) - len(original_side_assignments)
    )
    rng.shuffle(original_side_assignments)
    tasks: list[dict[str, object]] = []
    answer_key: list[dict[str, object]] = []
    original_side_counts = Counter()
    for task_number, ((pair, original, revised, checks), original_is_a) in enumerate(
        zip(prepared, original_side_assignments, strict=True), start=1
    ):
        original_side_counts["A" if original_is_a else "B"] += 1
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
                "month": pair.month,
                "target_lines": list(pair.target_lines),
                "original_side": "A" if original_is_a else "B",
                "original": original,
                "revised": revised,
                "operations": [asdict(item) for item in pair.operations],
                "claim_checks": [asdict(item) for item in pair.claim_checks],
                "locked_literals": list(pair.locked_literals),
                "retained_contrasts": list(pair.retained_contrasts),
                "voice_anchors": list(pair.voice_anchors),
                "validation": checks,
            }
        )

    diagnostics = {
        "pair_count": len(PAIRS),
        "distinct_document_count": len({pair.doc_id for pair in PAIRS}),
        "operation_count": sum(len(pair.operations) for pair in PAIRS),
        "claim_check_count": sum(len(pair.claim_checks) for pair in PAIRS),
        "original_frame_diagnostics": dict(aggregate_original),
        "revised_frame_diagnostics": dict(aggregate_revised),
        "original_side_counts": dict(original_side_counts),
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
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=Path("data/pilot/monthly"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    tasks, answer_key, diagnostics = build_artifacts(args.corpus_root, args.seed)
    protocol = build_protocol(args.seed)
    protocol["generation_diagnostics"] = diagnostics

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "tasks.json", tasks)
    write_json(args.output_dir / "answer_key.json", answer_key)
    write_json(args.output_dir / "protocol.json", protocol)
    (args.output_dir / "label_config.xml").write_text(
        LABEL_CONFIG,
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir.resolve()),
                "protocol_version": PROTOCOL_VERSION,
                "seed": args.seed,
                **diagnostics,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
