# Existing media development asset inventory

Date: 2026-09-14. Protocol and artifact schema:
`deaiodorant-media-development-inventory-1.0`.

This inventory reconnects the compact-refiner route to its actual target: whole
Chinese media articles such as the existing InfoQ exports. It preserves the
earlier corpus, reader observations, unsuccessful interventions, and provenance
warnings. It is preparation for development, not a new validation result or a
clean-corpus admission decision.

Later same-day maintainer calibration supersedes any reading of the candidate
list as confirmed severe positives: prior annotation samples were too weak for
the target question. The listed bodies and old comments remain intact and
useful for provenance and development history. See the
[calibrated objective](../../../target-feature-discovery.md).

## Scope and reproducibility

The offline script reads only `data/pilot/monthly/`, the nine persisted files in
`data/annotations/`, and two named historical evidence reports. It measures and
hashes stored bodies without displaying, copying, editing, or submitting their
text to a model. No network request, model call, training run, translation test,
final-test text, or sealed reserve is used. The stored monthly body is treated as
the whole available article export; completeness against the live source page
is not established by a byte/count check.

```powershell
python experiments/inventory_media_development.py `
  --output-dir data/local/compact_refiner/media-inventory-v1
```

Outputs are ignored local research artifacts:

- `documents.jsonl`: one record per existing monthly body, original metadata,
  file and normalized-text SHA-256 values, counts, agreement checks, preparation
  role, provenance status, and exact references to reader records;
- `reader-observations.jsonl`: all 73 persisted observations, preserved verbatim
  with original file identity and JSON pointer;
- `annotation-summaries.json`: all nine source summaries and round comments,
  preserved separately from document-specific feedback;
- `source-hashes.json`: hashes for all 54 inventoried source files;
- `summary.json`: exact counts, boundaries, reproduction command, and limitations.

The script refuses an existing output directory and requires outputs under
`data/local/`. Reproductions should use a fresh versioned directory. It checks
source bytes again before writing outputs and raises an error if they changed.
The file hash retains the on-disk identity; the content hash follows the pilot
exporter convention by normalizing line endings and removing its one appended
terminal newline. This does not rewrite a body or its historical metadata.

## What remains available

| Asset | Exact count or result |
|---|---:|
| Monthly metadata files | 13 |
| Monthly metadata records / body files / distinct IDs | 30 / 30 / 30 |
| Pre-period InfoQ | 10 |
| Post-period InfoQ | 10 |
| Pre-period Machine Heart (`jiqizhixin`) | 10 |
| Transition-period documents | 0 |
| Total stored body characters / CJK characters | 144,263 / 89,084 |
| Smallest / largest stored body, characters | 1,120 / 22,167 |
| Failed body hash, character, CJK, line, date, period, or URL-ID checks | 0 |
| Duplicate IDs / recorded URLs / exact content groups | 0 / 0 / 0 |
| Unreferenced or multiply referenced body files | 0 |
| Source files unchanged during inventory | 54 of 54 |

The period definitions remain before 2023-01-01 and on/after 2025-07-01. Length
checks establish metadata consistency, not reading quality. Near duplicates
have not been tested by this inventory. Historical page-view snapshots are not
age-matched audience measures. Machine Heart visibility was already recorded
as `editorial_source_only_unverified`.

All 30 documents have prior pilot feature-discovery exposure. Reader exposure
is recorded separately: nine post documents and two pre documents have linked
persisted reader observations. The 2026-05 document
`084c17f921cc74b858d04cdb` was reported unexposed to earlier reader tasks in the
2026-08-22 screen-v2 audit. That does not make it an independent validation
reserve: it was still part of the pilot's corpus feature discovery. Its body
remained unrendered in this inventory and it was not selected as a target.

## Post-period article map

Counts cover the entire stored export, not previously selected excerpts. Every
row is InfoQ. None is newly admitted for training or a clean corpus.

| Document ID | Published | Characters | CJK | Lines | Persisted reader records | Preparation role |
|---|---|---:|---:|---:|---:|---|
| `0431c592d5de8246cebcb8e2` | 2025-10-05 | 4,215 | 2,772 | 34 | 3 | Challenge candidate; foreign-compilation provenance requires review |
| `a127f5baf364930a89fb4005` | 2025-10-23 | 3,646 | 2,163 | 63 | 1 | Pairwise no-difference observation; not a confirmed clean control |
| `44aa81958a6c585ee8c06847` | 2026-01-16 | 2,350 | 1,296 | 40 | 3 | Leading whole-article development candidate |
| `48bda219eb0776f623161899` | 2026-01-29 | 7,428 | 5,068 | 116 | 2 | Secondary reader-friction candidate |
| `48a7a6192771112323fd6820` | 2026-02-24 | 22,167 | 8,901 | 315 | 1 | Secondary candidate; translated-document interpretation needs review |
| `b77b09a419c1631227112f0c` | 2026-03-27 | 2,090 | 1,423 | 22 | 2 | Lower-smell passage observations |
| `213dcab213f816c7c548fc09` | 2026-04-24 | 9,269 | 4,723 | 291 | 1 | Lower-smell observation with recorded original-link flag |
| `b186cdd4f9004e0413395bf3` | 2026-05-06 | 18,893 | 13,714 | 326 | 1 | Excluded known translation; historical preference retained |
| `084c17f921cc74b858d04cdb` | 2026-05-22 | 1,120 | 746 | 37 | 0 | Feature-exposed; no linked persisted reader record |
| `3c60dc0a981b686870095450` | 2026-06-26 | 5,834 | 3,877 | 97 | 7 | Leading whole-article development candidate |

The initial leading pair is `3c60dc0a981b686870095450` and
`44aa81958a6c585ee8c06847`: they match the media form, have explicit target
complaints and earlier editing feedback, and have no already-recorded
translation exclusion in the inspected evidence. Their provenance remains
unresolved until the separate whole-article review; this is not a pass based
on the pilot's `is_translation=false` value.

## Direct reader evidence to carry forward

These are preserved source quotations about passages. References use
`file#/array/zero-based-index`. References to AI inside a reader quotation are
perceptual feedback, not this report's authorship assessment.

