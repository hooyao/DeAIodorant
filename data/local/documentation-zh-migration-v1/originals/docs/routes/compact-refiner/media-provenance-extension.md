# Prospective Media Provenance Extension

Protocol: `media-provenance-extension-1.0`. Date: 2026-09-14.
Objective authority: `deaiodorant-target-discovery-1.3`.

This is a fresh, bounded acquisition and descriptive diagnostic extension, not
a representative corpus, reader study, meaning assessment, or training set.
Freeze this protocol, implementation, inputs, identities, and exact selection
before any new article GET. Keep all earlier acquisition and repair artifacts
unchanged.

## Sampling and protected identities

Use only the previously captured public InfoQ sitemap index_1 (intended post)
and index_3 (intended pre), verified against the earlier request hashes. These
frames contain no article dates. Do not infer publication from sitemap position,
last modification, or intended cohort. Refresh public robots.txt before
selection and again at fetch start; a stricter policy can reduce attempts but
cannot trigger replacement selection.

The new seed is `media-provenance-extension-v1-20260914`. For each intended frame,
rank canonical HTTPS `www.infoq.cn/article/` URLs by
SHA-256(seed + '-' + cohort + NUL + URL), after identity, duplicate-frame, and
robots exclusions. Select exactly 12 per frame, with no shared URLs and no
backfill. The cap is 24 article GETs, with no retries. Metadata-only inspection
must confirm the frozen quota and exclusions before fetch.

Use the earlier identity-only exclusion map and benchmark identity export;
verify their listed source hashes without displaying labels or bodies. Exclude
every prior staging selection and attempted article, including failed captures.
Freeze protected dataset and prior staging body hashes for a later mechanical
`ExclusionIndex` check. Known annotation and benchmark identities remain
excluded; no exposed benchmark result affects selection or diagnostics.

## Public access and capture

Reuse the existing `BoundedClient`, `robot_parser`, `robot_delay`, and
`extract_candidate` implementations without modifying them. Their identified
research user agent remains unchanged. Requests are unauthenticated ordinary
public GETs with environmental credentials disabled, fresh sessions, no
redirect following, hidden APIs, cookies, or referenced-media downloads. Respect
robots and at least two seconds after each completed request. Stop on 429,
Retry-After, authentication/access-denial responses, an unambiguous non-article
access-challenge title, response-size limits, or network exceptions. Do not
bypass restrictions. Preserve every response, error class, partial capture,
unattempted selection, and stop reason. No retry or automatic resume.

Archive the full HTML, normalized Chinese body, paragraph mapping, embedded
publication/update timestamps, collection timestamps, canonical links, and
media references privately. The public report contains aggregate metadata only.
Publication cohorts are before 2023-01-01 and on/after 2025-07-01; the transition
interval is separate. A UTC/Asia-Shanghai boundary disagreement remains
ambiguous. Missing dates, empty bodies, extraction failures, canonical mismatch,
and wrong-period cases remain outcomes. Wrong-period captures may contribute to
their actual unambiguous cohort, with the mismatch explicitly reported.

## Provenance and duplicate guard

Translations and adaptations are retained. The historical extractor's
translation exclusion is archived as a legacy decision and is not a new
research exclusion. Apply the same evidence rules to both periods:

- `mixed_adapted`: the existing foreign-media-transcript evidence or a matched
  existing direct-translation expression containing `编译`.
- `translated`: an explicit translator field or an existing direct-expression
  match containing `译自`, `翻译`, or `译者`, unless the first rule applies.
- `unresolved`: all other cases, including weaker legacy foreign-origin
  evidence; preserve that evidence separately.

These are declaration/evidence strata, not verified production histories. No
absence of evidence certifies original Chinese; this automated extension makes
no original-Chinese certification. Foreign names, links, difficulty, and cue
counts do not assign provenance. Original-only research remains a future
control requiring adequate evidence, never the global admission rule.

Before computing diagnostics, compare bodies mechanically against the fixed
prior pilot/smoke/benchmark dataset paths and prior staging bodies, then against
earlier records in this fixed batch. Use the existing `ExclusionIndex` at 0.9,
including its existing length, simhash, and shingle rules. Only identity and
content fields enter the index; no protected labels, bodies, or results enter
prompts or reports. Preserve matches and missingness. This heuristic does not
prove semantic independence. Duplicate captures remain archived but do not
contribute to the unique-document diagnostic groups.

## Frozen diagnostics and interpretation

Use the exact literal `而是` and CJK regular expressions from
`reading_burden.py`, without prefix-family or semantic classification. Count
the entire captured body, including quotations and retained extraction line
breaks. Use only the existing `contrast_context_audit.concentration` function
at widths 500 and 1000 CJK characters. Keep zero-count articles. Do not tune
windows, thresholds, subsets, or metrics after observing this batch.

Report per-document literal counts, CJK counts, rates per 1,000 and 10,000 CJK,
and both fixed concentration results privately. Public aggregates by actual
cohort, source, and provenance include documents, zero-count documents, total
CJK, total occurrences, pooled rates, and concentration-count distributions.
Also report the intended-to-actual cohort table, failures, exclusions, missing
visibility fields, and publication ranges. No length or readability gate applies.

These small unmatched available-frame results are exploratory replication.
Source/topic/genre/length/visibility are not jointly matched, current visibility
is age-confounded, provenance rules can miss evidence, and text capture omits
uninspected media. Rates are neither temporal causal effects nor population
estimates, and indicate neither authorship nor reader-disliked severity.
No LLM API, GPU, model training, human smell label, or meaning label is involved.

## Execution and immutable outputs

Run `python experiments/stage_media_provenance_extension.py` with phases
`freeze`, `inspect`, `fetch`, and `analyze`, in that order. The output is fixed
at `data/local/media-provenance-extension-v1/`. Each phase records its command,
timestamps, hashes, and terminal status. Reusing a started phase is refused;
failures are retained rather than overwritten. Record actual process liveness,
progress-file updates, and completed request counts during the fetch and
duplicate guard, independently of any background completion notification.
