# 边界竞争开发实验

## 状态

协议 `boundary-competition-development-1.0` 已于 2026-08-31 冻结，
冻结发生在实现新的词汇测量、选择段落、准备修订或收集任何新的读者结果之前。
任何操作变更都必须在结果披露前获得新的协议版本。

这是一项分阶段的单读者开发实验，不是验证研究、作者身份研究，也不是前后队列比较。
在下述测量和准入门槛通过之前，不得创建任何 Label Studio 项目。

## 研究问题

读者定位到了一种结构：多个修饰语出现在较晚出现的中心名词之前，内部又没有可靠的边界，
因此即使词语熟悉，仍然难以整合理解。工作示例如下：

> 这个 AI 算力池面向 AI 原生时代全新算力服务需求

本实验提出两个相互独立的问题：

1. 冻结后的词汇边界竞争测量，能否区分两类中心词前长字符串：
   一类可通过结构拆解改善，另一类表面相似，但具有较强的词汇边界？
2. 对于高竞争字符串，仅调整边界的拆解编辑能否在保留原文每一项主张的同时，
   提高读者继续阅读的意愿？

本实验不检验文本是否由 AI 撰写，也不检验删除或语义替换 `AI 原生时代` 等表达的效果。
语义具体性假设仍是一个独立问题。仅调整边界的编辑可能失败，因为保留下来的表达仍然信息量很低；
这样的结果具有信息价值，而不是在看到结果后扩大编辑范围的理由。

## 基于文献的测量界限

该测量依据以下五项研究发现，但不将其中任何一项视为该产品问题迹象的直接证据：

- 正确的视觉词边界可以促进中文阅读，而误导性的边界可能干扰阅读（Bai 等，2008，
  <https://doi.org/10.1037/0096-1523.34.5.1277>）；
- 在中文词语识别过程中，相互重叠的候选词会发生竞争（Ma 等，
  2014，<https://doi.org/10.1037/a0035389>）；
- 读者会利用统计证据，判断一个字是单字词，还是多字词的起始字（Zang 等，2015，
  <https://doi.org/10.1080/17470218.2015.1061030>）；
- 邻接种类数（accessor variety）和分支熵提供确定性的边界证据（Feng 等，2004，<https://doi.org/10.1162/089120104773633394>；
  Jin 和 Tanaka-Ishii，2006，<https://doi.org/10.3115/1273073.1273129>）；
- 分词标准存在分歧，而且可能改变下游的依存结构，因此分词器之间的一致性只能用于诊断，不能视为真值
  （RethinkCWS，<https://doi.org/10.18653/v1/2020.emnlp-main.457>）。

SUBTLEX-CH 的词频和语境多样性数据用于校准词汇格
（<https://doi.org/10.1371/journal.pone.0010729>）。每项外部资源都必须记录版本并计算哈希值。
构建测量时，不得纳入任何项目结果、读者的可选评论或模型判断。

外部参考分布来自与 <https://doi.org/10.3758/s13428-021-01730-2> 关联的北京句子语料库（Beijing Sentence Corpus）。
只能使用合法可获得的句子文本和已发表的可预测性字段。如果无法获得该语料库或其适用许可证，
则阶段 0 停止，并且必须先更新协议版本，才能替换为其他参考语料库。

## 阶段 0：测量与准入

### 结构定位

新的测量以 `nominal-chain-integration-probe-0.2` 中已冻结的宽泛结构门槛为起点：

- 中心词前至少有五个词汇 token；
- 中心词前至少有 10 个可见字符；
- 至少有三个 `acl`、`amod`、`compound` 或 `nmod` 关系；
- 没有显式内部边界、标点边界或中心词前动词；
- 是一个完整的散文段落，包含 120-360 个 CJK 字符，且至少有两个
  句末标记。

结构门槛仅用于定位片段。此前的 87 个候选项并不属于同一种一致的结构，
因此通过该门槛并不意味着读者会遇到阅读阻力。

### 词汇边界向量

`boundary_competition_v1` 必须提供一个向量，而不是不透明的分数：

- 所有词典支持的分词路径上的归一化熵；
- 最优路径与次优路径之间的对数概率差；
- 每个字间间隙的边界后验概率；
- 后验概率位于 `[0.25, 0.75]` 内的歧义间隙数量；
- 最后一个后验概率至少为 `0.80` 的边界
  到中心名词的距离；
- 单字词概率和多字词起始概率；
- 左分支熵和右分支熵；
- 左邻接种类数和右邻接种类数；
- 词汇覆盖率和弃判原因；
- 将专名、数字、ASCII 技术术语和带引号名称的锚点
  作为独立变量。

