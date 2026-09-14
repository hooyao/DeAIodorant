# Reassessment of the Traditional NLP Research Route

Date: 2026-09-14. Status: retrospective methodological critique and proposed
directions, not a frozen experiment or a new empirical validation.

The maintainer clarified that the problem is the failure to validate perceived
formulaic writing through traditional NLP features and statistics. Replacing
that question with an LLM smell judge or a generic rewriting product would not
resolve it. The recommendations below retain traditional NLP as the measurement
route and reader experience as the product outcome.

## Main finding

The existing work has rejected several specific proxies. It has not established
that the underlying reader experience is absent or beyond traditional NLP.
Three problems remain entangled: an unstable target construct, measurements
that often capture something else, and data with very limited inferential
capacity. More features or more unlabeled articles alone would not resolve them.

There is also positive evidence worth preserving: some conservative edits were
preferred. Those edits changed several aspects of the passage simultaneously,
so they do not identify the causal contribution of a particular marker.

## Evidence boundary

This review inspected code, tracked development annotations, experiment reports,
and the available local pilot/reader feature artifacts at commit
`306e5e0ec1802da2c6f7a741d2ea557d4db04be9`.

The current checkout has no `data/local/` directory. Results involving the
97-document and 93-document handoffs or later parser runs were checked against
their tracked reports and implementations, not independently rerun. No sealed
test or validation-reserve text was opened. No historical annotation, threshold,
feature configuration, or result was changed. No paid inference was needed.

## Why the statistics did not establish a smell

### 1. The observable outcome and the proposed phenomenon diverged

The original reader instrument combines fluency and willingness to continue.
The comments mention ornamental phrasing, empty expansion, grammar, reference,
logical progression, low information value, and topic-specific difficulty.
These experiences can coexist but need not share a feature direction.

The first intervention already separates them. Its first pair was judged to
have more obvious formulaic markers in the original, but worse grammatical
completeness in the revision. Other preferred revisions were criticized for a
cold voice. A single preference score cannot identify which of these dimensions
caused the choice.

The later sequence moved from contrastive reframing to integration burden,
delayed heads, segmentation competition, and attachment ambiguity. Those are
reasonable linguistic hypotheses, but each transition changed the construct.
A reader's description of difficulty segmenting a phrase is an observation;
it does not independently establish a psycholinguistic segmentation mechanism.

Keep three measurements distinct:

- perceived formulaicity: a style diagnostic, with concrete examples and
  counterexamples, never an authorship label;
- comprehension difficulty: sensitive to terminology, prior knowledge,
  reference, and missing context;
- willingness to continue: the primary product outcome, also sensitive to
  interest, information value, and voice.

If perceived formulaicity is not repeatable even with anchored examples, there
is no stable population construct to regress against yet. A reproducible
personal preference remains a legitimate, narrower target.

### 2. The early reader analysis has a severe resolution limit

Directly verified from `data/annotations/reader-friction-v1.json` and the local
`feature_runs/reader-friction-v1/` outputs:

| Quantity | Observed value |
|---|---:|
| Post-period rated passages | 8 |
| Distinct post-period documents | 7 |
| Readers | 1 |
| Observed post-period rating category sizes | 5 and 3 |
| Distinct permutations of those labels | 56 |
| Nonconstant features tested in this reader run | 138 |
| Smallest reported exact two-sided p-value | 0.035714 |
| Smallest reported BH q-value | 0.951128 |

There are only `8! / (5! * 3!) = 56` label arrangements. Exact p-values therefore
have resolution `1/56`. For a feature with distinct ranks, the most extreme
two-sided arrangement has p-value `2/56 = 0.035714`. Feature ties can change the
attainable tail, so this latter bound is not universal.

The first BH cutoff at false discovery rate 0.05 across 138 tests is
`0.05/138 = 0.000362`. BH can still reject if sufficiently many p-values are
small; it is not mathematically impossible. However, an isolated strong
candidate has little prospect of surviving this design. More Monte Carlo
permutations cannot add independent information to 56 unique arrangements.

