# Fresh Post-Only Reader-Friction Discrimination Screen

## Status

Protocol `post-only-friction-discrimination-development-3.0` was frozen on
2026-08-22 before reader outcomes. This is a single-reader development
calibration, not an intervention and not held-out validation.

## Corpus boundary

All passages come from the validated 50-document
`post-reader-corpus-handoff-1.1` at
`F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1`. Its manifest
SHA-256 is
`acde6900ae8b26b8da8821424be420ff48433752297c3f021e1a7e05ccfb2b14`.
Every selected document was published on or after 2025-07-01 and has not
appeared in an earlier reader task.

The batch contains 12 pairs from 12 documents:

| Source | Pairs |
|---|---:|
| InfoQ | 6 |
| Meituan technical blog | 6 |

| Format | Pairs |
|---|---:|
| Technical practice | 6 |
| Research summary | 2 |
| Industry reporting | 4 |

Only two research-summary documents yielded both a complete ranked candidate
and a complete matched control after formatting gates. The protocol retains
that limitation rather than admitting PDF labels, download metadata, author
profiles, or list fragments to force a four-pair format quota.

## Passage construction

The handoff bodies preserve source line breaks. Some Meituan pages split
sentences at inline emphasis tags. The generator deterministically rejoins
adjacent short lines into non-overlapping 120-360 CJK-character passages while
retaining source text and line breaks. It rejects:

- code, URLs, figure-dependent text, captions, and interview prompts;
- truncated passages and passages without terminal sentence punctuation;
- author biographies, paper-download labels, original-link metadata, and
  navigation labels;
- reconstructed segments containing more than one short heading-like line.

This produces 462 eligible passages in all 50 handoff documents. Forty
documents are pairable before format and source quotas; 27 remain after the
frozen marker-plus-structure and local-matching gates.

## Candidate and control ranking

The ranking is deterministic and computed only within each document. The
candidate must contain at least one frozen target marker and rank in the top
quartile for at least one auxiliary feature. Auxiliary features are
abstract-shell density, separator density, mean sentence length, and
referential-opening ratio. The control contains no target marker.

Each pair satisfies:

- control-to-candidate CJK-length ratio from 0.7 through 1.4;
- sentence-count difference no greater than two;
- source-line starts at least two lines apart;
- candidate-minus-control rank-sum gap of at least 0.75;
- CJK character-bigram Jaccard similarity of at least 0.015.

These are candidate-enrichment rules, not validated smell labels. Candidate
placement is balanced six-to-six and remains hidden until all responses are
complete.

## Reader task and decision rule

The reader answers which passage from the same post-period document makes them
less willing to continue. The choices are `A`, `B`, and `no meaningful
difference (both acceptable or both bad)`. Comments are optional. No authorship
or linguistic-feature classification is requested.

The batch has useful discrimination only if at least four of 12 pairs are
decisive. The deterministic ranking is directionally useful only if at least
eight pairs are decisive and the ranked candidate accounts for at least 75% of
decisive choices. At least four candidate wins and the directional threshold
are both required before any passage may enter intervention development. A
no-difference response is not a win, and comments cannot select passages.

## Frozen pair set

| Task | Source | Format | Date | Document | Candidate line | Control line | Markers | Auxiliary votes | Rank gap | Bigram Jaccard |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | InfoQ | Industry reporting | 2025-09-24 | 4121a1ef99d626111ffe59c6 | 11 | 14 | 1 | 3 | 1.731 | 0.075 |
| 2 | Meituan | Technical practice | 2026-03-13 | fbed7012bab78d329a4a523f | 91 | 143 | 1 | 3 | 1.963 | 0.033 |
| 3 | InfoQ | Industry reporting | 2026-06-02 | 7f94b33a5bd4833a79204e52 | 39 | 33 | 2 | 3 | 2.600 | 0.057 |
| 4 | InfoQ | Technical practice | 2026-02-26 | b67f13dfff28e0d399f298b1 | 145 | 5 | 1 | 3 | 1.750 | 0.037 |
| 5 | InfoQ | Industry reporting | 2025-12-10 | 886c72b909098cc5ec646704 | 13 | 8 | 1 | 3 | 1.929 | 0.063 |
| 6 | Meituan | Research summary | 2026-04-27 | 1b1059627ccd253b4042aa60 | 72 | 54 | 1 | 2 | 1.333 | 0.062 |
| 7 | Meituan | Technical practice | 2026-08-07 | 4e5a10869cabea3263bb576e | 104 | 116 | 1 | 3 | 1.857 | 0.062 |
| 8 | InfoQ | Technical practice | 2026-02-09 | 86acdf6932b6036ea979c084 | 105 | 124 | 2 | 3 | 2.591 | 0.030 |
| 9 | Meituan | Research summary | 2026-04-02 | 0a3e603aa9a9ad420334a890 | 23 | 66 | 1 | 2 | 1.400 | 0.031 |
| 10 | Meituan | Technical practice | 2026-04-20 | f8ecc915a65b4a79429f9fce | 28 | 1 | 1 | 3 | 2.125 | 0.152 |
| 11 | Meituan | Technical practice | 2026-05-07 | 0480ba19736016aeaa0c7d93 | 63 | 65 | 1 | 3 | 2.318 | 0.036 |
| 12 | InfoQ | Industry reporting | 2026-04-15 | 061767be12418dbf53feaf1d | 87 | 17 | 3 | 3 | 2.688 | 0.039 |

## Reproduction identity

Two independent runs produced byte-identical artifacts.

| Artifact | SHA-256 |
|---|---|
| Tasks | `bbb4c030f25eea43854377b1bfd291d57f8bd20ba41cc69ca3ba8d1e00250122` |
| Answer key | `a7ee8b9f4fd83003731f44ca48329b71bff76c07f22f0403ddff59b76144d4f8` |
| Protocol | `752397500afef679c87121534fc32bc2f30e7e7921c809e8ce059eaf6913eb90` |
| Label config | `5c0181d7973346b536d3d8c550a57d33a8fa8b4653ac9872a6deb323b15755da` |

~~~powershell
python experiments/prepare_reader_friction_screen_v3.py `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1 `
  --output-dir feature_runs/reader-friction-screen-v3 `
  --seed 2026082204
~~~

Generated tasks and the blinded answer key remain under ignored
`feature_runs/`.

## Outcome and termination

The reader stopped after six pairs because same-document sampling made most
passages stylistically similar and therefore provided little useful contrast.
Four responses were no meaningful difference, two selected the control as more
discouraging, and none selected the ranked candidate. One optional comment
stated that both passages had obvious AI-style smell.

The original rationale was to control source, topic, author, and format. In
practice it also controlled away much of the stylistic variation required by a
discrimination screen. This is an over-controlled comparison design. The six
responses are retained as design diagnostics, but neither the discrimination
nor enrichment threshold is evaluated, and no intervention may use this
batch.

A replacement must compare passages from different documents while matching
source, topic, format, length, and visibility. It must retain the explicit
no-difference response and cannot use the optional comments for selection.

The complete early-stop outcome is stored in
`data/annotations/reader-friction-screen-v3.json`.
