# 本地句法 parser 可行性

Protocol：`contrast-syntax-feasibility-1.0`。日期：2026-09-14。
状态：在本次 parser 运行和案例检查前冻结的探索性 protocol。研究本地 CPU 解析能否辅助具体阅读缺陷检查，不估计句法错误 prevalence，也不构成读者 validation。不恢复历史整体写作质量分数。

## 目的性输入

解析 `data/local/contrast-context-v1/packets/` 中以下已有中性材料包的完整、未改动精确正文：

- `doc-03`：信息密集的技术公告。
- `doc-05`：维护者指出难读的 Cowork 案例，已有弱臭味评价不变。
- `doc-11`：标记较少的技术实践对照。

选样是有意且依据上述描述进行的，不是随机、代表性或独立 validation，也不是时间 cohort 对照。即使 parser 找不到可用区别，也保留三篇文档。不读取语义复核输出。既有语料准入与抓取限制仍未解决。

## 执行与证据保留

使用已安装的 Stanza `zh-hans` / `gsdsimp` 模型，运行 `tokenize,pos,lemma,depparse`。要求 `DownloadMethod.NONE`、CPU 推理、一个 PyTorch 计算线程、一个 interoperation 线程、确定性算法，以及 seed `20260914`；不下载、不调用外部 API。复用仓库后端的确定性、包版本和模型指纹辅助函数。若本地模型缺失或不兼容，应报告可行性失败，不代表获准下载替代模型。Stanza 是已有可选依赖；本研究不增加模型、依赖、服务或训练成本。既有软件和模型许可证不变，不重新分发权重。

按准备阶段 manifest 检查正文和出现位置材料包 hash。保留精确原文字节，包括提取器插入的换行；解析前不合并行、不规范化标点、不纠正文句。私下保存完整句子、token 和 word 记录，包括 Universal Dependencies head、relation、tag、可用的 token 与 word 字符 offset、精确原文句子切片及片段间空隙。offset 使用从零开始、右端不包含的 Python Unicode 位置。记录缺失 offset 和分段不匹配；绝不悄悄编造坐标。另存 CoNLL-U 便于检查。

不可变解析 manifest 记录代码、protocol、输入、模型文件 hash、模型指纹、包和 Python 版本、seed、CPU 与线程选择、逐篇完成数量和耗时，以及输出 hash。进度日志只包含文档 ID 和处理数量。若运行超过一分钟，检查进程存活、CPU 时间和进度产物，并在余下运行期间分散继续检查。不要只依赖 watcher。

## 案例检查

阅读每篇完整原文及其标注。在原文支持时，每篇检查一个具体别扭构式和一个普通省略或其他连贯对照。不强行制造缺陷或配对。记录精确原文与 offset、选定 UD 分析、阅读问题或连贯解释，以及 parser 是否真的能区分它们。parser 结构本身不能确立缺失篇章前提、事实准确性、冗余对立、意义保留或读者反感。

缺少显式主语不是错误标签。中文省略、共享主语、topic-comment 结构、不及物表达、标题和列表都可能正常。解释依存结构前，先检查 attachment 歧义、tokenization 和 segmentation 错误。提取器换行与文章格式可能使 parser 边界不符合语言学句子；保留这些失败证据，不修改输入来修复。

案例判断是助手辅助的探索性观察，标记 `human_gold: false`；不产生自动缺陷分数、prevalence 分母、编辑、新版本、训练标签、效果结论或臭味状态升级。成功意味着解析可复现执行并产生可追踪证据，不意味着模型能诊断文章质量。

## 复现与输出

```powershell
python experiments/contrast_syntax_feasibility.py --model-dir models/stanza --output-dir data/local/contrast-syntax-v1
```

输出目录必须为新目录。完整标注、原文副本、manifest、运行计数，以及后续 `inspection.json` / `feasibility-report.md` 均私存于此 ignored 目录。独立案例检查与不可变 parser 输出分开记录，并拥有自己的 provenance 和产物 hash。本 protocol 在运行后保持不变。