The code also permutes and leaves out passages rather than whole documents.
Two post-period passages share a document, making unrestricted exchangeability
an additional assumption. Correcting that dependence would not create more
evidence. Repeated tasks from the same reader do not replicate readers.

The appropriate conclusion is insufficient identification, not proof of no
effect. Keep the multiplicity correction; change the prospective design.

### 3. A temporal contrast is an indirect route to a reader phenomenon

The initial same-source time comparison uses 10 pre and 10 post InfoQ documents,
150 dense features, and 6,597 sparse patterns. Topic and format are not matched,
and at least one post document is a known translation. The larger 119-document
handoff has no post-period documents. It cannot supply the missing matched
primary contrast.

A punctuation shift may describe editorial formatting. A reader-disliked
construction may occur in both periods, or be rare in both. Neither temporal
separability nor its absence establishes reader impact. The strongest initial
punctuation findings were sample-level distribution differences with unresolved
interpretation, not validated smells.

Retain time for secondary external replication and prevalence research. Do not
require a feature to differ by publication period before testing whether it
locates an editable reader problem.

### 4. The features often measure a different level of organization

Document averages can dilute a short irritating span. Marker totals discard
whether a contrast is necessary, where it occurs, and whether multiple pivots
repeat the same claim. Lexical overlap confounds explanatory restatement with
empty repetition and vocabulary change with genuine informational progress.

The discourse-support probe illustrates the limit: it emitted 241
indeterminate, 147 supported, and 88 mismatch decisions, but no unsupported or
redundant decisions. Its own audit found genuine contrasts misclassified as
elaboration. This is a construct-validity problem for that measurement, not
evidence that discourse support cannot matter.

Likewise, Huber estimates target the typical cohort location. That is useful for
contamination sensitivity, but a rare local pattern could lie in the very tail
that receives less influence. This is a possible estimand mismatch, not evidence
that Huber weighting caused the null results. Preserve raw and robust summaries
and define any future tail estimand prospectively.

### 5. Strict candidate gates tested proxy intersections

The lexical-boundary selector returned zero high-stratum cases. Its subtitle
lexicon did not represent the modern technical unit `算力` as intended. The
word-level probe scored only 34 of 87 candidates; none jointly passed the
entropy, margin, and familiarity conditions.

These are useful failures of the frozen selectors. They do not show that
readers never struggle with such phrases. Sparse domain counts can make model
uncertainty resemble attachment ambiguity. Conjunctive thresholds can also
eliminate the entire sampling support before any reader relationship is tested.

The correct next step is measurement calibration with positive controls and
matched counterexamples, not lowering the failed cutoffs on the same candidates.
Leave the 87-candidate boundary and the unopened reserve intact.

### 6. Sampling may remove the variation needed for the product question

The high-value, high-visibility corpus is appropriate for the original temporal
research objective. It need not represent drafts that users want edited.
Conservative value filtering and multi-model intersections can narrow the
range of expression; agreement does not guarantee unbiased selection. This is
a plausible selection mechanism, not an established cause of these failures.

The within-document screen also found little contrast, and one comment described
both passages as having obvious smell. Matching on document can control useful
confounders while also removing the style variation of interest. Cross-document
comparison restores variation but introduces topic-interest differences.

Use separate, explicitly named datasets for temporal prevalence and editing
research. Keep corpus-admission requirements intact; do not silently relabel a
broader editing-development set as the formal comparison corpus. Any controlled
synthetic perturbations belong to measurement calibration, not natural prevalence
estimation or human gold.

### 7. Editing evidence does not isolate a marker mechanism

The second round had six revised wins and four ties. Its operations jointly
remove framing, clarify arguments, change wording, and reorganize propositions.
The result supports investigating that editing bundle. It does not establish
that removing `不是...而是...`, punctuation, or emphasis alone caused the gain.

The fourth round's complete side-B pattern blocks an operator interpretation.
The six controlled decompression pairs split three to three. The latter offers
no aggregate advantage in that small development set; it is not an equivalence
test proving that decompression never helps.

Preservation checks also need careful interpretation. In
`prepare_refinement_pairs_v2.py` and `prepare_integration_pairs_v1.py`, claim
checks verify that supplied support strings occur in the original and revision.
They are valuable audit scaffolding but do not computationally prove entailment,
claim completeness, or unchanged scope. The editor's semantic judgment remains
part of the measurement.

