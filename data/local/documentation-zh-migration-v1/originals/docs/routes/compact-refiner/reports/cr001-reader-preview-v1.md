# CR-001 Reader Preview: First Human Feedback

Recorded: 2026-09-14. Status: one-reader qualitative development feedback;
neither a confirmatory preference result nor evidence of smell removal.

This is a follow-up to the [model-only preflight](cr001-preflight.md). The
original reader packet, A/B key, model assessments, and compact preflight summary
are preserved unchanged. New human feedback is stored in separate records.

## Source and exact responses

The project maintainer responded directly to the three-pair preview. No response
was inferred by an agent. Original typos and wording are preserved in the private
raw record.

| Pair | Verbatim response | Decoded direction | Qualification |
|---|---|---|---|
| 1 | `两段内容并不完全一样，A看上去更好读` | A is the revision | Apparent reading preference, with an unresolved content-difference concern |
| 2 | `B` | B is the revision | Preference stated; strength and semantic acceptance not specified |
| 3 | `A好一些，实话说区别不大` | A is the revision | Explicitly slight preference; retain it as slight rather than converting it to a tie or a strong win |

Set-level observation, verbatim:

> 这3租都没有明显的的ai臭味

This describes the three displayed pairs after comparison. It is not an
independent pre-edit baseline rating, a calibrated per-version smell score, or
an authorship judgment. It also does not establish that every other draft in
the development pool lacks smell.

## What the feedback establishes

The reader directionally prefers these revisions, with different qualifications.
This is real feedback about reading preference. It cannot by itself establish
that the edits preserve every proposition or reduce the project's target smell.
Pair 1 is specifically ineligible for a preservation-passing outcome until its
content concern is resolved. The reader did not separately certify semantic
equivalence for pairs 2 and 3 either.

Do not report a 100% success rate, three validated editing wins, a smell-removal
effect, or SFT/DPO readiness. Retain the difference between an explicit choice,
the magnitude of that choice, and satisfaction of preservation constraints.

The shown examples are two practical-instruction passages and a public notice.
They are useful for exercising order, conditions, and copy editing, but this
reader found no obvious target smell in them. The selected preview therefore
does not test whether a refiner can improve texts with the reader's target
problem. More model runs on similarly selected clean passages would not fix
that coverage gap.

Absence of obvious smell is not a human instruction to keep every passage
unchanged: the same reader still expressed some editing preferences. These
cases can inform ordinary editing or low-smell controls, but must not receive
automatic unchanged labels or be relabeled as smell-positive examples.

## Pair 1 preservation follow-up

A fresh agent reviewed only the displayed pair after the human comment, without
the earlier judgments, model identity key, or fact inventory. Its claim-alignment
record identifies two differences in explicit scope:

- the revision repeats both verification and placement as the affirmative
  condition before hanging, while the original repeats verification there but
  already requires both in its preceding prohibition;
- the original explicitly restricts the mismatch condition to the verification
  process, while the revision states the condition without that phrase inside
  the verification paragraph.

The agent did not establish a definite factual deletion or unsupported addition.
Context may reconcile these formulations, but that is not a resolution of the
human concern. The record remains `human_concern_resolved=false`; it is not a
new preservation pass. Do not guess that these are the exact differences the
reader intended to flag.

The historical T result of 13 model-assisted passes remains a historical
measurement. This human concern demonstrates why it cannot be treated as 13
verified semantic equivalences or automatic training acceptance.

## Data and eligibility

Three direct human preference records were added, bound to their exact A/B
hashes, source-group IDs, presentation hash, and original/revised mapping.
The raw set-level comment is separate from the per-pair choices.

| Item | Current state |
|---|---|
| Human preference responses | 3, from one reader |
| Independently human-certified preservation passes | 0 |
| Pair with reported content-difference concern | 1 |
| Explicitly slight preference | Pair 3 |
| New SFT or DPO exports | 0 |
| Validated smell-removal operations | 0 |
| GPU required for the next step | No |

The private files are
`data/local/compact_refiner/cr001-v1/reader-preview-v1-feedback.json`,
`preferences.reader-preview-v1.jsonl`, and
`pair1-preservation-followup-v1.json` in the same directory. The compact,
versioned follow-up is
`benchmark_results/compact_refiner/cr001-reader-preview-v1-summary.json`.
The old `cr001-summary.json` remains the pre-human snapshot.

The displayed packet SHA-256 remains
`65c497b0455a620bbb44cc0aafc6f77e647bfa628bd327dc1f7a5f0cd581a815`.
The follow-up summary records the exact feedback artifact hash. No external API
call, training job, candidate rewrite, or frozen-input change was needed. The
separate pair 1 follow-up remains an explicitly model-assisted agent assessment.

## Next research decision

Pause expansion of the short, fully specified notice/instruction preview as a
test of smell removal. Keep it as an engineering and ordinary-editing pilot.

For the next development experiment, establish original-only target coverage
before proposing edits. Use ordinary generated drafts for realistic writing
tasks, retain their context, and preserve clear/no-clear/uncertain cases. Do
not ask a generator to produce stereotypically bad AI writing or retry valid
drafts until they fit a desired label. Agent screening is proposal triage;
only actual reader observations can establish reader-perceived target coverage.

Previously exposed, explicitly reader-reported examples may clarify the target
for development discussion only. They are not fresh validation, gold training
targets, or grounds for restarting the paused temporal-selector experiments.
The legacy reserve remains closed.

Record baseline perceived smell, reading preference, and preservation as
separate observations. Preserve no-obvious-smell cases as a comparison group.
After target coverage is established, freeze a bounded editing experiment on
appropriate independent material. No new bulk generation, training reward,
large annotation batch, or GPU allocation follows from these three responses.
