# Compact Refiner Decision Log

Append decisions with date, authority, rationale, consequence, and status.
Supersede a decision explicitly; do not erase the reason for an earlier run.

## CR-D001: Pause corpus-first smell discovery

- Date: 2026-09-14.
- Authority: explicit maintainer instruction in the project conversation.
- Status: accepted.
- Decision: pause the old pre/post and selector-development route; activate
  compact-editor learning from accepted edits and preferences.
- Rationale: traditional NLP proxies have not supplied a validated smell reward;
  the intended product is a compact model that improves generated Chinese.
- Consequence: keep legacy evidence and reserves unchanged. Their old next-step
  instructions do not override this route. Resume only by a recorded maintainer
  decision.

## CR-D002: SFT before preference optimization; RL conditional

- Date: 2026-09-14.
- Authority: maintainer acceptance of the proposed route.
- Status: accepted.
- Decision: learn editing behavior with reviewed SFT pairs, evaluate, then test
  DPO when trustworthy preference pairs justify it. Online RL is optional and
  requires independently validated reward behavior.
- Alternative deferred: immediately optimize a hand-written NLP smell score.
- Consequence: no reward weights or RL training budget are frozen at this stage.

## CR-D003: Preserve the role of traditional NLP

- Date: 2026-09-14.
- Authority: route implementation of the maintainer's stated motivation.
- Status: accepted route policy.
- Decision: use deterministic checks and traditional features for constraints,
  diagnostics, and later validated auxiliary rewards. Human reading preference
  remains distinct from source-model identity and publication period.
- Consequence: a higher feature reward or a lower marker count alone cannot
  promote a checkpoint. A semantic failure cannot be offset by style gain.

## CR-D004: Separate records and dataset provenance

- Date: 2026-09-14.
- Authority: explicit request to record this route separately.
- Status: accepted.
- Decision: maintain all policy, decision, and experiment records under
  `docs/routes/compact-refiner/`; use new private data/run namespaces.
- Consequence: human labels, assistant proposals, operational checks, and
  synthetic fixtures remain separately attributed. No old example becomes fresh
  validation or human gold through a change of directory.

## CR-D005: Start with a bounded development batch

- Date: 2026-09-14.
- Authority: implementation choice within the authorized route.
- Status: planned; no generation or reader outcomes.
- Decision: start with 24 development groups across four genres, two source
  generators, and unchanged/compact-prompt/assistant candidates at medium
  intensity. Freeze concrete models and run settings before execution.
- Rationale: establish usable edits, checks, and judgments before investing in
  training or another feature battery.
- Consequence: this batch is not held-out evaluation. Working inference caps are
  USD 1 for smoke checks and USD 5 cumulatively for the first batch, subject to
  current price estimation and explicit recording of any revision.

## CR-D006: Verify training compute before choosing a recipe

- Date: 2026-09-14.
- Authority: maintainer's environment correction plus local read-only inspection.
- Status: clarified by CR-D008; cloud execution is selected, sizing unresolved.
- Observed: GTX 1080, 8192 MiB VRAM, driver 581.57, Python 3.13.5; no `gx10`.
- Decision: use OpenRouter for necessary inference; select an open student and
  verify a compatible training host separately. Do not infer training capability
  from API access or model parameter count.
- Consequence: model IDs, training host, actual stack, measured cost, and final
  hyperparameters remain unset until verified.

## CR-D007: Record remaining decisions without inventing answers

- Date: 2026-09-14.
- Status: open items, not permission requests or runtime failures.
- Before CR-001 generation: exact generator/student IDs, provider policy,
  current price snapshot, 24 briefs, and validated pipeline.
- Before reader tasks: actual reviewers, presentation allocation, semantic
  review evidence, and any session deviations.
- Before SFT: training rights/accepted data, verified compute, model license,
  checkpoint identity, frozen training recipe, and evaluation sample design.
- Before DPO/RL: enough reliable preferences; independent reward evidence if RL
  is proposed; stage-specific costs and stop rules.

## CR-D008: Defer training to a maintainer-provided cloud GPU

- Date: 2026-09-14.
- Authority: explicit maintainer clarification after pausing implementation.
- Status: accepted execution constraint; no training scheduled.
- Decision: do not run SFT on the local GTX 1080. The maintainer will supply a
  cloud GPU when the data, model choice, and training plan are ready.
- Required handoff: first give minimum and recommended GPU specifications,
  including count/VRAM, host memory/storage, software compatibility, estimated
  runtime/cost, and the assumptions behind them. Size SFT separately from DPO/RL.
