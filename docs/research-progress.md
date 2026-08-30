# Research Progress

## Checkpoint: 2026-08-31

This checkpoint includes deterministic discourse and compositional probes,
expanded post-period discovery corpora, and five completed blinded development
interventions. It is an exploratory research checkpoint, not a product
milestone.

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
- Froze and completed a 12-pair third development intervention across technical
  practice, research summary, and industry reporting passages.
- Froze a 24-passage raw-text reader-friction screen to separate candidate
  selection from editing before any fourth intervention is prepared.
- Terminated the absolute screen after scale collapse and froze a 10-pair
  within-document candidate-enrichment replacement before outcomes.
- Acquired, screened, deduplicated, materialized, and validated a 50-document
  fresh post-period reader-development handoff from two public sources.
- Froze a 12-pair post-only reader-friction discrimination screen with balanced
  source and candidate placement before outcomes.
- Terminated the over-controlled raw comparison and froze a 10-pair post-only
  original-versus-conservative-revision intervention before outcomes.
- Froze and ran a five-motif deterministic inventory on all 67 development
  documents while leaving the 30-document validation reserve unopened.
- Reproduced the earlier OpenRouter empty-answer failure and added explicit,
  auditable reasoning controls and response diagnostics to corpus triage.
- Acquired 720 new post-period records and produced a validated 93-document,
  three-source discovery handoff through a current three-model intersection.
- Applied the frozen motif inventory to the new discovery handoff without
  changing its lexicons or thresholds.
- Froze and ran a Stanza dependency probe for boundary-free pre-head nominal
  chains on `gx10`, including a documented pre-parse operational revision.
- Froze a staged boundary-competition development design before implementing
  the new lexical signal, selecting passages, editing text, or observing a new
  reader outcome.
- Ran its externally calibrated character-to-word boundary gate and rejected
  the selector before editing because no structural candidate entered the
  frozen high-competition stratum.
- Completed a bounded modifier-bracketing literature review and a separately
  frozen word-level dependency-association probe on `gx10`; it localized the
  reader example but failed to produce an independent high-confidence set.

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

## Raw-passage reader-friction screen

The third intervention round showed that exact marker presence and genre
balance do not reliably select passages with meaningful baseline friction. A
fourth edit round would therefore confound candidate quality with edit quality.

Protocol `raw-passage-friction-screen-development-1.0` was frozen before
outcomes. It contains 24 unchanged transition passages from 24 previously
unexposed documents: 12 InfoQ and 12 Machine Heart passages, with four short,
four medium, and four long passages per source. Deterministic completeness
gates leave 463 eligible passages from 55 documents. No smell feature, marker
count, model score, reader outcome, or provenance label enters selection.

The reader supplies only a four-level willingness-to-continue judgment and an
optional comment. Only the two unwilling ratings qualify a passage for a later
development intervention. At least four passages must qualify; otherwise a
fresh raw-text screen is required. At most eight may be edited, with excess
ties resolved by a frozen priority rather than by comments. These 24 documents
become development-exposed as soon as the screen is shown and cannot be used as
held-out validation material.

The screen was stopped early for lack of discrimination. Of 11 responses
persisted by Label Studio, 10 were `fairly willing to continue` and one was
`not very willing to continue`; the other two categories were unused. The
reader reported completing 12, but the unpersisted response is not imputed.
The dominant category share is 90.9%, and only one passage reaches the frozen
gate, below its minimum of four.

Do not complete the remaining tasks or prepare an intervention from this
batch. The failure combines an absolute-scale collapse with a uniformly
acceptable random editorial sample. A replacement development screen should
use within-document relative comparisons between a deterministically ranked
candidate and a length-matched control, retain an explicit no-difference
choice, and test enrichment rather than force an ordinal distinction.

## Within-document enrichment screen

Protocol `within-document-friction-enrichment-development-2.0` is frozen before
outcomes. It compares one ranked candidate with one zero-marker control from
the same document. The matching gates preserve passage-length band, restrict
the CJK-length ratio to 0.8-1.25, allow at most one sentence of difference,
require a rank-sum gap of at least 1.0, and require at least 0.02 CJK-bigram
Jaccard similarity.

The candidate ranking uses within-document percentile midranks for five
deterministic features: target-marker count, abstract-shell density, separator
density, mean sentence length, and referential-opening ratio. A candidate must
contain a target marker and receive at least one auxiliary top-quartile vote.
No previous reader outcome defines the features, thresholds, or weights.

