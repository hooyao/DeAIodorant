# Project Roadmap

The product objective is reader-preferred Chinese refinement, not AI-text
classification. Corpus research and product evaluation therefore proceed in
parallel rather than as a strict sequence.

Alternative technical routes, minimum experiments, hardware mapping, and
decision rules are defined in
[DeAIodorant Refinement Roadmap](refinement-roadmap.md).

## Milestone 0: Repository foundation

Status: complete.

Deliverables:

- project instructions and contribution workflow;
- Python package metadata and CI;
- architecture, data boundaries, and branch policy;
- deterministic feature extraction and provenance manifests.

## Workstream A: Corpus-based hypothesis discovery

Owner: the corpus-preparation workflow running independently on the DGX Spark.

Purpose:

- collect high-quality, high-visibility pre-2023 and post-2025-06 Chinese text;
- exclude translated and compiled foreign content;
- match source, topic, format, length, and visibility where possible;
- extract interpretable and sparse linguistic features;
- produce candidate writing-pattern hypotheses.

This workstream does not determine what readers dislike. A corpus difference
becomes a product candidate only after an editing intervention improves blinded
reader preference.

## Workstream B: Reader benchmark

Status: immediate next work.

This workstream does not wait for the large corpus.

Deliverables:

- 20 passages across at least three genres;
- unchanged inputs and 5–10 careful human edits;
- locked fact, entity, number, citation, negation, and modality fields;
- blinded pairwise preference questions;
- span-level notes about irritating passages and accepted edits.

Exit criteria:

- rating questions are understandable;
- readers can identify meaningful quality differences without guessing
  authorship;
- preservation failures can be recorded separately from style preference.

## Milestone 1: Smell hypothesis catalog

Inputs:

- corpus feature differences;
- direct editor observations;
- reader-highlighted spans;
- recurring rejected and accepted edits.

Each hypothesis records:

- a precise description;
- detector or locator;
- proposed edit operations;
- positive examples and counterexamples;
- known genre and source confounders;
- reader-intervention result;
- preservation risks.

The canonical records and their evidence status are maintained in
[Chinese Writing Smell Catalog](smell-catalog.md).

Exit criterion:

At least three smell categories have evidence that a bounded edit improves
reader preference without meaning loss.

## Milestone 2: Baseline route comparison

Run on the same 20 passages:

1. unchanged input;
2. high-precision deterministic rules;
3. one frozen prompt-only rewrite;
4. targeted span rewriting;
5. human edit on the upper-bound subset.

Measure:

- blinded reading preference;
- meaning and factual preservation;
- edit size;
- latency, memory, and throughput;
- failure and fallback rate.

Exit criterion:

Select the simplest approach that produces a reproducible preference gain while
passing preservation gates.

## Milestone 3: Hybrid refinement MVP

Recommended architecture:

~~~text
deterministic span analysis
    -> explicit edit plan
    -> bounded local rewrite
    -> preservation checks
    -> accept or revert each operation
    -> inspectable diff
~~~

Deliverables:

- low, medium, and high refinement intensity;
- operation reason codes;
- locked-content support;
- deterministic fallback to the original;
- batch CLI;
- human accept, reject, modify, and revert events.

Exit criteria:

- improved blinded reader preference over unchanged text;
- better preservation than prompt-only full-document rewriting;
- no critical fact, number, entity, citation, negation, or modality changes;
- every edit can be inspected and reverted.

## Milestone 4: Candidate generation and reranking

Add only if several candidates materially improve the MVP.

Deliverables:

- bounded candidate generation;
- deterministic preservation rejection;
- feature and edit-size diagnostics;
- human-selected candidate benchmark;
- optional small preference reranker.

Exit criterion:

Automatic selection approaches human candidate choice without increasing
meaning failures enough to outweigh the quality gain.

## Milestone 5: Data flywheel

Collect:

- original generated draft;
- proposed operation and candidate;
- accepted, rejected, modified, or reverted result;
- reason code and genre;
- preservation-check outcome;
- optional blinded preference.

Private text is excluded from logs by default. Training use requires explicit
rights and retention policy.

Exit criterion:

Enough reliable paired edits exist to justify a learned editor. A raw pre/post
corpus is not a substitute for paired editing data.

## Milestone 6: Learned compact refiner

Candidate methods:

- supervised LoRA or QLoRA;
- edit-operation prediction;
- encoder-decoder editing;
- teacher generation with human review;
- preference optimization;
- distillation into a production-sized model.

Start with supervised accepted edits. Add preference optimization only after
pairwise feedback is large and stable.

Exit criteria:

- match or exceed the hybrid MVP on reader preference;
- pass the same preservation gates;
- reduce latency or operating cost;
- remain stable across genres and refinement intensities.

## Milestone 7: Product interfaces

Deliverables:

- stable local API and service contract;
- editor or publishing integration;
- diff review and per-edit controls;
- privacy, retention, observability, and rollback policies;
- backend-independent configuration.

Exit criteria:

- all interfaces use the same evaluation and preservation contract;
- private text is not logged by default;
- deployments can be rolled back safely;
- model or rule updates cannot bypass quality gates.

## Standing non-goals

- classifying individual documents as human or AI;
- optimizing against commercial AI detectors;
- assuming every pre/post corpus difference is undesirable;
- fabricating voice, anecdotes, facts, citations, or personal experience;
- using unreviewed synthetic rewrites as gold training data;
- making the large corpus a prerequisite for small reader experiments.
