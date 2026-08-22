# Translation benchmark v2 artifacts

This directory contains third-party research data and generated benchmark
construction artifacts for protocol `translation-gate-2.0-development`.

The candidate pool was generated with:

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

`candidates/review_queue.csv` is unfinished review material. Blank review
fields do not imply original status. `development_silver.jsonl` contains silver
platform labels and is restricted to prompt-development diagnostics.

No validation or sealed-test file in this directory may be used to revise a
prompt after its predictions have been inspected. See
`docs/translation-benchmark-v2.md` for the complete access policy, provenance,
rights, and split rules.
