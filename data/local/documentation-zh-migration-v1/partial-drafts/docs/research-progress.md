# 研究进展

## 与证据关联的话语动作示例

[分析示例](routes/compact-refiner/reports/cognitive-move-analysis-v1.md)
现已使用问题、可选的先前观点或对照项、断言或承诺的内容、关系、依据或论证担保、信息更新
以及立场来描述六个语境案例。焦点动作与证据及后续总结分开呈现；
其中一个成本案例包含两个分别描述的推断。

这种操作化方式保留了有用的硬件纠正和普通解释作为对照，并记录了引发反感的标题
仍然提供组织结构这一点。它并未强行将强样本文章的每句话都归入
某个错误标签。八十处源文本片段出现记录在版本 1.1 中均通过精确校验；
语义解读仍属于助手标注，而非自动准确性结果
或读者效应结果。尚未执行新的关键词匹配器或奖励。

## 先研究机制，再扩展关键词

维护者澄清，更换对比连接词并不会改变目标修辞动作，
并将标题层面的读者议程框架定位出来。
[当前假设](routes/compact-refiner/rhetorical-mechanism-hypothesis.md)
关注的是在缺乏充分解释工作的情况下，反复表现出纠正或洞见：
无缘由的对立、以重新命名充当解释，以及缺乏连贯推进的判定。
这是行为假设，而非已证实的训练机制。词汇匹配器草案尚未执行，
不构成解释性结果或奖励。两个由读者提供的锚点无需额外的严重程度评分。

## 维护者提供的强锚点：2026-09-14

[SMZDM 锚点研究](routes/compact-refiner/reports/reader-anchor-feature-discovery-v1.md)
现已获得明确的人类强度证据：SMZDM `恶臭`，百度 `一般臭`。
强样本文章全文已采集为 30 个 DOM 文本块，其中 22 个发布方
引用标签与正文分开保存。文章自身的 AI 使用披露也单独保留。
旧的字面计数器返回零次 `而是`，而百度文章为三次；字面形式的
出现不能作为这位读者产生强烈印象的必要条件。

两项独立的助手分析提出了四类风格和四类
指代／支撑问题。最清晰的定性风格差异涉及
反复出现的平行判定，以及持续以圈内人口吻或指令式口吻对读者说话。成本范围
外推和未定义的版本三元组是具体的底层问题；
普通的计算相关省略和有用的限制则作为反例予以保留。
这些是以标签为条件的假设，而非编辑或奖励验证。
尚未发起重复评分请求、文章改写或 GPU 工作。

## 撤回 Cowork 预览：优先覆盖目标特征

维护者[否定了重复使用的 Cowork 预览](routes/compact-refiner/reports/cowork-preview-withdrawal.md)，
认为它并不是具有鲜明中文 AI 文风的好例子。它可能通过翻译
继承英语 LLM 的缺陷，却仍然缺乏预期目标特征。
应将此视为样本选择反馈，而非 A/B 偏好、
可读性结果，或全面排除译文的理由。

待进行的读者任务已撤回。已完成的编辑、保真检查、
语法分析运行和呈现工作作为工程证据保留；
它们并未解决强样本发现问题。
[重新筛查](routes/compact-refiner/target-coverage-rescreen.md)检查了十二篇
已采集的后期扩展文章，没有按线索计数排序。
不会仅凭这次重新筛查就安排替代读者任务或新的改写。

[已完成的重新筛查](routes/compact-refiner/reports/target-coverage-rescreen-v1.md)
阅读了全部十二篇正文和 690 个 DOM 块。未提名任何持续呈现目标特征的案例；
九篇仍属弱或模糊案例，三篇的格式匹配度较差。在 DHH 正文中
另行发现的一处翻译披露已被记录，但未改变其旧元数据。
另一项单次查询、单篇文章的定向发现工作，在完成来源身份和机械重叠检查后，
正在考察一篇新的国内公司分析文章；这是经关键词富集的开发材料，
并非另一项流行程度估计。未生成改写。已完成的独立审查支持
一项待进行的原始目标校准，不涉及改写比较。

[定向审查](routes/compact-refiner/reports/targeted-media-discovery-v1.md)
现因该文反复提升抽象层次、替代方案交代不足，以及反复出现缺乏支撑的过渡，
而暂时提名该文，同时保留技术和体裁方面的反例。独立审查的置信度为中等；
维护者感知到的严重程度仍未知。未产出编辑版本。

## 语境、翻译输入与实际句法分析可行性：2026-09-14

[全文审计](routes/compact-refiner/reports/contrast-context-audit-v1.md)
现已有两项独立的助手审查，覆盖 13 篇完整文章和全部 57
处选定出现位置。语义关系一致性为 51/57；表达包装一致性
为 44/57，在任一审查者提名的 21 个重复现象中，有 8 个获得共同提名。
证据与源文本精确一致；审查一致性并不等于人类有效性。具体
发现包括谓词角色转移、缺乏支撑的推断／归因，以及
被提名连接词之外的缺陷。

维护者明确反对一概排除译文，并要求
小型模型仅凭中文输入优化翻译成的中文。
来源背景现作为分层维度；仅保留原创的筛选属于历史／对照
视角。全部 40 篇可用的 InfoQ 正文均保留在新的描述性报告中：
前期 18 篇文章／5 次出现，后期 22/65，频率为每 10,000 个 CJK 字符
0.96/8.38 次。
长篇访谈中一处此前遗漏的明确翻译披露，使一篇出现 19 次的文档
被移入译文层。其余 34 篇文章的来源背景
尚未确定；它们并非经确认的原创文章。

两次成功的本地 CPU Stanza 运行对
三篇文章生成了逐字节相同的标注，共有 164 个解析器句子／5,602 个词。它们揭示了重要局限：
生硬分句被解析出看似合乎语法的树、正常对照文本上的错误、
跨标题／代码的切分，以及一个被表示为 `<UNK>` 的参考资料块。
应将解析用于可追溯的检查；尚无自动质量评分通过验证。

[媒体文本修复开发](routes/compact-refiner/reports/media-repair-development-v1.md)
现有三个完整的纯中文候选版本，其中包括一篇翻译访谈。
独立保真审查最初判定一个通过、一个不确定、
一个未通过。新版本中撤销了五项未通过的操作；所有最终
候选版本均通过助手保真审查，并完成精确的身份链检查。
共用的 DOM 呈现方式抵消了十一处仅涉及空白字符的提取修复带来的差异。
这一结果不构成人类结果、强 AI 味标签、训练导出或 GPU 运行的依据。
此前所有数据及弱结果／失败结果均继续保留。

[新一轮固定扩展](routes/compact-refiner/reports/media-provenance-extension-v1.md)
采集了 24 个新响应，保留了 21 篇去重后的非空正文，以及全部三篇
检出的译文。前期 9 篇／后期 12 篇文档的频率为每
10,000 个 CJK 字符 0.647/6.029 次。一篇长达 22,696 个 CJK 字符的访谈，
贡献了后期 28 次出现中的 19 次；
另行记录的事后集中度检查显示，从计算中移除
该贡献文章后，结果为 3.791，但仍保留了每个来源。
三篇检出的译文均为零次出现。体裁、长度、
历史缺失的不对称性，以及未确定的来源背景仍是混杂因素；
该结果复现的是字面线索差异，而非读者伤害或作者身份。

