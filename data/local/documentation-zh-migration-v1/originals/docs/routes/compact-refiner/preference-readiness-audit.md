# Compact Refiner: Pre-Human Diagnostic Audit

Audit ID: `compact-refiner-readiness-audit-1.0`  
Date: 2026-09-14  
Status: prospective implementation recommendations; no candidate outcomes were
available to this reviewer when this version was written.

## Decision

Run the bounded CR-001 development pipeline, then independently review its
outputs before asking for reader time or selecting training hardware. Do not
start SFT, DPO, or reward optimization from this audit. The available next step
is an inference and measurement feasibility experiment.

A useful autonomous result is a reproducible finding about editing opportunity,
content preservation, compact-model behavior, or review failure. It is not an
estimate of human willingness to continue reading. If no human judgments exist,
the reader experiment remains `awaiting_review`, even when its pre-human
diagnostic phase is complete.

This audit reads the route index, data contract, evaluation policy, first-batch
plan, training plan, decisions, experiment ledger, prompts, and report/manifest
templates. It also uses the exposed reader-friction and second-intervention
annotations and the 2026-09-14 reassessment as development context. It does not
inspect the legacy reserve, sealed tests, or the frozen 87 modifier candidates.

## What the current plan gets right

The unchanged control makes refusal to edit observable. The untuned compact
baseline prevents a later SFT-versus-original comparison from attributing prompt
effects to training. Preserving failed candidates and separating model review
from human acceptance prevents a polished proposal pool from becoming invented
gold. The paired input design also avoids requiring a pre/post corpus feature
difference before testing a useful edit.

The first experiment should retain these boundaries. Its principal risk is now
the relevance and measurability of the task, rather than the absence of a more
complicated training algorithm.

## Risks that need an observable diagnostic

### The source tasks may contain little editing opportunity

An ordinary answer to a complete, carefully organized fact packet may already
be quite good. A 300-600-character limit removes much of the long-range drift,
repeated concluding material, and poorly integrated exposition described in the
earlier comments. Conversely, a sparse packet combined with a minimum length
can manufacture padding. Neither pattern establishes natural problem prevalence.

Inspect every source draft alone before exposing its edits to the independent
reviewer. Record a candidate-blind opportunity inventory with evidence spans:

- `actionable_local_issue`: an identifiable in-scope defect and a plausible
  bounded change using only information already present;
- `no_clear_edit_needed`: no material defect identified under the contract;
- `content_correction_needed`: missing required source content, an unsupported
  assertion, or another defect that a style editor must not quietly repair;
- `uncertain`: ambiguity, context insufficiency, or disagreement prevents a
  defensible diagnosis.

Add nonexclusive issue tags such as redundant framing, unclear referent,
disordered information, awkward grammar, or voice mismatch. These are proposed
editor observations, not validated smell categories. Keep at least one evidence
span and a bounded rationale for an actionable label; do not infer a defect
merely from a marker, length, or model identity. Record the reviewer kind and
whether the inventory was completed before seeing any candidate outputs.

Do not select, regenerate, or exclude valid drafts based on this inventory.
Report all categories by source model and genre. If most drafts have no clear
editing opportunity, the immediate finding is restricted task coverage. A later,
separately versioned batch can include longer or realistically messy inputs,
with the sampling rules fixed before generating them. Do not request bad or
stereotypically machine-like prose to rescue the current effect.

### Constructed scenarios are not a natural writing distribution

Fictional names and quantities provide traceable facts and manageable rights;
they do not imply that the prose should be fictional storytelling. Keep the
requested genre, audience, and ordinary communicative purpose realistic. Do not
add anecdotes or personal experience to make revisions seem more human.

Report the constructed content origin prominently. A passage about a fictional
workplace can test a constraint, but it cannot estimate how often real user
drafts need editing. Familiarity, stakes, and topic interest may differ from real
reading. A successful synthetic development run still needs permission-cleared
realistic inputs in a later evaluation.

### Original validity and edit fidelity are separate questions

Audit the source against its packet in both directions: required supplied facts
omitted or altered, and unsupported facts introduced. A packet omission that
violates the generation task is a source failure, even if the prose is fluent.
Record optional versus required facts in the brief before source generation
when the task does not require every packet fact. A material source problem
goes to the content-correction quarantine.

For an admitted source, audit each candidate against the exact original passage,
using the same legitimate context/locks the editor received. Do not reward a
candidate for restoring a packet fact absent from the original; that is a
different task. Do not treat new plausible implications as preserved claims.
Check whether an alleged removal of empty framing also changes uncertainty,
scope, emphasis, attribution, or the author's stance. Mark unresolved cases
`uncertain`; automatic string checks cannot settle them.

### Candidate comparisons can be asymmetric before training starts

