# 确定性篇章关系支撑探测

## 目的

实验检验显式中文篇章关系是否可建模为带类型的边，由局部命题独立支撑所宣称的关系。使用确定性 Stanza 依存、冻结词表和图式重叠，不使用 LLM judge、embedding 模型或作者分类器。

目标区分如下，公式中的边表示显式标记所宣称的关系，旁支表示排除标记本身的局部证据路径：

~~~text
命题 A --[显式标记所宣称的关系类型]--> 命题 B
                    |
                    +-- 排除标记本身的局部证据路径
~~~

探测允许返回 `indeterminate`，此类实例不计作无支撑。

## 表示 v0.1

提取器识别五类宣称关系：

- 对比；
- 原因；
- 推断；
- 澄清；
- 强调。

处理句首、句内标记，以及 `不是...而是...` 等完整成对对比框架。每个实例保存标记、左右论元 span、句子索引、类型化证据、决定及原因码。

冻结证据向量包含：

- 两侧是否存在命题；
- 实体、实词、谓词和依存角色重叠；
- 共享非泛化谓词上的否定翻转；
- 小型冻结反义词表；
- 显式比较词；
- 新具体实体、谓词、数字及其他信息；
- 仅含 abstract shell 的信息；
- 加权局部锚点分数。

五种决定为 `supported`、`redundant`、`type_mismatch`、`unsupported`、`indeterminate`。文档指标保留全部决定及弃判率。时间分组解释前，将次数归一到每 100 个解析句。

实现为 `src/deaiodorant/analysis/discourse_relations.py`，实验运行器为 `experiments/relation_support_probe.py`。

## 既有数据

只使用已有受版本控制材料：

- 前时期 InfoQ 10 篇、后时期 InfoQ 10 篇；
- 八个后时期阅读阻力段落；
- 10 个已完成第二轮原文／修订配对。

时间比较采用逐特征组内 Huber 位置、固定 seed 的 5,000 次标签置换、leave-one-document-out 方向检查及移除已知译文的敏感性分析。段落分析使用 exact Spearman permutations。改写比较为描述性，因为变体本来就是为改变这些标记而构造。

## 实例输出

跨文档、段落及改写范围共输出 476 个实例：

| 决定 | 次数 |
|---|---:|
| 无法确定 | 241 |
| 有支撑 | 147 |
| 类型不匹配 | 88 |
| 冗余 | 0 |
| 无支撑 | 0 |


没有 `unsupported` 或 `redundant` 结果，不能说明关系正确，只说明当前高精度规则未在这些材料上作出此类判断。

## 时间比较

| 特征 | 前时期均值 | 后时期均值 | 稳健后减前效应 | Permutation p | BH q | LOO 稳定性 |
|---|---:|---:|---:|---:|---:|---:|
| 每 100 句强调实例数 | 1.07 | 3.84 | 1.34 | 0.100 | 0.564 | 1.00 |
| 无法确定比例 | 0.60 | 0.41 | -1.13 | 0.032 | 0.564 | 1.00 |
| 平均信息增量 | 11.49 | 8.23 | -0.83 | 0.123 | 0.564 | 1.00 |
| 平均局部锚点分数 | 0.054 | 0.045 | -0.58 | 0.242 | 0.618 | 1.00 |
| 每 100 句全部关系实例数 | 15.48 | 14.64 | 0.28 | 0.806 | 0.968 | 0.85 |
| 每 100 句对比实例数 | 8.94 | 8.18 | 0.06 | 0.921 | 0.968 | 0.60 |
| 每 100 句问题判断数 | 2.05 | 2.20 | 0.04 | 0.912 | 0.968 | 0.65 |
| 问题判断比例 | 0.15 | 0.13 | -0.03 | 0.941 | 0.968 | 0.60 |


没有特征通过校正。归一化宽泛对比率及问题率未复现特定完整否定对比框架的更强结果。移除译文会反转关系密度、对比密度和问题密度原本极小的方向。

后时期更低的无法确定比例稳定，但不是质量信号。规则只是找到更多具体信息，因而在后时期文章中作出更多决定。

## 阅读阻力比较

| 特征 | 仅后时期 Spearman rho | Exact p | BH q | LOO 稳定性 |
|---|---:|---:|---:|---:|
| 每 100 句对比实例数 | 0.51 | 0.232 | 1.00 | 1.00 |
| 每 100 句全部关系实例数 | 0.46 | 0.304 | 1.00 | 1.00 |
| 平均信息增量 | 0.39 | 0.393 | 1.00 | 1.00 |
| 平均局部锚点分数 | -0.34 | 0.446 | 1.00 | 1.00 |
| 每 100 句强调实例数 | 0.17 | 0.786 | 1.00 | 0.88 |
| 每 100 句问题判断数 | 0.06 | 1.000 | 1.00 | 0.50 |
| 问题判断比例 | 0.00 | 1.000 | 1.00 | 0.00 |


