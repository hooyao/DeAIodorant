# Boundary-Competition Development Experiment

## Status

Protocol `boundary-competition-development-1.0` was frozen on 2026-08-31
before implementing the new lexical measurement, selecting passages, preparing
revisions, or collecting any new reader outcome. Any operational change must
receive a new protocol version before outcomes are exposed.

This is a staged single-reader development experiment. It is not a validation
study, an authorship study, or a pre/post cohort comparison. No Label Studio
project may be created until the measurement and admission gates below pass.

## Research question

The reader localized a construction in which familiar words remain difficult to
integrate because several modifiers precede a late head noun without a reliable
internal boundary. The working example is:

> 这个 AI 算力池面向 AI 原生时代全新算力服务需求

The experiment asks two separate questions:

1. Does a frozen lexical boundary-competition measurement distinguish long
   pre-head strings that respond to structural unpacking from superficially
   similar strings with strong lexical boundaries?
2. For high-competition strings, does a boundary-only unpacking edit improve
   willingness to continue reading while preserving every source claim?

The experiment does not test whether the text was written by AI. It also does
not test deletion or semantic replacement of expressions such as `AI 原生时代`.
That semantic-specificity hypothesis remains orthogonal. A boundary-only edit
may fail because the preserved expression still carries little information;
such a result is informative rather than a reason to broaden the edit after
outcomes are seen.

## Literature-grounded measurement boundary

The measurement follows five findings without treating any of them as direct
evidence for the product smell:

