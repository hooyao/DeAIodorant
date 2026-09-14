# Media Provenance Extension v1

Date: 2026-09-14. Protocol: `media-provenance-extension-1.0`.
Status: completed bounded acquisition and descriptive available-frame extension.
This run provides no human smell labels, original-Chinese certification,
meaning judgments, formal corpus admission, or training eligibility.

## Result

The frozen selection produced 24 unique public article GETs, all complete HTTP
200 responses. Twenty-one responses yielded nonempty Chinese bodies; three
historical responses yielded empty text. All embedded publication dates agreed
with the intended cohort, with no transition or timezone-boundary cases. No
replacement URLs, retries, redirects, model calls, GPU use, or media downloads
occurred.

The 21 nonempty bodies passed the fixed mechanical duplicate guard against
396 protected pilot/smoke/benchmark records and 20 nonempty bodies from the
previous staging run. No known-content or within-batch match was found. This
heuristic result does not prove semantic independence or complete historical
coverage.

| Actual cohort | Provenance evidence stratum | Documents | Zero-count documents | CJK characters | Literal occurrences | Occurrences per 10,000 CJK |
|---|---|---:|---:|---:|---:|---:|
| Pre | All available | 9 | 7 | 30,913 | 2 | 0.647 |
| Pre | Unresolved | 9 | 7 | 30,913 | 2 | 0.647 |
| Post | All available | 12 | 6 | 46,439 | 28 | 6.029 |
| Post | Translated | 3 | 3 | 3,165 | 0 | 0.000 |
| Post | Unresolved | 9 | 3 | 43,274 | 28 | 6.470 |

All rows are InfoQ. The existing exact literal is `而是`; CJK characters are
counted using the unchanged reading-burden expression. Translations and
zero-count documents remain in the diagnostic population. No document received
the mixed/adapted stratum under the frozen evidence rules, and no document was
certified original Chinese. Unresolved provenance is not originality evidence.
The strata describe detected declarations or metadata, not a verified complete
production history.

The pre bodies span 2020-11-18 through 2022-10-12. The post bodies span
2025-11-07 through 2026-09-10. Each nonempty body has the four extracted
visibility fields (views, comments, likes, collects); nonmissing snapshot fields
do not establish visibility comparability or editorial relevance.

## Fixed concentration diagnostics

The existing concentration function counts connector starts within a fixed CJK
coordinate span. These are maximal observed local counts, not reading-severity
scores or independently defined linguistic passages.

| Actual cohort | Window width | Distribution of maximum local count across documents |
|---|---:|---|
| Pre | 500 CJK | 0: 7 documents; 1: 2 documents |
| Pre | 1,000 CJK | 0: 7 documents; 1: 2 documents |
| Post | 500 CJK | 0: 6 documents; 1: 4 documents; 2: 1 document; 3: 1 document |
| Post | 1,000 CJK | 0: 6 documents; 1: 4 documents; 2: 1 document; 4: 1 document |

The three translated post documents have a maximum of zero for both widths.
All per-document counts, full-precision rates, window coordinates, and
provenance evidence are private artifacts. No additional feature family,
window, threshold, severity score, or significance test was selected after
observing the batch.

## Acquisition, exclusions, and failure accounting

The cached public index_3 and index_1 sitemaps were verified against their
original successful request hashes. They had no article dates; sitemap position
or modification information was never treated as publication evidence. The new
seed was `media-provenance-extension-v1-20260914`.

| Intended frame | Article URLs | Excluded known identities or prior requests | Eligible URLs | Frozen selection | Nonempty outcomes |
|---|---:|---:|---:|---:|---:|
| Pre, index_3 | 7,868 | 78 | 7,790 | 12 | 9 |
| Post, index_1 | 4,023 | 68 | 3,955 | 12 | 12 |

The frozen exclusion map contains 419 document IDs and 394 URLs. It includes
all earlier staging selections and requests, even failed or empty captures.
There were zero identity overlaps in the selected 24 URLs. Selection ranking
was reproduced in a metadata-only inspection before the first article GET.