要求的离线测试套件现已通过 168 项测试及编译。这些审计、修复或扩展
均无需 GPU 或 OpenRouter 请求。

## 读者提名的对比形式族：2026-09-14

维护者指出，反复出现的 `不是……而是……`、`并非……而是……`
及相关 `而是` 形式是一项显著线索，并明确要求进行时间统计。
[新的描述性结果](routes/compact-refiner/reports/ershi-cohort-statistics-v1.md)
使用已获得的同源 InfoQ 正文，排除已知译文，
并分别分析采集批次和长度的敏感性。保留的
前期样本在 17 篇文章中出现 5 次（每 10,000 个 CJK 字符 1.04 次），
后期样本在 18 篇文章中出现 52 次（每 10,000 个字符 8.61 次）。两个采集批次均呈现
相同方向。这不是经过验证的 AI 味评分、作者身份信号或编辑规则。

读者对当前 Cowork 文章的描述仍是 AI 味较弱，但
难读且有翻译腔。产品必须同时处理引发反感的线索
和实际阅读缺陷。字面计数已完成；不能据此推断谓词—论元
和话语缺陷诊断。

## 指导性澄清：在真实媒体中发现目标样本

[校准后的目标](target-feature-discovery.md)保留现有
采集基础设施，以及 2023 之前／2025-06 之后的队列。当前开展的
前半部分工作必须从具有足够明显可感知差异的真实媒体样本中，
提取主观 AI 味印象的可重复特征。维护者表示，
此前的标注样本特征太弱，无法回答这一问题。保留所有
记录，但不要将过去的局部问题反馈用作已确认的强阳性标签，
也不要将合成编辑结果用作产品验证。SFT 仍位于下游。

[新的真实媒体分阶段报告](routes/compact-refiner/reports/media-contrast-calibration-v1.md)
保留前后期框架和所有排除项。独立审查者阅读了
六篇完整的已采集文本，并提名一篇文章用于特定的目标
判断。该提名不是人类标签，来源原创性仍暂不判定。
尚未启动新的效应测试、改写、奖励或训练。

## 当前路线：2026-09-14

维护者暂停了以语料库为先的异味发现工作，启用了单独记录的
[compact-refiner 路线](routes/compact-refiner/README.md)。准备工作和有明确范围限制的 API 实验
可由独立智能体自主推进。
当前工作旨在确认对原文的忠实度、编辑机会、紧凑模型基线，以及可供审阅的候选文本。
模型评估不能替代人类偏好。训练仍推迟到未来由维护者提供云 GPU 后进行。

首轮[自主预检](routes/compact-refiner/reports/cr001-preflight.md)
现已从 24 个计划组中生成 23 份草稿，有 13 个组通过原文检查，设置了三个
编辑实验组，并完成了智能体盲评。3B 基线经常改动条件或遗漏信息；
9B 对照模型出现此类问题较少。根据模型辅助评估，少数
由智能体撰写的提案具有具体的潜在收益。[首轮人类反馈](routes/compact-refiner/reports/cr001-reader-preview-v1.md)
现已记录对三次修订的 A/B/A 偏好，其中配对 1 存在尚未解决的内容
差异，对配对 3 的偏好则明确只是略微倾向。读者
表示，展示的所有配对中均无明显异味。这只能支持有限的
常规编辑观察，不能验证异味消除效果，也不能作为训练验收依据。
在进行下一次编辑比较前，应先确认目标覆盖情况；
目前还不需要 GPU。

## 方法论重新评估：2026-09-14

维护者要求批判性分析：为什么传统 NLP 特征和
统计方法未能验证人们感知到的公式化写作。
[注明日期的重新评估](research-reassessment-2026-09-14.md)区分了构念
效度、测量失效和统计信息有限这几个问题，并提出
新的经典 NLP 实验。这些是建议，而非新近验证的
结果，也不能替代已冻结的协议。当前环境没有
`gx10`；需要推理时已获准使用 OpenRouter，其凭据
保存在已被忽略的根目录 `.env` 中。以下检查点记录了历史
执行条件与证据。

## 检查点：2026-08-31

本检查点包括确定性的篇章与组合结构探针、
扩充后的后期发现语料库，以及五轮已完成的开发阶段盲法
干预。这是探索性研究检查点，而非产品
里程碑。

## 已完成的工作

- 保留了 10 份快速阅读阻力评分，包含有序的继续阅读
  意愿结果和可选的原话评论。
- 继续以时间作为主要比较轴：2023 之前与 2025-07 及之后。
- 将阅读阻力关联分析限制在八个后期
  段落内；两个前期评分单独用于敏感性分析。
- 在每个时间队列内实现了逐特征 Huber 加权，使孤立
  文档的影响降低，而无需手动删除。
- 基于 Stanza 依存解析、命题、实体、抽象概念和相邻
  篇章桥接，实现了确定性的异构篇章图。
- 对 10 篇前期和 10 篇后期 InfoQ
  文档的 161 项文档特征进行了比较，使用 5,000 次固定随机种子的标签置换，
  并检验逐一留出文档时的稳定性。
- 准备并完成了三组盲法最小编辑比较，针对
  公式化的对比式和强调式重述。
- 冻结了保守的第二轮编辑算子，并在七篇后期文档中完成了 10 组新的盲法
  比较，与 10 个阅读阻力开发区间
  均不重叠。
- 在现有的时间比较、阅读阻力和润色材料上，实现并运行了确定性的带类型篇章关系
  支持度探针。
- 审计了一份含 119 篇文档的只读语料库交接包，并运行了按来源分层的
  过渡表达发现探针，以及一项涵盖 23 篇文档的前期分布审计。
- 冻结并完成了含 12 组配对的第三轮开发干预，覆盖技术
  实践、研究摘要和行业报道段落。
- 冻结了一项含 24 个段落的原始文本阅读阻力筛查，在准备任何第四轮干预
  之前，将候选选择与编辑分开。
- 在评分尺度坍缩后终止了绝对评分筛查，并在结果产生前冻结了一项含 10 组配对的
  文档内候选富集替代方案。
- 从两个公开来源获取、筛查、去重、实体化并验证了一份含 50 篇文档的
  全新后期读者开发交接包。
- 在结果产生前冻结了一项含 12 组配对、仅针对后期材料的阅读阻力区分筛查，平衡了
  来源与候选文本的呈现位置。
- 终止了过度控制的原始文本比较，并在结果产生前冻结了一项含 10 组配对、仅针对后期材料的
  原文与保守修订版比较干预。
- 冻结并对全部 67 篇开发文档运行了五种模式的确定性清点，
  同时保持 30 篇文档的验证预留集未启用。
- 复现了先前 OpenRouter 的空回答故障，并在语料分流中加入了明确、
  可审计的推理控制和响应诊断。
- 获取了 720 条新的后期记录，并通过当前三个模型的交集，
  生成了一份经验证、含 93 篇文档、来自三个来源的发现交接包。
- 将已冻结的模式清点方法应用于新的发现交接包，
  未改变其词表或阈值。
- 冻结并在 `gx10` 上运行了用于无边界中心词前名词链的 Stanza 依存探针，
  其中包括一项有文档记录的解析前操作修订。
- 在实现新的词汇信号、选择段落、编辑文本或观察新的
  读者结果之前，冻结了分阶段的边界竞争开发设计。
