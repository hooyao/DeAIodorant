# Targeted Real-Media Discovery v1

Date: 2026-09-14. Status: one exploratory source nomination, not a confirmed
strong human example, rewrite experiment, or training record.

## Why selection changed

The [Cowork task was withdrawn](cowork-preview-withdrawal.md) because general
repairability had displaced the target-coverage question. The subsequent
[twelve-document rescreen](target-coverage-rescreen-v1.md) nominated no sustained
case. Rather than preparing more edits from that frame, a bounded search looked
for an informative article with the nominated style manifestations.

One Google UI query was used:
`site:infoq.cn/article "不是" "而是" "2025" "本质"`.
The visible domestic-company analysis result was selected and its actual URL
resolved before body inspection. Known identity checks passed. A public capture
used one robots GET and one article GET, with the existing conservative client,
no retries, and no media downloads. Exact/normalized/simhash-prefiltered shingle
checks at the existing 0.9 threshold found no match against available protected
datasets or either earlier staging frame. Protected text and labels were not
displayed or supplied to reviewers.

This is keyword-enriched development discovery. It cannot estimate prevalence,
replicate temporal rates, or supply independent validation.

## Candidate and evidence

Source: [Baidu's old-supply/new-supply analysis](https://www.infoq.cn/article/rDTKqBrlGD5R93NFDOI8),
published 2026-05-15; document ID `92ade4253c08a43329164bf5`.
Body SHA-256:
`2977deaed4317dd195716a9bd051e69a81d45fc2ffba94db7086aa0418a126e2`.
Both root and a separately prompted reviewer read the complete 5,872-character
body; the independent reviewer also read all 64 DOM blocks. No rewrite was
generated. The reviewer did not read the root's observations or prior reviews.

The independent disposition is `sustained_target_candidate`, with moderate
confidence, for a combination of recurring problems across the article:

- Local technical announcements are repeatedly recast as new demand, a new
  supply paradigm, a critical point, a new departure, and a generational
  architectural advantage. Recurrence extends beyond one quoted slogan.
- A token-billed/open versus credit-billed/closed platform dichotomy leads into
  a vendor third-way claim without establishing exhaustive alternatives or
  comparable cost. The closing Apple analogy introduces a price-versus-ecosystem
  causal replacement without showing that exclusive comparison.
- Asserted progression sometimes changes the problem being answered: bursty
  compute utilization moves to procurement/cooling flexibility; store/factory
  coordination moves to banking adoption and automotive training; marketplace
  growth moves to infrastructure first-mover advantage.

Local wording defects are also present, including
`主语的变化，背后意味着背后的技术工作` and
`但确实能帮助我们百度 Create 这次发布会的产业意义`.
Those possible predicate gaps are not the sole basis for nomination. The body
contains only three literal `而是` instances; count alone did not determine the
disposition.

Counterevidence remains substantial: the cache explanation supplies a mechanism,
several contrasts are attributed quotations or necessary technical distinctions,
and the conclusion is conditional. Company-event reporting and promotional
conventions are plausible competing explanations. Seven referenced images are
uninspected. The article's production route and degree of LLM involvement are
unknown; a domestic subject and Chinese byline do not establish them.

## Current evidence boundary

The nomination is a reason to calibrate raw target representativeness before
editing. It is not evidence that the maintainer finds the article strongly
aversive. No human preference, severity, authorship, or preservation label is
inferred. If raw target coverage is rejected, preserve that rejection and revise
sampling; do not proceed with generic repairs as a replacement objective.

## Artifacts

Private root: `data/local/targeted-media-discovery-v1/baidu-supply/`.
It retains selection, requests, original HTML, body/DOM mappings, source
metadata, mechanical overlap results, root observations, and the independent
`target-review.json` with 43 validated evidence spans and counterexamples.
The capture command and implementation are preserved in
`data/local/targeted-media-discovery-v1/capture_candidate.py`.

Two inherited extractor metadata strings are stale: `acquisition_method` names
the old sitemap process, and `exposure_status` says overlap checks are pending.
The selection record/capture script establish actual search discovery, and
the later result plus script establish completed available-index checks.
Those raw fields are retained rather than silently rewritten. They do not
provide an originality certification or prove semantic independence.
