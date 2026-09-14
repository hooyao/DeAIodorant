# Candidate Generation Mechanisms: Reference, Not Evidence

Version: `generation-mechanism-hypotheses-0.2`. Date: 2026-09-14.
Provenance: a maintainer-supplied discussion with Gemini, offered explicitly as
reference while the contrast-context audit was already running. The discussion
is an external model explanation without supporting citations or controlled
training evidence. The two ongoing independent reviews did not receive it.

## Useful linguistic hypotheses

| Hypothesis | Observable prediction | Current test boundary |
|---|---|---|
| Repeated claims of deeper explanation substitute for exposition | Multiple local contrasts reject a shallow label and assert a broader evaluative one while adding little distinct support | Describe both propositions, repeated moves, and supplied evidence in whole articles; do not infer training incentives |
| Recurrent framing accompanies argument or reference discontinuity | A contrast changes the predicate's semantic subject or leaves a relation unresolved in context | Separate overt subject omission, recoverable reference, semantic-role mismatch, and genuinely unresolved reference |
| Cross-language adaptation carries over formulaic framing | Paired source and Chinese passages share repeated contrast placement or exhibit mismatched relations | Needs actual aligned source evidence; foreign citations and translationese impressions alone do not establish adaptation |
| Compression weakens exposition | Material claims are present but their relationships or references remain underspecified | Identify whether repair is supported by existing information; a missing premise cannot be fabricated |

These are candidate explanations for language behavior. Marker frequency,
semantic contribution, perceived irritation, and reading difficulty remain
separate measurements. The current audit does not add a new label or threshold
in response to this reference.

## Unsupported causal claims and technical corrections

- DPO ordinarily optimizes preference pairs directly without requiring a
  separately fitted reward model. Preference optimization could concentrate
  stylistic habits, but the reference does not establish that this construction
  was rewarded or that reward hacking caused its observed frequency.
- Synthetic data can transmit a teacher's stylistic regularities. Exponential
  amplification, universal degradation, and transfer from private reasoning to
  published Chinese output are additional claims requiring evidence. They do
  not follow from the use of synthetic data alone.
- English-dominant training exposure does not establish a literal internal
  English-first reasoning and word-by-word Chinese decoding pipeline. Such an
  account requires model-specific evidence.
- Missing or awkward surface arguments do not identify attention decay,
  greedy decoding, or a length penalty as their cause. The reference's example
  `这不仅不是技术的退步，而是在实际业务中落地了降本增效` requires analysis of
  what `这` denotes and of parallelism; lack of a repeated subject is not by
  itself proof of an ungrammatical clause.
- The comparison table's claims that early GPT-4 had purely human, uncontaminated
  training data, uniformly mild alignment, and reliably superior Chinese
  grammatical completeness are not supported by the supplied material. No
  proprietary training-data composition or model internals are inferred here.

## Experiments that could discriminate mechanisms later

1. With fixed semantic briefs and controlled output length, compare neutral
   exposition prompts with explicit requests for counterintuitive/deeper
   analysis. Increased framing would show prompt sensitivity, not the cause in
   training. Synthetic outputs are engineering material, not target-media
   evidence.
2. Compare aligned original/translated media passages using documented source
   provenance. Keep translated material outside the original-only main cohorts.
3. If comparable base and post-trained checkpoints, preference data, and
   suitable compute become available, evaluate the same tasks across stages.
   Model/version differences alone cannot isolate RLHF, DPO, SFT, or data mix.
4. A controlled repeated-distillation study would need fixed teacher/student
   recipes and nonrecursive controls to assess inherited style or amplification.
   It is not necessary for the current refinement objective and is not scheduled.

## Current decision

Continue the source-grounded context and reading-defect audit unchanged. Use
the reference to organize rival explanations, not to label articles or explain
the 8.3-fold available-sample count ratio causally. Reader benefit and meaning
preservation can be tested without resolving proprietary training mechanisms.
No new generation experiment, training run, model download, or GPU request is
authorized by the reference itself.

## Further reference: English writing and translation chains

The maintainer supplied a second uncited Gemini explanation about English
reader complaints, low information return for reading effort, formulaic
vocabulary, uniform rhythm, and burden shifting. The maintainer also explicitly
warned that LLM-generated English can already be poor before an LLM translates
it into Chinese. This reference arrived after both independent semantic reviews
were substantively complete; it does not change their labels.

Useful hypotheses concern repeated propositions, redundant metadiscourse,
overstated conclusions, and the work readers perform to reconstruct or verify
an argument. They apply even when individual sentences are grammatical. The
diagnostic design will preserve source/translation pairs when actually
available, without inferring either author's identity or translation method.

The reference's stronger claims remain unverified: universally impeccable
English syntax, community-wide prevalence or intensity of aversion, a direct
connection between low perplexity and poor writing, and a demonstrated neural
or mentalizing mechanism. Information value is semantic and task-dependent;
token entropy is not a substitute. Familiar terminology, balanced syntax,
triples, or words such as `robust` can all be appropriate in context.

The [calibrated objective](../../target-feature-discovery.md) now explicitly
separates the original-only temporal control from the product's broader
translated-media diagnostic scope. No original-language source is assumed to
be high quality, and the claim that translation worsens a specific defect
requires paired evidence.

The maintainer's subsequent explicit correction supersedes any earlier emphasis
on translation exclusion in this record: translated Chinese is a core refinement
target, all provenance strata remain in research, and original-only filtering
is one sensitivity/control. The maintainer delegates direction to the current
source-grounded reading-defect and bounded-repair route. No inference about
RLHF, DPO, synthetic training, or English-first internal reasoning is added.