P and T need the same editable input, declared intensity, audience, voice,
read-only context, and legitimate locks. Claim inventories and expected review
answers are not extra editor input. Save the fully rendered input and hash for
both arms so this can be checked.

A T proposal created with iterative assistant deliberation is a useful
diagnostic ceiling, but not a matched one-call competitor to P. Record whether T
was a frozen API response or an assistant-authored/iteratively reviewed proposal,
including attempts and exposed context. Report observed latency/cost only where
available; record unavailable assistant compute as unknown. Do not conclude
that a capacity gap alone explains the difference.

An independent model reviewer should receive opaque candidate IDs and avoid
editor/model labels, deterministic verdicts, or a preferred answer. It still
sees the original for fidelity review; this is candidate-identity blinding, not
human reader blinding. Separate review calls or agents can reduce immediate
self-evaluation, but shared model families and instructions remain correlated
sources of error. Agreement does not become human validation.

### Hosted aliases do not establish training identity

Record requested and returned source/editor model IDs, provider if exposed,
checkpoint revision or its absence, reasoning/decoding policy, and timestamp.
Resolve a trainable student checkpoint and license separately. A hosted P is
only an approximate baseline if exact revision equivalence cannot be shown.
Before any training attribution, rerun the untuned actual base checkpoint under
the same input contract. The strongest accessible source/editor should not be
assumed to represent all deployed generators or all Chinese genres.

## Exact first-run artifacts and gates

The following are proposed additions to the CR-001 run freeze, not claims that
these artifacts or checks already exist. Freeze their definitions and applicable
thresholds before inspecting candidate outcomes. A code fix after outcomes
gets a new diagnostic version and retains the original result.

| Artifact | Required content | Gate or interpretation |
|---|---|---|
| Input and request manifest | 24 group IDs; constructed-origin/rights records; genre/source allocation; packet, prompt, request, code, and input hashes; prices and cost cap | Exactly one immutable group assignment; no missing provenance; no unrecorded model/prompt change |
| `generation_accounting.json` | Allocated, attempted, completed, rejected, uncertain, and unattempted source/candidate counts; reason codes; all attempts | Every planned ID has a terminal or explicit pending state; never drop a failed request from its denominator |
| `source_audit.jsonl` | Bidirectional packet review, required-fact omissions, unsupported additions, source-only opportunity inventory | Source failures/uncertainties are quarantined; no selection by likely edit success |
| `candidate_integrity.jsonl` | Source/output hashes, replay result, protected spans, quantities/units, edit size, exact no-edit status | Replay and identity checks pass for every candidate used downstream; malformed/truncated/empty results cannot be treated as no-edit |
| `review_controls.jsonl` plus private answer key | Separate constructed identity and planted semantic-error pairs | No control is a natural sample or reader outcome; reviewer misses expose an operational review weakness |
| `candidate_audit.jsonl` | Candidate-blind model review; retained/deleted/added claims; contextual evidence; pass/fail/uncertain; issue resolution status | Any critical failure or uncertainty blocks that candidate's review-ready status; an unchanged candidate is not evidence of benefit |
| `diagnostic_summary.json` | The counts and contrasts below, with explicit model-only provenance and missing human fields | No simulated human answer, smell score, or positive training export |
| Blinded reader packet and private mapping | Eligible contrasts, fixed allocation, identical context/formatting, diagnostics, item hashes | Freeze before actual responses; no unsafe candidate or reviewer hint enters the visible task |

Use two identity pairs and four constructed critical-change controls for the
first review smoke check. The four changes should cover negation, weakened
uncertainty, altered quantifier/scope, and a changed referent with intact surface
entities/numbers. Keep them outside the 24 groups. A reviewer that misses a
planted critical change is not adequate as the sole pre-human semantic gate.
Preserve the miss and revise on separately named development controls before
trusting that gate again. Passing six controls does not estimate a general miss
rate or certify accepted data. A simple string rule may miss the scope/referent
controls without invalidating its narrower advertised role.

An operationally complete diagnostic run has valid provenance, complete
accounting, reproducible outputs, explicit review outcomes, and a report. It can
complete even with zero safe edits. Preparing a substantive reader contrast
additionally requires at least one nonidentical candidate with resolved
model-assisted preservation status. That is an eligibility condition, not a
claim of useful quality or sufficient reader sample size. Human acceptance and
the existing export policy still control training eligibility.

## Prespecified descriptive analysis

Count independent task groups, not sentences, operations, reviewer passes, or
multiple variants as independent examples. For this development batch, use
counts, denominators, and paired descriptive tables rather than significance
tests on a model-generated quality score.

1. **Source coverage:** for all 24 allocated groups, report completion, packet
   failures/uncertainties, length compliance, opportunity categories, and source
   model by genre. Report source length continuously; a length violation alone
   is not automatically factual failure or an edit opportunity.
