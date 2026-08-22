# Read-Only Handoff Transition Probe

## Purpose

This experiment uses a locally materialized corpus handoff to expand
deterministic feature discovery without collecting new material. It does not
estimate the primary pre/post effect because the handoff contains no documents
published on or after 2025-07-01.

The analysis has two bounded purposes:

1. discover within-transition feature trends while controlling source and
   document length;
2. describe the 23 unmatched pre-period Machine Heart candidates with
   feature-wise Huber weights, without deleting any document.

The one reader observation is profiled only after feature extraction. It is not
used as an authorship label, validation label, or feature-selection target.

## Handoff audit

The read-only inputs use protocol `analysis-corpus-handoff-1.0` and are marked
`exploratory_pool_not_final_corpus`.

| Check | Result |
|---|---:|
| Indexed documents | 119 |
| Strict UTF-8 bodies readable | 119 |
| Body SHA-256 matches | 119 |
| CJK metadata matches | 119 |
| Line-count metadata matches | 119 |
| Overlap with tracked pilot IDs | 0 |
| Pre-period candidates | 23 |
| Transition discovery documents | 96 |
| Post-period documents | 0 |

Source composition is 23 pre-period Machine Heart documents, 53 transition
Machine Heart documents, and 43 transition InfoQ documents. Four provenance
decisions are human-reviewed and 115 are model-assisted measurements. Nine
value decisions are human-kept and 110 are model-assisted measurements. These
statuses are not human gold.

Machine Heart visibility remains `editorial_source_only_unverified`. The 23
pre-period documents therefore remain unmatched candidates rather than members
of a final primary cohort.

## Frozen exploratory method

The probe extracts deterministic surface, punctuation, discourse-marker,
rhetorical-hypothesis, and title-form features. Raw counts, MATTR, type-token
ratios, and entropy values are excluded from the transition trend test because
of their direct length sensitivity. Fifty-three normalized or structural
features remain.

For each feature, the transition analysis:

1. computes a Spearman partial correlation with publication date separately
   inside InfoQ and Machine Heart;
2. controls log CJK length within each source;
3. combines the two source-specific correlations by source sample size;
4. permutes date ranks 5,000 times within source;
5. records leave-one-document-out direction stability;
6. applies Benjamini-Hochberg correction across the 53 features.

This is discovery analysis. A source-consistent transition trend is not a
pre/post effect and cannot validate a refinement target.

For the pre-period candidates, Huber locations and weights are computed
separately for every feature with tuning constant 1.5. Unweighted values and
full distributions are retained. The document-level mean weight is descriptive
only and cannot be used for admission or deletion.

## Transition results

No feature has BH q below 0.10.

| Feature | Combined partial rho | InfoQ rho | Machine Heart rho | Permutation p | BH q | LOO stability |
|---|---:|---:|---:|---:|---:|---:|
| Quote-mark density | 0.286 | 0.355 | 0.229 | 0.0054 | 0.286 | 1.00 |
| Dash density | 0.250 | 0.221 | 0.274 | 0.0138 | 0.336 | 1.00 |
| URLs per 1,000 CJK | 0.240 | 0.204 | 0.270 | 0.0190 | 0.336 | 1.00 |
| List-item ratio | -0.224 | -0.172 | -0.266 | 0.0366 | 0.388 | 1.00 |
| Emphatic frames per 1,000 CJK | 0.221 | 0.262 | 0.189 | 0.0320 | 0.388 | 1.00 |
| Title colon present | 0.206 | 0.268 | 0.156 | 0.0470 | 0.415 | 1.00 |

Quote marks, dashes, and emphatic frames are source-consistent discovery
directions. The URL and list signals are likely format-sensitive. None may be
described as a reader-disliked pattern without a bounded intervention.

The existing focal features do not form one common trend:

