# Compact Refiner 决策日志

追加决策时，记录日期、授权依据、理由、影响和状态。
替代某项决策时须明确说明；不得抹去早期运行的理由。

## CR-D001：暂停语料优先的异味发现

- 日期：2026-09-14。
- 授权依据：维护者在项目对话中的明确指示。
- 状态：已接受。
- 决策：暂停旧的前后对比和选择器开发路线；启动
  从已接受的编辑和偏好中学习的紧凑编辑模型路线。
- 理由：传统 NLP 代理指标尚未提供经过验证的异味奖励；
  预期产品是一个能改善生成中文的紧凑模型。
- 影响：保持历史证据和预留资源不变。其旧有后续步骤
  指示不优先于本路线。只有记录维护者的决策后才能恢复。

## CR-D002：先做 SFT，再做偏好优化；RL 有条件采用

- 日期：2026-09-14。
- 授权依据：维护者接受了所提路线。
- 状态：已接受。
- 决策：通过经过审核的 SFT 样本对学习编辑行为，完成评估后，再在
  可信偏好对足以支持时测试 DPO。在线 RL 为可选项，
  且要求奖励行为经过独立验证。
- 暂缓的替代方案：立即优化手工编写的 NLP 异味分数。
- 影响：现阶段不冻结任何奖励权重或 RL 训练预算。

## CR-D003：保留传统 NLP 的作用

- 日期：2026-09-14。
- 授权依据：在路线实施中落实维护者已说明的动机。
- 状态：已接受的路线政策。
- 决策：将确定性检查和传统特征用于约束、
  诊断，以及后续经过验证的辅助奖励。人类阅读偏好
  仍须与源模型身份、发表时期区分开来。
- 影响：仅凭更高的特征奖励或更低的标记数量，不能
  将检查点晋级。风格收益不能抵消语义失败。

## CR-D004：分开记录并保留数据集溯源信息

- 日期：2026-09-14。
- 授权依据：明确要求单独记录本路线。
- 状态：已接受。
- 决策：将所有政策、决策和实验记录维护在
  `docs/routes/compact-refiner/` 下；使用新的私有数据和运行命名空间。
- 影响：人工标签、助手提案、运行检查和
  合成测试样例的来源归属仍须分别标明。任何旧样例都不会因为
  换了目录就变成新的验证数据或人工金标准。

## CR-D005：从规模受限的开发批次开始

- 日期：2026-09-14。
- 授权依据：在已授权路线内作出的实施选择。
- 状态：已规划；尚无生成结果或读者评审结果。
- 决策：从 24 个开发组开始，覆盖四种体裁、两个源文本
  生成器，以及中等强度下的原样保留／紧凑模型提示／助手候选文本。在执行前冻结具体模型和运行设置。
- 理由：先建立可用的编辑、检查和评判，再投入
  训练或另一套特征测试。
- 影响：本批次不是留出评估。暂定推理费用上限为：
  冒烟检查 1 美元，首批累计 5 美元；须依据
  当前价格估算，任何修订都须明确记录。

## CR-D006：选择训练方案前先核实训练算力

- 日期：2026-09-14。
- 授权依据：维护者对环境信息的纠正，加上本地只读检查。
- 状态：已由 CR-D008 澄清；已选择云端执行，资源规格尚未确定。
- 观测结果：GTX 1080，8192 MiB 显存，驱动 581.57，Python 3.13.5；无 `gx10`。
- 决策：使用 OpenRouter 完成必要推理；选择开放的学生模型，
  并另行核实兼容的训练主机。不得根据 API 访问能力或模型参数量
  推断训练能力。
- 影响：模型 ID、训练主机、实际技术栈、实测成本和最终
  超参数在核实前均保持未设定状态。

## CR-D007：记录剩余决策，不编造答案

- 日期：2026-09-14。
- 状态：待解决事项，不是权限请求或运行时故障。
- CR-001 生成前：确切的生成器／学生模型 ID、提供商政策、
  当前价格快照、24 份任务简述，以及经过验证的流水线。
