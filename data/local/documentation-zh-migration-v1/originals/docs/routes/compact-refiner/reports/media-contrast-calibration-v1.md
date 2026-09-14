# Real-Media Contrast Staging and Target Calibration

Date: 2026-09-14. Status: bounded discovery preparation; one concrete target
judgment is pending from the maintainer. No feature, edit, or training outcome is
validated by this report.

Subsequent same-day response: the maintainer describes the nominated article as
weak in AI smell, translationese-like, and difficult to read. The nomination is
therefore not a confirmed strong positive. That perception is not a provenance
label. The newer [contrast-family count](ershi-cohort-statistics-v1.md) follows
the maintainer's explicit feature request; the pending-judgment narrative below
is retained as the earlier checkpoint.

## Purpose and retained work

The [calibrated objective](../../../target-feature-discovery.md) retains the
existing acquisition and temporal grouping while rejecting old weak samples as
confirmed strong positives. The front-half problem is to explain a subjective
reader impression with repeatable features. It is not solved by synthetic
generation, publication-date labels, model agreement, or ordinary editing wins.

Existing corpus bodies, all human comments, frozen features, negative results,
and the compact-refiner engineering work remain intact. No old annotation was
rewritten to fit the new interpretation. The previously proposed synthetic
full-article tasks remain saved but unexecuted.

## New source staging

The [bounded staging run](media-contrast-staging-v1.md) reused InfoQ's public
sitemaps and the existing extraction machinery. It fixed twelve URLs from each
of two sitemap frames after identity/robots exclusions and seeded ordering.
The XML did not contain per-URL publication dates; an initial zero-selection
manifest based on unavailable hints was preserved before an explicit index-frame
amendment. Article publication dates came from embedded page state.

| Stage | Count |
|---|---:|
| Public article requests | 24 |
| Actual pre-2023 publication dates | 12 |
| Actual on/after-2025-07-01 dates | 12 |
| Complete HTTP responses | 24 |
| Nonempty extracted textual bodies | 20 |
| Deterministic translation exclusions in this staging run | 4 |
| Remaining for further textual inspection | 16: 7 pre, 9 post |
| Corpus admissions / human smell labels / training exports | 0 / 0 / 0 |

Four successful HTTP captures had empty extracted bodies. They are extraction
failures, not complete articles or replacement samples. No failed, wrong-period,
or excluded item was backfilled to improve the observed result.

The identity exclusion layer used prior document IDs, URLs, and available hashes.
A later mechanical leakage audit reused the existing fixed exact/normalized/
simhash-prefiltered shingle comparison at threshold 0.9. It found no known or
within-staging overlap among nonempty captured texts. Benchmark body content
was used only inside that mechanical guard; labels, model scores, and outcomes
were not exported, presented to reviewers, or used for tuning. The guard is not
a guarantee against every semantic overlap.

All source responses, paragraphs, image/link references, extraction limitations,
and timestamps are preserved privately. No media resource was downloaded.
Current views are collection-time observations, not age-matched visibility
measures. Length and successful extraction are not quality admission.

## Full-text review panel

Six articles were chosen from metadata before reading their bodies, forming
three provisional pairs: enterprise/cloud discussion, first-party technical
practice, and technology-news reporting. This is not a matched representative
corpus. The cloud pair has substantial length and interview/opinion differences;
other pairs also retain topical and visual-context differences.

The review presentation joins original DOM text blocks with paragraph spacing.
Its exact non-whitespace content matches each immutable captured body. No
sentence was rewritten, generated, omitted, or reduced to a selected excerpt.
Date/source metadata was withheld from the contrast reviewers; genuine textual
time cues were retained, so blinding is incomplete.

Two agents independently read all six whole textual articles and nominated
possible contrasts without seeing one another's results. Their task allowed
weak/no contrast and uncertainty and required actual evidence and counterexamples.

| Pair | Reviewer A | Reviewer B | Interpretation |
|---|---|---|---|
| Enterprise/cloud discussion | Weak/no contrast | Uncertain | Sales language and interview/opinion differences prevent a clean target claim |
| First-party technical practice | Weak/no contrast | Weak/no contrast | Both maintain concrete mechanisms; polished framing alone is insufficient |
| Technology-news reporting | Candidate contrast, B | Candidate contrast, B | A specific whole-article candidate for human calibration, not confirmed intensity |

This agreement does not turn an agent impression into a human observation.
The reviewers share related model capabilities; their errors can be correlated.
No classifier, NLP score, rewrite, or preference model was trained.

## Provenance review and correction

A separate agent inspected source metadata and complete article context. Its
initial review incorrectly called foreign-source citations deterministic evidence
of whole-article compilation. The executing agent checked that decision against
the existing project policy, which permits independently written Chinese
reporting and synthesis of foreign source material.

The [v1.1 addendum](media-contrast-qualification-v1.1.md) preserves the original
review while withdrawing that overclaim. Foreign references are observed;
translation versus independent Chinese synthesis is unresolved for the news
pair. Those articles remain on provenance hold for formal admission. The
maintainer is not being asked to resolve source provenance.

This correction demonstrates why model-assisted classification must retain
supporting evidence and uncertainty. Neither a Chinese byline nor foreign
citations alone proves the required originality status.

## Pending target judgment

The one nominated whole article is InfoQ's
[Cowork announcement and reaction article](https://www.infoq.cn/article/UN16P0pugHNutuMbgrNl),
published on 2026-01-13. It was captured directly from the public media page,
not generated from a project prompt or pre-edited by an assistant.

Both contrast reviewers independently highlighted recurrent abstract role
reframing and a reaction-section synthesis not adequately supported by the
reactions it lists. Their evidence includes counterexamples: necessary safety
distinctions and concrete product details are not automatically smells.

The required question is deliberately narrow: does this complete article reach
the maintainer's intended level of obvious target smell? The reader need not
derive feature rules or decide authorship/provenance. The original page is the
primary reading reference, retaining available figures and context; isolated
quotations are not a substitute.

Until that judgment arrives, the article is a nomination, not a strong-positive
label, admitted corpus document, training example, or validated feature. A
positive response would authorize development characterization of that observed
case, not population or temporal conclusions. A negative or uncertain response
must be retained and must not be overridden by agent agreement.

## Artifacts and integrity

- `data/local/media-contrast-staging-v1/`: frozen frames, all captures/attempts,
  eligibility audit, full text and paragraph/media maps.
- `data/local/media-contrast-overlap-v1/`: mechanical overlap audit and source
  file hashes, with no benchmark labels or bodies exported.
- `data/local/media-contrast-review-v1/`: full-text anonymous packets, private
  identity mapping, independent contrast reviews, and versioned qualification.
- `data/local/compact_refiner/calibration-20260914-strong-signal.json`: exact
  maintainer clarifications, preserving original wording.

The amended URL-selection manifest SHA-256 is
`e8c479f160f0591b28063fcc77f64f5c63ed4b276c4221dd474cabf8860f5679`.
The article-attempt ledger SHA-256 is
`348e8cc8ec34d1a6fe5517ee7f7858f6bfa78bb7424bc063b3bc9616858ac6f2`.
Each source and presentation has its own recorded hash. The current work made
ordinary bounded website requests and used agent review; it made no new paid
OpenRouter call, no edit generation, and no GPU/training job.