- Consequence: retain route documents as drafts and the numerical training
  recipes as proposals. No local training, cloud rental, or model download is
  initiated by this clarification. Local data/check/evaluation work and authorized
  OpenRouter inference remain the preparation tools.

## CR-D009: Resume autonomous preparation and bounded experiments

- Date: 2026-09-14.
- Authority: explicit maintainer instruction to proceed, delegate experiments,
  and return when there is a concrete finding; request GPU specifications when
  GPU execution becomes necessary.
- Status: accepted.
- Decision: build the reproducible preflight pipeline and run bounded inference;
  use separate agents for fixture construction, client implementation, and
  source/candidate assessment. No agent assessment becomes human preference or
  human training acceptance. SFT and cloud provisioning remain deferred.
- Consequence: source-only fidelity/opportunity review must be saved before
  candidate review. Keep all initial groups in reporting. Human input is sought
  only after a concrete reviewable result exists.

## CR-D010: First live model selection

- Date: 2026-09-14; before paid inference or candidate inspection.
- Status: selected for interface smoke tests, conditional on successful output.
- Catalog: 445 models; snapshot SHA-256
  `6875124fd348cbf584154a4413b8cd8cd01122f0563e048689546a13aa740f2b`.
- Draft generators: `deepseek/deepseek-v4.1-flash` and `qwen/qwen3.8-27b`.
- Compact prompt baseline: `mistralai/ministral-3b-2512` (3B; not a trained model).
- Catalog list prices in USD per million input/output tokens: DeepSeek 0.30/1.20,
  Qwen 0.214/2.55, Ministral 0.10/0.10. Cache/discounts may reduce actual costs;
  cost reservation uses undiscounted capped rates and includes retry exposure.
- Hugging Face metadata identifies MIT for the DeepSeek weights and Apache-2.0
  for Qwen and Ministral. Metadata snapshots are private run artifacts; provider
  API terms and unknown served checkpoint revisions remain distinct limitations.
- Ministral repository revision observed:
  `b35d4dfe56c142746f54dbd64f579faab2744308`. This is a potential later trainable
  base, not proof that the remote provider serves those exact bytes.
- Rationale: two current generator families and a genuinely compact available
  baseline with identifiable trainable weights. This is not a popularity ranking
  or a final student choice. Keep the USD 5 total development cap.

## CR-D011: Account for source API attrition before editing

- Date: 2026-09-14; after source outcomes, before compact-editor outcomes.
- Status: executed development amendment, not a confirmatory protocol.
- Decision: preserve source 23 as operationally unavailable after bounded HTTP 429
  attempts and a documented cooldown recovery. Keep all 24 planned groups in the
  denominator; review the 23 actual drafts and freeze a separate edit stage for
  the 13 source-pass groups.
- Consequence: preserve the original run manifest and every failed attempt;
  never fill the missing draft, label it a semantic failure, or silently replace
  its generator. Source review is model-assisted, not human admission gold.

## CR-D012: Test a second untuned baseline before attributing need to SFT

- Date: 2026-09-14; exploratory follow-up after initial preflight observations.
- Status: executed as CR-001B.
- Decision: use `qwen/qwen3.5-9b` on exactly the same 13 editor inputs, with a
  separately frozen manifest, one attempt per case, and fresh blinded review.
- Rationale: a poor 3B baseline is insufficient evidence that every compact model
  needs training. The 9B model is a capacity/language-family control, not a final
  student or a substitute for the original baseline.
- Consequence: retain all results. Different families, sizes, providers, and
  review agents limit causal interpretation; no fine-tuning gain was measured.

## CR-D013: Preserve evidence and request only targeted human feedback

- Date: 2026-09-14.
- Status: model-only preflight completed; human review pending.
- Decision: do not start SFT or request a GPU yet. Keep the few safe, concrete
  edit proposals and the failure examples. Prepare a three-pair qualitative
  reader preview rather than label agent opinions as human preference.
- Evidence: primary preservation passes were 2/13 for Ministral 3B, 13/13 for the
  independently authored agent proposals, and 8/13 for Qwen3.5-9B with three
  uncertain cases. These are model-assisted development assessments, not
  validated accuracy or reader-preference rates.
- Next priority: establish whether the reader values the proposed edits, compare
  suitable Chinese student baselines, and collect accepted edit/no-edit data.
  Training hardware is specified only when the workload and data are ready.

## CR-D014: Repair rate-limit handling after freezing experiment evidence

- Date: 2026-09-14, after all API experiment calls.
- Status: separate client maintenance.
- Decision: preserve the measurement implementation in an exact private code
  snapshot and update future client behavior to honor Retry-After deadlines,
  including deferred retry rather than long blocking sleeps or early calls.
