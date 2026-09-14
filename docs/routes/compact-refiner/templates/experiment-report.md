# 实验报告：<run_id>

状态：planned / running / awaiting_review / completed / failed / cancelled。

## 研究问题与预先冻结的判定规则

记录研究路线所处阶段、hypothesis、protocol 版本、预先指定的比较、最小有用收益、
meaning-preservation 与成本的准入条件，以及结果能够支持什么结论。
注明本次实验属于 development、validation 还是 final evaluation。

## 复现信息

记录代码 revision 与未提交 diff 的标识、输入及 split 的 hash、prompt 与配置的 hash、
确切的 model / checkpoint / provider、seed、运行环境、实际执行命令、产物路径及 hash、
起止时间和运行限制。不得在此粘贴凭据或完整的私有文本。

## 数据流与评审

报告独立分组、草稿、候选文本、使用权判定、排除项、缺失情况、deduplication 与 leakage
检查、人工及 model-assisted 评审数量、未通过的 meaning-preservation 检查，以及哪些候选
有资格进入 preference 评估。先说明对 protocol 的偏离，再展示结果。
同时交代 source generator、genre 和改写强度的构成。

## 实验结果

报告胜出、落败、两者都好、两者都差、无法判断的反馈，以及 reader / session 层面的诊断、
uncertainty interval 和主要比较。报告原始候选的失败情况、fallback、不改写行为、coverage、
改写幅度、latency、内存占用、token 用量、实际成本、重试和未完成任务。
不得用估计值填补缺失测量后，将其表述为实际观测。

## 反例与局限

说明策略在哪些情况下失败、排除了哪些样例、有哪些 meaning-preservation 风险、结果对
reader / genre 的适用限制，以及特征指标的改善是否与 preference 相背离。
仅在获得许可时使用 ID 和限定长度的引文；完整文本保留在私有数据中。

## 决策与下一步

注明决策：advance / retain baseline / revise on development / inconclusive / stop。
链接实验台账与决策记录，并保留失败产物。看到结果后，若修改 prompt、reward、threshold
或 checkpoint，必须建立新的实验版本。
