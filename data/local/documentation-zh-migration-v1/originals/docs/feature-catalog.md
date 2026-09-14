# Quantifiable Chinese Text Feature Catalog

## Scope

The current task is feature extraction. Given a prepared pre-2023 corpus and a
prepared post-2025-06 corpus, the pipeline emits one numeric row per document.
It does not select corpus documents, test statistical significance, train a
classifier, detect AI authorship, or interpret differences.

All features are deterministic. They use direct text statistics or a fixed
Stanza Universal Dependencies parse. No LLM, embedding model, prompt, or
generative judgment is used.

## Output unit

The document is the feature unit. Each row starts with non-feature identifiers:

| Column | Meaning |
|---|---|
| doc_id | Stable corpus document ID |
| cohort | Date-derived pre or post cohort |
| source | Publishing source |
| published_at | ISO publication date |
| published_month | Calendar month |
| topic | Prepared-corpus topic label, or a missing-value marker |
| format | Prepared-corpus format label, or a missing-value marker |

All remaining columns are numeric features. Raw text and raw titles are not
copied into the matrix.

## Shared definitions

- **CJK character**: a character in Unicode ranges U+3400–U+4DBF or
  U+4E00–U+9FFF.
- **Ratio**: numerator divided by the explicitly stated denominator.
- **Density**: occurrences divided by non-whitespace character count unless the
  feature name specifies another denominator.
- **Entropy**: Shannon entropy in bits, negative sum of
  **p(x) * log2(p(x))**.
- **Coefficient of variation (CV)**: population standard deviation divided by
  arithmetic mean. It is zero when the mean is zero.
- **MATTR**: mean type-token ratio over all overlapping fixed-size windows. If
  the document is shorter than the configured window, ordinary type-token
  ratio is used.

## Character composition

| Feature group | Quantities |
|---|---|
| Length | total characters, non-whitespace characters, CJK characters |
| Script composition | CJK ratio, ASCII-letter ratio, digit ratio |
| Character diversity | CJK entropy, CJK type-token ratio, 500-character MATTR |
| Compressibility | zlib level-9 compressed bytes divided by original UTF-8 bytes |
| External references | detected URL count per 1,000 CJK characters |

Raw length counts are useful for matching and diagnostics. They should not be
treated as style differences unless the cohorts have been length matched.

## Document structure and rhythm

Paragraphs are non-empty normalized lines. Sentences are split after Chinese or
ASCII full stops, question marks, and exclamation marks.

| Feature | Formula |
|---|---|
| Mean paragraph length | Mean CJK characters per paragraph |
| Paragraph-length CV | CV of paragraph CJK-character counts |
| Short-paragraph ratio | Paragraphs with 1–19 CJK characters divided by paragraphs |
| Long-paragraph ratio | Paragraphs with more than 200 CJK characters divided by paragraphs |
| Mean sentence length | Mean CJK characters per sentence |
| Sentence-length CV | CV of sentence CJK-character counts |
| Sentence-length autocorrelation | Pearson correlation of adjacent sentence-length sequences |
| Adjacent sentence-length change | Mean absolute adjacent length change divided by mean length |
| Mean sentences per paragraph | Mean detected sentence count in each paragraph |
| List-item ratio | Paragraphs beginning with bullets or ordinal markers divided by paragraphs |
| Question-sentence ratio | Sentences ending in a question mark divided by sentences |
| Exclamatory-sentence ratio | Sentences ending in an exclamation mark divided by sentences |

These features quantify structural uniformity without assigning a positive or
negative interpretation.

## Repetition and regularity

| Feature | Formula |
|---|---|
| Repeated character n-gram ratio | Repeated occurrences among all configured CJK n-grams |
| Sentence-opening repetition | Duplicate first four-CJK-character sequences divided by eligible sentences |
| Paragraph-opening repetition | Duplicate first four-CJK-character sequences divided by eligible paragraphs |
| Exact sentence repetition | Duplicate whitespace-normalized sentences divided by sentences |
| Exact paragraph repetition | Duplicate whitespace-normalized paragraphs divided by paragraphs |
| Compression ratio | Deterministic compressed size divided by source byte size |