- 运行了该设计中经外部校准的字到词边界门控，并在编辑前否决了
  该选择器，因为没有任何结构候选进入已冻结的
  高竞争层。
- 完成了范围受限的修饰语括组文献综述，并在 `gx10` 上完成了单独
  冻结的词级依存关联探针；它定位到了
  读者示例，但未能产出独立的高置信度集合。

## 当前证据

时间比较与读者评价中最强且可解释的交集，是形如
`不是/并非/不再是 ... 而是 ...` 的完整对比框架：

- 后期减前期的稳健效应：1.51；
- 时间比较的置换检验 p 值：0.033；
- 仅后期材料的阅读阻力 Spearman rho：0.78；
- 读者评价的精确置换检验 p 值：0.036；
- 两个方向在逐一剔除样本时均保持稳定。

这些 p 值仅具探索性。两项结果均未通过完整的扩展
多重检验校正，而且读者分析仅包含八个
后期段落，实际观察到的评分只有两个等级。

图指标的方向与读者假设一致，但证据仍较弱：

- 相邻篇章桥接均值在后期较低，在不受喜欢的
  段落中也较低；
- 主线绕行比在后期较高，在不受喜欢的段落中也较高；
- 抽象壳层比和无支持边比均朝预期方向变化。

精确谓词签名重复未能奏效。它在完整时间比较
与已评分段落中呈现相反方向，因此不得将其用作
语义重述检测器。

## 第一轮干预结果

对三份减少对比表达的变体与其原文进行了盲法比较：

| 结果 | 数量 |
|---|---:|
| 明确偏好修订版 | 2 |
| 明确偏好原文 | 0 |
| 平局或两者都差 | 1 |

两次胜出表明，去除重复框架并直接说明机制
可以实质性地改善清晰度。两个胜出的编辑版本都被认为
情感过于平淡。失败的编辑删除了过多显式语法论元；
读者认为其中省略的主语、谓语或宾语增加了阅读负担，尽管原文仍保留了
明显的公式化 AI 模式。

因此，下一版编辑算子需要增加两项约束：

1. 跨句保留明确的主谓宾
   结构；
2. 保留适量的语气和节奏，而不是追求最大程度的
   压缩。

这项试验尚不能证明公式化对比可作为产品规则。

## 第二轮干预结果

协议 `conservative-contrast-reduction-2.0` 在任何
第二轮结果产生前就已冻结。只有当实质内容可以直接陈述时，
该算子才会去除装饰性的对比和强调。它必须保留
必要的逻辑对比、明确的语法论元、命题、
实体、数字、否定、限定条件、不确定性、归属说明，以及
适量的语气和节奏。

该批次包含来自七篇文档的 10 个新后期段落。它与全部
10 个已评分开发段落均不重叠，而不仅仅是与第一轮的三个
干预段落不重叠。每项编辑均以精确的编辑前后替换记录表示，
附带算子代码、理由和关联的主张 ID。生成的审计包含：

- 26 项已记录的替换操作；
- 62 项命题支持检查；
- 精确的原文哈希与数值字面量保留情况；
- 各配对专属的锁定实体和技术术语；
- 保留对比和语气锚点的记录；
- 在固定随机种子下，五份原文位于 A 侧，五份位于 B 侧。

所有生成门控均通过。已冻结的表层诊断计数从九个
完整对比框架和 16 个强调标记，降至修订段落中的
零个计数实例。这确认了干预操作确已发生；但其本身
并不能证明修订版更好。

盲法结果如下：

| 结果 | 数量 |
|---|---:|
| 明确偏好修订版 | 6 |
| 明确偏好原版 | 0 |
| 持平或两者均无偏好 | 4 |

六次有明确倾向的选择全部支持修订版。两条判为持平的评论称修订版略好，但在主要计数中仍归为持平。没有评论指出事实缺失或逻辑变化。

评论显示出两个重要局限。一段 AI 味较淡的文本，以及一次删除单句强调的修改，都没有带来有意义的差异。另一处修订保留了句子 `因为云上变更天然需要工程化承接`，读者仍将其描述为带有 AI 味的抽象表述。当前操作方法可以减少刻意搭设的关系框架，但无法让周围的每一句话都变得易读。

两轮干预合计的描述性结果为：修订版胜出八次，原版胜出零次，持平五次。两轮均由同一位读者完成，段落经过有意挑选，所有来源均为 InfoQ，且第二轮有四段来自同一篇文档。这是更强的方向性证据，而非泛化结论或干预验证。

## 关系支持探测结果

首次尝试对“所声称的篇章关系是否有实际支持”进行建模时，提取了对比、因果、推论、澄清和强调实例。它使用依存角色、实体、谓词、否定、冻结的反义词集合、比较词、具体内容和抽象外壳内容，比较关系左右两侧的命题。它明确保留了 `indeterminate` 判定。

该探测在全部分析范围内输出了 476 个实例：241 个无法判定，147 个有支持，88 个类型不匹配。它没有产生任何高置信度的无支持或冗余判定。

提出的问题评分未能奏效：

- 每 100 句的问题判定数，其稳健时间效应为 0.04，仅后期样本中的读者评分 Spearman rho 为 0.06；
- 问题判定比例的稳健时间效应为 -0.03，与读者评分的 rho 为 0.00；
- 在第二轮 10 处修订中，该比例仅在两处下降，七处保持不变；
- 没有任何关系支持特征通过多重检验校正。

该规则正确识别出读者在多工具段落中指出的 `相反`，判定其为被误标为对比的详述关系。它也错误地将真实的 7:00 与 7:31 之间的时间对比，以及人工监控与 LLM 监控这两种替代方案，标为不匹配。若干读者不喜欢的 `真正` 框架，仅因后面跟着一个具体分句就被标为有支持。

归一化的宽泛对比密度与读者评分的 rho 为 0.51，但基本没有时间效应（0.06）；强调密度则具有稳定的时间效应 1.34，但与读者评分的 rho 较弱，为 0.17。这进一步说明，有必要将特定的完整否定对比构式与宽泛连接词分开处理。

弃用 v0.1 问题评分。仅保留其提取的实例和原因代码作为审计材料。失败在于语义和结构，而不是可以针对同一小批评分调参解决的阈值问题。

## 只读语料交接结果

本地交接包包含 119 篇文档，与已跟踪的试点语料没有重叠：23 篇前期机器之心候选文档、53 篇过渡期机器之心文档，以及 43 篇过渡期 InfoQ 文档。所有正文文件均通过严格的 UTF-8、SHA-256、CJK 字符计数和行数检查。

交接包中没有后期文档。过渡期文档仍仅作为探索材料，机器之心的可见性尚未验证。模型辅助生成的来源与价值标签仍是测量结果，而非人工金标准。

一项按来源分层的过渡期分析检验了 53 个归一化确定性特征，控制文档长度的对数，在各来源内部对日期进行了 5,000 次置换，并应用了多重检验校正。没有特征的 BH q 低于 0.10。不同来源间方向一致、最强的探索性发现是：

- 引号密度：合并偏相关 rho 为 0.286，p 为 0.0054，q 为 0.286；
- 破折号密度：rho 为 0.250，p 为 0.0138，q 为 0.336；
- 强调框架密度：rho 为 0.221，p 为 0.0320，q 为 0.388。

完整否定对比框架未能复现为共同的过渡期趋势。其合并 rho 为 0.050，其中 InfoQ 呈正向，机器之心则从基本持平到负向。这是反对将先前后期 InfoQ 结果推广至其他来源的直接证据。

