"""Build immutable assistant proposals from exact, source-supported replacements."""

from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).resolve().parents[5]
PRIVATE = ROOT / "data/local/media-repair-development-v1"
PACKETS = ROOT / "data/local/contrast-context-v1/packets"
MANIFEST = json.loads((PRIVATE / "preparation-manifest.json").read_text(encoding="utf-8"))
PROTOCOL = ROOT / "docs/routes/compact-refiner/media-repair-development.md"
REPLACEMENTS = {"doc-03": [], "doc-04": [], "doc-05": []}
ISSUES = {"doc-03": [], "doc-04": [], "doc-05": []}


def edit(alias, before, after, operation_type, reason, preservation_notes):
    REPLACEMENTS[alias].append((before, after, operation_type, reason, preservation_notes))


def issue(alias, anchor, description):
    ISSUES[alias].append((anchor, description))


edit("doc-03", "经常“瞎指挥”，在企业运维的十字路口", "经常“瞎指挥”。在企业运维的十字路口", "sentence_boundary", "Separate the diagnosis from its traffic metaphor.", "Both claims and the metaphor remain.")
edit("doc-03", "但却发现运维系统的十字路口却越来越拥堵了", "但却发现运维系统的十字路口越来越拥堵了", "redundancy_reduction", "Remove a duplicated adversative adverb within one clause.", "The claimed congestion and adversative relation remain.")
edit("doc-03", "和想象中的 Agent 们“游刃有余”的自动协同、分工协作不同，因为传统 Router 的上限太低、智能程度有限，很难跟上 Agent 们“匆匆忙忙”的脚步。", "与想象中 Agent 们“游刃有余”地自动协同、分工协作不同，传统 Router 的上限太低、智能程度有限，很难跟上 Agent 们“匆匆忙忙”的脚步。", "attachment_repair", "Give the comparison and following predicate an explicit common subject; repair the adverbial particle.", "Retains the contrast, both Router limitations, and both quoted metaphors.")
edit("doc-03", "TCAR（Tencent Cloud Andon Router）——\n一个只有 4B 参数，但学会了“先想清楚，再选择”的智能路由模型\n，它", "TCAR（Tencent Cloud Andon Router）——一个只有 4B 参数，但学会了“先想清楚，再选择”的智能路由模型。它", "layout_and_sentence_boundary", "Reconnect a model description split by extracted formatting and end its sentence.", "The model name, 4B quantity, contrast, and subsequent purpose are retained.")
edit("doc-03", "不同 agent 可能能解决一样的问题", "不同 agent 可能具备解决同类问题的能力", "expression_repair", "Remove an awkward adjacent modal sequence while expressing overlapping capabilities.", "Retains possibility and shared problem coverage rather than claiming every Agent is interchangeable.")
edit("doc-03", "就无法确定不确定是 CDN、COS 还是网络的问题", "就无法确定是 CDN、COS 还是网络的问题", "duplication_repair", "Remove an accidentally repeated uncertainty predicate.", "Uncertainty and all three possible causes remain.")
edit("doc-03", "把路由从直接预测标签，变成先推理再选择 Agent 集合\n。这时候", "把路由从直接预测标签，变成先推理再选择 Agent 集合。这时候", "layout_repair", "Reconnect punctuation detached from its sentence.", "No wording or contrast is removed.")
edit("doc-03", "它的工作职能从挑选队列最前面的 agent 完成任务，到在专家梯队中找到最合适的那个人选来完成任务。", "它的工作职能也从挑选队列最前面的 agent 完成任务，转向在专家梯队中找到最合适的那个人选来完成任务。", "coordination_repair", "Complete the predicate of the transition construction.", "Preserves the queue-versus-expert comparison and the source's singular candidate wording.")
edit("doc-03", "它就像是一个拥有顶尖专家团队的，高度聪明且能够自我决策的“项目经理”。", "它就像是一个拥有顶尖专家团队、非常聪明且能够自我决策的“项目经理”。", "coordination_repair", "Coordinate the modifiers of the project-manager metaphor and repair an awkward collocation.", "The expert team, intelligence, autonomy, and metaphor remain.")
edit("doc-03", "明确说明问题可能涉及哪些技术栈，不同 Agent 的职责边界，为什么多个 Agent 执行是合理的，这让路由不再是黑盒，而是可解释、可 Debug、可持续优化 Agent 描述。", "明确说明问题可能涉及哪些技术栈、不同 Agent 的职责边界，以及由多个 Agent 执行为什么合理。这样，路由不再是黑盒：决策可以解释、可以 Debug，Agent 描述也可以持续优化。", "coordination_and_reference_repair", "Separate the reasoning contents from their stated benefits and attach each benefit to a compatible object.", "All three reasoning contents, uncertainty, the black-box contrast, debugging, and Agent-description optimization remain.")
edit("doc-03", "当然，这也要建立在对指令聪明且充分的理解力上。", "当然，这也要求模型足够聪明，能够充分理解指令。", "attachment_repair", "Attach intelligence to the model and sufficient understanding to its instructions.", "The prerequisite remains a requirement rather than a claim of guaranteed performance.")
edit("doc-03", "最终输出一个完整、无冲突的答案，这套模式在排障类问题上效果尤其明显。", "最终输出一个完整、无冲突的答案。这套模式在排障类问题上效果尤其明显。", "sentence_boundary", "Separate the processing sequence from the assessment of its effect.", "Preserves the source's unverified completeness, conflict-free, and troubleshooting-effect claims.")
edit("doc-03", "在高歧义、跨域问题中更稳定，4B 参数量推理速度快成本低，更重要的是下游多 Agent + Refining Agent 的整体成功率显著提升。", "在高歧义、跨域问题中更稳定。模型参数量为 4B，推理速度快、成本低。更重要的是，下游多 Agent + Refining Agent 的整体成功率显著提升。", "sentence_boundary_and_coordination", "Split different performance claims and supply the local subject for the parameter count.", "Keeps 4B, all comparison scopes, cost, speed, and the significance claim without adding scores.")
edit("doc-03", "腾讯云还提供了全套的完整开源范式", "腾讯云还提供了完整的开源范式", "redundancy_reduction", "Remove synonymous completeness modifiers.", "The claim of complete availability and the entire following inventory remain.")

