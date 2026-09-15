# Azure GPT-4.1 研究接入

日期：2026-09-15。维护者提供了现成的 Azure `gpt-4.1` deployment、Responses API endpoint 和 key，并授权使用约50美元额度。此授权覆盖该Azure部署，与OpenRouter只用便宜小模型的约定分开。不能将GPT-4.1当作先前GPT-4 Turbo的同一模型或已验证的风格替代品。

## 配置与调用

根目录 `.env` 保存 `AZURE_OPENAI_API_KEY`、`AZURE_OPENAI_BASE_URL` 和 `AZURE_OPENAI_DEPLOYMENT`。原 `OPENAI_API_KEY` 继续属于 OpenRouter，不覆盖或回退混用。`.env` 被Git忽略，真实资源地址和key不进入研究产物。

```powershell
python -m pip install -e ".[dev,azure]"
```

接入使用OpenAI Python SDK的Responses API。Azure v1支持 `OpenAI(base_url=..., api_key=...)`，`model`填写deployment名称。读取 `response.output_text` 得到纯文本；`response.output[0]`是结构化输出项，不能始终当作答案字符串。

接口按官方文档核对：

- [Azure Responses API](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses?view=foundry-classic)
- [OpenAI文本生成](https://developers.openai.com/api/docs/guides/text)
- [Azure Responses请求与响应字段](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/responses?view=rest-microsoft-foundry-v1-preview&preserve-view=true)

本机原有SDK为2.28.0；已加入独立的 `azure` optional dependency，不要求既有离线分析和OpenRouter流程加载Azure SDK。SDK许可证为Apache-2.0（其自身第三方依赖遵循各自许可证），不下载模型权重或部署额外云资源。

## 预算记录

配置在 `configs/azure-gpt41-research-v1.json`。维护者所说的约50美元是可用额度说明，不代表已读取实际余额。本客户端设45美元本地运行上限留出余量。共享账本固定在 `.env` 同目录的 `.azure-responses-budget/`，缓存放在 `data/local/azure-gpt41-live-v1/`；更换实验缓存目录不会重置总账本。两者均保持Git忽略。

由于未取得该Azure资源的实际计费SKU与合同价格，暂按输入每百万token 10美元、输出30美元进行保守预算预留和用量估算。它们是管理用计划价，不是所声称的GPT-4.1实际费率。Responses返回的token用量与Azure实际账单应分开记录；账单金额未知时保持为空，不伪称估算就是实付金额。

调用前预留最大输出及保守输入预算，取得有效用量后更新估算。超时、HTTP失败或用量不明保留预留，不将未知调用当作免费。缓存命中不产生新请求，禁止为避开预算换目录重置账本。其他程序的调用不在此本地账本内，Azure门户的实际余额和账单仍是外部依据。

## 失败行为与实验边界

默认一次请求、零自动重试，不跟随重定向，不使用model fallback。文本请求设置 `store=False`，不打开联网或工具。错误只记录安全原因码，不保留原始HTTP、凭据或异常消息。身份、配额或额度失败时停止批次；没有得到答案的请求不能伪造为成功。

首次只做极小的连接检查。连接成功不等于模型改写能力得到验证，不能更新已有文章的阅读结果。后续实验仍使用完整原文、带版本的prompt、内容复核与读者反馈；当前不开始SFT或申请GPU。

同一次失败请求不会在客户端内部重试，也没有自动睡眠。当前适配器不实现自动 `Retry-After` 调度；遇到429、503等错误时，实验编排必须停止并按服务端要求安排后续调用，不能立即循环重发。连接检查脚本已有请求记录时直接拒绝再次执行。

活动账本和API缓存保持忽略。单次研究结果可经凭据检查后导出到新的冻结目录，连同用量、配置指纹和检查记录发布；不把未来还要写的live缓存直接加入Git。

换机时应恢复最新导出的账本和初始化标记到 `.azure-responses-budget/`，再使用新机器本地配置的.env；不能从零账本继续同一额度。首次冻结快照位于连接检查目录的 `live-ledger-snapshot.json` 和 `live-initialized-snapshot.json`。仅在新机器尚无账本时恢复，不用旧快照覆盖更新的账本。后续每次交接需导出新的快照；已成功请求若没有迁移相应缓存，客户端会拒绝为同一请求再次付费，其他新请求仍沿用累计预算。

## 本次已验证结果

唯一线上检查返回“连接成功”，状态为 `completed`，请求deployment和返回model均为 `gpt-4.1`。用量为输入13、输出3、合计16 tokens；按计划价计入本地账本的估算为0.00022美元，实际Azure账单金额未知。共享本地预算剩余估算为44.99978美元，这不是Azure余额查询结果。返回值没有公开具体checkpoint日期，不能推断为某个固定历史快照。

记录位于 `data/local/azure-gpt41-connection-v1/`，包括脱敏授权摘要、实际请求、响应、调用前后预算和检查结果。不要重新运行已有 `run.py` 来重复测试。后续使用入口为 `deaiodorant.refine.azure.AzureResponsesClient`，配置沿用同一个 `.env` 和中央账本。

适配器47项针对性离线测试通过，项目完整离线测试248项通过，编译检查通过。测试覆盖认证分离、请求前预算预留、重启与缓存、错误脱敏、缺失用量、不完整回答以及禁止重定向等情形；它们不构成对模型改写质量的判断。