宽泛对比和整体关系密度沿预期读者方向变化，但只有八段，也都没有与有用时间效应一致。拟议的问题决定与观察到的阅读阻力层级无关。

## 改写操作

| 特征 | 平均修订减原文差值 | 减少配对数 | 不变 | 增加 |
|---|---:|---:|---:|---:|
| 每 100 句全部关系实例数 | -21.96 | 9 | 1 | 0 |
| 每 100 句对比实例数 | -11.62 | 7 | 3 | 0 |
| 每 100 句强调实例数 | -10.49 | 8 | 2 | 0 |
| 每 100 句问题判断数 | -2.57 | 4 | 6 | 0 |
| 问题判断比例 | 0.014 | 2 | 7 | 1 |


大幅减少的次数确认第二轮算子改变了预期表层关系，不能验证带类型的支撑判断。问题比例并未跟随六次修订胜出。

## 定性审查

一个目标符合预期。原始多工具段落包含：

> 阿里云没有让 Agent 绕过既有工程体系，直接裸调 API。相反，它让 Agent 沿着成熟工具链进入云……

探测将 `相反` 标为 `type_mismatch`，原因为 `ELABORATION_EVIDENCE_WITHOUT_CONTRAST`，与读者可选评论一致。修订删去了该实例。

同一规则也产生清楚反例：

- 将 7:00 相连建筑与 7:31 变化后状态的时间对比判为不匹配；
- 将人工监控与 LLM 监控判为展开说明，而非备选方案；
- 仅因后面有具体信息，就把若干读者反感的 `真正` 框架判为有支撑。

这些是结构错误，不是阈值错误。词汇重叠和依存角色不能确立矛盾、备选选择、因果或修辞必要性。

## 决定

否决 `relation_support_problem_*` v0.1 作为臭味分数或阅读阻力指标。确定性实例提取、证据向量和原因码只保留作审查工具。

不得将特定完整对比框架结果泛化为所有连接词的广泛主张。强调密度仍是时间分组假设，不是读者支持的目标。真正的关系支撑需要更窄、可形式化检验的模式，或独立专家 span 标注。读者继续只提供低负担读者偏好，不作语言学分类。

## 复现

~~~powershell
deaiodorant-analysis download-syntax-model `
  --model-dir models/stanza `
  --language zh-hans `
  --package gsdsimp

deaiodorant-analysis annotate `
  --corpus data/pilot/monthly `
  --config configs/features.v1.json `
  --model-dir models/stanza `
  --output feature_runs/pilot-annotations-v1 `
  --device cpu

python experiments/prepare_smell_calibration.py `
  --corpus-root data/pilot/monthly `
  --output feature_runs/annotation-calibration-v1/tasks.json

python experiments/relation_support_probe.py `
  --corpus-root data/pilot/monthly `
  --config configs/features.v1.json `
  --annotations feature_runs/pilot-annotations-v1 `
  --reader-tasks feature_runs/annotation-calibration-v1/tasks.json `
  --reader-ratings data/annotations/reader-friction-v1.json `
  --refinement-answer-key feature_runs/refinement-pairs-v2/answer_key.json `
  --refinement-results data/annotations/refinement-pairwise-v2.json `
  --model-dir models/stanza `
  --output-dir feature_runs/relation-support-v1-2 `
  --device cpu `
  --permutations 5000 `
  --seed 20260822 `
  --tuning-constant 1.5
~~~

复现身份：

| 产物 | 指纹 |
|---|---|
| 语料 | d6cfb16560de7904ab5dc34a09e35e69642e7f39cb61d517a9bd1ffbc2a43014 |
| Stanza 模型文件 | 5fa23dfff06b543c63ef547b32006bb0a9acdd6bc1a3a1df23d768a171352af9 |
| 标注 manifest | fad4aa303d130cc6bbb3a22f1d602068f7dca6c8c625a5112f1daef4df510081 |
| 结果 | 95ce3dfbed147027b68c16b043af04b8e8e107d73f46a2587a68859f7663ee9b |


全部生成实例、标注及矩阵保留在被忽略的 `feature_runs/` 和 `models/` 目录下。
