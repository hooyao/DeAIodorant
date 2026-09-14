# Bounded InfoQ temporal candidate staging v1

Date: 2026-09-14. Acquisition protocol: `media-contrast-staging-v1`.
Selection amendment: `index-frame-selection-amendment-v1`.
Eligibility audit: `media-contrast-staging-eligibility-audit-v1`.

This run preserves and exercises the useful acquisition and temporal framework
under the [calibrated target-discovery objective](../../../target-feature-discovery.md).
It is unreviewed acquisition staging, not a clean corpus, a strong-smell sample,
a feature test, an editing experiment, or training data. No article body was
printed or presented to a model during this run. No model, GPU, or API inference
was used. Old weak-sample studies retain their historical limits.

## Result and retention

| Outcome | Intended post frame | Intended historical frame | Total |
| --- | ---: | ---: | ---: |
| Frozen article URLs / public article GETs | 12 / 12 | 12 / 12 | 24 / 24 |
| Complete HTTP 200 responses | 12 | 12 | 24 |
| Page-state dates in intended primary cohort | 12 | 12 | 24 |
| Nonempty collector-normalized bodies | 12 | 8 | 20 |
| Empty collector-body extraction failures | 0 | 4 | 4 |
| Deterministic translation exclusions | 3 | 1 | 4 |
| Remaining for further review | 9 | 7 | 16 |
| Formally admitted / confirmed smell labels | 0 / 0 | 0 / 0 | 0 / 0 |

Complete HTTP capture must not be confused with complete article extraction.
The reused collector returns article metadata even when `.ProseMirror` contains
no text. Four historical captures have empty bodies; their identical empty
SHA-256 values are an extraction failure, not an informative duplicate-text
cluster. The immutable attempt log calls all 24 `captured_unreviewed` because
the responses and metadata were captured. The separate `eligibility-audit.json`
records these four as unusable text captures without rewriting the attempt log.
No alternative endpoint, authenticated route, or replacement URL was used.

The empty-body IDs are `769ecc5e088514e4261ae7e0`,
`8a835ce2a2584c3c9040fcc5`, `c979e224eb220101fb785893`, and
`94484784827b950a4ea5beea`. The deterministic translation exclusions are
`9d2686869fb90420de5a6d40`, `9656e09a0c8ef6938c517cef`,
`83e3fb47524511fba7945931`, and `0c1bc051de0fc98fbcd0524d`.
These two sets are disjoint. No wrong-period outcome, selected-ID overlap,
declared canonical-URL conflict, or known exact-content-hash overlap occurred.
There are no within-batch exact duplicates among the nonempty bodies.

The actual historical publication dates range from 2020-07-06 to 2022-10-28;
the post dates range from 2025-10-30 to 2026-06-01. These narrow sitemap frames
do not cover the July 2025 boundary adequately for change-point inference.
The dates are sampling provenance, not individual authorship or smell labels.

## Frozen frame and explicit pre-body amendment

The only discovery endpoints were public `robots.txt` and the published
InfoQ sitemaps `index_1.xml` and `index_3.xml`. Both XML files contain 9,800
entries across page types. The article-only counts were:

| Frame | Unique article URLs | Known identity exclusions | Eligible index URLs | Selected |
| --- | ---: | ---: | ---: | ---: |
| `index_1.xml`, intended post | 4,023 | 56 | 3,967 | 12 |
| `index_3.xml`, intended historical | 7,868 | 66 | 7,802 | 12 |

Every XML entry provides only `loc`, `changefreq`, and `priority`. There is no
per-URL `lastmod` or publication date. HTTP `Last-Modified` describes the sitemap
response, not the articles. The initial conservative date-hint selector therefore
selected zero; its manifest and per-entry decisions remain preserved.

Before any article body was requested, the parent agent explicitly approved
using the originally specified indexes as intended-period frames. The amendment
reused the captured XML and robots bytes and did not change the quota, source,
or seed. After known-identity and robots exclusion, URLs were sorted with the
existing `stable_order` function using the seed
`media-contrast-staging-v1-20260914-<cohort>` and the first 12 were fixed.
Actual cohort membership was subsequently determined from embedded article
`publish_time`. Wrong-period, failed, and excluded captures would not be replaced.
This amendment was based solely on missing frame metadata, before article outcomes.

The frozen amended selection manifest SHA-256 is
`e8c479f160f0591b28063fcc77f64f5c63ed4b276c4221dd474cabf8860f5679`.
The preserved empty-selection manifest SHA-256 is
`8b594583e336cc675d9f237c0ae61a33af8fc1a86a02cfd30934f6816bdb1c5d`.

## Exposure and source restrictions

