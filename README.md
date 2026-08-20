# DeAIodorant

DeAIodorant is a Chinese-text refinement layer for the space between generation
and publication. It aims to reduce repetitive, generic, and recognizably
machine-like writing patterns while preserving the author's meaning, factual
content, and useful detail.

In 2026, generated content is common across the Chinese internet. The problem
DeAIodorant addresses is not whether a model wrote a document, but whether the
result is worth reading. The project is designed to help creators keep the
productivity benefits of generative AI without sacrificing reader attention,
voice, or clarity.

> **Project status:** research foundation. The repository currently implements
> a corpus-acquisition pilot and a translation-content gate. It does not yet
> contain the text-refinement engine.

## Product principles

- **Chinese first.** Analyze and improve patterns specific to modern written
  Chinese instead of translating English style advice.
- **Meaning preservation.** Never trade factual content, qualifications, or the
  author's actual position for a more natural surface style.
- **Reader value over detector scores.** Evaluate clarity, specificity,
  coherence, information retention, and reader preference. DeAIodorant is not
  an AI detector and is not optimized to defeat one.
- **Evidence before heuristics.** Derive transformations from controlled corpus
  comparisons and human evaluation rather than a list of internet folklore.
- **Auditable refinement.** Keep edits inspectable and make the intensity of
  rewriting controllable.

## Research design

The primary comparison uses high-quality, high-visibility Chinese web writing
from two deliberately separated periods:

| Cohort | Publication date | Role |
|---|---:|---|
| Pre-ChatGPT baseline | before 2023-01-01 | Reference for established human-authored web writing |
| Post-adoption cohort | on or after 2025-07-01 | Reference for writing after widespread generative-AI adoption |

The intervening period is excluded from the primary contrast. Individual
documents are not classified as human- or AI-written. Both cohorts are filtered
for editorial value and audience attention; low-value filler is not useful just
because it belongs to the correct period. Translated and compiled foreign
articles are excluded from both cohorts because translation style is a major
confounder.

The intended project pipeline is:

```text
source acquisition
    -> quality, visibility, and translation gates
    -> matched pre/post corpus
    -> linguistic contrast and pattern catalog
    -> automatic and human evaluation suite
    -> Chinese refinement engine
    -> CLI/API and publishing integrations
```

See [the project roadmap](docs/roadmap.md) for phase boundaries and acceptance
criteria.

## What exists today

The current collector validates source accessibility, publication dates, body
extraction, basic quality gates, available visibility signals, and low-cost
translation filtering. The initial sources are InfoQ China and Machine Heart.

| Source | Pilot window | Acquisition route |
|---|---|---|
| InfoQ China | 2021-07 to 2022-06; 2025-07 to 2026-06 | Published sitemap and public article pages |
| Machine Heart | June 2022; current-access probe | Common Crawl WARC for historical pages |

Machine Heart currently replaces recent article pages with a data-service
notice. The collector records this state and does not attempt to bypass it.

The tracked `data/pilot/` directory is pilot material, not a clean research
corpus. It includes known problematic examples retained for evaluation and
reproducibility.

## Repository layout

```text
src/deaiodorant/            Python package namespace for the future product
pilot_collect.py            Corpus acquisition and extraction pilot
translation_eval.py         Translation-gate development-set tooling
translation_holdout.py      Validation and holdout construction
translation_final_test.py   Frozen benchmark runner
tests/                      Automated tests
data/                       Pilot corpora and benchmark artifacts
benchmark_results/          Published benchmark summaries
docs/                       Research protocol, architecture, and roadmap
```

## Setup

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

Run a small collection pilot:

```powershell
python pilot_collect.py --target-per-cell 2 --output-dir data/smoke
```

Run the full current pilot:

```powershell
python pilot_collect.py --target-per-cell 10 --output-dir data/pilot
```

## Corpus layout

Normalized article bodies are stored as UTF-8 text with one metadata file per
publication month:

```text
data/pilot/monthly/
  2022-06/
    <doc_id>.txt
    meta.jsonl
  2025-09/
    <doc_id>.txt
    meta.jsonl
```

Each line in `meta.jsonl` maps to one body through its `text_file` field. New
collection work must preserve source URL, publication timestamp, collection
timestamp, source, quality signals, visibility signals, and filter decisions.

## Translation gate

Explicit translation metadata is rejected deterministically. In ambiguous
cases, the optional local classifier is fail-closed: only a high-confidence
`original` decision may enter the formal corpus. It judges translation status,
not AI authorship.

```powershell
python pilot_collect.py --translation-model qwen3.5:4b
```

The Qwen3.5-4B frozen final test did not meet the target: it retained 56% of
originals and admitted 2% of translations. Do not tune against that exposed
test. See [the translation benchmark protocol](docs/translation-benchmark.md)
for the current 9B validation procedure.

## Data and rights

This repository contains third-party article bodies for research transfer and
reproducibility. Their presence does not grant a license to republish, train on,
or commercially use them. Contributors are responsible for source terms,
copyright, privacy, robots directives, rate limits, and takedown requests. A
production corpus should prefer references and reproducible acquisition
manifests over redistributing full text when rights are unclear.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the repository instructions in
[AGENTS.md](AGENTS.md) before making changes. The `main` branch is intentionally
untouched beyond its initialization commit; current development belongs on
`init` until the maintainer explicitly changes that policy.