这 23 篇前期候选文档保留了完整的未加权分布和逐特征 Huber 权重。描述性文档权重最低的情况主要由代码、列表、标点、标题疑问句及其他格式特征驱动。没有删除任何文档。这些候选文档仍需要在来源、主题、格式、长度和可见性上匹配的后期证据。

唯一一篇经过读者观察的过渡期文章，在确定性特征上并非明显的离群值：其同来源内最大的稳健 z 为 1.84，对应标题中的一个数字。该观察仍仅用于开发校准，不会转化为作者身份标签或验证标签。

## 原始段落阅读阻力筛查

第三轮干预表明，精确标记的存在和体裁平衡，并不能可靠地选出基线阅读阻力有实质意义的段落。因此，第四轮编辑会将候选质量与编辑质量混为一谈。

方案 `raw-passage-friction-screen-development-1.0` 在结果出现前已冻结。它包含来自 24 篇此前未暴露文档的 24 段未经修改的过渡期文本：12 段 InfoQ 文本和 12 段机器之心文本，每个来源各有四段短文本、四段中等长度文本和四段长文本。经过确定性完整性门槛筛选，剩下来自 55 篇文档的 463 段合格文本。选择过程不使用任何 AI 味特征、标记数量、模型评分、读者结果或来源标签。

读者仅提供四级继续阅读意愿判断，以及可选评论。只有两个不愿意等级的评分，才能使段落进入后续开发干预。至少须有四段合格，否则需要重新进行一轮原始文本筛查。最多可编辑八段，超额时的并列情况按冻结的优先顺序处理，而不是依据评论。这 24 篇文档一旦在筛查中展示，就成为开发阶段已暴露材料，不能再用作留出验证材料。

由于缺乏区分度，筛查提前停止。在 Label Studio 已持久化保存的 11 条回答中，10 条为 `fairly willing to continue`，一条为 `not very willing to continue`；其余两个类别无人使用。读者报告完成了 12 条，但不对未持久化的回答进行填补。主导类别占比为 90.9%，且只有一段达到冻结的门槛，低于至少四段的要求。

不要完成剩余任务，也不要用这一批材料准备干预。此次失败同时涉及绝对量表的区分能力失效，以及随机抽取的编辑文本样本普遍可接受。替代的开发筛查应在同一文档内，对按确定性规则排序选出的候选段落与长度匹配的对照段落进行相对比较，保留明确的“无差异”选项，并检验富集效果，而不是强行区分等级。

## 文档内富集筛查

方案 `within-document-friction-enrichment-development-2.0` 在结果出现前已冻结。它比较同一文档中的一个排序候选段落与一个零标记对照段落。匹配门槛要求保持相同的段落长度档位，将 CJK 字符长度比限制在 0.8-1.25，句数差最多为一句，秩和差至少为 1.0，且 CJK 二元组 Jaccard 相似度至少为 0.02。

候选排序使用五个确定性特征在文档内的百分位中秩：目标标记数量、抽象外壳密度、分隔符密度、平均句长和指代性开头比例。候选段落必须包含目标标记，且至少有一个辅助特征投出“位于最高四分位”的票。特征、阈值和权重均不由此前的读者结果决定。

严格匹配后，剩下 10 篇可配对的过渡期文档：八篇 InfoQ 和两篇机器之心。候选段落的展示位置按五比五平衡。筛查在完成三对后终止，三对均被判断为没有有意义的差异。它们的日期分别为 2023-07-18、2023-10-09 和 2023-03-27。

读者正确指出了根本错配：这些过渡期段落普遍缺少产品需要着手改善的、2025-07 之后更强的 AI 风格阅读阻力。三条回答予以保留，但不评估富集阈值，也不得使用这一批材料开展任何干预。错误在于优先考虑未暴露材料是否可用，而非其是否与固定时间轴相符。

交接包中的后期文档为零，最晚日期为 2025-06-11。已跟踪的试点语料包含 10 篇后期文档，但其中九篇已通过读者评分或干预暴露。唯一完全未暴露的后期文档是 `084c17f921cc74b858d04cdb`，仅凭它无法支持另一轮筛查。

## 新增后期材料交接门槛

方案 `post-reader-corpus-handoff-1.1` 在开展任何进一步的读者项目之前已冻结。它不收集数据。它为未来的 DGX 交接定义了只读准入门槛，并防止将过渡期文档接纳为后期读者材料。

开发池至少需要 36 篇发表于
2025-07-01 当日或之后的新文档。要求至少覆盖两个来源，每个来源有 12 篇文档；覆盖三个主题分层，每层六篇文档；并在每种必需格式下各有六篇文档：技术实践、研究综述和行业报道。交接时最好提供
60 篇文档，以便在检查段落前冻结一份独立的文档级留出集。

版本 1.0 曾提出将来源与格式完全交叉。采集结果表明，
不同编辑来源各有擅长的格式，因此这条规则反而会鼓励错误的
格式标注。版本 1.1 在交接准入或读者接触材料之前冻结；
它保留了两个多样性维度，报告完整的交叉表，
并将明确的来源—格式匹配留给后续读者协议处理。

验证器检查正文是否严格符合 UTF-8、哈希值与计数、完全重复和近似
重复、此前的研究接触情况、日期边界、原创来源、
模型与提示词标识、实质价值状态、相对于来源的高
可见度证据，以及覆盖单元格。验证报告若判定失败，程序将以非零状态退出，
不得绕过这一结果创建 Label Studio 任务。现有的 119 篇文档
交接包被拒绝，因为它使用旧协议，且不包含任何后期
文档。

## 新后期文档交接结果

首批 `post-reader-corpus-handoff-1.1` 交付已完成，位于
`F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1`。其中包含 50
篇文档：25 篇 InfoQ 文章和 25 篇美团技术博客文章，发表于
2025-08 至 2026-08。每篇文档均有一份已落盘的 UTF-8 正文和一条
索引记录。

候选筛选流程完整保留：

- 108 个公开页面采集候选；
- 排除与已跟踪试点及此前交接包重复的文档后，剩余 99 篇；
- 经模型辅助判断，84 篇为高置信度原创，14 篇被排除，另有一篇
  来源不确定；
- 58 篇为高置信度实质性文章，16 篇因价值低被排除，另有 10 篇
  价值不确定；
- 57 篇的格式／主题测量具有高置信度，另有一篇置信度低；
- 应用已冻结的 InfoQ 季度内可见度阈值后，剩余 50 篇。

最终格式构成为 24 篇技术实践、八篇研究综述
和 18 篇行业报道。主题构成为 30 篇 AI／模型／智能体、
10 篇商业／行业、六篇软件工程和四篇数据基础设施
文档。来源与格式的专业化分工明确：InfoQ 提供七篇
技术实践和 18 篇行业报道；美团提供 17 篇
技术实践和八篇研究综述。

验证器报告零错误。唯一的警告是，50 篇文档
足以用于读者测试开发，但低于为单独验证留出集所期望的 60 篇
文档阈值。InfoQ 的可见度使用
按发表季度排名的页面浏览量。美团有来源级官方历史记录／信息流
证据，但没有文章级浏览量；这一限制仍被明确保留。
所有模型辅助的来源、价值、格式和主题标签仍然只是
测量结果，而非人工金标准。