词汇覆盖率低会导致弃判，不得将其转化为高竞争。专名、数字和技术术语记录为锚点，
不得按规则删除。Stanza 与词典分词之间的分歧仅保留用于诊断。

版本 1.0 的词汇格使用最多八个字符、仅含 CJK 字符的子串。
已知边获得一元权重
`(SUBTLEX WCount + 0.1) / (retained WCount total + 0.1 * vocabulary size)`。
当不存在已知的单字边时，回退权重为该字的 SUBTLEX
字符概率乘以 `0.01`。通过精确的前向—后向求和
计算路径熵和间隙后验概率；通过保留最优两条路径的动态规划计算
路径概率差。熵和概率差均除以参与评分的 CJK 长度。连续 ASCII
字符序列计为锚点，不纳入 CJK 词汇格。已知字符覆盖率
低于 0.80 时弃判，而不是给出高竞争结果。

必须在不使用短语专属词典条目或黑名单的情况下，对工作示例进行定位和评分。
若无法定位该示例，实验停止。

### 外部校准

所有百分位截点均在对后时期候选池排序之前，从北京句子语料库中长度匹配的 CJK 窗口计算得出。
熵按参与评分的字符数归一化，连续 ASCII 字符序列视为单个锚点；
若在中心词前片段长度上下两个评分字符的范围内，外部窗口少于 100 个，
则该候选项弃判。校准集、资源版本、归一化方式、平滑方法、未知 token
惩罚、窗口数量和 SHA-256 标识必须写入运行清单。
随后按如下标准固定高、低竞争分层：

- **高竞争：**路径熵达到或超过外部分布的第 90 百分位，
  最优与次优路径的概率差不高于外部分布的第 10 百分位，至少
  有两个歧义间隙，且到中心词的未消歧距离至少为六个
  字符；
- **低竞争：**路径熵不高于外部分布的中位数，
  最优与次优路径的概率差达到或超过外部分布的中位数，至多
  有一个歧义间隙，且到中心词的未消歧距离至多为三个
  字符。

在版本 1.0 中，分支熵、邻接种类数、分词器分歧和锚点数量
不决定准入。记录这些指标是为了诊断，以及供未来独立版本化的模型使用。

### 语料分离

候选段落只能来自在 2025-07-01 当日或之后发表、
且已在发现或开发阶段暴露的后时期文档。
`post_reader_handoff_v2` 中包含 30 篇文档的验证保留集仍保持未打开状态。
此前读者评分、筛选或干预中使用过的所有文档，都必须在排序前排除。

读者实验要求：

- 八个高竞争段落和八个匹配的低竞争段落；
- 16 篇不同文档，每篇文档仅取一个段落和一个目标片段；
- 至少三个来源，且任一分层中来自同一来源的文档不超过三篇；
- 每个分层至少包含两种编辑形式；
- 与之前的读者任务不存在来源正文重叠或 CJK 二元组重叠；
- 段落完整、可独立理解，并符合已冻结的散文门槛。

每个高竞争项按来源、编辑形式、目标片段长度、段落长度、锚点特征，以及可获得的发表月份，
与一个低竞争项匹配。来源、形式，以及专名、数字和 ASCII
锚点这三个二元指标必须完全匹配。目标片段的 CJK 长度最多可相差
两个字符；段落和目标句的 CJK 长度比都必须在
`[0.80, 1.25]` 范围内。

固定距离为 `0.35 * 片段长度差 / 2 + 0.35 * 归一化的
段落对数比绝对值 + 0.20 * 归一化的句子对数比绝对值 + 0.10 *
发表月份距离 / 24`，其中最后一项上限为一，对数比
按 `log(1.25)` 归一化。匹配器考虑每篇文档中最极端的
合格候选项，按距离对所有有效边排序，距离完全相同时按 `SHA-256(seed | high candidate | low candidate)`
打破平局，并以贪心方式接受跨文档边，不放回。任何来源均不得提供
超过三对。最终八对必须覆盖至少三个来源和
两种形式。如果无法获得八个有效匹配区组，实验停止，不得放宽阈值，也不得创建读者项目。

## 阶段 1：仅调整边界的干预

操作算子为 `unpack_boundary_competition`。它可以：

- 将中心名词前移；
- 将现有的修饰语—中心词关系转化为显式的主谓
  或话题—述题关系；
- 仅添加揭示该关系所必需的语法功能词、有明确先行词的代词或
  标点；
- 将一句拆成两句，同时保留显式论元和
  跨句指代；
- 重新排列现有修饰成分，使词汇锚点紧邻其
  中心词。

它不得：

- delete, generalize, or strengthen any proposition;
- add a premise, explanation, definition, causal claim, or concrete detail;
- replace or silently define an abstract expression;
- remove named entities, technical terms, quantities, negation, attribution,
  modality, qualification, or uncertainty;
