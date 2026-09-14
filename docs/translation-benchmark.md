# 翻译筛选 benchmark

翻译筛选使用两个冻结的 prompt profile，采用确定性采样（`temperature=0`、`seed=42`、关闭 thinking）：

1. 严格翻译检测器；
2. 原创内容 verifier，仅在存在确定性的强原创证据时调用。

准入策略采用 fail-closed。只有严格 profile 返回 `original/high`，或存在强原创证据且 verifier 同样返回 `original/high`，文章才可通过。所有不确定、失败或格式错误的响应均被拒绝。

## 本地模型配置

```bash
ollama pull qwen3.5:9b
```

在私有 benchmark 文件上运行冻结的筛选器：

```bash
python translation_final_test.py \
  --dataset data/translation_holdout/gold.jsonl \
  --results data/qwen9b_validation_results.jsonl \
  --summary data/qwen9b_validation_summary.json \
  --model qwen3.5:9b \
  --timeout 600
```

使用 RTX 4080 或 DGX Spark 时，让模型完整驻留显存／内存，并仅使用一个进程。当前脚本按顺序评估，以保证可复现性。吞吐 benchmark 与并发生产推理应单独开展，避免改变准确性测量。

## Benchmark 数据

`init` 分支跟踪当前 `data/` 目录，用于转移到其他评估机器。目录含第三方文章正文与本地模型缓存，使用者仍须负责遵守来源权利和条款。相关目录如下：

```text
data/translation_eval/
data/translation_holdout/
data/translation_test/
data/translation_benchmark/
```

查看 final-test 预测后，不得调试 prompt 或阈值。