Strict matching left 10 pairable transition documents: eight InfoQ and two
Machine Heart. Candidate placement was balanced five-to-five. The screen was
terminated after three pairs, all judged to have no meaningful difference.
Their dates were 2023-07-18, 2023-10-09, and 2023-03-27.

The reader correctly identified the fundamental mismatch: these transition
passages generally lack the stronger post-2025-07 AI-style friction that the
product needs to refine. The three responses are retained, but the enrichment
threshold is not evaluated and no intervention may use this batch. The
mistake was prioritizing unexposed availability over alignment with the fixed
time axis.

The handoff has zero post documents and ends on 2025-06-11. The tracked pilot
contains 10 post documents, but nine are already exposed through a reader
rating or intervention. The sole fully unexposed post document is
`084c17f921cc74b858d04cdb`, which cannot support another screen by itself.

## Fresh post-period handoff gate

Protocol `post-reader-corpus-handoff-1.1` is frozen before any further reader
project. It does not collect data. It defines a read-only gate for a future DGX
handoff and prevents transition documents from being accepted as post-period
reader material.

The minimum development pool is 36 fresh documents published on or after
2025-07-01. It requires at least two sources with 12 documents each, three
topic strata with six documents each, and six documents in each required
format: technical practice, research summary, and industry reporting. A
60-document handoff is preferred so an independent document-level reserve can
be frozen before paragraph inspection.

Version 1.0 proposed fully crossing source and format. Acquisition showed that
editorial sources specialize by format, so that rule would reward incorrect
format labels. Version 1.1 was frozen before handoff admission or reader
exposure; it retains both diversity axes, reports their complete cross-table,
and leaves explicit source-format matching to the later reader protocol.

The validator checks strict UTF-8 bodies, hashes and counts, exact and near
duplicates, prior research exposure, date boundaries, original provenance,
model and prompt identities, substantive value status, source-relative high-
visibility evidence, and coverage cells. A failed report exits nonzero and
must not be overridden to create Label Studio tasks. The existing 119-document
handoff is rejected because it uses an older protocol and contains zero post
documents.

## Fresh post-period handoff result

The first `post-reader-corpus-handoff-1.1` delivery is complete at
`F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1`. It contains 50
documents: 25 InfoQ and 25 Meituan technical-blog articles published from
2025-08 through 2026-08. Every document has one materialized UTF-8 body and one
index record.

The candidate flow is fully retained:

- 108 public-page acquisition candidates;
- 99 after tracked-pilot and prior-handoff duplicate exclusion;
- 84 high-confidence model-assisted originals, 14 exclusions, and one
  provenance-uncertain case;
- 58 high-confidence substantive articles, 16 low-value exclusions, and 10
  value-uncertain cases;
- 57 high-confidence format/topic measurements and one low-confidence case;
- 50 after the frozen InfoQ within-quarter visibility threshold.

The final format composition is 24 technical-practice, eight research-summary,
and 18 industry-reporting documents. Topic composition is 30 AI/model/agent,
10 business/industry, six software-engineering, and four data-infrastructure
documents. Source-format specialization is explicit: InfoQ contributes seven
technical-practice and 18 industry-reporting articles; Meituan contributes 17
technical-practice and eight research-summary articles.

The validator reports zero errors. The only warning is that 50 documents are
enough for reader development but below the preferred 60-document threshold
for a separate validation reserve. InfoQ visibility uses page views ranked
within publication quarter. Meituan has source-level official history/feed
evidence but no article-level view counts; this limitation remains visible.
All model-assisted provenance, value, format, and topic labels remain
measurements rather than human gold.

## Fresh post-only reader screen

Protocol `post-only-friction-discrimination-development-3.0` is frozen before
outcomes. It uses 12 documents from the new handoff, with six InfoQ and six
Meituan pairs. Format composition is six technical-practice, two research-
summary, and four industry-reporting pairs. Only two research-summary documents
produced both a complete candidate and a complete control after strict prose
formatting gates; PDF labels, author profiles, and list fragments remain
excluded rather than being used to fill a quota.

Short DOM-split source lines are rejoined deterministically into non-
overlapping complete passages. Candidate ranking remains within-document and
requires a target marker plus an auxiliary top-quartile structural signal. The
zero-marker control is matched by length, sentence count, source location, and
CJK-bigram overlap. Candidate placement is balanced six-to-six.

The reader chooses which passage makes them less willing to continue or reports
no meaningful difference. At least four decisive pairs are required to show
that the batch discriminates at all. Feature enrichment additionally requires
at least eight decisive pairs and a 75% candidate share.

