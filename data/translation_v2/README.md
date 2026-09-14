# 翻译 benchmark v2 产物

本目录包含 protocol `translation-gate-2.0-development` 所使用的第三方研究数据，以及生成的 benchmark 构建产物。

候选池由以下命令生成：

```powershell
.\.venv\Scripts\python.exe translation_benchmark_v2.py collect `
  --output-dir data\translation_v2\candidates `
  --infoq-translations 80 --infoq-originals 100 `
  --infoq-max-attempts 2500 `
  --jiqizhixin-translations 40 --jiqizhixin-originals 120 `
  --jiqizhixin-max-attempts 1600 `
  --lctt-translations 100 `
  --delay 0.12 --http-timeout 60
```

`candidates/review_queue.csv` 是尚未完成的复核材料，复核字段为空不代表原创。`development_silver.jsonl` 包含平台提供的 silver labels，仅限用于 prompt 开发诊断。

本目录中的任何 validation 或 sealed-test 文件，一旦其预测已被查看，就不得再用于修改 prompt。完整访问策略、来源、权利及 split 规则参见 `docs/translation-benchmark-v2.md`。
