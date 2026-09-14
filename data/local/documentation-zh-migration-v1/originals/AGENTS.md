# DeAIodorant Agent Guide

## Mission

The maintainer confirmed the current research objective on 2026-09-14 in
`docs/target-feature-discovery.md`: real full media articles such as InfoQ are
the target inputs. Discover repeatable features of the reader's subjective
AI-smell impression using adequately contrasted real-media samples before
claiming edit efficacy or advancing training. Preserve acquisition work and the
pre-2023 / post-2025-06 temporal cohorts. Old weak-sample studies are not confirmed
strong-positive evidence. Synthetic runs are retained as engineering controls.

The maintainer further clarified that the product targets both aversive style
cues and underlying reading defects. Recurrent contrastive-replacement forms
(`不是……而是……`, `并非……而是……`, and variants) are a nominated feature
family for descriptive cohort statistics. Do not equate cue counts with author
identity or reading quality, or treat normal Chinese ellipsis as a missing-SVO
error. Preserve meaning rather than inventing absent facts or premises.

The latest maintainer clarification rejects blanket translation exclusion as
the research approach. The trained refiner must improve translated Chinese
articles from Chinese input alone; an upstream English original is optional
support for research or verification. Treat original Chinese, translated,
mixed/adapted, and unresolved provenance as strata. Preserve legacy exclusions
as historical or original-only sensitivity decisions, not global research
rejections. Poor readability is part of the target, not an admission failure.

The maintainer rejected the repeated Cowork preview as an unrepresentative,
weak-style example. It may inherit English LLM problems while lacking strongly
characteristic Chinese target patterns. Do not reissue it as a readability task
or substitute generic repairability for the active strong-example discovery
problem. Translation remains in product scope, but provenance alone neither
qualifies nor disqualifies an example. Establish sustained target manifestations
in complete articles before preparing another reader task.

The maintainer has now supplied a strong positive: SMZDM Microduck article
`https://post.smzdm.com/p/a70dm4ll/`, described as `极其臭` and `恶臭`.
The Baidu article is explicitly `一般臭`. Use this source-linked human contrast
for feature discovery, without asking the same intensity questions again.
The strong article has zero literal `而是`; broader framing, parallel verdicts,
stance, and reference/support problems require context. Its publisher separately
discloses AI generation. Preserve these as different kinds of evidence, and do
not infer a model, translation process, reward mechanism, or universal rule.

The maintainer further stresses that connective substitution can leave the
rhetorical action and smell unchanged. Explain the repeated corrective/insight
framing, its semantic relationships and evidential support before designing a
measure. Merely extending keyword matching is insufficient. The title-level
`先把……算明白` observation is part of the target, not an instruction to build
a forbidden-phrase list. See `docs/routes/compact-refiner/rhetorical-mechanism-hypothesis.md`.

DeAIodorant is a Chinese-text refinement layer between content generation and
publication. Its product goal is to reduce repetitive, generic, and
recognizably machine-like writing patterns while preserving meaning, factual
content, useful detail, and authorial intent.

Optimize for reader experience, not AI-detector evasion. This project does not
classify individual documents as human- or AI-authored and must not claim that
its pre/post cohorts prove authorship for any individual document.

Corpus differences and machine-learning separability are hypothesis generators,
not the product objective. A writing pattern becomes a refinement target only
when a bounded edit improves blinded reader preference without meaning loss.

## Constitution

The following rules are non-negotiable and take precedence over local style
preferences:

1. Write all repository documentation in clear, standard English. This includes
   READMEs, design documents, research protocols, contribution guides, issue and
   pull-request templates, changelogs, and generated reports.
2. Write all code comments, docstrings, identifiers, log messages, error
   messages, configuration descriptions, and commit messages in English.
3. Use established English technical and scientific terminology consistently.
   Do not introduce literal translations or improvised terminology when a
   standard term exists.
4. Chinese text may appear verbatim when it is primary corpus material, a source
   quotation, a test fixture, a prompt example, a linguistic example, or the
   object of analysis. Keep the surrounding explanation, labels, captions, and
   interpretation in English.
5. Preserve quoted Chinese source text faithfully. Clearly distinguish source
   material from commentary, and do not silently "correct" source language in a
   way that would change research evidence.
6. When a Chinese term itself is analytically important, introduce it inside an
   English sentence and define it with precise English terminology.

## Current state