The reader terminated the batch after six pairs because same-document passages
were stylistically similar and lacked useful comparison contrast. Four choices
were no meaningful difference, two selected the control as more discouraging,
and none selected the ranked candidate. One optional comment said both passages
had obvious AI-style smell.

Do not evaluate the frozen thresholds or interpret this as ranking evidence.
The design controlled source, topic, author, and format, but also controlled
away much of the stylistic variation of interest. Any future raw-passage
comparison must use different documents while matching source, topic, format,
length, and visibility. Because that still introduces content-interest
confounding, the immediate replacement is a same-content edit intervention.
No intervention may use project 5 passages.

## Fourth intervention setup

Protocol `post-only-conservative-reframing-development-4.0` is frozen before
outcomes. Instead of comparing unrelated raw passages, it compares the same
content before and after a bounded conservative edit. The 10 passages come from
10 new post-period documents not selected for project 5: five InfoQ and five
Meituan, with four industry-reporting, three research-summary, and three
technical-practice passages.

The operator reduces ornamental contrast, clarification, and emphasis framing
while retaining necessary logic, explicit grammatical arguments, propositions,
entities, numbers, negation, uncertainty, rhythm, and authorial voice. It does
not maximize compression. The audit records 10 structured operations, 30
proposition-support checks, locked literals, voice anchors, exact numeric
sequences, source hashes, and unified diffs. All gates pass, and original
placement is balanced five-to-five.

Two draft revisions were rejected because they weakened assertion strength;
another newly introduced causal marker was removed before freezing. The final
surface manipulation decreases frozen target markers from 16 to three. This is
manipulation fidelity, not evidence of reader benefit. Outcomes are not yet
available.

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

## Post development motif inventory

Protocol `post-development-motif-inventory-0.1` was frozen before it was run on
the 67-document development partition. The scan uses only fixed lexical and
punctuation rules and does not open any of the 30 validation-reserve bodies.

Two motifs pass the necessary frequency gate of six independent documents and
three sources. Complete contrast frames occur 124 times in 37 documents across
all five sources. Abstract-shell clusters occur 14 times in 12 documents across
four sources. Neither supplies a coherent intervention target. A frozen
source-stratified contrast sample contains real alternatives, mechanism
distinctions, quoted definitions, benchmark criteria, and source fragments.
All 14 shell clusters mix normal technical uses, repeated literal senses, and
list fragments rather than one editable construction.

The other rules fail the frequency gate: four dense-clause surface candidates
in four documents, four emphatic abstract-payload candidates in three
documents, and zero strict delayed-head low-anchor stacks. No Project 8 is
prepared. The result strengthens the selection-precision limit: frequent
markers or abstract nouns are not sufficient intervention selectors.

## OpenRouter structured-output correction

The earlier MiMo-V2.5 and Hy3 smoke failures were interface false negatives.
The old request sent the local-server-specific
`chat_template_kwargs.enable_thinking=false` field and allowed only 320 output
tokens. A direct reproduction showed both models spending essentially the
entire allowance on reasoning, returning `finish_reason=length`, and emitting
no answer content.

Using OpenRouter's explicit reasoning control and a sufficient budget produced
valid schema-conforming answers from MiMo-V2.5, MiMo-V2.5-Pro, Hy3, Hy4 Preview,
GLM 5.3 Flash, DeepSeek V4 Flash 0731, Qwen3.8 Flash, Qwen3.8 Max, and Qwen3.8
2.4T-A95B. Hy4 initially returned a documented upstream shared-pool 429 and
succeeded on a later retry. This establishes interface compatibility, not
task accuracy.

The triage clients now include reasoning mode and token budget in the cache
identity and manifests, extract both string and content-part answers, and retain
non-sensitive finish, content, reasoning, and token diagnostics.

A fixed 12-document, five-source panel then ran the same provenance and value
prompts across seven current models. DeepSeek, MiMo, Hy3, GLM 5.3 Flash,
Qwen3.8 Max, and Qwen3.8 2.4T-A95B completed all 24 calls. Hy4 completed only
one because the shared upstream pool rate-limited the other 23. The panel has
no human gold and cannot rank accuracy.

The next acquisition batch therefore freezes a three-model fail-closed policy:
DeepSeek and GLM screen every deterministic candidate, while Qwen3.8 Max reviews
only their provisional high-confidence agreements. Final admission requires
high-confidence agreement from all three. This uses larger current models
without spending the most expensive endpoint on candidates already excluded by
the first two measurements.

## Current-model post corpus expansion v3

