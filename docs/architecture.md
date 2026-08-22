# Architecture

## System purpose

DeAIodorant refines generated Chinese text before publication. It is intended to
reduce repetitive structure, generic exposition, formulaic transitions, and
other patterns that weaken reader engagement while preserving the document's
meaning and useful information.

The system is organized around evidence and evaluation. Corpus acquisition is a
supporting subsystem, not the product itself.

## Target component model

```text
Acquisition adapters
    -> normalized document store
    -> quality / visibility / translation gates
    -> matched corpus builder
    -> linguistic analysis and smell hypotheses
    -> minimal editing interventions
    -> blinded reader preference
    -> validated edit-operation catalog
    -> refinement planner
    -> constrained Chinese rewriter
    -> semantic and factual verification
    -> CLI / API / publishing adapters
```

### Acquisition adapters

Retrieve only publicly or lawfully accessible documents at conservative rates.
Each adapter emits a shared metadata schema and preserves source provenance.
Adapters do not make claims about AI authorship.

The Windows local entry point is `scripts/run-corpus-pipeline.ps1`. It
bootstraps `.venv` and delegates orchestration to
`deaiodorant.corpus.pipeline`, which records the environment and configuration,
runs the existing root collector without migrating it, and invokes the corpus
integrity validator. Generated `data/local/` runs remain diagnostic pilot
material until manual review, matching, rights review, and all Phase 1 gates
are complete.

### Corpus gates

Quality, visibility, provenance, deduplication, language, and translation gates
construct comparable pre-2023 and post-2025-06 cohorts. Gates must expose both
their decision and supporting evidence. Admission policy is deterministic where
possible and fail-closed where uncertainty would contaminate the comparison.

Translation-benchmark candidates requiring human judgment are materialized in
an ignored local Label Studio workspace. The review service reads derived task
JSON and stores annotations in its local database; an explicit converter emits
the benchmark review CSV. It never rewrites candidate JSONL or deterministic
translation labels. Service failure leaves rows unreviewed rather than making
an admission decision.

An optional local triage stage runs only after existing human annotations are
exported. Human decisions take precedence. A versioned foreign-source safeguard
routes only high-confidence source-language judgments. Optional primary and
verifier profiles may be retained as supporting measurements but are not run by
the current routing-only protocol. The safeguard verifies that
an exclusion is specifically supported by non-Chinese source material,
preventing the Chinese marker `整理` (edited/compiled) on domestic speeches or
interviews from being treated as foreign compilation. Model-assisted originals
and exclusions remain separate diagnostic artifacts; only uncertain records
are copied to a second human-review project.

Research value is measured in a separate stage so promotion and information
thinness are not mislabeled as translation evidence. Two independent value
profiles must agree at high confidence; disagreements are copied to a dedicated
quality-review project.

### Matched corpus builder

Balances source, topic, document format, length, publication age, and available
attention signals. Its output supports population-level contrast; it is not a
classifier training set for labeling arbitrary documents as human or AI.

### Pattern catalog

Stores measurable Chinese writing phenomena with examples, extraction logic,
confounders, and observed effect sizes. A pattern becomes a product rule only
after a bounded editing intervention improves blinded reader preference without
meaning loss. Corpus separation alone is insufficient.

### Reader evaluation

Uses the same source passage across unchanged, rule-edited, model-edited, and
human-edited variants. The primary outcome is willingness to continue reading,
not perceived authorship. Preservation failures are recorded separately from
style preference.

### Deterministic feature package

`deaiodorant.analysis` is a read-only consumer of prepared corpora. It validates
cohort dates and content hashes and converts direct text measurements plus fixed
CoNLL-U annotations into a self-describing document-feature matrix. Statistical
comparison is deliberately outside the current component boundary. The feature
path contains no LLM calls. Syntax-model provenance, input fingerprints,
configuration, seeds, and output hashes are recorded in immutable manifests.

### Refinement engine

Separates diagnosis, edit planning, rewriting, and verification. The engine
should support multiple backends while keeping backend-specific prompting
outside the domain model. Every operation records its target span, intent, and
before/after representation so changes can be inspected or reverted.

### Verification

Checks preservation of named entities, numbers, dates, citations, negation,
modality, and key propositions. Fluency improvements do not override a failed
meaning-preservation check.

### Interfaces

The first interface should be a deterministic CLI suitable for batch evaluation.
An API and publishing integrations follow only after the evaluation contract is
stable.

## Package direction

New reusable modules should live under `src/deaiodorant/` with these eventual
boundaries:

```text
deaiodorant.corpus       schemas, normalization, matching, and gates
deaiodorant.analysis     feature extraction and contrast reports
deaiodorant.refine       diagnosis, planning, rewriting, and verification
deaiodorant.eval         automatic metrics and human-evaluation manifests
deaiodorant.cli          local command-line interface
```

The current root scripts remain operational research entry points. Move logic
out of them incrementally rather than performing a disruptive bulk rewrite.

## Cross-cutting constraints

- UTF-8 is the canonical encoding.
- Inputs and generated variants are private by default and should not appear in
  application logs.
- Model calls are replaceable, versioned, cached where appropriate, and bounded
  by explicit timeouts.
- Offline deterministic tests remain the default suite.
- Dataset and benchmark versions are immutable once used for a final result.
- Third-party text retains provenance and is not presumed redistributable.