## 仅使用新后期文档的读者筛查

协议 `post-only-friction-discrimination-development-3.0` 在结果产生前
冻结。它使用新交接包中的 12 篇文档，构成六对 InfoQ 和六对
美团材料。格式构成为六对技术实践、两对研究
综述和四对行业报道。在严格的行文格式门槛下，仅有两篇研究综述文档
同时产生了完整的候选段落和完整的对照段落；
PDF 标签、作者简介和列表片段仍被排除，不用于
凑足配额。

被 DOM 拆分的短原文行通过确定性方式重新拼接为
互不重叠的完整段落。候选排序仍在单篇文档内进行，并且
要求同时具有目标标记和一个位于最高四分位的辅助结构信号。
不含标记的对照段落按长度、句子数、原文位置以及
CJK 二元组重叠度进行匹配。候选段落的位置按六比六平衡。

读者选择哪个段落更让自己不愿继续阅读，或者报告
没有实质差异。至少需要四对明确选择，才能表明
该批次具有基本区分力。特征富集还要求
至少八对明确选择，且候选段落占比达到 75%。

读者在完成六对后终止了该批次，因为同一文档中的段落
风格相似，缺乏有用的对比差异。四次选择为
没有实质差异，两次选择对照段落更让人不愿继续阅读，
没有一次选择排名候选段落。一条可选评论指出，两个段落
都有明显的 AI 味。

不要评估已冻结的阈值，也不要将此解读为排序证据。
该设计控制了来源、主题、作者和格式，但也同时
消除了大量原本关注的风格差异。未来任何原始段落
比较都必须使用不同文档，同时匹配来源、主题、格式、
长度和可见度。由于这仍会引入内容兴趣
混淆，当前的替代方案是对相同内容进行编辑干预。
任何干预都不得使用项目 5 的段落。

## 第四次干预设置

协议 `post-only-conservative-reframing-development-4.0` 在结果产生前
冻结。它不比较互不相关的原始段落，而是比较相同
内容在有限度的保守编辑前后的版本。这 10 个段落来自
未被项目 5 选中的 10 篇新后期文档：五篇 InfoQ 和五篇
美团文章，段落格式为四个行业报道、三个研究综述和三个
技术实践。

编辑操作者减少装饰性的对比、澄清和强调框架，
同时保留必要逻辑、明确的语法论元、命题、
实体、数字、否定、不确定性、节奏以及作者声音。编辑
不以最大程度压缩为目标。审计记录了 10 项结构化操作、30 项
命题支持检查、锁定的字面文本、声音锚点、精确数字
序列、原文哈希和 unified diff。所有门槛均通过，且原文
位置按五比五平衡。

两个修订草稿因削弱了断言强度而被拒绝；
另一个新引入的因果标记在冻结前被删除。最终的
表层操纵将已冻结的目标标记数量从 16 减少到三个。这体现的是
操纵忠实度，而非读者获益的证据。目前尚无
结果。

## 离群值政策与当前局限

不会因为一名读者不喜欢某篇文档就将其硬删除。稳健权重
按队列和特征分别计算。那段被读者反感的 2022 Red Hat
段落仍保留在已存储的评分中，但不纳入仅后期数据的
读者阅读阻力关联分析。

当前通用的文档典型性汇总未能有把握地将那篇
Red Hat 文档排为前期最突出的离群值。这属于表征
失败，需要用更大规模的匹配数据改进，而不是插入人工
权重的理由。整体文档典型性仍仅作描述；当前
时间比较只使用按特征计算的权重。

## 后期开发集模式清单

协议 `post-development-motif-inventory-0.1` 在对
含 67 篇文档的开发分区运行之前冻结。扫描只使用固定的词汇和
标点规则，不打开 30 篇验证留出文档中的任何正文。

两种模式通过了六篇独立文档和
三个来源这一必要频次门槛。完整对比框架在
全部五个来源的 37 篇文档中出现 124 次。抽象外壳聚集在
四个来源的 12 篇文档中出现 14 次。两者均未提供一致的干预目标。已冻结的
按来源分层的对比样本包含真实替代选项、机制
区分、引用的定义、基准评测标准和原文片段。
全部 14 个外壳聚集都混合了正常的技术用法、重复的字面含义和
列表片段，而非一种可编辑的结构。

其他规则未通过频次门槛：四篇文档中有四个
密集分句表层候选，三篇文档中有四个强调型抽象内容候选，
严格的中心语后置低锚定堆叠则为零。没有准备项目 8。
这一结果进一步凸显了选择精度的限制：高频
标记或抽象名词不足以作为干预选择依据。

## OpenRouter 结构化输出修正

此前 MiMo-V2.5 和 Hy3 的冒烟测试失败属于接口假阴性。
旧请求发送了本地服务器专用的
`chat_template_kwargs.enable_thinking=false` 字段，且只允许 320 个输出
token。直接复现表明，两个模型几乎将
全部额度用于推理，返回 `finish_reason=length`，且未输出
任何回答内容。

使用 OpenRouter 的显式推理控制并提供充足预算后，
MiMo-V2.5、MiMo-V2.5-Pro、Hy3、Hy4 Preview、
GLM 5.3 Flash、DeepSeek V4 Flash 0731、Qwen3.8 Flash、Qwen3.8 Max 和 Qwen3.8
2.4T-A95B 均生成了符合 schema 的有效回答。Hy4 最初返回了文档中已说明的上游共享池 429，
随后重试成功。这证明的是接口兼容性，而非
任务准确率。

分诊客户端现在将推理模式和 token 预算纳入缓存
标识和清单，提取字符串形式及内容分块形式的回答，并保留
不含敏感信息的结束、内容、推理和 token 诊断信息。

A fixed 12-document, five-source panel then ran the same provenance and value
prompts across seven current models. DeepSeek, MiMo, Hy3, GLM 5.3 Flash,
Qwen3.8 Max, and Qwen3.8 2.4T-A95B completed all 24 calls. Hy4 completed only
one because the shared upstream pool rate-limited the other 23. The panel has
no human gold and cannot rank accuracy.

The next acquisition batch therefore freezes a three-model fail-closed policy:
DeepSeek and GLM screen every deterministic candidate, while Qwen3.8 Max reviews
only their provisional high-confidence agreements. Final admission requires
high-confidence agreement from all three. This uses larger current models
without spending the most expensive endpoint on candidates already excluded by
the first two measurements.

## Current-model post corpus expansion v3

The completed local handoff contains 93 post-period documents from Huawei,
Leiphone, and QbitAI. Its validator reports zero errors and zero warnings. The
flow is 720 raw acquisitions, 561 after deterministic translation and duplicate
exclusion, 372 after DeepSeek-plus-GLM provenance agreement, 130 after their
two-prompt value agreement, 103 after Qwen3.8 Max value review, and 93 after the
frozen Huawei visibility threshold.

The final composition is 39 Leiphone, 32 Huawei, and 22 QbitAI documents; 40
industry reports, 34 technical-practice articles, and 19 research summaries.
All model labels remain measurements. Fifty-three of 93 documents are from
2026-08, source and format remain strongly confounded, and editorial
distribution is not article-level readership for Leiphone or QbitAI. The pool
cannot support a matched pre/post estimate.

The DeepSeek provenance run had one documented process-restart anomaly. An
orphan and its retry briefly wrote the same cache, creating 95 duplicate cache
keys. The raw cache is retained, the stale processes were stopped, and the
final result was regenerated to exactly 561 unique document IDs. No value cache
contains a duplicate key.

