# Chinese Writing Smell Catalog

## Purpose

This catalog records reader-disliked, potentially editable Chinese writing
patterns. It is the bridge between corpus observations and refinement research.

A corpus difference is not automatically a smell. A pattern is promoted only
when its status and evidence justify the claim.

## Evidence statuses

| Status | Meaning |
|---|---|
| Hypothesis | Proposed from reading, theory, or sparse corpus evidence |
| Pilot quantified | Measured in the current small corpus with stated limitations |
| Reader reported | A reader explicitly describes the pattern as disruptive |
| Intervention validated | A bounded edit improves blinded reader preference without meaning loss |
| Product validated | The edit generalizes across held-out genres and real usage |

Multiple statuses may apply. “Reader reported” currently means direct
qualitative evidence, not population-level validation.

## Required record schema

Every smell record must include:

- stable ID and name;
- current evidence statuses;
- reader experience;
- linguistic realization;
- counterexamples and exclusions;
- direct and proxy metrics;
- exact formulas and denominators;
- current quantitative evidence;
- corpus, model, and configuration fingerprints;
- reproduction commands;
- known confounders;
- minimum intervention experiment;
- promotion or rejection condition.

Do not silently change an established metric. Create a new metric version.

---

## SMELL-001: Mainline interruption and insertion load

### Status

- Reader reported
- Pilot quantified through punctuation proxies
- Not intervention validated

### Reader experience

The reader is following an unfinished main clause when a dash, parenthesis,
quotation, colon-led explanation, or parenthetical clause introduces a
different information unit. The reader must retain the suspended mainline in
working memory, process the inserted material, and then recover the original
dependency.

Direct reader description:

> “就像在吃东西的时候硬生生把你打断，再喂给你别的东西吃。”

The aversion is not punctuation itself. It is forced context switching during
an incomplete information sequence.

### Typical linguistic realization

- a long dash insertion before the main proposition is complete;
- paired dashes or parentheses containing a detachable explanation;
- quotation marks around ordinary terms that create unnecessary emphasis;
- a colon followed by another explanatory unit inside an already complex
  sentence;
- several short rhetorical interruptions in one sentence;
- an inserted clause that could stand as a following sentence.

Synthetic example:

> 系统需要重新设计——尤其是在多个智能体并行调用、失败重试和权限动态变化的情况下——才能稳定运行。

Potentially smoother alternatives move the qualification before the main
claim, place it after a completed sentence, or split the information into two
sentences.

### Counterexamples and exclusions

Do not count all punctuation as harmful:

- ranges, minus signs, and lexical hyphens;
- code, command-line arguments, URLs, and identifiers;
- tables and enumerated specifications;
- transcript speaker labels;
- quotations where attribution matters;
- short parentheses that define an abbreviation;
- a dash after a complete sentence used once for a deliberate rhetorical turn;
- punctuation required to prevent ambiguity.

The same punctuation can be useful when it aligns with a completed semantic
boundary.

### Current proxy metrics

#### Punctuation density v1

~~~text
punctuation_density =
    Unicode punctuation code points / non-whitespace code points
~~~

#### Punctuation entropy v1

~~~text
punctuation_entropy =
    -sum(punctuation_type_probability * log2(punctuation_type_probability))
~~~

#### Dash density v1

~~~text
dash_density =
    occurrences of —, –, or - / non-whitespace code points
~~~

Dash density v1 intentionally reflects the existing implementation. It mixes
em dashes, en dashes, and hyphens and must be replaced by context-specific dash
metrics before causal interpretation.

### Proposed direct metrics

#### Insertion-event rate v2

~~~text
insertion_event_rate =
    mid-sentence detachable insertion events / parsed sentences * 100
~~~

Candidate insertion events include paired dashes, paired parentheses, and
dependency subtrees marked as parenthetical, appositional, paratactic, or
discourse material inside a larger clause.

#### Insertion span length v2

~~~text
insertion_span_length =
    syntactic tokens between insertion boundaries
~~~

Report mean, median, 90th percentile, and maximum per document.

#### Mainline suspension distance v2

~~~text
mainline_suspension_distance =
    continuation token index - interruption start token index
~~~

The continuation is the first token after the insertion that reconnects to the
pre-insertion head or completes its unresolved dependency.

#### High-interruption sentence ratio v2

~~~text
high_interruption_sentence_ratio =
    sentences with at least two insertion events
    or at least one insertion spanning 12 tokens
    / parsed sentences
~~~

The 12-token threshold is provisional and must be frozen before replication.

#### Detachability rate v2

Remove each candidate insertion and reparse with the same fixed parser.

~~~text
detachability_rate =
    candidate insertions whose removal preserves one root,
    all original non-insertion entities and numbers,
    and a connected dependency tree
    / candidate insertion events
~~~