issue("doc-03", "最后，经过 CLINC150、HWU64、MINDS14、SGD、Qcloud 五个数据集的评测", "The body asserts broad benchmark superiority, speed/cost benefits, and a significant downstream success-rate increase without quantitative results or comparison conditions. The claims and reference links are retained; this proposal does not verify them.")
issue("doc-03", "在专家梯队中找到最合适的那个人选来完成任务", "The expert-selection metaphor uses a singular candidate while the mechanism elsewhere selects an Agent subset. The text does not establish whether the singular is merely figurative; it is retained rather than silently reconciled.")

edit("doc-05", "Anthropic 工程师、\nClaude Code\n创建者 Boris Cherny", "Anthropic 工程师、Claude Code 创建者 Boris Cherny", "layout_repair", "Reconnect the person's affiliation and creator role.", "Preserves the name, organization, role, and following quotation unchanged.")
edit("doc-05", "Cowork 试图解决的，正是这一断裂问题。", "Cowork 试图解决的，正是对话模式与真实工作流之间的脱节。", "reference_clarification", "Name the two sides of the preceding paragraph's gap.", "The problem remains a stated product aim, supported by the immediately preceding workflow examples.")
edit("doc-05", "这种访问并非“全盘授权”，而是由用户明确选择、逐一控制的结果。", "这种访问并非“全盘授权”，而是由用户明确选择访问范围，并逐一控制。", "coordination_repair", "Make the object of selection explicit and remove the opaque result construction.", "Retains the full-access negation and the user's explicit, granular control; does not relax the source's guarantee.")
edit("doc-05", "而是 Claude 被嵌入进了用户的实际工作环境之中", "而是 Claude 被嵌入了用户的实际工作环境之中", "redundancy_reduction", "Remove a redundant directional complement.", "Preserves the meaningful smarter-versus-work-environment contrast.")
edit("doc-05", "必要时进行纠正或细化指令", "必要时纠正或细化指令", "coordination_repair", "Give both coordinated verbs the same direct object.", "Retains the conditional need to correct or refine instructions.")
edit("doc-05", "这一定位本身就释放了明确信号：\nAnthropic 并不认为自己已经找到了最终形态，而是希望通过真实用户的使用反馈，加速产品迭代\n。", "这一定位本身就释放了明确信号：Anthropic 并不认为自己已经找到了最终形态，而是希望通过真实用户的使用反馈，加速产品迭代。", "layout_repair", "Reconnect the explanation and its detached punctuation.", "Keeps the final-form negation and real-user-feedback rationale.")
edit("doc-05", "其中包括跨设备同步能力，使 Cowork 不再局限于单一终端；以及将其移植到 Windows 平台，从而覆盖更广泛的办公人群。", "这些改进包括跨设备同步，使 Cowork 不再局限于单一终端；还包括将其移植到 Windows 平台，从而覆盖更广泛的办公人群。", "coordination_repair", "Use parallel predicates for the two planned improvements.", "The preceding plan attribution, cross-device scope, Windows target, and audience rationale remain.")
edit("doc-05", "如果说 Claude Code 面向的是“愿意为效率付出学习成本”的开发者群体，\n那么 Cowork", "如果说 Claude Code 面向的是“愿意为效率付出学习成本”的开发者群体，那么 Cowork", "layout_repair", "Reconnect the two halves of an audience comparison.", "Preserves the contrast and every subsequent occupation.")
edit("doc-05", "其次是新增的一系列技能\n。这些技能", "其次是新增的一系列技能。这些技能", "layout_repair", "Reconnect detached sentence punctuation.", "The skills and all described file categories remain.")
edit("doc-05", "在 Cowork 发布之后，迅速在开发者社区、AI 产品圈以及更广泛的知识工作者群体中引发讨论。", "Cowork 发布之后，迅速在开发者社区、AI 产品圈以及更广泛的知识工作者群体中引发讨论。", "subject_repair", "Remove the preposition that obscures the explicit subject of the discussion trigger.", "Retains the release timing, rapid response, and all three audience groups.")
edit("doc-05", "评论集中在“\n只支持 macOS\n”这一点上。", "评论集中在“只支持 macOS”这一点上。", "layout_repair", "Join a quoted phrase broken by extracted emphasis formatting.", "Preserves the literal quotation and the platform restriction.")
edit("doc-05", "此外，值得注意的是，有些评论虽然不是专门针对 Cowork，但有一些用户还是对\nAnthropic 近期产品策略与沟通的不满\n，对 Cowork 的发布背景和用户关系具有间接关联语境。", "此外，还有一些用户表达了对 Anthropic 近期产品策略与沟通的不满。这些评论虽然并非专门针对 Cowork，但与它的发布背景和用户关系间接相关。", "predicate_and_coordination_repair", "Restore the missing predicate for dissatisfaction and separate it from the qualified relevance claim.", "Keeps both objects of dissatisfaction, the non-Cowork-specific qualification, and indirect rather than direct relevance.")
edit("doc-05", "在 Reddit 平台，有长期用户表示，自己已经从忠实支持者变成对 Anthropic 的\n信任下降甚至不满\n。该用户指出：", "在 Reddit 平台，有长期用户表示，自己曾是 Anthropic 的忠实支持者，如今对它的信任却已下降，甚至感到不满。该用户指出：", "predicate_and_reference_repair", "Replace a malformed person-to-state transition with the same user's earlier and current attitudes.", "Preserves Reddit attribution, long-term-user status, loyalty, declining trust, dissatisfaction, and the following quotation verbatim.")

