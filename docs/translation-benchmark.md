# Translation gate benchmark

The translation gate uses two frozen prompt profiles with deterministic
sampling (`temperature=0`, `seed=42`, thinking disabled):

1. a strict translation detector;
2. an original-content verifier, called only when deterministic
   strong-original evidence is present.

The admission policy is fail-closed. A document is accepted only when the
strict profile returns `original/high`, or when strong-original evidence exists
and the verifier also returns `original/high`. Every uncertain, failed, or
malformed response is rejected.

## Local model setup

```bash
ollama pull qwen3.5:9b
```

Run the frozen gate on a private benchmark file:

```bash
python translation_final_test.py \
  --dataset data/translation_holdout/gold.jsonl \
  --results data/qwen9b_validation_results.jsonl \
  --summary data/qwen9b_validation_summary.json \
  --model qwen3.5:9b \
  --timeout 600
```

For an RTX 4080 or DGX Spark, keep the model fully resident and use one process.
The current script evaluates sequentially for reproducibility. Throughput
benchmarking and concurrent production inference should be done separately so
they cannot alter accuracy measurements.

## Private data

`data/` is intentionally excluded from the public repository because it
contains third-party article bodies and local model caches. Copy the following
directories privately to the evaluation machine:

```text
data/translation_eval/
data/translation_holdout/
data/translation_test/
data/translation_benchmark/
```

Do not tune prompts or thresholds after inspecting final-test predictions.

