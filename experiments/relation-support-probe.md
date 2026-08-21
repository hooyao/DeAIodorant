# Deterministic Discourse-Relation Support Probe

## Purpose

This experiment asks whether an explicit Chinese discourse relation can be
modeled as a typed edge whose local propositions independently support the
claimed relation. It uses deterministic Stanza dependencies, frozen lexicons,
and graph-style overlap. It does not use an LLM judge, embedding model, or
authorship classifier.

The intended distinction is:

~~~text
proposition A --[explicit marker claims relation type]--> proposition B
                    |
                    +-- local evidence path excluding the marker itself
~~~

The probe is deliberately allowed to return `indeterminate`. An indeterminate
instance is not counted as unsupported.

## Representation v0.1

The extractor recognizes five claimed relation types:

- contrast;
- cause;
- inference;
- clarification;
- emphasis.

It handles sentence-initial and intra-sentence markers plus complete paired
contrast frames such as `不是...而是...`. Each instance stores the marker,
left and right argument spans, sentence indices, typed evidence, a decision,
and reason codes.

The frozen evidence vector contains:

- proposition presence on both sides;
- entity, content-word, predicate, and dependency-role overlap;
- negation flips on a shared non-generic predicate;
- a small frozen antonym lexicon;
- explicit comparative terms;
- new concrete entities, predicates, numbers, and other payload;
- abstract-shell-only payload;
- a weighted local anchor score.

The five decisions are `supported`, `redundant`, `type_mismatch`,
`unsupported`, and `indeterminate`. Document metrics retain all decisions and
the abstention rate. Counts are normalized per 100 parsed sentences before
time-cohort interpretation.

The implementation is
`src/deaiodorant/analysis/discourse_relations.py`. The experiment runner is
`experiments/relation_support_probe.py`.

## Existing data

The probe uses only already tracked material:

- 10 pre-period and 10 post-period InfoQ documents;
- the eight post-period reader-friction passages;
- the 10 completed second-round original/revised pairs.

The time comparison uses feature-wise cohort-local Huber locations, 5,000
fixed-seed label permutations, leave-one-document-out direction checks, and a
known-translation sensitivity analysis. The passage analysis uses exact
Spearman permutations. The refinement comparison is descriptive because the
variants were constructed to alter these markers.

## Instance output

Across all document, passage, and refinement scopes, the probe emitted 476
instances:

| Decision | Count |
|---|---:|
| Indeterminate | 241 |
| Supported | 147 |
| Type mismatch | 88 |
| Redundant | 0 |
| Unsupported | 0 |

The absence of `unsupported` and `redundant` results does not show that those
relations are sound. It shows that the current high-precision rules do not
reach those decisions on this material.

## Time comparison

| Feature | Pre mean | Post mean | Robust post-minus-pre effect | Permutation p | BH q | LOO stability |
|---|---:|---:|---:|---:|---:|---:|
| Emphasis instances / 100 sentences | 1.07 | 3.84 | 1.34 | 0.100 | 0.564 | 1.00 |
| Indeterminate ratio | 0.60 | 0.41 | -1.13 | 0.032 | 0.564 | 1.00 |
| Mean payload gain | 11.49 | 8.23 | -0.83 | 0.123 | 0.564 | 1.00 |
| Mean local anchor score | 0.054 | 0.045 | -0.58 | 0.242 | 0.618 | 1.00 |
| All relation instances / 100 sentences | 15.48 | 14.64 | 0.28 | 0.806 | 0.968 | 0.85 |
| Contrast instances / 100 sentences | 8.94 | 8.18 | 0.06 | 0.921 | 0.968 | 0.60 |
| Problem decisions / 100 sentences | 2.05 | 2.20 | 0.04 | 0.912 | 0.968 | 0.65 |
| Problem-decision ratio | 0.15 | 0.13 | -0.03 | 0.941 | 0.968 | 0.60 |

No feature survives correction. The normalized broad contrast rate and problem
rate do not reproduce the stronger result for the specific complete negative
contrast frame. Translation removal reverses the already tiny directions for
relation density, contrast density, and problem density.

The lower post-period indeterminate ratio is stable but is not a quality
signal. The rules simply find more concrete payload and therefore make more
decisions in the post-period documents.

## Reader-friction comparison