- 读者任务前：实际评审人员、呈现分配、语义
  审核证据，以及任何场次偏差。
- SFT 前：训练使用权／已接受的数据、已核实的算力、模型许可证、
  检查点身份、已冻结的训练方案，以及评估样本设计。
- DPO/RL 前：足够的可靠偏好；如提议采用 RL，则须有独立的奖励证据；
  各阶段的成本和停止规则。

## CR-D008：推迟训练，待维护者提供云端 GPU

- 日期：2026-09-14。
- 授权依据：暂停实施后，维护者作出的明确澄清。
- 状态：已接受的执行约束；尚未安排训练。
- 决策：不在本地 GTX 1080 上运行 SFT。待数据、模型选择和
  训练计划就绪后，维护者将提供云端 GPU。
- 必需的交接材料：先提供最低和推荐 GPU 规格，
  包括数量／显存、主机内存／存储、软件兼容性、预计
  运行时间／成本，以及这些估计所依据的假设。SFT 与 DPO/RL 须分别估算资源需求。
- 影响：路线文档仍保留为草案，数值化训练
  方案仍保留为提案。本次澄清不启动任何本地训练、云端租赁或模型下载。
  本地数据／检查／评估工作，以及已授权的
  OpenRouter 推理，仍是准备阶段的工具。

## CR-D009：恢复自主准备和受限实验

- 日期：2026-09-14。
- 授权依据：维护者明确指示继续推进、委派实验，
  并在有具体发现后返回汇报；当需要 GPU 执行时，再请求 GPU 规格。
- 状态：已接受。
- 决策：构建可复现的预检流水线，并运行受限推理；
  使用不同智能体分别完成测试样例构建、客户端实现和
  源文本／候选文本评估。任何智能体评估都不得变成人工偏好或
  人工训练准入认可。SFT 和云端资源配置仍然暂缓。
- 影响：必须先保存仅针对源文本的忠实性／改进机会审核，再审核
  候选文本。报告中保留所有初始组。只有在形成具体、可供审核的结果后，
  才征求人类意见。

## CR-D010：首次实际调用模型选择

- 日期：2026-09-14；在付费推理或查看候选文本之前。
- 状态：已选定用于接口冒烟测试，以成功输出为条件。
- 目录：445 个模型；快照 SHA-256
  `6875124fd348cbf584154a4413b8cd8cd01122f0563e048689546a13aa740f2b`。
- 草稿生成器：`deepseek/deepseek-v4.1-flash` 和 `qwen/qwen3.8-27b`。
- 紧凑模型提示基线：`mistralai/ministral-3b-2512`（3B；不是经过训练的模型）。
- 目录标价，单位为美元／百万输入或输出 token：DeepSeek 0.30/1.20，
  Qwen 0.214/2.55，Ministral 0.10/0.10。缓存／折扣可能降低实际成本；
  费用预留采用未折扣的封顶费率，并计入重试带来的潜在费用。
- Hugging Face 元数据显示，DeepSeek 权重使用 MIT 许可证，Qwen 和 Ministral
  使用 Apache-2.0。元数据快照属于私有运行产物；提供商
  API 条款和未知的在线服务检查点修订版本仍是不同的限制因素。
- 观测到的 Ministral 仓库修订版本：
  `b35d4dfe56c142746f54dbd64f579faab2744308`。这是后续可能用于训练的
  基座，并不能证明远程提供商所提供的正是这些字节内容。
- 理由：选择两个当前的生成器家族，以及一个真正紧凑、可用且
  可识别其可训练权重的基线。这不是流行度排名，
  也不是最终的学生模型选择。总开发费用上限仍为 5 美元。

## CR-D011：编辑前计入源文本 API 造成的样本缺失