#### Context-deviation score v2

Use TF-IDF, not embeddings or an LLM.

~~~text
context_deviation =
    1 - cosine(
        TF-IDF(insertion),
        TF-IDF(left context + right context)
    )
~~~

Keep this component separate from syntactic suspension until reader data can
justify a combined index and its weights.

### Current pilot evidence

Primary comparison: 10 pre-period InfoQ versus 10 post-period InfoQ documents.

| Proxy | Pre mean | Post mean | Hedges' g | Translation-removed g | Permutation p | BH q |
|---|---:|---:|---:|---:|---:|---:|
| Total punctuation density | 0.08 | 0.10 | 2.08 | 2.00 | 0.0002 | 0.030 |
| Punctuation entropy, bits | 2.40 | 3.22 | 1.70 | 1.81 | 0.0018 | 0.090 |
| Dash density | approximately 0.00 | approximately 0.01 | 1.58 | 1.79 | 0.0006 | 0.045 |

All directions survived leave-one-document-out removal. Removing the known
translated post document did not reverse them.

This evidence establishes a pilot punctuation difference and one direct reader
complaint. It does not establish that punctuation caused the complaint or that
the effect generalizes.

A later 96-document transition discovery pool adds source-stratified but
non-confirmatory directions. Quote-mark density rises with transition date in
both InfoQ and Machine Heart (combined partial rho 0.286, p 0.0054, BH q
0.286). Dash density also rises in both sources (rho 0.250, p 0.0138, q 0.336).
Total punctuation density is source-inconsistent. These results do not use a
post-period cohort and do not change the evidence status.

### Reproduction identity

| Artifact | Fingerprint |
|---|---|
| Corpus | d6cfb16560de7904ab5dc34a09e35e69642e7f39cb61d517a9bd1ffbc2a43014 |
| Annotation manifest | 6b774f981c8f173209735b2b39ca909fc38877480c2483e18949eb3f34e4eaac |
| Feature configuration | a40847a003f5df7068967470501cea7ec3cacc974c5ca2a4b9630278c54a3c0e |
| Stanza model files | 5fa23dfff06b543c63ef547b32006bb0a9acdd6bc1a3a1df23d768a171352af9 |
| Experiment commit | 2bc3692 |

### Reproduction commands

~~~powershell
deaiodorant-analysis annotate --corpus data/pilot/monthly --config configs/features.v1.json --model-dir models/stanza --output feature_runs/pilot-annotations-v1 --device cpu

deaiodorant-analysis extract --corpus data/pilot/monthly --config configs/features.v1.json --annotations feature_runs/pilot-annotations-v1 --output feature_runs/pilot-matrix-v1
~~~

On a CUDA host:

~~~bash
python experiments/pilot_direction_probe.py \
  --matrix-dir feature_runs/pilot-matrix-v1 \
  --output-dir feature_runs/pilot-probe-v1 \
  --dense-permutations 20000 \
  --sparse-permutations 5000
~~~

Detailed results are recorded in
[Pilot Direction Probe](../experiments/pilot-direction-probe.md).

### Known confounders

- current InfoQ editorial and formatting changes;
- code, lists, headings, quotations, and transcripts;
- translated or compiled content;
- longer post-period documents;
- unmatched topic and article format;
- dash v1 mixing lexical hyphens with em dashes;
- only 10 documents per same-source cohort.

### Minimum intervention experiment

1. Select 20 high-interruption sentences and 20 matched low-interruption
   sentences without showing cohort.
2. For each high-interruption sentence create:
   - unchanged original;
   - insertion moved after a completed main clause;
   - insertion split into a separate sentence.
3. Preserve all entities, numbers, claims, negation, and modality.
4. Ask which version is easier to continue reading.
5. Record whether the preference is caused by rhythm, clarity, brevity, or
   meaning change.

### Promotion condition

Promote to “intervention validated” only if:

- reduced insertion load improves blinded reading preference;
- the result appears in more than one genre;
- meaning-preservation checks pass;
- useful quotations, definitions, and intentional rhetorical turns are not
  systematically removed.

Reject or narrow the smell if readers dislike only one punctuation subtype or
if the effect disappears after removing formatting and translated content.

---

## SMELL-002: Formulaic contrastive and emphatic reframing

### Status

- Hypothesis
- Pilot quantified
- Post-only reader association observed in eight passages
- Initial intervention directionally positive: two revised wins, one tie
- Second intervention directionally positive: six revised wins, four ties,
  zero original wins
- Third development intervention mixed: four revised wins, one original win,
  seven ties; baseline smell was generally weak
- Raw-passage candidate screen failed: 10 of 11 persisted ratings in one band
- Within-document enrichment screen terminated after three transition-period
  no-difference responses; ranking not evaluated
