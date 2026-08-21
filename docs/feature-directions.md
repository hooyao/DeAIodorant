# Feature Exploration Directions

The current deliverable is a reproducible feature matrix, not a classifier or a
statistical conclusion. This document separates implemented dense features from
additional feature spaces worth extracting after the prepared corpus is
available.

## Direction A: Dense interpretable features

Status: implemented in feature schema 1.0.

This is the first matrix to produce because every column has a stable linguistic
interpretation:

- character composition and entropy;
- paragraph and sentence rhythm;
- punctuation;
- repetition and compression;
- title form;
- discourse and epistemic markers;
- token diversity and function-word use;
- Universal POS distributions;
- dependency-tree depth, distance, branching, direction, and non-projectivity;
- clause, coordination, modification, and passive structures;
- adjacent-sentence lexical cohesion.

These features are compact enough to inspect one column at a time.

## Direction B: Sparse stylometric patterns

Status: implemented in feature schema 1.0; the actual vocabulary is selected
after corpus arrival.

Extract count and normalized-rate matrices for:

- CJK character 2-grams through 5-grams;
- function-word 1-grams through 3-grams;
- POS 2-grams through 5-grams;
- punctuation sequences;
- sentence- and paragraph-opening character sequences;
- dependency treelets shaped as head POS, relation, and dependent POS;
- two-edge dependency-relation paths.

These features can discover formulaic patterns that a hand-built inventory
misses. They must be kept separate from topic-heavy content-word n-grams.
Vocabulary pruning uses combined-corpus document frequency without consulting
cohort labels. The selected vocabulary and every raw pattern are stored in a
separate catalog and must be frozen before a held-out comparison.

## Direction C: Constituency grammar

Status: planned.

A fixed Chinese constituency parser can provide:

- phrase-structure tree depth;
- mean and maximum branching;
- NP, VP, IP, CP, and subordinate-clause counts per sentence;
- noun-phrase to verb-phrase ratio;
- unary-chain rate;
- grammar-production entropy;
- normalized counts of common context-free grammar productions;
- repeated constituency-subtree signatures.

This direction is complementary to Universal Dependencies. It adds another
parser model and model-specific tag set, so its output must have a separate
manifest and sensitivity analysis.

## Direction D: Local cohesion without embeddings

Status: partially implemented.

The dense matrix already includes adjacent-sentence content-word and noun
Jaccard overlap. Further deterministic features can include:

- noun and named-entity carryover across adjacent sentences;
- pronoun-to-antecedent distance approximations;
- lexical-chain length;
- entity-grid transition counts;
- paragraph-to-paragraph content-word overlap;
- connective presence at discourse boundaries.

NER or coreference models would add measurement error. A first pass should use
fixed POS-based noun chains before adding another learned model.

## Direction E: Information concentration

Status: partially implemented.

Current features include character entropy, token entropy, MATTR, hapax ratio,
and compression ratio. Corpus-dependent additions can include:

- TF-IDF concentration and Gini coefficient within each document;
- share of tokens accounted for by the ten most frequent content words;
- within-document keyword burstiness;
- content-word entropy by paragraph;
- vocabulary overlap between title, opening paragraph, and conclusion.

IDF values must be fit once on the combined exploratory corpus and stored as an
artifact. Otherwise the same document can receive different values in
different runs.

## Direction F: Topic and genre diagnostics

Status: planned as control metadata, not style features.

Classical LDA or non-negative matrix factorization can quantify topic mixture.
The resulting components should be used to diagnose or control topic imbalance,
not presented as evidence of AI writing. Required outputs are:

- topic-mixture proportions per document;
- topic entropy;
- dominant-topic share;
- source, format, and topic cross-tabulations.

The vectorizer vocabulary, random seed, component count, and fitted model must
be frozen and hashed.

## Direction G: Temporal features

Status: deferred until monthly coverage is adequate.

After document features exist, aggregate each feature by publication month and
source. Useful quantities include:

- monthly median and interquartile range;
- within-source month-to-month change;
- robust trend slope;
- classical change-point candidates;
- cross-source direction agreement.

These are derived time-series features. They do not belong in the first
document matrix.

## Direction H: Readability formulas

Status: deliberately deferred.

Many Chinese readability formulas depend on school-level vocabulary lists,
sentence segmentation conventions, or features designed for educational text.
They should be added only when their lexical resources, licensing, domain fit,
and exact formula are documented. A single opaque readability score would hide
more information than the current sentence, token, and syntax measurements.

## Excluded directions

The current project excludes:

- LLM judgments or LLM-generated labels;
- commercial AI-detector scores;
- opaque text embeddings;
- generative-model perplexity as a primary feature;
- prompt-dependent semantic or style scoring.

These violate the requirement that feature values be inexpensive, inspectable,
and repeatable.
