# Research Progress

## Checkpoint: 2026-08-22

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
- Implemented and ran a deterministic typed discourse-relation support probe
  on the existing time, reader-friction, and refinement material.
- Audited a read-only 119-document corpus handoff and ran a source-stratified
  transition discovery probe plus a 23-document pre-period distribution audit.

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

## Relation-support probe result

The first attempt to model “whether a claimed discourse relation has actual
support” extracts contrast, cause, inference, clarification, and emphasis
instances. It compares their left and right propositions using dependency
roles, entities, predicates, negation, frozen antonyms, comparative terms,
concrete payload, and abstract-shell payload. It explicitly retains an
`indeterminate` decision.

The probe emitted 476 instances across all analysis scopes: 241 indeterminate,
147 supported, and 88 type mismatches. It produced no high-confidence
unsupported or redundant decisions.

The proposed problem score failed:

- problem decisions per 100 sentences had a robust time effect of 0.04 and a
  post-only reader Spearman rho of 0.06;
- problem-decision ratio had a robust time effect of -0.03 and reader rho 0.00;
- the ratio decreased in only two of the 10 second-round revisions and was
  unchanged in seven;
- no relation-support feature survived multiple-testing correction.

The rule correctly identified the reader-reported `相反` in the multi-tool
passage as elaboration mislabeled as contrast. It also falsely marked a real
7:00-versus-7:31 temporal contrast and the human-versus-LLM monitoring
alternative as mismatches. Several disliked `真正` frames were labeled
supported merely because a concrete clause followed them.

Normalized broad contrast density had reader rho 0.51 but essentially no time
effect (0.06), while emphasis density had a stable time effect of 1.34 but weak
reader rho 0.17. This reinforces the need to keep the specific complete
negative contrast construction separate from broad connectives.

Reject the v0.1 problem score. Keep its extracted instances and reason codes as
audit material only. The failure is semantic and structural, not a threshold
problem to tune against the same small ratings.

## Read-only corpus handoff result

The local handoff contains 119 documents with no overlap with the tracked
pilot: 23 pre-period Machine Heart candidates, 53 transition Machine Heart
documents, and 43 transition InfoQ documents. All body files pass strict UTF-8,
SHA-256, CJK-count, and line-count checks.

The handoff contains no post-period document. Transition documents remain
discovery material, and Machine Heart visibility is unverified. Model-assisted
provenance and value labels remain measurements rather than human gold.

A source-stratified transition analysis tested 53 normalized deterministic
features, controlled log document length, permuted dates within source 5,000
times, and applied multiple-testing correction. No feature has BH q below 0.10.
The strongest source-consistent discovery directions are:

- quote-mark density: combined partial rho 0.286, p 0.0054, q 0.286;
- dash density: rho 0.250, p 0.0138, q 0.336;
- emphatic-frame density: rho 0.221, p 0.0320, q 0.388.

Complete negative contrast frames do not replicate as a common transition
trend. Their combined rho is 0.050, with a positive InfoQ direction and a flat
to negative Machine Heart direction. This is direct evidence against
generalizing the earlier post-period InfoQ result across sources.

The 23 pre-period candidates retain full unweighted distributions and
feature-wise Huber weights. The lowest descriptive document weights are driven
mainly by code, lists, punctuation, title questions, and other format features.
No document is deleted. These candidates still require matched post-period
source, topic, format, length, and visibility evidence.

The single reader-observed transition article is not a strong deterministic
feature outlier: its largest same-source robust z is 1.84, for a digit in the
title. The observation remains development calibration only and does not
become an authorship or validation label.

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
- `src/deaiodorant/analysis/discourse_relations.py`: deterministic relation
  instances, evidence vectors, abstentions, and reason codes.
- `experiments/relation_support_probe.py`: existing-corpus time, reader, and
  intervention comparison.
- `experiments/relation-support-probe.md`: complete method, results,
  counterexamples, and rejection decision.
- `experiments/handoff_transition_probe.py`: read-only handoff audit,
  source-stratified transition trends, and pre-period Huber weights.
- `experiments/handoff-transition-probe.md`: handoff method, complete results,
  limitations, and reproduction identity.
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

Do not tune the rejected relation-support score against the same 10 ratings.
Further work on actual relation support requires either a narrower formally
testable motif or independent expert span annotations. The reader should not be
asked to supply those linguistic labels.

In parallel, run the same graph features on the larger matched corpus when it
arrives. Match source, topic, format, length, and visibility before interpreting
the time effect.

The current 119-document handoff is not that matched corpus: it has no post
documents and unverified Machine Heart visibility. It expands discovery only.
