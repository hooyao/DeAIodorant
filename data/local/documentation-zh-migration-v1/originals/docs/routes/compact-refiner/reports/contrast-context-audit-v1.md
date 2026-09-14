# Whole-Article Contrast and Reading-Defect Audit

Date: 2026-09-14. Protocols: `contrast-context-audit-1.0`,
`contrast-context-review-validation-1.0`, `contrast-syntax-feasibility-1.0`,
and `provenance-stratified-contrast-1.0`.

## Research decision

The next research unit is a source-linked reading problem in a complete real
Chinese article. Study repetitive framing, sentence/reference defects, and
unsupported discourse relations together, preserving their distinct evidence.
Translated Chinese is a required product capability and remains in the research
population. Original-only selection is now a sensitivity/control view, not a
global exclusion rule. The default compact-model input is Chinese alone.

This audit does not establish an automatic smell detector, reader benefit,
training acceptance, or causes in proprietary model training. No strong human
smell label was added. The Cowork article remains reader-described as difficult
and translationese-like but weak in AI smell.

## What was completed

Two independently prompted assistants read the same 13 complete articles and
reviewed all 57 literal `而是` occurrences selected by the preceding
known-translation-filtered count. Publication metadata and prior judgments were
withheld; article content still reveals topic, period, and format. The reviewers
did not read each other's files or the later Gemini reference discussions.
No precise checkpoint identity was available, so their records say unknown.

All 57 occurrence quotations in each review cover their assigned source offsets.
Every additional evidence, support, and counterexample quotation is source-exact.
The first reviewer proposed 25 localized reading defects and 18 counterexamples;
the second proposed 23 and 25 respectively. These are overlapping proposals,
not 48 independently established errors. Whole-body review is attested by each
assistant and its recorded access, not proven by the quote validator.

| Judgment | Exact agreement | Interpretation |
|---|---:|---|
| Dominant semantic relation | 51 / 57 | Useful descriptive consistency on this selected set |
| Reporter versus attributed voice | 56 / 57 | Attribution is comparatively stable here |
| Ordinary versus possibly repetitive packaging | 44 / 57 | Material uncertainty remains about redundancy |

Reviewer A nominated 9 repetition candidates and reviewer B 20; their union
contains 21, while only 8 were nominated by both. These disagreements are
retained. Majority or intersection labels cannot replace reader preference or
become an automatic reward. The eight shared nominations include conversational
recaps, which can be useful in an interview.

## Concrete findings and counterexamples

### Meaningful contrasts and repetitive presentation can coexist

The ClickHouse storage explanation distinguishes dynamic paths from shared
storage. Cowork's restricted-folder versus full-disk authorization contrast
communicates an important scope boundary. Both should survive any attempt to
reduce recurring connective language.

In the Alibaba cloud article, both reviewers nominate two adjacent governance
summaries, `doc-02-e05/e06`, after a concrete four-step workflow. The latter
repeats the trust-through-control point using the metaphor of restraints versus
a trusted boundary. This is a proposed redundancy problem with an identifiable
earlier statement; it is not established by the connector alone.

### Predicate coordination can change the implied actor

The Tencent routing article says:

> 这让路由不再是黑盒，而是可解释、可 Debug、可持续优化 Agent 描述。

The coordinated list moves from properties of routing to the action of
optimizing agent descriptions. Both reviewers identify the mismatch, although
they differ on its category and repairability. A repair must clarify the
relation without inventing an actor or additional model behavior. This is more
specific than counting missing subjects, verbs, or objects.

### A localized defect can occur without the nominated connector

Cowork's late paragraph moves from comments to users, then to
`Anthropic 近期产品策略与沟通的不满`, and concludes with
`对 Cowork 的发布背景和用户关系具有间接关联语境`.
Both reviewers locate the unclear attachment and relation in the same sentence.
Removing collector-inserted newlines does not resolve it. The qualification
that these comments are not specifically about Cowork remains material.

The low-marker Doris article also contains a boundary problem at
`资源隔离通过将计算层与存储层解耦`. One reviewer locates it; the other gives
no sufficiently confident additional defect. Independent CPU case inspection
also identifies the awkward boundary. The disagreement remains in raw evidence.

### A polished contrast can strengthen a claim beyond its support

The long translated interview's introduction says the limiting factor for AGI
is not model capability but humans. The interview answer instead describes
human limitations as one underestimated factor among several. Both reviewers
identify stronger exclusivity and scope in the introduction. This is an
article-internal attribution problem, not a factual verdict about AGI.

The Candle report cites revenue and then refers to achieved profitability;
it later moves from the social app into an AI-native business conclusion without
establishing an AI component in that current app. Both reviewers identify the
missing support. The company's previous AI shopping project does not establish
that connection for the replacement product. A stylistic rewrite cannot invent
costs, profit, or an AI mechanism.

### Ordinary ellipsis and article format remain counterexamples

In the Doris article, `最终采用后者作为临时方案` has a recoverable team actor
and an explicit preceding pair of choices. Cowork's `其次是新增的一系列技能`
is an ordinary list item. Neither becomes erroneous for lacking a repeated
subject or a transitive verb-object form.

Interview acknowledgements, summaries before transcripts, code blocks, captions,
and roundups explain some apparent repetition or topic jumps. A pre-period
container article contains the malformed `而是实际上`, showing that local
language problems also occur in the historical baseline. No age or provenance
stratum is automatically good writing.

## Local concentration is different from whole-body count

The deterministic preparation retained all 35 documents from its frozen
selection, including 22 zeros. CJK coordinates use the same Extension-A/basic
BMP character definition as the earlier count. Windows measure connector-start
positions, with maximum minus minimum strictly below the stated width.

