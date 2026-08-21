# Pilot Direction Probe

## Purpose

This is a one-off feasibility experiment for finding promising research
directions. It is not a product component, an AI detector, or a confirmatory
study.

The probe asks whether the current small corpus contains reproducible signals
worth investigating before the larger corpus arrives.

## Data

Primary comparison:

- 10 pre-period InfoQ documents;
- 10 post-period InfoQ documents.

Sensitivity checks:

- remove the known translated post document
  **b186cdd4f9004e0413395bf3**, leaving 10 versus 9;
- compare pre-period InfoQ with pre-period Machine Heart to estimate source
  sensitivity.

Known limitations:

- the pilot is not a clean corpus;
- additional unmarked translated or compiled documents may remain;
- publication topic and article format are not matched;
- there are only 20 same-source documents;
- current page selection is not representative of either period.

## Computation

- Stanza 1.14.0 Chinese Universal Dependencies annotation;
- 150 dense document features;
- 6,597 cohort-blind sparse patterns;
- 20,000 GPU label permutations for dense features;
- 5,000 GPU label permutations for sparse patterns;
- leave-one-out direction stability;
- Hedges' g and Cliff's delta;
- known-translation removal;
- source-to-time effect ratio;
- PCA and fold-local feature-selected ridge leave-one-out diagnostics.

Dense and sparse matrix computation ran on an RTX 4090 with PyTorch CUDA. Only
document IDs, numeric features, and extracted short patterns were uploaded to
the cloud instance. Article bodies remained local.

## Dense results

### Strongest result: punctuation system

| Feature | Pre mean | Post mean | Hedges' g | Known-translation-removed g | Permutation p | BH q |
|---|---:|---:|---:|---:|---:|---:|
| Total punctuation density | 0.08 | 0.10 | 2.08 | 2.00 | 0.0002 | 0.030 |
| Punctuation entropy, bits | 2.40 | 3.22 | 1.70 | 1.81 | 0.0018 | 0.090 |
| Dash density | approximately 0.00 | approximately 0.01 | 1.58 | 1.79 | 0.0006 | 0.045 |

All three directions survived leave-one-out removal. Total punctuation density
also had a small pre-period source effect relative to its time effect. Dash and
punctuation-entropy differences had larger source sensitivity but remained
smaller than the InfoQ time effect.

The result is real in this sample, but its interpretation is unresolved. It may
measure:

- formulaic contrast and emphasis;
- quotation and parenthetical asides;
- newer InfoQ formatting and editorial conventions;
- translated or compiled content;
- code, lists, headings, and product walkthrough structure.

The next probe must strip or separately model headings, code, quotations, and
list formatting before treating punctuation as a smell.

### Secondary candidates

| Feature | Pre mean | Post mean | Hedges' g | BH q | Interpretation risk |
|---|---:|---:|---:|---:|---|
| Lexical MATTR | 0.73 | 0.77 | 1.13 | 0.35 | topic and technical vocabulary |
| Adjacent-sentence content Jaccard | 0.07 | 0.05 | -0.98 | 0.52 | topic breadth and article length |
| Long-paragraph ratio | 0.02 | approximately 0.00 | -0.80 | 0.52 | web formatting |
| Mean paragraph CJK characters | 59.72 | 40.33 | -0.81 | 0.52 | editorial layout |
| Clause relations per sentence | 3.49 | 2.76 | -0.81 | 0.52 | parser and genre |

These effects are large enough to retain as hypotheses, but the current sample
does not support a reliable claim after multiple testing.

The higher post-period lexical diversity contradicts a simple “AI text has
lower lexical entropy” hypothesis. That direction should not be adopted without
topic matching.

## Feature-family results

| Family | Median absolute g | Features with absolute g at least 0.8 | BH q below 0.1 |
|---|---:|---:|---:|
| Punctuation | 0.89 | 6 | 3 |
| Character composition | 0.60 | 1 | 0 |
| Discourse and stance | 0.45 | 0 | 0 |
| Document structure | 0.42 | 3 | 0 |
| Dependency syntax | 0.35 | 2 | 0 |
| Title form | 0.33 | 1 | 0 |
| Universal POS | 0.32 | 2 | 0 |
| Token and lexical | 0.31 | 1 | 0 |
| Dependency relation | 0.27 | 3 | 0 |
| Repetition and regularity | 0.14 | 0 | 0 |

The current pilot does not support the initial idea that ordinary repetition
metrics or a generic discourse-marker list are the main direction.

## Sparse patterns

No sparse pattern survived Benjamini-Hochberg correction over 6,597 candidates.
Sparse findings therefore generate hypotheses only.

The most interesting manually consolidated pattern is contrastive reframing:

| Pattern | Pre InfoQ documents | Post InfoQ documents | Pre occurrences | Post occurrences |
|---|---:|---:|---:|---:|
| “不是/并非/不再是 ... 而是 ...” | 0 | 5 | 0 | 24 |
| Same pattern after removing the known translation | 0 | 4 of 9 | 0 | 15 |
| “正是” | 1 | 8 | 1 | 14 |
| “关键” | 2 | 10 | 5 | 35 |
| “系统性” | 0 | 5 | 0 | 6 |
| “缺乏” | 0 | 5 | 0 | 7 |

