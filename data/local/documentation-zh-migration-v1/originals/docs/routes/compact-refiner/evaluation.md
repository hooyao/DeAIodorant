# Compact Refiner Evaluation

Policy version: `compact-refiner-evaluation-1.1`.

This route policy defines outcomes and safeguards. Each reader or training run
must freeze its sample, allocation, exact contrasts, analysis, and decision
thresholds before outcomes. No held-out evaluation is frozen or running yet.

## Baselines and attribution

| Arm | Meaning |
|---|---|
| U | Unchanged draft |
| P | Untuned compact model with the frozen editor prompt |
| T | Strong assistant/model editing proposal, with provenance recorded |
| H | Optional independently human-edited candidate; not interchangeable with T |
| S | SFT compact model with the same input and evaluation contract as P |
| D | DPO model initialized from S, when that stage is justified |

The SFT primary comparison is S versus P. S versus U is a required product-value
comparison. The DPO primary comparison is D versus S, with U and P retained.
Comparing a trained model only to the raw draft cannot isolate the value of
training. Teacher or human candidates help diagnose achievable quality; they
are not automatic gold.

Use matched input/context/intensity and a fixed decoding policy. Record actual
inference identity. A hosted alias and a locally trained checkpoint are not
assumed to be the same base model without revision evidence.

## Required translated-Chinese evaluation

Evaluate complete Chinese inputs across direct-Chinese, translated,
mixed/adapted, and unresolved-provenance strata. A foreign original is optional
curation/verification evidence and is absent from the standard model input.
If an optional-source arm is evaluated, disclose and separate it.

Report reader preference, material preservation failures, uncertain reviews,
no-edit/fallback rate, and coverage for translated inputs as well as overall.
Freeze adequate translated-input coverage before evaluation; a pooled result
dominated by direct-Chinese articles cannot establish this required capability.
Keep source originals and all derived translations/adaptations in one split.
Neither translation provenance nor poor input readability is an automatic
exclusion. Coherent translations remain unchanged controls.

## Preservation before preference

Every input receives an independent claim/constraint inventory sufficient to
review important content. Inventory construction is development or evaluation
curation; its conclusions do not enter the model input or act as secret hints.
The generator sees only legitimate user-provided locks/context.

Run deterministic checks first: operation replay, exact protected spans,
numbers with units, named entities/terms, dates, citations, and edit boundaries.
Then review proposition retention, entailment, attribution, negation, modality,
scope, referents, and voice. A reviewer must inspect changed spans in context;
matching preselected strings is not proof of preservation.

A critical failure is a changed factual proposition, unsupported addition,
incorrect quantity/entity/citation, reversed negation, changed uncertainty or
attribution, or a material change to authorial intent. Any detected critical
failure blocks promotion of that checkpoint until a new version is evaluated.
Unresolved preservation judgments also block an edit's admission.

Fallback returns the original and logs a reason code. Report both the raw
candidate failure rate and the final system failure/fallback rate. A system that
always returns U is safe but has not demonstrated refinement benefit. Zero
observed failures has a nonzero uncertainty bound; it is not a zero-risk claim.

## Reader instrument

Primary question: which version makes the reader more willing to continue?

Choices:

- A;
- B;
- both acceptable, with no meaningful difference;
- both unacceptable;
- unable to judge.

Comments are optional. Do not require linguistic annotation or authorship
classification. Perceived formulaicity, clarity, and voice are optional
diagnostics on a planned subset, not replacements for the primary outcome.

Readers see identical surrounding context and visual formatting, with generator
identity and candidate labels hidden. Randomize A/B placement and task order.
Counterbalance contrasts across readers; avoid showing one reader all variants
of the same draft. Use bounded sessions and preserve incomplete submissions
without imputing outcomes.