An implementation preflight initially failed because 160 records in the old
identity-only export lacked `content_hash`. This happened before network access
or selection. The implementation now treats that field as optional while
retaining ID/URL exclusions, and the preflight history is archived. During the
later duplicate guard, all 396 records from the six protected datasets had
available text. Their bodies and labels were not displayed or used in prompts;
only allowlisted identity/content fields entered `ExclusionIndex`.

The historical extractor marked the three empty captures as
`known_exact_content_overlap` because their empty-string hash also occurs in
the old staging exclusions. Those labels do not demonstrate duplicate articles.
The original extraction and summary artifacts remain unchanged; the private
`exclusion-interpretation-addendum-v1.json` identifies all affected records and
explains the shared empty hash. All three remain empty-text outcomes, and the
21-body diagnostic totals are unchanged. The nonempty-body guard found zero
known or internal duplicates.

The inherited extractor's old translation exclusions are retained under
`legacy_extractor_exclusions`; they are removed from the new research eligibility
decision. No article was rejected for translation, low readability, short
length, or a zero literal count.

Two new robots GETs were made: before selection and at fetch start. The minimum
observed interval from a completed fetch response to the next request was
2.000132 seconds. There were no rate-limit, Retry-After, authentication,
access-challenge, response-size, or network stop events.

Ground-truth observations covered the initial running-session snapshot at two
completed selections, direct live-process/log checks at 10, 16, and 23, and the
successful exit plus final process-dead/complete check at 24. The duplicate
guard was observed after its first four indexed files and again at successful
completion; it finished in under one minute. These checks used actual process
and artifact state rather than a background notification alone.

## Reproduction and verification

The [prospective protocol](../media-provenance-extension.md) and
[implementation](../../../../experiments/stage_media_provenance_extension.py)
were frozen before article requests. Commands executed were:

```powershell
python -B experiments/stage_media_provenance_extension.py freeze
python -B experiments/stage_media_provenance_extension.py inspect
python -B -u experiments/stage_media_provenance_extension.py fetch
python -B -u experiments/stage_media_provenance_extension.py analyze
python -B -m pytest -q tests/test_translation_benchmark_v2.py -k exclusion_index -p no:cacheprovider
```

The comparator test passed. An independent artifact check verified all 72
frozen input hashes, 165 frozen output hashes, raw-response and body identities,
24 unique GETs, selected/requested URL equality, source spacing, and recomputed
literal/CJK counts for every diagnostic body. The repository-wide required
checks are coordinated by the root task separately.

Private output root: `data/local/media-provenance-extension-v1/`. It contains
the selection and frame files, identity map, request/outcome journals, original
HTML, bodies, DOM/paragraph/media mappings, duplicate guard, provenance metadata,
diagnostics, summaries, observer checks, addendum, and verification record.
The result manifest hashes the original outputs; later verification and the
interpretation addendum are additive artifacts and do not replace that manifest.

| Artifact | SHA-256 |
|---|---|
| Implementation | `5eb15e23d7bf69409b0e91171cef10f2dd49147bde9ba413e8d44a11468a788d` |
| Protocol | `59caa30c72c9fc62ffb7f389f718f67717b80eb0047905c0e02ac7dc226d49ed` |
| Cached pre sitemap | `1d5e50773f1c83e8704a1c24a16718fdf11a650d012e95aab266f97fad711bfd` |
| Cached post sitemap | `d91858055241a25d519d6c15c970e9db656368e82dd8c7252331c1dbd63c78c7` |
| Selection manifest | `46ebccdf0251c6b548fd1ca70093e093bf6566f55e3675d1f9717db23a0e0f3b` |
| Result manifest | `54477b371af5f50ca2fc9f44bab34dce941ea9708c966419cbd54f4b9ea170b7` |
| Empty-hash interpretation addendum | `13a4c2602610c50a922ff06383c7889d0a46777f581486b682bd657a0c9b5407` |

## Interpretation limits

This available-frame extension again has a higher pooled post-period literal
rate, while retaining translations and zero-count cases. It is small,
source-limited, and unmatched on topic, genre, length, visibility, and detailed
provenance. The historical empty-response loss is asymmetric. Current visibility
is age-confounded, provenance evidence can be missed, and referenced media were
not visually verified. These results are exploratory replication of a literal
measurement, not a population prevalence estimate, causal temporal effect,
authorship judgment, proof of reader irritation, or validated editing target.
