# 词级修饰语括分探测

## 状态

协议 `modifier-bracketing-probe-0.2` 于 2026-08-31 冻结，早于修订后的 Stanza 运行、关联计数、候选评分或读者任务生成。这是在 development-exposed 材料上的探索性计算门槛，不是干预、验证研究或作者身份分析。

之前的字到词边界模型未通过冻结阶段 0。本协议是新假设和新测量，不在事后放宽、替换或重新解释失败阈值。

版本 0.1 完成一次操作运行，但科学上不可解释。34 个可评分候选中的 26 个最优与次优路径差低于 `1e-12`。实现将各差值的百分位 midrank 与 0.20 比较；并列最小值获得 midrank 0.382，使原意为“不高于第 20 百分位值”的门槛不可能通过。版本 0.2 在重跑前冻结两项数值修正：低于 `1e-12` 的差设为零，原始值与 nearest-rank 经验分位数比较。没有改变语义阈值、语料、候选、关联窗口、熟悉度规则或读者结果。保留版本 0.1 产物作为操作偏离，不作为假设证据。

## 冻结观察

一位读者报告，`AI 原生时代全新算力服务需求` 中每个词都可理解，但组合困难，后到的中心词 `需求` 延迟了稳定理解。这是单个开发观察。

随后冻结 SUBTLEX 探测发现中心词前字符串没有歧义字间隙，未消歧距离为二；全部 87 个结构候选中，高层案例为零。因此，所测试的字到词分割模型未能解释该观察。

## 带日期的证据边界

2026-08-31 检索了 OpenAlex、Crossref 和 Semantic Scholar。检索式、结果限制、API 失败和覆盖限制保存在 `modifier-bracketing-search-boundary.json`；来源与主张关联在 `modifier-bracketing-evidence-ledger.csv`。检索有界且以英文元数据为主，不能确立新颖性，也不代表全面中文文献综述。Semantic Scholar 返回 HTTP 429，OpenAlex 在有界分页后耗尽匿名每日检索预算。

操作路线是类比迁移，未直接在中文技术文字上验证：

- Lauer（1995，<https://doi.org/10.3115/981658.981665>）比较统计名词复合词分析，在报告的英文任务中，dependency model 比 deepest-constituent model 更准确。
- Barriere 与 Menard（2014，<https://doi.org/10.3115/V1/W14-5708>）组合词汇、关系及并列关联证据，进行多词名词复合词括分。
- Nakov（<https://arxiv.org/abs/1912.01113>）将结构括分与隐含名词关系的显式释义视为不同问题。
- Fares（2016，<https://doi.org/10.18653/V1/P16-3011>）同样将括分和语义关系解释表示为关联但可分离的目标。
- Dronjic（2011，<https://doi.org/10.1093/wsr/wsr005>）综述了“词而非语素是普通话复合词基本表示单位”的证据。
- Hao、Wu 与 Duan（2024，<https://doi.org/10.1177/21582440241256249>）报告了涉及词频、语义透明度和词结构的加工差异。

这些来源均未证明读者定位的结构是一般臭味，也未证明拟议测量有效。

## 候选假设与竞争解释

### H-BRACKET：附着竞争

长后置中心名词序列中的熟悉词，可能支持多棵同样合理的修饰附着树。读者必须一直保留备选到最终中心词到来，增加整合成本。

### H-SEMANTIC：隐含关系欠明确

附着结构可能可恢复，但 `AI 原生时代` 如何使服务需求变得 `全新` 等关系没有陈述。因此，只调结构顺序、没有明确关系仍不够。

### H-TERM：领域术语或名称不匹配

低语料关联可能反映参考语料缺少的既定产品名、技术复合词、标题或新领域术语。测量会把语料覆盖问题误判为阅读阻力。

### H-GLOBAL：段落级负担

名词片段可能只是显眼症状，实际困难可能来自分句密度、命题负担、指代结构或周边论证组织。

### H-PARSER：处理伪影

Stanza 分词或依存错误可能制造候选片段或表面歧义。解析器一致性不是语言学 ground truth。

区分这些候选的预测冻结在 `modifier-bracketing-prediction-matrix.csv`。仍可能存在混合解释。

## 输入边界

精确使用 `feature_runs/nominal-chain-integration-v1/candidates.jsonl` 中的 87 个实例，SHA-256 为 `abfb5a5e9181c5b0e87d5636f649766c1c82437326ac5a0740229eec89e674c2`。它们来自 `post_reader_handoff_v2` 的 67 篇 development 文档，以及 `post_reader_handoff_v3` 的全部 93 篇 discovery-exposed 文档。早先候选生成已排除 30 篇 validation reserve，不得打开。