- Fresh post-only raw screen terminated after within-document over-control;
  fourth original-versus-revision intervention frozen, outcomes pending
- Broad typed relation-support score rejected
- Not intervention validated

### Candidate reader experience

The prose repeatedly converts direct claims into staged contrasts or emphatic
revelations. The logical content may be simple, but the sentence presents it as
a correction, reversal, or discovery.

### Typical linguistic realization

- “不是 X，而是 Y”
- “并非 X，而是 Y”
- “不再是 X，而是 Y”
- “不仅是 X，而是 Y”
- “正是...”
- “关键在于...”
- “问题不在于 X，而在于 Y”

Some uses express a necessary logical distinction. The candidate smell is
frequency, concentration, and ornamental use, not the construction itself.

### Quantification v1

#### Contrast-frame rate

~~~text
contrast_frame_rate =
    matched complete contrast frames / parsed sentences * 1000
~~~

Initial regular expression:

~~~text
(?:不是|并非|不只是|不仅是|不再是).{0,80}?而是
~~~

Run within sentence boundaries. Do not allow the expression to cross paragraph
or sentence boundaries.

#### Emphasis-frame rate

Count individual constructions per 1,000 sentences:

- 正是
- 关键在于
- 问题在于
- 这意味着
- 值得注意的是

#### Document coverage

~~~text
document_coverage =
    documents containing at least one frame / documents
~~~

#### Frame burstiness

~~~text
frame_burstiness =
    maximum frames in one paragraph / total document frames
~~~

Report zero when no frames occur.

### Current pilot evidence

| Pattern | Pre InfoQ documents | Post InfoQ documents | Pre count | Post count |
|---|---:|---:|---:|---:|
| Complete negative contrast frame | 0 of 10 | 5 of 10 | 0 | 24 |
| Same after removing known translation | 0 of 10 | 4 of 9 | 0 | 15 |
| 正是 | 1 of 10 | 8 of 10 | 1 | 14 |
| 关键 | 2 of 10 | 10 of 10 | 5 | 35 |
| 系统性 | 0 of 10 | 5 of 10 | 0 | 6 |
| 缺乏 | 0 of 10 | 5 of 10 | 0 | 7 |

The sparse search tested 6,597 patterns, and none survived global
Benjamini-Hochberg correction. These consolidated constructions are exploratory
and were selected after inspection.

In the later reader calibration, complete contrast-frame rate had a post-only
Spearman correlation of 0.78 with reading friction. The exact permutation p was
0.036, but the result did not survive correction across the expanded feature
set and uses only eight post-period passages.

A later typed relation-support probe must not replace this specific result with
a broad connective claim. After sentence-count normalization, broad contrast
density had a robust time effect of 0.06 and post-only reader rho 0.51. Emphasis
density had a robust time effect of 1.34 but reader rho 0.17. Neither survived
multiple-testing correction.

The 96-document transition discovery pool also does not generalize the complete
frame result. Complete negative contrast frames have combined partial rho 0.050
with opposite-to-flat source directions (InfoQ 0.131, Machine Heart -0.016; BH
q 0.834). Emphatic-frame density is source-consistent at rho 0.221, but its BH
q is 0.388 and it remains a discovery hypothesis rather than intervention
evidence.

The proposed high-confidence problem metric also failed. Problem decisions per
100 sentences had a time effect of 0.04 and reader rho 0.06; the corresponding
ratio had a time effect of -0.03 and reader rho 0.00. It decreased in only two
of the 10 second-round revisions. The v0.1 aggregate is rejected as a smell
score.

### Reproduction

Use the same corpus, annotation, configuration, and commands as SMELL-001.
The one-off consolidation and sensitivity analysis are implemented in
**experiments/pilot_direction_probe.py** and documented in
[Pilot Direction Probe](../experiments/pilot-direction-probe.md).

### Known confounders

- technical argument genre;
- author and editor preferences;
- translated English contrast structures;
- post-period topics involving product positioning;
- multiple testing and post-hoc construction selection;
- longer post-period documents.

### Minimum intervention experiment

Select 20 contrast frames. Create a direct declarative version that preserves
the actual distinction without staging it as a revelation. Compare:

1. original contrast frame;
2. direct claim;
3. contrast frame retained only when both sides are independently informative.

The primary question is whether readers prefer fewer ornamental reversals, not
whether the construction can identify a cohort.

The first three-pair implementation produced two clear preferences for the
revised version, no preference for the original, and one tie or both-bad
judgment. Both successful revisions were described as clearer but too cold.
The failed revision omitted too many explicit grammatical arguments. This is
directional evidence only. The next version must preserve subject-predicate-
object completeness and voice while reducing ornamental framing.