### Leading article: `3c60dc0a981b686870095450`

Source URL: <https://www.infoq.cn/article/s6TAS5JMIW1miPSqIsk0>.
Metadata title: `当 Agent 成为新的核心云用户：阿里云重新定义“用云范式”`.
The exact metadata title and source body remain in the local inventory.

`reader-friction-v1.json#/ratings/1`, lines 36–42:

> 这个主要是典型的ai排比句式，还是ai扩句，用各种无效比喻，还有语法混乱，没有主谓宾

`reader-friction-v1.json#/ratings/9`, lines 79–81:

> 妥妥的ai生成的无任何可读性的垃圾，我看到“指向一件比“接口好不好用”更深的事” 的时候就会把这个文章关了，后边的文字果然验证了我的预测。这个文章没有一点逻辑上的通顺也语言上的可读性

The first edit did not solve it. In
`refinement-pairwise-v1.json#/pairs/0`, the outcome was `tie_or_both_bad`:

> A主谓宾省略了很多，读了吃力，B有很多AI的特征，指向...事， 喜欢用冒号，喜欢不是而是，喜欢破折号，不过通顺性上比A好些

Four later v2 excerpts from this article produced two revised preferences and
two ties. The aggregate does not erase the warning that compression can harm
argument structure or the observation that tiny stylistic edits may leave the
main problem intact. The exact comments and operation lists are retained in
the observation artifact.

### Leading article: `44aa81958a6c585ee8c06847`

Source URL: <https://www.infoq.cn/article/cYlRMETcNGxhDvBqCDII>.
Metadata title: “拒绝传统Router“瞎指挥”，多智能体如何实现智能任务分配？”.

`reader-friction-v1.json#/ratings/4`, lines 15–22:

> 这个真是一坨垃圾了，各种莫名其妙的比喻，语法狗屁不通，上下文混乱，反正我完全看不懂

`refinement-pairwise-v1.json#/pairs/2` preferred the revision:

> 解释全新的概念，B通篇废话，A至少把问题解释清楚了，虽然文风冷淡

`refinement-pairwise-v2.json#/pairs/2`, different lines 1–6, qualified the win:

> A比B好的不多，只是稍微干净一点

Whole-article development should preserve these two distinct findings: some
explanatory repair helped a passage, but a small cleanup elsewhere was only a
small improvement. No full-article preference was collected.

### Challenge and secondary observations

`0431c592d5de8246cebcb8e2`, source URL
<https://www.infoq.cn/article/zYz0h5ygZd1M3cuWfUam>, has explicit complaints about
low-information expansion, unexplained quotation marks, and fragmented logic
in `reader-friction-v1.json#/ratings/6`. The preferred revision's comment in
`refinement-pairwise-v1.json#/pairs/1` was:

> A通篇废话，B把问题讲清楚了，但是文风太冷淡

This is a useful style-preservation challenge. Its story concerns a foreign
app/team, so compilation provenance needs review before it is eligible for
the primary route. The topic alone does not establish translation.

`48bda219eb0776f623161899`, `reader-friction-v1.json#/ratings/8`, lines 67–71:

> 每一句话的逻辑都明显断开。语法也生硬。

`48a7a6192771112323fd6820`, `reader-friction-v1.json#/ratings/2`, lines 119–125:

> 句法指代混乱，上下文跳跃混乱

The latter title describes line-by-line interpretation of an English agent
document. The lack of metadata translation flags must not be treated as
original-Chinese clearance. Neither secondary article needs to be opened for
the first leading-pair experiment.

## Lower-smell and control observations remain separate