issue("doc-05", "用户：没有 Linux 版本，差评！", "The section heading foregrounds Linux, while the following evidence explicitly discusses macOS exclusivity and subscription restrictions. No Linux-specific quotation or source attribution is supplied in the body. The heading is retained instead of inventing supporting testimony.")
issue("doc-05", "如果用户在 Chrome 浏览器中将 Cowork 与 Claude 配对使用", "The exact product or integration denoted by pairing Cowork with Claude in Chrome is not specified. The wording is retained rather than inserting an extension name or an unsupported setup procedure.")
issue("doc-05", "Claude 在执行任何“重要操作”之前，都会主动征求用户确认", "The body gives categorical access and confirmation assurances without defining important operations or their conditions and exceptions. These claims remain as source claims; this proposal does not certify the behavior.")
issue("doc-05", "这些指令会被自动排队、并行处理", "The body does not distinguish which feedback is queued from which work executes in parallel. No scheduling semantics are supplied or inferred.")
issue("doc-05", "“作为很早一批用户，我原本极力推荐 Claude，但最近几个月感觉 Anthropic 的产品质量沟通都变差了。”", "The direct quotation joins product quality and communication without clarifying their relationship. It is preserved verbatim, and no extra conjunction or interpretation is inserted into the quoted testimony.")


