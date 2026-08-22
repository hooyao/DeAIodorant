# Translation gate benchmark v2

## Status and purpose

Protocol `translation-gate-2.0-development` replaces the single-source,
small-sample development workflow with a larger, source-diverse benchmark
lifecycle. It is not frozen and has not produced a final-test result.

The task is translation provenance classification. It does not classify AI
authorship. A document is admitted only when it is confidently original under
the fail-closed decision policy.

## Non-negotiable split policy

- Prompt text and rules may be changed only after inspecting development data.
- Validation labels may be used to select among prompt versions that were
  already fixed on development data. Validation errors must not be converted
  into new same-cycle prompt rules.
- The sealed test must not be run until the prompt, model digest, decoding
  configuration, decision policy, and thresholds are frozen.
- A sealed-test failure may motivate a new protocol version and new disjoint
  test, but it may not be used to repair the version that produced the failure.
- The exposed v1 final test is permanently excluded from v2 construction and
  tuning.

## Sources

### InfoQ China

The collector uses published sitemaps and public article pages at a conservative
rate. An explicit translator field is deterministic translation evidence.
Original candidates require a Chinese byline, no translation marker, and a
Chinese reporting, interview, event, or first-party project signal. They still
require review before becoming original gold.

The v2 collector prioritizes the 2023-01-01 through 2025-06-30 transition
period, which is excluded from the primary pre/post corpus contrast.

### Machine Heart

Historical pages are retrieved from Common Crawl WARC records. The page-level
article type `翻译` or `编译` is deterministic translation evidence. The
article type `原创` creates an original candidate only; it is not sufficient
gold by itself because platform labels can conflict with body-level foreign
source evidence.

Current Machine Heart pages remain behind a data-service notice. The collector
does not bypass it.

### LCTT

LCTT is the former Linux China translation project. Published Markdown files
provide translator, reviewer, foreign author, and original URL metadata. The
repository is Apache-2.0 licensed. Collection is pinned to a Git commit and
uses only selected raw files rather than cloning the full repository.

LCTT translations are eligible for development only. Validation and sealed
test are restricted to sources that provide both translation and original
candidates, preventing a source name from becoming a perfect label proxy.

The xitu/gold-miner repository was considered but excluded from body
acquisition because it has no repository-level license and describes its
translations as limited to study, research, and exchange.

## Candidate and label tiers

| Tier | Meaning | Allowed use |
|---|---|---|
| Deterministic translation | Explicit translator, translation/compilation article type, or pinned LCTT publication metadata | Development, validation, sealed test |
| Reviewed original | Reviewer confirms Chinese reporting, interview, first-party practice, or independent synthesis and finds no specific translated foreign work | Development, validation, sealed test |
| Silver platform original | Platform says `原创`, but no human review exists | Development diagnostics only |
| Pending review | Candidate signals are present but no decision exists | No model comparison or release claim |

Model-assisted review is a measurement, not human gold. Its provenance must be
recorded in the `reviewer` field and reported separately.

## Leakage control

Before admission to a candidate pool, every document is compared against all
v1 development, validation, exposed-final, pilot, and smoke records by:

1. stable document ID;
2. canonical URL;
3. exact normalized-body hash;
4. character-shingle near-duplicate detection.

Split construction checks document IDs, URLs, and content hashes again. The
split seed is the protocol version.

## Current candidate pool

The initial v2 collection produced 440 candidates:

| Source | Translation | Original pending review | Total |
|---|---:|---:|---:|
| InfoQ China | 80 | 100 | 180 |
| Machine Heart | 40 | 120 | 160 |
| LCTT | 100 | 0 | 100 |
| Total | 220 | 220 | 440 |

The generated review queue is not a completed gold dataset. The current
160-document silver development artifact is explicitly diagnostic and must not
be reported as validation or final evidence.

## Commands

Collect candidates:

```powershell
.\.venv\Scripts\python.exe translation_benchmark_v2.py collect `
  --output-dir data\translation_v2\candidates `
  --infoq-translations 80 --infoq-originals 100 `
  --jiqizhixin-translations 40 --jiqizhixin-originals 120 `
  --lctt-translations 100
```

Generate the diagnostic silver development set:

```powershell
.\.venv\Scripts\python.exe translation_benchmark_v2.py bootstrap-development
```

### Local human-review workspace

Use the local review launcher instead of reading embedded JSONL bodies or
editing the candidate queue directly:

```powershell
.\scripts\run-translation-review.ps1 -Reviewer <stable-reviewer-id>
```

The command performs the following reproducible steps:

1. selects only `original_pending_review` records;
2. writes each source body unchanged to
   `data/local/translation_v2_review/texts/<source>/<doc_id>.txt`;
3. records the input hashes and review configuration in a workspace manifest;
4. provisions Label Studio Community Edition 1.23.0 in an isolated local
   environment;
5. creates the project and imports all pending records once; and
6. opens the browser-based reading and classification interface.

The interface shows the full body, title, source, publication date, document
ID, candidate evidence, and source link together. A reviewer selects either
`Reviewed original` or `Exclude or uncertain`, then supplies a structured
rationale and optional notes. Keyboard shortcuts `1` through `9` select the
decision and provenance rationale. Shortcut `0` records a separate exclusion
for low research value or primarily promotional material; it is not treated as
translation evidence. Uncertainty must use the exclusion path.

