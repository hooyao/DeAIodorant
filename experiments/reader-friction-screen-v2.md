# Within-Document Friction Enrichment Development Screen

## Status

Protocol `within-document-friction-enrichment-development-2.0` was frozen on
2026-08-22 before reader outcomes. This is a test of deterministic candidate
enrichment, not an edit intervention and not held-out validation.

## Rationale

The first raw-passage screen was stopped after 11 persisted responses. Ten
occupied the same `fairly willing to continue` category, and the reader
described the batch as having no discrimination. Repeating an absolute rating
on another uniform random sample would not identify whether the feature ranking
adds any useful information.

This replacement compares two unchanged passages from the same document. One
is selected by a frozen transparent ranking, and the other is a matched
zero-marker control. The reader may explicitly report no meaningful
difference. No reader outcome from the failed screen was used to define a
feature, threshold, or weight.

## Passage eligibility

Passages inherit the first screen's deterministic completeness gates and add
two exclusions: each passage must end with sentence punctuation, and compact
author-profile blocks are removed. Passages requiring an unseen figure,
algorithm, code block, interview prompt, or truncated neighboring line remain
ineligible.

Documents used before the first raw screen remain excluded. A document from
that failed screen may contribute a different passage because this is still
development work, but the previously selected line and either adjacent line
are excluded. Selection does not use the previous absolute rating.

The resulting pool contains 414 eligible passages in 54 transition documents.
Only 10 documents satisfy every candidate and control constraint: eight InfoQ
and two Machine Heart documents. The source imbalance is retained as a
limitation rather than weakened through looser matching.

## Frozen ranking

Every eligible passage is ranked only against other eligible passages in the
same document. Ties receive deterministic midranks scaled to `[0, 1]`.

The five rank features are:

1. count of complete negative contrast frames and frozen target markers;
2. abstract-shell density;
3. comma, semicolon, and colon density;
4. mean sentence length in CJK characters;
5. ratio of sentences beginning with a referential or connective form.

The target-marker lexicon contains the previously versioned emphatic and meta
frames plus `也就是说`, `正因如此`, `相反`, `反而`, `因此`, `因而`,
`然而`, `不过`, `所以`, and `由此`. This is a candidate ranking, not a
claim that every occurrence is a smell.

A candidate must contain at least one target marker, rank in the top quartile
for marker count, and rank in the top quartile for at least one of the other
four features. Its control must contain no target marker. The pair must also
satisfy all of the following:

- same frozen passage-length band;
- control-to-candidate CJK-length ratio from 0.8 through 1.25;
- sentence-count difference no greater than one;
- at least two source lines between the passages;
- candidate-minus-control rank-sum gap of at least 1.0;
- CJK character-bigram Jaccard similarity of at least 0.02.

The last constraint reduces within-document topic drift. It is a matching
control, not a semantic-similarity claim.

## Reader task and decision rule

The reader answers which passage makes them less willing to continue. The
choices are `A`, `B`, and `no meaningful difference (both acceptable or both
bad)`. Comments are optional, and the reader is not asked to classify a
linguistic feature. Candidate placement is balanced five-to-five and remains
hidden until all responses are complete.

A pair counts as a candidate win only when the candidate is explicitly chosen
as more discouraging. A no-difference response is not a win. The ranking is
directionally useful only if at least eight pairs are decisive and candidates
account for at least 75% of decisive choices. At least four candidate wins and
the directional threshold are both required before any candidate may enter a
later intervention. Optional comments cannot select cases.

## Frozen pair set

| Task | Source | Document | Candidate line | Control line | Markers | Auxiliary votes | Rank gap | Bigram Jaccard |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | InfoQ | b0f066a3a5abd771dc88d05d | 48 | 45 | 2 | 2 | 2.000 | 0.044 |
| 2 | InfoQ | 09c15d722428969f39d55a35 | 36 | 42 | 1 | 2 | 1.833 | 0.057 |
| 3 | Machine Heart | 9f1d90b6ac15dd29465af213 | 49 | 70 | 2 | 1 | 1.250 | 0.021 |
| 4 | InfoQ | f1f34167984d5e508d20f41c | 98 | 36 | 1 | 3 | 1.294 | 0.040 |
| 5 | InfoQ | 38edb35e93d5075f63c4a6cc | 6 | 9 | 1 | 1 | 1.571 | 0.053 |
| 6 | InfoQ | 48a9230fe1ff0bc5832f1e7c | 62 | 20 | 2 | 1 | 1.333 | 0.030 |
| 7 | InfoQ | 38790cda56298be3819d3798 | 95 | 67 | 1 | 2 | 1.643 | 0.052 |
| 8 | InfoQ | 3d2cea36287cf278258bee81 | 112 | 110 | 2 | 2 | 1.433 | 0.037 |
| 9 | InfoQ | 9894f671b6015ea06feb6543 | 33 | 14 | 1 | 2 | 1.750 | 0.038 |
| 10 | Machine Heart | b2e18d9fb55b6c290390b211 | 33 | 6 | 1 | 3 | 1.700 | 0.059 |

## Reproduction identity

Two independent runs produced byte-identical artifacts.

| Artifact | SHA-256 |
|---|---|
| Tasks | `d6fd858c55968da3461604050a15b211c045a2df92313d476f76ef46ea9839c7` |
| Answer key | `31ceac5b56360bf668dce7f1de08d9c432254be3feefd399af5236ac43705375` |
| Protocol | `a717c41dc7932bacf684c2ef2e8353533c551ba1c88c7782d9ad020d4b43254c` |
| Label config | `8ab3fbf59f6c85803789125596fd18561fa4347d63675e00956ca3ede9307179` |

~~~powershell
python experiments/prepare_reader_friction_screen_v2.py `
  --pool F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\analysis_pool.jsonl `
  --output-dir feature_runs/reader-friction-screen-v2 `
  --seed 2026082203
~~~

Generated tasks and the blinded answer key remain under ignored
`feature_runs/`. No handoff file is modified. All passages are transition-only
development material and cannot estimate the primary pre/post effect.