## Traditional NLP directions worth testing

These are candidates, not findings. Start with one direction, at most two, rather
than creating another large feature battery.

| Direction | Traditional measurement | Discriminating prediction | Necessary counterexample |
|---|---|---|---|
| Repeated framing with little content progression | Fixed paragraph windows; recurrence of rhetorical constructions; TF-IDF or LSA content similarity; new entity/action/quantity mentions; a prespecified interaction rather than marker count alone | Repeated framing becomes more irritating when successive units add little recoverable content; either component alone is insufficient | A useful recap, coherent technical term repetition, or a contrast that introduces a real alternative |
| Discourse order and reference continuity | Entity-grid transitions, lexical chains, mention distances, and sentence-to-sentence transition patterns; compare observed order with controlled permutations | The representation distinguishes broken local progression while unigram and marker totals remain constant | A legitimate topic shift, section boundary, or reference resolved by surrounding context |
| Formula recurrence beyond topic vocabulary | Entity/number masking, function-word and POS construction sequences, document-frequency dispersion, and smoothed log-odds within matched genres | Recurrent framing remains visible across topics and sources after content vocabulary is controlled | A standard methods description, legal template, or a useful recurring explanation pattern |
| Local concentration and heterogeneity | Prespecified fixed-length windows, upper-quantile or event-coverage summaries, and source/format interactions | A localized signal predicts within-passage reader response better than the document average | Length effects, one quoted passage, code, or an isolated parser error |

The first direction is the highest-priority candidate because it connects the
early comments about empty expansion and staged profundity to an explicit
interaction. Its components are imperfect: TF-IDF similarity is not semantic
equivalence, new entities are not automatically new propositions, and a familiar
fact can still be useful. Those limitations must be tested with counterexamples
before any composite score is defined.

For the second direction, sentence shuffling is a sensitivity control, not a
model of natural bad writing and not proof of reader harm. For the third,
unsupervised clusters or a sparse regularized model may organize development
observations, but their target must be an observable writing pattern or reader
response, never inferred human/AI authorship. Fit vocabularies, IDF, LSA, and
feature selection inside training partitions whenever predictive performance is
reported.

## A more informative next experiment

### Development: establish measurement behavior

1. Use the existing exposed reader examples only for transparent error analysis
   and initial construct descriptions. Retain comments verbatim; analyst
   interpretations are separate fields. Do not rescore them as independent
   validation or reselect from the frozen 87 candidates.
2. Build a small new development panel with both positive candidates and hard
   counterexamples. A budget of 24 distinct documents is a feasibility panel,
   not a powered validation sample. Include fluent formulaic prose, difficult
   technical prose without obvious formulaicity, useful repetition, and
   clearly progressing prose. These initial strata are analyst hypotheses.
3. On a small subset, check repeatability of perceived formulaicity separately
   from comprehension and willingness to continue. Use independent readers
   when available; otherwise state that the target is one reader's preference.
   Readers need not annotate syntax or infer authorship. Distinguish both-good
   and both-bad responses when a tie would otherwise hide the difference.
4. Fit and inspect at most two low-dimensional measurement families on this
   declared development set. Examine continuous distributions, coverage,
   false positives, and negative controls before selecting cutoffs. Development
   iteration is allowed when labeled as such; it is not confirmation.

### Frozen replication: test a specific mechanism

After the measurement behaves sensibly, freeze a separate protocol and acquire
independent evaluation documents. The existing reserve stays unopened.

For the framing/progression hypothesis, compare the same underlying passage in
four controlled forms where feasible: original; framing-only edit;
progression-only edit; combined edit. Retain all unique propositions, necessary
contrasts, negation, uncertainty, attribution, and voice. A case that cannot be
edited without inventing a relation should abstain. Do not assume every passage
supports all four conditions.

Counterbalance conditions across readers so a reader does not need to see all
versions of the same source. Keep willingness to continue as the primary
product outcome, formulaicity as a diagnostic, and preservation as a separate
gate. Estimate whether the feature selects responsive cases, not merely whether
the editor can improve a passage.