The completed local handoff contains 93 post-period documents from Huawei,
Leiphone, and QbitAI. Its validator reports zero errors and zero warnings. The
flow is 720 raw acquisitions, 561 after deterministic translation and duplicate
exclusion, 372 after DeepSeek-plus-GLM provenance agreement, 130 after their
two-prompt value agreement, 103 after Qwen3.8 Max value review, and 93 after the
frozen Huawei visibility threshold.

The final composition is 39 Leiphone, 32 Huawei, and 22 QbitAI documents; 40
industry reports, 34 technical-practice articles, and 19 research summaries.
All model labels remain measurements. Fifty-three of 93 documents are from
2026-08, source and format remain strongly confounded, and editorial
distribution is not article-level readership for Leiphone or QbitAI. The pool
cannot support a matched pre/post estimate.

The DeepSeek provenance run had one documented process-restart anomaly. An
orphan and its retry briefly wrote the same cache, creating 95 duplicate cache
keys. The raw cache is retained, the stale processes were stopped, and the
final result was regenerated to exactly 561 unique document IDs. No value cache
contains a duplicate key.

The handoff initially assigned all 93 documents to a discovery reserve. The
frozen motif scan subsequently opened every body, making the full handoff
feature-discovery exposed. The scan found zero strict delayed-head low-anchor
instances, two dense-clause surface candidates, and two emphatic abstract-
payload candidates. Complete contrast and the already rejected shell-cluster
proxy remained frequent but semantically heterogeneous. No Project 8 is
prepared.

## Boundary-free nominal-chain probe

Protocol `nominal-chain-integration-probe-0.2` replaces an aborted full-body
operational attempt. Version 0.1 wrote no candidate result: a 1,501-line tutorial
kept Stanza occupied because code and DOM fragments were filtered only after
parsing. Version 0.2 freezes the existing content-agnostic complete-passage gate
before parsing and leaves all nominal-chain thresholds unchanged.

The final `gx10` run parsed 1,393 complete passages from 133 of the 160 requested
documents. It accurately localized the reader example and found 87 candidates
in 41 documents across five sources, passing the preregistered frequency gate.
It failed the coherence gate. Forty-seven instances contain proper-name or
numeric anchors, 67 have dependency-chain depth one, and the set mixes formal
names, specifications, technical compounds, dense modifiers, and parser part-
of-speech errors.

The narrower audit-only subgroup with no recorded anchor and depth at least two
contains 13 instances in seven documents and four sources. Six come from one
QbitAI document; the rest still mix titles, official program names, ordinary
terms, parsed contrast, and possible integration problems. The probe therefore
does not support one edit operator across six independent documents. Reject it
as an intervention selector, retain the reader example as a single case, and do
not prepare Project 8.

## Boundary-competition experiment design

Protocol `boundary-competition-development-1.0` converts the reader-localized
segmentation observation into a staged, falsifiable experiment without
promoting the rejected UD candidate rule. Stage 0 must implement an explicit
lexical vector using segmentation-path entropy, best-versus-second path margin,
gap-level boundary posteriors, ambiguous-gap count, and unresolved distance to
the head. Branching entropy, accessor variety, tokenizer disagreement, and
proper-name or technical anchors remain diagnostics in version 1.0 rather than
admission rules.

External percentile cutoffs must be calibrated and hashed before the
post-period pool is ranked. The working reader example must be localized without
a phrase-specific exception. The reader stage additionally requires eight high-
competition and eight matched low-competition passages from 16 distinct,
previously unexposed post-period documents, at least three sources, and at
least two formats per stratum. The 30-document validation reserve remains
unopened. Failure to assemble all eight matched blocks stops the experiment;
thresholds may not be relaxed to force a batch.

Every selected passage receives the same boundary-only structural-unpacking
operator. The editor is blind to high/low stratum and display side. The 16
interventions are balanced within stratum and session, with one identical-text
diagnostic and one later mirrored repeat, for 18 tasks under seed `2026083101`.
The reader still answers only which version makes them more willing to
continue, with an explicit no-difference choice.

The development decision requires passed instrument, preservation, and
manipulation gates; at least six decisive high-stratum answers; at least 75%
revised preference among those answers; high-stratum net preference of at least
0.50; and a high-minus-low selector contrast of at least 0.50. Low-stratum
benefit without contrast rejects the selector even if the operator remains
interesting. Optional comments cannot affect any gate.

