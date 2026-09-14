# 可量化的中文文本特征目录

## 范围

当前任务是特征提取。输入已准备好的 2023 年前语料和 2025 年 6 月之后语料，流程为每篇文档输出一行数值。它不选择语料文档、不检验统计显著性、不训练分类器、不检测 AI 作者身份，也不解释差异。

所有特征都是确定性的，使用直接文本统计或固定的 Stanza Universal Dependencies 解析。不使用 LLM、embedding 模型、prompt 或生成式判断。

## 输出单位

以文档为特征单位。每行首先包含以下非特征标识列：

| 列 | 含义 |
|---|---|
| doc_id | 稳定的语料文档 ID |
| cohort | 根据日期划分的 pre 或 post 组 |
| source | 发布来源 |
| published_at | ISO 发布日期 |
| published_month | 日历月份 |
| topic | 已准备语料的主题标签，或缺失值标记 |
| format | 已准备语料的体裁标签，或缺失值标记 |

其余列均为数值特征。原始正文与标题不复制到矩阵中。

## 共同定义

- **CJK character**：Unicode 范围 U+3400–U+4DBF 或 U+4E00–U+9FFF 内的字符。
- **Ratio**：分子除以明确指定的分母。
- **Density**：出现次数除以非空白字符数，除非特征名称指定了其他分母。
- **Entropy**：以 bit 为单位的 Shannon entropy，即 **p(x) * log2(p(x))** 之和的负值。
- **Coefficient of variation (CV)**：总体标准差除以算术平均值。平均值为零时，CV 为零。
- **MATTR**：所有重叠固定窗口的平均 type-token ratio。文档短于配置窗口时，使用普通 type-token ratio。

## 字符构成

| 特征组 | 测量量 |
|---|---|
| 长度 | 总字符数、非空白字符数、CJK 字符数 |
| 文字构成 | CJK 占比、ASCII 字母占比、数字占比 |
| 字符多样性 | CJK entropy、CJK type-token ratio、500 字符 MATTR |
| 可压缩性 | zlib level-9 压缩后的字节数除以原始 UTF-8 字节数 |
| 外部引用 | 每 1,000 个 CJK 字符中检测到的 URL 数 |

原始长度计数可用于匹配和诊断。在完成组间篇幅匹配前，不应把长度差异当作风格差异。

## 文档结构与节奏

段落定义为规范化后的非空行。句子在中文或 ASCII 句号、问号和感叹号之后切分。

| 特征 | 公式 |
|---|---|
| 平均段落长度 | 每段 CJK 字符数的均值 |
| 段落长度 CV | 段落 CJK 字符数的 CV |
| 短段落比例 | 含 1–19 个 CJK 字符的段落数除以段落数 |
| 长段落比例 | 含超过 200 个 CJK 字符的段落数除以段落数 |
| 平均句长 | 每句 CJK 字符数的均值 |
| 句长 CV | 句子 CJK 字符数的 CV |
| 句长 autocorrelation | 相邻句长序列的 Pearson correlation |
| 相邻句长变化 | 相邻句长绝对变化的均值除以平均句长 |
| 每段平均句数 | 各段中检测到的句子数的均值 |
| 列表项比例 | 以 bullet 或序号标记开头的段落数除以段落数 |
| 疑问句比例 | 以问号结尾的句子数除以句子数 |
| 感叹句比例 | 以感叹号结尾的句子数除以句子数 |

这些特征量化结构的一致程度，不赋予正面或负面解释。

## 重复与规律性

| 特征 | 公式 |
|---|---|
| 重复字符 n-gram 比例 | 全部已配置 CJK n-gram 中重复出现的比例 |
| 句首重复 | 开头四个 CJK 字符序列的重复数除以符合条件的句子数 |
| 段首重复 | 开头四个 CJK 字符序列的重复数除以符合条件的段落数 |
| 完全相同句子重复 | 空白规范化后重复的句子数除以句子数 |
| 完全相同段落重复 | 空白规范化后重复的段落数除以段落数 |
| Compression ratio | 确定性压缩大小除以来源字节大小 |

