# 新后时期读者语料交接

## 状态

协议 `post-reader-corpus-handoff-1.1` 在生成下一读者任务前冻结。它定义开发筛查的最低输入，不授权在本工作区采集语料，也不使语料成为最终或有代表性的集合。

直接目的是避免用 2025-07 之前或过渡期材料替代 2025-07-01 当日及之后的文章。新建 Label Studio 项目之前，验证器必须通过。

## 必需目录布局

~~~text
<handoff-root>/
  manifest.json
  documents.jsonl
  texts/
    <doc_id>.txt
~~~

`documents.jsonl` 的路径必须相对交接根目录。验证器不修改该目录。

## Manifest schema

`manifest.json` 必须包含：

~~~json
{
  "protocol_version": "post-reader-corpus-handoff-1.1",
  "generated_at": "2026-08-22T00:00:00Z",
  "status": "candidate_pool_not_reader_exposed",
  "post_start": "2025-07-01",
  "documents": 60,
  "documents_file": "documents.jsonl",
  "documents_sha256": "<lowercase SHA-256>"
}
~~~

索引 hash 覆盖 `documents.jsonl` 的准确字节。

## 文档 schema

每条 JSON Lines 记录必须包含：

- `doc_id`：24 个小写十六进制字符；
- `source`、`title`、`url`、`published_at`、`collected_at`；
- 相对 `body_path`、`content_hash`、`cjk_chars`、`text_chars`、`line_count`；
- `quality_pass`、`is_translation`、`translation_evidence`；
- `provenance_status`、`provenance_basis`、`value_status`；
- `visibility_status` 和结构化 `visibility_evidence`；
- `topic_stratum`、`format_stratum`。

准入记录须全部满足：

- `published_at` 为 2025-07-01 当日及之后；
- `quality_pass` 为 true，`is_translation` 为 false；
- 来源状态为 `human_reviewed_original` 或 `model_assisted_original`；
- 模型辅助来源记录注明模型、冻结置信度至少 0.90，并记录 prompt 版本；
- 价值状态为 `human_kept` 或 `model_assisted_substantive`；
- 模型辅助价值记录注明模型及 prompt 版本；
- 传播可见度状态为 `verified_high_visibility`，证据非空；
- 体裁为 `technical_practice`、`research_summary` 或 `industry_reporting`。

模型辅助来源及价值决定仍属测量，不是人工 gold。翻译和编译排除必须 fail closed，并与最终的前时期比较对称。

正文文件采用严格 UTF-8，无 BOM，使用 LF 换行，结尾恰好一个 LF。`content_hash` 是去掉该末尾 LF 后正文的 SHA-256，字符数也使用同一正文。拒绝与受版本控制 pilot 或其他交接记录完全或近似重复的正文。

## 最低覆盖门槛

准入池满足以下要求，开发才准备就绪：

- 至少 36 篇文档；
- 至少两个来源各 12 篇；
- 至少三个主题分层各六篇；
- 每个要求的体裁分层至少六篇。

这是最低开发池，不是验证池。优先准备 60 篇，以便看段落前冻结独立文档级保留区。通过少于 60 篇时可以开发，但不能主张 held-out validation。

传播可见度须相对来源及采集窗口定义。单一当前原始浏览量不足，会引入文章年龄和 survivorship bias。

版本 1.0 提出完整交叉的来源×体裁最低要求，后来在任何交接或读者暴露前替换，因为真实编辑来源有各自体裁专长，强制每来源覆盖每单元会诱发错误体裁标签。版本 1.1 保留来源与体裁多样性、报告完整交叉表，并要求后续匹配控制不平衡。

## 暴露与泄漏门槛

验证器拒绝已出现在受版本控制标注、实验协议或研究文档中的文档 ID，也拒绝与受版本控制 pilot 重叠的文档 ID、URL、精确正文和高相似正文。

Discovery、读者 development、held-out validation 和已暴露的翻译 final test 保持分离。通过验证器不等于分配了 validation 角色；文档级分区随后按固定 seed 完成，并在段落结果前记录。

## 计划中的读者使用

交接通过后：

1. 查看读者结果前冻结文档分区。
2. 用确定性格式门槛选出上下文完整的后时期段落，排除代码、图注、采访问题、依赖图的文字、作者简介及截断行。
3. 先做 12 对后时期／后时期区分校准。匹配来源、主题、体裁、篇幅与传播可见度，平衡 A/B，不展示元数据或特征身份。
4. 只询问哪段更不愿意继续阅读，提供明确无实质差异选项及可选评论。
5. 若校准多数为平局，在更大比较图之前停止，不强迫区分或提高编辑强度。
6. 若区分度足够，使每个开发段落在连通、平衡的图中比较两至三次，拟合考虑平局的 Davidson model。特征规则仍是候选生成器，不是标签。
7. 只有重复读者选择将段落置于高阻力区域时，才准入干预开发。评论不能选样。
8. 盲法原文／修订比较前，冻结保守编辑算子及原意保留审查。

读者不分类语言特征或作者身份。原意保留仍通过操作日志及确定性的命题／实体／数量／否定审查。

Held-out validation 要求独立保留区、至少三种体裁和多名独立读者。开发已暴露文档绝不能重新命名为验证材料。

## 复现

