# Worked Analysis of Explanatory and Corrective Moves

Date: 2026-09-14. Protocol: `cognitive-move-analysis-1.0`.
Status: six source-linked worked cases; no automatic semantic detector, quality
score, reader intervention, or training result.

## Operational definition

Describe what a text span does to an account of the subject, using explicit
source evidence. Do not infer the reader's actual prior belief. Identify a
focal move and distinguish its support, later summaries, and subsequent moves.
A paragraph can contain multiple moves, while a move can depend on evidence
in other paragraphs. The six cases are contextual packets, not a claim that
each entire paragraph is one atomic unit.

| Record component | Question answered |
|---|---|
| Question under discussion | What issue does this span address, and is that issue explicit or reconstructed by the analyst? |
| Prior or foil A | What claim is rejected or revised? Is it stated earlier, introduced here, quoted, or unknown? A may be absent. |
| Asserted/promised content B | What fact, interpretation, qualification, value focus, or organization is supplied? |
| Relation R | Are A and B alternatives on one dimension, compatible dimensions, a restriction, a causal account, or another relation? |
| Grounds and warrant E/W | What source passage supports B, and what bridge actually connects the evidence to it? |
| Information update | What becomes more specific or better organized? Is this a useful recap, value prioritization, or a stronger extrapolation? |
| Stance and recurrence | How does the narrator express certainty, correction, authority or guidance, and where does that move recur? |

The analytical descriptions are explicitly paraphrases, not source quotations.
All source evidence retains view identity, DOM block, exact quote, and Unicode
offsets. Content/relationship assessment and style assessment remain separate.

## Six worked cases

| Case | Focal action | Content/relationship observation | Style observation and limit |
|---|---|---|---|
| M01: SMZDM title | Agenda setting | No rejected A is required. Three body sections implement the route organization; their existence does not prove all costs are clarified. | The maintainer already explicitly dislikes the title phrase. Its causal mechanism and editing response remain unknown. |
| M02: Onboard hardware | Concrete correction | Jetson and RK3566 occupy the same platform slot. The article specifies the board and supplies deployment context. No reader belief is established. | The reader identifies the construction as a strong cue. Useful technical content must remain; no individual numerical severity is inferred. |
| M03: Product value | Purpose-conditioned value emphasis | Toy enjoyment and learning infrastructure can coexist. The word core and the learning condition make prioritization a plausible reading. Market exclusivity is a separate claim with missing comparison evidence. | The corrective presentation may be repetitive without being a formal false dichotomy. |
| M04: DIY and replication costs | Two successive inferences | A qualified retail-cost estimate becomes a broader savings verdict; then the comparison shifts to reverse-engineered commercial replication. Configuration, owned parts, geography and scale are not held constant. | Definitive judgment can outrun the stated uncertainty; the actual cost propositions are not proven false. |
| M05: Cache mechanism | Explanation | No A is needed. Reuse of retained computation links overlapping context to less repeated work; implementation scope remains simplified. | Explanatory usefulness does not require novelty to every reader. Dramatic wording is a separate observation. |
| M06: Apple analogy | Causal replacement and transfer | Outcome figures accompany a plausible platform mechanism but do not isolate causal priority, first-mover status, or transferability to Agent infrastructure. | A decisive corrective formulation can make an open causal hypothesis sound more settled; the later conditional conclusion is retained. |

M04 illustrates why this is more informative than counting connectors. The
annotation retains the estimate qualification, identifies the stronger
conclusion, locates the explicit backward reference in the next paragraph,
and names the changed comparison scope. Its issue is an underspecified
inference bridge; no particular connective is necessary to expose it.

M01 and M02 are equally important controls. A disliked title can organize an
article, and a reader-nominated corrective construction can add real information.
The framework would be circular if it forced both into content failure simply
because the whole article was rated severe.

## Revision and source checks

The initial analyst version linked six packets to 43 exact source-span
occurrences. Root review requested two corrections: retain the already supplied
localized title feedback, and distinguish focal actions from support and
subsequent moves. Version 1.1 preserves the original and adds explicit focus,
contextual moves, and the two successive M04 inferences.

The current artifact has 80 validated span occurrences representing 58 unique
spans, with 16 input hashes checked by the analyst. An independent root script
checks six case IDs, required fields, exact source strings, view/block bounds,
and protocol/record identity. These counts are evidence links, not independent
examples, measured accuracy, or reader judgments. Semantic interpretations
remain reviewable assistant annotations with unknowns and counterinterpretations.

## Practical computation path

Traditional NLP can locate candidate clauses, entities, negation, modality,
referential expressions and recurrence. Existing lexical/UD probes cannot be
promoted to proof that two claims concern the same dimension or that evidence
supports a conclusion. Those are the difficult semantic steps.

A bounded prototype can use a strong model to produce these evidence-linked
records, then independent review to challenge scope, attribution, and invented
foils. Test paraphrase invariance and meaning sensitivity before trusting its
outputs: connective-only changes should preserve the core move, while changes
in polarity, quantification, scope, or relation should be reflected. This run
does not claim an automatic model passed those tests.

Only after annotation reliability should article-level distributions and
within-article editing experiments test the hypothesis. Preserve separate
measures for correction frequency, evidence/claim gaps, and repeated stance.
Do not invent a weighted total or call it an RL reward. No feature is validated
merely because its explanatory annotation sounds plausible.

## Artifacts

Private directory: `data/local/cognitive-move-analysis-v1/`.

- `units.json`: unchanged first annotation.
- `units-v1.1.json`: revised focus/context and existing human evidence.
- `validation.json` and `validation-v1.1.json`: exact linkage checks.
- `validate_units.py` and `validate_units_v1_1.py`: reproduction scripts for
  those checks, with existing outputs protected from overwrite.

No source article, prior feedback, benchmark or feature configuration was
changed. No external API, GPU, rewritten article, or new reader question was
used for these worked examples.