| Feature | Post-only Spearman rho | Exact p | BH q | LOO stability |
|---|---:|---:|---:|---:|
| Contrast instances / 100 sentences | 0.51 | 0.232 | 1.00 | 1.00 |
| All relation instances / 100 sentences | 0.46 | 0.304 | 1.00 | 1.00 |
| Mean payload gain | 0.39 | 0.393 | 1.00 | 1.00 |
| Mean local anchor score | -0.34 | 0.446 | 1.00 | 1.00 |
| Emphasis instances / 100 sentences | 0.17 | 0.786 | 1.00 | 0.88 |
| Problem decisions / 100 sentences | 0.06 | 1.000 | 1.00 | 0.50 |
| Problem-decision ratio | 0.00 | 1.000 | 1.00 | 0.00 |

Broad contrast and overall relation density move in the expected reader
direction, but the sample is eight passages and neither aligns with a useful
time effect. The proposed problem decision is unrelated to the observed
reading-friction levels.

## Refinement manipulation

| Feature | Mean revised-minus-original delta | Pairs decreased | Unchanged | Increased |
|---|---:|---:|---:|---:|
| All relation instances / 100 sentences | -21.96 | 9 | 1 | 0 |
| Contrast instances / 100 sentences | -11.62 | 7 | 3 | 0 |
| Emphasis instances / 100 sentences | -10.49 | 8 | 2 | 0 |
| Problem decisions / 100 sentences | -2.57 | 4 | 6 | 0 |
| Problem-decision ratio | 0.014 | 2 | 7 | 1 |

The large count reductions confirm that the second-round operator manipulated
the intended surface relations. They do not validate the typed support
decision. The problem ratio does not track the six revised wins.

## Qualitative audit

One target behaved as hoped. The original multi-tool passage contained:

> 阿里云没有让 Agent 绕过既有工程体系，直接裸调 API。相反，它让 Agent 沿着成熟工具链进入云……

The probe marked `相反` as `type_mismatch` with reason
`ELABORATION_EVIDENCE_WITHOUT_CONTRAST`, matching the reader's optional
comment. The revised version removed the instance.

The same rule also produced clear counterexamples:

- it marked the temporal contrast between the connected buildings at 7:00 and
  their changed state at 7:31 as a mismatch;
- it marked human monitoring versus LLM monitoring as elaboration rather than
  an alternative;
- it treated several disliked `真正` frames as supported merely because a
  concrete payload followed them.

These errors are structural, not threshold errors. Lexical overlap and
dependency roles do not establish contradiction, alternative choice,
causality, or rhetorical necessity.

## Decision

Reject `relation_support_problem_*` v0.1 as a smell score or reader-friction
metric. Keep the deterministic instance extraction, evidence vectors, and
reason codes as audit tooling only.

Do not generalize the specific complete contrast-frame result into a broad
claim about all connectives. Emphasis density remains a time-cohort hypothesis,
not a reader-supported target. Actual relation support requires either a much
narrower formally testable motif or independent expert span annotations. The
reader must continue to provide only low-burden reading preference, not
linguistic classifications.

## Reproduction

~~~powershell
deaiodorant-analysis download-syntax-model `
  --model-dir models/stanza `
  --language zh-hans `
  --package gsdsimp

deaiodorant-analysis annotate `
  --corpus data/pilot/monthly `
  --config configs/features.v1.json `
  --model-dir models/stanza `
  --output feature_runs/pilot-annotations-v1 `
  --device cpu

python experiments/prepare_smell_calibration.py `
  --corpus-root data/pilot/monthly `
  --output feature_runs/annotation-calibration-v1/tasks.json

python experiments/relation_support_probe.py `
  --corpus-root data/pilot/monthly `
  --config configs/features.v1.json `
  --annotations feature_runs/pilot-annotations-v1 `
  --reader-tasks feature_runs/annotation-calibration-v1/tasks.json `
  --reader-ratings data/annotations/reader-friction-v1.json `
  --refinement-answer-key feature_runs/refinement-pairs-v2/answer_key.json `
  --refinement-results data/annotations/refinement-pairwise-v2.json `
  --model-dir models/stanza `
  --output-dir feature_runs/relation-support-v1-2 `
  --device cpu `
  --permutations 5000 `
  --seed 20260822 `
  --tuning-constant 1.5
~~~

Reproduction identity:

| Artifact | Fingerprint |
|---|---|
| Corpus | d6cfb16560de7904ab5dc34a09e35e69642e7f39cb61d517a9bd1ffbc2a43014 |
| Stanza model files | 5fa23dfff06b543c63ef547b32006bb0a9acdd6bc1a3a1df23d768a171352af9 |
| Annotation manifest | fad4aa303d130cc6bbb3a22f1d602068f7dca6c8c625a5112f1daef4df510081 |
| Results | 95ce3dfbed147027b68c16b043af04b8e8e107d73f46a2587a68859f7663ee9b |

All generated instances, annotations, and matrices remain under ignored
`feature_runs/` and `models/` directories.
