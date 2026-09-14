# 参与 DeAIodorant

DeAIodorant 目前正在建设研究基础。贡献应增强可复现性，并推进以读者体验为中心的中文文本改写，避免夸大现有语料能够支持的结论。

## 开始之前

阅读 `AGENTS.md`、`docs/` 中的相关协议，以及准备修改的代码附近的测试。当前工作放在 `init` 分支；在维护者明确更改分支策略之前，不得更新 `main`。

涉及语料或评估的工作，应说明：

- 研究问题；
- 来源和日期覆盖范围；
- 纳入、排除及去重规则；
- 传播可见度和质量信号；
- 已知混杂因素和数据缺失；
- 可复现生成产物的准确命令。

## 本地配置

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

## 修改要求

- 每个 pull request 聚焦一个研究、产品或基础设施目标。
- 行为变化时，添加或更新测试。
- 默认测试保持离线、确定性运行。
- 阅读 final-test 结果之后，不得修改冻结的 gold data。
- 不得提交凭据、cookie、个人数据、模型权重，或没有来源记录及可再分发理由说明的抓取内容。
- 保留现有命令行入口；若有意引入 breaking change，必须记录。
- 文档统一使用清楚、自然的中文，必要时保留标准 English terminology。此要求覆盖 README、研究协议、报告、模板及 Agent 指南。代码标识符、命令、路径、配置键和 schema 字段保持既有形式；原始语料、语言学示例及冻结实验输入保留原文。本次文档语言迁移不要求改写既有代码或 commit 信息。

## Commit 信息

使用简短的祈使式标题，或遵循 Conventional Commits 格式，例如：

```text
feat: add matched-cohort sampler
fix: preserve negation during sentence fusion
docs: record translation benchmark protocol
```

## Pull request 检查清单

- [ ] 修改范围清楚，没有无关的数据重写。
- [ ] 测试在本地通过。
- [ ] 生成产物附有复现元数据。
- [ ] 语料改动保留月度元数据不变量。
- [ ] 改写改动保留原意，并提供可检查的 diff。
- [ ] 文档反映行为或项目边界的变化。