The second-round implementation froze that revised operator before outcomes.
It contains 10 new post-period passages from seven documents and is disjoint
from all 10 reader-friction development ranges. The operator retains necessary
contrasts, explicit arguments, propositions, entities, numbers, negation,
qualifications, uncertainty, attribution, and selected voice cues. Its
structured audit contains 26 exact before/after operations and 62 proposition-
support checks. All deterministic generation gates pass, and the fixed seed
balances the original side five-to-five.

The intervention reduces the frozen surface diagnostics from nine complete
contrast frames and 16 emphasis markers in the originals to zero counted
instances in the revisions. This verifies manipulation fidelity only.

Six revised passages were clearly preferred, no original was clearly
preferred, and four comparisons were ties or neither-preferred. Two tied
comments described the revision as slightly better, but they remain ties in
the primary outcome. No comment reported missing facts or changed logic.

The comments also identify boundaries. Minimal edits to low-smell passages can
be imperceptible. Removing formulaic contrast does not remove every abstract or
generic claim around it. In one preferred revision, the reader specifically
described `相反`, `这样一来`, and `它真正解决的` as empty or misleading
relation framing. In one tie, a retained statement about cloud changes
“naturally” requiring engineering support was still disliked.

The two intervention rounds total eight revised wins, zero original wins, and
five ties. They use one reader, selected InfoQ passages, and repeated passages
from one document. The evidence status is therefore not promoted to
“intervention validated.”

A third cross-genre development round used 12 transition passages from 12 new
documents. It produced four revised wins, one original win, and seven ties or
neither-preferred judgments. The reader reported that the passages generally
had little obvious smell, so most edits made little difference. One optional
comment specifically identified `换句话说`; removing it was preferred.

The third round does not contradict the earlier high-friction wins. It shows
that marker presence alone has poor precision for selecting intervention
targets. Do not respond by maximizing compression or editing intensity.

A separate low-burden baseline-friction screen was frozen before outcomes. It
contains 24 unchanged passages from 24 previously unexposed transition
documents, balanced by source and passage length. Selection uses no smell
feature or marker count. Only the two unwilling-to-continue ratings qualify a
passage for a later intervention, and optional comments cannot influence
selection. All screened passages remain outside held-out validation. This
screen does not promote the smell evidence status.

The screen was terminated after 11 persisted responses because 10 occupied the
same `fairly willing to continue` category and only one reached the frozen
eligibility gate. The reader described the batch as having no discrimination.
Do not interpret the one eligible passage as a selected intervention target or
complete the remaining tasks. A within-document candidate-versus-control
comparison is needed to test enrichment without relying on a collapsed
absolute scale. An explicit no-meaningful-difference choice remains mandatory.

That replacement is now frozen before outcomes. It contains 10 same-document
pairs: a marker-bearing candidate that also has at least one auxiliary
top-quartile structural vote, and a length-, sentence-, and topic-matched
zero-marker control. Candidate placement is balanced and hidden. The design
tests whether the transparent ranking enriches for friction; it does not assume
the candidate is worse. At least eight decisive pairs and a 75% candidate share
among decisive choices are required. No-difference responses are retained and
do not count as candidate wins.

The replacement was terminated after three pairs, all no-difference choices.
Their dates were in March, July, and October 2023. The reader correctly noted
that the transition corpus generally lacks the stronger post-2025-07 AI-style
friction of interest. These responses do not evaluate the ranking, because the
target population is wrong. That handoff has no post documents, and only one of
the tracked pilot's 10 post documents remains fully unexposed. No further
reader screen should use those sources. A new 50-document post-period pool has
now passed the frozen
[Fresh Post-Period Reader Corpus Handoff](../experiments/post-reader-corpus-handoff.md)
gate with zero errors. It enables a new development screen but contains no new
reader outcome, so the smell's evidence status does not change.

A 12-pair post-only screen is now frozen before outcomes. It balances InfoQ and
Meituan six-to-six, uses only documents published on or after 2025-07-01, and
compares a marker-plus-structure candidate with a locally matched zero-marker
control from the same document. See
[Fresh Post-Only Reader-Friction Discrimination Screen](../experiments/reader-friction-screen-v3.md).
The reader stopped after six pairs: four no-difference choices, two control-
more-discouraging choices, and zero candidate-more-discouraging choices. One
comment said both passages had obvious AI-style smell. Same-document matching
over-controlled stylistic variation, so the ranking is not evaluated and the
evidence status does not change. A future raw comparison would need different
documents matched on source, topic, format, length, and visibility, but would
still confound content interest with style.

Rather than replacing that design with unrelated raw passages, the fourth
development intervention now compares each selected post-period passage with a
conservative revision of the same content. It uses 10 new documents, balances
InfoQ and Meituan five-to-five, retains 30 proposition-support checks and exact
numeric preservation, and reduces frozen target markers from 16 to three. See
[Fresh Post-Only Conservative Reframing Intervention](../experiments/refinement-pairs-v4.md).

