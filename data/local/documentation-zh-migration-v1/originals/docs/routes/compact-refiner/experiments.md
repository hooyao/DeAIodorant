# Compact Refiner Experiment Ledger

This ledger contains only the new route. A planned record is not an executed
experiment. Reference full manifests/reports by path and hash when they exist.

| ID | Date | Stage | State | Inputs / output | Decision |
|---|---|---|---|---|---|
| CR-000 | 2026-09-14 | R0 | completed | Route contracts, prompts, templates, client/record utilities, and environment inspection | Autonomous preflight authorized; legacy route paused and SFT deferred |
| CR-001 | 2026-09-14 | R1 | preflight complete; target coverage unresolved | [Preflight report](reports/cr001-preflight.md): 24 groups planned, 23 generated, 13 source-pass groups, 26 P/T candidates | Human follow-up is recorded separately; no training acceptance or smell-removal validation |
| CR-001B | 2026-09-14 | R1 | completed; model-only | Same 13 editor inputs, Qwen3.5-9B capacity control, 13 outputs and blinded agent review | Do not infer all compact-model behavior from the 3B baseline; no SFT benefit measured |
| CR-001-preview-1 | 2026-09-14 | R1 | qualitative feedback recorded | [Human feedback](reports/cr001-reader-preview-v1.md): A/B/A, with a content concern on pair 1 and slight preference on pair 3 | All shown pairs lack obvious smell according to the reader; establish target coverage before another smell-removal comparison |
| Media-contrast-staging-v1 | 2026-09-14 | Target discovery | Source staging and qualitative feedback recorded | [New media calibration](reports/media-contrast-calibration-v1.md): 24 responses, 20 nonempty bodies, 16 remaining after translation flags; no admissions | Reader describes nominated article as weak in AI smell but difficult/translationese-like; it is not a confirmed strong positive |
| Ershi-cohort-v1 | 2026-09-14 | Target discovery | Descriptive count complete | [Contrast-family statistics](reports/ershi-cohort-statistics-v1.md): known-translation-excluded InfoQ pre 5/17 and post 52/18 occurrences/articles; independent byte-identical reproduction | Retain as a reader-nominated cue hypothesis; no quality reward or edit rule validated |
| Contrast-context-v1 | 2026-09-14 | Target discovery | completed | [Whole-article audit](reports/contrast-context-audit-v1.md): two reviews, 57 occurrences/13 complete documents; exact evidence validated; preparation reproduced | Agreement is model consistency only; 8 shared repetition candidates, no human smell labels |
| Contrast-syntax-v1 | 2026-09-14 | Parser feasibility | completed | [CPU protocol](contrast-syntax-feasibility.md): 3 bodies, 164 parser sentences, 5,602 words; two byte-identical successful runs; failed launcher preserved | Parser is an inspection aid; no missing-subject or complete-tree quality rule |
| Provenance-stratified-contrast-v1 | 2026-09-14 | Target discovery | completed | [Retained-media count and correction](reports/contrast-context-audit-v1.md): all 40 InfoQ bodies retained; one newly documented translation | Translation becomes a provenance stratum; unresolved does not mean original |
| Media-repair-development-v1 | 2026-09-14 | Editing development | completed; reader preview withdrawn | [Development result](reports/media-repair-development-v1.md) retained; [sample rejection](reports/cowork-preview-withdrawal.md) supersedes the Cowork reader request | Engineering evidence only; no human preference, smell-efficacy claim, acceptance, export, or training |
| Target-coverage-rescreen-v1 | 2026-09-14 | Target discovery | completed | [Rescreen result](reports/target-coverage-rescreen-v1.md): twelve complete bodies; zero sustained nominations, nine weak/ambiguous and three poor-format fits | Preserve the coverage gap; no replacement reader task or rewrite follows |
| Cowork-reader-preview-v1 | 2026-09-14 | Reader preview | cancelled | [Withdrawal](reports/cowork-preview-withdrawal.md): exact maintainer sample-rejection feedback in preview v1.1 sidecar | No preference or readability outcome inferred; do not reissue |
| Targeted-media-discovery-v1 | 2026-09-14 | Target discovery | completed; reader feedback recorded | [One-article discovery](reports/targeted-media-discovery-v1.md); maintainer later calls Baidu `一般臭` | Lower-intensity reference in the supplied pair; no rewrite or efficacy claim |
| Reader-anchor-feature-discovery-v1 | 2026-09-14 | Target discovery | completed exploratory analysis | [Strong-anchor report](reports/reader-anchor-feature-discovery-v1.md): human severe SMZDM versus general-smell Baidu; 30/64 full blocks, four style families and four relation findings | Human severity is supplied; mechanisms and measurements remain exploratory; no repeated rating, edit, reward, or training |
| Cognitive-move-analysis-v1 | 2026-09-14 | Operationalization | completed worked annotation | [Six source-linked cases](reports/cognitive-move-analysis-v1.md), revised focus/context boundaries and exact source validation | Descriptive semantic records with controls; no automatic detector, scalar score, intervention, or training result |
| Media-provenance-extension-v1 | 2026-09-14 | Independent acquisition/diagnostics | completed | [Extension result](reports/media-provenance-extension-v1.md): 24 fixed GETs, 21 nonempty unique texts; pre 9 documents/2 occurrences, post 12/28; 3 translated post items retained | Existing literal/concentration definitions reproduced; one long interview contributes 19/28 post occurrences; no smell or authorship labels |

## CR-000: Route initialization

Purpose: record the maintainer's route change and make the new workflow
independently understandable and reproducible.

Artifacts are listed in the [route index](README.md). The observed
environment is Windows with Python 3.13.5 and an NVIDIA GeForce GTX 1080,
8192 MiB VRAM, driver 581.57. No inference calls, model downloads, training,
reader tasks, or new corpus acquisition were executed for CR-000.

Route links, template JSON, prompt fields, fixture identity, credential exclusion,
and whitespace were checked. The pre-maintenance implementation passed 90
offline tests and compilation. This verifies engineering behavior, not reader
benefit. Subsequent client-backoff maintenance has its own validation record;
the final full suite passed 113 tests and compilation.

The maintainer clarified that SFT will use a cloud GPU they provide. Before
provisioning, supply workload-specific minimum/recommended hardware and
runtime/cost estimates under CR-D008. The maintainer later resumed API experiments
under CR-D009; training remains deferred.

Historical worktree changes from the preceding reassessment remain separate:
`docs/research-reassessment-2026-09-14.md` and its earlier documentation edits
are not CR-001 results. Git `init` remains the development branch.

## Required entry for each subsequent run

Record run ID, stage, protocol/config version, state, start/end time, code/input
identity, actual commands, model/host identity, output hashes, review status,
cost, failures, exclusions, report link, and next decision. Valid states are
`planned`, `running`, `awaiting_review`, `completed`, `failed`, and `cancelled`.

Do not call a run completed merely because an API request or training process
exited successfully. Validate its required artifacts and report missing evidence.
