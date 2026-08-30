# Current OpenRouter Corpus-Model Interface Audit

## Purpose

This audit selects model-backed corpus measurements from live OpenRouter
metadata and a fixed task-specific panel. It does not use remembered model
popularity, judge writing features, or treat model agreement as human gold.

## Live model evidence

The public weekly-token ranking was captured on 2026-08-30. The identified
models relevant to this audit were DeepSeek V4 Flash 0731 at position 2,
MiMo-V2.5 at position 3, Hy3 at position 5, and GLM 5.3 Flash at position 8.
Hy4 Preview, Qwen3.8 Max, Qwen3.8 2.4T-A95B, and Qwen3.8 Flash were also
confirmed in the live `/api/v1/models` catalog. Ranking measures usage, not
quality.

## Empty-answer diagnosis

The earlier MiMo-V2.5 and Hy3 smoke calls used a local-server-specific
`chat_template_kwargs.enable_thinking=false` field and a 320-token completion
budget. Exact reproduction yielded:

| Model | Finish reason | Answer characters | Completion tokens | Reasoning tokens |
|---|---|---:|---:|---:|
| MiMo-V2.5 | `length` | 0 | 320 | 319 |
| Hy3 | `length` | 0 | 320 | 320 |

The models did not fail to answer. Reasoning exhausted the allowance before an
answer could be emitted. Explicit OpenRouter reasoning controls and sufficient
budgets produced valid structured output from both models.

GLM 5.3 Flash, Qwen3.8 Max, and Qwen3.8 2.4T-A95B reject disabled reasoning.
They succeeded with low reasoning and a 4,096-token budget. Hy4 Preview
succeeded in an isolated retry but failed 23 of 24 fixed-panel calls because
the Tencent shared upstream pool returned rate-limit errors.

## Fixed panel

The 12-document panel was selected before any model result was available. It
covers five sources, three surface formats, and deterministic provenance and
value cues. It has no human gold labels.

| Artifact | SHA-256 |
|---|---|
| Panel | `50a1275ea9cd235c4b135cff53542897d85f3011eefe150d2de6d81f21719d48` |
| Complete result matrix | `8f67382f662c78f9b68148e37081ffce4e13bb99210be3220de99380b6f515d3` |

Each model received the same frozen foreign-source safeguard prompt and the
same primary research-value prompt.

| Model | Successful calls | Provenance labels: original / excluded | Value labels: substantive / low / uncertain |
|---|---:|---:|---:|
| DeepSeek V4 Flash 0731 | 24/24 | 8 / 4 | 7 / 5 / 0 |
| MiMo-V2.5 | 24/24 | 9 / 3 | 9 / 3 / 0 |
| Hy3 | 24/24 | 10 / 2 | 8 / 3 / 1 |
| Hy4 Preview | 1/24 | unavailable | 1 / 0 / 0 |
| GLM 5.3 Flash | 24/24 | 10 / 2 | 9 / 3 / 0 |
| Qwen3.8 Max | 24/24 | 9 / 3 | 9 / 3 / 0 |
| Qwen3.8 2.4T-A95B | 24/24 | 9 / 3 | 8 / 3 / 1 |

Among the six interface-reliable models, pairwise exact agreement ranges from
9/12 to 12/12 for each task. MiMo-V2.5 and Qwen3.8 Max agree on all 24 panel
labels. GLM 5.3 Flash and Qwen3.8 Max agree on all 12 value labels and 11 of 12
provenance labels. DeepSeek is more exclusionary on this panel. These are
measurement differences, not accuracy estimates.

## Batch policy

The next acquisition batch uses a cost-aware three-model intersection:

1. DeepSeek V4 Flash 0731 and GLM 5.3 Flash run on every deterministic
   candidate;
2. only their high-confidence provenance and value agreements continue;
3. Qwen3.8 Max reviews only those provisional passes;
4. final admission requires high-confidence agreement from all three models;
5. every request error, malformed response, non-high confidence, uncertainty,
   or disagreement fails closed.

Qwen3.8 Max is selected over the 2.4T-A95B endpoint because both have the same
listed price and complete interface success, while Max returned high confidence
on all 24 panel tasks and 2.4T-A95B did not. MiMo and Hy3 remain useful audit
measurements but add no human-gold evidence. Hy4 is excluded from batch work for
current service reliability, not answer quality.

The OpenRouter key is read from an ignored local environment file into process
memory. It is never printed, copied to `gx10`, written into an artifact, or
committed.

## Reproduction

~~~powershell
$env:OPENAI_API_KEY = "<read from ignored local environment>"
$env:PYTHONPATH = "src"
python experiments/compare_openrouter_corpus_models.py `
  --panel <fixed-panel.jsonl> `
  --output-dir <ignored-output-directory> `
  --concurrency 4 `
  --model-spec deepseek/deepseek-v4-flash-0731 disabled 1024 `
  --model-spec xiaomi/mimo-v2.5 disabled 1024 `
  --model-spec tencent/hy3 disabled 1024 `
  --model-spec tencent/hy4-preview low 4096 `
  --model-spec z-ai/glm-5.3-flash low 4096 `
  --model-spec qwen/qwen3.8-max low 4096 `
  --model-spec qwen/qwen3.8-2.4t-a95b low 4096
~~~

Generated prompts, evidence strings, raw corpus excerpts, and API caches remain
in ignored local storage.
