# 小型精修模型数据约定

约定版本：`compact-refiner-data-1.2`。1.2 版包含中文译文输入和上游来源分组。此前合成及媒体记录保持不变；版本化 sidecar 可补充新 provenance 字段。development 记录工具已存在，完整训练约定 validator 和训练 exporter 尚未实现。

## 数据与任务单位

真实媒体的基本单位是来源文章及其 provenance 组，不是孤立段落。转载、近似重复、节选、修订和重复判断留在同一组。辅助合成材料中，同一生成任务全部版本构成一个 generation-task 组。

主要产品评估使用完整媒体文章上下文，返回可检查的完整文章。单项操作可以局部进行，但不能丢失全文链接，也不能当作独立样本。原合成 pilot 的段落任务保留为历史辅助格式。理由、主张清单、复核决定和 reward 诊断与 student target 分开。

## 真实媒体来源记录

记录 `source_document_id`、`article_group_id`、canonical URL、来源平台、标题、署名、发布与更新及采集时间、原始抓取身份、规范化正文身份、提取与呈现版本、段落／图／表／代码／链接映射、来源质量和传播可见性证据、翻译证据、使用权状态、历史暴露及缺失上下文。

原文是采集到的媒体来源，不是助手重构或模型生成替代品。保留原始字节和每次转换记录。来源清理必须版本化，区分布局提取和行文改写。抓到文本正文不证明已抓取全部多媒体上下文；不可用的重要图仍是明确限制。

保留时间 cohort 和既有边界。没有直接记录时，作者身份未知；发布日期和目标臭味印象不提供个体作者标签。历史弱标注不是已确认强正例。训练使用权与合法研究采集、检查分开评估。

以下合成任务说明及草稿 schema 描述 CR-001 等辅助生成记录，不要求把真实媒体改成合成事实包，也不要求分析前生成新原文。

不要训练模型推断输入由人还是 AI 创作。已知生成 provenance 只用于复现和评估分层。

## 翻译与上游来源 sidecar

新媒体记录保留 `provenance_status`（`direct_chinese`、`translated`、`mixed_or_adapted`、`unresolved`）、支持证据与复核版本、`upstream_source_ids`、`upstream_source_languages`，以及可选来源对齐记录。不可用字段显式未知；外文姓名、外部引用和风格不确立来源语言或 LLM 使用。旧排除标签单独保留。

默认 `input_language` 为中文，不要求外文原文。区分中文输入文章与上游来源，避免意义保留记录中“原文”含糊。原语言文本、译文、混合改编、节选和修订构成一个连通 provenance 组，用于 train 与 evaluation split。

翻译 provenance 不阻止研究，也不阻止通过其他门槛后的训练资格。使用权、意义保留、编辑接受和组隔离仍适用。只有真实对齐证据支持时，才归类为继承缺陷、翻译新增、编辑新增或未解决缺陷。

## 数据集版本中的文件

| 文件 | 必需内容 |
|---|---|
| `dataset_manifest.json` | Schema、版本、父版本、角色、来源、使用权政策、hash、计数、排除及 split 算法 |
| `briefs.jsonl` | 生成指令和可用来源事实或上下文 |
| `drafts.jsonl` | 模型原始输出和精确推理身份 |
| `candidates.jsonl` | 不修改对照和有限修订 |
| `preservation_reviews.jsonl` | 自动检查输出与独立标明评估者的语义复核 |
| `preferences.jsonl` | 盲评判断、呈现映射、读者身份和有效性状态 |
| `split_manifest.json` | 不可变组分配与重叠审计 |
| `exclusions.jsonl` | 条目 ID、阶段、理由、证据引用和可能处理方式 |
| `exports/` | 衍生 SFT/DPO 文件、schema、筛选、hash 和计数 |

原始模型文本和人工评论保存在 ignored 数据集目录。运行日志只含 ID、状态、耗时和有限错误，不记录文章正文、含私有文本的 prompt 或凭据。

## 任务说明记录

必需字段：

- `brief_id`、`task_group_id`、`dataset_version`、`created_at_utc`；
- `genre`、`topic`、`audience`、`intended_voice`、`requested_length`；
- `instruction_text`、`fact_packet`、`read_only_context`、`locked_content`；
- `rights_status`、`rights_evidence`、`content_origin`、`contains_personal_data`；
- `brief_sha256`、`fact_packet_sha256`，以及任何上游来源 ID 或 hash。

首批优先使用专门撰写、明确虚构且含完整事实包的任务说明。虚构姓名和数字标为构造材料，不当作自然 prevalence 的实证例子。真实用户草稿需要适用许可和保留记录。公开可读本身不代表可训练或再发布。

使用来源材料时保留 provenance 和 license 或许可。训练权利不明者不得进入训练导出；不要从文章被旧研究语料准入推断使用权。

## 草稿记录

必需字段：

- `draft_id`、`task_group_id`、`brief_id`、`split`、`draft_text`、`draft_sha256`；
- `generator_kind`、`requested_model`、`returned_model`、`provider`、`checkpoint_revision`、`prompt_version`、`prompt_sha256`；
- `request_config`、`request_config_sha256`、`seed`、`seed_supported`、`generated_at_utc`、`finish_reason`、`usage`、`cost`；
- `generation_status`、`fact_packet_consistency`、`exclusion_reason`。

提供者不支持或未提供的 metadata 显式记为 `null` 并说明理由，不猜身份。seed 不代表远程推理确定性。cache key 包含完整实际请求、模型与提供者身份、内容 hash，不只包含 prompt 版本。

生成普通任务回答，不要求差写作、刻板或“AI 臭味”风格。保留已写得好的草稿：不修改是必要编辑行为。不要按目标标记或 NLP 分数挑选全部草稿。