- flatten rhythm and authorial voice into a compressed instruction-manual
  style;
- alter any non-target sentence except the immediately required antecedent.

Every revision must preserve all source content words unless an exact
coreference substitution is logged. It must retain at least 70% character
similarity and may increase CJK length by no more than 25%. These are safety
bounds, not optimization targets.

The editor receives the 16 items in a seeded order without the high/low label,
rank, reader history, or future display side. Every edit records the exact
before and after span, moved material, inserted function words, explicit
relation, linked proposition IDs, locked literals, entity checks, numeric
sequence, negation, modality, attribution, uncertainty, voice anchors, and a
unified diff. A passage with an unresolved preservation question is rejected
before task generation; no replacement is selected after reader outcomes.

## Experimental design

The paragraph is the intervention unit and the source document is the
replication unit. The reader sees both versions of the same paragraph, so each
paragraph is its own block. High/low matched blocks control source, format, and
length variation. Repeated answers from one reader do not create independent
reader replication.

The frozen layout contains:

- eight high-competition intervention pairs;
- eight low-competition intervention pairs receiving the same operator;
- one identical-text diagnostic;
- one mirrored repeat of a randomly selected high-competition pair;
- two session blocks of nine tasks, with a break requested between blocks.

Within each stratum, four originals appear on side A and four on side B. Each
session contains four high and four low items plus one diagnostic. The mirrored
repeat reverses its first display side and occurs at least eight tasks later.
Task order and side placement use seed `2026083101`. Candidate identities are
assigned to the placeholder schedule by a separately recorded seeded mapping
only after the eligible matched set is frozen.

The reader is blind to original/revised status, competition stratum, score,
operator, source identity, and control role. The editor must not see outcomes.

## Reader instrument

The only required question is:

> Which version makes you more willing to continue reading?

The choices are version A, version B, or no meaningful difference/both bad.
An optional comment remains available but cannot change eligibility, decoding,
or a decision gate. The task does not ask for linguistic classification,
authorship judgment, or a reason for the choice.

## Outcomes and analysis

Decode each independent intervention unit as:

- `+1`: revised version preferred;
- `0`: no meaningful difference or both bad;
- `-1`: original version preferred.

Let `S_high` and `S_low` be the sums across the eight independent units in each
stratum. The primary development quantities are:

- high-stratum net preference: `S_high / 8`;
- low-stratum net preference: `S_low / 8`;
- selector contrast: `(S_high - S_low) / 8`;
- revised share among decisive answers in each stratum;
- tie rate and display-side choice distribution.

No confirmatory p-value is attached to the primary development gate. Exact
binomial intervals may be reported descriptively for decisive preferences, but
the reader is a fixed development reader and cannot support population-level
reader inference.

## Frozen decision gates

Interpretation proceeds in this order:

1. **Instrument gate:** the identical pair must receive the no-difference
   answer; the mirrored repeat must preserve the content preference or produce
   no difference both times; and the exact two-sided binomial test of display
   side among decisive intervention answers must not reject a 0.5 side share at
   `alpha=0.05`. Failure makes the intervention outcome uninterpretable.
2. **Preservation gate:** every independent revision must retain all locked
   propositions, entities, quantities, negation, modality, attribution,
   uncertainty, and voice anchors. Any detected failure blocks operator
   promotion even when preference is positive.
3. **Manipulation gate:** every high-stratum revision must shorten unresolved
   distance to the head and lower path entropy without lowering lexical
   coverage. Failure rejects the implementation of the operator.
4. **High-stratum benefit gate:** at least six high items must be decisive; the
   revised share among them must be at least 0.75; and `S_high / 8` must be at
   least 0.50.
5. **Selector-specificity gate:** `(S_high - S_low) / 8` must be at least 0.50.

If gates 1-5 pass, the selector and operator advance to a separately powered,
multi-reader validation design. If the high and low strata both meet the
benefit gate but the selector contrast fails, only the operator remains a
candidate and `boundary_competition_v1` is rejected as a selector. If
`S_high <= 0`, the current operator is rejected. Any other outcome is
inconclusive; more independent examples may be acquired under the frozen
measurement, but thresholds and edits must not be tuned against these outcomes.

## Sample-size boundary

Sixteen independent passages are a development screen, not a powered
validation study. For an optimistic exact two-sided binomial test against a
0.5 decisive preference rate at `alpha=0.05` and 80% power, the minimum
decisive-pair counts are:

| True revised preference | Decisive pairs | Tasks with 20% ties |
|---:|---:|---:|
| 0.65 | 90 | 113 |
| 0.70 | 49 | 62 |
| 0.75 | 30 | 38 |
| 0.80 | 20 | 25 |