- 日期：2026-09-14；在源文本结果之后、紧凑编辑模型结果之前。
- 状态：已执行的开发修订，不是验证性协议。
- 决策：在有限次 HTTP 429
  尝试及有记录的冷却恢复后，仍将源文本 23 保留为运行层面不可用。分母中保留全部 24 个计划组；
  审核 23 份实际草稿，并为
  13 个源文本审核通过组冻结独立的编辑阶段。
- 影响：保留原始运行清单和每次失败尝试；
  绝不补齐缺失草稿、将其标记为语义失败，或悄然替换
  其生成器。源文本审核由模型辅助完成，不是人工准入金标准。

## CR-D012：在将需求归因于 SFT 前，测试第二个未经调优的基线

- 日期：2026-09-14；初步预检观测后的探索性跟进。
- 状态：已作为 CR-001B 执行。
- 决策：在完全相同的 13 个编辑器输入上使用 `qwen/qwen3.5-9b`，
  单独冻结清单，每个案例尝试一次，并重新进行盲审。
- 理由：一个表现不佳的 3B 基线不足以证明所有紧凑模型
  都需要训练。9B 模型是容量／语言家族对照，不是最终的
  学生模型，也不能替代原始基线。
- 影响：保留所有结果。家族、规模、提供商和
  评审智能体的差异限制了因果解释；尚未测量任何微调收益。

## CR-D013：保留证据，仅请求有针对性的人工反馈

- Date: 2026-09-14.
- Status: model-only preflight completed; human review pending.
- Decision: do not start SFT or request a GPU yet. Keep the few safe, concrete
  edit proposals and the failure examples. Prepare a three-pair qualitative
  reader preview rather than label agent opinions as human preference.
- Evidence: primary preservation passes were 2/13 for Ministral 3B, 13/13 for the
  independently authored agent proposals, and 8/13 for Qwen3.5-9B with three
  uncertain cases. These are model-assisted development assessments, not
  validated accuracy or reader-preference rates.
- Next priority: establish whether the reader values the proposed edits, compare
  suitable Chinese student baselines, and collect accepted edit/no-edit data.
  Training hardware is specified only when the workload and data are ready.

## CR-D014: Repair rate-limit handling after freezing experiment evidence

- Date: 2026-09-14, after all API experiment calls.
- Status: separate client maintenance.
- Decision: preserve the measurement implementation in an exact private code
  snapshot and update future client behavior to honor Retry-After deadlines,
  including deferred retry rather than long blocking sleeps or early calls.
- Consequence: new behavior has separate tests and provenance; it does not
  retroactively change CR-001 or CR-001B outputs, charges, or failures.

## CR-D015: Record human preferences without overstating their meaning

- Date: 2026-09-14.
- Authority: direct maintainer feedback on the three-pair preview.
- Status: recorded as qualitative development evidence.
- Observation: the chosen sides A/B/A all map to revisions, but pair 1 carries
  an unresolved content-difference concern and pair 3 is only slightly preferred.
  The reader reports no obvious smell in any of the displayed pairs.
- Decision: preserve every original response and the set-level comment. Do not
  report three validated wins, certify preservation, force the slight preference
  into a tie, or turn no-obvious-smell observations into automatic keep labels.
- Consequence: separate feedback/summary files supplement the unchanged
  pre-human artifacts. Pair 1 remains excluded from preservation-passing
  outcomes; all training exports remain empty.

## CR-D016: Establish target coverage before another smell-removal comparison

- Date: 2026-09-14.
- Authority: methodological response to CR-D015 within the selected route.
- Status: next-step requirement; no new batch or model run started.
- Decision: retain this notice/instruction batch as an engineering and ordinary
  editing pilot. Before another smell-removal experiment, inspect original-only
  realistic generated drafts and establish the reader's target coverage
  separately from reading preference and preservation. Do not manufacture bad
  prose, tune against the legacy reserve, or treat agent triage as human gold.
