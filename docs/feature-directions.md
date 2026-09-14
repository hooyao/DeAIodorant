# 特征探索方向

当前交付物是可复现的特征矩阵，不是分类器或统计结论。本文区分已实现的稠密特征，以及准备好的语料可用后值得继续提取的特征空间。

## 方向 A：可解释的稠密特征

状态：已在 feature schema 1.0 中实现。

首先生成这一矩阵，因为每一列都有稳定的语言学解释：

- 字符构成与 entropy；
- 段落和句子节奏；
- 标点；
- 重复与压缩；
- 标题形式；
- 篇章与认识情态标记；
- token 多样性与功能词使用；
- Universal POS 分布；
- 依存树深度、距离、分支、方向及 non-projectivity；
- 分句、并列、修饰和被动结构；
- 相邻句子的词汇衔接。

这些特征足够精简，可以逐列检查。

## 方向 B：稀疏 stylometry 模式

状态：已在 feature schema 1.0 中实现；实际词表在语料可用后选择。

为以下模式提取计数矩阵与归一化频率矩阵：

- CJK 字符 2-gram 至 5-gram；
- 功能词 1-gram 至 3-gram；
- POS 2-gram 至 5-gram；
- 标点序列；
- 句首与段首字符序列；
- 由中心词 POS、关系及依存词 POS 构成的 dependency treelet；
- 两条边的依存关系路径。

这些特征可以发现手工清单遗漏的公式化模式。它们必须与主题性较强的实词 n-gram 分开。词表裁剪使用合并语料的 document frequency，不读取时间组标签。选定词表与每个原始模式保存在单独目录中，必须在 held-out 比较之前冻结。

## 方向 C：Constituency grammar

状态：规划中。

固定的中文 constituency parser 可以提供：

- 短语结构树深度；
- 平均与最大分支数；
- 每句 NP、VP、IP、CP 和从属分句数量；
- 名词短语与动词短语比值；
- unary-chain 比率；
- grammar-production entropy；
- 常见 context-free grammar production 的归一化计数；
- 重复的 constituency 子树签名。

这一方向补充 Universal Dependencies。它会引入另一个 parser 模型及模型特有的标签集，因此输出必须具有独立 manifest 和敏感性分析。

## 方向 D：不依赖 embedding 的局部衔接

状态：部分实现。

稠密矩阵已经包含相邻句子实词和名词的 Jaccard overlap。后续确定性特征可以包括：

- 名词与命名实体在相邻句子间的延续；
- 代词与先行词距离的近似；
- 词汇链长度；
- entity-grid 转移计数；
- 相邻段落的实词重叠；
- 篇章边界是否出现连接词。

NER 或 coreference 模型会引入测量误差。第一步应使用固定的、基于 POS 的名词链，再考虑增加另一个学习模型。

## 方向 E：信息集中程度

状态：部分实现。

当前特征包括字符 entropy、token entropy、MATTR、hapax ratio 和 compression ratio。依赖语料的补充特征可以包括：

- 每篇文档内的 TF-IDF 集中程度与 Gini coefficient；
- 最高频的十个实词占全部 token 的比例；
- 文档内部关键词的 burstiness；
- 按段落计算的实词 entropy；
- 标题、首段和结尾之间的词汇重叠。

IDF 值必须在合并的探索语料上拟合一次，并作为产物保存，否则同一文档在不同运行中可能获得不同数值。

## 方向 F：主题与体裁诊断

状态：计划作为对照 metadata，不作为风格特征。

经典 LDA 或 non-negative matrix factorization 可以量化主题混合。得到的成分用于诊断或控制主题不均衡，不能作为 AI 写作证据。所需输出包括：

- 每篇文档的主题混合比例；
- 主题 entropy；
- 主导主题占比；
- 来源、体裁和主题交叉表。

vectorizer 词表、随机 seed、成分数和拟合后的模型必须冻结并记录 hash。

## 方向 G：时间特征

状态：推迟到月度覆盖充分之后。

得到文档特征后，按发布月份和来源聚合每个特征。有用的量包括：

- 月度中位数与 interquartile range；
- 同一来源的逐月变化；
- robust trend slope；
- 经典 change-point 候选；
- 跨来源的方向一致性。

这些是派生的时间序列特征，不属于第一版文档矩阵。

## 方向 H：可读性公式

状态：有意推迟。

许多中文可读性公式依赖学校年级词表、分句惯例或面向教育文本设计的特征。只有记录清楚词汇资源、许可证、领域适用性和精确公式后，才应引入。与当前的句子、token 和句法测量相比，单一且不透明的可读性分数会隐藏更多信息。

## 排除的方向

当前项目排除：

- LLM 判断或 LLM 生成的标签；
- 商业 AI detector 分数；
- 不透明的 text embedding；
- 将生成模型 perplexity 作为主要特征；
- 依赖 prompt 的语义或风格评分。

这些方法不符合特征值应低成本、可检查、可重复的要求。