The handoff initially assigned all 93 documents to a discovery reserve. The
frozen motif scan subsequently opened every body, making the full handoff
feature-discovery exposed. The scan found zero strict delayed-head low-anchor
instances, two dense-clause surface candidates, and two emphatic abstract-
payload candidates. Complete contrast and the already rejected shell-cluster
proxy remained frequent but semantically heterogeneous. No Project 8 is
prepared.

## Boundary-free nominal-chain probe

Protocol `nominal-chain-integration-probe-0.2` replaces an aborted full-body
operational attempt. Version 0.1 wrote no candidate result: a 1,501-line tutorial
kept Stanza occupied because code and DOM fragments were filtered only after
parsing. Version 0.2 freezes the existing content-agnostic complete-passage gate
before parsing and leaves all nominal-chain thresholds unchanged.

The final `gx10` run parsed 1,393 complete passages from 133 of the 160 requested
documents. It accurately localized the reader example and found 87 candidates
in 41 documents across five sources, passing the preregistered frequency gate.
It failed the coherence gate. Forty-seven instances contain proper-name or
numeric anchors, 67 have dependency-chain depth one, and the set mixes formal
names, specifications, technical compounds, dense modifiers, and parser part-
of-speech errors.

The narrower audit-only subgroup with no recorded anchor and depth at least two
contains 13 instances in seven documents and four sources. Six come from one
QbitAI document; the rest still mix titles, official program names, ordinary
terms, parsed contrast, and possible integration problems. The probe therefore
does not support one edit operator across six independent documents. Reject it
as an intervention selector, retain the reader example as a single case, and do
not prepare Project 8.

## Boundary-competition experiment design

Protocol `boundary-competition-development-1.0` converts the reader-localized
segmentation observation into a staged, falsifiable experiment without
promoting the rejected UD candidate rule. Stage 0 must implement an explicit
lexical vector using segmentation-path entropy, best-versus-second path margin,
gap-level boundary posteriors, ambiguous-gap count, and unresolved distance to
the head. Branching entropy, accessor variety, tokenizer disagreement, and
proper-name or technical anchors remain diagnostics in version 1.0 rather than
admission rules.

External percentile cutoffs must be calibrated and hashed before the
post-period pool is ranked. The working reader example must be localized without
a phrase-specific exception. The reader stage additionally requires eight high-
competition and eight matched low-competition passages from 16 distinct,
previously unexposed post-period documents, at least three sources, and at
least two formats per stratum. The 30-document validation reserve remains
unopened. Failure to assemble all eight matched blocks stops the experiment;
thresholds may not be relaxed to force a batch.

Every selected passage receives the same boundary-only structural-unpacking
operator. The editor is blind to high/low stratum and display side. The 16
interventions are balanced within stratum and session, with one identical-text
diagnostic and one later mirrored repeat, for 18 tasks under seed `2026083101`.
The reader still answers only which version makes them more willing to
continue, with an explicit no-difference choice.

The development decision requires passed instrument, preservation, and
manipulation gates; at least six decisive high-stratum answers; at least 75%
revised preference among those answers; high-stratum net preference of at least
0.50; and a high-minus-low selector contrast of at least 0.50. Low-stratum
benefit without contrast rejects the selector even if the operator remains
interesting. Optional comments cannot affect any gate.

Exact-binomial sensitivity shows why this 16-passage experiment cannot be
called validation. With no ties, a true revised preference probability of 0.70
requires 49 decisive comparisons for 80% power at two-sided alpha 0.05; 0.75
requires 30, and 0.80 requires 20. Repeated outcomes from the same reader do not
provide independent reader replication at any of those counts. A later
confirmatory design must use multiple readers, held-out passages, and
simulation under a crossed reader-item model.

Stage 0 subsequently used SUBTLEX-CH and 150 public Beijing Sentence Corpus
sentences to calibrate the frozen lattice. All 87 prior structural candidates
were scored without opening the validation reserve. Zero candidates entered
the high-competition stratum; 36 instances in 23 documents entered the low
stratum, and 51 instances were middle or unscored. Seven candidates passed the
entropy and path-margin gates, but only one had two ambiguous character gaps
and none reached the required unresolved distance of six characters. The
maximum was four, so no high/low matching edge existed.

The reader example itself had zero ambiguous gaps, unresolved distance two,
entropy percentile 0.669, and margin percentile 0.346. Its best SUBTLEX path
was `原生 / 时代 / 全新 / 算 / 力 / 服务`; the outdated-domain split of `算力`
is recorded rather than corrected after the result. Reject
`boundary_competition_v1`, do not create Project 8, and reinterpret the current
hypothesis as word-level modifier-attachment or phrase-bracketing competition
rather than character-to-word segmentation.

## Word-level modifier-bracketing probe

A bounded OpenAlex, Crossref, and Semantic Scholar search identified English
noun-compound methods based on dependency probabilities, word association,
term evidence, and hidden-relation paraphrases, plus contextual Mandarin work
on word frequency, semantic transparency, and word structure. Search queries,
partial-result limits, OpenAlex budget exhaustion, Semantic Scholar 429 errors,
and six exact-DOI abstract checks are recorded. The transfer from English noun
compounds to Chinese technical modifier stacks remains an unvalidated analogy.

Protocol `modifier-bracketing-probe-0.2` enumerates every right-headed binary
tree over Stanza content tokens. It scores attachments with ordered token-pair
probabilities from 1,393 complete passages while excluding the candidate's
entire document. Proper names, numbers, ASCII terms, quoted titles, token
familiarity, exact-sequence termhood, and cross-source support remain separate
rival variables.

Version 0.1 was operationally invalid because percentile midranks made a tied
minimum-margin gate impossible. Version 0.2 froze a `1e-12` numerical-zero
tolerance and nearest-rank value cutoffs before rerunning; no substantive
threshold or input changed. Two independent `gx10` runs then produced
byte-identical artifacts.

The reader example passes the case-level gate: normalized tree entropy 0.822,
zero best-second margin, 0.857 familiar-token fraction, and four weak
attachments. The multi-source gate fails. Of 34 scorable candidates, seven
pass the entropy gate, 26 the margin gate, 17 the familiarity gate, and 27 the
weak-attachment gate. Five pass entropy and margin together, but none also pass
familiarity. Those five are names or sparse technical strings rather than an
independent set of familiar-word modifier stacks.

Reject the current word-level tree-entropy vector as an intervention selector.
Retain attachment competition only as a localized explanation for the one
reader example. The stronger next candidate is hidden semantic-relation
underdetermination, but this result does not prove it. Any new familiar-word
weak-relation measurement must be frozen and tested on an independent corpus;
the 87 exposed candidates cannot be re-filtered after this result. No Project 8
is prepared.

## Reproducible artifacts

- `data/annotations/reader-friction-v1.json`: 10 quick ratings.
- `data/annotations/refinement-pairwise-v1.json`: three blinded A/B outcomes.
- `data/annotations/refinement-pairwise-v2.json`: 10 conservative second-round
  outcomes with frozen artifact fingerprints and operation identities.
- `data/annotations/refinement-pairwise-v3.json`: 12 cross-genre development
  outcomes and the reader's round-level baseline-friction observation.