- Consequence: no new large annotation batch, reward, SFT run, or GPU request.
  Low-smell cases remain useful controls; the old corpus-first route stays paused.

## CR-D017: Use real media as the product input distribution

- Date: 2026-09-14.
- Authority: explicit maintainer confirmation of the calibrated project goal.
- Status: governing scope correction.
- Decision: complete real Chinese media articles such as acquired InfoQ articles
  are the target. Synthetic notices or prompted articles remain auxiliary
  engineering material. Preserve prior corpus, annotations, tools, and results.
- Consequence: CR-002 synthetic article tasks remain saved but unexecuted; no
  target-media effect is inferred from CR-001. Source identity and full-context
  audits may proceed without turning those sources into strong-positive labels.

## CR-D018: Restore adequately sampled feature discovery as the front half

- Date: 2026-09-14.
- Authority: maintainer clarification that subjective smell must first be
  characterized, that earlier annotation samples were too weak, and that the
  acquisition/time framework remains valuable.
- Status: active research priority; supersedes the generated-source/immediate-
  editing next steps in CR-D016 and earlier route drafts.
- Decision: follow [the calibrated evidence plan](../../target-feature-discovery.md).
  Retain the pre-2023 baseline, separate transition interval, and post-2025-06
  cohort. Seek an adequate real-media perceptual contrast before new feature or
  edit-efficacy claims. Do not demand that the reader invent the feature rules.
- Consequence: old local preferences are not confirmed strong-positive labels;
  earlier calculations remain historical. Low-signal probes and training stay
  paused. Bounded source staging and integrity work can reuse prior acquisition
  infrastructure, with raw candidates unadmitted until their gates are checked.
- Scientific boundary: the July 2025 transition is a sampling hypothesis and
  maintainer observation, not a measured discontinuity. Date does not certify
  individual authorship or smell severity.

## CR-D019: Measure the nominated contrast family and retain both product targets

- Date: 2026-09-14.
- Authority: direct maintainer reflection and an explicit request for pre-2023
  versus post-June-2025 counts of the broader `而是` construction family.
- Decision: distinguish aversive cues from actual reading defects and address
  both. Run a bounded non-LLM descriptive count under
  [the dedicated protocol](ershi-cohort-statistics.md), preserving all variants
  in the literal count and reporting lexical categories separately.
- Evidence boundary: the reader calls the current article difficult and
  translationese-like, with weak AI smell. It is not a confirmed strong positive,
  and that language judgment is not a translation-provenance label.
- Consequence: no syntactic error count, logical-disconnection label, composite
  reward, or safe rewrite rule is inferred from the literal statistic. Chinese
  argument omission must be evaluated in context. SFT remains downstream.

## CR-D020: Audit semantic contribution and underlying reading defects

- Date: 2026-09-14.
- Authority: maintainer authorized the proposed next-step context audit.
- Decision: freeze [the context protocol](contrast-context-audit.md), inspect
  all 57 occurrences in 13 complete source bodies, retain zero-count documents
  in concentration diagnostics, and preserve two independent assistant reviews.
- Boundary: exact evidence and agreement establish auditability and assistant
  consistency, not reader validity. Do not turn redundant-looking presentation
  into deletion instructions or training rewards.
- Source correction: one reviewed long interview explicitly discloses
  translation. A separate provenance addendum will correct the primary count
  population; raw original statistics and review packets remain frozen.

## CR-D021: Preserve translated media as a separate diagnostic group

- Date: 2026-09-14.
- Authority: maintainer explains that poor English LLM writing may be translated
  into Chinese with further defects; supplied Gemini discussions are reference.
- Decision: preserve original-only temporal exclusions while including
  translated media in a separately recorded product-diagnostic group. Inspect
  upstream information and reasoning as well as downstream Chinese syntax.
- Boundary: no article is labeled LLM-authored or LLM-translated by style.
  Determine inherited versus added defects only with actual paired evidence.
  Reward optimization, synthetic-data inheritance, and cross-language projection
  remain candidate mechanisms in [the reference record](generation-mechanism-hypotheses.md).

