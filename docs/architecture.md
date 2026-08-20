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
    -> linguistic analysis and pattern catalog
    -> evaluation datasets and metrics
    -> refinement planner
    -> constrained Chinese rewriter
    -> semantic and factual verification
    -> CLI / API / publishing adapters
```

### Acquisition adapters

Retrieve only publicly or lawfully accessible documents at conservative rates.
Each adapter emits a shared metadata schema and preserves source provenance.
Adapters do not make claims about AI authorship.

### Corpus gates

Quality, visibility, provenance, deduplication, language, and translation gates
construct comparable pre-2023 and post-2025-06 cohorts. Gates must expose both
their decision and supporting evidence. Admission policy is deterministic where
possible and fail-closed where uncertainty would contaminate the comparison.

### Matched corpus builder

Balances source, topic, document format, length, publication age, and available
attention signals. Its output supports population-level contrast; it is not a
classifier training set for labeling arbitrary documents as human or AI.

### Pattern catalog

Stores measurable Chinese writing phenomena with examples, extraction logic,
confounders, and observed effect sizes. A pattern becomes a product rule only
after it survives held-out validation and reader evaluation.

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
