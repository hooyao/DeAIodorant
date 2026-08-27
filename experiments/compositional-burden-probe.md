# Compositional Integration Burden Probe

## Status

This is a post-outcome development probe. It was motivated by a reader report
after the fourth post-only intervention and is neither a frozen validation
analysis nor evidence of authorship.

The reader described a distinct experience: individual words remained
understandable, but the combined technical prose was difficult to assemble,
as though too many words had been twisted into one unit. The difficulty was not
experienced primarily as an obvious formulaic AI-style marker.

## Measurement target

The probe operationalizes *compositional integration burden* as a vector of
transparent syntactic measurements. It deliberately does not construct a
single burden score.

The vector includes:

- CJK characters, clause heads, content tokens, and distinct content lemmas per
  sentence;
- content tokens per clause head;
- function-to-content token ratio;
- immediate overt-argument coverage of clause heads;
- dependency distance, long dependency arcs, and tree depth;
- nominal-modifier span and consecutive nominal-modifier depth;
- subordinate and coordinate relations per sentence.

The two frozen exploratory thresholds are five token positions for a long
dependency arc and four positions for a long nominal modifier. They are
descriptive cutoffs, not product thresholds.

Universal Dependencies parses are deterministic measurements with parser
error. They are not human linguistic gold labels. The reader is not asked to
label any of these features.

## Fourth-intervention diagnostic

The controlled material contains the 10 original/revised pairs from
`post-only-conservative-reframing-development-4.0`. The pairwise outcome cannot
validate a feature: all nine decisive answers selected display side B, while
original placement was balanced five-to-five.

The revision deltas nevertheless expose side effects of the frozen edit
operator:

| Measurement | Revision increased | Revision decreased |
|---|---:|---:|
| Function-to-content ratio | 0 | 10 |
| Content tokens per clause head | 6 | 4 |
| CJK characters per sentence | 3 | 7 |
| Mean tree depth | 2 | 8 |
| Long dependency-arc ratio | 1 | 9 |
| Mean dependency distance | 4 | 6 |

The operator consistently removed function words and often placed more content
under each predicate, which is compatible with compression. At the same time,
most revisions shortened sentences, reduced tree depth, and reduced long
dependencies. The observations therefore do not support collapsing the vector
into a generic sentence-complexity score.

Preference-alignment counts are retained in the generated summary only as a
diagnostic. They must not be used to tune feature thresholds because display
side is completely confounded with the answers.

## Fresh-post discovery scan

The same feature vector was applied to post-period passages whose documents
were not selected for the third reader-friction screen or fourth intervention.
The scan covered 183 eligible passages from 26 documents.

Candidate ranking uses six predeclared signals:

- low overt-argument coverage;
- high content tokens per clause head;
- high distinct content lemmas per sentence;
- low function-to-content ratio;
- high long-dependency-arc ratio;
- high mean nominal-modifier span.

Signals are converted to within-source-and-format percentiles. The scan counts
how many lie in the putative top burden quartile; it does not average them into
a score. Reader outcomes are not inputs.

Question-and-answer fragments, speaker profiles, navigation fragments,
section-heading fragments, and image-generation prompts were excluded during
manual completeness review. Six passages from distinct documents were retained
for a bounded proposition-decompression intervention: three InfoQ and three
Meituan passages, with two each from industry reporting, research summaries,
and technical practice.

## Resulting intervention hypothesis

The next hypothesis is narrower than “make sentences shorter”:

> Distributing an unchanged proposition set across clearer integration units
> can improve willingness to continue reading without deleting information or
> flattening the author's voice.

The edit may split at an existing semantic boundary and repeat an already-fixed
referent. It may not add a premise, causal relation, mechanism, example, or
evidence. It preserves every proposition, entity, number, negation, qualifier,
uncertainty marker, attribution, and technical term. Length is bounded to 95%
through 125% of the source, and sentence count must increase.

Because project 6 produced complete side-B selection, the new intervention
contains one identical-text control and one nonadjacent mirrored pair. Treatment
preference is interpreted only if the identical pair receives a no-difference
answer and the mirrored answers follow content rather than display side.

## Reproduction

~~~powershell
python experiments/compositional_burden_probe.py `
  --answer-key feature_runs/refinement-pairs-v4/answer_key.json `
  --results data/annotations/refinement-pairwise-v4.json `
  --model-dir models/stanza `
  --output-dir feature_runs/compositional-burden-v1 `
  --device cpu `
  --seed 2026082703

python experiments/scan_post_compositional_burden.py `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1 `
  --exclude-answer-key feature_runs/reader-friction-screen-v3/answer_key.json `
  --exclude-answer-key feature_runs/refinement-pairs-v4/answer_key.json `
  --model-dir models/stanza `
  --output-dir feature_runs/compositional-burden-post-scan-v1 `
  --device cpu `
  --seed 2026082704
~~~

The maintainer requested that future model inference, including bulk parser
inference, run on `gx10`. The commands above identify the artifacts and
arguments; they do not prescribe the execution host.

Two repeated paired-probe runs were byte-identical:

| Artifact | SHA-256 |
|---|---|
| Variant features | `2e10a7347e2ed4030366dad1293b35243d5fab740aef1a2a22a615b8bf5eb44a` |
| Pair deltas | `f773c345bf7c4442a906f087674031b24d785c0c2da54f518084ce685fe867ef` |
| Summary | `de9decfda0acca5234beb9bd0b7ce6009e25ea683e93e08a8967680b31a8c373` |

Generated parses, feature matrices, shortlists, source passages, and blinded
answer keys remain under ignored `feature_runs/` or the local handoff. They are
not committed.
