# First Development Batch

Plan ID: `CR-001`  
Plan version: `compact-refiner-first-batch-1.1`  
Status: model-assisted preflight executed; human judgments and training outcomes
remain absent. See the [result and deviations](reports/cr001-preflight.md).

Version 1.1 records a pre-generation operational clarification: source-only
fidelity/opportunity review precedes editing, and autonomous agent labels remain
model-assisted. This separates source-generation defects from editor defects.
No candidate output or preference outcome was used to choose this revision.

Read the [preference-readiness audit](preference-readiness-audit.md) for the
pre-human interpretation limits and [decision log](decisions.md) for model
selection. Data and code identities are frozen in the actual run manifest.

## Question

Can bounded editing produce useful Chinese revisions without meaning loss, and
can the data/review pipeline distinguish an accepted edit from an unchanged
case or a failed candidate? This is a feasibility question, not a universal
smell-definition or model-promotion study.

## Sample budget

Prepare 24 independent briefs, six in each of four genres:

- technical explanation;
- practical instructions;
- evidence-based analysis/commentary;
- workplace or public-facing communication.

Each brief supplies audience, voice, a complete fact packet, and a target length
of approximately 300-600 Chinese characters. Keep the first task to one complete
passage. Include constraints, qualifications, or tradeoffs where natural so
preservation is meaningfully tested. Do not create all briefs from one repeated
template with only entity substitutions.

Use two currently available large source models, 12 briefs per model, balanced
three per genre. Choose exact model IDs from the live catalog after checking
license/terms, price, context, and structured/text output behavior. Record the
selection; none is chosen yet. Each brief receives one source draft initially.
Do not retry valid prose simply because it lacks a target smell marker.

All 24 task groups are development. The batch supplies no validation reserve.
It must not use the old sealed reserve, the 87 frozen modifier candidates, or
exposed translation final tests.

## Candidate arms

For each admitted draft, retain U (unchanged), generate P (one frozen compact
prompt baseline), and prepare T (one assistant/model editing proposal). R1 uses
`medium` intensity throughout to avoid mixing intensity effects. H is optional
only when a person actually authors an edit. Assistant reasoning and review do
not count as H or as independent human preference.

Use the versioned prompts in this directory. P must receive the same legitimate
context and instructions intended for the later student. T may expose a useful
editing ceiling, but its provenance and method must be explicit. Candidate
identity, text, operations, and any rejection are durable before reader outcomes.

## Execution order

1. Materialize and hash the 24 briefs/fact packets; validate distinct groups,
   rights, lengths, and coverage. Record any departures from the planned mix.
2. Check live source/student catalog entries and freeze IDs, prompts, decoding,
   reasoning settings, token limits, provider policy, and spending budget.
3. Run at most four interface-smoke requests against constructed development
   fixtures. Verify complete answers, identity, usage, error handling, and
   secret-free logging. These fixtures are not additional independent samples.
4. Freeze the CR-001 run manifest, then generate the ordinary source drafts.
   Freeze separate agent assessments of source fidelity and editing opportunity
   before exposing revisions. Quarantine factual deviations or unresolved source
   fidelity from the main edit comparison; report every exclusion.
5. Produce P and T, retain U, and replay exact edit operations. Preserve every
   failed candidate rather than selecting only successful rewrites for reporting.
6. Perform deterministic and separately attributed semantic review. Eligible
   reader comparisons require preservation-passing candidates. Keep all groups
   in the attrition denominator, including those with no eligible edit.
7. Freeze a blinded, balanced reader schedule before any preference outcome.
   Use the [evaluation policy](evaluation.md) and preserve control mappings.
8. Export actual judgments, complete the experiment report, and decide whether
   to improve the instrument, collect accepted edits, or stop the current policy.

## Reader schedule boundary

The baseline schedule has 24 source items, each assigned to U versus one eligible
candidate. Target 12 U/P and 12 U/T comparisons, balanced across genres and
source models, plus one identical-text and one mirrored-repeat diagnostic in
two short sessions. Assignment uses seed `20260914` and must be frozen before
outcomes. If eligibility prevents the balance, record attrition and freeze a
revised schedule before showing it; do not fill gaps based on preferred results.

One reader sees at most one substantive comparison per original draft in this
batch. More independent readers can use a counterbalanced allocation to cover
the alternate candidate. With one reader, results are personal development
evidence and cannot support a general teacher-versus-student ranking. Human
participation is a real prerequisite; no answer is imputed when it is absent.

## Completion and decision

CR-001 is complete only after the report records actual data counts, prompt/model
identities, checks, human-review state, preference outcomes or explicit missing
outcomes, costs, failures, and the decision. Generating drafts alone is not a
completed reader experiment. A run awaiting a person is marked `awaiting_review`.

Advance data collection when the instrument is usable and there are reviewed
examples demonstrating useful edits or justified no-edit behavior. Do not call
this SFT readiness, reward validation, or proof of generalized preference gain.

## Implementation needed before execution

Development record validation, canonical prompt rendering, the bounded API
client, operation replay, and private artifact logging are implemented under
`src/deaiodorant/refine/` with experiment drivers under `experiments/`.
The full training-data contract validator and SFT/DPO exporters remain planned.
No current preflight output is automatically training-eligible. Keep acquisition,
editing judgments, and future human acceptance separate.