edit("doc-04", "自 8 月 GPT-5 发布以来，\nCodex\n展现出惊人的爆发力，\n用户增长 20 倍\n，每周处理数万亿 tokens，成为了 Open AI 最受欢迎的编程智能体。", "自 8 月 GPT-5 发布以来，Codex 展现出惊人的爆发力，用户增长 20 倍，每周处理数万亿 tokens，成为了 Open AI 最受欢迎的编程智能体。", "layout_repair", "Reconnect the opening sentence fragmented by extracted emphasis formatting.", "Preserves every name, quantity, date expression, popularity claim, and the source's growth metric wording.")
edit("doc-04", "早期的 Codex\n“太过未来”\n，采用远程异步交互方式", "早期的 Codex“太过未来”，采用远程异步交互方式", "layout_repair", "Reconnect the quoted characterization and its explanation.", "Preserves the characterization and remote asynchronous interaction.")
edit("doc-04", "对于\n未来 AGI 会何时到来\n，Alexander Embiricos 也给出了一个有趣的视角，\n他认为当前真正的限制 AGI 的因素不是模型能力，而是人类——我们输入速度有限、审查速度有限\n，正在拖累其发展\n。", "对于未来 AGI 会何时到来，Alexander Embiricos 也给出了一个有趣的视角。他认为，当前真正限制 AGI 的因素不是模型能力，而是人类——我们输入速度有限、审查速度有限，正在拖累其发展。", "layout_and_attachment_repair", "Reconnect the passage, separate the introduction from the attributed claim, and repair the modifier of limiting factors.", "Keeps attribution, the model-versus-human contrast, both limits, and the claim that they impede development.")
edit("doc-04", "他做了一个预判，\n第一批生产力曲线出现陡增的用户将在明年出现，其后的变化会加速扩散\n。", "他做了一个预判：第一批生产力曲线出现陡增的用户将在明年出现，其后的变化会加速扩散。", "layout_and_sentence_boundary", "Attach the forecast to its introduction with a colon and remove formatting breaks.", "Retains prediction status, next-year timing, first-user scope, and subsequent acceleration.")
edit("doc-04", "当它将 Codex 带回工程师们日常工作的地方", "当 OpenAI 将 Codex 带回工程师们日常工作的地方", "reference_clarification", "Replace a pronoun that could refer to Codex with the organization named in the same paragraph.", "The organization, relocation claim, and following developer-environment description remain source-supported.")
edit("doc-04", "OpenAI 显然是一家与你过去工作过的所有公司都截然不同的地方。", "OpenAI 显然是一个与你过去工作过的所有公司都截然不同的地方。", "classifier_repair", "Match the classifier to the predicate noun for a place.", "Preserves the comparison with all prior workplaces and the interviewer's emphasis.")
edit("doc-04", "不过在 OpenAI，我深刻意识到影响力之巨大，而要把工作做好，需要投入极高的精力。", "不过在 OpenAI，我深刻意识到这项工作的影响力之巨大，而要把它做好，需要投入极高的精力。", "reference_clarification", "Connect the influence and effort predicates to the work already being discussed.", "Retains the OpenAI context and the speaker's high influence and effort claims without assigning a new project.")
edit("doc-04", "还是因为我对开源软件的运作方式不够了解，所以才让团队能这样快速前进？", "还是因为我对开源软件的运作方式不够了解，才没看出团队为什么能这样快速前进？", "logical_attachment_repair", "Repair a question that grammatically makes the interviewer's lack of knowledge cause team speed; the surrounding question asks for an explanation of that speed.", "Retains the interviewer's uncertainty, the exact open-source-software reference, and the rapid-team-progress premise.")
edit("doc-04", "这里的组织架构设计为高度自下而上运作，每个人都渴望快速推进。", "这里的组织架构采用高度自下而上的运作方式，每个人都渴望快速推进。", "expression_repair", "Use a complete predicate for the organizational structure.", "Preserves the degree of bottom-up operation and every person's desire for speed.")
edit("doc-04", "这个比喻有一定道理，但目标成分本身是模糊的。", "这个比喻有一定道理，但目标本身是模糊的。", "expression_repair", "Remove an extraneous noun in the qualification of the aiming metaphor.", "Preserves qualified agreement and uncertainty about the target.")
edit("doc-04", "安装后，你可以与 Codex 互动，回答与代码相关的问题，编写代码，运行测试，执行代码等", "安装后，你可以与 Codex 互动，让它回答与代码相关的问题、编写代码、运行测试、执行代码等", "subject_and_coordination_repair", "Attach the listed software actions to Codex rather than grammatically to the user.", "Retains all four actions and the following software-lifecycle scope; this follows the paragraph's product-capability description.")
edit("doc-04", "因此，我们与 Codex 合作的大部分目标，是弄清楚如何打造这样一种默认情况下就能提供帮助的“队友智能体”。", "因此，我们与 Codex 合作的主要目标，是弄清楚如何打造这样一种默认情况下就能提供帮助的“队友智能体”。", "expression_repair", "Use a singular principal goal for the single purpose supplied by the sentence.", "Retains cooperation, the exploratory goal, and default helpfulness; does not claim that goal is already achieved.")
edit("doc-04", "Codex 模型目前每周服务数万亿级的代币", "Codex 模型目前每周处理数万亿级的 tokens", "terminology_and_collocation_repair", "Use the token terminology already supplied in the article's opening and a compatible processing verb.", "The current weekly scale and model attribution are unchanged; no metric value is inferred.")
edit("doc-04", "这已经超过传统模型的上下文长度，因此我们必须为此设计出解决方案，也就是“压缩”。", "这种长时间运行所需的上下文已经超过传统模型的上下文长度，因此我们必须为此设计出解决方案，也就是“压缩”。", "reference_and_quantity_scope_repair", "Make context, rather than the preceding duration, the thing compared with context length.", "Preserves the stated overflow problem and compaction solution without supplying a context limit or new duration.")
edit("doc-04", "如果想训练一个模型，让它在所有框架下都表现最佳，可能并非不可能，但速度一定会被拖慢。", "如果想训练一个模型，让它在所有框架下都表现最佳，或许可以做到，但速度一定会被拖慢。", "redundancy_reduction", "Reduce a nested possibility/negation phrase while retaining uncertainty.", "Keeps the all-framework optimum, qualified feasibility, and categorical speed tradeoff as source claims.")
edit("doc-04", "写代码是模型最好的方式与编码智能体的未来", "写代码是模型执行任务的最佳方式与编码智能体的未来", "reference_clarification", "Supply the missing activity in a heading using the section's repeated explanation that models act by writing code.", "Retains the strongest-way claim and coding-agent-future topic; adds no new mechanism.")
edit("doc-04", "他们会安排日程、移动会议、主动修复问题、提出建议", "他们会安排日程、调整会议安排、主动修复问题、提出建议", "collocation_repair", "Replace a literal movement collocation with adjustment of meeting arrangements.", "Keeps every example without inventing a particular meeting time, place, or cancellation.")
edit("doc-04", "当你只需要表达任务时，聊天就够了。所以我们希望构建的人工智能", "当你只需要表达任务时，聊天就够了。\n所以我们希望构建的人工智能", "paragraph_boundary", "Separate the interface-use example from the broader assistant-product goal.", "All words and the same Alex speaker turn remain.")
edit("doc-04", "你甚至在工作之外也会使用它。等你开始工作时，你自然会说", "你甚至在工作之外也会使用它。\n等你开始工作时，你自然会说", "paragraph_boundary", "Separate the personal-use analogy from the return-to-work example.", "No content or speaker attribution is removed.")
edit("doc-04", "你能从工程师如何使用你的工具里学到巨量东西，也能更清楚应该把什么融入产品。", "你能从工程师如何使用你的工具中学到非常多的东西，也能更清楚应该把什么融入产品。", "collocation_repair", "Repair a literal quantity collocation while retaining its strong degree.", "Both learning from engineers and deciding what to integrate remain.")
edit("doc-04", "让用户感到拥有掌控感", "让用户拥有掌控感", "redundancy_reduction", "Remove a duplicated feeling construction.", "The intended sense of control and following contrast remain.")
edit("doc-04", "这种方式其实比写规范更普遍，也更贴近日常行为模式。如果人工智能智能体要融入团队", "这种方式其实比写规范更普遍，也更贴近日常行为模式。\n如果人工智能智能体要融入团队", "paragraph_boundary", "Separate the account of existing teamwork from its proposed implication for agents.", "Preserves prevalence, naturalness, the conditional, and the same speaker turn.")
edit("doc-04", "工程师能愿意写代码，但大型团队投入最多时间的活动往往是代码审查和验证", "工程师愿意写代码，但大型团队投入最多时间的活动往往是代码审查和验证", "predicate_repair", "Remove a stray modal preceding willingness.", "Keeps willingness, the contrast, the largest-time claim, and its often qualification.")
edit("doc-04", "Alex：对我来说，我感受到的最大变化是“能力被大幅增强”的感觉。", "Alex：对我来说，最大的变化是感到自己的“能力被大幅增强”。", "redundancy_reduction", "Remove the repeated experience/feeling frame around one subjective observation.", "Retains Alex attribution, subjectivity, superlative scope, and the quoted description.")
edit("doc-04", "OpenAI 的技术复杂度非常高，而过去一年我们看到全公司各类角色的使用技巧都大幅提升，而 Codex 的影响也随之增强。", "OpenAI 的技术复杂度非常高。过去一年，我们看到全公司各类角色的使用技巧都大幅提升，Codex 的影响也随之增强。", "sentence_boundary_and_coordination", "Separate the background statement from the past-year observation and remove a repeated weak coordinator.", "Retains technical complexity, timing, company-wide role scope, large skill gains, and the corresponding Codex effect.")
edit("doc-04", "而现在的团队基本都是高级用户级别地使用 Codex", "而现在的团队使用 Codex 基本都达到了高级用户的水平", "collocation_repair", "Replace an awkward adverbial level construction with a compatible predicate.", "Keeps the current-team scope and basically qualification.")
edit("doc-04", "整个公司因为 Codex 而加速，从研究到模型训练速度，再到设计与营销，我们经常看到产品营销人员直接在 Slack 里更新字符串或文案，这些都是变化的一部分。", "从研究和模型训练，到设计与营销，整个公司都因为 Codex 而加速。我们经常看到产品营销人员直接在 Slack 里更新字符串或文案，这些都是变化的一部分。", "coordination_and_sentence_boundary", "Coordinate work areas at the same grammatical level and separate the concrete marketing example.", "Retains acceleration across the company, research, training, design, marketing, frequency, Slack, strings, and copy.")
edit("doc-04", "你仍然需要对自己构建的东西的本质有理解，但具体细节将越来越抽象，就像你不用懂汇编语言也能写 Swift，一样的道理。", "你仍然需要理解自己构建的东西的本质，但具体细节将越来越抽象。就像你不用懂汇编语言也能写 Swift，道理是一样的。", "collocation_and_sentence_boundary", "Use a direct understanding predicate and separate the analogy.", "Retains necessity, increasing abstraction, and the exact assembly/Swift example without changing the prediction.")
edit("doc-04", "未来 Codex 甚至能自动告诉你如何设置环境，甚至在代码库里自动设置。", "未来 Codex 甚至能自动告诉你如何设置环境，还能在代码库里自动设置。", "redundancy_reduction", "Remove repeated escalation framing from two coordinated future capabilities.", "Both future capabilities, automation, and the codebase location remain.")
edit("doc-04", "一切所有的前后环节都显得更关键了", "所有的前后环节都显得更关键了", "redundancy_reduction", "Remove duplicated universal quantification.", "The full scope and stronger-importance claim remain.")
edit("doc-04", "尤其是面对被现有 AI 工具严重服务不足的客户", "尤其是面对现有 AI 工具远远无法满足其需求的客户", "collocation_repair", "Replace a malformed passive service construction with the same substantial unmet-need relation.", "Keeps the emphasis on severely underserved customers and existing AI tools; no specific unmet need is invented.")
edit("doc-04", "Alex：一个我不断提醒自己的事情是，像 Codex 这样的产品", "Alex：我不断提醒自己：像 Codex 这样的产品", "redundancy_reduction", "Remove an unnecessary thing-is frame around the recurring self-reminder.", "Preserves Alex attribution, recurrence, and the entire reminder.")
edit("doc-04", "做过一个关于屏幕共享与结对编程方向的创业项目", "做过一个屏幕共享与结对编程方向的创业项目", "redundancy_reduction", "Remove duplicated topic-marking around the startup-project domain.", "Both screen sharing and pair programming remain.")
edit("doc-04", "想象我们要覆盖的所有世界范围的任务，智能体每天有可能帮助你成千上万次。", "想象一下，我们要覆盖世界范围内的所有任务，智能体每天有可能帮助你成千上万次。", "modifier_attachment_repair", "Attach worldwide scope to tasks rather than leaving stacked incompatible modifiers.", "Preserves universal task scope, daily frequency, large quantity, and possibility.")
edit("doc-04", "真正理想的方式是，当你专注于某个工作，比如查看仪表盘时指标突然下降，智能体可以在右侧出现，为你解释原因，并告诉你可能的解决方案，而且它只在你关心的那一刻出现。", "真正理想的方式，是让智能体在你专注于某项工作时提供帮助。比如，你查看仪表盘时，指标突然下降，智能体可以在右侧出现，为你解释原因，并告诉你可能的解决方案，而且它只在你关心的那一刻出现。", "example_attachment_and_sentence_boundary", "Separate the desired contextual-help behavior from the dashboard example so the timing clause is complete.", "Keeps user focus, dashboard, falling metric, right-side placement, explanation, possible solutions, and only-at-the-relevant-moment scope.")
edit("doc-04", "在你最需要的恰当时刻表现出智能", "在你最需要的时候表现出智能", "redundancy_reduction", "Reduce duplicated timing qualification.", "Retains need-sensitive timing and the contrast with notification overload.")
edit("doc-04", "确实有很多意想不到的用法，但目前为止", "确实有很多意想不到的用法，但到目前为止", "expression_repair", "Complete the conventional up-to-now expression.", "Preserves surprise, quantity, temporal limitation, and the following qualification.")
edit("doc-04", "Lenny ：Codex 的自我训练到底意味着什么", "Lenny：Codex 的自我训练到底意味着什么？", "speaker_label_and_punctuation", "Normalize spacing in an existing speaker label and complete its explicit question.", "Does not add a speaker turn or alter the question's subject.")
edit("doc-04", "所以 Codex 会在循环中持续检查这些图表的表现", "所以 Codex 会在循环中持续检查这些图表所显示的情况", "reference_clarification", "Attach monitoring to the information shown in the charts rather than the charts' performance.", "Preserves the causal link, continuous loop, same charts, and subsequent inference from them without specifying unseen metrics.")
edit("doc-04", "如果你明年是一家创业公司，正在构建一个新应用", "如果你明年在一家创业公司，正在构建一个新应用", "predicate_repair", "Repair the person-is-a-company construction using the parallel employment setting in the following SAP example.", "Retains next-year timing, startup context, and new-app activity without assigning an ownership role.")