Exact-binomial sensitivity shows why this 16-passage experiment cannot be
called validation. With no ties, a true revised preference probability of 0.70
requires 49 decisive comparisons for 80% power at two-sided alpha 0.05; 0.75
requires 30, and 0.80 requires 20. Repeated outcomes from the same reader do not
provide independent reader replication at any of those counts. A later
confirmatory design must use multiple readers, held-out passages, and
simulation under a crossed reader-item model.

Stage 0 subsequently used SUBTLEX-CH and 150 public Beijing Sentence Corpus
sentences to calibrate the frozen lattice. All 87 prior structural candidates
were scored without opening the validation reserve. Zero candidates entered
the high-competition stratum; 36 instances in 23 documents entered the low
stratum, and 51 instances were middle or unscored. Seven candidates passed the
entropy and path-margin gates, but only one had two ambiguous character gaps
and none reached the required unresolved distance of six characters. The
maximum was four, so no high/low matching edge existed.

The reader example itself had zero ambiguous gaps, unresolved distance two,
entropy percentile 0.669, and margin percentile 0.346. Its best SUBTLEX path
was `原生 / 时代 / 全新 / 算 / 力 / 服务`; the outdated-domain split of `算力`
is recorded rather than corrected after the result. Reject
`boundary_competition_v1`, do not create Project 8, and reinterpret the current
hypothesis as word-level modifier-attachment or phrase-bracketing competition
rather than character-to-word segmentation.

## Word-level modifier-bracketing probe

A bounded OpenAlex, Crossref, and Semantic Scholar search identified English
noun-compound methods based on dependency probabilities, word association,
term evidence, and hidden-relation paraphrases, plus contextual Mandarin work
on word frequency, semantic transparency, and word structure. Search queries,
partial-result limits, OpenAlex budget exhaustion, Semantic Scholar 429 errors,
and six exact-DOI abstract checks are recorded. The transfer from English noun
compounds to Chinese technical modifier stacks remains an unvalidated analogy.

Protocol `modifier-bracketing-probe-0.2` enumerates every right-headed binary
tree over Stanza content tokens. It scores attachments with ordered token-pair
probabilities from 1,393 complete passages while excluding the candidate's
entire document. Proper names, numbers, ASCII terms, quoted titles, token
familiarity, exact-sequence termhood, and cross-source support remain separate
rival variables.

Version 0.1 was operationally invalid because percentile midranks made a tied
minimum-margin gate impossible. Version 0.2 froze a `1e-12` numerical-zero
tolerance and nearest-rank value cutoffs before rerunning; no substantive
threshold or input changed. Two independent `gx10` runs then produced
byte-identical artifacts.

The reader example passes the case-level gate: normalized tree entropy 0.822,
zero best-second margin, 0.857 familiar-token fraction, and four weak
attachments. The multi-source gate fails. Of 34 scorable candidates, seven
pass the entropy gate, 26 the margin gate, 17 the familiarity gate, and 27 the
weak-attachment gate. Five pass entropy and margin together, but none also pass
familiarity. Those five are names or sparse technical strings rather than an
independent set of familiar-word modifier stacks.

Reject the current word-level tree-entropy vector as an intervention selector.
Retain attachment competition only as a localized explanation for the one
reader example. The stronger next candidate is hidden semantic-relation
underdetermination, but this result does not prove it. Any new familiar-word
weak-relation measurement must be frozen and tested on an independent corpus;
the 87 exposed candidates cannot be re-filtered after this result. No Project 8
is prepared.

## Reproducible artifacts

- `data/annotations/reader-friction-v1.json`: 10 quick ratings.
- `data/annotations/refinement-pairwise-v1.json`: three blinded A/B outcomes.
- `data/annotations/refinement-pairwise-v2.json`: 10 conservative second-round
  outcomes with frozen artifact fingerprints and operation identities.
- `data/annotations/refinement-pairwise-v3.json`: 12 cross-genre development
  outcomes and the reader's round-level baseline-friction observation.
- `data/annotations/refinement-pairwise-v4.json`: 10 fresh-post intervention
  outcomes, the complete side-B selection diagnostic, and the reader's
  compositional-difficulty observation.
- `data/annotations/integration-pairwise-v1.json`: six proposition-
  decompression outcomes, two passed position controls, and localized reader
  observations about delayed heads and abstract modifier stacks.
- `data/annotations/reader-friction-screen-v1.json`: 11 persisted absolute
  ratings, the early-stop discrepancy, and the instrument-failure decision.
- `data/annotations/reader-friction-screen-v2.json`: three no-difference
  responses and the transition-corpus mismatch termination decision.
