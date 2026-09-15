# DeAIodorant

**让读者看得舒服。** DeAIodorant 改写公众号、媒体解读、科普和技术说明等公众信息文章，让问题讲得更清楚，减少惹人反感的表达，改善措辞、句子和行文顺序，同时保留原意与有效信息。中文译文也在范围内；艺术文体不属于本项目。

本机最新进展：《亡灵遗产》局部稿获得“至少我愿意读”的反馈，Microduck第二版也被评价为总体不错、目标臭味不明显，仍有一些翻译腔。[生成过程和新反馈](docs/routes/compact-refiner/reports/microduck-method-and-reader-feedback-v1.md)已记录；当前保留两篇具体阅读参考，后续复试合适的中文译文，再考虑便宜小模型，暂不训练。检查点见 [HANDOFF.md](HANDOFF.md)。

最新完整归档和续研入口：[HANDOFF.md](HANDOFF.md)（2026-09-15）。包含篇章动作实验、找回的历史语料/实验文件和最新Label Studio研究状态。

换机继续研究请先读 [HANDOVER.md](HANDOVER.md)，并检出 `init` 分支。交接包含本地产物与 corpus，以及不依赖 API 或 GPU 的恢复检查。

此前完成的[篇章动作首轮工程实验](docs/routes/compact-refiner/reports/cognitive-move-pilot-v1.md)和[同体裁真实文章发现](docs/routes/compact-refiner/reports/independent-media-discovery-v1.md)继续保留；这些字段实验本身不证明读者收益，也没有训练结果。后续改写的具体阅读反馈以上方当前检查点为准。

DeAIodorant 是位于内容生成与发布之间的中文文本改写层。它旨在保留作者原意、事实内容及有效细节的同时，减少重复、空泛和明显机械化的写作模式。

输入包括直接用中文写作的文章，以及翻译成中文的文章。规划中的小模型 refiner 必须仅凭中文文章就能工作；英文原文为可选材料。翻译来源是研究分层依据，不能作为丢弃目标文章的理由。

到 2026 年，生成内容已遍布中文互联网。DeAIodorant 关注文章是否值得阅读，不判定文章是否由模型写作。项目希望帮助创作者保留 generative AI 带来的效率收益，同时维护读者注意力、表达风格和清晰度。

> **项目状态：研究基础建设阶段。** 仓库目前实现了语料采集 pilot、翻译内容筛选，以及不依赖 LLM 的确定性特征提取框架。文本改写引擎尚未实现。

当前前半部分的工作是[真实媒体目标特征发现](docs/target-feature-discovery.md)，保留 2023 年前和 2025 年 6 月之后的时间分组及已有采集工作。[小模型改写路线](docs/routes/compact-refiner/README.md) 保留给下游通过验收的编辑、SFT 和有条件开展的 preference optimization。不会把旧的弱信号实验当作已经验证了目标而继续扩展。尚未开始 SFT 或本地 GPU 训练；Agent 评估不等于人工 gold labels。

## 产品原则

当前的[研究目标与证据计划](docs/target-feature-discovery.md) 使用完整的真实媒体文章，保留既有时间分组，并在特征验证或模型训练之前，优先建立反差充分的主观印象对照。合成编辑 pilot 继续作为工程对照；此前的弱样本实验不能证明消除臭味的效果。

- **以中文为本。** 分析并改善现代书面中文自身的模式，不照搬英文风格建议。
- **保留原意。** 不得以事实内容、限定条件或作者实际立场为代价，换取表面上更自然的表达。
- **读者价值优先。** 评估清晰度、具体性、连贯性、信息保留和读者偏好。DeAIodorant 不承担 AI detector 的功能，也不以规避检测为优化目标。
- **先有证据，再用启发式规则。** 从受控语料比较和人工评估中形成转换方法，不依赖网络上流传的经验清单。
- **可审计的改写。** 编辑结果应可检查，改写强度应可控制。

## 研究设计

以下前后时间对照设计仍是主要采样框架。既有语料和冻结证据均予保留。合成工程 pilot 与目标媒体证据分别记录；编辑来源记录见[数据契约](docs/routes/compact-refiner/data-contract.md)。

主比较使用两个刻意分隔的时间段内，高质量且传播可见度较高的中文网络文章：

| 分组 | 发布日期 | 用途 |
|---|---:|---|
| ChatGPT 出现前的基线 | 2023-01-01 之前 | 作为既有人工网络写作的参考 |
| 普及后的分组 | 2025-07-01 当日及之后 | 作为 generative AI 广泛采用后写作的参考 |

中间过渡期不纳入主比较。不对单篇文章作人类／AI 作者分类。在保留编辑相关性、来源完整性和受众关注证据的同时，不因可读性差而排除文章。在相同时间窗口内比较不同来源分层：直接中文写作、翻译、混合／改编内容及来源未明。旧的仅原创结果保留为对照视图；改善译文本身就是改写能力的目标。