全部关联计数只使用相同的 160 篇 development/discovery 文档和冻结完整正文门槛。每个候选的计数排除其整篇来源文档；leave-one-document-out 规则避免把同篇重复当作附着支撑。

## 冻结解析器与对齐门槛

解析仅在 `gx10` 上进行，使用 Stanza `zh-hans/gsdsimp`、processors `tokenize,pos,lemma,depparse` 及已记录模型指纹 `5fa23dfff06b543c63ef547b32006bb0a9acdd6bc1a3a1df23d768a171352af9`。

每个候选重解析必须复现来源句、中心词形式、左边界及中心词前词汇 token 数。目标序列包含从左边界到中心词的所有非标点 token。少于四个或多于 10 个目标 token、内部有动词、显式并列或 `的/之` 边界、或对齐失败时弃判。不得人工修改 token 或依存。

## Cross-fitted 关联模型

实词 lemma 作 case folding，缺失时退回表面形式。关联语料按文档和来源分别记录：

- Token 出现次数及文档／来源频次；
- 后续四个实词 token 窗口内的有序词对次数；
- 相邻有序词对次数；
- 精确目标序列的文档及来源频次；
- 由 `、/和/与/及/或` 连接的显式并列次数。

对于候选文档 `d`，减去 `d` 贡献的全部计数。主要附着概率为 Lauer 式条件关联：

~~~text
P(head | modifier, not d)
  = (ordered_pair_count + 0.1)
    / (all_outgoing_pair_count_for_modifier + 0.1 * vocabulary_size)
~~~

相邻 NPMI、词对文档／来源频次、并列证据及精确序列 termhood 保持为独立诊断，在版本 0.2 中不改变主要树概率。

一个 token 只有出现在至少五篇其他文章和至少两个来源中，才为 `cross-corpus familiar`。报告熟悉目标 token 比例。低熟悉度支持 H-TERM 或语料不足，不自动等于高括分竞争。

## 右中心括分格

穷举目标词序列的所有完整二叉括分。每个成分继承最右词汇中心词；合并左右成分时，添加从左成分中心词指向右成分中心词的一条有向附着。树分数为各条件附着概率 log 的和。

对所有树分数作 softmax 归一化，得到：

- 除以 `log(Catalan(n - 1))` 的归一化树熵；
- 除以 `n - 1` 个附着的最优与次优树差；
- 每个附着的后验概率；
- 最佳树中，至多获一篇其他文档和一个来源支撑的附着数；
- 最佳括分及附着审查。

探测公开此向量，不压成通用写作质量分数。

## 冻结计算门槛

百分位基于固定 87 候选池的可评分实例计算，因此本次运行属于相对该池的探索，不构成外部常模。

第 80、20、50 百分位门槛使用 nearest-rank 经验值：将 `n` 项测量排序，按从一开始的索引选择 `ceil(p * n)` 项。门槛将原始测量与该值比较；midrank 百分位只用于描述。

只有以下条件全部满足，候选才为 `high bracketing competition`：

- 归一化树熵达到或超过合并池第 80 百分位；
- 归一化最优与次优差不高于合并池第 20 百分位；
- 至少 80% 目标 token 为 cross-corpus familiar；
- 最佳树至少两个附着的支撑不超过一篇其他文档和一个来源。

工作示例必须完全对齐，熟悉 token 比例至少 0.80，熵不低于合并中位数、路径差不高于合并中位数，且至少两个弱最佳树附着。失败将挑战本测量下的 H-BRACKET，并停止路线。

多来源门槛另要求至少三个来源、八篇高竞争文档。每来源最多三篇，按固定元组选择：熵降序、路径差升序、经熟悉度调整的弱边数降序、SHA-256 打破平局。选中的八篇至少四篇不含专名、数字、ASCII 或引号标题锚点。这是覆盖要求，不是人工删除有锚点案例；报告保留锚点分层计数。

工作示例或多来源门槛任一失败，版本 0.2 结束。看到结果后，不得更改关联窗口、平滑、熟悉度计数、百分位、解析 token 或锚点定义。

## 解释矩阵

- 示例及多来源门槛通过，且锚点不占主导：保留 H-BRACKET 为可进入检验的开发候选，另行设计仅调整边界的干预。
- 高分主要出现在锚点或不熟悉术语：保留 H-TERM，否决括分筛选器。
- 测量有效但示例树熵低：挑战 H-BRACKET，优先 H-SEMANTIC。
- 解析对齐或关联覆盖失败：结果无法确定；在独立材料上修订测量，不将它解释为语言证据。
- 全局段落特征可与任何结果并存，后续需匹配干预区分 H-GLOBAL。