issue("doc-04", "Sora 团队更是依靠 Codex，在短短 28 天时间，从 0 到 1 完成 Android 应用的上线，直接冲到 App Store 第一。", "The article combines an Android launch with an App Store ranking and repeats this combination in its summary. The Chinese body does not establish the exact store or ranking scope; both names and the claim are retained rather than corrected using outside knowledge.")
issue("doc-04", "过去 6 个月里，Codex 的使用量增长了 20 倍。", "Growth appears as users in the lead, usage here, and model growth elsewhere; the body also alternates since-August and past-six-month windows without an article date in the supplied body. No shared metric or time window is inferred.")
issue("doc-04", "因此，我的理解是：最初版本的 Codex 太“未来”，像一个远程云端智能体，以异步方式工作；而你们所做的，是把它重新拉回开发者熟悉的环境，让它在 IDE 本地工作，使用户更容易习惯新的开发方式。", "This apparent interviewer restatement lacks a speaker label, although the following turn is labeled Alex. The candidate does not invent a Lenny attribution or alter the supplied turn sequence.")
issue("doc-04", "GPT-5.1.1 Codex Max", "The precise model identifier is not independently established by the supplied Chinese body. It remains exactly as written, along with other model names; this is not a model-name correction pass.")
issue("doc-04", "智能体人像使用手机一样工作，它看到的一切都是竖屏视频流", "The subject in this speculative interface description is malformed, and the passage shifts between an agent's observation and a user swiping suggestions. The body alone does not establish which entity operates a phone or sees a vertical feed. The ambiguity remains instead of changing the actor.")
issue("doc-04", "Branded Codebase", "This proper-name-like expression is linked to an early OpenAI product, the model behind GitHub Copilot, and a reused brand, but its identity is not resolved in the Chinese body. It is retained verbatim without substituting another product name.")
issue("doc-04", "他们甚至建立了类似 “Vibe-coded” 的分类体系，把自己的原型直接做成 Codex 使用的版本。", "The taxonomy and the relationship between prototypes and a version used by Codex are underspecified. The proposal retains the assertion rather than choosing an implementation or prototype workflow.")
issue("doc-04", "团队只用了两周时间就完成上线准备，而整个四周流程包括投产上线", "This two-week/four-week account appears alongside 18 days to employee testing and 10 additional days to public release. Different milestones may be intended, but the body does not reconcile them. All quantities and milestones remain.")
issue("doc-04", "使 Codex 帮助 Codex 自身服务训练系统", "The grammatical relationship among helping Codex, its own training, and serving training systems is unclear. The surrounding paragraph supports involvement in training infrastructure but not a unique repair of this clause; no extra agent relationship or self-training mechanism is supplied.")