Label Studio Community Edition is Apache-2.0 software. The isolated Windows
runtime currently uses approximately 700 MiB. The service binds only to
`127.0.0.1`; credentials, database, logs, raw text, task JSON, and a complete
dependency snapshot remain under the ignored `data/local/` workspace. If the
runtime or service is unavailable, review stops and no automatic decision is
created. The original candidate JSONL and frozen labels are never rewritten.
Analytics, frontend and backend Sentry, version checks, and online feature
flags are disabled so source text and review decisions remain local.
The loopback-only service forces a persistent 14-day login cookie because
embedded browser sessions may discard non-persistent cookies while a labeling
page remains open, causing annotation submissions to return HTTP 401.

### Model-assisted triage

Protocol `translation-review-triage-1.1` reduces repetitive human review
without converting model output into human gold. First export the currently
submitted annotations, then run and publish triage:

```powershell
.\scripts\export-translation-review.ps1 -Reviewer <stable-reviewer-id>
.\scripts\run-dgx-qwen38-review-triage.ps1
```

The current triage configuration is deterministic and cacheable:

- model: `Qwen3.8-27B` in BF16 on the DGX Spark GB10;
- serving runtime: NVIDIA vLLM 26.04 with batch/concurrency `16`;
- model configuration SHA-256:
  `191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`;
- temperature: `0`;
- seed: `42`;
- foreign-source safeguard:
  `translation-review-triage-foreign-source-safeguard-v2`; and
- normal/retry output budgets: `320`/`512` tokens, with a second parse failure
  mapped to `uncertain/low`.

A submitted human decision always takes precedence. Remaining records are
operationally routed when the foreign-source safeguard produces a
high-confidence source-language judgment. The current routing-only run does not
execute the older primary and verifier profiles. The safeguard explicitly prevents domestic
Chinese interviews, speeches, conferences, first-party practice, and Chinese
research interpretation from being excluded merely because they use the
Chinese marker `整理` (edited/compiled) or contain English paper links. It only
confirms an exclusion when the evidence establishes a specific non-Chinese
source work. Any disagreement or weaker result remains `uncertain` and is
copied into a separate Label Studio project for human review.

The current run preserved 11 submitted human originals and 3 human exclusions,
routed 175 documents as model-assisted originals, routed 31 as model-assisted exclusions,
and left no unresolved records. The earlier 83-document review project remains
available as an optional human spot-check surface and contains 5 preserved
submissions. These counts are operational triage results, not
benchmark accuracy evidence. The full manifest, caches, evidence, and
per-status artifacts are under `data/local/translation_v2_review/triage_qwen38/`.

Research value is a separate measurement under protocol
`research-value-triage-1.0`. Two Qwen3.8-27B BF16 profiles,
`research-value-primary-v3` and `research-value-verifier-v3`, must agree at high
confidence. Of 186 provenance-eligible documents, 110 were routed as
substantive, 51 as low value or promotional, and 25 remained uncertain. The 25
uncertain documents are in Label Studio project 3 with a dedicated quality
interface. Human review of that project is complete: 9 documents were kept and
16 were excluded for low research value. Export its submitted decisions with:

```powershell
.\scripts\export-research-value-review.ps1 -Reviewer <stable-reviewer-id>
```

The DGX runtime loaded approximately 50.22 GiB of model memory. The NVIDIA vLLM
container is governed by NVIDIA's software license terms; model redistribution
must be checked against the model card. If the remote service, structured
output, or connection fails, caches preserve completed measurements and the
record remains uncertain rather than being silently admitted.

### Transition-period reader observation

A reviewer reported strong machine-like stylistic patterns in the July 2023
article titled `安卓手机上跑15亿参数大模型，12秒不到就推理完了`, while many other
2023–2024 articles retained conventional editorial style. This is recorded as
a diagnostic reader-perception observation, not an authorship label.

The observation reinforces the frozen cohort policy: material published from
2023-01-01 through 2025-06-30 is heterogeneous transition-period evidence and
is excluded from the primary temporal contrast. It may support exploratory
pattern discovery and evaluation design, but it must not be used to claim that
an individual article was AI-authored. Pre-2023 and post-2025-06 cohorts measure
changes in stylistic-pattern prevalence; they do not prove individual
authorship.

After reviewing the uncertain project, export and merge only the submitted
human decisions from both Label Studio projects:

```powershell
.\scripts\export-translation-triage-review.ps1 -Reviewer <stable-reviewer-id>
```

The merged CSV contains no model-assisted decisions. The interface also offers
`Low research value or promotional material` as a separate exclusion rationale;
it records a benchmark-quality exclusion and is not translation evidence.

Export current decisions in the benchmark CSV schema:

```powershell
.\scripts\export-translation-review.ps1 -Reviewer <stable-reviewer-id>
```

The export contains `review_include`, `review_gold_label`, `reviewer`,
`reviewed_at`, and `review_notes`. Unreviewed rows remain blank and are ignored
by finalization. Stop the service without deleting review data with:

```powershell
.\scripts\stop-translation-review.ps1
```

Finalization fails closed when reviewed originals or balanced source cells are
insufficient:

```powershell
.\.venv\Scripts\python.exe translation_benchmark_v2.py finalize `
  --decisions data\local\translation_v2_review\review_decisions.csv
```

Default finalized sizes are 160 development documents, 80 validation
documents, and 100 sealed-test documents, balanced by label. Finalization only
creates artifacts and hashes; it does not run the sealed test.

## Diagnostic model result

Qwen3.8-27B BF16 was run only on the silver development artifact. After
deterministic body-marker cleanup, the current v1 prompt admitted 76 of 80
silver originals and zero of 80 deterministic translations. Review showed that
the four rejected `原创` pages were themselves foreign-source translations or
compilations, so this result does not justify relaxing the prompt. The labels
must be reviewed before prompt optimization resumes.
