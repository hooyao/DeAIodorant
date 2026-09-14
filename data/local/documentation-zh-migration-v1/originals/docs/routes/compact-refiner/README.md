# Compact Refiner Route

Route ID: `compact-refiner-v1`  
Route policy version: `1.2`  
Started: 2026-09-14  
Status: downstream refiner planning is retained; active research first follows
the [calibrated feature-discovery objective](../../target-feature-discovery.md).
Previous weak-sample or synthetic experiments do not establish target efficacy.
SFT remains deferred. See the
[human-feedback follow-up](reports/cr001-reader-preview-v1.md) and historical
[CR-001 preflight](reports/cr001-preflight.md).

Latest selection correction: the [Cowork preview is withdrawn](reports/cowork-preview-withdrawal.md).
Completed repairability and preservation checks did not establish adequate
target coverage. Current work rescreens real articles for sustained target
patterns; translated-input product support remains in scope.

## Decision and objective

The maintainer paused the previous corpus-first smell-discovery route and
selected this route on 2026-09-14. Train a compact Chinese editor on accepted
edits, improve it with reliable same-input preferences, and consider online
reinforcement learning only if a validated reward makes it worthwhile.

The product inputs are complete real media articles, including acquired InfoQ
articles. The product objective is greater willingness to continue reading while
preserving meaning, factual claims, qualifications, and authorial voice.
Translated Chinese articles are a required capability, using the Chinese input
alone by default. Translation is a provenance stratum; original-only filtering
is a control view. Source originals, when available, support diagnosis and
verification without becoming a hidden input requirement.
Traditional NLP supplies inexpensive checks and diagnostics. It does not supply
an unvalidated universal smell score or an authorship objective.

```text
traceable real media articles and adequately contrasted reader impressions
    -> repeatable target-feature discovery and counterexamples
    -> bounded edit candidates with whole-article context and unchanged controls
    -> independent preservation review and blinded reader preference
    -> accepted editing dataset
    -> compact-model SFT
    -> held-out comparison with the untuned model and unchanged input
    -> optional DPO on trustworthy preference pairs
    -> optional online RL after reward validation
```

## Canonical records

| Record | Purpose |
|---|---|
| [Data contract](data-contract.md) | Inputs, edits, review evidence, export eligibility, and split boundaries |
| [Evaluation protocol](evaluation.md) | Preservation, reader instrument, baselines, statistics, and promotion gates |
| [Training plan](training.md) | Model selection, SFT, DPO, optional RL, and compute requirements |
| [First batch](first-batch.md) | Concrete scope and completion criteria for the first development batch |
| [Decision log](decisions.md) | Dated decisions, rationale, alternatives, and supersession |
| [Experiment ledger](experiments.md) | Every planned/completed run, failures, and next decisions |
| [Contrast context audit](contrast-context-audit.md) | Whole-article interpretation of the nominated cue and separate reading-defect proposals |
| [Generation-mechanism hypotheses](generation-mechanism-hypotheses.md) | Maintainer-supplied external explanation, competing hypotheses, and causal-evidence limits |
| [Discourse-move analysis](cognitive-move-analysis.md) | Source-linked question, foil, claim, relation, evidence, information update, and stance |
| [Run manifest template](templates/run-manifest.example.json) | Configuration and provenance captured before execution |
| [Experiment report template](templates/experiment-report.md) | Consistent result and failure reporting |
| [Draft prompt](prompts/draft-v1.txt) | First-batch generation prompt |
| [Editor prompt](prompts/editor-v1.txt) | Bounded text-only editing contract |

This directory is the source of current route policy. Repository-level roadmaps
summarize it. Dated legacy reports retain their original evidence; their former
next-step instructions do not schedule active work.

## Scope of the pause

The old low-signal selector probes and stopped reader screens remain paused;
legacy validation reserves remain closed. Acquisition infrastructure, temporal
sampling, and feature discovery remain useful under the calibrated objective.
Preserve existing code, annotations, frozen configurations, and failure reports.

The time-period rules remain active; translation exclusions retain their legacy
scope and no longer discard translated articles from the active research.
The synthetic CR-001 dataset has its own provenance and remains an engineering
pilot, not a replacement for the media corpus. Historical examples can inform
development discussion but are not automatically strong positives, training gold,
or held-out evaluation.

