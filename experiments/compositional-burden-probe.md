# 组合整合负担探测

## 状态

这是结果后的开发探测，由第四轮仅后时期干预之后的读者反馈引发，不属于冻结的验证分析，也不是作者身份证据。

读者描述了独特体验：单个词仍可理解，但组合后的技术文本很难整合，仿佛太多词被拧成一个单位。这种困难主要不是明显的程式化 AI 风格标记。

## 测量目标

本探测将 *compositional integration burden* 操作化为一组透明的句法测量向量，有意不构造单一负担分数。

向量包含：

- 每句 CJK 字符数、分句中心词数、实词 token 数和不同实词 lemma 数；
- 每个分句中心词的实词 token 数；
- 虚词与实词 token 比；
- 分句中心词直接显式论元的覆盖率；
- 依存距离、长依存弧及树深；
- 名词修饰跨度与连续名词修饰深度；
- 每句从属和并列关系数。

两个冻结的探索阈值为：长依存弧五个 token 位置，长名词修饰四个位置。这些是描述截点，不是产品阈值。

Universal Dependencies 解析是带解析器误差的确定性测量，不是人工语言学 gold labels。不会要求读者标注这些特征。

## 第四轮干预诊断

受控材料包括 `post-only-conservative-reframing-development-4.0` 的 10 个原版／修订配对。配对结果不能验证特征：全部九个明确回答选展示侧 B，而原版侧别按五比五平衡。

修订差值仍暴露出冻结编辑算子的副作用：

| 测量 | 修订后增加 | 修订后减少 |
|---|---:|---:|
| 虚实词比 | 0 | 10 |
| 每分句中心词实词 token 数 | 6 | 4 |
| 每句 CJK 字符数 | 3 | 7 |
| 平均树深 | 2 | 8 |
| 长依存弧比例 | 1 | 9 |
| 平均依存距离 | 4 | 6 |

算子始终删去虚词，并常把更多内容放到每个谓词之下，与压缩现象相容。同时，多数修订缩短句子、降低树深和长依存。这些观察不支持把向量合并成一般句子复杂度分数。

偏好一致次数仅作为诊断保留在生成摘要中。展示侧与回答完全混杂，不得用这些次数调整特征阈值。

## 新后时期发现扫描

同一向量应用于未被第三轮阅读阻力筛查或第四轮干预选中的后时期文档段落，覆盖 26 篇文章中的 183 个合格段落。

候选排序使用六个预先声明的信号：

- 显式论元覆盖率低；
- 每分句中心词实词 token 数高；
- 每句不同实词 lemma 数高；
- 虚实词比低；
- 长依存弧比例高；
- 平均名词修饰跨度高。

信号转换为来源与体裁内部的百分位。扫描统计有多少信号落入假定最高负担四分位，不取均值构成分数。读者结果不作为输入。

人工完整性复核排除了问答片段、发言人简介、导航片段、章节标题片段和图像生成 prompt。限定范围的命题解压缩干预保留六篇不同文章的六个段落：InfoQ 三个、美团三个；行业报道、研究摘要、技术实践各两个。

## 形成的干预假设

下一假设比“缩短句子”更窄：

> 将不变的命题集合分配到更清楚的整合单位中，可以在不删除信息、不压平作者风格的情况下，提高继续阅读意愿。

编辑可在已有语义边界拆句，并重复已经确定的指称对象；不得添加前提、因果关系、机制、示例或证据。必须保留全部命题、实体、数字、否定、限定、不确定性标记、归因及技术术语。篇幅限制为原文的 95% 至 125%，句数必须增加。

项目 6 的全部明确回答均选 B，因此新干预包含一个相同文本控制和一个不相邻的镜像配对。只有相同对选择无差异、镜像回答随内容而非侧别变化时，才解释处理偏好。

两个控制后来均通过。六项命题解压缩干预中，三项偏好修订、三项偏好原版。因此不升级广义解压缩。读者定位的残留问题支持将研究收窄到名词中心词延迟及低锚点抽象修饰堆叠；参见[后置中心词修饰语延迟探测](head-final-modifier-probe.md)。

## 复现

~~~powershell
python experiments/compositional_burden_probe.py `
  --answer-key feature_runs/refinement-pairs-v4/answer_key.json `
  --results data/annotations/refinement-pairwise-v4.json `
  --model-dir models/stanza `
  --output-dir feature_runs/compositional-burden-v1 `
  --device cpu `
  --seed 2026082703

python experiments/scan_post_compositional_burden.py `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1 `
  --exclude-answer-key feature_runs/reader-friction-screen-v3/answer_key.json `
  --exclude-answer-key feature_runs/refinement-pairs-v4/answer_key.json `
  --model-dir models/stanza `
  --output-dir feature_runs/compositional-burden-post-scan-v1 `
  --device cpu `
  --seed 2026082704
~~~

维护者要求未来模型推理（包括批量解析器推理）在 `gx10` 上运行。以上命令标识产物与参数，不指定执行主机。

两次重复配对探测逐字节一致：

| 产物 | SHA-256 |
|---|---|
| 变体特征 | `2e10a7347e2ed4030366dad1293b35243d5fab740aef1a2a22a615b8bf5eb44a` |
| 配对差值 | `f773c345bf7c4442a906f087674031b24d785c0c2da54f518084ce685fe867ef` |
| 摘要 | `de9decfda0acca5234beb9bd0b7ce6009e25ea683e93e08a8967680b31a8c373` |

生成的解析、特征矩阵、短名单、来源段落和盲法 答案键 保留在被忽略的 `feature_runs/` 或本地交接目录，不提交。