- Consequence: new behavior has separate tests and provenance; it does not
  retroactively change CR-001 or CR-001B outputs, charges, or failures.

## CR-D015: Record human preferences without overstating their meaning

- Date: 2026-09-14.
- Authority: direct maintainer feedback on the three-pair preview.
- Status: recorded as qualitative development evidence.
- Observation: the chosen sides A/B/A all map to revisions, but pair 1 carries
  an unresolved content-difference concern and pair 3 is only slightly preferred.
  The reader reports no obvious smell in any of the displayed pairs.
- Decision: preserve every original response and the set-level comment. Do not
  report three validated wins, certify preservation, force the slight preference
  into a tie, or turn no-obvious-smell observations into automatic keep labels.
- Consequence: separate feedback/summary files supplement the unchanged
  pre-human artifacts. Pair 1 remains excluded from preservation-passing
  outcomes; all training exports remain empty.

## CR-D016: Establish target coverage before another smell-removal comparison

- Date: 2026-09-14.
- Authority: methodological response to CR-D015 within the selected route.
- Status: next-step requirement; no new batch or model run started.
- Decision: retain this notice/instruction batch as an engineering and ordinary
  editing pilot. Before another smell-removal experiment, inspect original-only
  realistic generated drafts and establish the reader's target coverage
  separately from reading preference and preservation. Do not manufacture bad
  prose, tune against the legacy reserve, or treat agent triage as human gold.
- Consequence: no new large annotation batch, reward, SFT run, or GPU request.
  Low-smell cases remain useful controls; the old corpus-first route stays paused.

## CR-D017: Use real media as the product input distribution

- Date: 2026-09-14.
- Authority: explicit maintainer confirmation of the calibrated project goal.
- Status: governing scope correction.
- Decision: complete real Chinese media articles such as acquired InfoQ articles
  are the target. Synthetic notices or prompted articles remain auxiliary
  engineering material. Preserve prior corpus, annotations, tools, and results.
- Consequence: CR-002 synthetic article tasks remain saved but unexecuted; no
  target-media effect is inferred from CR-001. Source identity and full-context
  audits may proceed without turning those sources into strong-positive labels.

## CR-D018: Restore adequately sampled feature discovery as the front half

- Date: 2026-09-14.
- Authority: maintainer clarification that subjective smell must first be
  characterized, that earlier annotation samples were too weak, and that the
  acquisition/time framework remains valuable.
- Status: active research priority; supersedes the generated-source/immediate-
  editing next steps in CR-D016 and earlier route drafts.
- Decision: follow [the calibrated evidence plan](../../target-feature-discovery.md).
  Retain the pre-2023 baseline, separate transition interval, and post-2025-06
  cohort. Seek an adequate real-media perceptual contrast before new feature or
  edit-efficacy claims. Do not demand that the reader invent the feature rules.
- Consequence: old local preferences are not confirmed strong-positive labels;
  earlier calculations remain historical. Low-signal probes and training stay
  paused. Bounded source staging and integrity work can reuse prior acquisition
  infrastructure, with raw candidates unadmitted until their gates are checked.
- Scientific boundary: the July 2025 transition is a sampling hypothesis and
  maintainer observation, not a measured discontinuity. Date does not certify
  individual authorship or smell severity.

## CR-D019: Measure the nominated contrast family and retain both product targets

- Date: 2026-09-14.
- Authority: direct maintainer reflection and an explicit request for pre-2023
  versus post-June-2025 counts of the broader `而是` construction family.
- Decision: distinguish aversive cues from actual reading defects and address
  both. Run a bounded non-LLM descriptive count under
  [the dedicated protocol](ershi-cohort-statistics.md), preserving all variants
  in the literal count and reporting lexical categories separately.
- Evidence boundary: the reader calls the current article difficult and
  translationese-like, with weak AI smell. It is not a confirmed strong positive,
  and that language judgment is not a translation-provenance label.
- Consequence: no syntactic error count, logical-disconnection label, composite
  reward, or safe rewrite rule is inferred from the literal statistic. Chinese
  argument omission must be evaluated in context. SFT remains downstream.

## CR-D020: Audit semantic contribution and underlying reading defects

- Date: 2026-09-14.
- Authority: maintainer authorized the proposed next-step context audit.
- Decision: freeze [the context protocol](contrast-context-audit.md), inspect
  all 57 occurrences in 13 complete source bodies, retain zero-count documents
  in concentration diagnostics, and preserve two independent assistant reviews.
- Boundary: exact evidence and agreement establish auditability and assistant
  consistency, not reader validity. Do not turn redundant-looking presentation
  into deletion instructions or training rewards.
