# Fresh Post-Only Conservative Reframing Intervention

## Status

Protocol `post-only-conservative-reframing-development-4.0` was frozen on
2026-08-27 before reader outcomes. This is a development intervention, not
held-out validation.

## Rationale

The post-only raw comparison was stopped because two passages from the same
document shared too much authorial and editorial style. Matching raw passages
from different documents would restore style variation but introduce content
interest and argument-difficulty confounds. This intervention instead compares
the same source content before and after a bounded conservative edit.

The batch uses 10 new post-period documents that were not selected for project
5. Five come from InfoQ and five from the Meituan technical blog. Format
composition is four industry-reporting, three research-summary, and three
technical-practice passages.

## Frozen edit operator

Each edit may:

- reduce ornamental contrast, clarification, and emphasis framing;
- merge repeated staged pivots;
- state an already-present argument chain more directly;
- repair local argument structure without adding a premise.

Each edit must:

- retain necessary contrast, negation, modality, attribution, and uncertainty;
- preserve explicit subjects, predicates, objects, and referents;
- preserve propositions, entities, numbers, technical terms, rhythm, and
  authorial voice;
- avoid maximum compression and uniformly flat prose;
- avoid adding a new target marker while removing another one.

The reader answers only which version makes them more willing to continue.
Comments are optional, and no linguistic or authorship classification is
requested.

## Preservation audit

The generator verifies:

- exact source body hashes against the validated handoff;
- 30 explicit original-to-revision proposition-support checks;
- pair-specific locked entities and technical terms;
- exact numeric-literal sequences;
- pair-specific voice anchors;
- one structured full-passage operation with operator code, before/after text,
  and reason for every pair;
- balanced original placement, five on A and five on B.

Two initial revisions were rejected before freezing because they weakened
assertion strength (`will` to `may`) or replaced a breakthrough claim with a
weaker improvement claim. A later audit also removed a newly introduced causal
marker. The frozen versions retain the original certainty and voice.

The surface manipulation count decreases from 16 frozen target markers in the
originals to three in the revisions. Remaining markers express necessary
contrast or causality. Marker reduction confirms manipulation only; it is not
evidence of reader benefit.

## Reader outcome

All 10 tasks were completed. The decoded treatment totals are five revised
preferences, four original preferences, and one no-difference answer. These
totals are not interpretable as an operator effect: all nine decisive answers
selected display side B, while original placement was balanced five-to-five.
There were zero A selections.

This complete side pattern confounds pair-specific readability with position,
order, or display effects. The apparent 55.6% revised share among decisive
answers must not be reported as evidence of benefit. No operator-specific
conclusion is drawn.

The reader reported that most A versions were difficult, but not mainly because
of an obvious AI-style marker. Individual words were understandable while the
combined technical prose felt unusually difficult to assemble. This is retained
as a new development observation, not a linguistic gold label or authorship
judgment.

The result motivates a separate compositional-integration hypothesis and the
position diagnostics in the next experiment. See
[Compositional Integration Burden Probe](compositional-burden-probe.md) and
[Proposition-Decompression Development Intervention](integration-pairs-v1.md).

## Frozen passage set

| Task | Source | Format | Date | Document | Line | Operator | Original markers | Revised markers |
|---:|---|---|---|---|---:|---|---:|---:|
| 1 | Meituan | Technical practice | 2026-04-07 | 4c4d1156bf248a78ba057cb3 | 1 | Clarify argument structure | 1 | 0 |
| 2 | InfoQ | Industry reporting | 2026-06-15 | 7c1423cab64a9a1b24d75243 | 41 | Merge repeated reframing | 1 | 1 |
| 3 | InfoQ | Industry reporting | 2026-01-07 | da81d4c0f5b616b43f9e1472 | 93 | Remove ornamental emphasis | 2 | 0 |
| 4 | InfoQ | Industry reporting | 2025-11-28 | e6b904412ae6774c9ee56964 | 16 | Clarify argument structure | 3 | 1 |
| 5 | Meituan | Research summary | 2026-05-15 | fdbd90f96ec1d4752373dcf1 | 1 | Remove ornamental emphasis | 1 | 0 |
| 6 | InfoQ | Technical practice | 2026-02-13 | 21129f35e0f1ae2b265bb287 | 27 | Clarify argument structure | 2 | 1 |
| 7 | Meituan | Technical practice | 2026-08-20 | a174fe26e705b96c18acb00e | 105 | Direct contrast | 0 | 0 |
| 8 | Meituan | Research summary | 2026-07-24 | 398d56824414e91464ffc3d8 | 78 | Direct contrast | 2 | 0 |
| 9 | Meituan | Research summary | 2026-07-24 | ee642b95d3e1e32aea9e8ccf | 1 | Clarify argument structure | 2 | 0 |
| 10 | InfoQ | Industry reporting | 2025-12-30 | ddb4214a54ff80efa0f5b210 | 19 | Merge repeated reframing | 2 | 0 |

## Reproduction identity

Two independent runs produced byte-identical artifacts.

| Artifact | SHA-256 |
|---|---|
| Tasks | `881952f731233037a90eb4b6e31e05b4bfa4a43a353a67dc098a289091ae752a` |
| Answer key | `8152816cd789175f759588a95145dfdae78fcdafeaaa3da96eeb84a91b0bafab` |
| Protocol | `34cf0672fd3a1f8a7e778ef46e2dce833c7dea1a41efc90acbceb75712b619c7` |
| Label config | `168369c7bd2af58b6d3570f50885d4d337008b3f9f071930e935352c63951e03` |

~~~powershell
python experiments/prepare_refinement_pairs_v4.py `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1 `
  --output-dir feature_runs/refinement-pairs-v4 `
  --seed 2026082702
~~~

Generated tasks, full operation logs, diffs, and the blinded answer key remain
under ignored `feature_runs/`.
