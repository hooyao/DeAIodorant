# 有界 InfoQ 时间候选暂存 v1

日期：2026-09-14。采集实验方案：`media-contrast-staging-v1`。
选择修订：`index-frame-selection-amendment-v1`。
资格审计：`media-contrast-staging-eligibility-audit-v1`。

本次运行在[校准的目标发现要求](../../../target-feature-discovery.md) 下保留并运用有用的采集和时间框架。它是未经评审的采集暂存，不是干净语料、强臭味样本、特征测试、编辑实验或训练数据。运行期间没有打印文章正文或向模型展示正文。未使用模型、GPU 或 API 推理。旧弱样例研究的历史局限仍保留。

## 结果与保留情况

| 结果 | 预期后期抽样框 | 预期历史抽样框 | 合计 |
| --- | ---: | ---: | ---: |
| 冻结文章 URL／公开文章 GET | 12 / 12 | 12 / 12 | 24 / 24 |
| 完整 HTTP 200 响应 | 12 | 12 | 24 |
| 页面状态日期符合预期主要组 | 12 | 12 | 24 |
| 非空采集器归一化的正文 | 12 | 8 | 20 |
| 采集器正文为空的提取失败 | 0 | 4 | 4 |
| 确定性翻译排除 | 3 | 1 | 4 |
| 剩余待进一步评审 | 9 | 7 | 16 |
| 正式准入／已确认臭味标签 | 0 / 0 | 0 / 0 | 0 / 0 |

完整 HTTP 抓取不能与完整文章提取混淆。复用采集器即便在 `.ProseMirror` 无文本时，也返回文章元数据。四个历史抓取正文为空；相同的空 SHA-256 代表提取失败，不是有意义的重复文本聚类。不可变尝试日志将全部 24 项称为 `captured_unreviewed`，因为已捕获响应和元数据。单独的 `eligibility-audit.json` 将这四项记录为不可用文本抓取，没有重写尝试日志。未使用替代端点、需认证路径或替补 URL。

空正文 ID 为 `769ecc5e088514e4261ae7e0`、`8a835ce2a2584c3c9040fcc5`、`c979e224eb220101fb785893` 和 `94484784827b950a4ea5beea`。确定性翻译排除为 `9d2686869fb90420de5a6d40`、`9656e09a0c8ef6938c517cef`、`83e3fb47524511fba7945931` 和 `0c1bc051de0fc98fbcd0524d`。两组不相交。没有时期不符结果、已选 ID 重合、声明的规范 URL 冲突或已知精确内容 hash 重合。非空正文中无批内精确重复。

实际历史发布日期范围为 2020-07-06 至 2022-10-28，后期为 2025-10-30 至 2026-06-01。这些狭窄 sitemap 抽样框没有充分覆盖 7 月 2025 边界，无法支持变化点推断。日期属于抽样来源过程，不是个体作者身份或臭味标签。

## 冻结抽样框与正文请求前的明确修订

唯一发现端点是公开 `robots.txt` 和 InfoQ 发布的 `index_1.xml`、`index_3.xml` sitemap。两个 XML 文件各含 9,800 个跨页面类型条目。仅文章计数如下：

| 抽样框 | 不同文章 URL | 已知标识排除 | 合格索引 URL | 选中 |
| --- | ---: | ---: | ---: | ---: |
| `index_1.xml`，预期后期 | 4,023 | 56 | 3,967 | 12 |
| `index_3.xml`，预期历史 | 7,868 | 66 | 7,802 | 12 |

每条 XML 条目只提供 `loc`、`changefreq`、`priority`，没有逐 URL `lastmod` 或发布日期。HTTP `Last-Modified` 描述 sitemap 响应，不是文章。因此初始保守日期提示选择器选出零项；其 manifest 和逐条目决定均保留。

请求任何正文之前，主 agent 明确批准用原先指定索引作为预期时期抽样框。修订复用已抓取 XML 和 robots 字节，不改变配额、来源或 seed。排除已知标识和 robots 禁止项后，用现有 `stable_order` 函数及 seed `media-contrast-staging-v1-20260914-<cohort>` 排序，固定前 12 项。实际时期组归属随后由嵌入文章 `publish_time` 判定。时期不符、失败或被排除抓取都不替补。修订仅基于抽样框元数据缺失，在文章结果出现之前作出。

冻结后的修订选择 manifest SHA-256：`e8c479f160f0591b28063fcc77f64f5c63ed4b276c4221dd474cabf8860f5679`。
保留的空选择 manifest SHA-256：`8b594583e336cc675d9f237c0ae61a33af8fc1a86a02cfd30934f6816bdb1c5d`。

## 暴露与来源限制

