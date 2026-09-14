# OpenRouter 客户端维护：Retry-After

日期：2026-09-14

客户端版本：`compact-refiner-openrouter-1.1`

重试策略：`openrouter-retry-after-1.0`

本次维护发生在 CR-001 和 CR-001B 推理完成后。维护前的代码与输入已连同 hash 归档至 `feature_runs/compact_refiner/cr001-code-snapshot/`。本次变更不重新计算任何历史结果、费用预留、来源排除或模型评估。维护过程没有发起网络请求或进行训练。

旧客户端在短暂固定延迟后重试暂时性失败响应，忽略 `Retry-After`。后续调用改用以下规则：

| 响应条件 | 行为 |
|---|---|
| HTTP 429 或 503，且给出正整数秒数 | 至少等待该时长，再次尝试。 |
| HTTP 429 或 503，且给出有效 HTTP 日期 | 计算 UTC 时间间隔，向上取整，避免过早重试。 |
| 所需等待超过 60 秒 | 结束事务并抛出 `RetryDeferredError`；绝不为满足 sleep 上限而缩短服务器要求的间隔。 |
| header 缺失、格式错误、为零或日期已过 | 按配置的重试次数，使用 15、30、60 秒的有界确定性延迟。 |
| 有效数值间隔超出 datetime 范围 | 延后重试并设置 `manual_retry_required=true`；不得改用短延迟。 |
| 非暂时性 HTTP 失败 | 停止；存在 header 不会使该失败变得可重试。 |

`RetryDeferredError.metadata` 包括 `retry_not_before_utc`、规范化重试信息，以及刚刚请求失败时的底层安全失败原因。即使 `max_retries=0` 也可能抛出此异常，因为后续调用仍需遵守服务器截止时间。无法表示的截止时间显式设为 null，需要人工处理。不持久保存原始 header 或 HTTP 错误正文。

服务器截止时间持久保存。使用同一缓存的新 completion 请求不能通过改变 prompt、模型或 seed 绕过有效截止时间。由于服务器不能可靠提供 rate limit 范围，冷却期保守地应用于共享该账本的所有新 completion 请求。成功缓存的回答仍可直接读取，不发起网络调用。模型目录请求使用独立私有重试状态文件，不消耗支出账本。延后的调用不会自行调度；调用方必须安排之后再次调用。

状态不明确的失败尝试保留完整的保守费用预留。重试延后时，释放未尝试部分的额度，将事务标为完成；服务器截止时间仍有效时，后续调用不会再预留费用。对于真正中断的在途请求，继续保留既有的保守中断处理。

账本 schema 仍为 `compact-refiner-openrouter-1.0`，旧事务记录无需迁移。新事务与响应记录客户端及重试策略版本。请求正文 hash 和成功缓存标识保持不变，因为本次维护不改变模型请求或 prompt。复用旧结果时保留原 metadata，仅在返回值中增加 `cache_read_client_version` 字段；不改写磁盘记录。

验证使用 mocked transport 和可控 UTC 时钟。专项离线测试覆盖秒数、HTTP 日期、向上取整、60 秒边界、长延迟推迟、格式错误和极大 header、有界默认 backoff、目录请求行为、恢复后的冷却期、费用结算，以及旧缓存和账本兼容性：

```powershell
python -m pytest tests/test_refiner_openrouter.py
```

全部 56 项专项测试通过。HTTP 日期解释依赖正确的本地 UTC 时钟。冷却期不协调不同缓存目录或外部客户端。客户端仍无法保证远程提供者遵守其声明的计费上限；意外收费继续按现有记账政策记录并拒绝。本次变更尚未在真实触发 rate limit 的服务上验证。
