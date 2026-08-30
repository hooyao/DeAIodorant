# Word-Level Modifier-Bracketing Probe

## Status

Protocol `modifier-bracketing-probe-0.2` was frozen on 2026-08-31 before its
revised Stanza run, association count, candidate score, or reader task was
produced.
This is an exploratory computational gate over development-exposed material.
It is not an intervention, a validation study, or an authorship analysis.

The preceding character-to-word boundary model failed its frozen Stage 0 gate.
The present protocol is a new hypothesis with new measurements; it does not
relax, replace, or reinterpret the failed thresholds after the fact.

Version 0.1 completed one operational run but was not scientifically
interpretable. Twenty-six of 34 scorable candidates had a best-versus-second
margin below `1e-12`. The implementation compared each margin's percentile
midrank with 0.20; the tied minimum received midrank 0.382, making the intended
"at or below the 20th-percentile value" gate impossible. Version 0.2 freezes
two numerical corrections before rerunning: margins below `1e-12` become zero,
and raw values are compared with nearest-rank empirical quantiles. No semantic
threshold, corpus, candidate, association window, familiarity rule, or reader
outcome changed. Version 0.1 artifacts are retained as an operational
deviation, not hypothesis evidence.

## Frozen observation

One reader reported that the words in `AI 原生时代全新算力服务需求` were
individually understandable but difficult to assemble, and that the late head
`需求` delayed a stable reading. This is a single development observation.

The frozen SUBTLEX probe subsequently found no ambiguous character gap in the
pre-head string and assigned an unresolved distance of two. Across all 87
structural candidates it produced zero high-stratum cases. The observation is
therefore not explained by the tested character-to-word segmentation model.

## Dated evidence boundary

OpenAlex, Crossref, and Semantic Scholar were searched on 2026-08-31. Search
queries, result limits, API failures, and coverage limitations are preserved in
`modifier-bracketing-search-boundary.json`; source-to-claim links are in
`modifier-bracketing-evidence-ledger.csv`. The search was bounded and
English-metadata dominant. It does not establish novelty or a comprehensive
Chinese-language literature review. Semantic Scholar returned HTTP 429, and
OpenAlex exhausted its anonymous daily search budget after bounded pages.

The operational route is analogous rather than directly validated for Chinese
technical prose:

