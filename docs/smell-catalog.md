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
- Not reader reported as an independent category
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

### Promotion condition

Promote only if:

- a preregistered detector replicates in the larger matched corpus;
- human review separates necessary from ornamental contrasts reliably;
- reducing ornamental frames improves blinded reader preference;
- the intervention does not erase real logical distinctions or author voice.

---

## Watchlist: not yet cataloged as smells

| Candidate | Pilot observation | Current decision |
|---|---|---|
| Lower adjacent-sentence content overlap | Hedges' g approximately -0.98, BH q approximately 0.52 | Investigate local cohesion after topic and length control |
| Shorter paragraphs and fewer clause relations | Effects approximately -0.8, BH q approximately 0.52 | Treat as possible formatting effect |
| Generic repetition | No feature with absolute g at least 0.8 | Deprioritize current metrics; semantic restatement needs a new definition |
| Broad discourse-marker categories | No reliable dense separation | Replace broad categories with specific constructions |
| Pure syntax classification | Unstable and below chance after punctuation removal | Deprioritize as a standalone direction |

Watchlist entries require stronger evidence or better measurement before they
receive a smell ID.
