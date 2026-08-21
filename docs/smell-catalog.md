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

Reproduce the frozen batch with:

~~~powershell
python experiments/prepare_refinement_pairs_v2.py `
  --corpus-root data/pilot/monthly `
  --output-dir feature_runs/refinement-pairs-v2 `
  --seed 20260821
~~~

The protocol, exclusions, and limitations are documented in
[Second-Round Conservative Contrast Intervention](../experiments/refinement-pairs-v2.md).

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

| Candidate | Pilot observation | Current decision |
|---|---|---|
| Lower adjacent-sentence content overlap | Hedges' g approximately -0.98, BH q approximately 0.52 | Investigate local cohesion after topic and length control |
| Shorter paragraphs and fewer clause relations | Effects approximately -0.8, BH q approximately 0.52 | Treat as possible formatting effect |
| Generic repetition | No feature with absolute g at least 0.8 | Deprioritize current metrics; semantic restatement needs a new definition |
| Broad discourse-marker categories | No reliable dense separation | Replace broad categories with specific constructions |
| Pure syntax classification | Unstable and below chance after punctuation removal | Deprioritize as a standalone direction |

Watchlist entries require stronger evidence or better measurement before they
receive a smell ID.