Representative post-period constructions include repeated sequences shaped as:

- “not X, but Y”;
- “no longer X, but Y”;
- “the key is...”;
- “it is precisely...”;
- “the problem is not..., but...”.

This suggests a candidate direction:

> generated-era prose may overuse contrast and emphasis frames to create a
> sense of argument, even when a direct declarative sentence would carry the
> same information.

This direction is more specific and editable than generic “AI style.” It needs
a preregistered detector and a matched-corpus replication.

## PCA and linear diagnostic

PCA did not reveal a single global cohort axis:

- PC1 explained 26.2% of variance;
- PC1 cohort correlation was only 0.19;
- content, format, and source variation dominate the first component.

Fold-local top-five-feature ridge leave-one-out:

- accuracy: 75%;
- AUC: 0.82;
- label-permutation p varied around 0.06–0.08 across 100-permutation runs;
- permutation mean accuracy: approximately 0.46–0.49.

The features selected in nearly every fold were punctuation density,
punctuation entropy, dash density, punctuation dependency ratio, and title
length. The classifier is therefore mostly a punctuation and editorial-format
diagnostic.

## Feature-family ablation

| Feature subset | Accuracy | AUC | Label-permutation p |
|---|---:|---:|---:|
| All dense features | 0.75 | 0.82 | 0.079 |
| Lexical and character | 0.65 | 0.66 | 0.158 |
| Discourse and repetition | 0.50 | 0.53 | 0.515 |
| Document structure | 0.40 | 0.48 | 0.723 |
| Grammar only | 0.30 | 0.12 | 0.832 |
| Without punctuation or title | 0.20 | 0.03 | 0.921 |

The below-chance results in the last two rows reflect severe fold instability,
not useful reverse classifiers. With only 20 documents, the selected directions
change when one document is held out.

Traditional machine learning is feasible, but it currently confirms only that
the punctuation family contains a sample signal. It does not provide a stable
general “AI smell” representation.

## Direction decisions

### Priority 1: Contrastive and emphatic rhetorical frames

Why:

- concrete span-level patterns;
- large document-presence differences;
- remains after known-translation removal;
- directly testable through minimal edits;
- more interpretable than a classifier.

Next probe:

- freeze a lexicon and syntactic detector before viewing more data;
- count normalized uses per 1,000 sentences;
- distinguish necessary logical contrast from ornamental reframing;
- replicate on the larger matched corpus.

### Priority 1: Punctuation and inserted emphasis

Why:

- strongest dense effect;
- only family surviving dense multiple-testing correction;
- stable under leave-one-out and known-translation removal.

Next probe:

- separate body prose from headings, lists, code, quotations, and transcripts;
- split dash uses into range/hyphen, parenthetical insertion, quotation, and
  emphatic turn;
- rerun within matched article formats;
- test whether punctuation is a symptom of rhetorical templates rather than an
  independent target.

### Priority 2: Local cohesion

Why:

- post-period adjacent content overlap is lower;
- the direction survives leave-one-out and translation removal;
- could measure idea hopping or weak local continuity.

Next probe:

- calculate entity and noun-chain carryover;
- control sentence count, article length, and topic breadth;
- inspect paragraph-boundary versus within-paragraph cohesion separately.

### Priority 2: Clause and paragraph compression

Why:

- shorter paragraphs and fewer clause relations per sentence appear in post
  documents;
- may interact with web formatting and list-heavy writing.

Next probe:

- normalize out headings and bullet lists;
- compare prose-only sentences;
- add constituency production and clause-depth features only if the effect
  remains.

### Deprioritize: Generic repetition metrics

No current repetition or regularity feature had absolute g of at least 0.8.
Do not invest in a large repetition subsystem until a different definition of
semantic restatement is available.

### Deprioritize: Generic transition lexicon

The current causal, contrast, enumeration, summary, framing, hedge, booster, and
directive category totals did not separate the cohorts reliably. Broad category
counts hide the more specific “not X, but Y” construction.

### Deprioritize: General classifier

The small linear model is unstable and driven by editorial punctuation.
Improving its accuracy would move the project toward authorship classification
without identifying editable reader-disliked behavior.

## Feasibility conclusion

The direction-finding workflow is feasible:

- deterministic parsing completed for all 30 documents;
- dense and sparse matrices were produced;
- GPU permutation and linear diagnostics completed in seconds;
- known translation and source sensitivity can be measured explicitly.

The pilot does not support a broad conclusion about AI-generated Chinese text.
It does support two concrete next directions:

1. repeated contrastive/emphatic rhetorical framing;
2. punctuation and inserted emphasis after removing editorial-format effects.

Local cohesion is the strongest secondary direction. Generic repetition,
generic discourse markers, and general classification should not receive more
effort at this stage.