字符 n-gram 大小保存在特征配置中。重复特征对 boilerplate、引用和文档体裁敏感。

## 标点

矩阵包含总标点 density、标点 entropy，以及以下各类标点的独立 density：

- 逗号和顿号；
- 句号、问号和感叹号；
- 冒号；
- 分号；
- 破折号和连字符；
- 引号；
- 圆括号和方括号。

标点风格受来源和编辑者影响，因此保留来源标识列，供后续分层使用。

## 标题形式

标题特征包括：

- CJK 字符数；
- ASCII 字母占比；
- 是否包含数字、冒号、问号、感叹号或引号；
- 标题中不同 CJK 字符也出现在正文中的比例。

从 metadata 读取原始标题，但不将其写入特征矩阵。

## 篇章与认识情态标记

固定短语表按每 10,000 个 CJK 字符量化以下频率：

- 因果过渡；
- 对比过渡；
- 列举；
- 框架引导短语；
- metadiscourse；
- 总结短语；
- epistemic boosters；
- epistemic hedges；
- 指令性表达。

矩阵还记录篇章标记总频率和标记类型覆盖率。精确中文短语在 **src/deaiodorant/analysis/surface.py** 中进行版本管理。这些是词表测量，不是语义判断，受主题和体裁影响。

## Token 与词汇特征

Stanza 的分词、lemmatization 和 Universal POS 标签提供：

| 特征 | 公式 |
|---|---|
| 词汇 token 数 | 排除 PUNCT 和 SYM 的 token 数 |
| Token type-token ratio | 不同 case-folded token 形式数除以词汇 token 数 |
| Token MATTR | 100-token 窗口的平均 type-token ratio |
| Hapax ratio | 仅出现一次的 token 类型数除以词汇 token 数 |
| Token entropy | 词汇 token 形式的 Shannon entropy |
| 平均 token 长度 | 每个词汇 token 中 CJK 字符数的均值 |
| Token 长度 CV | 词汇 token 的 CJK 长度 CV |
| 实词比例 | ADJ、ADV、NOUN、PROPN 和 VERB token 数除以词汇 token 数 |
| 功能词比例 | ADP、AUX、CCONJ、DET、PART、PRON 和 SCONJ token 数除以词汇 token 数 |
| 第一人称代词比例 | 固定词表中第一人称形式的出现次数除以词汇 token 数 |
| 第二人称代词比例 | 固定词表中第二人称形式的出现次数除以词汇 token 数 |

Token 特征依赖 parser 和分词，两组必须使用完全相同的模型文件。

## 局部词汇衔接

对于每一对已解析的相邻句子，提取器计算以下词集的 Jaccard overlap：

- 标签为 ADJ、ADV、NOUN、PROPN 或 VERB 的 lemmatized 实词；
- 标签为 NOUN 或 PROPN 的 lemmatized 名词。

文档特征是相邻句子重叠程度的均值。这是透明的局部衔接近似，不需要 embedding 或 coreference 模型。

## Universal POS 分布

矩阵对每个 Universal POS 标签都包含：

**该标签的 token 数 / 全部已解析 token 数**

标签为 ADJ、ADP、ADV、AUX、CCONJ、DET、INTJ、NOUN、NUM、PART、PRON、PROPN、PUNCT、SCONJ、SYM、VERB 和 X。

POS bigram 和 trigram entropy 测量局部语法序列的多样性，但不保留序列本身。

## 依存树复杂度

| 特征 | 公式 |
|---|---|
| Dependency distance | 依存词与中心词之间 token 位置差的绝对值 |
| 平均、中位数及最大 dependency distance | 对文档非 root 弧进行聚合 |
| Dependency-distance CV | 非 root 依存距离的 CV |
| 左侧依存词比例 | 位于中心词左侧的依存词数除以非 root 弧数 |
| 平均及最大树深度 | root 到 token 的边数 |
| 平均及最大非叶节点分支数 | 至少有一个子节点的 token 的子节点数 |
| Root 相对位置 | root token 索引除以句子 token 数，再按文档取均值 |
| 交叉弧比例 | 交叉弧对数除以全部非 root 弧对数，再按句子取平均 |
| 依存关系 entropy | 基础 Universal Dependencies 关系的 entropy |
| Treelet entropy | 中心词 POS、关系、依存词 POS 三元组的 entropy |

