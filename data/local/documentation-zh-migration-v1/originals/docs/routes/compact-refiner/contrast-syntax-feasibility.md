# Local Syntax Parser Feasibility

Protocol: `contrast-syntax-feasibility-1.0`. Date: 2026-09-14.
Status: exploratory protocol frozen before this parser run and its case
inspection. This is a feasibility study of local CPU parsing as an aid to
concrete reading-defect inspection, not syntax-error prevalence or reader
validation. No historical aggregate writing-quality score is reinstated.

## Purposive inputs

Parse the complete, unchanged exact bodies of these existing neutral packets
from `data/local/contrast-context-v1/packets/`:

- `doc-03`: a dense technical announcement.
- `doc-05`: the maintainer's difficult Cowork example, whose existing weak-smell
  assessment remains unchanged.
- `doc-11`: a low-marker technical-practice control.

Selection is intentional and informed by these descriptions. It is not random,
representative, independent validation, or a temporal-cohort comparison. Keep
all three documents even if the parser finds no usable distinction. Do not read
semantic reviewer outputs. Existing corpus admission and capture limitations
remain unresolved.

## Execution and preserved evidence

Use the already installed Stanza `zh-hans` / `gsdsimp` model with
`tokenize,pos,lemma,depparse`. Require `DownloadMethod.NONE`, CPU inference,
one PyTorch computation thread, one interoperation thread, deterministic
algorithms, and seed `20260914`; make no downloads or external API calls. Reuse
the repository backend's determinism, package-version, and model-fingerprint
helpers. A missing or incompatible local model is a reported feasibility
failure, not permission to fetch a replacement. Stanza is an existing optional
dependency; this study adds no model, dependency, service, or training cost.
Existing software/model licenses are unchanged and no weights are redistributed.

Hash-check bodies and occurrence packets against the preparation manifest.
Preserve exact source bytes, including extractor-inserted line breaks; do not
join lines, normalize punctuation, or correct text before parsing. Save complete
sentence/token/word records privately, including Universal Dependencies heads,
relations, tags, available token and word character offsets, exact sentence
source slices, and intervening source gaps. Offsets use zero-based,
end-exclusive Python Unicode positions. Record any unavailable offsets and
segmentation mismatch; never silently invent coordinates. Save CoNLL-U as an
additional inspection format.

The immutable parse manifest records code/protocol/input/model-file hashes,
model fingerprint, package and Python versions, seed, CPU/thread choices,
per-document completion counts and elapsed time, and output hashes. Progress
logs contain document IDs and processing counts only. Check process liveness,
CPU time, and progress artifacts if execution exceeds one minute, with further
checks spread across the remaining run. Do not rely on a watcher alone.

## Case inspection

Read each full original body and its annotations. Within each document, inspect
one concrete awkward construction and one ordinary ellipsis or other coherent
control when supported. Do not force a defect or a matched pair where the body
does not support one. Record exact source evidence and offsets, the selected
UD analysis, the reading issue or coherent interpretation, and whether the
parser actually distinguishes them. Parser structure alone cannot establish
missing discourse premises, factual accuracy, redundant opposition, meaning
preservation, or reader dislike.

An absent overt subject is not an error label. Chinese ellipsis, shared
subjects, topic-comment structure, intransitives, headings, and lists may be
ordinary. Inspect attachment ambiguity and tokenization/segmentation errors
before interpreting dependency structure. Extractor line breaks and article
formatting may cause parser boundaries that do not match linguistic sentences;
retain evidence of those failures rather than repairing the input.

Case judgments are assistant-assisted, exploratory observations with
`human_gold: false`; no automatic defect score, prevalence denominator, edits,
new variants, training labels, efficacy conclusion, or smell-status promotion
is produced. Success means that parsing executes reproducibly and yields
traceable evidence, not that the model diagnoses prose quality.

## Reproduction and outputs

```powershell
python experiments/contrast_syntax_feasibility.py --model-dir models/stanza --output-dir data/local/contrast-syntax-v1
```

The output directory must be new. Full annotations, source copies, manifest,
runtime counts, and later `inspection.json` / `feasibility-report.md` remain
private under this ignored directory. Independent case inspection is recorded
separately from immutable parser outputs and receives its own provenance and
artifact hashes. This protocol remains unchanged after the run.
