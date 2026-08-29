# Fresh Post-Period Reader Corpus Handoff

## Status

Protocol `post-reader-corpus-handoff-1.1` is frozen before another reader task
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
  "protocol_version": "post-reader-corpus-handoff-1.1",
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
- at least two sources with 12 documents each;
- at least three topic strata with six documents each;
- at least six documents in each required format stratum.

This is a minimum development pool, not a validation pool. A 60-document
handoff is preferred so a separate document-level reserve can be frozen before
paragraph inspection. If fewer than 60 pass, development may start but no
held-out validation claim is available.

Visibility must be defined relative to source and collection window. A raw
current view count alone is insufficient because it creates age and
survivorship bias.

Version 1.0 proposed a fully crossed source-by-format minimum. It was replaced
before any handoff or reader exposure because real editorial sources specialize
in different formats; forcing every source into every cell would encourage
incorrect format labels. Version 1.1 retains source and format diversity,
reports the full cross-table, and requires later matching to control the
imbalance.

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

## First completed handoff

The first version 1.1 handoff was generated at:

~~~text
F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1
~~~

It contains 50 documents, with 25 each from InfoQ and the Meituan technical
blog. The format composition is 24 technical practice, eight research summary,
and 18 industry reporting. Publication dates span 2025-08 through 2026-08.

The validation report contains zero errors and one warning: the handoff passes
the 36-document development gate but does not reach the preferred 60-document
threshold for an independent validation reserve.

| Artifact | SHA-256 |
|---|---|
| Manifest | `acde6900ae8b26b8da8821424be420ff48433752297c3f021e1a7e05ccfb2b14` |
| Documents index | `a16f73542edab7f38fb3b24b2dc19fde798b5d14dcc035adfd560bc028c6dc6d` |
| Validation report | `ccee95e7bdf9c3373fa782497bf60377f1445346ad62d40766a0eb685547a2ce` |

The handoff is ignored local research data and is not committed to Git. Its
manifest records all acquisition inputs, candidate-flow exclusions, model and
prompt identities, source/month/format/topic composition, and output hashes.

The acquisition and review sequence was:

~~~powershell
$staging = 'F:\MyProjects\DeAIodorant\data\local\post_reader_staging_v1'
$handoff = 'F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1'

python experiments/acquire_post_candidates.py `
  --output-dir "$staging\infoq" --target 100 --max-attempts 400

python experiments/acquire_meituan_post_candidates.py `
  --output-dir "$staging\meituan"

python experiments/prepare_post_review_candidates.py `
  --input "$staging\infoq\infoq_post_candidates.jsonl" `
  --input "$staging\meituan\meituan_post_candidates.jsonl" `
  --exclude-index F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\analysis_pool.jsonl `
  --output-dir "$staging\review_candidates"

python translation_benchmark_v2.py triage-review `
  --candidate-dir "$staging\review_candidates" `
  --decisions "$staging\review_candidates\no_human_decisions.csv" `
  --output-dir "$staging\triage_qwen38" `
  --model qwen3.8-27b `
  --model-digest 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab `
  --backend openai --endpoint http://192.168.1.200:8000/v1 `
  --concurrency 16 --routing-only

python translation_benchmark_v2.py triage-value `
  --candidate-dir "$staging\review_candidates" `
  --provenance-results "$staging\triage_qwen38\triage_results.jsonl" `
  --output-dir "$staging\triage_qwen38\value" `
  --model qwen3.8-27b `
  --model-digest 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab `
  --backend openai --endpoint http://192.168.1.200:8000/v1 `
  --concurrency 16

python experiments/classify_post_corpus_strata.py `
  --candidate-dir "$staging\review_candidates" `
  --provenance-results "$staging\triage_qwen38\triage_results.jsonl" `
  --value-results "$staging\triage_qwen38\value\value_results.jsonl" `
  --output-dir "$staging\strata_qwen38" `
  --model qwen3.8-27b `
  --model-digest 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab `
  --endpoint http://192.168.1.200:8000/v1 --concurrency 16

python experiments/build_post_reader_handoff.py `
  --candidate-dir "$staging\review_candidates" `
  --provenance-results "$staging\triage_qwen38\triage_results.jsonl" `
  --provenance-manifest "$staging\triage_qwen38\triage_manifest.json" `
  --value-results "$staging\triage_qwen38\value\value_results.jsonl" `
  --value-manifest "$staging\triage_qwen38\value\value_manifest.json" `
  --strata-results "$staging\strata_qwen38\strata_results.jsonl" `
  --strata-manifest "$staging\strata_qwen38\manifest.json" `
  --preparation-manifest "$staging\review_candidates\manifest.json" `
  --acquisition-manifest "$staging\infoq\manifest.json" `
  --acquisition-manifest "$staging\meituan\manifest.json" `
  --output-dir $handoff

python experiments/validate_post_reader_handoff.py `
  --handoff-root $handoff --repository-root . `
  --report "$handoff\validation_report.json"
~~~

The InfoQ collector discovered 79 rather than the requested 100 documents and
therefore returned a nonzero completeness status after writing its staging
artifacts. The combined two-source staging pool nevertheless contained 108
documents, above the frozen minimum of 60 raw candidates; no failed record was
silently admitted.

## Expanded second handoff

A second handoff was generated after reader projects 5 through 7 exposed most
of the useful first-pool documents:

~~~text
F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v2
~~~

It contains 97 unexposed post-period documents across five sources and passes
this validator with zero errors and zero warnings. The role partition was frozen
before new paragraph analysis: 67 development documents and a 30-document
validation reserve. The reserve contains three sources, three formats, and
three topic strata, but still requires multiple independent readers before any
validation claim.

QbitAI, Leiphone, and Huawei Cloud Community were added through public editorial
or recommendation surfaces. Admission required agreement between the local
Qwen3.8-27B baseline and OpenRouter's live weekly-usage number-two identified
model, DeepSeek V4 Flash 0731. Model choice, interface smoke tests, disagreement
rates, value screening, visibility policy, partitioning, and complete artifact
identity are recorded in
[Multi-Source Post Corpus Expansion v2](post-reader-corpus-expansion-v2.md).
