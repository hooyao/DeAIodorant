# Raw-Passage Reader-Friction Development Screen

## Status

Protocol `raw-passage-friction-screen-development-1.0` was frozen on
2026-08-22 before reader outcomes. This is a development candidate screen, not
an intervention round and not held-out validation.

## Rationale

The third intervention round produced four revised wins, one original win, and
seven ties or neither-preferred judgments. The reader reported that almost all
source passages had little obvious smell. This indicates a candidate-selection
failure: marker presence and genre balance did not identify passages with
enough baseline friction to benefit from conservative editing.

This screen therefore shows unchanged passages before any edit is prepared. It
measures willingness to continue reading and does not ask the reader to identify
AI authorship or classify a linguistic feature.

## Sampling design

The batch contains 24 transition-period passages from 24 documents in the
read-only corpus handoff. InfoQ and Machine Heart contribute 12 passages each.
Within each source, four passages are sampled from each frozen CJK-length band:

| Band | Inclusive CJK characters | Passages per source |
|---|---:|---:|
| Short | 120-159 | 4 |
| Medium | 160-199 | 4 |
| Long | 200-360 | 4 |

The deterministic completeness gates require at least two sentence endings,
at least 50% CJK characters among visible characters, and no more than 520
total characters. They reject URLs, interview questions, captions, leading
punctuation fragments, passages ending in a question or colon, obvious
dependent line starts caused by extraction, and references that require an
unseen figure or algorithm. One passage is allowed per document.

All documents previously exposed through a reader rating, intervention, or
explicit style observation are excluded. The selection uses no smell feature,
marker count, model score, reader outcome, or author-provenance label. The
eligible pool contains 463 passages from 55 documents after the frozen gates.

## Reader task

The reader answers one required question:

> After reading this original passage, how willing are you to continue?

The ordered choices are:

1. very willing to continue;
2. fairly willing to continue;
3. not very willing to continue;
4. not at all willing to continue.

An optional free-text comment is available. The instruction explicitly says
not to judge whether the passage was written by AI and not to analyze its
linguistic features.

## Frozen follow-up gate

Only passages rated `not very willing to continue` or `not at all willing to
continue` may enter the next development intervention. If fewer than four
passages qualify, another fresh raw-passage screen must be run; acceptable
passages must not be edited more aggressively to manufacture a contrast.

At most eight passages may enter the intervention. If more than eight qualify,
the lower rating is taken first and ties use the precomputed follow-up priority
below. Optional comments cannot affect selection. Once shown in this screen,
all 24 documents are development-exposed and cannot be described as held-out
validation material.

## Frozen passage set

