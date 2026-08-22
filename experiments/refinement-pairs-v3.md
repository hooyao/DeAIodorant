# Third-Round Cross-Genre Development Intervention

## Status

Protocol `conservative-reframing-development-3.0` was frozen on 2026-08-22
before reader outcomes. This is a development intervention, not held-out
validation: all source documents belong to the transition handoff that has
already been used for feature discovery.

## Design

The round contains 12 new passages from 12 distinct documents:

| Genre stratum | Pairs |
|---|---:|
| Technical practice | 4 |
| Research summary | 4 |
| Industry reporting | 4 |

No passage or document was used in the first two intervention rounds. The
single transition document with a reader style observation is excluded. All
source documents are transition-period material and must not enter the primary
pre/post comparison.

The edit operator remains conservative:

- reduce ornamental contrast, clarification, and emphasis framing;
- retain every necessary contrast, negation, qualification, uncertainty, and
  attribution;
- preserve explicit subjects, predicates, objects, and referents;
- preserve propositions, entities, numbers, technical terms, rhythm, and
  authorial voice;
- avoid maximum compression and uniformly flat prose.

The reader answers only which version makes them more willing to continue.
Comments are optional, and no linguistic classification is requested.

## Passage set

| Pair | Genre | Document | Lines |
|---|---|---|---:|
| contrast-v3-01 | Technical practice | 44ff5a1d8bda9c7b50f6290f | 36 |
| contrast-v3-02 | Technical practice | c4f3d04d7db01e65460fb2dd | 14 |
| contrast-v3-03 | Technical practice | ed4b0601b5481ee4065a337a | 26 |
| contrast-v3-04 | Technical practice | 2e209708bce31c124797ce6c | 63–65 |
| contrast-v3-05 | Research summary | 10b4ff947e750938d62a417a | 21 |
| contrast-v3-06 | Research summary | 7103a1b4c0cb80218a653a03 | 46–48 |
| contrast-v3-07 | Research summary | 646b73aae2b0dc8f311a9f0c | 18–20 |
| contrast-v3-08 | Research summary | a76e84a2a44062b098288efc | 29–32 |
| contrast-v3-09 | Industry reporting | d4407ed937d0f78f325c3fbd | 5–10 |
| contrast-v3-10 | Industry reporting | 3c33241e2bb2fd68fb3c6147 | 1–7 |
| contrast-v3-11 | Industry reporting | 9f693cf901d640ffb7312bd9 | 52–57 |
| contrast-v3-12 | Industry reporting | 51ad0427b938c45e289e9d1a | 1–8 |

## Audit

The generator records 19 exact before/after operations, 39 proposition-support
checks, pair-specific locked literals, numeric-literal equality, retained
contrasts, and voice anchors. All gates pass. The frozen marker diagnostic
falls from 21 instances in the originals to six in the revisions; the
remaining markers occur inside preserved quotations, necessary contrasts, or
voice-bearing text.

Original placement is balanced: six originals appear as A and six as B. Two
independent runs produced byte-identical artifacts.

| Artifact | SHA-256 |
|---|---|
| Tasks | f0ee5c5cce52f793d84be891c8e38e307b05c533c655889c3b31c37155a8df04 |
| Answer key | 83ec5ac78c7a862d6d1750e1282b2bb7e748c84378dfa449373948ffe4abbe86 |
| Protocol | fb91136846ded20bb3d5cb41614f82762bb3d7f42d160bf90d840ee2747db4f0 |
| Label config | 9f3a55c8e2e6191ff43c0d27558ffb77ea1fa15a98bbf0c5ac7e173083283a27 |

## Reproduction

~~~powershell
python experiments/prepare_refinement_pairs_v3.py `
  --pool F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\analysis_pool.jsonl `
  --output-dir feature_runs/refinement-pairs-v3 `
  --seed 20260822
~~~

Generated tasks and the answer key remain under ignored `feature_runs/`. The
answer key must not be shown before all responses in this round are complete.