2. **Raw candidate behavior:** per P/T arm, report allocated and attempted
   requests, complete outputs, exact unchanged outputs, nonempty edits, malformed
   results, critical failures, uncertain reviews, and qualified review-ready
   edits. Include the all-allocated denominator and the narrower valid-source
   denominator where relevant.
3. **Coverage versus safety:** separately report raw output failures, rejected
   outputs, fallback-to-U outputs, safe nonidentical edits, and naturally
   unchanged responses. Never merge fallback with successful no-edit behavior.
4. **Matched P/T diagnostic table:** among the same admitted source groups,
   cross-tab preservation dispositions and unchanged/edited status. Add the
   source-only opportunity category. An edited candidate on a no-clear-issue
   source is a potential overediting case, not automatically a failure.
5. **Independent edit diagnosis:** for each resolved candidate, record whether
   the originally identified issue was addressed, not addressed, or replaced by
   a new issue. Use `uncertain` if the criterion is subjective. This is a
   model-assisted problem-resolution assessment, not a reader win.
6. **Inspection examples:** retain every critical failure and uncertainty in a
   private appendix. Select at most eight public-report IDs by a deterministic
   hash order, balanced by genre/source when possible, rather than selecting
   only attractive examples. Full private text stays in the ignored data path.
7. **Operations:** report latency distribution, total tokens including exposed
   reasoning use, actual cost or explicit missingness, retries, finish reasons,
   and checkpoint/provider uncertainty. Present estimates separately.

All 24 original groups remain visible in attrition accounting. A small cell in a
source/genre table describes these briefs; it cannot rank source models or
establish subgroup generality. Do not select a new reward from the largest
feature change or model-review difference in this run.

## What can count as a concrete finding

| Observed pattern | Defensible finding | Next action |
|---|---|---|
| Valid source outputs mostly receive no-clear-issue labels before edit inspection | This short constructed task set has limited model-diagnosed editing opportunity | Retain no-edit examples; design a distinct realistic-task development batch before scaling labels |
| Many sources fail packet review | Source generation or brief design limits this experiment | Diagnose required-fact coverage and conflicting instructions; version the source task, not the editor reward |
| P introduces repeatable scope/claim losses while T avoids them under matched inputs | A concrete compact-baseline failure mode exists on these development items | Preserve challenge cases; test an appropriately versioned policy repair; no SFT benefit has yet been measured |
| Both P and T fail the same relation/voice cases | Input ambiguity or the editing contract may be the bottleneck | Identify the missing legitimate context or narrow scope; do not add invented content |
| Safe nonidentical candidates address independently identified issues | There are specific proposals worth asking a reader to compare | Freeze the review packet and report that human outcomes are still absent |
| Automatic checks pass but semantic review finds a material change | The literal check coverage is incomplete | Keep the failure as a challenge and document the check's limits |
| Reviewer controls fail or reviewers disagree on important content | The semantic review process cannot currently resolve admission | Preserve uncertainty and repair the measurement before collecting positive exports |
| All paths return U or rely heavily on fallback | The policy can be conservative but useful refinement is unestablished | Diagnose whether source opportunity or editing behavior limits coverage |

One counterexample can invalidate a universal safety assertion. A few appealing
examples cannot establish a universal benefit assertion. Report this asymmetry
explicitly when deciding whether there is enough substance to involve a reader.

## Budget, execution, and follow-up

Retain the documented working caps of USD 1 for interface smoke requests and
USD 5 cumulatively for CR-001 inference. Before paid execution, estimate a
conservative maximum using live prices, full input/output token limits,
reasoning policy, number of planned requests, and retry exposure. Cached
successes do not need paid reruns. Log cost uncertainty rather than treating
missing usage as zero. If the estimated worst case exceeds the cap, revise the
scope or record a separate budget decision before sending those requests.

The first diagnostic workflow needs API inference and local CPU tooling only.
There is no need for a cloud GPU yet. Do not download weights, rent hardware, or
start local SFT for this audit. Hardware sizing becomes concrete after accepted
data, student identity, and a sequence-length/tuning workload are established.

Inspect process liveness, growing artifact/log counts, last completed item, and
terminal state after approximately one minute and approximately five times
across expected job duration. A watcher is supplementary. Never start a second
writer merely because a watcher timed out. Report unfinished requests and
unknown cost on failure.

After the root agent supplies artifact paths, this audit's reviewer can perform
two independent passes: source-only opportunity and consistency review first,
then candidate-identity-blinded fidelity and issue-resolution review. Save the
first pass before opening the second. Do not author T candidates in the same
review assignment. Any resulting judgments remain explicitly assistant/model
assessments. The next human-facing update should present the resulting concrete
finding, limitations, and a reviewable packet; it should not ask for a GPU to
compensate for missing evidence.
