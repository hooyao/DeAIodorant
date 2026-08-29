# Multi-Source Post Corpus Expansion v2

## Status

The expanded handoff was generated on 2026-08-30 and passed the frozen
`post-reader-corpus-handoff-1.1` validator with zero errors and zero warnings.
It is local research data, not a final or representative corpus.

~~~text
F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v2
~~~

The handoff contains 97 documents published on or after 2025-07-01. It replaces
neither the first handoff nor any tracked corpus artifact.

## Acquisition expansion

The first handoff contained only 50 documents from InfoQ and the Meituan
technical blog. Twenty-nine document identities later appeared in reader
development artifacts, leaving only 21 documents eligible for further
development use.

The second acquisition stage added three public sources:

- QbitAI through its public WordPress API and official RSS feed;
- Leiphone through public editorial category pages, its sitemap, and live
  article pages;
- Huawei Cloud Community through public recommendation pages, article-level
  view snapshots, and live article pages.

QbitAI and Leiphone produced 219 raw records: 99 and 120 respectively. The
QbitAI public API returned one page of 100 records; one failed the deterministic
minimum body gate, so the requested 120-record target was not silently reported
as complete. Deterministic translation evidence excluded 46 records and
cross-corpus near-duplicate checks excluded two, leaving 171 for model review.

Huawei acquisition scanned 30 public recommendation pages, found 280
topic-relevant entries, and materialized the first 100 complete records that
passed the deterministic body gate. The topic expression was only an acquisition
aid and did not assign final strata.

No access control, login, paywall, CAPTCHA, or source restriction was bypassed.

## Current-model selection

Model selection did not use remembered popularity. A public OpenRouter ranking
snapshot was captured immediately before review. Its declared metric was weekly
token usage, not task quality. The first four positions were:

1. Ox Alpha;
2. DeepSeek V4 Flash 0731;
3. MiMo-V2.5;
4. Hy3.

Ox Alpha was excluded because its identity was opaque. The other three were
confirmed live in the OpenRouter model catalog and tested on the same real
candidate with the frozen structured-output schema. DeepSeek V4 Flash 0731
returned a compliant result. MiMo-V2.5 and Hy3 returned no answer content, so
they were recorded as interface smoke failures and were not batch-run.

The two batch measurements were therefore:

- `qwen3.8-27b`, the existing local baseline, served in BF16 on `gx10`;
- `deepseek/deepseek-v4-flash-0731`, the highest-ranked identified model that
  passed the task-specific OpenRouter smoke test.

The OpenRouter key was read from an ignored `.env` file into process memory. It
was not copied to `gx10`, written to an artifact, printed, or committed.

## Fail-closed two-model review

Each model applied the same frozen foreign-source safeguard. A document could
continue only when both independently returned high-confidence `original`.
Every disagreement and uncertainty failed closed.

For QbitAI and Leiphone, exact source-status agreement was 135/171 (78.9%). The
models agreed on 131 originals. Qwen marked 19 records original that DeepSeek
excluded, demonstrating that a single Qwen gate would have been materially more
permissive.

Both models then applied the existing two-prompt research-value protocol. A
document continued only when both models' internal primary/verifier agreement
was `substantive` and the cross-model decisions also agreed. Exact value-status
agreement was 70/131 (53.4%), leaving 54 documents. High-confidence strata
retained 53: 40 Leiphone and 13 QbitAI.

For Huawei, source-status agreement was 82/100. The research-value stage retained
36 cross-model substantive documents. Article views were converted to
source-quarter percentiles over the 100 acquired recommended records; the
frozen 0.40 minimum retained 23 documents. This avoids applying one raw view
threshold across publication ages, but remains a collection-time visibility
measurement.

Model results are measurements, not human gold. Cross-model agreement supports
conservative routing and does not establish accuracy.

## Final composition and partition

The 97-document handoff contains:

| Dimension | Counts |
|---|---|
| Sources | Leiphone 40; Huawei 23; QbitAI 13; Meituan 11; InfoQ 10 |
| Formats | Industry reporting 43; technical practice 36; research summary 18 |
| Topics | AI/models/agents 59; business/industry 22; data infrastructure 13; software engineering 3 |
| Roles | Development 67; validation reserve 30 |

The 21 retained first-handoff documents had already entered deterministic
feature scans, so all are development-only. The 76 new admitted documents were
partitioned before any new paragraph analysis. A fixed hash seed selected a
30-document reserve with frozen topic quotas: 16 AI/models/agents, seven
business/industry, and seven data infrastructure. The reserve contains all
three formats: 14 industry-reporting, 10 technical-practice, and six
research-summary documents.

The reserve has not been used for paragraph extraction, feature discovery, or
reader tasks. Multiple independent readers are still required before it can
support validation claims.

## Narrow-hypothesis result

The frozen head-final modifier rule was applied only to the 67-document
development partition. It found 23 broad delayed-head candidates across 14
documents and zero strict low-anchor abstract-modifier stacks. The reserve was
not read.

The reader-localized `AI 原生时代全新算力服务需求` motif therefore remains a
clear single case but did not replicate in the expanded development material.
No new Label Studio task should be created by relaxing the rule against these
outcomes.

## Reproduction artifacts

The acquisition, comparison, partition, and validation scripts are:

- `experiments/acquire_editorial_post_candidates.py`;
- `experiments/acquire_huawei_post_candidates.py`;
- `experiments/snapshot_openrouter_rankings.py`;
- `experiments/compare_provenance_models.py`;
- `experiments/compare_value_models.py`;
- `experiments/build_expanded_post_reader_handoff.py`;
- `experiments/validate_post_reader_handoff.py`.

The local handoff identity is:

| Artifact | SHA-256 |
|---|---|
| Manifest | `ecab7336c2ca54f59d24b79bcb841f0d3f4085a9c80a117f5a3ea0e31fec5d01` |
| Documents index | `096a4e42a947c1cc7e60c17b0b91251fd83579e682bdf8ea7bb0e15aed3fbd80` |
| Validation report | `64d42f47c29a52e61faf53aacd80fb16efdb89f1bd06bc7cce571737cf0483e7` |
| OpenRouter ranking snapshot | `abbdc3216fe27f82cc5354843f7f198db743d63b45d7e7702cee06bcd0090c5a` |

All source bodies, model caches, disagreements, ranking snapshots, and generated
handoffs remain ignored local artifacts. No corpus body or model output is
committed.