- `data/annotations/reader-friction-screen-v3.json`: six post-only responses
  and the within-document over-control termination decision.
- `src/deaiodorant/analysis/discourse_graph.py`: graph schema and metrics.
- `experiments/analyze_reader_friction.py`: post-only ordinal association.
- `experiments/robust_typicality_probe.py`: cohort-wise Huber analysis.
- `experiments/prepare_refinement_pairs.py`: frozen three-pair intervention.
- `experiments/prepare_refinement_pairs_v2.py`: frozen 10-pair conservative
  intervention with structured operation and preservation logs.
- `experiments/refinement-pairs-v2.md`: second-round protocol and passage set.
- `experiments/prepare_refinement_pairs_v3.py`: frozen 12-pair cross-genre
  development generator.
- `experiments/refinement-pairs-v3.md`: third-round protocol, audit, and result.
- `experiments/prepare_reader_friction_screen_v1.py`: deterministic balanced
  selection and Label Studio task generation for unchanged passages.
- `experiments/reader-friction-screen-v1.md`: frozen screen, follow-up gate,
  passage identities, artifact hashes, and reproduction command.
- `experiments/prepare_reader_friction_screen_v2.py`: within-document ranking,
  matching, blinding, and Label Studio task generation.
- `experiments/reader-friction-screen-v2.md`: frozen replacement protocol,
  pair identities, decision threshold, limitations, and artifact hashes.
- `experiments/validate_post_reader_handoff.py`: read-only admission,
  disjointness, duplicate, integrity, and minimum-coverage gate.
- `experiments/post-reader-corpus-handoff.md`: frozen post-period handoff schema
  and the planned low-burden reader use after admission.
- `experiments/acquire_post_candidates.py`: post-only InfoQ acquisition staging.
- `experiments/acquire_meituan_post_candidates.py`: public official-history
  Meituan technical-blog acquisition staging.
- `experiments/prepare_post_review_candidates.py`: cross-corpus duplicate
  exclusion and model-review candidate preparation.
- `experiments/classify_post_corpus_strata.py`: cached model-assisted format and
  topic measurements for balancing only.
- `experiments/build_post_reader_handoff.py`: fail-closed admission,
  visibility filtering, materialization, and manifest generation.
- `experiments/prepare_reader_friction_screen_v3.py`: post-only passage
  reconstruction, candidate/control matching, blinding, and task generation.
- `experiments/reader-friction-screen-v3.md`: frozen post-only reader protocol,
  pair identities, thresholds, limitations, and artifact hashes.
- `experiments/prepare_refinement_pairs_v4.py`: fresh post-only conservative
  intervention, structured operation logs, and preservation gates.
- `experiments/refinement-pairs-v4.md`: frozen fourth-intervention protocol,
  passage identities, audit, compromised outcome, and artifact hashes.
- `experiments/compositional_burden_probe.py`: deterministic integration-load
  vector for controlled variants without a composite score.
- `experiments/scan_post_compositional_burden.py`: source-format-stratified
  discovery scan over previously unselected post passages.
- `experiments/compositional-burden-probe.md`: measurement definitions,
  fourth-round diagnostics, scan results, and limitations.
- `experiments/prepare_integration_pairs_v1.py`: bounded proposition-
  decompression intervention with preservation and position controls.
- `experiments/integration-pairs-v1.md`: frozen fifth-development protocol,
  passage identities, passed position gate, split outcome, and reproduction
  identity.
- `experiments/head_final_modifier_probe.py`: model-free cue-to-head span and
  low-anchor abstract-modifier candidate extraction.
- `experiments/head-final-modifier-probe.md`: localized construction,
  deterministic rule, corpus audit, false positives, and admission boundary.
- `experiments/inventory_post_development_motifs.py`: frozen five-motif scan of
  the development partition only.
- `experiments/post-development-motif-inventory.md`: rules, frequency gate,
  result, coherence audit, and no-intervention decision.
- `experiments/compare_openrouter_corpus_models.py`: fixed-panel current-model
  interface and cross-model measurement comparison without human gold.
- `experiments/openrouter-corpus-model-interface-audit.md`: live model evidence,
  empty-answer diagnosis, fixed-panel results, and frozen batch policy.
- `experiments/acquire_editorial_post_candidates.py`: public QbitAI and
  Leiphone post-period acquisition staging.
- `experiments/acquire_huawei_post_candidates.py`: topic-focused public Huawei
  recommendation and article-view acquisition staging.
- `experiments/snapshot_openrouter_rankings.py`: live public weekly-usage
  ranking snapshot used for current-model selection.
