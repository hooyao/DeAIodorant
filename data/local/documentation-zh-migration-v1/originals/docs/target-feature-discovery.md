# Calibrated Research Objective and Evidence Plan

Version: `deaiodorant-target-discovery-1.6`.
Authority: the maintainer's project-goal and evidence clarifications on
2026-09-14. This is the current research-priority record; completed experiment
inputs and outcomes retain their original versions.

## Problem to solve

Improve complete, real Chinese media articles such as InfoQ articles that carry
the reader's perceived machine-like writing problems, while preserving facts,
information, qualifications, authorial intent, and useful detail. The article's
context and discourse matter. Synthetic notices or newly prompted synthetic
articles are not substitutes for the target media distribution.

The front half of the project must discover repeatable linguistic features of
that subjective experience. The reader is not required to articulate a formal
feature definition before research can begin: the felt difference is an
observation to explain. However, a weak or indistinct sample cannot identify
features of a phenomenon it barely exhibits. Repeating feature tests, rewrites,
or model comparisons on such material does not solve the sampling problem.

The downstream product may use a compact editor, supervised fine-tuning,
preference optimization, and validated NLP-based reward components. Those
methods do not replace the front-half discovery task or demonstrate success by
themselves. GPU training remains deferred.

## Current human-supplied intensity anchors

The maintainer now identifies the complete SMZDM Microduck article at
`https://post.smzdm.com/p/a70dm4ll/` as `极其臭` and `恶臭`, and the previously
nominated Baidu article as `一般臭`. This is an actual strong-positive reader
observation with a lower-intensity reference, not an assistant-invented label.
Retain the exact wording and do not request the same rating again. Source,
genre, length, and presentation differ; one reader's two article judgments
support exploratory discovery, not a validated intensity model.

The [anchor analysis](routes/compact-refiner/reports/reader-anchor-feature-discovery-v1.md)
separates recurring surface style from reference and support problems. The strong
article has zero literal `而是`; implicit contrastive forms and recurrent stance
must be considered in context. No source has been rewritten, and no feature is
promoted to an RL reward. The publisher's explicit AI disclosure is separate
from the reader's judgment and does not identify the generation pipeline.

The maintainer explicitly clarifies that `而是` remains a strong signal, with
bare-copula realizations expressing the same correction in the supplied example.
The title's `先把买、搓、等三条路算明白` is also directly localized as aversive.
A connective substitution does not remove the underlying rhetorical action.
The next explanatory priority is the
[corrective-framing hypothesis](routes/compact-refiner/rhetorical-mechanism-hypothesis.md),
including motivation of the contrast, semantic relations, new information, and
support. Keyword inventory expansion alone cannot satisfy that priority.

## Two linked targets: aversive cues and actual reading defects

The maintainer describes smell as an indicator of anticipated reading difficulty,
using an analogy with odor warning against spoiled food. This is the reader's
explanatory account, not an experimentally established psychological mechanism.
The product must address both irritating surface/discourse cues and the actual
sentence, reference, or reasoning problems behind them. Removing a marker while
leaving broken exposition is not success; repairing structure while retaining
needlessly repetitive packaging may also leave the reader dissatisfied.

Keep measurements separate: cue frequency and recurrence; predicate/argument
and reference diagnostics; discourse support/progression; and actual reader
difficulty/preference. Do not collapse them into an unvalidated score. Chinese
does not require an overt subject, verb, and object in every sentence. Legitimate
ellipsis, shared arguments, intransitive and nominal predicates are counterexamples
to a simplistic missing-SVO detector.

The reader calls the current Cowork article weak in AI smell but difficult and
translationese-like. That perception does not establish translation provenance.
It also demonstrates why cue counts, felt smell, and reading difficulty cannot
be treated as interchangeable labels.

The maintainer subsequently rejected the repeated Cowork reading preview as a
poor example of strongly characteristic Chinese AI-style writing. It may carry
upstream English LLM problems through translation, but that does not provide the
needed target contrast. The preview is withdrawn; its sample-selection rejection
is not an A/B preference or readability outcome. Do not reissue Cowork under a
generic readability objective. Its completed repairs remain engineering records.

The immediate front-half priority is finding sustained, obvious manifestations
of the target in real complete Chinese articles. Source language or generation
route is explanatory context, not a severity label. Neither a direct-Chinese
label nor a high connector count, isolated typo, or difficult translation is
sufficient. Translated-article capability remains part of the eventual product;
it does not replace this discovery priority.

