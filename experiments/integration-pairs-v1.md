# Proposition-Decompression Development Intervention

## Status

Protocol `proposition-decompression-development-1.0` was frozen on 2026-08-27
before reader outcomes. This is post-only, single-reader development work, not
held-out validation.

## Rationale

The fourth intervention ended with five revised preferences, four original
preferences, and one no-difference answer. Those treatment totals are not
interpretable because all nine decisive answers selected side B. The reader
also identified a different problem from obvious formulaic AI-style markers:
technical prose can use familiar words yet remain unusually difficult to
assemble as a whole.

This intervention tests a bounded response to that observation. It distributes
an unchanged proposition set across clearer integration units instead of
deleting more framing language or maximizing compression.

## Frozen operator

The `decompress_proposition_chain` operator may:

- split a dense proposition chain at an existing semantic boundary;
- repeat an already-fixed referent when needed to anchor a new sentence;
- turn an existing parallel list into separate, explicitly anchored clauses.

It must:

- preserve every proposition, entity, number, technical term, negation,
  qualifier, uncertainty marker, attribution, and logical relation;
- retain authorial voice and domain terminology;
- keep CJK length between 95% and 125% of the source;
- increase sentence count;
- avoid adding premises, evidence, mechanisms, examples, or causal relations;
- avoid treating formulaic-marker removal as the intervention target.

Every edit has a structured operation record, three explicit proposition-
support checks, locked literals, voice anchors, exact numeric preservation, an
exact source hash, and a full diff.

## Passage set

The six intervention passages come from previously unselected post-period
documents. The set balances source three-to-three and contains two passages
each from industry reporting, research summaries, and technical practice.

| Base pair | Source | Format | Date | Document | Line | Revised/original CJK ratio | Added sentences |
|---|---|---|---|---|---:|---:|---:|
| 01 | InfoQ | Industry reporting | 2025-09-29 | 4e2108f7b04c3847a564bfd4 | 1 | 1.078 | 4 |
| 02 | InfoQ | Industry reporting | 2026-04-10 | 8873215c1410ad3babd84bbb | 1 | 1.006 | 4 |
| 03 | InfoQ | Technical practice | 2026-04-02 | 24fb6134577093ddcff37689 | 8 | 1.080 | 4 |
| 04 | Meituan | Research summary | 2026-06-11 | 610ba7a9b468d78a3d59def1 | 18 | 0.954 | 5 |
| 05 | Meituan | Research summary | 2026-06-05 | 75583336dc40b896d68598d0 | 11 | 1.045 | 3 |
| 06 | Meituan | Technical practice | 2026-03-20 | 69566776f457ecf4c98ecbe0 | 34 | 1.080 | 3 |

The ratio column is revised CJK characters divided by original CJK characters.
The six intervention originals are balanced three on A and three on B.

## Position diagnostics

The reader sees eight tasks:

- six distinct intervention pairs;
- one pair whose A and B texts are byte-identical;
- one nonadjacent repetition of pair 01 with A and B swapped.

The identical control must receive a no-difference answer. The two presentations
of pair 01 must agree on content rather than display side. Aggregate treatment
preference is not interpreted unless both conditions pass.

The controls diagnose the complete side-B pattern from project 6. They are not
attention checks and are not counted as intervention wins.

## Reproduction identity

Two independent generations must reproduce these frozen artifacts:

| Artifact | SHA-256 |
|---|---|
| Tasks | `cf84bbfa9a2add22bb86adcd6ad9f4841f85cbe943e8ed93bcdbe09d9be74389` |
| Answer key | `73edf62b5b5be63f2e3efa67bf974e62a6c80f02293b5bfa6a83439c7975eba8` |
| Protocol | `57c57847d275daa0b708ee463ff2ffd14feeafd57b5d0a2e3e4a67e205823779` |
| Label config | `0ff910c04d65c908b917d4c962ae185d6bab829e66df3cb2826d98c60b92116a` |

~~~powershell
python experiments/prepare_integration_pairs_v1.py `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1 `
  --output-dir feature_runs/integration-pairs-v1 `
  --seed 2026082705
~~~

Generated tasks, diffs, full operation logs, source text, and the blinded answer
key remain under ignored `feature_runs/`.

## Reader outcome

All eight tasks were completed. Both position diagnostics passed:

- the byte-identical A/B control received a no-difference answer;
- pair 01 was preferred in its original form both before and after A/B sides
  were reversed.

The six unique interventions therefore enter development interpretation. Three
revisions were preferred and three originals were preferred, with no ties. The
generic proposition-decompression operator has no aggregate advantage and must
not be promoted.

The reader localized a narrower residual problem in pair 03. Its revision was
preferred, but the phrase `AI 原生时代全新的算力服务需求` remained difficult:
the head noun arrived after a long modifier stack, and the stack itself did not
state what was substantively new. This yields a more specific head-delay and
low-anchor abstract-stacking hypothesis. See
[Head-Final Modifier Delay Probe](head-final-modifier-probe.md).

## Interpretation boundary

This round can only establish whether proposition decompression deserves
further development. It cannot establish a general smell detector, a pre/post
time effect, or authorship. The six passages were selected after a reader-
reported hypothesis and deterministic discovery scan, so all outcomes are
development evidence. Independent validation still requires fresh documents,
multiple readers, and a frozen analysis plan.