The fourth intervention produced five revised preferences, four original
preferences, and one no-difference answer. All nine decisive responses selected
display side B even though original placement was balanced five-to-five. The
result is position-confounded, does not validate the operator, and does not
change this smell's evidence status. The reader's round-level observation
instead motivates the compositional-integration watchlist entry below.

Reproduce the frozen batch with:

~~~powershell
python experiments/prepare_refinement_pairs_v2.py `
  --corpus-root data/pilot/monthly `
  --output-dir feature_runs/refinement-pairs-v2 `
  --seed 20260821
~~~

The protocol, exclusions, and limitations are documented in
[Second-Round Conservative Contrast Intervention](../experiments/refinement-pairs-v2.md).
The candidate-selection boundary is documented in
[Raw-Passage Reader-Friction Development Screen](../experiments/reader-friction-screen-v1.md).
The replacement enrichment test is documented in
[Within-Document Friction Enrichment Development Screen](../experiments/reader-friction-screen-v2.md).

### Promotion condition

Promote only if:

- a preregistered detector replicates in the larger matched corpus;
- human review separates necessary from ornamental contrasts reliably;
- reducing ornamental frames improves blinded reader preference;
- the intervention does not erase real logical distinctions or author voice.

---

## SMELL-003: Low-information expansion and broken proposition chain

### Status

- Reader reported
- Hypothesis
- Partially supported by pilot examples
- Not systematically quantified
- Not intervention validated

### Reader experience

The passage appears long and structured, but the reader receives little new
information. Several sentences rename, reframe, announce, or metaphorically
repeat the same idea. Abstract placeholders delay the concrete payload, and
logical connectives imply a relationship that the surrounding propositions do
not make explicit.

The result is not simple word repetition. It is a poor information-to-reading-
effort ratio and a proposition chain that repeatedly loses or postpones its
mainline.

### Source example

Document:

~~~text
data/pilot/monthly/2026-06/3c60dc0a981b686870095450.txt
~~~

Relevant lines: 36–42.

Observed subtypes:

1. **Restatement without payload**
   - “阿里云这次要做的，正是围绕 Agent 重新整理云开放平台的底层链路。”
   - “更准确地说，它是在给 Agent 操作云资源加上一套工程化的‘安全带’。”
   - The second sentence announces greater precision but replaces an abstract
     claim with a metaphor rather than adding a concrete mechanism.
2. **Parallel restatement**
   - “Agent 可以自动化，但不能无边界地自动化；Agent 可以自主执行，但必须被……约束住。”
   - Two balanced clauses carry substantially overlapping propositions.
3. **Abstract payload delay**
   - “这套体系可以拆成三层。每一层，处理的都是一种不确定性。”
   - The prose announces structure and an abstract category before delivering
     the first concrete layer.
4. **Weak discourse bridge**
   - The behavior comparison is followed by “因此，Gateway 不能只被看作普通的流量入口。”
   - The connective announces a conclusion, but the concrete mechanism and
     responsibilities arrive only afterward.
5. **Subject-predicate interruption**
   - “每一层，处理的都是一种不确定性。”
   - The comma separates a short subject from its predicate without a clear
     information-structural need.

These are reader observations to be encoded and tested, not final grammatical
or semantic judgments.

### Human proposition annotation protocol v1

An atomic proposition is the smallest clause-level unit that can be evaluated
as true or false while retaining its necessary arguments and modality.

For each proposition, record one label:

| Label | Definition |
|---|---|
| NEW | Adds a concrete actor, action, mechanism, constraint, relation, quantity, or consequence |
| RESTATEMENT | Rephrases a proposition already present in the preceding context |
| META | Announces structure, importance, precision, or interpretation without adding the announced payload |
| PLACEHOLDER | Uses an abstract reference whose concrete content is delivered later or remains unclear |
| UNSUPPORTED_LINK | Uses a causal, contrastive, or clarifying relation without an explicit local bridge |

Annotators also mark the character span supporting each label. A proposition
may have NEW content plus a separate META span, but it cannot be both NEW and
RESTATEMENT as a whole.

Use two independent annotators for calibration. Resolve disagreements only
after calculating raw agreement and Cohen's kappa.

### Core metrics

#### New proposition density v1

~~~text
new_proposition_density =
    NEW propositions / non-whitespace Chinese characters * 100
~~~

Low values indicate that reading length grows faster than concrete
propositional content.

#### Restatement proposition ratio v1

~~~text
restatement_proposition_ratio =
    RESTATEMENT propositions / all propositions
~~~

#### Framing overhead v1

~~~text
framing_overhead =
    characters inside META or PLACEHOLDER spans
    / non-whitespace Chinese characters
~~~

#### Unsupported discourse-link rate v1

~~~text
unsupported_discourse_link_rate =
    UNSUPPORTED_LINK instances
    / explicit causal, contrastive, and clarification connectives
~~~

#### Payload delay v1

For announcements such as “three layers,” “the following aspects,” or “one
kind of uncertainty”:

~~~text
payload_delay =
    syntactic tokens from the abstract announcement
    to the first concrete named item or mechanism
~~~

Report the mean, 90th percentile, and maximum per document.

#### Abstract shell density v1

Maintain a versioned shell-noun lexicon including context-dependent uses of:

~~~text
问题, 体系, 链路, 逻辑, 判断, 层面, 维度, 能力, 方式, 模式,
价值, 意义, 不确定性, 底层, 框架
~~~

~~~text
abstract_shell_density =
    shell-noun mentions / content-word tokens * 100
~~~

The lexicon count is a weak signal. A shell noun is not a smell when its
concrete content is immediately supplied.

#### Sentence information novelty v1

Use a traditional, reproducible approximation:

1. extract content lemmas and dependency subject-predicate-object tuples;
2. calculate corpus-frozen IDF weights;
3. compare the current sentence with the preceding three sentences;
4. count content units not already present or matched through a frozen synonym
   lexicon.

~~~text
sentence_information_novelty =
    IDF weight of new content units
    / IDF weight of all current-sentence content units
~~~

Static TF-IDF and dependency tuples will miss metaphorical restatement, such as
“reorganize the chain” versus “add a safety belt.” Human annotation remains the
gold standard for calibration.

#### Subject-predicate comma rate v1

Using the fixed dependency parse:

~~~text
subject_predicate_comma_rate =
    clauses with punctuation between a short nominal subject
    and its governing predicate
    / finite clauses
~~~

Report short-subject thresholds separately. Do not treat topic-comment
constructions or long subjects as automatic errors.

### Automated candidate ranking

Do not decide this smell with one regular expression. Rank paragraphs using a
small transparent model whose inputs are:

- proposition novelty approximation;
- adjacent-sentence TF-IDF similarity;
- repeated dependency tuples;
- framing-marker and abstract-shell density;
- payload delay;
- explicit-connective bridge overlap;
- subject-predicate comma events;
- entity and noun-chain continuity;
- paragraph length and sentence count as controls.

Train Logistic Regression or a shallow tree model only after human labels
exist. The target is paragraph-level smell localization, not human-versus-AI
classification.

### Reproduction and calibration set

Initial calibration:

- source: the current 20 InfoQ documents;
- sample 50 paragraphs across both periods without displaying cohort;
- include the 20 highest automatic candidates and 30 random paragraphs;
- annotate proposition labels and an overall “low information / broken chain”
  judgment;
- report precision on ranked candidates and agreement between annotators.

Freeze:

- sentence splitter;
- Stanza model fingerprint;
- shell-noun and connective lexicons;
- synonym resource;
- TF-IDF vocabulary and IDF values;
- context window;
- all thresholds.

### Known confounders

- introductions and summaries legitimately contain restatement;
- tutorials may announce structure before delivering it;
- technical definitions require abstract shell nouns;
- rhetorical parallelism can be intentional and effective;
- topic shifts can lower lexical overlap while adding real information;
- metaphors defeat lexical similarity metrics;
- parser errors affect proposition tuples and subject-predicate detection;
- excerpts can appear contextless when surrounding sections are omitted.

### Minimum intervention experiment

Select 20 paragraphs with high human-confirmed framing overhead.

Produce a conservative version that:

- removes META and RESTATEMENT spans;
- replaces PLACEHOLDER spans with their concrete payload when already present;
- moves delayed mechanisms next to their claim;
- removes unsupported connectives rather than inventing a missing premise;
- preserves all NEW propositions, entities, numbers, negation, and modality.

Compare unchanged and compressed versions blindly. Ask:

1. Which is easier to follow?
2. Which delivers more useful information for the reading effort?
3. Did the edit remove any necessary reasoning or context?

### Promotion condition

Promote to “intervention validated” only if:

- two annotators can apply the proposition labels with acceptable agreement;
- ranked paragraphs have substantially higher smell prevalence than random
  paragraphs;
- conservative removal improves blinded reader preference;
- factual and logical content is preserved;
- the result replicates across more than one genre.

---

## Watchlist: not yet cataloged as smells

### Deterministic discourse-graph probe

The first graph representation treats sentences, dependency-derived
propositions, entities, and abstract shell concepts as nodes. It links them
through argument roles, entity carryover, and adjacent discourse bridges.

The pilot supports weak but directionally consistent signals for lower
adjacent-bridge strength and more mainline detours in post-period and disliked
passages. Formulaic contrast frames remain the strongest interpretable feature
that aligns the time comparison with post-period reader friction. Exact
predicate-signature repetition failed as a semantic-restatement measure and
must not be promoted.

Implementation and results are recorded in
[Deterministic Discourse Graph Probe](../experiments/discourse-graph-probe.md).

The follow-up typed relation-support probe correctly localized one
reader-reported misuse of `相反`, but it also mislabeled a real temporal contrast
and a real monitoring alternative. Lexical overlap and dependency roles cannot
establish contradiction, alternative choice, causality, or rhetorical
necessity. Its aggregate problem score is rejected; only the inspectable
instances and reason codes remain useful for audit. See
[Deterministic Discourse-Relation Support Probe](../experiments/relation-support-probe.md).

| Candidate | Pilot observation | Current decision |
|---|---|---|
| Lower adjacent-sentence content overlap | Hedges' g approximately -0.98, BH q approximately 0.52 | Investigate local cohesion after topic and length control |
| Shorter paragraphs and fewer clause relations | Effects approximately -0.8, BH q approximately 0.52 | Treat as possible formatting effect |
| Generic repetition | No feature with absolute g at least 0.8 | Deprioritize current metrics; semantic restatement needs a new definition |
| Broad discourse-marker categories | No reliable dense separation | Replace broad categories with specific constructions |
| Typed discourse-relation support | Problem-density time effect 0.04 and reader rho 0.06; clear false positives | Reject v0.1 score; retain instance audit only |
| Transition quote and dash growth | Source-consistent rhos 0.286 and 0.250, but BH q values 0.286 and 0.336 | Retain for discovery; require post matching and interventions |
| Pure syntax classification | Unstable and below chance after punctuation removal | Deprioritize as a standalone direction |
| Compositional integration burden | Position controls pass, but generic decompression splits 3 revised to 3 original preferences | Reject broad operator; investigate delayed heads and low-anchor modifier stacks |

Watchlist entries require stronger evidence or better measurement before they
receive a smell ID.

### Compositional integration burden

#### Status

- Reader reported
- Hypothesis
- Deterministically measured on one post-outcome development batch
- Pre-outcome boundary-competition experiment protocol frozen
- Character-to-word boundary selector rejected at Stage 0
- Word-level bracketing selector rejected at Stage 0
- No unconfounded reader association
- Not intervention validated

#### Reader experience

Each word or technical term is understandable in isolation, but too many
relations, modifiers, entities, and propositions appear to be packed into one
integration unit. The reader can decode the vocabulary yet struggles to build
a stable statement from it. This was experienced as difficulty rather than as
an obvious formulaic AI-style marker.

This candidate differs from low-information expansion: it may contain ample
real information. The suspected problem is how that information is packaged,
not simply how little payload the passage contains.

#### Current measurement

The exploratory vector includes content tokens and distinct content lemmas per
sentence, content tokens per clause head, function-to-content ratio, overt-
argument coverage, dependency distances, nominal-modifier spans, tree depth,
and subordinate or coordinate relations. No single score is defined.

On the fourth intervention's revisions, function-to-content ratio fell in all
10 pairs and content tokens per clause head rose in six. However, mean tree
depth fell in eight and long-dependency ratio fell in nine. The vector is mixed
and does not explain the universal side-B answers. Feature-preference tuning on
these outcomes is prohibited.

The proposition-decompression intervention preserved content and bounded
length. Its identical-text and mirrored controls both passed, but the six
interventions split three revised preferences to three original preferences.
Generic decompression is therefore not promoted.

One preferred revision still contained `AI 原生时代全新的算力服务需求`.
The reader identified two separable problems: the head noun `需求` arrives only
after a long modifier string, and generic era or novelty modifiers do not state
what makes the requirement new. A deterministic lexical probe finds 21 broad
delayed-head instances in 10 of the 50 post documents, but manual audit exposes
phrase-boundary false positives. Only the exact reader-localized passage meets
the stricter low-anchor abstract-stack rule. This localizes a hypothesis but
does not replicate it. The same frozen rule found zero strict instances in the
separate 119-document pre/transition discovery handoff. That zero is retained
but cannot estimate a time effect because the rule was defined after the post
example and the corpora are not matched.

The corpus was subsequently expanded to 97 unexposed post documents from five
sources and partitioned before new paragraph analysis. Scanning only the 67
development documents found 23 broad delayed-head candidates across 14
documents and again found zero strict low-anchor abstract stacks. The
30-document validation reserve was not read. The strict motif therefore has two
independent non-replications and remains a single-case observation.

A separately frozen five-motif inventory reached the same boundary. It found
zero strict delayed-head cases. Four dense-clause surface candidates in four
documents and four emphatic abstract-payload candidates in three documents did
not reach the minimum six-document gate. A three-shell lexical cluster did pass
the frequency gate, with 14 instances in 12 documents across four sources, but
inspection of every instance showed literal technical senses, repeated terms,
and list fragments rather than one coherent integration problem. The lexical
cluster is rejected as an intervention selector in version 0.1.

Complete negative contrast frames were common in the same inventory, but their
source-stratified audit mixed necessary alternatives and mechanism distinctions
with possible rhetorical framing. This confirms that marker frequency cannot
stand in for a compositional-burden or ornamental-use judgment.

The frozen inventory was then replicated without threshold changes on a new
93-document, three-source post discovery handoff. It again found zero strict
delayed-head cases. Dense-clause and emphatic abstract-payload rules found only
two documents each. The shell cluster again passed frequency, with 20 instances
in 13 documents across three sources, but again consisted of repeated category
labels, literal technical senses, coordinate lists, and polysemous terms. This
independent discovery result strengthens rejection of the shell-cluster proxy
and leaves the reader-localized delayed-head construction unreplicated.

A follow-up Stanza probe removed the lexical cue and head lists and instead
required a long pre-head nominal span with at least three nominal-modifier
relations and no overt boundary, punctuation, or pre-head verb. It localized
the reader example and found 87 instances in 41 documents across five sources.
Frequency therefore passed, but candidate coherence failed. The instances mix
formal names, quantified specifications, lexicalized technical compounds,
ordinary modifiers, and parser category errors. An unanchored, depth-at-least-
two diagnostic retained 13 instances in seven documents, with six from one
document and no single edit operation covering the remainder. Reject the v0.2
UD rule as an intervention selector; do not convert frequency passage into a
smell promotion.

Protocol `boundary-competition-development-1.0` now freezes the next attempt
before a new lexical measurement or reader outcome exists. It separates
segmentation-path entropy, best-versus-second path margin, gap-level boundary
posteriors, and unresolved distance to the head from diagnostic branching
entropy, accessor variety, tokenizer disagreement, and anchor variables. It
requires eight high-competition and eight matched low-competition passages
from distinct post-period documents before any reader project can be created.
Every passage receives the same boundary-only unpacking operator, so the
high-minus-low preference contrast tests whether the measurement selects
responsive cases rather than whether rewriting in general helps. The 30-
document validation reserve remains unopened. This protocol is a planned test,
not new evidence and not a smell promotion.

The frozen Stage 0 run then rejected the selector before any edit was prepared.
Across all 87 structural candidates, zero met the high-competition gate, 36
instances in 23 documents met the low gate, and 51 were middle or unscored.
Seven candidates jointly met the high-entropy and low-margin thresholds, but
only one had two ambiguous character gaps and none sustained a low-confidence
boundary for the required six characters before the head. The observed maximum
was four.

The reader example was not a lexical boundary case under this measurement: it
had no ambiguous gap and an unresolved distance of two. SUBTLEX produced the
best path `原生 / 时代 / 全新 / 算 / 力 / 服务`, revealing that its subtitle-era
lexicon also lacks the modern technical unit `算力`. Do not repair that result
with a phrase-specific dictionary entry. Reject `boundary_competition_v1` and
move the hypothesis from character-to-word segmentation toward word-level
modifier attachment or phrase bracketing. That replacement is not yet a smell
metric and requires a separately frozen protocol.

The separately frozen word-level probe then enumerated right-headed binary
trees and used leave-one-document-out ordered-pair probabilities to score
attachments. It processed 1,393 passages and 5,670 sentences without opening
the validation reserve. The reader example passed its case-level gate, with
normalized tree entropy 0.822, zero best-second margin, 0.857 familiar-token
fraction, and four weak attachments.

The result did not generalize within the development pool. Only 34 of 87
candidates contained the prespecified content POS throughout. Seven passed the
entropy gate, 26 passed the margin gate, 17 passed familiarity, and five passed
entropy plus margin; none passed entropy, margin, and familiarity together.
The joint entropy-margin cases were names or sparse technical strings. Reject
the tree-entropy vector as a selector and retain H-BRACKET only as a localized
candidate explanation.

Hidden semantic-relation underdetermination is now the stronger rival: familiar
words may be individually recognizable while their relation remains unstated.
This is not yet a metric or established smell. The exposed 87 candidates must
not be re-filtered to construct it; a frozen weak-relation rule needs a new
independent corpus. See
[Word-Level Modifier-Bracketing Probe](../experiments/modifier-bracketing-probe.md).

No further reader batch should be assembled from the five remaining broad
candidates: they are all from Meituan and mostly technical or section-heading
fragments. Independent multi-source examples are required before freezing a
narrow `unpack_delayed_head` intervention. See
[Compositional Integration Burden Probe](../experiments/compositional-burden-probe.md)
and
[Head-Final Modifier Delay Probe](../experiments/head-final-modifier-probe.md).
The staged design is documented in
[Boundary-Competition Development Experiment](../experiments/boundary-competition-development.md).