## CR-D022: Replace blanket exclusion with provenance-stratified research

- Date: 2026-09-14, superseding the primary-filter emphasis in CR-D021.
- Authority: maintainer explicitly critiques the previous blanket translation
  exclusion, requires automatic translated-Chinese refinement, and delegates
  research direction.
- Decision: study direct Chinese, translations, mixed/adapted, and unresolved
  provenance. Keep temporal cohorts within these strata and original-only
  controls separately. Preserve earlier exclusions and frozen results without
  treating them as global research rejection.
- Product contract: the compact model accepts complete Chinese articles,
  including translations, without requiring an English original. Training and
  evaluation must cover translated input, unchanged good translations, and
  preservation. Upstream sources are optional verification/curation evidence;
  all translations and adaptations share a leakage-control group.
- Execution: pursue source-linked repetitive framing, sentence/reference
  defects, and unsupported discourse relations, followed by bounded repair
  development. Neither low readability nor provenance uncertainty discards a
  research case; provenance uncertainty never certifies originality.
- Boundary: missing information cannot be invented. SFT, DPO, and NLP rewards
  remain conditional on reviewed data and independent reader outcomes.

## CR-D023: Withdraw Cowork and stop substituting repairability for target coverage

- Date: 2026-09-14.
- Authority: maintainer rejects repeatedly using Cowork, then clarifies that
  inherited English LLM problems do not make it a strongly characteristic
  Chinese target example.
- Diagnosis: the assistant anchored on available text, localized grammar
  defects, and completed tooling, then used the translated-input requirement
  to justify another weak-sample reader request. This repeats the earlier
  selection failure despite the known low-smell assessment.
- Decision: withdraw the Cowork preview without inferring a preference outcome.
  Preserve all artifacts and exact feedback. Do not reissue it as a readability
  question or automatically replace it with another edited development article.
- Priority: inspect real complete Chinese articles for sustained target-style
  manifestations before edits or reader requests. Provenance is context;
  translated origin neither guarantees nor rules out those manifestations.
  Translated-input training/evaluation remains required downstream.

## CR-D024: Use the supplied strong anchor and preserve its relative severity

- Date: 2026-09-14.
- Authority: maintainer supplies the SMZDM Microduck article as `极其臭`, then
  explicitly contrasts Baidu `一般臭` with SMZDM `恶臭`.
- Decision: make SMZDM the primary strong-positive discovery anchor and Baidu
  the lower-intensity reference. Do not repeat either rating question or promote
  the prior assistant nomination into a stronger human label than was given.
- Evidence: preserve source HTML, DOM blocks, citation attributes, publication
  metadata, publisher AI disclosure, exact human wording, and separate
  label-conditioned style and claim/relation analyses.
- Consequence: the zero-literal-connector strong anchor requires a broader
  linguistic account. Study recurring parallel verdicts, insider/directive
  stance, and inference/reference problems in context; no forbidden-word list,
  SVO-presence rule, scalar reward, or immediate SFT is justified.

## CR-D025: Explain rhetorical behavior and require surface-form invariance

- Date: 2026-09-14.
- Authority: maintainer retains contrastive framing as a strong signal,
  identifies a bare-copula equivalent and the title-level agenda frame, and
  rejects an explanation confined to the literal connective.
- Decision: prioritize the rhetorical action and its semantic/evidential
  function. Investigate unmotivated corrective framing and prepackaged insight
  as hypotheses; do not claim an identified RLHF or other training cause.
- Measurement consequence: eventual diagnostics must withstand connective-only
  substitutions and distinguish necessary contrasts from unsupported or
  repeatedly ornamental ones. A keyword-only improvement is not product gain.
- Current scope: the new narrow lexical measurement draft is retained
  unexecuted. No extra human rating, rewrite, reward, or training follows from
  these localized observations alone.