The repository contains corpus acquisition, translation and research-value
triage, human-review tooling, a deterministic non-LLM corpus-analysis CLI, and
exploratory discourse and modifier-structure experiments. Five development
editing interventions have been completed; no smell has reached independent
intervention validation. The general refinement engine, product evaluation
package, and product API are planned but not implemented. Experimental editing
and reader-evaluation scripts already exist under `experiments/`.

Use `docs/research-progress.md` and dated experiment reports for the latest
evidence and distinguish proposed next steps from frozen protocols. The
2026-09-14 reassessment concerns traditional NLP measurement and statistical
validation; it does not replace reader outcomes with model judgments.

The maintainer subsequently paused the corpus-first discovery route and chose
the compact-refiner route documented in `docs/routes/compact-refiner/`. Those
route documents govern the resumed preparation and API experiments. On
2026-09-14 the maintainer authorized autonomous progress and independent agents.
Record model-assisted experiments separately from human validation and report
when a concrete finding or necessary human/GPU input is available. SFT remains
deferred to a maintainer-provided cloud GPU.

Subsequent clarification restores target-feature discovery as the active front
half of the project. The pause applies to continuing the old low-signal selector
experiments, not to discarding temporal sampling or acquisition infrastructure.
The calibrated objective above supersedes synthetic-input or immediate-editing
next steps in historical route drafts.

Current execution context, confirmed by the maintainer on 2026-09-14:

- `gx10` / DGX Spark is unavailable; historical commands do not establish
  current hardware access.
- The local GTX 1080 is excluded from SFT for this project. The maintainer will
  provide a cloud GPU when training is ready. First specify minimum and
  recommended GPU/VRAM, host RAM/storage, compatible software, and estimated
  runtime/cost based on the selected model, sequence length, and tuning method.
  Local work covers data preparation, deterministic checks, and evaluation;
  do not start local SFT or provision a cloud training host from this instruction.
- OpenRouter is authorized for necessary inference. The root `.env` holds
  `OPENAI_API_KEY` and is ignored by Git. Existing compatible clients read the
  process environment; load the file explicitly when needed without printing
  credentials or placing them in tracked artifacts.
- This checkout lacks the historical `data/local/` handoffs. Distinguish
  inspected reports from locally reproduced results.

Important facts that must remain visible in related work:

- The primary comparison is Chinese content published before 2023-01-01 versus
  content published on or after 2025-07-01.
- The 2023-01-01 through 2025-06-30 transition period is not part of the primary
  contrast.
- Retain source integrity, editorial relevance, and visibility evidence.
  Correct dates alone do not make a useful comparison, and poor readability
  must not screen out the phenomenon being investigated.
- Translated and compiled articles remain in research with provenance strata;
  original-only views are controls. Translation is a core refinement target.
- `data/pilot/` is diagnostic pilot material, not a clean or final corpus. It
  contains known problematic examples.
- The exposed Qwen3.5-4B final translation test missed the acceptance target.
  Never tune prompts, rules, or thresholds against it.

## Repository map

- `src/deaiodorant/`: product package namespace; new reusable code belongs here.
- `src/deaiodorant/analysis/`: read-only deterministic feature extraction,
  Universal Dependencies processing, and feature metadata.
- `configs/`: versioned analysis configurations; treat a configuration as
  immutable after its feature matrix has been used for analysis.
- `pilot_collect.py`: current monolithic acquisition pilot.
- `translation_*.py`: translation benchmark construction and evaluation.
- `tests/`: automated tests.
- `data/`: tracked pilot and benchmark artifacts; treat as third-party research
  data, not as ordinary source fixtures.
- `benchmark_results/`: compact, reviewable benchmark outcomes.
- `docs/`: architecture, roadmap, and frozen research protocols.

Do not perform a broad migration of the root scripts merely to match the target
layout. Extract modules incrementally when a feature needs them, keeping command
compatibility or documenting a deliberate breaking change.

## Working rules

1. Inspect the relevant source, tests, metadata schema, and existing artifacts
   before editing.
2. Follow the language and terminology rules in the Constitution.
3. Make the smallest coherent change. Separate acquisition, analysis,
   evaluation, and refinement concerns.
4. Preserve reproducibility: record seeds, model identifiers, prompt versions,
   thresholds, source timestamps, and configuration used to produce artifacts.
5. Never silently rewrite frozen benchmark inputs or gold labels. Create a new
   version and document why.