- `b77b09a419c1631227112f0c`, post InfoQ, has mixed local evidence. The reader
  said most of lines 19–22 were acceptable while identifying particular
  framing; for the v2 pair on lines 7–10 the exact comment was
  “这两个几乎没有差别，而且AI臭味也不严重”. This supports a lower-smell
  passage observation, not a clean full article.
- `bf1abf6ca461ec0bbac14bd7`, pre InfoQ, lines 28–32, was rated smooth, with
  “这段我看不大出是ai写的，没什么臭味”. It is an exposed pre-period
  control observation, not evidence of authorship or period equivalence.
- `213dcab213f816c7c548fc09`, lines 270–275, elicited
  “这像是早期AI的文本，臭味不强，可以读一读”. Its
  `original_link_marker` prevents treating it as an admitted original control.
- `a127f5baf364930a89fb4005` has the v2 comment “没有任何区别”. A tie does
  not distinguish both acceptable from both problematic; it is not a
  low-smell label.
- `9e271d7b118c949e83c9ff8d`, pre InfoQ, lines 10–12, was hard to read:
  “信息很少，而且信息重要程度很低，但是句式繁杂，上下文乱切，逻辑跳跃”.
  Earlier material can contain relevant friction. Publication period cannot
  be used as the target label.

## Provenance conflicts must survive the route change

The pilot metadata has `is_translation=false` for all 30 documents. It also
records `original_link_marker` for three documents:
`73e9f6e61e27e1e32264551f`, `aa8f2104314751c5873dbab7`, and
`213dcab213f816c7c548fc09`. These are unresolved flags; an original link by
itself is not sufficient to decide the relationship to the source.

More seriously, `experiments/pilot-direction-probe.md:21–22` already identifies
`b186cdd4f9004e0413395bf3` as a known translated post document. The weak pilot
metadata failed to carry that finding. Later v2 reader work included a passage
from it and recorded “B很绕口” with a revised preference. Preserve that
historical observation while excluding the document from primary-route
admission. Do not silently change the frozen record or use the preference as
an exception to symmetric translation exclusion.

The inventory consequently records one known translation exclusion, three
unresolved provenance flags, and 26 documents with no recorded exclusion but
unresolved provenance. It records **no provenance passes**. Public availability
does not establish training rights: `training_rights` remains `unverified` for
all 30 documents.

## How much earlier reader work can be reconnected locally

| Annotation file | Persisted observations | Explicit distinct document IDs | Rows without a document ID |
|---|---:|---:|---:|
| `reader-friction-v1.json` | 10 | 9 | 0 |
| `refinement-pairwise-v1.json` | 3 | 3 | 0 |
| `refinement-pairwise-v2.json` | 10 | 7 | 0 |
| `reader-friction-screen-v1.json` | 11 | 11 | 0 |
| `reader-friction-screen-v2.json` | 3 | 3 | 0 |
| `reader-friction-screen-v3.json` | 6 | 0 | 6 |
| `refinement-pairwise-v3.json` | 12 | 12 | 0 |
| `refinement-pairwise-v4.json` | 10 | 10 | 0 |
| `integration-pairwise-v1.json` | 8 | 7 | 0 |

Across files there are 73 rows and 53 distinct explicit document IDs. Eleven
IDs with 23 observations have matching monthly bodies; 42 IDs with 44
observations do not. Six screen-v3 rows have no explicit `doc_id`; their pair
IDs must not be silently substituted for a document identity. Missing bodies
were neither searched outside the allowed scope nor downloaded. These counts
do not discard the wider 42-document feedback history.

Round-level observations are retained at round level. In particular, v3's
“这一轮几乎都没有区别，全是AI臭味都不明显” is not assigned as a new
document label; v4's position confound still invalidates a simple interpretation
of its aggregate treatment preference; the integration round's six unique
interventions remain split 3–3 after its controls passed. The failed screens
and their sampling problems remain design evidence.

## Immediate consequence for the next experiment

Use the two leading real articles with their complete stored context. Build
the article-level problem map and preservation ledger before creating edits.
Keep per-passage history available when interpreting the new whole-article
candidate. Judge a candidate against the same unchanged article and audit
cross-paragraph transitions and style loss; do not equate fewer framing words
with success. Model/agent review remains development evidence, and new human
full-article preference is still an unmet outcome. No SFT or GPU is required
for this preparation stage.

## Verification

The inventory ran on Python 3.13.5. An independent check rehashed all 54 input
files, verified every one of the 73 copied observation records against its
original JSON pointer, and confirmed the script hash recorded in the summary.
A repeated run produced identical document, observation, annotation-summary,
and source-hash artifacts. The earlier local run is retained at
`data/local/compact_refiner/media-inventory-v1-initial/`; the current run also
records the script and runtime identities. Compilation of the inventory
script passed, and Git confirms that the output directory is ignored.
