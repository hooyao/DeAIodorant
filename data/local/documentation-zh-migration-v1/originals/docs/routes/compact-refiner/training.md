# Compact Refiner Training Plan

Draft policy version: `compact-refiner-training-1.1`. No base checkpoint,
training backend, or hyperparameter configuration has been selected or run.
The numerical recipes below are planning proposals, not authorization to begin
training or settled hardware requirements.

## Model roles

Separate the draft generator, candidate editor, compact student, preservation
reviewer, and preference reader. A model serving more than one role is recorded
explicitly. Self-consistency is not independent human validation.

The active assistant can develop the editing policy and propose carefully
audited candidates directly. Additional OpenRouter calls serve a concrete need
such as diverse source drafts or a reproducible compact-model baseline. Do not
pay for extra models merely to obtain a majority vote that resembles gold.

The compact student learns to revise complete real Chinese media articles,
including translations, while preserving source claims and useful information.
The earlier factual-brief generation tasks are auxiliary engineering records.
Do not train article-authorship classification or use old human writing as an
unpaired target for arbitrary new content.

## Required translated-input capability

The maintainer explicitly requires automatic optimization of translated Chinese
articles. The standard input is Chinese text; a foreign original is optional.
Cover both direct-Chinese and translated/mixed inputs in accepted training and
independent evaluation, retaining unresolved provenance as unknown.

Include concrete Chinese sentence/reference repairs, repetitive discourse
framing, and information-progression problems that can be repaired from existing
content. Include coherent translations that should remain unchanged. Do not
remove technical distinctions, compress away qualifications, or invent absent
premises to make a translation sound natural.

When source originals aid curation, keep the source, translation, reprints,
adaptations, and all edits in one provenance group and split. Source-assisted
curation cannot leak the original into a Chinese-only evaluation input. A
separate optional-source arm needs its own disclosed input contract.

Training readiness requires reviewed translated-input examples and an independent
translated-input evaluation plan. Report useful preference, preservation,
fallback, and coverage in that stratum. Success restricted to direct-Chinese
articles does not satisfy the requested product scope.

## Student selection

Start by evaluating an openly trainable Chinese-capable instruction checkpoint
in roughly the 1.5B-4B range. This is a search range, not a claim that every
model fits the observed GPU or can solve the task. Compare larger students only
if a recorded failure justifies the added cost.

Before selecting a checkpoint, record:

- exact repository ID/revision, tokenizer, chat template, and special tokens;
- weight availability and license for adaptation and intended distribution;
- Chinese editing quality on development inputs;
- context length and complete-input/output token requirements;
- supported precision, quantization, kernels, and training-stack compatibility;
- measured memory, throughput, failures, and cost on the proposed host.

A hosted model name is not sufficient proof of an identical trainable revision.
Record when an OpenRouter prompt baseline is only an approximate counterpart.
Final training attribution requires an untuned baseline from the actual selected
base checkpoint under the same evaluation policy.

## Compute prerequisite

The maintainer confirmed on 2026-09-14 that the local GTX 1080 is not to be used
for SFT and that a cloud GPU will be supplied when training is ready. There is no
`gx10`. Local work is data preparation, checks, statistics, and artifact handling;
OpenRouter supplies the authorized inference route. No training host has been
provided and no training has begun.

Before the maintainer selects the cloud instance, prepare a workload-specific
hardware brief with two options: the minimum workable configuration and the
recommended configuration with memory/runtime margin. Include:

- GPU model or required capabilities, GPU count, and VRAM per GPU;
- selected base checkpoint/parameter count, precision, and LoRA/QLoRA/full-tuning
  method; do not estimate solely from parameter count;
- maximum complete sequence length, microbatch, gradient accumulation, effective
  batch size, optimizer, and memory-saving assumptions;
- host CPU/RAM, working storage, checkpoint retention, and download requirements;
- compatible OS, Python, CUDA/driver, framework, and kernel versions;
- estimated throughput, total GPU-hours, price assumptions, and total cost;
- what remains uncertain and the smoke test needed to verify the estimate.

Account for weights, optimizer states, gradients, activations, temporary buffers,
and memory margin. State whether the estimate covers SFT only; DPO reference
storage and any later RL rollout/reward workload require separate sizing.

Do not name a firm VRAM requirement before selecting the model and workload.
After the cloud host is provided, verify a pinned environment and a complete
forward/backward/checkpoint smoke test before dataset-scale execution. Python
3.13.5 on the local machine is not a training-stack requirement. API inference
access does not itself provide fine-tuning or exportable weights.

## R2: Accepted-edit data

Build the human-reviewed export defined in [the data contract](data-contract.md).
The first working collection budget is 200 accepted records, including genuine
unchanged cases and a range of edit sizes. Track independent groups separately
from examples. This budget is adjustable during declared development and is
not a minimum data theorem or a promotion threshold.

An initial training run may reveal that data coverage, semantic review, or
label consistency is inadequate. Expand those dimensions before increasing
model size or introducing RL. Keep unreviewed assistant/model edits in a
separate proposal pool. No synthetic acceptance labels are silently promoted.

## R3: Supervised fine-tuning

Use the same student input contract in training and evaluation: task instruction,
legitimate context/locks, intensity, and original passage. Train the model to
return only the revised or unchanged passage. Mask loss on the input and apply
it to the target response. Do not train on private model reasoning, reviewer
notes, feature scores, or answer keys.

