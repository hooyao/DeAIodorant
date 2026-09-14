# Compact Refiner Data Contract

Contract version: `compact-refiner-data-1.2`. Version 1.2 includes translated
Chinese inputs and upstream-source grouping. Earlier synthetic and media
records remain unchanged; versioned sidecars may supply new provenance fields.
Development record utilities exist; the full training-contract validator and
training exporters are not implemented yet.

## Unit of data and task

The fundamental unit for real media is the source article and its provenance
group, not an isolated paragraph. Reprints, near duplicates, excerpts, revisions,
and repeated judgments stay in the same group. For auxiliary synthetic material,
all variants of one generation task remain a generation-task group.

Main product evaluation uses complete media-article context and returns an
inspectable complete article. Individual operations may be local, but cannot
lose links to the full source or be treated as independent samples. The original
synthetic pilot's passage-sized task remains a historical auxiliary format.
Rationale, claim inventories, reviewer decisions, and reward diagnostics remain
separate from the student target.

## Real-media source record

Record `source_document_id`, `article_group_id`, canonical URL, source platform,
title, byline, publication/update/collection timestamps, raw capture identity,
normalized body identity, extraction and presentation versions, paragraph/figure/
table/code/link mapping, source-quality and visibility evidence, translation
evidence, rights status, historical exposure, and missing context.

The original is the acquired media source, not an assistant reconstruction or a
model-generated substitute. Keep original bytes and every transformation record.
Source cleanup must be versioned and distinguish layout extraction from prose
rewriting. A captured textual body is not proof that all multimedia context was
captured; unavailable essential figures remain an explicit limitation.

Retain temporal cohorts and their existing boundaries. Authorship is unknown
unless directly documented; publication date and target-smell impression do not
supply individual authorship labels. Historical weak annotations are not
confirmed strong positives. Training rights are evaluated separately from
lawful research acquisition and inspection.

The synthetic brief/draft schema below describes auxiliary generated records,
including CR-001. It does not require rewriting real media into a synthetic fact
packet or generating a new original before analysis.

Do not train a model to infer whether the input was authored by a human or AI.
Known generation provenance is recorded for reproducibility and evaluation
stratification only.

## Translation and upstream-source sidecar

For new media records, retain `provenance_status` (`direct_chinese`,
`translated`, `mixed_or_adapted`, `unresolved`), supporting evidence and review
version, `upstream_source_ids`, `upstream_source_languages`, and an optional
source-alignment record. Unavailable fields are explicitly unknown; foreign
names, external citations, and style do not establish source language or use
of an LLM. Existing legacy exclusion labels are preserved separately.

The default `input_language` is Chinese and the foreign original is not
required. Distinguish the Chinese input article from any upstream source so
the word original is not ambiguous in preservation records. Original sources,
translations, mixed adaptations, excerpts, and revisions form one connected
provenance group for train/evaluation splitting.

Translation provenance does not block research or, once other gates pass,
training eligibility. Rights, preservation, accepted edits, and group separation
still apply. Track inherited, translation-added, editorial-added, and unresolved
defects only when actual alignment evidence supports the assignment.

## Files in a dataset version

| File | Required contents |
|---|---|
| `dataset_manifest.json` | Schema/version, parent version, role, sources, rights policy, hashes, counts, exclusions, and split algorithm |
| `briefs.jsonl` | Generation instructions and available source facts/context |
| `drafts.jsonl` | Original model outputs and exact inference identity |
| `candidates.jsonl` | Unchanged controls and bounded revisions |
| `preservation_reviews.jsonl` | Automatic check output and independently attributed semantic review |
| `preferences.jsonl` | Blinded judgments, presentation mapping, reviewer identity, and validity state |
| `split_manifest.json` | Immutable group assignment and overlap audit |
| `exclusions.jsonl` | Item ID, stage, reason, evidence reference, and possible disposition |
| `exports/` | Derived SFT/DPO files, schema, filters, hashes, and counts |

