# Evidence-Linked Analysis of Explanatory and Corrective Discourse Moves

Protocol: `cognitive-move-analysis-1.0`. Date: 2026-09-14.
Status: exploratory worked annotation, not an automatic detector or validated
reward. The previous mechanism account is a hypothesis to test.

## Unit and scope

A discourse move is the smallest source-linked span that performs one coherent
communicative operation, with the context needed to interpret it. It can occupy
part of a sentence, several sentences, a heading plus its elaboration, or
cross-paragraph support. Do not force every sentence into an A-versus-B template.
The analyst describes the text's move, not the reader's actual mental state or
an inspected internal model process.

Keep detection, semantic description, and evaluation separate. A necessary
correction can exhibit the reader-nominated surface style; a stylistically
aversive title can still deliver a useful organization. Lack of a locally
stated misconception does not by itself prove a straw man. An unverified claim
is not automatically false, and a useful recap need not add new facts.

## Structured move record

Each record includes an ID, document/view identity, exact source spans, context
block IDs, and these semantic fields:

1. `operation`: correction, scope restriction, explanation, inference,
   evaluative reframing, recap, or agenda setting; multiple roles are allowed
   when a primary role is identified.
2. `question_under_discussion`: a neutral analytical description of what the
   passage addresses, with `explicit`, `analyst_reconstruction`, or `unknown`
   provenance. Do not present a reconstruction as quoted source text.
3. `prior_or_foil`: the rejected/prior claim if supplied, its source location,
   and whether it was introduced here, stated earlier, quoted, or unresolved.
   Explicitly distinguish a negated proposition from evidence that a reader
   actually believed it. This field can be null.
4. `asserted_or_promised_content`: the affirmative claim, qualification, value
   focus, or organizational promise. Retain entity, time, scope, modality,
   attribution, and quantities. An agenda promise is not a factual correction.
5. `relation`: the relationship expressed or implied between propositions:
   same-dimension alternatives, restriction/subset, compatible dimensions,
   cause, means-end, restatement, epistemic strengthening, or unresolved.
   Type observations are not formal entailment proofs.
6. `grounds_and_warrant`: exact evidence spans, the inference bridge actually
   supplied, any plausible but unstated bridge, and what remains unknown.
   Separate support inside the article from independently verified truth.
7. `information_update`: concrete specification, clarification, qualification,
   reorganization, recap, value prioritization, unsupported extrapolation, or
   unclear contribution. Repeated information may still orient the reader.
8. `stance_and_presentation`: observable claims of certainty, correction,
   authority, direct address, parallelism, or metadiscourse, without inventing
   motives. Describe recurrence elsewhere with exact source references.

Finish with separate assessments: content/relationship status, possible style
burden, preserved utility, counterinterpretation, confidence, and unresolved
questions. No overall smell score and no new per-unit human severity label.

## Fixed worked examples

Use six already exposed units, selected for explanatory contrast rather than
prevalence. Read both complete source articles before labeling any unit:

- SMZDM title: the explicit reader-localized agenda frame; A may be absent.
- SMZDM b006 platform distinction: the reader-nominated bare-copula form,
  retaining its useful concrete distinction.
- SMZDM b011 product-value reframe: retain `核心` and the learning-use condition;
  do not turn emphasis into a falsely asserted logical contradiction.
- SMZDM b015-b017 cost inference: inspect b013 and b026 as context, including
  component/scale differences, existing parts, and the estimate qualification.
- Baidu b012 cache mechanism: ordinary explanation without a required foil.
- Baidu b058 Apple causal replacement: inspect b057-b064 as context; distinguish
  source assertions, analogy, and established causation.

The source texts/blocks are in `data/local/reader-style-anchors-v1/smzdm/` and
`data/local/targeted-media-discovery-v1/baidu-supply/documents/92ade4253c08a43329164bf5/`.
SMZDM analytical offsets exclude publisher citation chips; title offsets refer
to metadata.title. Baidu offsets refer to its saved body. All quoted spans must
validate exactly. Semantic paraphrases are explicitly analyst-produced fields,
never replacements for the raw article or source quotations.

## Reliability checks and future computation

Check that alternative wordings can preserve the same move representation and
that a changed claim/polarity/scope would change it. These are prospective
validation requirements; merely writing equivalent analytical records is not
proof of an automatic model's invariance. No artificial article becomes a new
strong-positive sample.

Traditional NLP can assist sentence/block navigation, negation/modality/entity
extraction, coreference candidates, discourse-marker search, and repetition
localization. It cannot reliably decide whether A and B address the same
dimension, whether a warrant is sufficient, or whether a reader needs a recap.
Source-grounded LLM annotation and independent review can bootstrap those
records; they remain fallible measurements requiring evidence and disagreement
tracking. The historical lexical/UD support probe is not silently promoted to
general semantic support or revived as a validated quality score.

First demonstrate usable annotation and repeatability on a bounded set. Later
test whether proposed problem types predict useful same-article edits with
preservation and reader preference. Only afterward assess whether selected
components can be measured cheaply or distilled for refinement/reward use.
No annotation batch, rewritten article, SFT, GPU, or scalar reward is created by
these six worked examples.

## Outputs

Private directory: `data/local/cognitive-move-analysis-v1/`. Save the six
structured units, source/protocol hashes, quote validation, and analyst/reviewer
identity. Public documentation uses compact examples and English interpretation.
The known human labels remain article-level: SMZDM severe and Baidu lower
intensity. Do not ask for those labels again or treat these exposed units as
fresh validation evidence.