- `experiments/compare_provenance_models.py`: fail-closed two-model provenance
  intersection and disagreement report.
- `experiments/compare_value_models.py`: fail-closed two-model research-value
  intersection and disagreement report.
- `experiments/build_expanded_post_reader_handoff.py`: five-source handoff
  materialization and frozen development/reserve assignment.
- `experiments/post-reader-corpus-expansion-v2.md`: acquisition flow, live model
  selection, model effects, final composition, partition, and identity.
- `experiments/post-reader-corpus-expansion-v3.md`: current-model admission,
  run anomaly, final discovery composition, limitations, and identity.
- `experiments/nominal_chain_integration_probe.py`: frozen pre-parse prose gate
  and dependency-based boundary-free nominal-chain extraction.
- `experiments/nominal-chain-integration-probe.md`: protocol revisions,
  aggregate result, coherence failure, and rejection decision.
- `experiments/design_boundary_competition_experiment.py`: frozen balanced
  placeholder allocation and exact-binomial sensitivity calculation.
- `experiments/boundary-competition-development.md`: pre-outcome staged
  measurement, intervention, randomization, analysis, decision protocol, and
  failed Stage 0 result.
- `src/deaiodorant/analysis/boundary_competition.py`: deterministic SUBTLEX
  segmentation lattice, gap posteriors, path entropy, path margin, and
  branching diagnostics.
- `experiments/boundary_competition_probe.py`: Beijing Sentence Corpus
  calibration, frozen candidate classification, corpus-separation audit, and
  high/low matching gate.
- `experiments/modifier-bracketing-search-boundary.json`: bounded literature
  queries, result-depth limits, API failures, and coverage statement.
- `experiments/modifier-bracketing-evidence-ledger.csv`: seven auditable
  source-to-claim records, including the challenging local Stage 0 result.
- `experiments/modifier-bracketing-prediction-matrix.csv`: prespecified
  discriminating predictions for attachment, semantic, term, and global-load
  candidates.
- `experiments/modifier_bracketing_probe.py`: cross-fitted word association,
  exhaustive right-headed tree enumeration, anchor diagnostics, and frozen
  computational gates.
- `experiments/modifier-bracketing-probe.md`: literature boundary, rivals,
  protocol deviation, complete result, and reproduction identity.
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

Generated `feature_runs/` artifacts and Stanza weights are intentionally
ignored. They can be reproduced from the tracked pilot corpus and scripts.
Local model inference, including bulk parser inference, runs on `gx10`; the
local workstation is limited to deterministic artifact preparation and checks.
Remote API inference may use OpenRouter with the ignored key held only in
process memory and with model, reasoning mode, token budget, and prompt version
recorded.

## Next research step

Do not build a product interface, train a general classifier, or ask the reader
to continue any stopped screen. The fourth intervention is complete: five
revised preferences, four original preferences, and one no-difference answer.
All nine decisive answers selected side B despite balanced original placement,
so the treatment totals are position-confounded and do not validate the
operator.

The reader reported a separate form of difficulty in which familiar individual
words become difficult to integrate as a whole. A deterministic post-outcome
probe found mixed evidence: revisions reduced function-to-content ratio in all
10 pairs and increased content per clause head in six, but usually reduced
sentence length, tree depth, and long dependencies. No composite burden score
is defined or validated.

The proposition-decompression intervention is complete. Its identical-text and
mirrored controls both passed, so the six treatment outcomes are interpretable
as development evidence. Three revisions and three originals were preferred,
with no ties. Generic sentence splitting or proposition decompression is not
promoted.

One preferred revision retained a reader-localized problem: `AI 原生时代全新的
算力服务需求`. The head noun `需求` arrives after a long modifier string, and
the generic era and novelty modifiers do not specify what makes the requirement
new. A model-free lexical probe localizes both the original and revised forms.

The first 50-document handoff left only 21 development-eligible documents after
projects 5 through 7. Public QbitAI, Leiphone, and Huawei acquisition added 319
raw records. Deterministic translation and duplicate exclusion, current-model
source agreement, two-prompt value screening, cross-model value agreement,
strata confidence, and visibility filtering produced a new 97-document,
five-source handoff. It passes the frozen validator with zero errors and zero
warnings.