- correct visual word boundaries can facilitate Chinese reading, while
  misleading boundaries can interfere with it (Bai et al., 2008,
  <https://doi.org/10.1037/0096-1523.34.5.1277>);
- overlapping candidate words compete during Chinese word recognition (Ma et
  al., 2014, <https://doi.org/10.1037/a0035389>);
- readers use statistical evidence that a character is a single-character word
  or the beginning of a multi-character word (Zang et al., 2015,
  <https://doi.org/10.1080/17470218.2015.1061030>);
- accessor variety and branching entropy provide deterministic boundary
  evidence (Feng et al., 2004, <https://doi.org/10.1162/089120104773633394>;
  Jin and Tanaka-Ishii, 2006, <https://doi.org/10.3115/1273073.1273129>);
- segmentation standards disagree and can change downstream dependency
  structure, so tokenizer agreement is diagnostic rather than truth
  (RethinkCWS, <https://doi.org/10.18653/v1/2020.emnlp-main.457>).

SUBTLEX-CH word frequency and contextual-diversity data calibrate the
lexical lattice (<https://doi.org/10.1371/journal.pone.0010729>). Every external
resource must be versioned and hashed. No project outcome, optional reader
comment, or model judgment may enter measurement construction.

The external reference distribution is the Beijing Sentence Corpus associated
with <https://doi.org/10.3758/s13428-021-01730-2>. Only lawfully available
sentence text and published predictability fields may be used. If the corpus or
its applicable license cannot be obtained, Stage 0 stops and the protocol must
be versioned before substituting another reference corpus.

## Stage 0: measurement and admission

### Structural localization

The new measurement starts from the frozen broad structural gate in
`nominal-chain-integration-probe-0.2`:

- at least five pre-head lexical tokens;
- at least 10 visible pre-head characters;
- at least three `acl`, `amod`, `compound`, or `nmod` relations;
- no overt internal boundary, punctuation boundary, or pre-head verb;
- a complete prose passage containing 120-360 CJK characters and at least two
  sentence endings.

The structural gate locates spans only. Its earlier 87 candidates were not one
coherent construction, so passing it does not imply reader friction.

### Lexical boundary vector

`boundary_competition_v1` must expose a vector rather than an opaque score:

- normalized entropy over all lexicon-supported segmentation paths;
- log-probability margin between the best and second-best paths;
- posterior boundary probability at every inter-character gap;
- number of ambiguous gaps with posterior probability in `[0.25, 0.75]`;
- distance from the last boundary with posterior probability at least `0.80`
  to the head noun;
- single-character-word and multi-character-word-start probabilities;
- left and right branching entropy;
- left and right accessor variety;
- lexical coverage and abstention reason;
- proper-name, numeric, ASCII-technical-term, and quoted-name anchors as
  separate variables.

Low lexical coverage causes abstention; it must not be converted into high
competition. Proper names, numbers, and technical terms are recorded as
anchors and are not deleted by rule. Stanza-versus-dictionary segmentation
disagreement is retained only as a diagnostic.

The version 1.0 lattice uses CJK-only substrings of at most eight characters.
A known edge receives unigram weight
`(SUBTLEX WCount + 0.1) / (retained WCount total + 0.1 * vocabulary size)`.
When no known one-character edge exists, the fallback weight is its SUBTLEX
character probability multiplied by `0.01`. Exact forward-backward summation
produces path entropy and gap posteriors; a two-best dynamic program produces
the path margin. Entropy and margin are divided by scored CJK length. ASCII
runs are counted as anchors and omitted from the CJK lattice. Known-character
coverage below 0.80 causes abstention rather than a high-competition result.

The working example must be localized and scored without a phrase-specific
lexicon entry or blacklist. Failure to localize it stops the experiment.

### External calibration

All percentile cutoffs are computed from length-matched CJK windows in the
Beijing Sentence Corpus before the post-period candidate pool is ranked.
Entropy is normalized per scored character, ASCII runs are treated as single
anchors, and a candidate abstains when fewer than 100 external windows exist
within plus or minus two scored characters of its pre-head span length. The
calibration set, resource versions, normalization, smoothing, unknown-token
penalty, window counts, and SHA-256 identities must be written to the run
manifest. The high and low strata are then fixed as follows:

- **high competition:** path entropy at or above the external 90th percentile,
  best-versus-second margin at or below the external 10th percentile, at least
  two ambiguous gaps, and unresolved distance to the head of at least six
  characters;
- **low competition:** path entropy at or below the external median,
  best-versus-second margin at or above the external median, no more than one
  ambiguous gap, and unresolved distance to the head of at most three
  characters.

Branching entropy, accessor variety, tokenizer disagreement, and anchor counts
do not decide admission in version 1.0. They are recorded for diagnosis and a
future independently versioned model.

### Corpus separation

Candidate passages may come only from post-period documents published on or
after 2025-07-01 that are already discovery or development exposed. The
30-document validation reserve in `post_reader_handoff_v2` remains unopened.
All documents in previous reader ratings, screens, or interventions are
excluded before ranking.

The reader experiment requires:

- eight high-competition and eight matched low-competition passages;
- 16 distinct documents, with one passage and one target span per document;
- at least three sources and no more than three documents from one source in
  either stratum;
- at least two editorial formats in each stratum;
- no source-body or CJK-bigram overlap with a previous reader task;
- a complete, self-contained passage under the frozen prose gate.

Each high item is matched to one low item by source, editorial format, target
span length, passage length, anchor profile, and publication month where
available. Source, format, and the three binary proper-name, numeric, and ASCII
anchor indicators must match exactly. Target-span CJK length may differ by at
most two characters; passage and target-sentence CJK-length ratios must both be
within `[0.80, 1.25]`.

The fixed distance is `0.35 * span difference / 2 + 0.35 * normalized absolute
passage log-ratio + 0.20 * normalized absolute sentence log-ratio + 0.10 *
publication-month distance / 24`, with the last term capped at one and log
ratios normalized by `log(1.25)`. The matcher considers the most extreme
eligible candidate per document, sorts all valid edges by distance, breaks
exact ties by `SHA-256(seed | high candidate | low candidate)`, and greedily
accepts cross-document edges without replacement. No source may supply more
than three pairs. The final eight pairs must cover at least three sources and
two formats. If eight valid matched blocks are unavailable, the experiment
stops without relaxing thresholds or creating a reader project.

## Stage 1: boundary-only intervention

The operator is `unpack_boundary_competition`. It may:

- move the head noun earlier;
- turn an existing modifier-head relation into an explicit subject-predicate
  or topic-comment relation;
- add only grammatical function words, pronouns with explicit antecedents, or
  punctuation needed to expose that relation;
- split one sentence into two while retaining explicit arguments and
  cross-sentence reference;
- reorder existing modifier material so a lexical anchor is adjacent to its
  head.

It must not:

- delete, generalize, or strengthen any proposition;
- add a premise, explanation, definition, causal claim, or concrete detail;
- replace or silently define an abstract expression;
- remove named entities, technical terms, quantities, negation, attribution,
  modality, qualification, or uncertainty;
- flatten rhythm and authorial voice into a compressed instruction-manual
  style;
- alter any non-target sentence except the immediately required antecedent.

Every revision must preserve all source content words unless an exact
coreference substitution is logged. It must retain at least 70% character
similarity and may increase CJK length by no more than 25%. These are safety
bounds, not optimization targets.

The editor receives the 16 items in a seeded order without the high/low label,
rank, reader history, or future display side. Every edit records the exact
before and after span, moved material, inserted function words, explicit
relation, linked proposition IDs, locked literals, entity checks, numeric
sequence, negation, modality, attribution, uncertainty, voice anchors, and a
unified diff. A passage with an unresolved preservation question is rejected
before task generation; no replacement is selected after reader outcomes.

## Experimental design

The paragraph is the intervention unit and the source document is the
replication unit. The reader sees both versions of the same paragraph, so each
paragraph is its own block. High/low matched blocks control source, format, and
length variation. Repeated answers from one reader do not create independent
reader replication.

The frozen layout contains:

- eight high-competition intervention pairs;
- eight low-competition intervention pairs receiving the same operator;
- one identical-text diagnostic;
- one mirrored repeat of a randomly selected high-competition pair;
- two session blocks of nine tasks, with a break requested between blocks.

Within each stratum, four originals appear on side A and four on side B. Each
session contains four high and four low items plus one diagnostic. The mirrored
repeat reverses its first display side and occurs at least eight tasks later.
Task order and side placement use seed `2026083101`. Candidate identities are
assigned to the placeholder schedule by a separately recorded seeded mapping
only after the eligible matched set is frozen.

The reader is blind to original/revised status, competition stratum, score,
operator, source identity, and control role. The editor must not see outcomes.

## Reader instrument

The only required question is:

> Which version makes you more willing to continue reading?

The choices are version A, version B, or no meaningful difference/both bad.
An optional comment remains available but cannot change eligibility, decoding,
or a decision gate. The task does not ask for linguistic classification,
authorship judgment, or a reason for the choice.

## Outcomes and analysis

Decode each independent intervention unit as:

- `+1`: revised version preferred;
- `0`: no meaningful difference or both bad;
- `-1`: original version preferred.

Let `S_high` and `S_low` be the sums across the eight independent units in each
stratum. The primary development quantities are:

- high-stratum net preference: `S_high / 8`;
- low-stratum net preference: `S_low / 8`;
- selector contrast: `(S_high - S_low) / 8`;
- revised share among decisive answers in each stratum;
- tie rate and display-side choice distribution.

No confirmatory p-value is attached to the primary development gate. Exact
binomial intervals may be reported descriptively for decisive preferences, but
the reader is a fixed development reader and cannot support population-level
reader inference.

## Frozen decision gates

Interpretation proceeds in this order:

1. **Instrument gate:** the identical pair must receive the no-difference
   answer; the mirrored repeat must preserve the content preference or produce
   no difference both times; and the exact two-sided binomial test of display
   side among decisive intervention answers must not reject a 0.5 side share at
   `alpha=0.05`. Failure makes the intervention outcome uninterpretable.
2. **Preservation gate:** every independent revision must retain all locked
   propositions, entities, quantities, negation, modality, attribution,
   uncertainty, and voice anchors. Any detected failure blocks operator
   promotion even when preference is positive.
3. **Manipulation gate:** every high-stratum revision must shorten unresolved
   distance to the head and lower path entropy without lowering lexical
   coverage. Failure rejects the implementation of the operator.
4. **High-stratum benefit gate:** at least six high items must be decisive; the
   revised share among them must be at least 0.75; and `S_high / 8` must be at
   least 0.50.
5. **Selector-specificity gate:** `(S_high - S_low) / 8` must be at least 0.50.

If gates 1-5 pass, the selector and operator advance to a separately powered,
multi-reader validation design. If the high and low strata both meet the
benefit gate but the selector contrast fails, only the operator remains a
candidate and `boundary_competition_v1` is rejected as a selector. If
`S_high <= 0`, the current operator is rejected. Any other outcome is
inconclusive; more independent examples may be acquired under the frozen
measurement, but thresholds and edits must not be tuned against these outcomes.

## Sample-size boundary

Sixteen independent passages are a development screen, not a powered
validation study. For an optimistic exact two-sided binomial test against a
0.5 decisive preference rate at `alpha=0.05` and 80% power, the minimum
decisive-pair counts are:

| True revised preference | Decisive pairs | Tasks with 20% ties |
|---:|---:|---:|
| 0.65 | 90 | 113 |
| 0.70 | 49 | 62 |
| 0.75 | 30 | 38 |
| 0.80 | 20 | 25 |

The 0.70 row is the smallest practically interesting effect for a targeted
editing rule, but 49 comparisons from one reader would still not replicate the
reader. A later confirmatory design must cross multiple independent readers
with held-out passages and determine reader and item counts by simulation under
the planned mixed-effects model. The development effect estimate must be
shrunk rather than copied directly into that power calculation.

## Reproduction

Generate the placeholder allocation and exact-binomial sensitivity table with:

~~~powershell
python experiments/design_boundary_competition_experiment.py `
  --output-dir feature_runs/boundary-competition-design-v1 `
  --seed 2026083101
~~~

The generated files contain no corpus text and remain under ignored
`feature_runs/`. The actual task generator must validate the frozen allocation,
corpus-separation, matching, preservation, and manipulation gates before it can
emit Label Studio tasks.

## Immediate stop/go decision

The next action is to implement and externally calibrate
`boundary_competition_v1`. Do not inspect the 30-document validation reserve,
write passage-specific lexical exceptions, prepare revisions, or open Project 8
until Stage 0 produces eight valid high/low matched blocks under this protocol.

## Stage 0 result

Stage 0 was run on 2026-08-31 without changing the frozen thresholds. The
external calibration used 150 sentences from the public Beijing Sentence
Corpus OSF workbook and the public SUBTLEX-CH word and character tables. The
Beijing workbook has SHA-256
`5c96e829a3de8203739893eef6b54e6ebddf055976919d9b29b2797053d81876`.
Its OSF and DataCite metadata do not specify a license, so the file remains an
untracked local research input and is not redistributed. The SUBTLEX word and
character table hashes are
`086536450b1f77d0c7ff3ac0fc8375897162ace807d3167bec48b4c493434077`
and
`03ffacc65c4d14530338c1bffb72b2e98d06ee23bed14546dc8001ab4bcbb415`;
their Figshare record specifies CC BY 4.0.

All 87 previously frozen structural candidates were scored. None came from a
previous reader document, and the 30-document validation reserve was absent
from the candidate input and remained unopened. The result was:

| Boundary stratum | Instances | Documents |
|---|---:|---:|
| High competition | 0 | 0 |
| Low competition | 36 | 23 |
| Middle or unscored | 51 | 28 |

Seven candidates in seven documents independently passed both the high-entropy
and low-margin percentile gates. Only one candidate had at least two ambiguous
gaps, no candidate had unresolved distance of at least six characters, and the
maximum observed unresolved distance was four. The high candidates therefore
number zero, no high/low matching edge exists, and Stage 0 fails before editing.

The reader-localized example was fully scorable but did not resemble lexical
segmentation competition. Its entropy percentile was 0.669, margin percentile
was 0.346, ambiguous-gap count was zero, and unresolved distance was two. The
best SUBTLEX path was `原生 / 时代 / 全新 / 算 / 力 / 服务`. This also exposes a
domain-age limitation: the subtitle lexicon does not treat the modern technical
term `算力` as one word. Adding it after seeing the result would be prohibited
phrase-specific tuning and would not address the larger result.

Reject `boundary_competition_v1` as an intervention selector. The reader's
description is better interpreted as competition among word-level modifier
attachments or phrase bracketings than as uncertainty about character-to-word
segmentation. Do not prepare revisions, assign the frozen allocation, or create
Project 8 from this run. A word-level bracketing hypothesis requires its own
pre-outcome literature review, measurement protocol, and independent gate.

Two independent runs produced byte-identical artifacts:

| Artifact | SHA-256 |
|---|---|
| Summary | `0d8babb378cce2789ebf2a47717b6242549ef34de86a68f6fe4241e6497dfc9b` |
| Candidate measurements | `77926cc1f71a60c7959c488b98863af43b0b7bcdfd42d47e7aa95fc2982cabe5` |
| Candidate table | `60a42c4ca6541ba2f0f1cd4cad8d9556b94dd89501904aacbc2b9566c885c5f5` |
| Empty matched-pair file | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

~~~powershell
python experiments/boundary_competition_probe.py `
  --candidates feature_runs/nominal-chain-integration-v1/candidates.jsonl `
  --nominal-summary feature_runs/nominal-chain-integration-v1/summary.json `
  --subtlex-word-file feature_runs/boundary-competition-resources-v1/subtlex_ch/SUBTLEX-CH-WF `
  --subtlex-character-file feature_runs/boundary-competition-resources-v1/subtlex_ch/SUBTLEX-CH-CHR `
  --bsc-workbook feature_runs/boundary-competition-resources-v1/BSC.Word.Info.v2.xlsx `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v2 `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v3 `
  --annotation-dir data/annotations `
  --output-dir feature_runs/boundary-competition-probe-v1
~~~