- `data/annotations/refinement-pairwise-v4.json`: 10 fresh-post intervention
  outcomes, the complete side-B selection diagnostic, and the reader's
  compositional-difficulty observation.
- `data/annotations/integration-pairwise-v1.json`: six proposition-
  decompression outcomes, two passed position controls, and localized reader
  observations about delayed heads and abstract modifier stacks.
- `data/annotations/reader-friction-screen-v1.json`: 11 persisted absolute
  ratings, the early-stop discrepancy, and the instrument-failure decision.
- `data/annotations/reader-friction-screen-v2.json`: three no-difference
  responses and the transition-corpus mismatch termination decision.
- `data/annotations/reader-friction-screen-v3.json`: six post-only responses
  and the within-document over-control termination decision.
- `src/deaiodorant/analysis/discourse_graph.py`: graph schema and metrics.
- `experiments/analyze_reader_friction.py`: post-only ordinal association.
- `experiments/robust_typicality_probe.py`: cohort-wise Huber analysis.
- `experiments/prepare_refinement_pairs.py`: frozen three-pair intervention.
- `experiments/prepare_refinement_pairs_v2.py`: frozen 10-pair conservative
  intervention with structured operation and preservation logs.
- `experiments/refinement-pairs-v2.md`: second-round protocol and passage set.
- `experiments/prepare_refinement_pairs_v3.py`: frozen 12-pair cross-genre
  development generator.
- `experiments/refinement-pairs-v3.md`: third-round protocol, audit, and result.
- `experiments/prepare_reader_friction_screen_v1.py`: deterministic balanced
  selection and Label Studio task generation for unchanged passages.
- `experiments/reader-friction-screen-v1.md`: frozen screen, follow-up gate,
  passage identities, artifact hashes, and reproduction command.
- `experiments/prepare_reader_friction_screen_v2.py`: within-document ranking,
  matching, blinding, and Label Studio task generation.
- `experiments/reader-friction-screen-v2.md`: frozen replacement protocol,
  pair identities, decision threshold, limitations, and artifact hashes.
- `experiments/validate_post_reader_handoff.py`: read-only admission,
  disjointness, duplicate, integrity, and minimum-coverage gate.
- `experiments/post-reader-corpus-handoff.md`: frozen post-period handoff schema
  and the planned low-burden reader use after admission.
- `experiments/acquire_post_candidates.py`: post-only InfoQ acquisition staging.
- `experiments/acquire_meituan_post_candidates.py`: public official-history
  Meituan technical-blog acquisition staging.
- `experiments/prepare_post_review_candidates.py`: cross-corpus duplicate
  exclusion and model-review candidate preparation.
- `experiments/classify_post_corpus_strata.py`: cached model-assisted format and
  topic measurements for balancing only.
- `experiments/build_post_reader_handoff.py`: fail-closed admission,
  visibility filtering, materialization, and manifest generation.
- `experiments/prepare_reader_friction_screen_v3.py`: post-only passage
  reconstruction, candidate/control matching, blinding, and task generation.
- `experiments/reader-friction-screen-v3.md`: frozen post-only reader protocol,
  pair identities, thresholds, limitations, and artifact hashes.
- `experiments/prepare_refinement_pairs_v4.py`: fresh post-only conservative
  intervention, structured operation logs, and preservation gates.
- `experiments/refinement-pairs-v4.md`: frozen fourth-intervention protocol,
  passage identities, audit, compromised outcome, and artifact hashes.
- `experiments/compositional_burden_probe.py`: deterministic integration-load
  vector for controlled variants without a composite score.
- `experiments/scan_post_compositional_burden.py`: source-format-stratified
  discovery scan over previously unselected post passages.
- `experiments/compositional-burden-probe.md`: measurement definitions,
  fourth-round diagnostics, scan results, and limitations.
- `experiments/prepare_integration_pairs_v1.py`: bounded proposition-
  decompression intervention with preservation and position controls.
- `experiments/integration-pairs-v1.md`: frozen fifth-development protocol,
  passage identities, passed position gate, split outcome, and reproduction
  identity.
- `experiments/head_final_modifier_probe.py`: model-free cue-to-head span and
  low-anchor abstract-modifier candidate extraction.
- `experiments/head-final-modifier-probe.md`: localized construction,
  deterministic rule, corpus audit, false positives, and admission boundary.
- `experiments/inventory_post_development_motifs.py`: frozen five-motif scan of
  the development partition only.
- `experiments/post-development-motif-inventory.md`: rules, frequency gate,
  result, coherence audit, and no-intervention decision.
- `experiments/compare_openrouter_corpus_models.py`: fixed-panel current-model
  interface and cross-model measurement comparison without human gold.
- `experiments/openrouter-corpus-model-interface-audit.md`: live model evidence,
  empty-answer diagnosis, fixed-panel results, and frozen batch policy.
- `experiments/acquire_editorial_post_candidates.py`: public QbitAI and
  Leiphone post-period acquisition staging.
- `experiments/acquire_huawei_post_candidates.py`: topic-focused public Huawei
  recommendation and article-view acquisition staging.
- `experiments/snapshot_openrouter_rankings.py`: live public weekly-usage
  ranking snapshot used for current-model selection.
- `experiments/compare_provenance_models.py`: fail-closed two-model provenance
  intersection and disagreement report.
- `experiments/compare_value_models.py`: fail-closed two-model research-value
  intersection and disagreement report.
- `experiments/build_expanded_post_reader_handoff.py`: five-source handoff
  materialization and frozen development/reserve assignment.
- `experiments/post-reader-corpus-expansion-v2.md`: acquisition flow, live model
  selection, model effects, final composition, partition, and identity.
- `experiments/post-reader-corpus-expansion-v3.md`: current-model admission,
  run anomaly, final discovery composition, limitations, and identity.
- `experiments/nominal_chain_integration_probe.py`: frozen pre-parse prose gate
  and dependency-based boundary-free nominal-chain extraction.
- `experiments/nominal-chain-integration-probe.md`: protocol revisions,
  aggregate result, coherence failure, and rejection decision.
- `experiments/design_boundary_competition_experiment.py`: frozen balanced
  placeholder allocation and exact-binomial sensitivity calculation.
- `experiments/boundary-competition-development.md`: pre-outcome staged
  measurement, intervention, randomization, analysis, decision protocol, and
  failed Stage 0 result.
- `src/deaiodorant/analysis/boundary_competition.py`: deterministic SUBTLEX
  segmentation lattice, gap posteriors, path entropy, path margin, and
  branching diagnostics.
- `experiments/boundary_competition_probe.py`: Beijing Sentence Corpus
  calibration, frozen candidate classification, corpus-separation audit, and
  high/low matching gate.
- `experiments/modifier-bracketing-search-boundary.json`: bounded literature
  queries, result-depth limits, API failures, and coverage statement.
- `experiments/modifier-bracketing-evidence-ledger.csv`: seven auditable
  source-to-claim records, including the challenging local Stage 0 result.
- `experiments/modifier-bracketing-prediction-matrix.csv`: prespecified
  discriminating predictions for attachment, semantic, term, and global-load
  candidates.
- `experiments/modifier_bracketing_probe.py`: cross-fitted word association,
  exhaustive right-headed tree enumeration, anchor diagnostics, and frozen
  computational gates.
- `experiments/modifier-bracketing-probe.md`: literature boundary, rivals,
  protocol deviation, complete result, and reproduction identity.
