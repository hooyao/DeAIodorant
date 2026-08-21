# Research Progress

## Checkpoint: 2026-08-21

This checkpoint includes the first deterministic discourse-graph probe and two
completed rounds of blinded refinement comparisons. It is an exploratory
research checkpoint, not a product milestone.

## Completed work

- Preserved 10 quick reader-friction ratings with an ordinal continue-reading
  outcome and optional verbatim comments.
- Kept time as the primary comparison axis: pre-2023 versus 2025-07 and later.
- Restricted the reader-friction association analysis to the eight post-period
  passages; the two pre-period ratings are a separate sensitivity analysis.
- Implemented feature-wise Huber weighting inside each time cohort so isolated
  documents lose influence without being manually deleted.
- Implemented a deterministic heterogeneous discourse graph using Stanza
  dependency parses, propositions, entities, abstract concepts, and adjacent
  discourse bridges.
- Compared 161 document features on 10 pre-period and 10 post-period InfoQ
  documents with 5,000 fixed-seed label permutations and
  leave-one-document-out stability.
- Prepared and completed three blinded minimal-edit comparisons targeting
  formulaic contrastive and emphatic reframing.
- Froze a conservative second-round edit operator and completed 10 new blinded
  comparisons across seven post-period documents without overlapping any of
  the 10 reader-friction development ranges.

## Current evidence

The strongest interpretable time-and-reader intersection is the complete
contrast frame shaped like `不是/并非/不再是 ... 而是 ...`:

- robust post-minus-pre effect: 1.51;
- time-comparison permutation p: 0.033;
- post-only reader-friction Spearman rho: 0.78;
- reader exact permutation p: 0.036;
- both directions are stable under leave-one-out removal.

These p-values are exploratory. Neither result survives the full expanded
multiple-testing correction, and the reader analysis contains only eight
post-period passages with two observed rating levels.

Graph directions align with the reader hypothesis but remain weaker:

- mean adjacent discourse bridge is lower post-period and lower in disliked
  passages;
- mainline detour ratio is higher post-period and higher in disliked passages;
- abstract-shell and unsupported-edge ratios move in the expected direction.

Exact predicate-signature repetition failed. It moves in opposite directions
between the full time comparison and the rated passages, so it must not be used
as a semantic-restatement detector.

## First intervention result

Three contrast-reduction variants were compared blindly with their originals:

| Outcome | Count |
|---|---:|
| Revised version clearly preferred | 2 |
| Original clearly preferred | 0 |
| Tie or both bad | 1 |

The two wins show that removing repeated framing and stating the mechanism
directly can materially improve clarity. Both winning edits were described as
too emotionally flat. The failed edit removed too many explicit grammatical
arguments; the reader found its omitted subjects, predicates, or objects
effortful even though the original retained obvious formulaic AI patterns.

The next edit operator therefore needs two additional constraints:

1. preserve explicit subject-predicate-object structure across sentence
   boundaries;
2. preserve an appropriate amount of voice and rhythm instead of maximizing
   compression.

This pilot does not yet validate formulaic contrast as a product rule.

## Second intervention result

Protocol `conservative-contrast-reduction-2.0` was frozen before any
second-round outcome was available. The operator removes ornamental contrast
and emphasis only when the payload can be stated directly. It must retain
necessary logical contrasts, explicit grammatical arguments, propositions,
entities, numbers, negation, qualifications, uncertainty, attribution, and a
moderate amount of voice and rhythm.

The batch contains 10 new post-period passages from seven documents. It is
disjoint from all 10 rated development passages, not only the three first-round
interventions. Every edit is represented by an exact before/after replacement
with an operator code, reason, and linked claim IDs. The generated audit has:

- 26 logged replacement operations;
- 62 proposition-support checks;
- exact source hashes and numeric-literal preservation;
- pair-specific locked entities and technical terms;
- retained-contrast and voice-anchor records;
- five originals on side A and five on side B under the fixed seed.

All generation gates pass. The frozen surface diagnostics decrease from nine
complete contrast frames and 16 emphasis markers to zero counted instances in
the revised passages. This confirms that the manipulation occurred; it is not
itself evidence that the revisions are better.

The blinded outcome is:

| Outcome | Count |
|---|---:|
| Revised version clearly preferred | 6 |
| Original version clearly preferred | 0 |
| Tie or neither preferred | 4 |

All six decisive choices favored the revision. Two tied comments described the
revision as slightly better, but they remain ties in the primary count. No
comment identified missing facts or changed logic.

The comments show two important limits. A low-smell passage and a one-sentence
emphasis removal produced no meaningful difference. Another revision retained
the sentence `因为云上变更天然需要工程化承接`, which the reader still described
as AI-smelling abstraction. The current operator can reduce staged relation
framing without making every surrounding sentence readable.

Across both intervention rounds, the descriptive total is eight revised wins,
zero original wins, and five ties. The same reader completed both rounds, the
passages were deliberately selected, all sources are InfoQ, and four
second-round passages come from one document. This is stronger directional
evidence, not generalization or intervention validation.

## Outlier policy and current limitation

Documents are not hard-deleted because one reader dislikes them. Robust weights
are computed separately by cohort and feature. The disliked 2022 Red Hat
passage remains in the stored ratings but does not enter the post-only
reader-friction association.

The current generic document-typicality summary did not confidently rank that
Red Hat document as the strongest pre-period outlier. This is a representation
failure to improve with larger matched data, not a reason to insert a manual
weight. Overall document typicality remains descriptive; only feature-wise
weights are used in the current time comparison.

## Reproducible artifacts

- `data/annotations/reader-friction-v1.json`: 10 quick ratings.
- `data/annotations/refinement-pairwise-v1.json`: three blinded A/B outcomes.
- `data/annotations/refinement-pairwise-v2.json`: 10 conservative second-round
  outcomes with frozen artifact fingerprints and operation identities.
- `src/deaiodorant/analysis/discourse_graph.py`: graph schema and metrics.
- `experiments/analyze_reader_friction.py`: post-only ordinal association.
- `experiments/robust_typicality_probe.py`: cohort-wise Huber analysis.
- `experiments/prepare_refinement_pairs.py`: frozen three-pair intervention.
- `experiments/prepare_refinement_pairs_v2.py`: frozen 10-pair conservative
  intervention with structured operation and preservation logs.
- `experiments/refinement-pairs-v2.md`: second-round protocol and passage set.
- `experiments/discourse-graph-probe.md`: method and detailed evidence.
- `docs/smell-catalog.md`: evidence-status integration.

Generated `feature_runs/` artifacts and local Stanza weights are intentionally
ignored. They can be reproduced from the tracked pilot corpus and scripts.

## Next research step

Do not build a product interface or train a general classifier. The next step
is a held-out replication, not another revision of these 10 pairs:

1. freeze a small multi-reader protocol using new passages across at least
   three genres;
2. retain the same required continue-reading choice and optional comment;
3. keep the current operator unchanged so the replication tests rather than
   retunes it;
4. record meaning-preservation concerns separately from reading preference;
5. treat residual abstract engineering claims as a new hypothesis, not a
   post-hoc extension of the completed operator.

In parallel, run the same graph features on the larger matched corpus when it
arrives. Match source, topic, format, length, and visibility before interpreting
the time effect.