| Article | Body CJK characters | Total occurrences | Maximum within 500 CJK | Maximum within 1000 CJK |
|---|---:|---:|---:|---:|
| Long Codex interview | 17,540 | 19 | 3 | 4 |
| Cowork report | 2,669 | 8 | 4 | 6 |
| Alibaba cloud article | 3,877 | 8 | 4 | 5 |
| Tencent routing article | 1,296 | 5 | 4 | 5 |
| ClickHouse explanation | 2,163 | 1 | 1 | 1 |

These are overlapping descriptive maxima, not validated irritation thresholds.
Cowork remains a direct counterexample to interpreting concentration as a
strong-smell label. Heading, quote, and code composition can affect the measure.
All original metrics reproduced byte-identically after two preventive integrity
fixes: exhaustive unique offset comparison and binding current source identities
to the preceding manifest. The initial packet was valid and unchanged.

## Translation correction and the new retained population

The long interview explicitly says:

> 我们翻译了该内容，并在不改变原意基础上进行了删减和整理，以飨读者。

The previous automatic flag missed this disclosure. A separate audit checked
all 35 retained bodies for provenance markers and their contexts, all available
metadata, and 18 local full HTML captures. It confirmed this one additional
translation. The other 34 remain unresolved, including two Snowflake items
with labeled external-original links. Names or English URL slugs alone did not
determine source language. No original-language sources were fetched.

The new statistical view retains all 40 available nonempty InfoQ articles.
Existing and newly documented translations remain a provenance stratum.

| View | Pre articles / occurrences | Post articles / occurrences | Pre / post occurrences per 10,000 CJK |
|---|---:|---:|---:|
| All available media retained | 18 / 5 | 22 / 65 | 0.96 / 8.38 |
| Documented translation/adaptation | 1 / 0 | 5 / 32 | 0.00 / 9.23 |
| Unresolved provenance | 17 / 5 | 17 / 33 | 1.04 / 7.70 |
| Historical known-translation-filtered result | 17 / 5 | 18 / 52 | 1.04 / 8.61 |

The all-media rate ratio is approximately 8.7; the unresolved-stratum ratio is
approximately 7.4. The previously reported 8.3 belongs to the preserved old
selection before the missed disclosure was found. The unresolved stratum is
not an original-Chinese cohort. These small, unmatched samples do not estimate
translation effects, prove authorship, establish a July breakpoint, or locate
the origin of a defect. The single pre-period documented translation is an
inadequate comparison group.

## Actual CPU syntax experiment

Stanza 1.14.0 with installed `zh-hans/gsdsimp` models and Torch 2.13.0 parsed
three complete articles on CPU, one computation/interoperation thread, seed
20260914. Two successful runs took 65.328 and 69.421 seconds. All nine
source/annotation/CoNLL-U artifacts were byte-identical, with 164 parser
sentences and 5,602 words. These are execution counts, not error denominators.

Awkward wording still receives complete trees. In the routing article,
`无法确定不确定` becomes a nested complement structure. The awkward Cowork
sentence receives grammatical-looking attachments without resolving its
reference. Conversely, ordinary shared-subject clauses lack overt subject
edges, and technical `路由` is sometimes split into two words.

The parser also merges headings with prose and one SQL block with its following
heading and paragraph. A 207-character Cowork URL block becomes `<UNK>`.
Fourteen token/source-surface discrepancies remain traceable because the exact
source spans are retained. Parser token text cannot substitute for source
evidence. These results reject using missing-subject counts or complete parse
trees as a stand-alone quality rule; they retain parsing as an inspection aid.

The first launcher attempt died before annotations, and its precise exception
was unavailable. Its state/snapshot remain preserved. The corrected driver
waits for its seeded subprocess and records failure diagnostics only inside
the newly created run directory. Ground-truth process/artifact checks and the
two completed runs are documented in the private feasibility report.

## Next experiment and promotion boundary

The [bounded repair development](../media-repair-development.md) now uses three
complete Chinese articles, including the translated interview. An editor sees
Chinese text only and proposes source-supported operations; a separate reviewer
checks complete originals and variants. No SFT, preference export, or GPU is
scheduled. Reader evaluation must distinguish readability improvement from
smell removal and must not relabel these exposed sources as fresh validation.

The current feature directions are local contrast concentration, repeated
evaluative propositions, semantic-role discontinuity, and evidence-scope
inflation. The first has a deterministic implementation; the others are
source-anchored annotation hypotheses, not validated NLP rewards.

## Reproduction and artifacts

```powershell
python experiments/contrast_context_audit.py --output-dir data/local/contrast-context-v1-reproduction
python experiments/summarize_contrast_context_reviews.py --input-dir data/local/contrast-context-v1 --output-dir data/local/contrast-context-v1-summary
python experiments/provenance_stratified_contrast_statistics.py --output-dir feature_runs/provenance-stratified-contrast-v1
python experiments/contrast_syntax_feasibility.py --model-dir models/stanza --output-dir data/local/contrast-syntax-v1/reproduction-02
```

The listed output directories are existing frozen runs; a repetition requires
new output paths. Preparation and numeric summaries are deterministic; assistant
review generation is not guaranteed deterministic. Manifests bind all source,
review, code, protocol, model, and output artifacts. No external API requests,
new downloads, GPU, training, or changes to source corpora/old feedback occurred.

Private records: `data/local/contrast-context-v1/` (packets, independent reviews,
provenance addendum and original implementation snapshot),
`data/local/contrast-context-v1-summary/`,
`feature_runs/provenance-stratified-contrast-v1/`, and
`data/local/contrast-syntax-v1/` (failed start, successful runs, six inspected
cases, process checks, and report).