6. Do not add a network service, model dependency, or large binary artifact
   without documenting its cost, license, and failure behavior.
7. Prefer deterministic local logic before model inference. Model-backed gates
   must be cacheable, versioned, and fail closed when used for corpus admission.
8. Do not bypass access controls, authentication, paywalls, CAPTCHAs, source
   rate limits, or explicit data-service restrictions.
9. Preserve `main` at its initialization commit. Commit current work only to
   `init` unless the maintainer explicitly authorizes a branch-policy change.
10. Do not train a human-versus-AI classifier as a proxy for refinement quality.
    Evaluate edits against unchanged text using reader preference and
    preservation gates.

## Corpus invariants

The primary monthly corpus layout is:

```text
data/<run>/monthly/YYYY-MM/
  <doc_id>.txt
  meta.jsonl
```

For every admitted document:

- store exactly one normalized UTF-8 body file;
- store exactly one matching metadata record in that month's `meta.jsonl`;
- keep stable document IDs and canonical source URLs;
- retain publication and collection timestamps;
- retain source, quality, visibility, translation, and admission evidence;
- reject missing or ambiguous publication dates from the primary comparison;
- deduplicate exact and near-duplicate content before analysis;
- never infer audience quality from length alone.

Apply provenance definitions symmetrically across time periods. Explicit
translation/compilation evidence assigns the appropriate stratum; it does not
discard the article from research. Unknown source language or process stays
unknown. The legacy original-only control remains fail-closed: deterministic
translation evidence excludes from that view, and uncertain model judgments do
not certify originality. Foreign citations or names alone do not prove
translation. Preserve all earlier benchmark inputs and labels unchanged.

## Scientific safeguards

- Match pre/post samples by source, topic, format, length, and visibility where
  practical before attributing a difference to time.
- Avoid survivorship bias from comparing old all-time popular pages with newly
  published pages using raw current view counts.
- Keep discovery, development, validation, and final-test documents disjoint.
- Freeze the analysis plan and evaluation thresholds before reading final-test
  outcomes.
- Report retention, leakage, exclusions, missingness, and source composition;
  do not report only a single aggregate score.
- Treat model-assisted labels as measurements with error, not ground truth.

## Product safeguards

Refinement features must:

- preserve propositions, named entities, quantities, citations, uncertainty,
  and negation unless the user explicitly requests content changes;
- make edits traceable through a diff or structured operation log;
- expose refinement intensity instead of applying an opaque maximum rewrite;
- avoid fabricating anecdotes, sources, personal experience, or authority;
- evaluate Chinese fluency and discourse structure directly;
- keep source text and generated variants out of logs by default.
- treat willingness to continue reading as the primary product outcome;
- keep feature distance and perceived authorship as diagnostics only;
- validate candidate smell patterns through editing interventions before
  turning them into product rules.

## Development commands

Set up the project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Run the required checks:

```powershell
python -m pytest
python -m compileall -q src pilot_collect.py translation_eval.py translation_holdout.py translation_final_test.py
```

Tests that exercise real websites or local language models must be opt-in and
clearly separated from the default offline suite.

## Documentation expectations

- Update `README.md` when user-facing scope or setup changes.
- Update `docs/architecture.md` when component boundaries or data flow change.
- Update `docs/roadmap.md` when a phase begins or meets its exit criteria.
- Update `docs/smell-catalog.md` when a smell hypothesis, metric, evidence
  status, counterexample, or intervention result changes.
- Add an explicit protocol version for benchmark policy changes.
- Document generated artifacts with the command and configuration that created
  them.

## Code review rules

Flag changes that:

- describe pilot data as a final, clean, or representative corpus;
- tune against an exposed final test or leak gold labels into model input;
- label ambiguous provenance as original, or globally discard translated
  research material under a superseded original-only policy;
- compare cohorts without accounting for source or visibility imbalance;
- optimize the product around AI-detector scores;
- optimize the product around human-versus-AI classification accuracy;
- treat a pre/post feature difference as a validated reader-disliked pattern;
- promote a smell status without recording reproduction identity, confounders,
  counterexamples, and intervention evidence;
- drop meaning-preservation checks from a refinement path;
- add scraping behavior that bypasses source restrictions;
- commit secrets, personal data, model weights, or unexplained large artifacts;
- modify `main` without explicit maintainer authorization.

When raising a concern, identify the violated invariant and suggest the smallest
safe correction.
