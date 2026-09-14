# 翻译筛选 benchmark v2

## 状态与目的

Protocol `translation-gate-2.0-development` 用更大、来源更多样的 benchmark 生命周期，替代单一来源、小样本的开发流程。该 protocol 尚未冻结，也没有产生 final-test 结果。

任务是翻译来源分类，不判断 AI 作者身份。根据 fail-closed 决策策略，只有高置信度确认原创的文章才准入。

## 必须遵守的 split 策略

- 只能依据 development 数据修改 prompt 文本和规则。
- Validation 标签可用于选择已在 development 数据上固定的 prompt 版本。不得将 validation 错误转化为同一周期的新 prompt 规则。
- Prompt、模型 digest、解码配置、决策策略和阈值冻结前，不得运行 sealed test。
- Sealed-test 失败可以促成新 protocol 版本及与原数据不相交的新测试，但不能用于修补产生该失败的版本。
- 已暴露的 v1 final test 永久排除在 v2 构建与调优之外。

## 来源

### InfoQ 中国

采集器以保守频率使用已发布 sitemap 和公开文章页。显式译者字段是确定性翻译证据。原创候选需要中文作者署名、不带翻译标记，并具有中文报道、访谈、活动或第一方项目信号。成为 original gold 前仍须复核。

v2 采集器优先处理 2023-01-01 至 2025-06-30 过渡期，该时期不属于主要前后时间语料对比。

### 机器之心

历史页从 Common Crawl WARC 记录获取。页面级文章类型 `翻译` 或 `编译` 是确定性翻译证据。文章类型 `原创` 只能产生原创候选，本身不足以作为 gold，因为平台标签可能与正文中的外文来源证据冲突。

机器之心当前页面仍显示数据服务通知，采集器不会绕过。

### LCTT

LCTT 是原 Linux 中国翻译项目。已发布 Markdown 文件提供译者、reviewer、外文作者及原文 URL metadata。仓库采用 Apache-2.0 许可证。采集固定到一个 Git commit，只使用选定的 raw 文件，不克隆整个仓库。

LCTT 译文仅可用于 development。Validation 和 sealed test 限于同时提供翻译与原创候选的来源，防止来源名称成为完美的标签代理。

曾考虑 xitu/gold-miner 仓库，但它没有仓库级许可证，并说明译文仅限学习、研究和交流，因此未采集其正文。

## 候选与标签层级

| 层级 | 含义 | 允许用途 |
|---|---|---|
| 确定性翻译 | 显式译者、翻译／编译文章类型，或固定版本的 LCTT 发布 metadata | Development、validation、sealed test |
| 已复核原创 | Reviewer 确认属于中文报道、访谈、第一方实践或独立综合，并未发现具体被翻译的外文作品 | Development、validation、sealed test |
| 平台原创 silver label | 平台标为 `原创`，但没有人工复核 | 仅限 development 诊断 |
| 待复核 | 有候选信号但尚无决策 | 不得用于模型比较或发布效果声明 |

模型辅助复核属于测量，不是 human gold。其来源必须记录在 `reviewer` 字段中，并单独报告。

## 泄漏控制

进入候选池之前，每篇文档都与全部 v1 development、validation、已暴露 final、pilot 和 smoke 记录比较：

1. 稳定文档 ID；
2. canonical URL；
3. 规范化正文的精确 hash；
4. 基于 character shingle 的近重复检测。

构建 split 时，再检查文档 ID、URL 和内容 hash。Split seed 使用 protocol 版本。

## 当前候选池

初始 v2 采集得到 440 个候选：

| 来源 | 翻译 | 原创待复核 | 总数 |
|---|---:|---:|---:|
| InfoQ 中国 | 80 | 100 | 180 |
| 机器之心 | 40 | 120 | 160 |
| LCTT | 100 | 0 | 100 |
| 合计 | 220 | 220 | 440 |

生成的复核队列不是已经完成的 gold 数据集。当前含 160 篇文档的 silver development 产物明确用于诊断，不得作为 validation 或最终证据报告。

## 命令

采集候选：

```powershell
.\.venv\Scripts\python.exe translation_benchmark_v2.py collect `
  --output-dir data\translation_v2\candidates `
  --infoq-translations 80 --infoq-originals 100 `
  --jiqizhixin-translations 40 --jiqizhixin-originals 120 `
  --lctt-translations 100
```

生成诊断用 silver development 集：

```powershell
.\.venv\Scripts\python.exe translation_benchmark_v2.py bootstrap-development
```

### 本地人工复核工作区

使用本地复核启动器，不直接阅读嵌在 JSONL 中的正文或编辑候选队列：

```powershell
.\scripts\run-translation-review.ps1 -Reviewer <stable-reviewer-id>
```

命令执行以下可复现步骤：

1. 只选择 `original_pending_review` 记录；
2. 将每篇来源正文原样写入 `data/local/translation_v2_review/texts/<source>/<doc_id>.txt`；
3. 在工作区 manifest 中记录输入 hash 和复核配置；
4. 在隔离的本地环境配置 Label Studio Community Edition 1.23.0；
5. 创建项目，并一次性导入全部待复核记录；
6. 打开基于浏览器的阅读与分类界面。

界面同时显示完整正文、标题、来源、发布日期、文档 ID、候选证据及来源链接。Reviewer 选择 `Reviewed original` 或 `Exclude or uncertain`，再提供结构化理由和可选说明。快捷键 `1` 至 `9` 用于选择决策与来源理由。快捷键 `0` 单独记录因研究价值低或以宣传为主而排除的情况，不作为翻译证据。不确定时必须走排除路径。

