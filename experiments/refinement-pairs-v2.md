# Second-Round Conservative Contrast Intervention

## Status

Protocol version `conservative-contrast-reduction-2.0` was frozen on
2026-08-21 before any second-round preference outcome was available. This is a
small exploratory intervention, not a validated product rule or a
preregistration for confirmatory inference.

## Question

The sole required reader question is:

> Which version makes you more willing to continue reading?

The reader chooses version A, version B, or “about the same / neither.” A free
comment is optional. The form does not ask the reader to identify linguistic
features, infer authorship, or explain the preference.

## Frozen operator

The intervention is conservative contrast reduction. It permits four bounded
operations:

1. remove an ornamental attention, importance, or revelation frame when its
   payload is stated directly in the same passage;
2. restate an ornamental contrast directly while retaining both sides,
   negation, direction of change, and modality;
3. merge adjacent frames that repeat one relation while retaining every unique
   proposition and necessary logical contrast;
4. repair an interrupted or implicit grammatical argument using only an actor
   or object already explicit in the source passage.

The operator must not:

- delete or weaken a proposition, entity, number, negation, qualifier,
  uncertainty, or attribution;
- invent a fact, example, causal link, opinion, anecdote, or authority;
- remove a necessary logical contrast merely because it matches a surface
  pattern;
- maximize compression or normalize the passage into uniformly flat prose;
- drop explicit subjects, predicates, objects, or cross-sentence referents.

Selective metaphors, questions, parallel rhythm, first-person stance, and
evaluative language remain when they carry the passage's voice. The operation
log records retained necessary contrasts and voice anchors separately from
changed spans.

## Development-data separation

The first-round result and the 10 quick reader-friction ratings informed only
the operator-level constraints: preserve explicit arguments and avoid a cold,
maximum-compression style. None of the second-round line ranges overlaps any of
the 10 rated development passages. In particular, the three first-round ranges
remain excluded:

- `3c60dc0a981b686870095450`, lines 79–81;
- `0431c592d5de8246cebcb8e2`, lines 7–10;
- `44aa81958a6c585ee8c06847`, lines 15–22.

No second-round outcome was inspected while selecting passages or editing
variants.

## Passage set

All 10 passages are post-period material published on or after 2025-07-01.
They come from seven documents and have no recorded translation evidence in
their monthly metadata.

| Pair | Month | Document | Lines |
|---|---|---|---:|
| contrast-v2-01 | 2026-03 | b77b09a419c1631227112f0c | 7–10 |
| contrast-v2-02 | 2025-10 | a127f5baf364930a89fb4005 | 8–15 |
| contrast-v2-03 | 2026-06 | 3c60dc0a981b686870095450 | 3–7 |
| contrast-v2-04 | 2026-06 | 3c60dc0a981b686870095450 | 51–58 |
| contrast-v2-05 | 2026-06 | 3c60dc0a981b686870095450 | 59–68 |
| contrast-v2-06 | 2026-06 | 3c60dc0a981b686870095450 | 82–90 |
| contrast-v2-07 | 2026-01 | 44aa81958a6c585ee8c06847 | 1–6 |
| contrast-v2-08 | 2026-01 | 48bda219eb0776f623161899 | 17–21 |
| contrast-v2-09 | 2025-10 | 0431c592d5de8246cebcb8e2 | 21–23 |
| contrast-v2-10 | 2026-05 | b186cdd4f9004e0413395bf3 | 169–174 |

The set includes passages where a real contrast must remain, passages where
several reveal frames can be merged, and a first-person interview passage that
tests voice retention.

## Audit and preservation

`experiments/prepare_refinement_pairs_v2.py` stores every change as an exact,
ordered before/after replacement with an operator code, reason, and linked
claim IDs. Generation fails if an edit span is missing or ambiguous.

Each pair also records:

- the SHA-256 of the exact source passage;
- an exact set comparison of numeric literals;
- pair-specific locked names and technical terms;
- source and revised support spans for every proposition group;
- retained necessary contrasts;
- voice anchors that must remain in the revised passage.

The support-span manifest is a transparent manual audit, not proof of semantic
equivalence. It makes the preservation judgment inspectable and allows the
reader or a later reviewer to reject a variant. It does not use an LLM judge.

The frozen batch contains 26 logged replacements and 62 proposition checks.
The surface diagnostics decrease from nine complete contrast frames and 16
emphasis markers in the originals to zero counted instances in the revisions.
These counts verify that the intended manipulation occurred; they are not a
quality score.

## Blinding and reproduction

The fixed seed balances the original side exactly: five originals appear as A
and five as B. Pair order and side assignment are deterministic. Generated
tasks and the answer key remain in ignored `feature_runs/`; the answer key must
not be shown during rating.

~~~powershell
python experiments/prepare_refinement_pairs_v2.py `
  --corpus-root data/pilot/monthly `
  --output-dir feature_runs/refinement-pairs-v2 `
  --seed 20260821
~~~

Import `tasks.json` with `label_config.xml` into Label Studio. After all 10
responses are complete, store a new versioned annotation artifact rather than
modifying the first-round result. Report all outcomes, including ties, original
wins, preservation concerns, and unchanged or rejected variants.