The explicitly nominated construction family includes `不是……而是……`,
`并非……而是……`, and other `而是` forms. A bounded descriptive count across
the existing time cohorts is authorized and useful before a strong-positive
dataset is complete. It tests occurrence differences, not reader harm or edit
efficacy. Weak-sample limitations do not prohibit checking a concrete observable
feature; they prohibit overstating what that check establishes.

The meaning-preservation boundary remains: missing facts or unsupported logical
premises cannot be invented to make a passage appear coherent. Record a gap when
it cannot be repaired from the article's actual information.

## Translated media and upstream content quality

The maintainer further emphasizes that an English source can already contain
repetitive framing, weak information gain, and unsupported reasoning, with
translation adding Chinese wording or reference defects. Treat this as a
possible layered failure pathway, not a verified authorship history for any
particular article or a universal defect of translation.

The maintainer explicitly rejects the earlier blanket-exclusion approach and
requires the fine-tuned model to improve translated Chinese articles. Retain
original Chinese, translated, mixed/adapted, and unresolved provenance as
research strata. The same temporal boundaries apply within these strata, while
an original-only view is a control/sensitivity rather than the definition of
useful research material. Historical filtered results keep their original scope.
No article is discarded solely because it is translated or difficult to read.

The default product input is the complete Chinese article. Its original foreign
text is optional and must not become a hidden prerequisite for the compact
model. Training, validation, and final evaluation must explicitly cover Chinese
translations, with separate preference, preservation, and fallback results.
When actual source alignment is available, distinguish defects
already present in the source, defects introduced or amplified by translation,
editorial additions, and cases whose origin is unknown. Never assume that the
English source was good or that an LLM wrote or translated it.

Evaluate information progression alongside grammar: repeated propositions,
claims stronger than their supporting evidence, redundant framing, and the
effort required to reconstruct relations. Neither low token entropy nor low
perplexity measures useful information or reader benefit by itself. Source
alignment and assistant judgments generate hypotheses; human reading outcomes
and preservation remain the product evaluation.

## Temporal comparison remains useful

Retain the established primary cohorts:

| Cohort | Publication date | Research role |
|---|---|---|
| Historical baseline | Before 2023-01-01 | Writing from a period dominated by human production |
| Transition | 2023-01-01 through 2025-06-30 | Separate diagnostic interval, excluded from the primary contrast |
| Post-adoption cohort | On or after 2025-07-01 | Primary search interval following the maintainer's observed approximate change in perceived style |

The July 2025 boundary is the maintainer's observation and the existing sampling
policy, not a statistically established discontinuity from the current data.
Do not silently retune it after looking at results. Any change-point analysis
needs a separately frozen plan and adequate temporal coverage.

Dates provide a useful sampling prior, not document-level authorship or smell
labels. Early automatic generation and later updates of older pages prevent an
absolute individual-authorship guarantee. Later writing can be good, and earlier
writing can be poor. Keep publication/update/collection provenance visible and
do not train a human-versus-AI classifier.

## What to preserve and reuse

- Acquired media bodies, stable IDs, canonical URLs, timestamps, source metadata,
  quality/visibility signals, and exact/near-duplicate handling.
- Translation/foreign-compilation evidence and old exclusion decisions,
  reinterpreted only in new versions as provenance strata and original-only
  controls; contradictory metadata never silently certifies originality.
- Existing NLP implementations, frozen feature configurations, source-stratified
  analyses, and documented negative results.
- Every original human comment, rating, and A/B choice, without retrospective
  rewriting or conversion into stronger labels.
- API clients, request/cache provenance, cost control, whole-source hashes,
  presentation mappings, operation replay, and preservation checks.
- Synthetic CR-001 fixtures/results as engineering controls and limited behavior
  diagnostics on their actual task distribution.

The old low-signal experiments remain historical evidence with narrow limits.
Pausing their continuation does not mean discarding collection infrastructure,
temporal cohorts, feature discovery as an objective, or the entire corpus.

## Correction to historical annotation interpretation

The maintainer states that previous annotation samples did not have sufficiently
strong or obvious target characteristics, and that those experiments did not
meaningfully answer the target question. Earlier local complaints or editing
preferences must therefore not be treated as confirmed severe positives for a
new experiment. Preserve the tension between old local comments and the current
assessment rather than erasing either.

