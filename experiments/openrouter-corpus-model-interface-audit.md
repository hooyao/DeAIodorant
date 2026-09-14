# 当前 OpenRouter 语料模型接口审查

## 目的

本审查依据实时 OpenRouter 元数据及固定任务专用面板，选择基于模型的语料测量。不凭记忆中的模型热度、不评判写作特征，也不把模型一致性当作人工 gold。

## 实时模型证据

公开周 token 排名于 2026-08-30 捕获。与本审查相关的已识别模型为 DeepSeek V4 Flash 0731 第 2、MiMo-V2.5 第 3、Hy3 第 5、GLM 5.3 Flash 第 8。实时 `/api/v1/models` 目录也确认 Hy4 Preview、Qwen3.8 Max、Qwen3.8 2.4T-A95B 和 Qwen3.8 Flash。排名衡量用量，不衡量质量。

## 空回答诊断

先前 MiMo-V2.5 和 Hy3 的 smoke 调用使用本地服务器专用字段 `chat_template_kwargs.enable_thinking=false` 和 320-token completion budget。精确复现得到：

| 模型 | 结束原因 | 回答字符数 | Completion token 数 | Reasoning token 数 |
|---|---|---:|---:|---:|
| MiMo-V2.5 | `length` | 0 | 320 | 319 |
| Hy3 | `length` | 0 | 320 | 320 |


Reasoning 在回答输出前耗尽额度，导致空回答。使用显式 OpenRouter reasoning 控制及足够 budget 后，两模型均返回有效结构化输出。

GLM 5.3 Flash、Qwen3.8 Max、Qwen3.8 2.4T-A95B 拒绝关闭 reasoning；使用 low reasoning 和 4,096-token budget 后成功。Hy4 Preview 在单独重试中成功，但固定面板 24 次调用有 23 次因腾讯上游共享池限流失败。

## 固定面板

12 篇面板在任何模型结果可用之前选定，覆盖五个来源、三种表层体裁，以及确定性来源与价值线索。没有人工 gold labels。

| 产物 | SHA-256 |
|---|---|
| 面板 | `50a1275ea9cd235c4b135cff53542897d85f3011eefe150d2de6d81f21719d48` |
| 完整结果矩阵 | `8f67382f662c78f9b68148e37081ffce4e13bb99210be3220de99380b6f515d3` |


每个模型接收相同的冻结外文来源保护 prompt，以及相同的主要研究价值 prompt。

| 模型 | 成功调用 | 来源标签：original / excluded | 价值标签：substantive / low / uncertain |
|---|---:|---:|---:|
| DeepSeek V4 Flash 0731 | 24/24 | 8 / 4 | 7 / 5 / 0 |
| MiMo-V2.5 | 24/24 | 9 / 3 | 9 / 3 / 0 |
| Hy3 | 24/24 | 10 / 2 | 8 / 3 / 1 |
| Hy4 Preview | 1/24 | 不可用 | 1 / 0 / 0 |
| GLM 5.3 Flash | 24/24 | 10 / 2 | 9 / 3 / 0 |
| Qwen3.8 Max | 24/24 | 9 / 3 | 9 / 3 / 0 |
| Qwen3.8 2.4T-A95B | 24/24 | 9 / 3 | 8 / 3 / 1 |


六个接口可靠模型中，各任务两两精确一致度为 9/12 至 12/12。MiMo-V2.5 和 Qwen3.8 Max 的全部 24 个标签一致。GLM 5.3 Flash 和 Qwen3.8 Max 的 12 个价值标签全一致，来源标签 12 个中 11 个一致。DeepSeek 在该面板上更倾向排除。这些是测量差异，不是准确率估计。

## 批次策略

下一采集批次使用兼顾成本的三模型交集：

1. DeepSeek V4 Flash 0731 和 GLM 5.3 Flash 运行全部确定性候选；
2. 只有来源及价值高置信度一致的项目继续；
3. Qwen3.8 Max 只复核这些暂时通过项；
4. 最终准入要求三模型高置信度一致；
5. 任意请求错误、格式错误、非高置信度、不确定或分歧均 fail closed。

选择 Qwen3.8 Max 而非 2.4T-A95B，是因为二者标价相同且接口全部成功，但 Max 对面板全部 24 项给出高置信度，2.4T-A95B 没有。MiMo 和 Hy3 仍可用于审查测量，却不会增加人工 gold 证据。Hy4 因当前服务可靠性排除出批次，并非因回答质量。

OpenRouter key 从被忽略的本地环境文件读入进程内存，不打印、不复制到 `gx10`、不写入产物或提交。

## 复现

~~~powershell
$env:OPENAI_API_KEY = "<read from ignored local environment>"
$env:PYTHONPATH = "src"
python experiments/compare_openrouter_corpus_models.py `
  --panel <fixed-panel.jsonl> `
  --output-dir <ignored-output-directory> `
  --concurrency 4 `
  --model-spec deepseek/deepseek-v4-flash-0731 disabled 1024 `
  --model-spec xiaomi/mimo-v2.5 disabled 1024 `
  --model-spec tencent/hy3 disabled 1024 `
  --model-spec tencent/hy4-preview low 4096 `
  --model-spec z-ai/glm-5.3-flash low 4096 `
  --model-spec qwen/qwen3.8-max low 4096 `
  --model-spec qwen/qwen3.8-2.4t-a95b low 4096
~~~

生成的 prompt、证据字符串、原始语料摘录和 API 缓存保留在被忽略的本地存储。