Include a small prespecified number of identical-text and mirrored-repeat
diagnostics. They are not counted as treatment wins. Record side preference,
repeat consistency, inability-to-judge, and missingness. Passing a few controls
does not prove absence of bias. If diagnostics invalidate a session, keep its
records, explain the rule, and do not reinterpret it as operator evidence.

## Development versus validation

R1 is a feasibility study. One reader may support a documented personal
development direction, not a population preference claim. The three-pair
[qualitative preview](reports/cr001-reader-preview-v1.md) now has direct human
feedback, including a preservation concern and no-obvious-smell observations.
It does not constitute a controlled reader study or separate semantic
certification; agent/model judgments cannot fill those gaps.

A validation run requires fresh groups, a frozen candidate generator/checkpoint,
and an allocation plan crossing independent readers with items. Set sample size
by simulation or an explicit precision target under the expected tie rate and
reader/item variation. Do not copy the largest development effect into the
power calculation. More judgments from the same document or person are not
equivalent to independent sampling.

Freeze the final-test manifest without opening its texts for feature, prompt,
reward, or checkpoint development. Validation may choose among a prespecified
small set of configurations; the final test runs once after selection. Further
changes require a new independent final test. The legacy reserve stays sealed.

## Analysis contract

Report wins, losses, both-good ties, both-bad ties, unable-to-judge responses,
missingness, and preservation failures separately. A descriptive net preference
is `(wins - losses) / eligible judged comparisons`; also report decisive-only
share with its denominator. Never hide a high tie or fallback rate by reporting
only decisive wins.

For sufficient data, prespecify a pairwise/ordinal model with reader and item
effects, or another justified clustered analysis. Retain genre, source generator,
length, intensity, and no-edit cases as planned strata. For small development
data, report clustered/descriptive intervals and limitations rather than fitting
an unsupported high-dimensional model.

Before validation outcomes, define the smallest useful preference improvement,
acceptable operational costs, uncertainty criterion, and analysis contrasts.
Keep at most two primary contrasts per stage and prespecify multiplicity
handling. Do not select the winning subgroup or threshold after seeing results.

## Promotion and stop decisions

| Observation | Decision |
|---|---|
| Critical preservation failure | Reject promotion; investigate and create a new candidate version |
| Reader/session evidence is unreliable | Repair the instrument on development data; do not infer model quality |
| S beats U but not P | Training benefit is not established; retain or improve the prompt baseline |
| S beats P and U under the frozen useful-gain criterion, with preservation and cost gates passing | Advance the SFT checkpoint within the evaluated scope |
| D does not improve on S | Retain S; DPO is not mandatory |
| Wide interval spanning benefit and no benefit | Inconclusive; acquire evidence under the frozen policy if worthwhile |
| Performance is confined to one reader or genre | State the narrower scope; do not promote generality |
| High safety achieved mainly through fallback | Report low coverage; refinement efficacy still needs evidence |

## Role of traditional NLP

Keep the current features as versioned diagnostics initially. Useful candidates
include edit size, protected-content changes, repetition, local rhetorical
recurrence, and discourse continuity. No current smell proxy is authorized as a
main reward solely because it is cheap or correlates with publication period.

To introduce an auxiliary style reward, freeze it and test whether feature
changes predict independent within-input human preferences after accounting for
content preservation and edit size. Report counterexamples and coverage. Run
an ablation against the same training recipe without the feature reward.

Probe reward exploitation deliberately: content deletion, shortened but
ungrammatical output, synonym replacement of penalized markers, punctuation
fragmentation, denominator padding, uniform no-edit output, and style changes
that weaken claims. A feature that can be improved without reader gain remains
a diagnostic. Auxiliary gains cannot compensate for preservation failure.

## Required result table

Every model report includes base/checkpoint identity, independent groups and
readers, candidate counts, preference breakdown, raw critical failures,
uncertain reviews, fallback/no-edit rate, coverage, edit-size distribution,
genre/generator breakdown, latency, token use, cost, memory where observed, and
all exclusions. Distinguish measured values from estimates or missing fields.