Raw model text and human comments remain in the ignored dataset directory.
Operational logs contain IDs, status, timings, and bounded errors rather than
article bodies, prompts containing private text, or credentials.

## Brief record

Required fields:

- `brief_id`, `task_group_id`, `dataset_version`, `created_at_utc`;
- `genre`, `topic`, `audience`, `intended_voice`, and `requested_length`;
- `instruction_text`, `fact_packet`, `read_only_context`, and `locked_content`;
- `rights_status`, `rights_evidence`, `content_origin`, `contains_personal_data`;
- `brief_sha256`, `fact_packet_sha256`, and any upstream source IDs/hashes.

For the first batch, prefer purpose-written, explicitly fictional task briefs
with a complete fact packet. Label fictional names and numbers as constructed
material. Do not present them as empirical examples of natural prevalence.
Real user drafts require an applicable permission and retention record.
Public availability alone is not permission to train or republish.

If source material is used, preserve its provenance and license/permission.
Reject uncertain training rights from the training export; do not infer rights
from an article's admission to the old research corpus.

## Draft record

Required fields:

- `draft_id`, `task_group_id`, `brief_id`, `split`, `draft_text`, `draft_sha256`;
- `generator_kind`, `requested_model`, `returned_model`, `provider`,
  `checkpoint_revision`, `prompt_version`, and `prompt_sha256`;
- `request_config`, `request_config_sha256`, `seed`, `seed_supported`,
  `generated_at_utc`, `finish_reason`, `usage`, and `cost`;
- `generation_status`, `fact_packet_consistency`, and `exclusion_reason`.

Unsupported or unavailable provider metadata is explicit `null` plus a reason,
not a guessed identity. A seed does not imply deterministic remote inference.
The cache key includes the full effective request, model/provider identity, and
content hash, not just the prompt version.

Generate ordinary task responses without asking for a bad, stereotyped, or
"AI-smelling" style. Keep already-good drafts: unchanged output is an essential
editing behavior. Do not curate every draft by a target marker or NLP score.

If the draft invents a fact or contradicts its fact packet, quarantine it for a
separate content-correction task. This style route does not quietly repair that
claim or count its removal as a style improvement.

## Candidate record

Required fields:

- `candidate_id`, `task_group_id`, `draft_id`, `candidate_kind`, `parent_id`;
- `intensity` (`low`, `medium`, or `high`), `editable_span`, `context_sha256`;
- `output_text`, `output_sha256`, `operations`, and `candidate_provenance`;
- generator/editor identity and prompt/request fields when applicable;
- `deterministic_checks`, `preservation_review_ids`, and `eligibility_status`.

Candidate kinds are `unchanged`, `compact_prompt`, `assistant_edit`,
`human_edit`, `sft`, and `dpo`. Additional kinds require a versioned extension.
An assistant edit is model-assisted, even when carefully inspected by that
assistant. It is not a human-edited upper bound.

Each operation records `operation_id`, `type`, `start_char`, `end_char`,
`before`, `after`, `reason`, and `claim_ids`. Offsets use Unicode code points in
the exact original passage, with a half-open interval `[start_char, end_char)`.
Operations must be nonoverlapping and reproduce the output when applied from
right to left. An unchanged candidate has identical hashes and no operations.

Initial operation types: `clarify_reference`, `reduce_redundant_framing`,
`reorder_existing_information`, `repair_grammar`, `split_or_merge`, and `keep`.
These describe proposed edits; they are not claims that the smell catalog has
validated universal rules. Content additions and factual corrections are out
of scope.

During the autonomous preflight, `unclassified_rewrite` records a complete
passage replacement before semantic intent review. It is an auditable proposal,
not an accepted training operation, and cannot bypass review or export gates.

## Preservation review record

Record `review_id`, input/candidate hashes, reviewer kind and stable ID,
review time, review-policy version, evidence spans, issue codes, and disposition
(`pass`, `fail`, or `uncertain`). Keep human, assistant, and other model
assessments separate. A model may flag risk but cannot certify human acceptance.

