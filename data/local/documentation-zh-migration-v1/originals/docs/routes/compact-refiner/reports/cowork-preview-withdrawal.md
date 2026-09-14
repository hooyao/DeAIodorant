# Cowork Preview Withdrawal and Sample-Selection Correction

Date: 2026-09-14. Decision: `CR-D023`.
Status: reader task withdrawn for target mismatch; no A/B preference recorded.

## What the maintainer rejected

The maintainer had already called the Cowork article weak in AI smell. The
assistant later prepared a complete-article rewrite and requested another
reading preference, despite this known limitation. The maintainer rejects
Cowork as a representative strongly characteristic Chinese AI-style article.
It may carry English LLM defects through translation while still being a poor
example of the intended Chinese phenomenon. This distinction does not establish
the article's actual generation history or make translation a severity label.

## Why the approach drifted

Source availability, measurable grammar defects, working parse/diff tooling,
and completed preservation review made Cowork convenient. The assistant treated
these engineering advantages as sufficient reason for another reader task.
That substituted general repairability for target coverage and repeated the
earlier weak-example error. Calling the question readability feedback did not
fix its mismatch with the active feature-discovery priority.

The requirement to support translated articles is a product coverage requirement.
It did not make this one weak case the central discovery example. Equally,
direct-Chinese provenance by itself cannot make an article a strong example.

## Actions

- Withdraw the pending Cowork preview. The maintainer's feedback is a selection
  rejection, not a tie, original win, revision loss, preservation verdict, or
  measured readability outcome.
- Preserve all original/candidate texts, operations, failures, reversions,
  reviews, syntax analyses, rendering artifacts, counts, and feedback.
- Keep the completed repair run as bounded engineering/translation-readability
  evidence. Do not automatically substitute another already-edited article into
  the same reader request or issue Cowork again under a different outcome name.
- Resume source inspection for sustained target-style manifestations in real
  complete Chinese articles before producing another rewrite or asking for
  reader judgment. Counts, isolated typos, ordinary translationese, and
  unsupported factual claims do not independently qualify a strong-style case.
- Retain translated, mixed, direct-Chinese, and unresolved provenance in the
  project. Preserve source evidence to explain differences; neither infer
  authorship from style nor impose a blanket translation exclusion.

## Records and evidence boundary

`data/local/media-repair-development-v1/reader-preview-v1.1.json` retains the
two exact maintainer comments and hashes the original unanswered preview.
`ready-selection-status-v1.1.json` supersedes the reader-ready status without
modifying the original selection or its candidate hashes. The original HTML
comparison remains archival and no longer carries an active reader task.

The [bounded target-coverage rescreen](../target-coverage-rescreen.md) inspects
all twelve already acquired post-period extension bodies, keeping zero-marker
cases and translation strata. A reviewer can nominate none. No candidate from
that screen becomes a human label, reader task, or training record automatically.
