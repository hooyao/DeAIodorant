# Fresh Post-Period Reader Corpus Handoff

## Status

Protocol `post-reader-corpus-handoff-1.0` is frozen before another reader task
is generated. It defines the minimum input for development screening; it does
not authorize corpus acquisition in this workspace and does not make a corpus
final or representative.

The immediate purpose is to prevent pre-2025-07 and transition material from
being substituted for prose published on or after 2025-07-01. The validator
must pass before any new Label Studio project is created.

## Required directory layout

~~~text
<handoff-root>/
  manifest.json
  documents.jsonl
  texts/
    <doc_id>.txt
~~~

Paths in `documents.jsonl` must be relative to the handoff root. The validator
never modifies this directory.

## Manifest schema

`manifest.json` must contain:

~~~json
{
  "protocol_version": "post-reader-corpus-handoff-1.0",
  "generated_at": "2026-08-22T00:00:00Z",
  "status": "candidate_pool_not_reader_exposed",
  "post_start": "2025-07-01",
  "documents": 60,
  "documents_file": "documents.jsonl",
  "documents_sha256": "<lowercase SHA-256>"
}
~~~

The index hash covers the exact bytes of `documents.jsonl`.

## Document schema

Each JSON Lines record must contain:

- `doc_id`: 24 lowercase hexadecimal characters;
- `source`, `title`, `url`, `published_at`, and `collected_at`;
- relative `body_path`, `content_hash`, `cjk_chars`, `text_chars`, and
  `line_count`;
- `quality_pass`, `is_translation`, and `translation_evidence`;
- `provenance_status`, `provenance_basis`, and `value_status`;
- `visibility_status` and structured `visibility_evidence`;
- `topic_stratum` and `format_stratum`.

Admitted records must satisfy all of the following:

- `published_at` is on or after 2025-07-01;
- `quality_pass` is true and `is_translation` is false;
- provenance is `human_reviewed_original` or
  `model_assisted_original`;
- model-assisted provenance records name the model and have frozen confidence
  at least 0.90, and record the prompt version;
- value status is `human_kept` or `model_assisted_substantive`;
- model-assisted value records name the model and prompt version;
- visibility status is `verified_high_visibility` with non-empty evidence;
- format is `technical_practice`, `research_summary`, or
  `industry_reporting`.

Model-assisted provenance and value decisions remain measurements, not human
gold. Translation and compilation exclusion must remain fail-closed and
symmetric with the eventual pre-period comparison.

Body files are strict UTF-8 without a BOM, use LF line endings, and end with
exactly one LF. `content_hash` is the SHA-256 of the body without that terminal
LF. Counts use the same body. Exact and near duplicates of the tracked pilot or
another handoff record are rejected.

## Minimum coverage gate

Development is not ready unless the admitted pool contains:

- at least 36 documents;
- at least three topic strata with six documents each;
- at least two sources that each contribute six documents to all three required
  format strata.

This is a minimum development pool, not a validation pool. A 60-document
handoff is preferred so a separate document-level reserve can be frozen before
paragraph inspection. If fewer than 60 pass, development may start but no
held-out validation claim is available.

Visibility must be defined relative to source and collection window. A raw
current view count alone is insufficient because it creates age and
survivorship bias.

## Exposure and leakage gate

The validator rejects any document ID already named in tracked annotations,
experiment protocols, or research documentation. It also rejects document IDs,
URLs, exact bodies, and high-similarity bodies that overlap the tracked pilot.

Discovery, reader development, held-out validation, and the exposed translation
final test remain disjoint. Passing this validator does not assign a validation
role; document-level partitioning happens afterward under a fixed seed and is
recorded before paragraph outcomes.

## Planned reader use

After a handoff passes:

1. Freeze document partitions before inspecting reader outcomes.
2. Select context-complete post-period passages with deterministic formatting
   gates. Exclude code, captions, interview questions, figure-dependent text,
   author profiles, and truncated lines.
3. Begin with a 12-pair post/post discrimination calibration. Match source,
   topic, format, length, and visibility; balance A/B placement; expose neither
   metadata nor feature identity.
4. Ask only which passage makes the reader less willing to continue, with an
   explicit no-meaningful-difference choice and optional comment.
5. Stop before a larger comparison graph if the calibration is mostly ties.
   Do not force distinctions or increase edit intensity.
6. If discrimination is adequate, compare each development passage two or
   three times under a connected balanced graph and fit a tie-aware Davidson
   model. Feature rules remain candidate generators, not labels.
7. Admit a passage to intervention development only when repeated reader
   choices place it in the high-friction region. Comments cannot select cases.
8. Freeze the conservative edit operator and preservation audit before blinded
   original-versus-revision comparisons.

The reader never classifies linguistic features or authorship. Meaning
preservation remains an operation-log and deterministic proposition/entity/
quantity/negation audit.

Held-out validation requires the separate reserve, at least three formats, and
multiple independent readers. Development-exposed documents can never be
renamed as validation material.

## Reproduction

~~~powershell
python experiments/validate_post_reader_handoff.py `
  --handoff-root F:\path\to\post_reader_handoff_v1 `
  --repository-root . `
  --report feature_runs/post-reader-handoff-v1/validation_report.json
~~~

The command exits with status 0 only when the development gate passes. A failed
gate must not be overridden manually to create reader tasks.