Check propositions, entities, numbers with units, dates, citations, negation,
modality, qualifications, attribution, scope, reference, and voice. Check both
directions: material removed from the input and material introduced by the edit.
Literal checks alone cannot establish entailment or completeness.

`fail` and `uncertain` do not enter the accepted training or preference export.
Preserve them as labeled audit/challenge material. A repaired candidate gets a
new ID/hash and a new review; the old failure remains visible.

## Preference record

Required fields: `judgment_id`, `task_group_id`, `draft_id`, two candidate IDs,
protocol and presentation IDs, original A/B mapping, stable pseudonymous reader
ID, reader kind, timestamp, chosen answer, optional comment, and validity state.

Valid human answers are A, B, both acceptable/no meaningful difference, both
unacceptable, and unable to judge. Do not force ties or disagreement into a
binary preference. Do not substitute a model-generated preference for a missing
human response. The public task view excludes generator identity, intervention
type, NLP scores, preservation verdicts, and expected answers.

The reader must see enough identical context to interpret both candidates.
Keep contextual information the same in both arms. A change in context is a
different experiment, not a style edit.

## Dataset roles and leakage

Use explicit roles: `development`, `train`, `validation`, `final_test`, and
`challenge`. Historical discovery and reader examples remain development-only
unless separately reviewed for training rights and eligibility; they can never
become fresh validation or final-test evidence.

Assign connected groups before generating or inspecting variants. Shared fact
packets, source documents, lightly varied briefs, passage extracts, near
duplicates, and rewritten derivatives belong to the same connected component.
All components stay in one split. Topic names alone do not define independence.

For a new training dataset, a starting allocation of 80% train, 10% validation,
and 10% final-test groups is a planning default, not a power calculation. Freeze
the assignment with seed `20260914`, group identities, algorithm version, and
balance report. Acquire additional independent evaluation groups if the frozen
sample-size design needs more; do not count variants as new groups.

R1's 24 groups are all development. No part of that batch is held-out validation.
Do not read the legacy 30-document reserve or old sealed translation tests.

## Export rules

| Export | Eligibility |
|---|---|
| SFT positive edit | Rights cleared; accepted semantic review by a human; explicit human acceptance of the edit; correct group split; exact source and output hashes |
| SFT unchanged | Rights cleared; human reviewer affirms no beneficial in-scope edit is needed; output exactly equals input |
| DPO pair | Same exact student input/context/intensity; two preservation-passing candidates; decisive, valid human preference; no unresolved disagreement; both candidates in the same group |
| Challenge set | Versioned failure type and evidence; excluded from positive training exports |
| Model-assisted proposal pool | Clearly labeled unreviewed/synthetic; not silently mixed into human-accepted exports |

A separate synthetic-only feasibility run may test plumbing, but cannot claim
reader improvement or satisfy R2's human-reviewed data gate. Preserve naturally
occurring no-edit cases; the working SFT mix aims for roughly 20-30% unchanged
examples when supported by review. Do not fabricate labels or discard legitimate
cases to meet a ratio. Report the actual mix and sampling weights.

SFT exports contain only the canonical instruction/context/intensity, input
passage, and accepted output. DPO exports contain the identical canonical input
plus chosen/rejected outputs. Review notes, source-model labels, expected answer
keys, feature scores, and split names never enter model input.

## Required validation before export

Validate schemas, IDs, UTF-8, hashes, rights, split membership, duplicate groups,
input equality within preference pairs, operation replay, review provenance,
and eligibility. Fail closed on missing or contradictory evidence. Export a
count of every exclusion reason and the untouched input manifest hash.

Do not provide a runnable training command until the validator/exporter exists
and the target export passes it. Implement reusable data and evaluation logic
incrementally under `src/deaiodorant/`; preserve existing root commands.