Model choice used a captured live OpenRouter weekly-usage ranking rather than
remembered popularity. Opaque Ox Alpha was excluded. DeepSeek V4 Flash 0731,
the number-two model, passed the task-specific structured-output smoke test.
MiMo-V2.5 and Hy3 appeared to return empty answer content and were not batch-
run. A later audit reproduced those empty answers as token-budget exhaustion:
the unsupported disable-thinking field left reasoning enabled, and reasoning
consumed all 320 completion tokens. Both models return valid structured answers
under corrected OpenRouter parameters. The v2 handoff retains its original
Qwen3.8-27B plus DeepSeek measurement identity; the interface correction does
not retroactively change it. The ignored API key was never persisted or copied
to `gx10`.

The role split is frozen before new paragraph analysis: 67 development
documents and 30 validation-reserve documents. The reserve has not been read
for feature discovery and cannot support validation without multiple readers.

Applying the same frozen rule to the separate 119-document handoff produced 38
broad delayed-head candidates but zero strict low-anchor abstract stacks. The
strict motif did not replicate. The handoff contains only pre and transition
documents and is not matched to the post pool, so this zero cannot estimate a
time effect.

Applying it only to the expanded handoff's development partition produced 23
broad candidates across 14 documents and again zero strict instances. The
validation reserve was not read. Do not relax the definition against these
results or create project 8 from broad false-positive candidates.

The wider frozen motif inventory also failed to produce a coherent selector.
The new 93-document handoff passed the fixed current-model and integrity gates
and was disjoint from both v2 partitions and every prior reader artifact. Its
complete frozen-rule scan again found zero strict delayed-head instances and no
new coherent operator. All 93 documents are now feature-discovery exposed, not
reader-validation material.

The immediate step is no longer to prepare a boundary- or bracketing-based
reader batch. Both selectors failed their frozen corpus gates. The one reader
example is compatible with word-level attachment competition, but the same
tree-entropy pattern does not appear among familiar-word candidates across the
development corpus. The next candidate is hidden semantic-relation
underdetermination: familiar words are juxtaposed without saying how their
claims relate. A deterministic familiar-word weak-relation rule must be frozen
before collecting and opening a new independent post-period discovery corpus.
Do not re-filter the exposed 87 candidates or open the validation reserve.

The broader Stanza nominal-chain probe does not remove this requirement. Its
frequency gate passed but its candidates were not one construction. The new
protocol used an independently frozen lexical-familiarity and segmentation-
boundary vector; Stage 0 failed. Post-hoc lexical blacklists against the 87
candidates remain prohibited, and no Project 8 was created.

This remains single-reader development work. The expanded corpus now preserves
an independent document reserve with three sources, three formats, and three
topic strata. Held-out validation still requires multiple independent readers
and a frozen operator and analysis plan before outcomes.

Do not tune the rejected relation-support score against the same 10 ratings.
Further work on actual relation support requires either a narrower formally
testable motif or independent expert span annotations. The reader should not be
asked to supply those linguistic labels.

In parallel, run the same graph features on the larger matched corpus when it
arrives. Match source, topic, format, length, and visibility before interpreting
the time effect.

The current 119-document handoff is not that matched corpus: it has no post
documents and unverified Machine Heart visibility. It expands discovery only.

The third intervention round uses 12 transition passages from this discovery-
exposed handoff. It broadens genre coverage but is development evidence, not
held-out validation. Its operator, passages, edits, preservation checks, task
order, and A/B balance were frozen before outcomes.

The outcome is four revised wins, one original win, and seven ties or neither-
preferred judgments. Research summaries produced two wins and two ties;
technical practice produced one win, one original win, and two ties; industry
reporting produced one win and three ties. The reader reported that almost all
pairs had little difference because the original passages had little obvious
smell. Only one optional comment identified a specific marker: `换句话说`.

The third round therefore diagnoses a selection problem, not a reason to
rewrite more aggressively. Marker presence and genre balance alone do not
identify passages with enough baseline friction to benefit. Future development
sampling should use a separate low-burden baseline-friction screen, while
keeping screened material out of held-out validation. See
`experiments/refinement-pairs-v3.md` and
`data/annotations/refinement-pairwise-v3.json`.

That screen was frozen as `experiments/reader-friction-screen-v1.md` and then
terminated early. Ten of 11 persisted responses occupied one category, so the
remaining tasks are not needed. The replacement should compare ranked and
matched-control passages within the same document rather than repeat the same
absolute-rating design.

That replacement is now frozen as
`experiments/reader-friction-screen-v2.md`. It contains 10 blinded pairs and
retains an explicit no-meaningful-difference choice. It was terminated after
three no-difference responses because every completed pair came from the
transition period. The ranking is not evaluated from this mismatched batch.