Known identity exclusions were collected mechanically from pilot monthly
metadata, reader annotation document IDs, and the separately prepared
`data/local/media-identity-exclusions-v1.json`. That export contains only
document/URL/content-hash identities from prior datasets. This staging script
did not open its underlying benchmark files, bodies, gold labels, decisions,
scores, or outcomes. The combined exclusions include 395 document IDs,
370 canonical URLs, and 210 known content hashes. Source file hashes and the
export hash are recorded in both exclusion and selection provenance.

These checks exclude known exact identities; near duplicates and missing
historical handoff coverage remain unresolved. The 16 remaining documents are
candidates for inspection, not an independent validation reserve. No source
text was exposed to the agent through console output before that audit.

The session made 27 ordinary unauthenticated GETs: one robots request, two
sitemap requests, and exactly 24 article requests. All returned HTTP 200, with
no redirects, retry, authentication, cookies, alternative content endpoints,
linked-resource fetches, or referenced-media downloads. The minimum measured
interval from a response's completion to the next request was 2.000066 seconds.
The client stops further requests on HTTP 429 or `Retry-After`, and does not
backfill. Ambient environment credentials are disabled for this public client.

Article requests ran from 06:34:05 through 06:35:19 UTC. Direct checks at roughly
10, 24, 40, and 60 seconds confirmed process liveness, increasing CPU time,
growing request/attempt logs, and progress; the completion check confirmed
exit code 0. `progress.json` was updated before requests and after every attempt.
No monitor notification was relied on as the source of truth.

## What is preserved and what remains unknown

Private captures include the exact response bytes exposed by `requests`
(HTTP transfer decompression applies), safe response headers, request and
completion timestamps, hashes, full available collector-normalized text,
parsed article HTML, semantic paragraph mappings, and figure/caption/link/media
references. Raw response HTML is the authoritative source representation;
`article.dom.html` is a parser serialization. Reconstructed paragraph text
matches the normalized body exactly for all 24 captures, including the four
empty-body failures. No source whitespace or content was silently rewritten.

The collector's normalized lines are not original paragraph counts. The reused
presentation mapper handles inline text boundaries and preserves source-line
mapping. It does not establish browser rendering or recover material inside
images. There are 30 post and 33 historical image/media references and 57 post
and 44 historical hyperlinks; referenced resources were not fetched.

The four deterministic translation flags are exclusions. Absence of such a
flag on the other documents is not originality clearance. Substantive quality,
translation/compilation provenance, source-text completeness, and suitable
visibility evidence require further review. Pilot `quality_pass` is retained
only as `legacy_quality_pass_diagnostic_only`, never as an admission gate.
Among nonempty captures, post text length ranges from 243 to 21,891 characters;
length alone says nothing sufficient about quality or target relevance.

Current page-view snapshots range from 2,507 to 18,433 for post pages and
1,360 to 8,076 for historical pages. They are not fixed-age or source-quarter
comparable audience measures. No high-visibility pass, source/topic/format match,
strong/weak perceptual contrast, prevalence estimate, or temporal effect is claimed.
Public access does not establish redistribution or training rights.

## Commands, artifacts, and verification

```powershell
python experiments/stage_media_contrast_candidates.py freeze --output-dir data/local/media-contrast-staging-v1
python experiments/stage_media_contrast_candidates.py select-index-frame --output-dir data/local/media-contrast-staging-v1
python experiments/stage_media_contrast_candidates.py fetch --output-dir data/local/media-contrast-staging-v1
```

The first command refuses an existing directory. The amendment refuses an
already amended or started selection. Fetch refuses an existing attempt run;
there are no automatic retries or overwrites. The initial empty selection and
the explicit amendment are separate artifacts. This is a bounded one-run script,
not a new general collection service.

All generated source data live under the Git-ignored directory
`data/local/media-contrast-staging-v1/`, approximately 20.2 MiB. Principal files:

- `selection-manifest.json` and `selection-manifest-index-v1.json`: initial and
  amended frozen selection identities, runtimes, source hashes, and policy;
- `frame-*.jsonl`: all article-frame decisions, including unselected exclusions;
- `identity-exclusions.json`: identity-only exclusion snapshot and input hashes;
- `requests.jsonl`, `article-attempts.jsonl`, and `progress.json`: all network
  attempts and progress, with no printed article text;
- `raw/` and `documents/<doc_id>/`: source responses, normalized bodies, parsed
  HTML, semantic blocks, structures, and metadata;
- `summary.json`, `verification.json`, and `eligibility-audit.json`: capture
  outcomes, independent integrity checks, and usable-text/exclusion correction.

The script, collector, and presentation-mapper hashes and package versions are
recorded in the manifest. Compilation passed. Independent checks verified
all 27 response hashes, 24 normalized-body hashes, all block concatenations,
the exact frozen URL order, request uniqueness and spacing, unchanged identity
source files, and unchanged acquisition/presentation source code. UTF-8 decoding
introduced no replacement characters. Existing repository corpus/benchmark
artifacts and configs were not modified. Inference cost is zero and no dependency
or model artifact was added.