## 分句与修饰结构

| 特征 | 公式 |
|---|---|
| 从属关系比例 | acl、advcl、ccomp、csubj 和 xcomp 弧数除以 token 数 |
| 每句分句关系数 | 上述关系数除以已解析句子数 |
| 并列关系比例 | cc 和 conj 弧数除以 token 数 |
| 名词修饰关系比例 | acl、amod、compound 和 nmod 弧数除以 token 数 |
| 被动关系比例 | 依存关系子类型包含 pass 的弧数除以 token 数 |

矩阵还包含每种基础 Universal Dependencies 关系的比例，以便保留细节供后续探索，无需重新解析。

## 稀疏 stylometry 特征

除了 150 列的稠密矩阵，schema 1.0 还可以为以下模式输出稀疏特征：

- CJK 字符 2-gram、3-gram 和 4-gram；
- POS 2-gram、3-gram 和 4-gram；
- 功能词形式；
- 实词 lemma，明确标记为对主题敏感；
- 句首 CJK 序列；
- 连续标点序列；
- root POS 值；
- 由中心词 POS、关系和依存词 POS 构成的 dependency treelet；
- 两条边的依存关系路径。

词表选择合并两组，仅使用合并后的 document frequency 和总计数，绝不读取时间组标签。每个选定模式分配确定性的 feature ID。非零值同时包含原始计数，以及该特征家族每 1,000 次机会的计数。

词表上限和最小 document frequency 保存在 **configs/features.v1.json** 中。稀疏特征属于探索性特征：没有主题控制时，不能将对主题敏感的家族解释为写作风格。

## Parser 与复现契约

句法层使用：

~~~text
Stanza 1.14.0
language: zh-hans
package: gsdsimp
processors: tokenize,pos,lemma,depparse
~~~

Stanza 是学习型 NLP parser，不是 LLM。在特征提取之前，将标注输出冻结为 CoNLL-U。标注 manifest 记录精确包版本、模型文件指纹、device、seed、语料指纹和每个 CoNLL-U 文件的 hash。

Stanza 使用 Apache-2.0 许可证。选定的 Universal Dependencies Chinese GSD treebank 使用 CC BY-SA 4.0。可选安装包含 PyTorch 和数百 MB 模型文件，体积显著大于核心包。为保证可复现性，默认使用 CPU 标注；处理大语料时可能较慢。

特征提取不会隐式下载模型。模型文件缺失、parser 输出不完整、依存树格式错误、语料指纹不匹配或标注 hash 改变时，命令停止，不会静默替换数据。

模型下载必须显式执行：

~~~powershell
python -m pip install -e ".[syntax]"
deaiodorant-analysis download-syntax-model --model-dir models/stanza
~~~

准备好的语料可用后，提取特征矩阵：

~~~powershell
deaiodorant-analysis annotate --corpus data/final/monthly --config configs/features.v1.json --model-dir models/stanza --output feature_runs/annotations-v1 --device cpu

deaiodorant-analysis extract --corpus data/final/monthly --config configs/features.v1.json --annotations feature_runs/annotations-v1 --output feature_runs/matrix-v1
~~~

输出目录包含：

~~~text
document_features.csv
feature_catalog.json
feature_config.json
summary.json
feature_manifest.json
sparse_feature_catalog.json
sparse_feature_values.csv
~~~

manifest 为每个产物记录 hash。绝不覆盖已有输出目录。

## 后续比较的约束

特征提取本身不能确立人类写作与 AI 时代写作的差异。后续比较至少必须：

- 按来源、主题、体裁、篇幅和传播可见度匹配或分层；
- 将文档而非句子作为独立观察；
- 区分原始计数和归一化频率；
- 报告 parser 敏感性及缺失 metadata；
- 将探索性特征选择与 held-out 确认分开。