Label Studio Community Edition 采用 Apache-2.0。隔离的 Windows runtime 当前约占 700 MiB。服务仅绑定 `127.0.0.1`；凭据、数据库、日志、原文、任务 JSON 和完整依赖快照留在被 Git 忽略的 `data/local/` 工作区。Runtime 或服务不可用时，复核停止，不产生自动决策。原始候选 JSONL 和冻结标签绝不改写。Analytics、前后端 Sentry、版本检查和在线 feature flag 均关闭，确保原文与复核决策留在本地。

仅限 loopback 的服务强制使用有效期 14 天的持久登录 cookie，因为内嵌浏览器可能在标注页仍打开时丢弃非持久 cookie，导致提交标注返回 HTTP 401。

### 模型辅助分流

Protocol `translation-review-triage-1.1` 减少重复人工复核，不把模型输出转为 human gold。先导出当前已提交标注，再运行并发布分流结果：

```powershell
.\scripts\export-translation-review.ps1 -Reviewer <stable-reviewer-id>
.\scripts\run-dgx-qwen38-review-triage.ps1
```

当前分流配置具有确定性并可缓存：

- 模型：DGX Spark GB10 上的 BF16 `Qwen3.8-27B`；
- Serving runtime：NVIDIA vLLM 26.04，batch／并发为 `16`；
- 模型配置 SHA-256：`191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`；
- temperature：`0`；
- seed：`42`；
- 外文来源 safeguard：`translation-review-triage-foreign-source-safeguard-v2`；
- 正常／重试输出预算：`320`/`512` tokens，第二次解析失败映射为 `uncertain/low`。

已提交的人工决策始终优先。对于剩余记录，当外文来源 safeguard 给出高置信度源语言判断时，才执行操作性分流。当前仅分流运行不执行旧版 primary 和 verifier profile。Safeguard 明确防止国内中文访谈、演讲、会议、第一方实践和中文研究解读，仅因带有 `整理` 标记或英文论文链接而被排除。只有证据确立了某个具体非中文来源作品时，才确认排除。任何分歧或较弱结果继续标为 `uncertain`，复制到独立 Label Studio 项目供人工复核。

当前运行保留了 11 篇人工确认原创与 3 篇人工排除，175 篇分流为模型辅助原创，31 篇分流为模型辅助排除，没有未解决记录。此前含 83 篇文档的复核项目仍可用于可选人工抽查，其中保留 5 份已提交标注。这些计数是操作性分流结果，不是 benchmark 准确性证据。完整 manifest、缓存、证据和按状态划分的产物位于 `data/local/translation_v2_review/triage_qwen38/`。

研究价值在独立 protocol `research-value-triage-1.0` 下测量。两个 Qwen3.8-27B BF16 profile——`research-value-primary-v3` 和 `research-value-verifier-v3`——必须在高置信度下达成一致。186 篇来源合格文档中，110 篇分流为内容充实，51 篇为价值低或宣传性内容，25 篇保持不确定。25 篇不确定文档位于 Label Studio 项目 3，并有专门的质量界面。该项目人工复核已完成：保留 9 篇，因研究价值低排除 16 篇。使用以下命令导出其已提交决策：

```powershell
.\scripts\export-research-value-review.ps1 -Reviewer <stable-reviewer-id>
```

DGX runtime 加载模型约占 50.22 GiB 内存。NVIDIA vLLM 容器受 NVIDIA 软件许可条款约束；模型再分发必须核查 model card。远程服务、结构化输出或连接失败时，缓存保留已完成的测量，该记录继续保持不确定，不会静默准入。

### 过渡期读者观察

一位 reviewer 报告，2023 年 7 月文章 `安卓手机上跑15亿参数大模型，12秒不到就推理完了` 存在强烈机械化风格，而其他许多 2023–2024 年文章仍保持常规编辑风格。这作为读者感知的诊断观察记录，不作为作者身份标签。

这项观察支持既定的冻结分组策略：2023-01-01 至 2025-06-30 的材料是异质的过渡期证据，不纳入主要时间对比。它们可用于探索性模式发现与评估设计，但不得据此声称单篇文章由 AI 撰写。2023 年前与 2025 年 6 月之后两组测量风格模式 prevalence 的变化，不证明个体作者身份。

复核不确定项目后，仅导出并合并两个 Label Studio 项目中已提交的人工决策：

```powershell
.\scripts\export-translation-triage-review.ps1 -Reviewer <stable-reviewer-id>
```

合并 CSV 不含模型辅助决策。界面还提供 `Low research value or promotional material` 作为独立排除理由，记录 benchmark 质量排除，不作为翻译证据。

按 benchmark CSV schema 导出当前决策：

```powershell
.\scripts\export-translation-review.ps1 -Reviewer <stable-reviewer-id>
```

导出包含 `review_include`、`review_gold_label`、`reviewer`、`reviewed_at` 和 `review_notes`。未复核行保持空白，finalization 时忽略。使用以下命令停止服务，同时保留复核数据：

```powershell
.\scripts\stop-translation-review.ps1
```

已复核原创数量或平衡后的来源单元不足时，finalization 采用 fail-closed：

```powershell
.\.venv\Scripts\python.exe translation_benchmark_v2.py finalize `
  --decisions data\local\translation_v2_review\review_decisions.csv
```

默认定稿规模为 160 篇 development、80 篇 validation 和 100 篇 sealed-test 文档，各自按标签平衡。Finalization 只生成产物和 hash，不运行 sealed test。

## 模型诊断结果

Qwen3.8-27B BF16 仅在 silver development 产物上运行。经过确定性正文标记清理后，当前 v1 prompt 接受了 80 篇 silver 原创中的 76 篇，80 篇确定性译文全部被拒绝。复核发现，被拒绝的四个 `原创` 页面本身就是外文来源的翻译或编译，因此该结果不足以支持放宽 prompt。恢复 prompt 优化前，必须先复核标签。