The character n-gram size is stored in the feature configuration. Repetition
features are sensitive to boilerplate, quotations, and document genre.

## Punctuation

The matrix includes total punctuation density, punctuation entropy, and
separate densities for:

- commas and enumeration commas;
- full stops, question marks, and exclamation marks;
- colons;
- semicolons;
- dashes and hyphens;
- quotation marks;
- parentheses and brackets.

Punctuation style is source- and editor-sensitive, so source remains an
identifier column for later stratification.

## Title form

Title features include:

- CJK-character count;
- ASCII-letter ratio;
- presence of digits, a colon, a question mark, an exclamation mark, or
  quotation marks;
- proportion of distinct title CJK characters also appearing in the body.

The raw title is read from metadata but is not written to the feature matrix.

## Discourse and epistemic markers

Fixed phrase lists quantify rates per 10,000 CJK characters for:

- causal transitions;
- contrastive transitions;
- enumeration;
- framing phrases;
- metadiscourse;
- summary phrases;
- epistemic boosters;
- epistemic hedges;
- directives.

The matrix also records total discourse-marker rate and marker-type coverage.
The exact Chinese phrases are versioned in
**src/deaiodorant/analysis/surface.py**. These are lexicon measurements, not
semantic judgments. They are sensitive to topic and genre.

## Token and lexical features

Stanza tokenization, lemmatization, and Universal POS tags provide:

| Feature | Formula |
|---|---|
| Lexical token count | Tokens excluding PUNCT and SYM |
| Token type-token ratio | Distinct case-folded token forms divided by lexical tokens |
| Token MATTR | Mean 100-token window type-token ratio |
| Hapax ratio | Token types occurring once divided by lexical tokens |
| Token entropy | Shannon entropy of lexical token forms |
| Mean token length | Mean CJK characters per lexical token |
| Token-length CV | CV of lexical-token CJK lengths |
| Content-word ratio | ADJ, ADV, NOUN, PROPN, and VERB tokens divided by lexical tokens |
| Function-word ratio | ADP, AUX, CCONJ, DET, PART, PRON, and SCONJ tokens divided by lexical tokens |
| First-person pronoun ratio | Fixed first-person forms divided by lexical tokens |
| Second-person pronoun ratio | Fixed second-person forms divided by lexical tokens |

Token features are parser- and segmentation-dependent. Both cohorts must use
the identical model files.

## Local lexical cohesion

For each pair of adjacent parsed sentences, the extractor calculates Jaccard
overlap for:

- lemmatized content words tagged ADJ, ADV, NOUN, PROPN, or VERB;
- lemmatized nouns tagged NOUN or PROPN.

The document feature is the mean adjacent-sentence overlap. This is a
transparent local-cohesion approximation and does not require embeddings or a
coreference model.

## Universal POS distribution

For every Universal POS tag, the matrix contains:

**tokens with that tag / all parsed tokens**

The tags are ADJ, ADP, ADV, AUX, CCONJ, DET, INTJ, NOUN, NUM, PART, PRON,
PROPN, PUNCT, SCONJ, SYM, VERB, and X.

POS bigram and trigram entropy measure the diversity of local grammatical
sequences without retaining the sequences themselves.

## Dependency-tree complexity

| Feature | Formula |
|---|---|
| Dependency distance | Absolute token-position distance between dependent and head |
| Mean, median, maximum dependency distance | Document aggregates over non-root arcs |
| Dependency-distance CV | CV over non-root dependency distances |
| Left-dependent ratio | Dependents to the left of their head divided by non-root arcs |
| Mean and maximum tree depth | Root-to-token edge counts |
| Mean and maximum non-leaf branching | Child count among tokens with at least one child |
| Root relative position | Root token index divided by sentence token count, averaged by document |
| Crossing-arc ratio | Crossing arc pairs divided by all non-root arc pairs, averaged by sentence |
| Dependency-relation entropy | Entropy of base Universal Dependencies relations |
| Treelet entropy | Entropy of head-POS, relation, dependent-POS triples |