本计算探测的任何结果均不直接授权 Project 8。读者实验仍需独立冻结算子、原意保留审查、高低匹配、位置控制及同样的低负担继续阅读问题。

## 复现计划

受版本控制的实现将在被忽略的 `feature_runs/` 下输出 token 与附着审查、候选测量、各门槛流失、来源／锚点构成、解析器身份、输入 hash 和摘要。解释结果前，两次独立 `gx10` 运行必须逐字节一致。

## 结果

版本 0.2 在 `gx10` 运行两次，产物逐字节一致。从请求的 160 篇文章中的 133 篇解析了 1,393 个完整段落，得到 5,670 句、9,100 个实词 token 类型和 160,747 个有序词对类型。未请求或打开 30 篇 validation reserve。

87 个冻结候选中，34 个只含预定实词 POS，可评分；另 53 个因目标序列含非实词 token 而弃判。致命对齐失败为零。这是运行前固定的机械排除。

读者示例通过单例门槛：

- 目标 token：`AI / 原生 / 时代 / 全新 / 算力 / 服务 / 需求`；
- 归一化树熵 0.822，高于经验中位数 0.636；
- 最优与次优差 0.000，等于经验中位数 0.000；
- 跨语料熟悉 token 比例 0.857；
- 弱最佳树附着四个；
- 在 34 个可评分候选中的熵百分位 0.765。

这成功定位了一个已观察案例，不是通用筛选器的独立证据。最佳树后验概率仅 0.065，四个附着至多获一篇其他文档及一个来源支撑。

独立候选门槛失败：

| 门槛组件 | 实例数 | 文档数 |
|---|---:|---:|
| 熵达到或超过 P80 | 7 | 6 |
| 路径差不高于 P20 | 26 | 16 |
| 熟悉 token 比例至少 0.80 | 17 | 13 |
| 至少两个弱附着 | 27 | 17 |
| 熵与路径差联合 | 5 | 5 |
| 熵、路径差和熟悉度联合 | 0 | 0 |


五个高熵、零路径差实例是不熟悉的名称或技术字符串，包括以 `Multi Animate`、`蚂蚁数科首期开源实时`、`韩国 KG 集团旗下咖啡`、`Union Jack 格子
Bose-Hubbard`、`Nine Data 增量复制任务` 开头的来源短语。熟悉词候选没有相同高熵／低差模式。这与 H-TERM 或关联语料稀疏相容，没有产生多来源 H-BRACKET 集合。

因此 `modifier-bracketing-probe-0.2` 阶段 0 失败。H-BRACKET 仅保留为读者示例的局部候选解释，否决当前树熵向量作为干预筛选器。H-SEMANTIC（熟悉词之间隐含关系未说明）现在是更强的开发方向，但比较不能确立它为真。

不创建 Project 8，不放宽熟悉度规则、不降低熵门槛，也不人工从结果中删除名称。新的熟悉词弱关系测试必须冻结测量并使用独立语料，不重新挑选这 87 个候选。

## 复现身份

复制到 `gx10` 的受版本控制脚本 SHA-256 为 `3c7c0ce5c5effc2ff4b5b3a7c4fe149d5964e44e6cd11816246ce4d155c5b331`。两次独立运行产生：

| 产物 | SHA-256 |
|---|---|
| 摘要 | `80f09a3d7827f658c93abd9c38387b49bb309e846d727f0155043138d981bce1` |
| 候选测量 | `5bcfc6475cf17697ebcd4c6d04603b738be26b31c6e6f0878aa787faeaa47e35` |
| 机械弃判 | `8334f8bb7a21c77bffc011264599a7a6cd1ae71918bbda58ce067696ed95aeff` |
| 空的选中候选文件 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |


~~~bash
PYTHONPATH=/home/hooyao/DeAIodorant-post-v2/src:/home/hooyao/deaiodorant-modifier-bracketing-v1/run \
  /home/hooyao/DeAIodorant-post-v2/.venv/bin/python \
  modifier_bracketing_probe_v02.py \
  --candidates /home/hooyao/deaiodorant-nominal-chain-v1/output-v2/candidates.jsonl \
  --handoff /home/hooyao/deaiodorant-nominal-chain-v1/data/post_reader_handoff_v2 development \
  --handoff /home/hooyao/deaiodorant-nominal-chain-v1/data/post_reader_handoff_v3 discovery_reserve \
  --model-dir /home/hooyao/deaiodorant-nominal-chain-v1/models/stanza \
  --output-dir /home/hooyao/deaiodorant-modifier-bracketing-v1/output-v2a \
  --device cuda \
  --seed 2026083102
~~~