- Source correction: one reviewed long interview explicitly discloses
  translation. A separate provenance addendum will correct the primary count
  population; raw original statistics and review packets remain frozen.

## CR-D021: Preserve translated media as a separate diagnostic group

- Date: 2026-09-14.
- Authority: maintainer explains that poor English LLM writing may be translated
  into Chinese with further defects; supplied Gemini discussions are reference.
- Decision: preserve original-only temporal exclusions while including
  translated media in a separately recorded product-diagnostic group. Inspect
  upstream information and reasoning as well as downstream Chinese syntax.
- Boundary: no article is labeled LLM-authored or LLM-translated by style.
  Determine inherited versus added defects only with actual paired evidence.
  Reward optimization, synthetic-data inheritance, and cross-language projection
  remain candidate mechanisms in [the reference record](generation-mechanism-hypotheses.md).

## CR-D022: Replace blanket exclusion with provenance-stratified research

- Date: 2026-09-14, superseding the primary-filter emphasis in CR-D021.
- Authority: maintainer explicitly critiques the previous blanket translation
  exclusion, requires automatic translated-Chinese refinement, and delegates
  research direction.
- Decision: study direct Chinese, translations, mixed/adapted, and unresolved
  provenance. Keep temporal cohorts within these strata and original-only
  controls separately. Preserve earlier exclusions and frozen results without
  treating them as global research rejection.
- Product contract: the compact model accepts complete Chinese articles,
  including translations, without requiring an English original. Training and
  evaluation must cover translated input, unchanged good translations, and
  preservation. Upstream sources are optional verification/curation evidence;
  all translations and adaptations share a leakage-control group.
- Execution: pursue source-linked repetitive framing, sentence/reference
  defects, and unsupported discourse relations, followed by bounded repair
  development. Neither low readability nor provenance uncertainty discards a
  research case; provenance uncertainty never certifies originality.
- Boundary: missing information cannot be invented. SFT, DPO, and NLP rewards
  remain conditional on reviewed data and independent reader outcomes.

## CR-D023: Withdraw Cowork and stop substituting repairability for target coverage

- Date: 2026-09-14.
- Authority: maintainer rejects repeatedly using Cowork, then clarifies that
  inherited English LLM problems do not make it a strongly characteristic
  Chinese target example.
- Diagnosis: the assistant anchored on available text, localized grammar
  defects, and completed tooling, then used the translated-input requirement
  to justify another weak-sample reader request. This repeats the earlier
  selection failure despite the known low-smell assessment.
- Decision: withdraw the Cowork preview without inferring a preference outcome.
  Preserve all artifacts and exact feedback. Do not reissue it as a readability
  question or automatically replace it with another edited development article.
- Priority: inspect real complete Chinese articles for sustained target-style
  manifestations before edits or reader requests. Provenance is context;
  translated origin neither guarantees nor rules out those manifestations.
  Translated-input training/evaluation remains required downstream.

## CR-D024: Use the supplied strong anchor and preserve its relative severity

- Date: 2026-09-14.
- Authority: maintainer supplies the SMZDM Microduck article as `极其臭`, then
  explicitly contrasts Baidu `一般臭` with SMZDM `恶臭`.
- Decision: make SMZDM the primary strong-positive discovery anchor and Baidu
  the lower-intensity reference. Do not repeat either rating question or promote
  the prior assistant nomination into a stronger human label than was given.
- Evidence: preserve source HTML, DOM blocks, citation attributes, publication
  metadata, publisher AI disclosure, exact human wording, and separate
  label-conditioned style and claim/relation analyses.
- Consequence: the zero-literal-connector strong anchor requires a broader
  linguistic account. Study recurring parallel verdicts, insider/directive
  stance, and inference/reference problems in context; no forbidden-word list,
  SVO-presence rule, scalar reward, or immediate SFT is justified.

## CR-D025: Explain rhetorical behavior and require surface-form invariance

- Date: 2026-09-14.
- Authority: maintainer retains contrastive framing as a strong signal,
  identifies a bare-copula equivalent and the title-level agenda frame, and
  rejects an explanation confined to the literal connective.
- Decision: prioritize the rhetorical action and its semantic/evidential
  function. Investigate unmotivated corrective framing and prepackaged insight
  as hypotheses; do not claim an identified RLHF or other training cause.
- Measurement consequence: eventual diagnostics must withstand connective-only
  substitutions and distinguish necessary contrasts from unsupported or
  repeatedly ornamental ones. A keyword-only improvement is not product gain.
- Current scope: the new narrow lexical measurement draft is retained
  unexecuted. No extra human rating, rewrite, reward, or training follows from
  these localized observations alone.
