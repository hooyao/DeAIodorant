# 多来源后时期语料扩展 v2

## 状态

扩展交接于 2026-08-30 生成，通过冻结的 `post-reader-corpus-handoff-1.1` 验证器，零错误、零警告。它是本地研究数据，不是最终或具有代表性的语料。

~~~text
F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v2
~~~

包含 97 篇 2025-07-01 当日及之后发布的文档，不替换首次交接或任何受版本控制语料产物。

## 采集扩展

首次交接仅有 InfoQ 和美团技术博客的 50 篇文档。后来 29 个文档身份进入读者开发产物，仅剩 21 篇可继续开发。

第二采集阶段加入三个公开来源：

- 量子位：公开 WordPress API 和官方 RSS；
- 雷锋网：公开编辑分类页、sitemap 和实时文章页；
- 华为云社区：公开推荐页、文章级浏览量快照和实时文章页。

量子位与雷锋网得到 219 条原始记录，分别 99 和 120。量子位公开 API 返回一页 100 条，其中一条未通过确定性最小正文门槛，因此未将请求的 120 条目标静默标作完成。确定性翻译证据排除 46 条、跨语料近重复排除两条，剩 171 条进入模型复核。

华为采集扫描 30 页公开推荐，发现 280 个相关主题项，将前 100 条通过确定性正文门槛的完整记录落盘。主题表达式仅帮助采集，不分配最终分层。

没有绕过访问控制、登录、付费墙、CAPTCHA 或来源限制。

## 当前模型选择

模型选择不凭记忆热度。复核前立即捕获公开 OpenRouter 排名快照，其声明指标为周 token 用量，不是任务质量。前四名为：

1. Ox Alpha；
2. DeepSeek V4 Flash 0731；
3. MiMo-V2.5；
4. Hy3。

Ox Alpha 因身份不透明排除。另三者在实时模型目录中确认，并使用冻结结构化输出 schema 在同一个真实候选上测试。DeepSeek V4 Flash 0731 返回合规结果；MiMo-V2.5 与 Hy3 没有回答内容，记录为接口 smoke 失败，未批量运行。

因此，两项批次测量为：

- `qwen3.8-27b`：既有本地基线，在 `gx10` 上以 BF16 服务；
- `deepseek/deepseek-v4-flash-0731`：排名最高且通过任务专用 OpenRouter smoke test 的已识别模型。

OpenRouter key 从被忽略的 `.env` 读入进程内存，未复制到 `gx10`、写入产物、打印或提交。

### 后续接口修正

2026-08-30 审查复现 MiMo-V2.5 与 Hy3 空回答，发现是客户端假阴性。请求使用本地服务器字段 `chat_template_kwargs.enable_thinking=false`，未关闭 OpenRouter reasoning，并限制 completion 为 320 tokens。MiMo 用了 319 个 reasoning token，Hy3 用完 320 个，均因长度限制在回答输出前停止。显式设置 OpenRouter reasoning 控制及足够 budget 后，两者均返回有效结构化回答。

不重写或重标 v2 交接，保留原有 Qwen3.8-27B 加 DeepSeek 测量身份。修正改变对被排除 smoke 模型的解释及未来客户端，不改变既有 v2 准入决定。参见[当前 OpenRouter 语料模型接口审查](openrouter-corpus-model-interface-audit.md)。

## Fail-closed 双模型复核

两模型应用同一冻结外文来源保护规则，仅当二者独立返回高置信度 `original` 时，文档才继续。全部分歧及不确定均 fail closed。

量子位与雷锋网来源状态精确一致度为 135/171（78.9%），共同认定原创 131 篇。Qwen 将 DeepSeek 排除的 19 条判为原创，说明单独 Qwen 门槛会明显更宽松。

随后两模型都应用既有双 prompt 研究价值协议。只有每个模型内部 primary/verifier 一致为 `substantive`，且跨模型决定也一致时才继续。价值状态精确一致度 70/131（53.4%），剩 54 篇；高置信度分层保留 53 篇，雷锋网 40、量子位 13。

华为来源状态一致度为 82/100。研究价值阶段保留 36 篇跨模型 substantive 文档。将浏览量转换为采集的 100 条推荐记录内部的来源—季度百分位，冻结最低 0.40 后保留 23 篇。这避免跨发布日期使用单一原始浏览量阈值，但仍属于采集时传播可见度测量。

模型结果是测量，不是人工 gold。跨模型一致支持保守分流，不能确立准确率。

## 最终构成与分区

97 篇交接包含：

| 维度 | 数量 |
|---|---|
| 来源 | 雷锋网 40; 华为 23; 量子位 13; 美团 11; InfoQ 10 |
| 体裁 | 行业报道 43; 技术实践 36; 研究摘要 18 |
| 主题 | AI／模型／Agent 59; 商业／行业 22; 数据基础设施 13; 软件工程 3 |
| 角色 | 开发 67; 验证保留区 30 |


保留的 21 篇首次交接文档已进入确定性特征扫描，因此全部仅限开发。新准入 76 篇在任何新段落分析前分区。固定 hash seed 按冻结主题配额选择 30 篇 reserve：AI／模型／Agent 16、商业／行业七、数据基础设施七。Reserve 包含全部三种体裁：行业报道 14、技术实践 10、研究摘要六。

Reserve 未用于段落提取、特征发现或读者任务，仍需多名独立读者才能支持验证主张。

## 狭义假设结果

冻结的后置中心词修饰规则仅应用于 67 篇 development 分区，在 14 篇中找到 23 个宽泛中心词延迟候选，严格低锚点抽象修饰堆叠为零。未阅读 reserve。

读者定位的 `AI 原生时代全新算力服务需求` 因而仍是清楚的单例，未在扩展开发材料中复现。不得依据这些结果放宽规则来创建新 Label Studio 任务。

## 复现产物

采集、比较、分区及验证脚本为：

- `experiments/acquire_editorial_post_candidates.py`；
- `experiments/acquire_huawei_post_candidates.py`；
- `experiments/snapshot_openrouter_rankings.py`；
- `experiments/compare_provenance_models.py`；
- `experiments/compare_value_models.py`；
- `experiments/build_expanded_post_reader_handoff.py`；
- `experiments/validate_post_reader_handoff.py`。

本地交接身份为：

| 产物 | SHA-256 |
|---|---|
| Manifest | `ecab7336c2ca54f59d24b79bcb841f0d3f4085a9c80a117f5a3ea0e31fec5d01` |
| 文档索引 | `096a4e42a947c1cc7e60c17b0b91251fd83579e682bdf8ea7bb0e15aed3fbd80` |
| 验证报告 | `64d42f47c29a52e61faf53aacd80fb16efdb89f1bd06bc7cce571737cf0483e7` |
| OpenRouter 排名快照 | `abbdc3216fe27f82cc5354843f7f198db743d63b45d7e7702cee06bcd0090c5a` |


全部正文、模型缓存、分歧、排名快照和生成交接保留为被忽略的本地产物。不提交语料正文或模型输出。