## Clause and modification structure

| Feature | Formula |
|---|---|
| Subordinate-relation ratio | acl, advcl, ccomp, csubj, and xcomp arcs divided by tokens |
| Clause relations per sentence | Same relation count divided by parsed sentences |
| Coordinate-relation ratio | cc and conj arcs divided by tokens |
| Nominal-modifier ratio | acl, amod, compound, and nmod arcs divided by tokens |
| Passive-relation ratio | Dependency subtypes containing pass divided by tokens |

The matrix additionally includes one proportion for every base Universal
Dependencies relation. This preserves detail for later exploration without
requiring a new parse.

## Sparse stylometric features

In addition to the 150-column dense matrix, schema 1.0 can emit sparse pattern
features for:

- CJK character 2-grams, 3-grams, and 4-grams;
- POS 2-grams, 3-grams, and 4-grams;
- function-word forms;
- content lemmas, explicitly marked as topic-sensitive;
- sentence-opening CJK sequences;
- punctuation runs;
- root POS values;
- dependency treelets shaped as head POS, relation, and dependent POS;
- two-edge dependency-relation paths.

Vocabulary selection pools both cohorts and uses only combined document
frequency and combined total count. It never consults the cohort label. Each
selected pattern receives a deterministic feature ID. Non-zero values contain
both raw count and count per 1,000 opportunities in that feature family.

The vocabulary limits and minimum document frequency are stored in
**configs/features.v1.json**. Sparse features are exploratory: topic-sensitive
families must not be interpreted as writing style without topic control.

## Parser and reproducibility contract

The syntax layer uses:

~~~text
Stanza 1.14.0
language: zh-hans
package: gsdsimp
processors: tokenize,pos,lemma,depparse
~~~

Stanza is a learned NLP parser, not an LLM. Annotation output is frozen as
CoNLL-U before feature extraction. The annotation manifest records exact
package versions, model-file fingerprint, device, seed, corpus fingerprint, and
every CoNLL-U file hash.

Stanza is distributed under Apache-2.0. The selected Universal Dependencies
Chinese GSD treebank is distributed under CC BY-SA 4.0. The optional
installation includes PyTorch and several hundred megabytes of model files, so
it is materially larger than the core package. CPU annotation is the default
for reproducibility and can be slow on a large corpus.

Feature extraction never downloads a model implicitly. Missing model files,
incomplete parser output, malformed dependency trees, corpus-fingerprint
mismatches, and annotation-hash changes stop the command instead of silently
substituting data.

Model download is explicit:

~~~powershell
python -m pip install -e ".[syntax]"
deaiodorant-analysis download-syntax-model --model-dir models/stanza
~~~

Extract a feature matrix after the prepared corpus arrives:

~~~powershell
deaiodorant-analysis annotate --corpus data/final/monthly --config configs/features.v1.json --model-dir models/stanza --output feature_runs/annotations-v1 --device cpu

deaiodorant-analysis extract --corpus data/final/monthly --config configs/features.v1.json --annotations feature_runs/annotations-v1 --output feature_runs/matrix-v1
~~~

The output directory contains:

~~~text
document_features.csv
feature_catalog.json
feature_config.json
summary.json
feature_manifest.json
sparse_feature_catalog.json
sparse_feature_values.csv
~~~

The manifest hashes every artifact. An existing output directory is never
overwritten.

## Comparison constraints for later work

Feature extraction does not establish a difference between human and
AI-era writing. Later comparisons must, at minimum:

- match or stratify by source, topic, format, length, and visibility;
- use documents rather than sentences as independent observations;
- separate raw counts from normalized rates;
- report parser sensitivity and missing metadata;
- keep exploratory feature selection separate from held-out confirmation.
