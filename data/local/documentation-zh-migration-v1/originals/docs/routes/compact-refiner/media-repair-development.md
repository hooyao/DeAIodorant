# Source-Supported Media Repair Development

Protocol: `media-repair-development-1.0`. Date: 2026-09-14.
Status: bounded development preparation after the completed context reviews;
not a smell-removal validation study or a training dataset.

## Decision and purpose

The maintainer delegates research direction and explicitly requires translated
Chinese refinement. The next executable development question is whether a
complete real article can receive traceable useful repairs while retaining its
claims, details, attribution, uncertainty, and voice. Existing concrete reading
defects provide a task; no strong-smell label is assumed.

Use three exposed development sources from `contrast-context-v1`: `doc-03`
(technical announcement), `doc-05` (reader-described difficult, weak-smell
Cowork report), and `doc-04` (explicitly translated long interview). Preserve
all original bodies and their hashes. This purposive selection has no population
or temporal-effect interpretation. Source author identity and translation method
remain unverified. No fresh validation/test material is opened.

## Candidate contract

The editor receives each complete Chinese body, this protocol, and the general
editing objective. It does not receive private reasoning, occurrence scores,
reviewer defect labels, an English original, or expected reader preferences.
Save one proposed complete-article variant per source, retaining the unchanged
input as control. English metadata surrounds Chinese source/variant text.

Allowed operations are local expression/attachment repair, reference
clarification supported by the article, reduction of demonstrably redundant
framing, and reordering/splitting existing information. Preserve meaningful
negation and contrast. Do not mechanically replace every connector, globally
shorten, add anecdotes, supply facts, or assume the source's claims are true.

Specific material numbers, entities, technical terms, dates, qualifications,
citations, interview speaker turns, distinct examples, and unique information
must remain. Do not silently resolve internal contradictions or unsupported
claims. Record a separate `unresolved_content_issues` entry when necessary.
Content correction is distinct from a style/structure repair and cannot be
hidden in a candidate advertised as preserving meaning.

Write exact nonoverlapping source operations with `operation_id`,
`start_char`, `end_char`, `before`, `after`, `operation_type`, `reason`, and
`preservation_notes`; offsets are Unicode code points in the original body.
Replaying operations from right to left must reproduce the candidate exactly.
Each source has a complete `output.txt` and `operations.json`, including source
and output hashes, role/model identity when available, and unresolved issues.
An unchanged result is allowed when no supported repair exists.

## Checks and review

Root validates immutable source hashes, operation bounds, nonoverlap, exact
before text, replay, full-output hashes, and inventory differences. Literal
change checks are diagnostics, not semantic preservation proof. A separate
assistant then reads original and output in full and audits removed/added
propositions, including attribution, negation, numerical scope, and omitted
details. Preserve failures, uncertainty, and proposed improvements separately;
never overwrite a failed candidate to erase its history.

Assistant preservation passes remain assistant judgments. No human acceptance,
preference rate, smell intensity, SFT export, or training eligibility follows.
Reader comparisons, if subsequently justified, use whole-article context and
the same presentation, and distinguish readability from perceived smell. Do not
send a large batch of subtle changes as another strong-smell annotation task.

## Outputs and limits

Private root: `data/local/media-repair-development-v1/`. Record source and
protocol hashes before editing and editor/reviewer artifacts afterward. No
external API, model download, local/cloud training, or GPU is needed. This is a
current-assistant engineering/development proposal; reproducibility is in source
identity and operation replay, not guaranteed deterministic text generation.

Do not train until reviewed data coverage, translated-input evaluation, rights,
and the actual model/workload justify it. The prospective independent sampling
step retains translations as strata and zero-cue cases, with source/genre/topic
matching and a separately frozen analysis plan.