Use document and reader as sampling units. For adequate data, a prespecified
ordinal or pairwise mixed-effects analysis can model reader/item differences;
for a small pilot, use clustered descriptive estimates and intervals without
pretending that a complicated model creates power. Determine evaluation size
from simulation of a practically meaningful effect, ties, and reader/document
variation, not from the largest exploratory correlation. Keep only one or two
primary contrasts and retain multiplicity control.

Interpret outcomes separately:

- unreproducible reader judgments: revise or narrow the construct;
- failed measurement controls: revise the representation on development data;
- edits help but features do not select gains: reject the selector;
- a valid measurement with a wide effect interval: insufficient evidence;
- a narrow interval excluding the prespecified useful gain: evidence against
  that particular feature/operator combination;
- preference improves with a preservation failure: reject the edit.

## What to stop and what to retain

Stop extending the single nominal-chain example into progressively more complex
general selectors without independent calibration. Stop adding hundreds of
features to the same eight ratings. Stop treating a zero candidate count, a
non-significant test, and an invalid measurement as the same negative result.

Retain the frozen failure records, provenance manifests, reader comments,
inspectable edit operations, deterministic features, and separation of
development from validation. These are useful infrastructure. The needed reset
is in construct and experimental design, not a wholesale code rewrite.

## Current execution environment

The maintainer reports that `gx10` is unavailable. This reassessment requires
only local deterministic inspection and statistics. OpenRouter is authorized
for necessary external inference, but it does not replace classical feature
measurements or independent reader evidence. The root `.env` stores the
credential as `OPENAI_API_KEY`, matching the existing compatible client, and is
excluded by `.gitignore`. Existing clients read the process environment; they
do not automatically load the root file. No credential value belongs in a
report, command output, or tracked artifact.

## Reproduce the capacity audit

The annotation file has SHA-256
`fd228aa54050a718989f7cd58c719af1dd1980be01200046a4a88262557673b8`.
The command below uses the existing local correlation artifact without
recomputing features or changing any frozen result:

```powershell
@'
import csv
import json
import math
from collections import Counter
from pathlib import Path

ratings = json.loads(Path('data/annotations/reader-friction-v1.json').read_text(encoding='utf-8'))['ratings']
post = [row for row in ratings if row['month'] >= '2025-07']
counts = Counter(row['rating'] for row in post)
arrangements = math.factorial(len(post))
for count in counts.values():
    arrangements //= math.factorial(count)
with Path('feature_runs/reader-friction-v1/feature_correlations_post.csv').open(encoding='utf-8', newline='') as handle:
    rows = list(csv.DictReader(handle))
print(json.dumps({
    'passages': len(post),
    'documents': len({row['doc_id'] for row in post}),
    'category_sizes': sorted(counts.values()),
    'label_arrangements': arrangements,
    'tested_features': len(rows),
    'minimum_p': min(float(row['exact_p_value']) for row in rows),
    'minimum_q': min(float(row['bh_q_value']) for row in rows),
    'first_bh_cutoff_at_0_05': 0.05 / len(rows),
}, indent=2))
'@ | python -
```

## Sources inspected

- [Reader ratings](../data/annotations/reader-friction-v1.json)
- [First editing round](../data/annotations/refinement-pairwise-v1.json)
- [Second editing round](../data/annotations/refinement-pairwise-v2.json)
- [Reader correlation implementation](../experiments/analyze_reader_friction.py)
- [Pilot direction probe](../experiments/pilot-direction-probe.md)
- [Relation-support probe](../experiments/relation-support-probe.md)
- [Within-document screen](../experiments/reader-friction-screen-v3.md)
- [Fourth editing round](../experiments/refinement-pairs-v4.md)
- [Decompression intervention](../experiments/integration-pairs-v1.md)
- [Boundary-competition design and failure](../experiments/boundary-competition-development.md)
- [Modifier-bracketing probe](../experiments/modifier-bracketing-probe.md)
- [Post-corpus expansion](../experiments/post-reader-corpus-expansion-v3.md)
