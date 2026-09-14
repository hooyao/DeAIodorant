# 对比上下文与阅读缺陷审计

Protocol：`contrast-context-audit-1.0`。日期：2026-09-14。
定义时的状态：已经观察字面 cohort 计数、尚未开展新语义复核的探索性 protocol，不是对已观察时间差异的预注册确认。

## 范围与问题

审计 `ershi-cohort-statistics-1.0` 排除已知译文视图所保留的 13 篇正计数 InfoQ 文档中，全部 57 次字面 `而是`。确定性上下文指标保留全部 35 篇文档，包括 22 篇零计数文档。明确声明按指定信号选样：这是特征解释，不是臭味 prevalence 估计。既有正式准入不确定性仍未解决。

逐次识别语义关系，以及删除任一侧会损失什么。另行定位可能的阅读缺陷，包括远离连接词的缺陷。不要把纠正或重复对比等同于多余措辞。合理关系也可能被重复包装；没有标记的句子仍可能难读。

## 不可变输入与确定性观察

复用此前运行中经 hash 检查的正文和字面 offset。私下保存精确正文副本和不含公开正文的 manifest；不覆盖旧输入、标签或输出。Unicode offset 从零开始，右端不包含。

记录正文 CJK 长度、字面次数，以及连续 500 和 1000 个 CJK 字符位置内连接词起点的最大数量。对每个片段，要求末位置减首位置严格小于窗口长度。这些重叠窗口最大值是描述性聚集指标，不是错误或臭味阈值。继续标明短文档。非 CJK 连续文本不推进此坐标系统；同时提供 Unicode 位置。

机械上下文单元以 `。！？!?` 结束；换行不划分句子，因为抓取会在行内元素中插入换行。保留完整正文访问。这些单元是导航辅助，不是已验证的语言学句子或 DOM 段落。不得根据采集器换行测量段落缺陷。

## 复核流程与字段

两位独立助手复核者通读全部 13 篇提供的完整正文。每人收到相同的中性文档别名与带 offset 索引的出现位置。材料包不包含发布 metadata、cohort、先前判断和总体频率差异。这只隐藏 metadata：文章内容可能透露时间、来源和体裁。不得声称完全盲态或人工判断。复核者不得读取彼此输出或身份映射。

每位复核者写入 `review-a.json` 或 `review-b.json`，包含 `reviewer`、`model_identity`（仅在可用时）、`human_gold: false`、`documents`。每篇文档包含 `alias`、`whole_body_read: true`、`genre_observation`、`occurrences`、`reading_defects`、`counterexamples` 和 `document_note`。

每次出现包含：

- `occurrence_id` 及包含连接词的精确 `evidence_quote`；
- `relation`：`correction`、`scope_extension`、`temporal_change`、`procedural_alternative`、`evaluative_reframing`、`unclear_or_malformed` 或 `mixed`，选择主要关系并解释重叠；
- `voice`：`reporter`、`attributed_quote_or_paraphrase`、`mixed` 或 `uncertain`；
- `contrast_contribution`：简述传达的信息；
- `packaging`：`ordinary`、`repetition_candidate` 或 `uncertain`；
- `packaging_reason`、`preservation_risk` 和 `confidence`，后者取 `high`、`medium` 或 `low`。

`repetition_candidate` 要求同一文章其他位置有明确重复动作，或独立描述出的冗余对立；不能仅凭标记存在或一般性地不喜欢主题。实质贡献和可能重复的呈现分别记录，不提供臭味强度分数。

每项局部 `reading_defects` 包含 `defect_id`、`kind`、精确 `evidence_quote`、`explanation`、`repairability`、`support_quotes` 和 `confidence`。`kind` 为 `argument_or_reference`、`relation_or_support`、`attachment_or_density`、`lexical_or_translationese`、`possible_capture_issue` 或 `other`。`repairability` 为 `local_reexpression`、`article_supported`、`requires_missing_information` 或 `uncertain`。重视少量具体且有支持的发现，不凑数量。缺陷列表可以为空。普通中文省略、不及物表达、共享主语、名词谓语和有意使用的列表或标题，不自动构成缺陷。仅仅不熟悉技术也不够。

每个反例包含精确 `evidence_quote` 和 `explanation`，说明必要对比或连贯构式为何会被过宽规则破坏。完整文档仍是解释单位。不产生编辑、训练标签、原创准入或事实真值认证。

## 验证与解释

验证出现位置覆盖完整且不重复，所有证据字符串与精确正文一致。保留独立原始复核和分歧。简单一致率只代表助手在这个选定集合上的一致性，绝不代表读者有效性。结合上下文检查分歧和高置信缺陷主张；裁定另行记录，不覆盖原始判断。

提出操作性特征前，先报告来源、体裁、引述声音的聚集和明确反例。新特征定义仍属探索，需要独立匹配文档。可以标记缺失主张或前提，但不能为了改得流畅而编造。无论复核标记多少，Cowork 的已知反馈仍是臭味弱、难读。

## 下一阶段门槛

只有候选真实文章显示可解释、持续的对照，才准备少量具体读者校准。agent 可以提名，不能认证。不根据假定的强标签开展新的去臭效果实验。已经单独确立的难读案例，可以支持明确限定范围的可读性个案研究，但必须检查意义保留，不作臭味结论。

检查新 validation 文档前，冻结前瞻性的来源、主题、格式抽样及诊断定义。扩大样本必须保留零计数文章和对称的 provenance 排除。SFT、DPO、RL reward 和 GPU 配置仍暂缓。

## 复现

```powershell
python experiments/contrast_context_audit.py --output-dir data/local/contrast-context-v1
```

复核 JSON 是助手生成的产物，不能确定性复现。任何衍生结果都必须附其 hash、覆盖检查、复核者身份和范围。确定性准备的外部 API 请求与 GPU 使用均为零；助手复核使用当前 agent runtime，单独报告。
