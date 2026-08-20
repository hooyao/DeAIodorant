# Chinese Web Corpus Pilot

This repository contains a small, reproducible acquisition pilot for a study of
high-quality, high-visibility Chinese web writing before and after widespread
adoption of generative AI.

The pilot intentionally does **not** classify individual documents as human- or
AI-written. It validates source accessibility, publication dates, body
extraction, basic quality gates, and available visibility signals.

## Pilot cells

| Source | PRE window | POST window | Acquisition route |
|---|---|---|---|
| InfoQ China | 2021-07-01 to 2022-06-30 | 2025-07-01 to 2026-06-30 | Published sitemap + public article pages |
| Machine Heart | June 2022 | July 2025 onward probe | Common Crawl WARC for historical pages; current accessibility probe only |

Machine Heart currently replaces article pages with a data-service notice. The
collector records this state and does not attempt to bypass it.

## Run

```powershell
python pilot_collect.py --target-per-cell 10 --output-dir data/pilot
```

For a faster smoke test:

```powershell
python pilot_collect.py --target-per-cell 2 --output-dir data/smoke
```

Generated files include one JSONL file per source/period, a merged corpus,
`manual_review_queue.csv`, and `report.json`. The `init` branch currently also
tracks the generated `data/` directory for project transfer and reproducibility.
It includes third-party article bodies; users remain responsible for source
rights and terms.

The primary corpus layout is monthly:

```text
data/pilot/monthly/
  2022-06/
    <doc_id>.txt
    meta.jsonl
  2025-09/
    <doc_id>.txt
    meta.jsonl
```

Each UTF-8 text file contains one normalized article body. Each monthly
`meta.jsonl` contains exactly one metadata record per text file; the `text_file`
field provides the mapping.

## Quality and visibility

The automated quality gate checks only extraction failures, minimum Chinese
content length, and excessive repeated lines. It does not use perplexity, an AI
detector, or an LLM style score.

Documents explicitly marked as translated are excluded in every period. InfoQ
uses its structured translator field; Machine Heart uses the article-type label
(`翻译` or `编译`). Translation quality is not considered: the presence of an
explicit translation label is sufficient for exclusion.

An optional second layer can use a local 8B 4-bit Ollama model only when the
rules are inconclusive:

```powershell
python pilot_collect.py --translation-model qwen3.5:4b
```

Qwen3.5-4B is used in non-thinking mode with Q4_K_M local quantization. The
classifier receives only the title, byline, first 600 characters, and last 1200
characters. It does not judge AI authorship. Results are cached locally. The
filter is fail-closed: only `original` with `high` confidence is admitted;
`translation`, `uncertain`, medium/low confidence, and malformed results are
excluded from the formal corpus.

For bulk filtering, run one model instance and submit 8 concurrent requests
first, then benchmark 16. Concurrent requests allow the inference server to
batch prefill work without loading multiple model copies. The classification
response is capped at 160 tokens in the pilot and should be reduced further
after prompt validation.

See [docs/translation-benchmark.md](docs/translation-benchmark.md) for the
frozen translation-gate protocol and commands for running the 9B comparison on
an RTX 4080 or DGX Spark.

InfoQ exposes a page-view count in its server-rendered state. The pilot gathers
twice the requested number of eligible candidates and retains those with the
highest observed views. View counts are current snapshots, so they are useful
for accessibility validation but not yet a historically age-normalized metric.

Machine Heart historical WARC pages do not expose a reliable attention signal.
They therefore remain an auxiliary sample until an authorized visibility source
is available.
