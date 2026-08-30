# Current-Model Post Corpus Expansion v3

## Status

The local handoff was generated on 2026-08-30 and passes the frozen
`post-reader-corpus-handoff-1.1` validator with zero errors and zero warnings.
It is discovery material, not a representative, matched, validation, or final-
test corpus.

~~~text
F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v3
~~~

## Acquisition and deterministic exclusion

Public acquisition produced 720 post-period records: 240 each from QbitAI,
Leiphone, and Huawei Cloud Community. Access controls, authentication, paywalls,
CAPTCHAs, and source limits were not bypassed.

Deterministic translation evidence and cross-corpus exact and near-duplicate
checks reduced the pool to 561 records: Huawei 232, Leiphone 194, and QbitAI
135. The exclusions were 92 explicit translations, 59 duplicate document IDs,
and eight near duplicates. There is no document-ID, URL, hash, or near-duplicate
overlap with the first two post handoffs, the pre/transition handoff, the
tracked pilot, or existing reader artifacts.

## Current-model admission

Model selection used a live OpenRouter weekly-usage snapshot, a same-day live
model catalog, and the fixed 12-document interface panel documented in
[Current OpenRouter Corpus-Model Interface Audit](openrouter-corpus-model-interface-audit.md).

DeepSeek V4 Flash 0731 and GLM 5.3 Flash screened all 561 deterministic
candidates. Their high-confidence provenance intersection retained 372. Their
two-prompt, within-model and cross-model high-confidence research-value
intersection retained 130. Qwen3.8 Max then reviewed only those provisional
passes: all 130 passed its provenance safeguard, and 103 passed both value
prompts. The frozen Huawei source-quarter visibility threshold excluded 10,
leaving 93 high-confidence stratified documents.

Every request error, malformed result, non-high confidence, uncertainty, or
model disagreement failed closed. These labels remain measurements rather than
human gold.

## Run anomaly

A failed DeepSeek provenance retry left an orphaned process while a lower-
concurrency retry began. Two processes appended to the same cache before the
condition was detected. The original cache is retained and contains 95 duplicate
cache-key groups and 95 extra lines. Both stale processes were stopped. The
final provenance result was regenerated from the cache-key index and contains
exactly 561 rows and 561 unique document IDs. Every value cache has zero
duplicate keys. The anomaly is recorded in the local manifest and admission-
flow artifact rather than hidden.

## Final composition

| Dimension | Counts |
|---|---|
| Sources | Leiphone 39; Huawei 32; QbitAI 22 |
| Formats | Industry reporting 40; technical practice 34; research summary 19 |
| Topics | AI/models/agents 57; business/industry 17; data infrastructure 13; software engineering 6 |
| Roles at handoff generation | Discovery reserve 93; development 0; validation 0; final test 0 |

The monthly distribution is strongly recent: 53 of 93 documents were published
in 2026-08. Source and format are also confounded: all 32 Huawei documents are
technical practice, while Leiphone and QbitAI contribute most reporting and
research summaries. QbitAI and Leiphone visibility is official editorial
distribution evidence, not article-level readership. Huawei visibility is a
collection-time source-quarter view percentile.

After handoff validation, all 93 documents were opened by the frozen
deterministic motif inventory. They are therefore feature-discovery exposed and
must not be repurposed as validation or final-test documents.

## Artifact identity

| Artifact | SHA-256 |
|---|---|
| Manifest | `5462a30c6c9d8e598fd1f8f6af567bbb4d4efbcc7cc30e3bfd36d4965225ebac` |
| Documents index | `dd2d3b3f99d17c2fe7179e8fcdeb7f31e5036a7d7b117ed819e12825eacd4a4d` |
| Text-set identity | `58bf3d51fddedb053c8f6fa8d99ea660e7616d95ff013d5d39bba8285039b095` |
| Validation report | `d180dda220274c0989588fdc9072e66b74216bb7b650f4b750ab817e2aa771c2` |
| External overlap report | `d78e0d9d68b803363cb88fa654fe99e99eaf378fc09c605f145c266d93e8b5df` |
| Admission flow | `13a7d9df4701f8d96e57dd0ee51d8f6390225aa29107599ac6b1fbc58d37572c` |

All source bodies, model caches, live catalog snapshots, comparison results,
and generated handoffs remain in ignored local storage. No API key, credential,
corpus body, or model output is committed.