Resuming the paused route requires a maintainer decision recorded here. This is
a research-priority change, not a claim that the old hypotheses were disproved.

## Stage plan

| Stage | Deliverable | Exit condition | Current state |
|---|---|---|---|
| R0: Route setup | Versioned contracts, prompts, run/report templates, and decision record | Cross-links, templates, environment facts, and historical boundaries checked | Complete |
| R1: Development baseline | First batch of 24 independent draft groups; unchanged and edited candidates; review outcomes | Pipeline is reproducible, preservation review is usable, and reader tasks yield interpretable evidence | Three human preview responses recorded; target-smell coverage absent in shown pairs and one preservation concern unresolved |
| R2: Training data | Versioned human-reviewed SFT examples and separately labeled preference records | Rights, group separation, semantic review, unchanged examples, and export validation pass | Not started |
| R3: SFT | One compact model trained on accepted edits | Independent comparison shows useful gain over the untuned model while preserving content | Not started |
| R4: Preference optimization | Optional DPO checkpoint and ablation | Reliable preference data exists and DPO improves over SFT under the same gates | Conditional |
| R5: Online RL | Optional reward model, exploit audit, and bounded training experiment | Reward predicts independent human preference and optimization adds value over DPO | Deferred |
| R6: Product integration | Inspectable edits, intensity control, and per-edit fallback | Evaluation contract is stable and deployment/runtime requirements are met | Deferred |

Data-count budgets are feasibility choices, not claims of statistical power.
R1 is not a validation study. R2 may begin with a working target of 200 accepted
examples, but reaching 200 does not itself authorize promotion or imply model
sufficiency. Evaluation size is set by a prospective power/precision design.

Stages may stop at a successful SFT model. DPO and RL are experiments, not
mandatory upgrades. If a frozen prompt on the untuned compact model already
meets the practical objective, retain that baseline rather than inventing a
training requirement.

## Current environment and execution

Observed on 2026-09-14: Windows, Python 3.13.5, NVIDIA GeForce GTX 1080 with
8192 MiB VRAM, driver 581.57. The maintainer reports no `gx10` access. These are
observations, not a verified training compatibility matrix.

Use the local machine for dataset construction, deterministic checks, diffs,
statistics, and artifact management. The maintainer has excluded the GTX 1080
from SFT and will provide a cloud GPU when training is ready. Before that
handoff, specify minimum and recommended hardware, compatibility, and estimated
runtime/cost using the selected model and training workload, as described in
[the training plan](training.md). No local SFT or cloud provisioning is underway.
OpenRouter is authorized for required inference; a verified cloud training
environment remains a separate prerequisite for R3.

Load `OPENAI_API_KEY` from the ignored root `.env` into the request process only.
Do not print it or include it in manifests. Record source/target model IDs,
provider identity when available, decoding and reasoning settings, prompt
hashes, usage, cost, and errors. Exact reproducibility may be limited when a
provider does not expose checkpoint revisions; disclose that limit.

## Artifact boundaries

```text
docs/routes/compact-refiner/                 tracked policy and run summaries
data/local/compact_refiner/<dataset_version>/ ignored briefs, drafts, edits, labels
feature_runs/compact_refiner/<run_id>/        ignored manifests, diagnostics, diffs
models/compact_refiner/<run_id>/              ignored checkpoints/adapters
benchmark_results/compact_refiner/            future compact, privacy-safe reports
```

The existing ignore rules cover these private artifact directories. Use
repository-relative paths in manifests where possible. Never overwrite a
finished run, a split assignment, or an exported dataset in place. Record a new
version and its parent identity.

## Recording rule

Before each run, copy the manifest template, replace every required placeholder,
record the exact prompts/configuration/input hashes, and add a ledger entry.
After the run, complete a report including exclusions, failures, raw candidate
quality, fallback behavior, and the decision. Human annotation and model-assisted
assessment are distinct provenance classes throughout.

Before outcomes, a protocol revision receives a new version and explanation.
After outcomes, preserve the old run and declare the revision a new development
experiment. Never silently convert an exploratory success into a confirmatory
result. No historical final test is reopened for this route.
