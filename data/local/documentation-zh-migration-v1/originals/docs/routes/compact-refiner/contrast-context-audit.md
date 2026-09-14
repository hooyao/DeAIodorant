# Contrast Context and Reading-Defect Audit

Protocol: `contrast-context-audit-1.0`. Date: 2026-09-14.
Status at definition: exploratory protocol after literal cohort counts were
observed, before new semantic reviews. It is not a preregistered confirmation
of the observed temporal difference.

## Scope and questions

Audit all 57 literal occurrences of `而是` in the 13 positive-count InfoQ
documents retained by the known-translation-excluded view of
`ershi-cohort-statistics-1.0`. Keep all 35 documents in deterministic context
metrics, including 22 zero-count documents. Selection by the nominated cue is
explicit: this is feature interpretation, not a smell prevalence estimate.
Existing formal-admission uncertainties remain unresolved.

For each occurrence, identify the semantic relation and what would be lost by
deleting either side. Separately localize any possible reading defect, including
defects away from the connector. Do not equate correction or repeated contrast
with unnecessary wording. A legitimate relation can still be packaged
repetitively; a sentence without the marker can still be difficult.

## Immutable inputs and deterministic observations

Reuse the hash-checked bodies and literal offsets from the earlier run. Save
private exact-body copies and a public-free manifest; do not overwrite earlier
inputs, labels, or outputs. Unicode offsets are zero-based and end-exclusive.

Record body CJK length, literal count, and the maximum number of connector
starts within 500 and 1000 consecutive CJK-character positions. For each span,
require last minus first position to be strictly less than the window length.
These overlapping maxima are descriptive concentration measures, not error or
smell thresholds. Short documents remain identified. A non-CJK run does not
advance this coordinate system; expose Unicode positions as well.

Mechanical context units end at `。！？!?`; newlines do not delimit sentences
because capture inserts line breaks inside inline elements. Preserve full body
access. These units are navigation aids, not validated linguistic sentences or
DOM paragraphs. Do not measure paragraph defects from collector line breaks.

## Review procedure and fields

Two independent assistant reviewers read all 13 complete supplied bodies.
Each receives the same neutral document aliases and offset-indexed occurrences.
Publication metadata, cohort, previous judgments, and aggregate rate differences
are omitted from packets. This masks metadata only: article content can reveal
time, provenance, and genre. No claim of complete blinding or human judgment is
permitted. Reviewers must not read each other's outputs or identity mappings.

Each reviewer writes `review-a.json` or `review-b.json` with `reviewer`,
`model_identity` (only if available), `human_gold: false`, `documents`.
Each document has `alias`, `whole_body_read: true`, `genre_observation`,
`occurrences`, `reading_defects`, `counterexamples`, and `document_note`.

Every occurrence has:

- `occurrence_id` and an exact `evidence_quote` containing the connector;
- `relation`: `correction`, `scope_extension`, `temporal_change`,
  `procedural_alternative`, `evaluative_reframing`, `unclear_or_malformed`,
  or `mixed` (choose a dominant relation; explain overlap);
- `voice`: `reporter`, `attributed_quote_or_paraphrase`, `mixed`, or `uncertain`;
- `contrast_contribution`: a short description of the information conveyed;
- `packaging`: `ordinary`, `repetition_candidate`, or `uncertain`;
- `packaging_reason`, `preservation_risk`, and `confidence`: `high`, `medium`,
  or `low`.

`repetition_candidate` requires an explicit repeated move elsewhere in the
same article or an independently described redundant opposition, not marker
presence or a general dislike of the topic. Keep substantive contribution and
possible repetitive presentation on separate axes. No smell intensity score.

Each localized `reading_defects` entry has `defect_id`, `kind`, an exact
`evidence_quote`, `explanation`, `repairability`, `support_quotes`, and
`confidence`. `kind` is `argument_or_reference`, `relation_or_support`,
`attachment_or_density`, `lexical_or_translationese`, `possible_capture_issue`,
or `other`. `repairability` is `local_reexpression`, `article_supported`,
`requires_missing_information`, or `uncertain`. Prefer a few specific supported
findings over a quota. Empty defect lists are valid. Ordinary Chinese ellipsis,
intransitives, shared subjects, nominal predicates, and intentional list/headings
are not automatically defects. Technical unfamiliarity alone is insufficient.

Each counterexample has an exact `evidence_quote` and an `explanation` of a
necessary contrast or a coherent construction that an overly broad rule would
damage. Full documents remain the interpretation unit. No edits, training
labels, originality admission, or factual truth certification are produced.

## Validation and interpretation

Validate exhaustive unique occurrence coverage and all evidence strings against
the exact body. Retain independent raw reviews and disagreements. Report simple
agreement only as assistant consistency on this selected set, never reader
validity. Inspect disagreements and high-confidence defect claims in context;
record adjudication separately without overwriting raw judgments.

Report source/genre/quoted-voice concentration and clear counterexamples before
proposing an operational feature. New feature definitions are exploratory and
need independent matched documents. Missing claims/premises may be flagged;
they may not be invented to make an edit fluent. The known Cowork feedback stays
weak-smell/difficult, regardless of the number of review flags.

## Next-stage gates

Prepare a small concrete reader calibration only if candidate real articles
show an interpretable, sustained contrast. Agents can nominate, not certify it.
No new smell-removal efficacy experiment proceeds on an assumed strong label.
The separately established difficult-reading case can support an explicitly
limited readability case study, with preservation checks and no smell claim.

Freeze prospective source/topic/format sampling and diagnostic definitions
before inspecting new validation documents. Sample-size expansion must retain
zero-count articles and symmetric provenance exclusions. SFT, DPO, RL rewards,
and GPU provisioning remain deferred.

## Reproduction

```powershell
python experiments/contrast_context_audit.py --output-dir data/local/contrast-context-v1
```

Review JSON files are assistant-produced artifacts and are not deterministically
reproducible. Their hashes, coverage checks, reviewer identity, and review scope
must accompany any derived results. External API requests and GPU use are zero
for the deterministic preparation; assistant reviews use the current agent
runtime and are reported separately.