- `src/deaiodorant/analysis/discourse_relations.py`: deterministic relation
  instances, evidence vectors, abstentions, and reason codes.
- `experiments/relation_support_probe.py`: existing-corpus time, reader, and
  intervention comparison.
- `experiments/relation-support-probe.md`: complete method, results,
  counterexamples, and rejection decision.
- `experiments/handoff_transition_probe.py`: read-only handoff audit,
  source-stratified transition trends, and pre-period Huber weights.
- `experiments/handoff-transition-probe.md`: handoff method, complete results,
  limitations, and reproduction identity.
- `experiments/discourse-graph-probe.md`: method and detailed evidence.
- `docs/smell-catalog.md`: evidence-status integration.

Generated `feature_runs/` artifacts and Stanza weights are intentionally
ignored. They can be reproduced from the tracked pilot corpus and scripts.
Local model inference, including bulk parser inference, runs on `gx10`; the
local workstation is limited to deterministic artifact preparation and checks.
Remote API inference may use OpenRouter with the ignored key held only in
process memory and with model, reasoning mode, token budget, and prompt version
recorded.

## Next research step

Do not build a product interface, train a general classifier, or ask the reader
to continue any stopped screen. The fourth intervention is complete: five
revised preferences, four original preferences, and one no-difference answer.
All nine decisive answers selected side B despite balanced original placement,
so the treatment totals are position-confounded and do not validate the
operator.

The reader reported a separate form of difficulty in which familiar individual
words become difficult to integrate as a whole. A deterministic post-outcome
probe found mixed evidence: revisions reduced function-to-content ratio in all
10 pairs and increased content per clause head in six, but usually reduced
sentence length, tree depth, and long dependencies. No composite burden score
is defined or validated.

The proposition-decompression intervention is complete. Its identical-text and
mirrored controls both passed, so the six treatment outcomes are interpretable
as development evidence. Three revisions and three originals were preferred,
with no ties. Generic sentence splitting or proposition decompression is not
promoted.

One preferred revision retained a reader-localized problem: `AI 原生时代全新的
算力服务需求`. The head noun `需求` arrives after a long modifier string, and
the generic era and novelty modifiers do not specify what makes the requirement
new. A model-free lexical probe localizes both the original and revised forms.

The first 50-document handoff left only 21 development-eligible documents after
projects 5 through 7. Public QbitAI, Leiphone, and Huawei acquisition added 319
raw records. Deterministic translation and duplicate exclusion, current-model
source agreement, two-prompt value screening, cross-model value agreement,
strata confidence, and visibility filtering produced a new 97-document,
five-source handoff. It passes the frozen validator with zero errors and zero
warnings.

Model choice used a captured live OpenRouter weekly-usage ranking rather than
remembered popularity. Opaque Ox Alpha was excluded. DeepSeek V4 Flash 0731,
the number-two model, passed the task-specific structured-output smoke test.
MiMo-V2.5 and Hy3 appeared to return empty answer content and were not batch-
run. A later audit reproduced those empty answers as token-budget exhaustion:
the unsupported disable-thinking field left reasoning enabled, and reasoning
consumed all 320 completion tokens. Both models return valid structured answers
under corrected OpenRouter parameters. The v2 handoff retains its original
Qwen3.8-27B plus DeepSeek measurement identity; the interface correction does
not retroactively change it. The ignored API key was never persisted or copied
to `gx10`.

The role split is frozen before new paragraph analysis: 67 development
documents and 30 validation-reserve documents. The reserve has not been read
for feature discovery and cannot support validation without multiple readers.

Applying the same frozen rule to the separate 119-document handoff produced 38
broad delayed-head candidates but zero strict low-anchor abstract stacks. The
strict motif did not replicate. The handoff contains only pre and transition
documents and is not matched to the post pool, so this zero cannot estimate a
time effect.

Applying it only to the expanded handoff's development partition produced 23
broad candidates across 14 documents and again zero strict instances. The
validation reserve was not read. Do not relax the definition against these
results or create project 8 from broad false-positive candidates.

The wider frozen motif inventory also failed to produce a coherent selector.
The new 93-document handoff passed the fixed current-model and integrity gates
and was disjoint from both v2 partitions and every prior reader artifact. Its
complete frozen-rule scan again found zero strict delayed-head instances and no
new coherent operator. All 93 documents are now feature-discovery exposed, not
reader-validation material.

The immediate step is no longer to prepare a boundary- or bracketing-based
reader batch. Both selectors failed their frozen corpus gates. The one reader
example is compatible with word-level attachment competition, but the same
tree-entropy pattern does not appear among familiar-word candidates across the
development corpus. The next candidate is hidden semantic-relation
underdetermination: familiar words are juxtaposed without saying how their
claims relate. A deterministic familiar-word weak-relation rule must be frozen
before collecting and opening a new independent post-period discovery corpus.
Do not re-filter the exposed 87 candidates or open the validation reserve.

The broader Stanza nominal-chain probe does not remove this requirement. Its
frequency gate passed but its candidates were not one construction. The new
protocol used an independently frozen lexical-familiarity and segmentation-
boundary vector; Stage 0 failed. Post-hoc lexical blacklists against the 87
candidates remain prohibited, and no Project 8 was created.

This remains single-reader development work. The expanded corpus now preserves
an independent document reserve with three sources, three formats, and three
topic strata. Held-out validation still requires multiple independent readers
and a frozen operator and analysis plan before outcomes.

Do not tune the rejected relation-support score against the same 10 ratings.
Further work on actual relation support requires either a narrower formally
testable motif or independent expert span annotations. The reader should not be
asked to supply those linguistic labels.

In parallel, run the same graph features on the larger matched corpus when it
arrives. Match source, topic, format, length, and visibility before interpreting
the time effect.

The current 119-document handoff is not that matched corpus: it has no post
documents and unverified Machine Heart visibility. It expands discovery only.

The third intervention round uses 12 transition passages from this discovery-
exposed handoff. It broadens genre coverage but is development evidence, not
held-out validation. Its operator, passages, edits, preservation checks, task
order, and A/B balance were frozen before outcomes.

The outcome is four revised wins, one original win, and seven ties or neither-
preferred judgments. Research summaries produced two wins and two ties;
technical practice produced one win, one original win, and two ties; industry
reporting produced one win and three ties. The reader reported that almost all
pairs had little difference because the original passages had little obvious
smell. Only one optional comment identified a specific marker: `换句话说`.

The third round therefore diagnoses a selection problem, not a reason to
rewrite more aggressively. Marker presence and genre balance alone do not
identify passages with enough baseline friction to benefit. Future development
sampling should use a separate low-burden baseline-friction screen, while
keeping screened material out of held-out validation. See
`experiments/refinement-pairs-v3.md` and
`data/annotations/refinement-pairwise-v3.json`.

That screen was frozen as `experiments/reader-friction-screen-v1.md` and then
terminated early. Ten of 11 persisted responses occupied one category, so the
remaining tasks are not needed. The replacement should compare ranked and
matched-control passages within the same document rather than repeat the same
absolute-rating design.

That replacement is now frozen as
`experiments/reader-friction-screen-v2.md`. It contains 10 blinded pairs and
retains an explicit no-meaningful-difference choice. It was terminated after
three no-difference responses because every completed pair came from the
transition period. The ranking is not evaluated from this mismatched batch.