规划中的项目流程如下：

```text
来源采集
    -> 来源完整性、传播可见度与来源分层
    -> 匹配的前后时间分组语料
    -> 语言特征对照与模式目录
    -> 自动与人工评估套件
    -> 中文改写引擎
    -> CLI/API 及发布集成
```

阶段边界与验收标准见[项目路线图](docs/roadmap.md)；从语料研究通往产品的备选方法见[改写路线图](docs/refinement-roadmap.md)。

已验证及候选的读者反感模式，以及准确的量化方法和复现流程，记录在[中文写作臭味目录](docs/smell-catalog.md)中。

## 已有能力

当前采集器检查来源可访问性、发布日期、正文提取、基本质量筛选、可获取的传播可见度信号，以及低成本翻译过滤。初始来源为 InfoQ 中文站和机器之心。

| 来源 | Pilot 窗口 | 采集方式 |
|---|---|---|
| InfoQ 中文站 | 2021-07 至 2022-06；2025-07 至 2026-06 | 已发布的 sitemap 与公开文章页 |
| 机器之心 | 2022 年 6 月；当前访问探测 | 通过 Common Crawl WARC 获取历史页面 |

机器之心目前将近期文章页替换为数据服务声明。采集器会记录该状态，不尝试绕过。

受版本控制的 `data/pilot/` 目录是 pilot 材料，不是干净的研究语料。它包含已知存在问题的样本，保留它们是为了评估和复现。

分析包与采集功能有意分离。它读取将来准备好的月度语料，验证冻结的元数据与内容 hash，提取无模型的表层特征及固定的 Universal Dependencies 句法特征，并输出带有完整说明的数值矩阵。它不调用 LLM，也不作统计推断。

## 仓库布局

```text
src/deaiodorant/            未来产品的 Python 包命名空间
src/deaiodorant/analysis/   可复现的文档特征提取
pilot_collect.py            语料采集与提取 pilot
translation_eval.py         翻译筛选器 development set 工具
translation_holdout.py      Validation 与 holdout 构建
translation_final_test.py   冻结 benchmark 运行器
tests/                      自动化测试
data/                       Pilot 语料与 benchmark 产物
benchmark_results/          已发布的 benchmark 摘要
docs/                       研究协议、架构和路线图
```

## 可复现的非 LLM 特征提取

安装可选的固定句法解析器：

~~~powershell
python -m pip install -e ".[dev,syntax]"
deaiodorant-analysis download-syntax-model --model-dir models/stanza
~~~

正式语料准备好之后，冻结 Universal Dependencies 标注并提取特征矩阵：

~~~powershell
deaiodorant-analysis annotate --corpus data/final/monthly --config configs/features.v1.json --model-dir models/stanza --output feature_runs/annotations-v1 --device cpu

deaiodorant-analysis extract --corpus data/final/monthly --config configs/features.v1.json --annotations feature_runs/annotations-v1 --output feature_runs/matrix-v1
~~~

矩阵包含字符、结构、标点、篇章、标题、词汇、POS 和 dependency tree 特征。公式、单位及已知敏感因素见[特征目录](docs/feature-catalog.md)。其他传统 NLP 特征空间记录在[特征探索方向](docs/feature-directions.md)中。

同一次提取还会生成不读取分组标签的稀疏 stylometry 词表，覆盖字符／POS n-grams、功能词、句首、连续标点和 dependency treelets。

## 环境配置

需要 Python 3.10 或更新版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

在 Windows 上，可复现的本地流程入口会创建并使用 `.venv`，安装项目，执行离线检查，配置可选的本地翻译筛选器，采集一轮新的诊断数据，并验证月度语料布局：

```powershell
.\scripts\run-corpus-pipeline.ps1 -TargetPerCell 2
```

每轮结果写入 `data/local/` 下一个新的、被 Git 忽略的目录。其中包括规范化月度语料、复核队列、采集器报告、完整性报告、依赖快照、采集日志，以及 run manifest。Manifest 记录 Git revision、Python 可执行文件、GPU 详情、采集窗口、模型 digest、prompt 版本、超时设置和确定性选择 seed。脚本显式调用 `.venv\Scripts\python.exe`，因此无需激活 shell 环境。如果任何必需的来源／时间单元未达到目标数量，经过模型筛选的文章缺少指定模型给出的通过决定，或者月度语料完整性检查失败，整轮运行都会失败。

当前完整 pilot 规模使用 `-TargetPerCell 10`。`-WithoutTranslationModel` 仅用于低成本诊断；它不提供由模型支撑的 fail-closed 准入筛选。

运行小规模采集 pilot：