| Task | Source | Document | Date | Line | Band | CJK | Priority |
|---:|---|---|---|---:|---|---:|---:|
| 1 | InfoQ | cf88120b3afa80da3fc4c302 | 2023-12-20 | 20 | Short | 154 | 21 |
| 2 | InfoQ | 3d2cea36287cf278258bee81 | 2025-01-16 | 50 | Long | 272 | 6 |
| 3 | Machine Heart | 9f1d90b6ac15dd29465af213 | 2023-03-27 | 26 | Long | 331 | 16 |
| 4 | InfoQ | ca20838db88af51d53f9d94f | 2024-04-29 | 30 | Medium | 171 | 13 |
| 5 | Machine Heart | e9d24bfa7ebff01c6a08c4fb | 2024-05-30 | 60 | Medium | 193 | 2 |
| 6 | InfoQ | 32820b09ec8dd3edac07c47f | 2023-12-07 | 19 | Long | 237 | 14 |
| 7 | InfoQ | 8edbbf17c05ba07ef9db5e86 | 2023-02-25 | 90 | Long | 295 | 5 |
| 8 | InfoQ | 3729e9b9209e427e19e16173 | 2025-02-13 | 18 | Short | 125 | 9 |
| 9 | InfoQ | 78c8f407c8d04f43bd8907f5 | 2024-01-09 | 3 | Medium | 172 | 4 |
| 10 | Machine Heart | fad56cf7dd43cacc459a9b91 | 2023-09-18 | 23 | Short | 147 | 23 |
| 11 | Machine Heart | 44f7193de55b94460aa94c83 | 2023-09-08 | 19 | Short | 156 | 1 |
| 12 | Machine Heart | 552a90a3f24cf3a0a56ae17b | 2023-09-19 | 30 | Medium | 196 | 18 |
| 13 | InfoQ | ff33cd9163c1c6a848fa040f | 2023-07-25 | 50 | Long | 224 | 10 |
| 14 | Machine Heart | 043edbbdbc99db8af9111e6c | 2024-06-11 | 21 | Long | 229 | 3 |
| 15 | InfoQ | c43904af3434cd97a9c1c348 | 2025-05-21 | 7 | Short | 137 | 20 |
| 16 | Machine Heart | 6d28870921e2543cc882d1a0 | 2023-10-24 | 4 | Short | 159 | 19 |
| 17 | InfoQ | 82ff13fc3eaf733f81673809 | 2025-03-06 | 15 | Medium | 161 | 22 |
| 18 | Machine Heart | e7bdd871f45cc11e19b00f02 | 2023-08-04 | 7 | Medium | 161 | 15 |
| 19 | InfoQ | f1f34167984d5e508d20f41c | 2023-06-27 | 31 | Medium | 170 | 24 |
| 20 | Machine Heart | 6ef00b4fadbccbd00b6f011c | 2023-06-25 | 6 | Long | 239 | 12 |
| 21 | Machine Heart | b22137fdaff3ca8dc1d72095 | 2023-07-26 | 86 | Short | 123 | 17 |
| 22 | Machine Heart | f58aa7e373f216c50420cc5b | 2023-06-09 | 16 | Medium | 184 | 11 |
| 23 | InfoQ | 48a9230fe1ff0bc5832f1e7c | 2023-02-15 | 48 | Short | 159 | 7 |
| 24 | Machine Heart | e89331895381298c2efeba0b | 2023-08-07 | 22 | Long | 206 | 8 |

## Reproduction identity

Two independent runs produced byte-identical artifacts.

| Artifact | SHA-256 |
|---|---|
| Tasks | `251f2034216e9063b55d4912162eb19fb5c214267fa6941e617aac97a9cafd42` |
| Protocol | `0d448d12925aa9b808b4c0d8272b3703e15ac6ce686595bec86de1f8cb7bdbd4` |
| Label config | `0f79332c65416c61c02c984533c7e61d2afd68b6d7eafb900ca03e4a9ba3e698` |

~~~powershell
python experiments/prepare_reader_friction_screen_v1.py `
  --pool F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\analysis_pool.jsonl `
  --output-dir feature_runs/reader-friction-screen-v1 `
  --seed 2026082202
~~~

Generated tasks remain under ignored `feature_runs/`. No handoff file is
modified. This transition-only screen cannot estimate the primary pre/post
effect or substitute for a matched post-period corpus.

## Outcome

The reader stopped the screen early because the passages felt the same and the
batch had no useful discrimination. Label Studio persisted 11 completions even
though the reader reported completing 12; the unpersisted response is not
imputed.

| Rating | Persisted count |
|---|---:|
| Very willing to continue | 0 |
| Fairly willing to continue | 10 |
| Not very willing to continue | 1 |
| Not at all willing to continue | 0 |

The dominant category contains 90.9% of persisted responses. Only one passage
reaches the frozen follow-up gate, below the required minimum of four. The
remaining tasks are terminated rather than completed for protocol appearance.
No intervention will be prepared from this batch.

This is both an instrument and sampling failure. Absolute four-level ratings
provided almost no separation, while uniformly sampled editorial passages were
mostly acceptable. The replacement development design should test whether a
frozen deterministic ranking enriches for friction by comparing two passages
from the same document and allowing an explicit no-meaningful-difference
response. It must not treat a forced relative choice as evidence of a smell.

The complete persisted outcome and early-stop decision are stored in
`data/annotations/reader-friction-screen-v1.json`.