def build():
    protocol_hash = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    assert protocol_hash == MANIFEST["protocol_hash"], "Protocol hash mismatch"
    for alias, replacements in REPLACEMENTS.items():
        source_path = PACKETS / alias / "body.txt"
        source_bytes = source_path.read_bytes()
        source = source_bytes.decode("utf-8")
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        assert source_hash == MANIFEST["source_hashes"][alias], f"Source hash mismatch: {alias}"
        operations = []
        for before, after, operation_type, reason, preservation_notes in replacements:
            assert before != after, f"No-op in {alias}"
            assert source.count(before) == 1, f"Nonunique or missing source span in {alias}: {before!r}"
            start = source.index(before)
            operations.append({
                "start_char": start,
                "end_char": start + len(before),
                "before": before,
                "after": after,
                "operation_type": operation_type,
                "reason": reason,
                "preservation_notes": preservation_notes,
            })
        operations.sort(key=lambda item: item["start_char"])
        previous_end = 0
        for index, operation in enumerate(operations, 1):
            operation["operation_id"] = f"{alias}-op-{index:03d}"
            assert operation["start_char"] >= previous_end, f"Overlapping spans: {alias}"
            assert source[operation["start_char"]:operation["end_char"]] == operation["before"]
            previous_end = operation["end_char"]
        output = source
        for operation in reversed(operations):
            output = output[:operation["start_char"]] + operation["after"] + output[operation["end_char"]:]
        pieces = []
        cursor = 0
        for operation in operations:
            pieces.extend((source[cursor:operation["start_char"]], operation["after"]))
            cursor = operation["end_char"]
        pieces.append(source[cursor:])
        assert "".join(pieces) == output, f"Coverage/replay mismatch: {alias}"
        unresolved = []
        for index, (anchor, description) in enumerate(ISSUES[alias], 1):
            assert source.count(anchor) == 1, f"Nonunique issue anchor: {alias}"
            start = source.index(anchor)
            unresolved.append({
                "issue_id": f"{alias}-issue-{index:03d}",
                "start_char": start,
                "end_char": start + len(anchor),
                "source_excerpt": anchor,
                "description": description,
                "disposition": "Retained in the candidate; requires source or content verification beyond Chinese-only expression repair.",
            })
        output_bytes = output.encode("utf-8")
        metadata = {
            "protocol": MANIFEST["protocol"],
            "protocol_sha256": protocol_hash,
            "candidate_id": f"{alias}-assistant-proposal-v1",
            "source_alias": alias,
            "source_path": source_path.relative_to(ROOT).as_posix(),
            "source_sha256": source_hash,
            "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
            "source_char_count": len(source),
            "output_char_count": len(output),
            "offset_convention": "Zero-based Unicode code points in the original UTF-8 decoded body; end_char is exclusive; no newline normalization.",
            "replay_order": "Descending start_char; apply every operation to the original body.",
            "editor_role": "assistant_editor",
            "editor_identity": "/root/media_repair_editor",
            "model_identity": "Codex, GPT-6-based; exact runtime model identifier not exposed in task context.",
            "prompt_version": "media-repair-development-1.0-editor-assignment-2026-09-14",
            "generation_seed": None,
            "seed_note": "Current-assistant generation; deterministic text generation is not claimed.",
            "intensity_policy": "Local, source-supported repairs with no edit quota; preserve unique content and meaningful contrasts.",
            "input_contract": "Complete Chinese bodies, general AGENTS.md instructions, protocol, and preparation manifest only.",
            "full_source_read": True,
            "status": "assistant_proposal_pending_independent_preservation_review",
            "human_gold": False,
            "human_acceptance": False,
            "training_eligible": False,
            "external_api_calls": 0,
            "gpu_used": False,
            "operations": operations,
            "unresolved_content_issues": unresolved,
            "internal_validation": {
                "source_hash_matches_manifest": True,
                "protocol_hash_matches_manifest": True,
                "exact_before_spans": True,
                "bounds_and_nonoverlap": True,
                "right_to_left_replay": True,
                "left_to_right_full_coverage": True,
                "output_utf8_hash_recorded": True,
                "semantic_preservation": "Editor proposal only; independent review pending.",
            },
            "reproduction_command": "python data/local/media-repair-development-v1/candidates/doc-03/create_candidates.py",
        }
        destination = PRIVATE / "candidates" / alias
        destination.mkdir(parents=True, exist_ok=True)
        for path, payload in (
            (destination / "output.txt", output_bytes),
            (destination / "operations.json", (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
        ):
            assert not path.exists(), f"Refusing to overwrite immutable candidate: {path}"
            path.write_bytes(payload)
        print(json.dumps({"alias": alias, "operations": len(operations), "issues": len(unresolved), "source_chars": len(source), "output_chars": len(output), "source_sha256": source_hash, "output_sha256": metadata["output_sha256"]}))


if __name__ == "__main__":
    build()