```powershell
python pilot_collect.py --target-per-cell 2 --output-dir data/smoke
```

运行当前完整 pilot：

```powershell
python pilot_collect.py --target-per-cell 10 --output-dir data/pilot
```

## 语料布局

规范化正文以 UTF-8 文本保存，每个发布月份对应一份元数据文件：

```text
data/pilot/monthly/
  2022-06/
    <doc_id>.txt
    meta.jsonl
  2025-09/
    <doc_id>.txt
    meta.jsonl
```

`meta.jsonl` 的每一行通过 `text_file` 字段关联一篇正文。新增采集工作必须保留来源 URL、发布时间戳、采集时间戳、来源、质量信号、传播可见度信号及筛选决定。

## 历史仅原创视图的翻译筛选器

以下工具和冻结 benchmark 继续用于复现仅原创对照。当前研究在各自的来源分层中保留译文及来源未明的文章；此筛选器不定义产品适用资格，也不用于排除全部译文研究材料。

有明确翻译元数据时，使用确定性规则拒绝。在有歧义的情况下，可选本地分类器采用 fail-closed 策略：只有高置信度的 `original` 决定才能进入正式语料。它判断的是翻译状态，不是 AI 作者身份。

```powershell
.\.venv\Scripts\python.exe pilot_collect.py --translation-model qwen3.5:9b
```

Qwen3.5-4B 的冻结 final test 未达目标：保留了 56% 的原创文章，并误收了 2% 的译文。不得依据已暴露的测试调参。当前 9B 验证流程见[翻译 benchmark 协议](docs/translation-benchmark.md)。

`translation_benchmark_v2.py` 可用于翻译筛选器 v2 的候选采集。它从 InfoQ 中文站、机器之心档案及 Apache-2.0 许可的 LCTT 翻译项目构建经过全局去重的多来源复核池。Prompt 修改仅限于已复核的 development data；validation 只用于选择冻结候选，新的封存测试不得运行或用于调参。参见 [v2 协议](docs/translation-benchmark-v2.md)。

可在本地 Label Studio 界面复核待确认原创池。启动器会将每篇待复核正文保存为独立 UTF-8 文件，创建复核项目，导入任务并打开浏览器：

```powershell
.\scripts\run-translation-review.ps1 -Reviewer <stable-reviewer-id>
```

Label Studio Community Edition 1.23.0 是可选的 Apache-2.0 依赖。它安装在 `data/local/` 下被 Git 忽略的隔离环境中，在当前 Windows 环境约占 700 MiB。服务仅绑定 `127.0.0.1`；凭据、数据库、生成的任务文件、原文副本、依赖快照及日志都保留在被忽略的复核工作区。若安装或本地服务失败，不会给任何文章写入决定，候选数据保持原样。Analytics、Sentry、版本检查及在线 feature flags 均被禁用，使文章文本留在本地。

保留已提交的人工标注后，可以对剩余池进行保守的本地模型辅助分流：

```powershell
.\scripts\run-dgx-qwen38-review-triage.ps1
```

人工决定优先。只有外文来源检查返回高置信度的源语言判断时，剩余记录才进入相应操作分流。研究价值由两个判断一致的 profile 单独评估；较弱结果发布到独立的 Label Studio 项目。这是历史运行记录，使用了 DGX Spark 上的 Qwen3.8-27B BF16；当前没有 DGX Spark，不能据此启动上述远程命令。模型辅助结果属于诊断性测量，绝不导出为人工 gold labels。

默认 Windows 流程使用 Ollama 的 `qwen3.5:9b` 量化包。当前下载量约为 6.6 GB，可完整装入 16 GB 的 RTX 4080 级 GPU。Qwen3.5 按 Apache 2.0 许可证分发；再分发前应核验 model card 与 Ollama 包元数据。模型是可选的本地运行依赖，不是 Python 包依赖。模型响应缓存在运行目录内。若 Ollama、所需模型或推理调用不可用，基于模型的运行会停止，不会接纳不确定的文章。

## 数据与权利

本仓库包含用于研究交接及复现的第三方文章正文。这些正文的存在不构成再发布、训练或商业使用许可。贡献者应遵守来源条款、版权、隐私、robots 指令、限流及下架请求。权利不明确时，生产语料应优先保留引用和可复现采集 manifest，避免再分发全文。

## 参与贡献

修改前阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和仓库指令 [AGENTS.md](AGENTS.md)。仓库文档统一使用中文，必要时保留标准 English terminology、代码标识符及来源引文；迁移边界与历史原件核对方法见[文档语言规范](docs/documentation-language.md)。原始语料和冻结实验输入不随文档语言迁移而改写。`main` 分支有意保持在初始化 commit，后续不作修改；在维护者明确更改策略之前，当前开发放在 `init`。
