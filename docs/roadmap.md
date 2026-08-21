# Project Roadmap

The phases below are ordered by dependency, not by calendar date. A phase is
complete only when its exit criteria are met.

## Phase 0: Repository foundation

Deliverables:

- project instructions and contribution workflow;
- standard Python package metadata and offline CI;
- documented architecture, research boundaries, and branch policy.

Exit criteria:

- a clean environment can install the project and run the test suite;
- agents and contributors can distinguish pilot data from final corpus data.

## Phase 1: Trustworthy corpus

Deliverables:

- reproducible source manifests for pre-2023 and post-2025-06 Chinese content;
- quality and visibility rules appropriate to each source;
- translation, language, and near-duplicate filters;
- source/topic/format matching and bias reports;
- a new, disjoint final benchmark for any revised translation gate.

Exit criteria:

- original-content retention is at least 80% with zero known translation
  admissions on a frozen, disjoint final test;
- monthly corpus files and metadata pass integrity checks;
- cohort composition and exclusions are reviewable and reproducible;
- redistribution rights or reference-only handling are documented per source.

## Phase 2: Chinese writing-pattern analysis

Current status: deterministic document-feature extraction and a versioned v1
feature catalog exist. Statistical comparison and formal corpus-dependent
results remain pending.

Deliverables:

- preregistered feature families covering vocabulary, syntax, discourse,
  paragraph structure, rhetoric, specificity, and repetition;
- matched-cohort effect estimates with uncertainty;
- confounder and source-ablation analyses;
- a versioned pattern catalog with positive and counterexamples.

Exit criteria:

- findings replicate across held-out sources or topics;
- every candidate pattern has a measurable definition and documented failure
  modes;
- no conclusion depends only on an AI-detector score or subjective "AI smell."

## Phase 3: Evaluation harness

Deliverables:

- meaning-preservation tests for propositions, entities, numbers, dates,
  citations, negation, and modality;
- Chinese fluency, specificity, repetition, and coherence measures;
- blinded pairwise reader-evaluation protocol;
- latency and cost benchmarks for supported refinement backends.

Exit criteria:

- evaluation datasets are split into development, validation, and frozen final
  tests;
- human ratings have documented sampling and agreement procedures;
- quality regressions block product releases.

## Phase 4: Refinement engine MVP

Deliverables:

- structured diagnosis and edit plan;
- controllable low/medium/high refinement intensity;
- constrained rewriting with inspectable diffs;
- semantic and factual verification with safe fallback to the original text;
- batch-oriented CLI.

Exit criteria:

- the frozen evaluation shows improved reader preference without material
  meaning loss;
- failure or uncertainty preserves the original rather than emitting an
  unverified rewrite;
- every edit can be inspected and reverted.

## Phase 5: Product interfaces

Deliverables:

- stable local API and service contract;
- publishing-system integrations;
- privacy controls, observability, rate limits, and operational documentation;
- model/backend configuration without coupling product semantics to one model.

Exit criteria:

- interfaces share the same evaluation and verification contract;
- private text is excluded from logs by default;
- deployment, rollback, and data-retention behavior are documented.

## Out of scope

- proving whether an individual document was written by a human or a model;
- optimizing against commercial AI detectors;
- fabricating personal voice, experience, citations, or authority;
- bypassing source access restrictions to assemble the corpus.