~~~powershell
python experiments/validate_post_reader_handoff.py `
  --handoff-root F:\path\to\post_reader_handoff_v1 `
  --repository-root . `
  --report feature_runs/post-reader-handoff-v1/validation_report.json
~~~

只有开发门槛通过，命令才以状态 0 退出。不得人工覆盖失败门槛以创建读者任务。

## 首个完成的交接

首个版本 1.1 交接生成于：

~~~text
F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1
~~~

包含 50 篇文档，InfoQ、美团技术博客各 25 篇。体裁为技术实践 24 篇、研究摘要八篇、行业报道 18 篇，发布日期覆盖 2025-08 至 2026-08。

验证报告零错误、一条警告：通过 36 篇开发门槛，但未达到优选的 60 篇独立验证保留区阈值。

| 产物 | SHA-256 |
|---|---|
| Manifest | `acde6900ae8b26b8da8821424be420ff48433752297c3f021e1a7e05ccfb2b14` |
| 文档索引 | `a16f73542edab7f38fb3b24b2dc19fde798b5d14dcc035adfd560bc028c6dc6d` |
| 验证报告 | `ccee95e7bdf9c3373fa782497bf60377f1445346ad62d40766a0eb685547a2ce` |


交接属于被忽略的本地研究数据，不提交 Git。Manifest 记录全部采集输入、候选流程排除、模型和 prompt 身份、来源／月份／体裁／主题构成及输出 hash。

采集和复核顺序如下：

~~~powershell
$staging = 'F:\MyProjects\DeAIodorant\data\local\post_reader_staging_v1'
$handoff = 'F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1'

python experiments/acquire_post_candidates.py `
  --output-dir "$staging\infoq" --target 100 --max-attempts 400

python experiments/acquire_meituan_post_candidates.py `
  --output-dir "$staging\meituan"

python experiments/prepare_post_review_candidates.py `
  --input "$staging\infoq\infoq_post_candidates.jsonl" `
  --input "$staging\meituan\meituan_post_candidates.jsonl" `
  --exclude-index F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\analysis_pool.jsonl `
  --output-dir "$staging\review_candidates"

python translation_benchmark_v2.py triage-review `
  --candidate-dir "$staging\review_candidates" `
  --decisions "$staging\review_candidates\no_human_decisions.csv" `
  --output-dir "$staging\triage_qwen38" `
  --model qwen3.8-27b `
  --model-digest 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab `
  --backend openai --endpoint http://192.168.1.200:8000/v1 `
  --concurrency 16 --routing-only

python translation_benchmark_v2.py triage-value `
  --candidate-dir "$staging\review_candidates" `
  --provenance-results "$staging\triage_qwen38\triage_results.jsonl" `
  --output-dir "$staging\triage_qwen38\value" `
  --model qwen3.8-27b `
  --model-digest 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab `
  --backend openai --endpoint http://192.168.1.200:8000/v1 `
  --concurrency 16

python experiments/classify_post_corpus_strata.py `
  --candidate-dir "$staging\review_candidates" `
  --provenance-results "$staging\triage_qwen38\triage_results.jsonl" `
  --value-results "$staging\triage_qwen38\value\value_results.jsonl" `
  --output-dir "$staging\strata_qwen38" `
  --model qwen3.8-27b `
  --model-digest 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab `
  --endpoint http://192.168.1.200:8000/v1 --concurrency 16

python experiments/build_post_reader_handoff.py `
  --candidate-dir "$staging\review_candidates" `
  --provenance-results "$staging\triage_qwen38\triage_results.jsonl" `
  --provenance-manifest "$staging\triage_qwen38\triage_manifest.json" `
  --value-results "$staging\triage_qwen38\value\value_results.jsonl" `
  --value-manifest "$staging\triage_qwen38\value\value_manifest.json" `
  --strata-results "$staging\strata_qwen38\strata_results.jsonl" `
  --strata-manifest "$staging\strata_qwen38\manifest.json" `
  --preparation-manifest "$staging\review_candidates\manifest.json" `
  --acquisition-manifest "$staging\infoq\manifest.json" `
  --acquisition-manifest "$staging\meituan\manifest.json" `
  --output-dir $handoff

python experiments/validate_post_reader_handoff.py `
  --handoff-root $handoff --repository-root . `
  --report "$handoff\validation_report.json"
~~~

InfoQ 采集器只发现 79 篇，未达到请求的 100 篇，因此写出暂存产物后返回非零完整性状态。合并的双来源暂存池仍有 108 篇，超过冻结的 60 条原始候选最低要求；没有静默接纳失败记录。

## 扩展的第二次交接

读者项目 5 至 7 暴露第一池多数有用文档后，生成第二次交接：

~~~text
F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v2
~~~

含五个来源的 97 篇未暴露后时期文档，验证器报告零错误、零警告。新段落分析前冻结角色分区：67 篇 development、30 篇 validation reserve。保留区覆盖三个来源、三种体裁及三个主题分层，但仍需多名独立读者才能作验证主张。

通过公开编辑或推荐页面加入量子位、雷锋网和华为云社区。准入要求本地 Qwen3.8-27B 基线与 OpenRouter 实时周使用量排名第二的已识别模型 DeepSeek V4 Flash 0731 一致。模型选择、接口 smoke test、分歧率、价值筛查、传播可见度策略、分区及完整产物身份见[多来源后时期语料扩展 v2](post-reader-corpus-expansion-v2.md)。