The 0.70 row is the smallest practically interesting effect for a targeted
editing rule, but 49 comparisons from one reader would still not replicate the
reader. A later confirmatory design must cross multiple independent readers
with held-out passages and determine reader and item counts by simulation under
the planned mixed-effects model. The development effect estimate must be
shrunk rather than copied directly into that power calculation.

## Reproduction

Generate the placeholder allocation and exact-binomial sensitivity table with:

~~~powershell
python experiments/design_boundary_competition_experiment.py `
  --output-dir feature_runs/boundary-competition-design-v1 `
  --seed 2026083101
~~~

The generated files contain no corpus text and remain under ignored
`feature_runs/`. The actual task generator must validate the frozen allocation,
corpus-separation, matching, preservation, and manipulation gates before it can
emit Label Studio tasks.

## Immediate stop/go decision

The next action is to implement and externally calibrate
`boundary_competition_v1`. Do not inspect the 30-document validation reserve,
write passage-specific lexical exceptions, prepare revisions, or open Project 8
until Stage 0 produces eight valid high/low matched blocks under this protocol.

## Stage 0 result

Stage 0 was run on 2026-08-31 without changing the frozen thresholds. The
external calibration used 150 sentences from the public Beijing Sentence
Corpus OSF workbook and the public SUBTLEX-CH word and character tables. The
Beijing workbook has SHA-256
`5c96e829a3de8203739893eef6b54e6ebddf055976919d9b29b2797053d81876`.
Its OSF and DataCite metadata do not specify a license, so the file remains an
untracked local research input and is not redistributed. The SUBTLEX word and
character table hashes are
`086536450b1f77d0c7ff3ac0fc8375897162ace807d3167bec48b4c493434077`
and
`03ffacc65c4d14530338c1bffb72b2e98d06ee23bed14546dc8001ab4bcbb415`;
their Figshare record specifies CC BY 4.0.

All 87 previously frozen structural candidates were scored. None came from a
previous reader document, and the 30-document validation reserve was absent
from the candidate input and remained unopened. The result was:

| Boundary stratum | Instances | Documents |
|---|---:|---:|
| High competition | 0 | 0 |
| Low competition | 36 | 23 |
| Middle or unscored | 51 | 28 |

Seven candidates in seven documents independently passed both the high-entropy
and low-margin percentile gates. Only one candidate had at least two ambiguous
gaps, no candidate had unresolved distance of at least six characters, and the
maximum observed unresolved distance was four. The high candidates therefore
number zero, no high/low matching edge exists, and Stage 0 fails before editing.

The reader-localized example was fully scorable but did not resemble lexical
segmentation competition. Its entropy percentile was 0.669, margin percentile
was 0.346, ambiguous-gap count was zero, and unresolved distance was two. The
best SUBTLEX path was `原生 / 时代 / 全新 / 算 / 力 / 服务`. This also exposes a
domain-age limitation: the subtitle lexicon does not treat the modern technical
term `算力` as one word. Adding it after seeing the result would be prohibited
phrase-specific tuning and would not address the larger result.

Reject `boundary_competition_v1` as an intervention selector. The reader's
description is better interpreted as competition among word-level modifier
attachments or phrase bracketings than as uncertainty about character-to-word
segmentation. Do not prepare revisions, assign the frozen allocation, or create
Project 8 from this run. A word-level bracketing hypothesis requires its own
pre-outcome literature review, measurement protocol, and independent gate.

Two independent runs produced byte-identical artifacts:

| Artifact | SHA-256 |
|---|---|
| Summary | `0d8babb378cce2789ebf2a47717b6242549ef34de86a68f6fe4241e6497dfc9b` |
| Candidate measurements | `77926cc1f71a60c7959c488b98863af43b0b7bcdfd42d47e7aa95fc2982cabe5` |
| Candidate table | `60a42c4ca6541ba2f0f1cd4cad8d9556b94dd89501904aacbc2b9566c885c5f5` |
| Empty matched-pair file | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

~~~powershell
python experiments/boundary_competition_probe.py `
  --candidates feature_runs/nominal-chain-integration-v1/candidates.jsonl `
  --nominal-summary feature_runs/nominal-chain-integration-v1/summary.json `
  --subtlex-word-file feature_runs/boundary-competition-resources-v1/subtlex_ch/SUBTLEX-CH-WF `
  --subtlex-character-file feature_runs/boundary-competition-resources-v1/subtlex_ch/SUBTLEX-CH-CHR `
  --bsc-workbook feature_runs/boundary-competition-resources-v1/BSC.Word.Info.v2.xlsx `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v2 `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v3 `
  --annotation-dir data/annotations `
  --output-dir feature_runs/boundary-competition-probe-v1
~~~