The three CR-001 preview preferences are ordinary qualitative editing feedback:
one carries a content-difference concern, one has unspecified strength, and one
is explicitly slight. The reader found no obvious smell in the shown pairs.
Neither those choices nor agent preservation verdicts establish smell-removal
efficacy, a validated reward, or training acceptance.

## Revised evidence sequence

1. **Retain the acquisition foundation.** Audit available sources, time groups,
   extraction fidelity, exclusions, missing material, and prior exposure. Keep
   the entire article and any material figures/captions/links available.
2. **Improve target coverage in real media.** Search the appropriate time/source
   strata for candidate strong and weak impressions. Agent/local inspection may
   nominate cases and evidence, but must preserve uncertainty and counterexamples.
   Do not manufacture a positive through prompting or editing.
3. **Establish a perceptible contrast.** Use a small amount of concrete human
   comparison only where the target boundary genuinely requires the maintainer's
   judgment. Do not ask the reader to label syntax or derive the features. Do not
   repeatedly send indistinct passages in a large annotation batch.
4. **Discover features on declared development data.** Compare observable
   constructions, discourse progression, recurrence, and local concentration
   while controlling source, topic, format, length, translation, and visibility
   where practical. Time differences and subjective intensity are distinct axes.
5. **Test reproducibility and rival explanations.** Use independent documents,
   counterexamples, source/genre sensitivity, appropriately clustered sampling,
   and a feasible prespecified test family. Strong/weak enrichment supports
   discovery, not natural prevalence estimates.
6. **Validate editing interventions.** Freeze bounded operations only after the
   relevant phenomenon is established. Present whole-article context and require
   both useful reader preference and meaning preservation.
7. **Choose training methods afterward.** Collect properly reviewed edit and
   preference data. SFT, DPO, and online RL remain conditional on their own
   evidence and compute requirements.

Do not require the yet-to-be-discovered feature to select its own first positive
examples. Initial perceptual comparison and source inspection can establish
provisional contrast; independent material must test the resulting feature.
Conversely, do not call an agent's impression a confirmed human label merely to
avoid a real decision point.

## Immediate state

At the earlier version-1.1 checkpoint, no media edit or SFT run had started.
The proposed synthetic CR-002 article
tasks are retained but unexecuted and are not the next main experiment. Current
source audits establish textual identity and presentation limitations only;
they do not make the inspected articles strong positives.

Useful completed checks include the [media inventory](routes/compact-refiner/reports/media-development-inventory.md),
[source completeness audit](routes/compact-refiner/reports/media-source-completeness-v1.md),
and [synthetic generation-chain audit](routes/compact-refiner/reports/cr001-generation-chain-audit.md).
All previously collected bodies and feedback remain intact.

A new [bounded real-media staging and calibration run](routes/compact-refiner/reports/media-contrast-calibration-v1.md)
has since captured 24 fixed public responses, with 20 nonempty texts and 16
remaining after deterministic translation exclusions. Two independent whole-text
reviews nominated one article; the maintainer subsequently described it as weak
in AI smell but difficult and translationese-like. It remains outside formal
admission and is not a confirmed strong positive. The separately requested
[contrast-family statistics](routes/compact-refiner/reports/ershi-cohort-statistics-v1.md)
now provide an exact descriptive cue measurement, not an efficacy or training
result. Originality remains a separate unresolved gate for that article.

The subsequent [whole-article audit](routes/compact-refiner/reports/contrast-context-audit-v1.md)
and CPU parser feasibility are complete. A new all-media statistical view
retains translated material, with provenance strata and an explicit correction
to the old filtered count. [Bounded repair development](routes/compact-refiner/media-repair-development.md)
now prepares complete Chinese-only article proposals, including a translated
interview. These are exposed development sources, not fresh validation or
human-confirmed strong-smell examples. SFT remains unstarted.

Those proposals and preservation reviews are now complete, but the Cowork
reader request was [withdrawn for sample mismatch](routes/compact-refiner/reports/cowork-preview-withdrawal.md).
No reader preference was supplied. The next action is
[target-coverage rescreening](routes/compact-refiner/target-coverage-rescreen.md),
with no automatic rewrite, replacement reader task, or training export.