草稿若编造事实或与事实包矛盾，应隔离到独立内容纠正任务。本风格路线不悄悄修复该主张，也不将删除错误算成风格改善。

## 候选记录

必需字段：

- `candidate_id`、`task_group_id`、`draft_id`、`candidate_kind`、`parent_id`；
- `intensity`（`low`、`medium` 或 `high`）、`editable_span`、`context_sha256`；
- `output_text`、`output_sha256`、`operations`、`candidate_provenance`；
- 适用时的生成器或编辑者身份及 prompt、request 字段；
- `deterministic_checks`、`preservation_review_ids`、`eligibility_status`。

候选类别为 `unchanged`、`compact_prompt`、`assistant_edit`、`human_edit`、`sft` 和 `dpo`。新增类别需要版本化扩展。助手编辑即使由该助手仔细检查，仍是模型辅助，不是人工编辑上限。

每项操作记录 `operation_id`、`type`、`start_char`、`end_char`、`before`、`after`、`reason` 和 `claim_ids`。offset 按精确原始段落的 Unicode code point 计算，区间为左闭右开 `[start_char, end_char)`。操作必须不重叠，从右向左应用后复现输出。不修改候选 hash 相同且没有操作。

初始操作类型：`clarify_reference`、`reduce_redundant_framing`、`reorder_existing_information`、`repair_grammar`、`split_or_merge` 和 `keep`。它们描述编辑提案，不表示臭味目录已验证通用规则。内容新增与事实纠正不在范围内。

自主预检期间，`unclassified_rewrite` 在语义意图复核前记录整段替换。这是可审计提案，不是已接受训练操作，不能绕过复核或导出门槛。

## 意义保留复核记录

记录 `review_id`、输入与候选 hash、复核者类别和稳定 ID、复核时间、政策版本、证据片段、问题代码，以及结果（`pass`、`fail` 或 `uncertain`）。人工、助手和其他模型评估分开。模型可以标风险，不能认证人工接受。

检查命题、实体、带单位数字、日期、引用、否定、情态、限定、归属、范围、指代和风格。双向检查：输入删除了什么，编辑新增了什么。字面检查本身不能确立 entailment 或完整性。

`fail` 与 `uncertain` 不进入已接受训练或偏好导出，保留为有标签的审计或 challenge 材料。修复候选取得新 ID、hash 和新复核，旧失败保持可见。

## 偏好记录

必需字段：`judgment_id`、`task_group_id`、`draft_id`、两个候选 ID、protocol 和呈现 ID、原始 A/B 映射、稳定匿名读者 ID、读者类别、时间戳、所选答案、可选评论与有效性状态。

有效人工答案为 A、B、两个都可接受且无实质差别、两个都不可接受、无法判断。不要把平局或分歧硬转为二元偏好。不得以模型生成偏好代替缺失人工响应。公开任务视图不显示生成器身份、干预类型、NLP 分数、意义保留结论和预期答案。

读者必须看到足够且一致的上下文，才能解释两候选。两组上下文保持相同。改变上下文是另一个实验，不是风格编辑。

## 数据集角色与泄漏

明确使用角色：`development`、`train`、`validation`、`final_test`、`challenge`。历史发现和读者示例默认仅 development；若要训练，须单独复核使用权与资格。它们永远不能成为新的 validation 或 final-test 证据。

生成或检查版本前，先分配连通组。共享事实包、来源文档、轻微变动的任务说明、段落节选、近似重复和改写衍生物，属于同一 connected component。每个 component 整体留在同一 split。仅主题名称不同不能定义独立性。

新训练数据集初始分配 80% train、10% validation、10% final-test 组，是规划默认值，不是 power 计算。以 seed `20260914`、组身份、算法版本和平衡报告冻结分配。冻结样本量设计若需要更多，补采独立评估组，不把版本算成新组。

R1 的 24 组全部 development，没有任何部分是 held-out validation。不要读取旧 30 篇文档预留集或旧封存翻译测试。

## 导出规则

| 导出 | 资格 |
|---|---|
| SFT 正向编辑 | 使用权明确；真人通过语义复核；真人明确接受编辑；组 split 正确；精确来源与输出 hash |
| SFT 不修改 | 使用权明确；人工复核确认不需要有益且在范围内的编辑；输出精确等于输入 |
| DPO 对 | 完全相同的 student 输入、上下文和强度；两个候选都通过意义保留；明确有效的人工偏好；无未解决分歧；两候选同组 |
| Challenge 集 | 版本化失败类型和证据；不进入正向训练导出 |
| 模型辅助提案池 | 明确标注未复核或合成；不悄悄混入人工接受导出 |

独立纯合成可行性运行可以检查工程连接，但不能声称读者改善，也不能满足 R2 人工复核数据门槛。保留自然出现的不修改案例；在复核支持时，SFT 工作构成目标约 20-30% 不修改。不要编标签或丢弃合法案例来凑比例。报告实际构成和采样权重。

SFT 导出只含 canonical 指令、上下文、强度、输入段落和已接受输出。DPO 导出含相同 canonical 输入及 chosen/rejected 输出。复核笔记、来源模型标签、预期答案键、特征分数和 split 名称绝不进入模型输入。

## 导出前必需验证

验证 schema、ID、UTF-8、hash、使用权、split 归属、重复组、偏好对输入一致、操作重放、复核 provenance 和资格。证据缺失或矛盾时 fail closed。导出每种排除理由计数和未改动输入 manifest hash。

Validator 与 exporter 实现且目标导出通过检查之前，不提供可运行训练命令。复用数据和评估逻辑逐步实现在 `src/deaiodorant/`，保留现有根目录命令。
