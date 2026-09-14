# 确定性篇章图探测

## 目的

本实验检验：读者描述的中文“AI 臭味”，是否更适合表示为表层阅读成本与篇章结构的失配。它是探索性方向探测，不是分类器、作者身份检测器或已验证的质量分数。

## 表示

每段转为包含四类节点的异构图：

- 句子实例；
- 从依存谓词导出的命题实例；
- 具体实体及名词链提及；
- `体系`、`框架`、`能力`、`意义` 等抽象 shell 概念。

边记录：

- 句子包含命题；
- 句子提及实体；
- 命题到论元的依存角色；
- 相邻句的篇章衔接，包括实体、实词及谓词重叠；
- 显式因果、对比、澄清或列举标记。

实现使用 Stanza 1.14 中文 Universal Dependencies、固定规则及集合重叠，不使用 LLM 或 embedding 模型。

## 数学假设

工作假设为**表层与结构失配**：

> 阅读成本增加，但图中有依据的新命题很少，相邻命题联系较弱，反复返回同一局部主张，或向主线插入连接稀疏的绕行。

初始图特征包括：

- 每 100 CJK 字符的命题数；
- 每个唯一命题签名的 CJK 字符数；
- 命题复述比例；
- 相邻衔接平均权重；
- 零衔接比例及缺少支撑的显式边比例；
- 语义连通分量比例与孤立句比例；
- 最大连通句子分量覆盖率；
- 主线绕行比例；
- 抽象 shell 及无具体支撑的抽象 shell 比例；
- 无论元命题比例。

## 数据与分离策略

时间比较使用前时期 10 篇及后时期 10 篇 InfoQ 文档。每个分组内部单独应用逐特征 Huber 权重，不人工删除文档。后时期阅读分析只使用八个已评分后时期段落；两个前时期段落保留为单独敏感性分析。

这一分离防止读者不喜欢的 2022 年 Red Hat 段落定义后时期阅读阻力关系。当前通用特征空间**没有**高置信度地将该文档识别为前时期最不典型文档，这说明加权表示仍不完整，不能据此人工覆盖结果。

## 探索结果

| 特征 | 稳健的后减前效应 | 时间 permutation p | 仅后时期阻力 Spearman rho | 方向一致 |
|---|---:|---:|---:|---|
| 完整对比框架 | 1.51 | 0.033 | 0.78 | 是 |
| 平均相邻图衔接 | -1.88 | 0.026 | -0.39 | 是 |
| 主线绕行比例 | 0.83 | 0.089 | 0.35 | 是 |
| 抽象 shell 密度 | 0.71 | 0.189 | 0.28 | 是 |
| 缺少支撑的显式边比例 | 0.50 | 0.531 | 0.22 | 是 |
| 总标点密度 | 2.36 | 0.0016 | 0.39 | 是 |

所列时间方向在 leave-one-document-out 和移除已知译文后均保留。但在扩展的 161 特征探测中，没有图或修辞结果通过全局 multiple-testing correction。八个后时期段落评分只有两个 ordinal 层级，样本远不足以确认。

精确命题签名复述目前不能作为通用测量：它在后时期全文中更低（稳健效应 -0.98），却在最不受喜欢的后时期段落中更高（rho 0.51）。规则遗漏了以不同谓词和比喻表达的语义复述。

## 方向决定

继续研究两个图相关假设：

1. 程式化对比与强调制造冗余篇章边；
2. 薄弱相邻衔接及主线绕行导致局部阅读中断。

第一次最小干预测试了对比与强调式重新表述，因为其时间和读者信号的一致性最强。`experiments/prepare_refinement_pairs.py` 生成了三个盲法 A/B 任务。

两个修订版被明确偏好，没有原版被明确偏好。第三对被评为平局或两个版本都不好。读者在两次胜出中独立报告相同取舍：修订解释更清楚，但情感过平。在失败配对中，激进压缩省掉过多显式语法论元，导致修订难解析。

这为删去装饰性对比和反复重新表述提供正向方向证据，也直接反驳最大压缩。后续变体必须保留显式主谓宾结构和适度作者风格。

不将图分数升级为臭味指数。特征权重和阈值仍是暂定，当前图基于词汇，并非完整语义。

## 复现

~~~powershell
python experiments/robust_typicality_probe.py `
  --matrix feature_runs/pilot-matrix-v1/document_features.csv `
  --catalog feature_runs/pilot-matrix-v1/feature_catalog.json `
  --corpus-root data/pilot/monthly `
  --annotations feature_runs/pilot-annotations-v1 `
  --output-dir feature_runs/robust-typicality-v1 `
  --permutations 5000 `
  --seed 20260821 `
  --tuning-constant 1.5

python experiments/analyze_reader_friction.py `
  --tasks feature_runs/annotation-calibration-v1/tasks.json `
  --ratings data/annotations/reader-friction-v1.json `
  --model-dir models/stanza `
  --output-dir feature_runs/reader-friction-v1 `
  --device cpu

python experiments/prepare_refinement_pairs.py `
  --output-dir feature_runs/refinement-pairs-v1 `
  --seed 20260821
~~~

生成的图 schema 为 `deaiodorant-discourse-graph-0.1`。中间矩阵及图实例保留在被忽略的 `feature_runs/` 目录。

冻结配对结果保存在 `data/annotations/refinement-pairwise-v1.json`。