| Feature | Combined partial rho | Source directions consistent | Permutation p | BH q |
|---|---:|---|---:|---:|
| Complete negative contrast frames | 0.050 | No | 0.626 | 0.834 |
| Emphatic frames | 0.221 | Yes | 0.032 | 0.388 |
| Meta frames | 0.062 | Yes | 0.561 | 0.804 |
| Total punctuation density | 0.088 | No | 0.396 | 0.670 |
| Colon density | 0.099 | No | 0.336 | 0.670 |

Complete negative contrast frames rise weakly in transition InfoQ but are flat
to slightly lower in transition Machine Heart. This handoff does not strengthen
the earlier post-period complete-frame result. It instead shows why source
matching remains necessary.

## Pre-period distribution audit

The lowest descriptive mean Huber weights are:

| Document | Date | CJK characters | Mean weight | Minimum feature weight |
|---|---|---:|---:|---:|
| 0bacfeaea20d086539948d1d | 2021-07-20 | 1,580 | 0.79 | 0.09 |
| cbf364e6fe771c6b1f5d5147 | 2021-10-24 | 4,027 | 0.85 | 0.17 |
| 774e84408a478c4cdef91612 | 2022-06-23 | 1,367 | 0.87 | 0.17 |
| 8d03602a0069443799951a8d | 2021-10-21 | 992 | 0.93 | 0.16 |
| 70294f6e4051db3347bfcba2 | 2021-10-18 | 2,864 | 0.94 | 0.20 |

The first document is downweighted mainly for dash, punctuation, parenthesis,
list, and paragraph-structure features in a technical article. The next two are
strongly affected by title questions, list formatting, digits, and discourse
markers. These are format signals, not evidence that the articles should be
removed.

All 23 documents remain in the unweighted distribution artifacts. Machine
Heart visibility is unverified, and no post-period Machine Heart match exists
in this handoff. The existing limitation that generic typicality did not
identify the disliked 2022 Red Hat passage remains unchanged; no manual weight
is introduced here.

## Reader-observation case

The transition document `55a8c05716103aaced6ecf7f` has one diagnostic reader
observation. Its largest same-source robust deviation is only 1.84, for a digit
in the title. Comma density reaches robust z 1.66; sentence-length
autocorrelation reaches 1.18; emphatic-frame density reaches 0.72.

The current deterministic features therefore do not make this reader-observed
case a strong multivariate outlier. This is a representation limitation, not a
reason to treat the observation as an authorship label or to tune thresholds
against one document.

## Decision

This handoff substantially improves discovery coverage but does not fill the
missing validation data:

- retain quote-mark density, dash density, and emphatic-frame density as
  transition discovery directions;
- do not promote them to smells or product rules;
- do not generalize the complete contrast-frame direction across sources;
- keep all pre-period candidates and their unweighted feature values;
- require new post-period samples matched by source, topic, format, length, and
  visibility for the primary analysis;
- require new cross-genre, multi-reader interventions for product validation.

## Reproduction

~~~powershell
python experiments/handoff_transition_probe.py `
  --manifest F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\manifest.json `
  --pool F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\analysis_pool.jsonl `
  --reader-observations F:\MyProjects\DeAIodorant\data\local\translation_v2_review\reader_style_observations.jsonl `
  --pilot-root data/pilot/monthly `
  --output-dir feature_runs/handoff-transition-v1-1 `
  --permutations 5000 `
  --seed 20260822 `
  --tuning-constant 1.5
~~~

Reproduction identity:

| Artifact | SHA-256 |
|---|---|
| Handoff manifest | 00bbd66d54e7beabd03a86c87031ef0cd7cc7b49c6eb38bce1c5dc8f7e98a604 |
| Analysis pool | 58697a9c490cb316d8af8d1bd07980b6d8a0de59fd34add3e47ba11ba8712da2 |
| Reader observation | d9666a3bf73e0ececac6cdd0d32c4fd68d8ed4f59c6994d4b8678e0a24a92d5b |
| Results | b07b1897d922723ba028bc98163ca4dcdf7f438f8dcf1baa98af4e9619cf3d15 |

The handoff files remain unmodified. Generated matrices and weights remain
under ignored `feature_runs/`.