Start with parameter-efficient adaptation if the selected stack supports it.
Keep one base model and one initial recipe to make failures interpretable.

The following are provisional starting values, to be frozen in the actual run
manifest after the hardware smoke test and before training:

| Setting | Starting proposal |
|---|---|
| Method | LoRA; QLoRA only after compatibility is demonstrated |
| Rank / alpha / dropout | 16 / 32 / 0.05 |
| Target modules | Selected attention projection modules, resolved against the actual architecture |
| Learning rate | `1e-4` |
| Epochs | 1 initially |
| Effective batch size | 16 groups/examples, with actual grouping and accumulation recorded |
| Sequence length | Determine from complete real article input-plus-output token lengths using the pinned tokenizer; 4096 is not a default for this corpus |
| Seed | `20260914` |
| Precision and optimizer | Chosen by measured compatibility; never inferred from an old command |

No silent truncation is allowed. An example that exceeds the verified token
budget is either excluded with a reason or segmented under a versioned policy
that retains required context and group identity. Do not pack examples in a way
that exposes another example's target or permits cross-example attention.

The current translated-interview development case alone has 21,891 Unicode
characters (17,540 counted CJK characters) before any revised response. These
are character counts, not tokenizer measurements. They make the synthetic
pilot's short-context assumptions unsuitable for hardware sizing. Measure
complete input-plus-target lengths and choose a supported long-context recipe
or a separately evaluated context-preserving segmentation policy before
requesting GPU specifications.

Freeze validation schedule, checkpoint selection rule, and training budget before
the run. Keep the candidate search small and recorded; no final-test feedback
enters learning-rate, prompt, checkpoint, or stopping decisions. A checkpoint is
not promoted merely because training loss falls.

Save the adapter, base revision, tokenizer/template, export hash, effective
configuration, dependency snapshot, seeds, training log, and checkpoint hashes.
Report train/validation loss alongside reader and preservation outcomes. A
failed or interrupted run remains a ledger entry.

## R4: Direct preference optimization

DPO is an offline preference-learning step; it does not require an online
hand-written scalar reward. Begin only after SFT has usable editing behavior
and decisive, reliable same-input human preferences have accumulated.

Initialize from the selected SFT checkpoint and use an immutable copy of that
checkpoint as the reference. Both candidates in a style preference pair must
pass preservation. Keep unsafe outputs in a separate challenge/audit set so
style preference is not conflated with factual correctness. Ties, both-bad
answers, unknown judgments, and unresolved reviewer disagreements are excluded
from binary DPO pairs with their counts retained.

A first provisional recipe is beta `0.1`, learning rate `1e-5`, one epoch,
effective batch size 8, and seed `20260914`. Resolve actual adapter modules,
precision, sequence handling, optimizer, and reference storage in the run
manifest before execution. These defaults may change on development evidence,
but every change is recorded; they are not already validated hyperparameters.

Monitor response length, unnecessary rewriting, lost voice, factual failures,
and chosen/rejected log-probability behavior. Preference optimization can exploit
length or annotation bias even without an explicit reward model. Compare DPO
against its SFT parent on the same independent evaluation protocol.

## R5: Conditions for online reinforcement learning

Online RL is deferred. Its reward need not be differentiable or based on
traditional NLP; a cheap scalar is convenient, but cheap computation says nothing
about alignment with reader preference.

Before an RL run, require:

1. a frozen reward with evidence on independent human preferences;
2. preservation checks with a documented miss rate and human audit;
3. the exploitation tests and feature ablations in [evaluation](evaluation.md);
4. comparison against SFT and DPO, including output length and edit coverage;
5. a fixed rollout/token/cost budget, reference policy, optimization settings,
   interruption behavior, and rollback checkpoint.

Use reader preference as the quality target. Traditional NLP may contribute
validated auxiliary signals; penalties for literal changes and excessive edits
are incomplete safety signals. Never trade a critical semantic failure for a
better style score. Runtime acceptance must still reject or revert failed edits.

Stop if reward improves while independent reader preference stalls, content
failures rise, outputs collapse to one style, or no-edit behavior dominates.
Keep the simpler checkpoint if online RL adds no useful gain.

## Inference operations

For the first batch, start with one request at a time, a 120-second request
timeout, and at most two retries per item. Retry only transient failures, respect
service retry instructions, and record every attempt and its cost. A truncated
or empty answer is a failed candidate; never substitute hidden reasoning text.
Do not change token limits or prompts invisibly during a run.

Use a conservative working spending cap of USD 1 for the initial interface smoke
test and USD 5 cumulatively for the first development-batch inference. These are
agent-selected operating limits within the existing authorization, not price
quotes. Fetch current model prices and estimate worst-case request cost before
launch. Stop when the cap would be exceeded; record a revised budget decision
before continuing. Actual calls, failed-attempt reservations, and cost are
recorded in the [experiment report](reports/cr001-preflight.md).

For any long-running generation/training job, inspect the actual process/log or
provider job state after about one minute and approximately five times across
its expected duration. A watcher is supplementary; completion comes from exit
status, terminal markers, and validated artifacts. Never relaunch into the same
mutable cache while an earlier writer may still be alive.