已知标识排除机械地收集自试验按月元数据、读者标注文档 ID 及单独准备的 `data/local/media-identity-exclusions-v1.json`。该导出只含先前数据集的文档 / URL / 内容 hash 标识。本暂存脚本没有打开底层 benchmark 文件、正文、金标准标签、决定、分数或结果。合并排除覆盖 395 个文档 ID、370 个规范 URL、210 个已知内容 hash。来源文件 hash 和导出 hash 同时记录在排除与选择来源过程中。

这些检查排除已知精确标识；近似重复和缺失的历史交接材料覆盖仍未解决。余下 16 篇是待检查候选，不是独立验证保留集。在该审计前，未通过控制台输出向 agent 暴露源文本。

会话共发出 27 次普通未认证 GET：一次 robots、两次 sitemap、恰好 24 次文章请求。全部返回 HTTP 200；没有重定向、重试、认证、cookies、替代内容端点、链接资源获取或引用媒体下载。响应完成到下一请求的最小测得间隔为 2.000066 秒。客户端遇 HTTP 429 或 `Retry-After` 停止后续请求，不回填。该公开客户端禁用环境隐式凭据。

文章请求从 06:34:05 持续至 06:35:19 UTC。在约 10、24、40、60 秒的直接检查确认进程存活、CPU 时间增长、请求 / 尝试日志增长和进度；结束检查确认退出代码 0。`progress.json` 在请求前及每次尝试后更新。没有把监控器通知当作事实来源。

## 已保留内容与未知事项

私有抓取包括 `requests` 暴露的精确响应字节（会应用 HTTP 传输解压）、安全响应头、请求 / 完成时间戳、hash、可获得的完整采集器归一化的文本、解析后的文章 HTML、语义段落映射及图表 / 图注 / 链接 / 媒体引用。原始响应 HTML 是权威来源表示，`article.dom.html` 是解析器序列化。重建段落文本与全部 24 个抓取的归一化的正文精确匹配，包括四项空正文失败。没有静默重写来源空白或内容。

采集器归一化的行不是原段落数。复用呈现映射器处理行内文本边界并保留来源行映射，不能确定浏览器呈现，也不能恢复图像内部内容。后期和历史分别有 30、33 个图像 / 媒体引用，57、44 个超链接；所引资源未获取。

四个确定性翻译标记作为排除处理。其他文档没有该标记，不代表通过原创审查。实质质量、翻译／编译来源过程、来源文本完整性及合适传播可见度证据仍需进一步评审。试验 `quality_pass` 仅保留为 `legacy_quality_pass_diagnostic_only`，绝不作为准入准入检查。非空抓取中，后期文本长度从 243 到 21,891 字符；长度本身不能充分说明质量或目标相关性。

当前页面浏览量快照：后期为 2,507 至 18,433，历史为 1,360 至 8,076。它们不是固定年龄或按来源季度可比的受众指标。未声称高传播可见度通过、来源 / 主题 / 形式匹配、强／弱感知对比、普遍程度估计或时间效应。公开访问不能确定再分发或训练权利。

## 命令、产物与验证

```powershell
python experiments/stage_media_contrast_candidates.py freeze --output-dir data/local/media-contrast-staging-v1
python experiments/stage_media_contrast_candidates.py select-index-frame --output-dir data/local/media-contrast-staging-v1
python experiments/stage_media_contrast_candidates.py fetch --output-dir data/local/media-contrast-staging-v1
```

首个命令拒绝已有目录。修订拒绝已经修订或开始执行的选择。获取拒绝已有尝试运行；不自动重试或覆盖。初始空选择与明确修订分开保存。本脚本是有界单次运行工具，不是新的通用采集服务。

全部生成来源数据位于 Git 忽略目录 `data/local/media-contrast-staging-v1/`，约 20.2 MiB。主要文件：

- `selection-manifest.json` 和 `selection-manifest-index-v1.json`：初始及修订后冻结选择标识、运行环境、来源 hash 与政策；
- `frame-*.jsonl`：全部文章抽样框决策，包含未选中的排除项；
- `identity-exclusions.json`：仅标识的排除快照及输入 hash；
- `requests.jsonl`、`article-attempts.jsonl`、`progress.json`：全部网络尝试与进度，不打印正文；
- `raw/` 和 `documents/<doc_id>/`：来源响应、归一化的正文、解析后的 HTML、语义块、结构、元数据；
- `summary.json`、`verification.json`、`eligibility-audit.json`：抓取结果、独立完整性检查、可用文本／排除纠正。

manifest 记录脚本、采集器、呈现映射器 hash 和包版本。编译通过。独立检查验证全部 27 个响应 hash、24 个归一化正文 hash、所有块拼接、精确冻结 URL 顺序、请求唯一性与间隔、标识来源文件未变以及采集 / 呈现源码未变。UTF-8 解码未引入替代字符。现有仓库语料 / benchmark 产物和配置未修改。推理成本为零，没有新增依赖项或模型产物。
