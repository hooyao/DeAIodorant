# 小型精修模型实验账本

本账本只包含新路线。计划记录不等于已执行实验。完整 manifest 和报告存在时，按路径与 hash 引用。

| ID | 日期 | 阶段 | 状态 | 输入／输出 | 决策 |
|---|---|---|---|---|---|
| CR-000 | 2026-09-14 | R0 | 已完成 | 路线约定、prompt、模板、客户端及记录工具、环境检查 | 授权自主预检；旧路线暂停，SFT 暂缓 |
| CR-001 | 2026-09-14 | R1 | 预检完成；目标覆盖未解决 | [预检报告](reports/cr001-preflight.md)：计划 24 组，生成 23 组，13 组来源通过，26 个 P/T 候选 | 人工跟进另行记录；没有训练接受或去臭验证 |
| CR-001B | 2026-09-14 | R1 | 已完成；仅模型评估 | 相同 13 个编辑输入，Qwen3.5-9B 容量对照，13 个输出和盲态 agent 复核 | 不根据 3B 基线推断全部小模型行为；未测量 SFT 收益 |
| CR-001-preview-1 | 2026-09-14 | R1 | 已记录定性反馈 | [人工反馈](reports/cr001-reader-preview-v1.md)：A/B/A；第 1 组存在内容顾虑，第 3 组偏好轻微 | 读者认为所有展示配对都无明显臭味；再次去臭比较前先确立目标覆盖 |
| Media-contrast-staging-v1 | 2026-09-14 | 目标发现 | 已记录来源暂存与定性反馈 | [新媒体校准](reports/media-contrast-calibration-v1.md)：24 个响应，20 篇非空正文，翻译标记后剩 16 篇；没有准入 | 读者认为提名文章 AI 臭味弱，但难读且像翻译腔；不是已确认强正例 |
| Ershi-cohort-v1 | 2026-09-14 | 目标发现 | 描述性计数完成 | [对比家族统计](reports/ershi-cohort-statistics-v1.md)：排除已知译文后，InfoQ 前期 5/17、后期 52/18（次数／文章数）；独立复现字节一致 | 保留为读者指定的信号假设；未验证质量 reward 或编辑规则 |
| Contrast-context-v1 | 2026-09-14 | 目标发现 | 已完成 | [全文审计](reports/contrast-context-audit-v1.md)：两次复核，57 次出现／13 篇完整文档；精确证据验证，准备过程复现 | 一致仅代表模型一致性；8 个共同重复候选，没有人工臭味标签 |
| Contrast-syntax-v1 | 2026-09-14 | Parser 可行性 | 已完成 | [CPU protocol](contrast-syntax-feasibility.md)：3 篇正文，164 个 parser 句子，5,602 个 word；两次成功运行字节一致，失败启动记录保留 | Parser 是检查辅助；不建立缺主语或完整树质量规则 |
| Provenance-stratified-contrast-v1 | 2026-09-14 | 目标发现 | 已完成 | [保留媒体计数与纠正](reports/contrast-context-audit-v1.md)：保留全部 40 篇 InfoQ 正文；新增一篇有记录的译文 | 翻译成为 provenance 分层；未解决不等于原创 |
| Media-repair-development-v1 | 2026-09-14 | 编辑开发 | 已完成；读者预览已撤回 | 保留[开发结果](reports/media-repair-development-v1.md)；[样本否定](reports/cowork-preview-withdrawal.md)取代 Cowork 读者请求 | 仅工程证据；没有人工偏好、去臭效果主张、接受、导出或训练 |
| Target-coverage-rescreen-v1 | 2026-09-14 | 目标发现 | 已完成 | [重新筛查结果](reports/target-coverage-rescreen-v1.md)：十二篇完整正文；零个持续目标提名，九个弱或不明确，三个格式不合适 | 保留覆盖缺口；不因此替换读者任务或改写 |
| Cowork-reader-preview-v1 | 2026-09-14 | 读者预览 | 已取消 | [撤回](reports/cowork-preview-withdrawal.md)：维护者否定样本的精确反馈存于预览 v1.1 sidecar | 不推断偏好或可读性结果；不重新提交 |
| Targeted-media-discovery-v1 | 2026-09-14 | 目标发现 | 已完成；人工反馈已记录 | [单篇发现](reports/targeted-media-discovery-v1.md)；维护者随后将 Baidu 评为 `一般臭` | 所给配对中的低强度参照；没有改写或效果主张 |
| Reader-anchor-feature-discovery-v1 | 2026-09-14 | 目标发现 | 探索性分析已完成 | [强参照报告](reports/reader-anchor-feature-discovery-v1.md)：人工评为严重的 SMZDM 与一般臭的 Baidu；30/64 个完整 block，四个风格家族和四项关系发现 | 人工严重程度已有依据；机制和测量仍探索性；不重复评分，不编辑、不设 reward、不训练 |
| Cognitive-move-analysis-v1 | 2026-09-14 | 操作化 | 示例标注已完成 | [六个关联原文的案例](reports/cognitive-move-analysis-v1.md)，修订核心动作与上下文边界并精确验证原文 | 带对照的描述性语义记录；没有自动检测器、标量分数、干预或训练结果 |
| Media-provenance-extension-v1 | 2026-09-14 | 独立采集／诊断 | 已完成 | [扩展结果](reports/media-provenance-extension-v1.md)：24 个固定 GET，21 篇非空唯一文本；前期 9 篇／2 次，后期 12/28；保留 3 篇后期译文 | 复用现有字面与聚集定义；一篇长访谈贡献后期 19/28 次出现；没有臭味或作者身份标签 |

## CR-000：路线初始化

目的：记录维护者的路线变化，使新工作流能够独立理解和复现。

产物见[路线索引](README.md)。观察到的环境是 Windows、Python 3.13.5、NVIDIA GeForce GTX 1080、8192 MiB VRAM、驱动 581.57。CR-000 未执行推理调用、模型下载、训练、读者任务或新语料采集。

已检查路线链接、模板 JSON、prompt 字段、fixture 身份、凭据排除和空白。维护前实现通过 90 项离线测试和编译。这验证工程行为，不验证读者收益。随后客户端 backoff 维护有独立验证记录；最终完整测试通过 113 项和编译。

维护者澄清 SFT 将使用其提供的云 GPU。配置前，按 CR-D008 提供针对工作负载的最低及推荐硬件、时长和成本估计。维护者随后按 CR-D009 恢复 API 实验；训练继续暂缓。

前次重新评估的历史工作区变更单独保留：`docs/research-reassessment-2026-09-14.md` 及更早文档修改不属于 CR-001 结果。Git `init` 仍是开发分支。

## 后续每次运行的必需记录

记录 run ID、阶段、protocol 或配置版本、状态、起止时间、代码与输入身份、实际命令、模型及主机身份、输出 hash、复核状态、成本、失败、排除、报告链接和下一步决策。有效状态为 `planned`、`running`、`awaiting_review`、`completed`、`failed` 和 `cancelled`。

不要仅因 API 请求或训练进程成功退出就宣布运行完成。验证必需产物，并报告缺失证据。