- Lauer (1995, <https://doi.org/10.3115/981658.981665>) compared statistical
  noun-compound analyses and found a dependency model more accurate than a
  deepest-constituent model in the reported English task.
- Barriere and Menard (2014,
  <https://doi.org/10.3115/V1/W14-5708>) combined lexical, relational, and
  coordinate association evidence for multiword noun-compound bracketing.
- Nakov (<https://arxiv.org/abs/1912.01113>) treated structural bracketing and
  explicit paraphrases of hidden noun relations as distinct problems.
- Fares (2016, <https://doi.org/10.18653/V1/P16-3011>) likewise represented
  bracketing and semantic relation interpretation as linked but separable
  targets.
- Dronjic (2011, <https://doi.org/10.1093/wsr/wsr005>) reviewed evidence that
  the word, rather than the morpheme, is the basic Mandarin compound
  representation unit.
- Hao, Wu, and Duan (2024,
  <https://doi.org/10.1177/21582440241256249>) reported processing differences
  involving word frequency, semantic transparency, and word structure.

None of these sources shows that the reader-localized construction is a
general smell or that the proposed measurement will work.

## Candidate hypotheses and rivals

### H-BRACKET: attachment competition

Familiar words in a long head-final nominal sequence support several similarly
plausible modifier-attachment trees. The reader must retain alternatives until
the final head, increasing integration effort.

### H-SEMANTIC: hidden relation underdetermination

The attachment structure may be recoverable, but relations such as how an
`AI 原生时代` makes a service requirement `全新` remain unstated. Structural
reordering without an explicit relation will therefore be insufficient.

### H-TERM: domain term or name mismatch

Low corpus association may reflect an established product name, technical
compound, title, or new domain term absent from the reference corpus. The
measurement would then mistake corpus coverage for reader friction.

### H-GLOBAL: passage-level load

The nominal span may only be a salient symptom. Clause density, proposition
load, referential structure, or surrounding argument organization may account
for the difficulty.

### H-PARSER: processing artifact

Stanza segmentation or dependency errors may manufacture the candidate span or
its apparent ambiguity. Parser agreement is not linguistic ground truth.

The predictions that distinguish these candidates are frozen in
`modifier-bracketing-prediction-matrix.csv`. Mixed explanations remain
possible.

## Input boundary

The probe uses exactly the 87 instances in
`feature_runs/nominal-chain-integration-v1/candidates.jsonl`, SHA-256
`abfb5a5e9181c5b0e87d5636f649766c1c82437326ac5a0740229eec89e674c2`.
They come from 67 development documents in `post_reader_handoff_v2` and all 93
discovery-exposed documents in `post_reader_handoff_v3`. The 30-document
validation reserve is excluded by the earlier candidate generation and must
not be opened.

All association counts use only the same 160 development/discovery documents
and the frozen complete-prose gate. Counts for a candidate exclude its entire
source document. This leave-one-document-out rule avoids using repetition
inside one article as attachment support.

## Frozen parser and alignment gate

Parsing runs only on `gx10` with Stanza `zh-hans/gsdsimp`, processors
`tokenize,pos,lemma,depparse`, and the already recorded model fingerprint
`5fa23dfff06b543c63ef547b32006bb0a9acdd6bc1a3a1df23d768a171352af9`.

For every candidate, reparsing must reproduce the source sentence, head form,
left boundary, and pre-head lexical-token count. The target sequence contains
all non-punctuation tokens from the left boundary through the head. Candidates
with fewer than four or more than 10 target tokens, an internal verb, an overt
coordination or `的/之` boundary, or failed alignment abstain. No token or
dependency correction is allowed by hand.

## Cross-fitted association model

Content-token lemmas are case-folded; missing lemmas fall back to surface form.
The association corpus records, separately by document and source:

- token occurrence count and document/source frequency;
- ordered token-pair count within the next four content tokens;
- adjacent ordered-pair count;
- exact target-sequence document and source frequency;
- overt coordinate occurrences joined by `、/和/与/及/或`.

For candidate document `d`, all counts contributed by `d` are subtracted.
The primary attachment probability is Lauer-style conditional association:

~~~text
P(head | modifier, not d)
  = (ordered_pair_count + 0.1)
    / (all_outgoing_pair_count_for_modifier + 0.1 * vocabulary_size)
~~~

Adjacent NPMI, pair document/source frequency, coordinate evidence, and exact
sequence termhood remain separate diagnostics. They do not alter the primary
tree probability in version 0.2.

A token is `cross-corpus familiar` only when it occurs in at least five other
documents and at least two sources. The fraction of familiar target tokens is
reported. Low familiarity is evidence for H-TERM or corpus insufficiency, not
automatically high bracketing competition.

## Right-headed bracketing lattice

Enumerate every full binary bracketing over the target word sequence. Every
constituent inherits its rightmost lexical head. Combining left and right
constituents adds one directed attachment from the left constituent's head
to the right constituent's head. A tree score is the sum of log conditional
attachment probabilities.

Softmax normalization over all tree scores yields:

- normalized tree entropy, divided by `log(Catalan(n - 1))`;
- best-versus-second tree margin divided by `n - 1` attachments;
- posterior probability of each attachment;
- number of best-tree attachments supported by no more than one other document
  and one source;
- best bracketing and its attachment audit.

The probe exposes this vector and does not collapse it into a generic writing-
quality score.

## Frozen computational gates

Percentiles are computed over scorable instances in the fixed 87-candidate
pool. This makes the run exploratory and relative to this pool; it does not
create an external norm.

The 80th-, 20th-, and 50th-percentile gates use the nearest-rank empirical
value: sort `n` measurements and select item `ceil(p * n)`, with one-based
indexing. The gate compares the raw measurement to that value. Midrank
percentiles remain descriptive only.

A candidate is `high bracketing competition` only when:

- normalized tree entropy is at or above the pooled 80th percentile;
- normalized best-versus-second margin is at or below the pooled 20th
  percentile;
- at least 80% of its target tokens are cross-corpus familiar;
- at least two best-tree attachments have support from no more than one other
  document and one source.

The working example must be fully aligned, have familiar-token fraction at
least 0.80, entropy at or above the pooled median, margin at or below the pooled
median, and at least two weak best-tree attachments. Failure challenges
H-BRACKET under this measurement and stops the route.

The multi-source gate additionally requires at least eight high-competition
documents from at least three sources. Select at most three documents per
source by the fixed tuple of decreasing entropy, increasing margin, decreasing
familiarity-adjusted weak-edge count, and SHA-256 tie break. The selected eight
must include at least four cases without a proper-name, numeric, ASCII, or
quoted-title anchor. This is a coverage requirement, not manual deletion of
anchored cases; anchor-stratified counts remain in the report.

Failure of the working-example gate or multi-source gate ends version 0.2. Do
not change association windows, smoothing, familiarity counts, percentiles,
parser tokens, or anchor definitions after seeing results.

## Interpretation matrix

- Example and multi-source gates pass, anchors do not dominate: retain
  H-BRACKET as a test-ready development candidate and design a separate
  boundary-only intervention.
- High scores occur mainly in anchors or unfamiliar terms: retain H-TERM and
  reject the bracketing selector.
- The example has low tree entropy despite valid measurement: challenge
  H-BRACKET and prioritize H-SEMANTIC.
- Parser alignment or association coverage fails: the result is indeterminate;
  revise measurement on independent material rather than interpreting it as
  linguistic evidence.
- Global passage features may coexist with any result and require a future
  matched intervention to distinguish H-GLOBAL.

No outcome from this computational probe authorizes Project 8 directly. A
reader experiment still requires a separately frozen operator, preservation
audit, high/low matching, position controls, and the same low-burden continued-
reading question.

## Reproduction plan

The tracked implementation will emit token and attachment audits, candidate
measurements, gate attrition, source/anchor composition, parser identity, input
hashes, and a summary under ignored `feature_runs/`. Two independent `gx10`
runs must be byte-identical before the result is interpreted.

## Result

Version 0.2 ran twice on `gx10` and produced byte-identical artifacts. It parsed
1,393 complete passages from 133 of the 160 requested documents, yielding
5,670 sentences, 9,100 content-token types, and 160,747 ordered pair types. The
30-document validation reserve was not requested or opened.

Of the 87 frozen candidates, 34 contain only the prespecified content POS and
are scorable. The other 53 abstain because a non-content token occurs inside
the target sequence; there are zero fatal alignment failures. This exclusion
is mechanical and was fixed before the run.

The reader example passes its case-level gate:

- target tokens: `AI / 原生 / 时代 / 全新 / 算力 / 服务 / 需求`;
- normalized tree entropy: 0.822, above the empirical median 0.636;
- best-versus-second margin: 0.000, at the empirical median 0.000;
- cross-corpus familiar-token fraction: 0.857;
- weak best-tree attachments: four;
- entropy percentile among the 34 scorable candidates: 0.765.

The example result is a successful localization of the one observed case, not
independent evidence for a general selector. Its best tree has only 0.065
posterior probability, and four attachments have support from at most one
other document and one source.

The independent-candidate gate fails:

| Gate component | Instances | Documents |
|---|---:|---:|
| Entropy at or above P80 | 7 | 6 |
| Margin at or below P20 | 26 | 16 |
| Familiar-token fraction at least 0.80 | 17 | 13 |
| At least two weak attachments | 27 | 17 |
| Entropy and margin jointly | 5 | 5 |
| Entropy, margin, and familiarity jointly | 0 | 0 |

The five high-entropy, zero-margin instances are low-familiarity names or
technical strings, including source phrases beginning `Multi Animate`,
`蚂蚁数科首期开源实时`, `韩国 KG 集团旗下咖啡`, `Union Jack 格子
Bose-Hubbard`, and `Nine Data 增量复制任务`. Familiar candidates do not share
the same high-entropy/low-margin pattern. This is consistent with H-TERM or
association-corpus sparsity and yields no multi-source H-BRACKET set.

Therefore `modifier-bracketing-probe-0.2` fails Stage 0. Retain
H-BRACKET only as a localized candidate explanation for the reader example;
reject the current tree-entropy vector as an intervention selector. H-SEMANTIC,
in which the hidden relations between familiar words remain unspecified, is
now the stronger development direction. This comparison does not establish
that H-SEMANTIC is true.

Do not create Project 8, relax the familiarity rule, lower the entropy gate, or
manually remove names from these outcomes. A new test of familiar-word weak
relations must freeze its measurement and use an independent corpus rather
than reselecting these 87 candidates.

## Reproduction identity

The tracked script copied to `gx10` has SHA-256
`3c7c0ce5c5effc2ff4b5b3a7c4fe149d5964e44e6cd11816246ce4d155c5b331`.
Two independent runs produced:

| Artifact | SHA-256 |
|---|---|
| Summary | `80f09a3d7827f658c93abd9c38387b49bb309e846d727f0155043138d981bce1` |
| Candidate measurements | `5bcfc6475cf17697ebcd4c6d04603b738be26b31c6e6f0878aa787faeaa47e35` |
| Mechanical abstentions | `8334f8bb7a21c77bffc011264599a7a6cd1ae71918bbda58ce067696ed95aeff` |
| Empty selected-candidate file | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

~~~bash
PYTHONPATH=/home/hooyao/DeAIodorant-post-v2/src:/home/hooyao/deaiodorant-modifier-bracketing-v1/run \
  /home/hooyao/DeAIodorant-post-v2/.venv/bin/python \
  modifier_bracketing_probe_v02.py \
  --candidates /home/hooyao/deaiodorant-nominal-chain-v1/output-v2/candidates.jsonl \
  --handoff /home/hooyao/deaiodorant-nominal-chain-v1/data/post_reader_handoff_v2 development \
  --handoff /home/hooyao/deaiodorant-nominal-chain-v1/data/post_reader_handoff_v3 discovery_reserve \
  --model-dir /home/hooyao/deaiodorant-nominal-chain-v1/models/stanza \
  --output-dir /home/hooyao/deaiodorant-modifier-bracketing-v1/output-v2a \
  --device cuda \
  --seed 2026083102
~~~
