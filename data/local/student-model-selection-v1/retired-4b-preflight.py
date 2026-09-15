"""检查4B学生的云端SFT链路；默认只做离线计划检查。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

ROOT = Path(__file__).resolve().parents[1]
MODEL = "Qwen/Qwen3.5-4B"
REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-cloud-probe", action="store_true")
    parser.add_argument("--pair", type=Path, default=ROOT / "data/local/student-sft-preparation-v1/development-pair-prototype.json")
    parser.add_argument("--output", type=Path, default=ROOT / "models/student-sft-preflight-v1")
    parser.add_argument("--max-length", type=int, default=8192)
    args = parser.parse_args()
    pair = json.loads(args.pair.read_text(encoding="utf-8"))
    assert pair["split"] == "development_only" and not pair["teacher_is_gpt41"]
    for key in ("source", "teacher"):
        assert digest(ROOT / pair[f"{key}_path"]) == pair[f"{key}_sha256"]
    messages = pair["messages"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant"]
    assert all(isinstance(m["content"], str) and m["content"] for m in messages)
    if not args.execute_cloud_probe:
        print(json.dumps({"status": "offline_plan_valid", "model": MODEL, "revision": REVISION,
                          "pair_sha256": digest(args.pair), "max_length": args.max_length,
                          "weights_downloaded": False, "training_started": False}, ensure_ascii=False))
        return
    if platform.system() != "Linux":
        raise SystemExit("此执行模式仅供Linux云GPU；不在当前Windows/GTX1080上训练。")
    if args.output.exists():
        raise SystemExit("输出目录已存在，不覆盖训练检查记录。")
    if args.max_length < 1:
        raise SystemExit("max-length必须为正数。")
    args.output.mkdir(parents=True)
    report = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "model": MODEL,
              "revision": REVISION, "pair_sha256": digest(args.pair),
              "purpose": "单条开发样例的3步兼容检查，不是正式SFT或效果评估", "status": "started"}
    try:
        import importlib.metadata
        import torch
        from peft import LoraConfig, PeftModel, get_peft_model
        from transformers import AutoModelForImageTextToText, AutoTokenizer

        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError("modern_cuda_bf16_gpu_required")
        report["packages"] = {name: importlib.metadata.version(name) for name in ["torch", "transformers", "peft", "accelerate", "tokenizers"]}
        report["gpu"] = {"name": torch.cuda.get_device_name(0), "vram_bytes": torch.cuda.get_device_properties(0).total_memory,
                         "cuda_version": torch.version.cuda}
        torch.manual_seed(20260915)
        cache = ROOT / "models/huggingface-cache"
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False, token=False, cache_dir=cache)
        prefix = tokenizer.apply_chat_template(messages[:2], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, enable_thinking=False)
        if not full.startswith(prefix):
            raise RuntimeError("assistant_prefix_does_not_match_full_template")
        encoded = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True, return_tensors="pt")
        offsets = encoded.pop("offset_mapping")[0].tolist()
        sequence_length = encoded["input_ids"].shape[1]
        report["sequence_tokens"] = sequence_length
        report["assistant_start_char"] = len(prefix)
        if sequence_length > args.max_length:
            raise RuntimeError("full_document_exceeds_max_length_no_truncation_allowed")
        labels = encoded["input_ids"].clone()
        for index, (start, end) in enumerate(offsets):
            if start < len(prefix) or end <= len(prefix):
                labels[0, index] = -100
        report["supervised_tokens"] = int((labels != -100).sum())
        if report["supervised_tokens"] < 1:
            raise RuntimeError("empty_assistant_loss_mask")
        if tokenizer.eos_token_id is not None and encoded["input_ids"][0, -1].item() == tokenizer.eos_token_id:
            labels[0, -1] = tokenizer.eos_token_id
        report["prompt_tokens_masked"] = all(labels[0, i].item() == -100 for i, (start, _) in enumerate(offsets) if start < len(prefix))
        if not report["prompt_tokens_masked"]:
            raise RuntimeError("prompt_loss_leak")
        print(json.dumps({"event": "tokenization_checked", "sequence_tokens": sequence_length,
                          "supervised_tokens": report["supervised_tokens"]}), flush=True)
        model = AutoModelForImageTextToText.from_pretrained(
            MODEL, revision=REVISION, trust_remote_code=False, token=False, cache_dir=cache,
            dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa",
        )
        model.eval()
        prompt_inputs = tokenizer(prefix, add_special_tokens=False, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            baseline_ids = model.generate(**prompt_inputs, max_new_tokens=128, do_sample=False)
        baseline_text = tokenizer.decode(baseline_ids[0, prompt_inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        (args.output / "baseline-short-output.txt").write_text(baseline_text, encoding="utf-8")
        report["baseline_short_generation_nonempty"] = bool(baseline_text.strip())
        if not report["baseline_short_generation_nonempty"]:
            raise RuntimeError("empty_base_generation")
        targets = [name for name, module in model.named_modules()
                   if isinstance(module, torch.nn.Linear) and ".layers." in name
                   and not any(part in name.lower() for part in ["visual", "vision", "lm_head", "mtp"])]
        if not targets:
            raise RuntimeError("no_verified_language_linear_targets")
        model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.0,
                    target_modules=targets, task_type="CAUSAL_LM", bias="none"))
        if any(parameter.requires_grad for name, parameter in model.named_parameters()
               if "visual" in name.lower() or "vision" in name.lower()):
            raise RuntimeError("vision_parameters_unexpectedly_trainable")
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
        model.train()
        report["lora_targets"] = targets
        report["trainable_parameters"] = sum(p.numel() for p in model.parameters() if p.requires_grad)
        batch = {key: value.to("cuda") for key, value in encoded.items()}
        batch["labels"] = labels.to("cuda")
        optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
        report["steps"] = []
        for step in range(3):
            started = time.monotonic()
            optimizer.zero_grad(set_to_none=True)
            loss = model(**batch, use_cache=False).loss
            if not torch.isfinite(loss):
                raise RuntimeError("nonfinite_loss")
            loss.backward()
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            if not grads or not all(torch.isfinite(g).all() for g in grads):
                raise RuntimeError("missing_or_nonfinite_lora_gradient")
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            optimizer.step()
            torch.cuda.synchronize()
            row = {"step": step + 1, "loss": float(loss.detach()), "seconds": time.monotonic() - started}
            report["steps"].append(row)
            print(json.dumps({"event": "probe_step", **row}), flush=True)
        report["peak_vram_allocated_bytes"] = torch.cuda.max_memory_allocated()
        report["peak_vram_reserved_bytes"] = torch.cuda.max_memory_reserved()
        adapter = args.output / "adapter-probe"
        model.save_pretrained(adapter, safe_serialization=True)
        before = {name: parameter.detach().cpu().clone() for name, parameter in model.named_parameters() if "lora_" in name}
        base_model = model.unload()
        reloaded = PeftModel.from_pretrained(base_model, adapter, is_trainable=False)
        after = {name: parameter.detach().cpu() for name, parameter in reloaded.named_parameters() if "lora_" in name}
        if before.keys() != after.keys() or not all(torch.equal(before[name], after[name]) for name in before):
            raise RuntimeError("adapter_reload_mismatch")
        report["adapter_reload_exact"] = True
        reloaded.eval()
        with torch.inference_mode():
            probe_ids = reloaded.generate(**prompt_inputs, max_new_tokens=128, do_sample=False)
        probe_text = tokenizer.decode(probe_ids[0, prompt_inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        (args.output / "probe-short-output.txt").write_text(probe_text, encoding="utf-8")
        report["probe_short_generation_nonempty"] = bool(probe_text.strip())
        if not report["probe_short_generation_nonempty"]:
            raise RuntimeError("empty_reloaded_generation")
        report["status"] = "compatibility_probe_passed"
        report["reading_quality_established"] = False
    except Exception as error:
        report["status"] = "failed"
        report["exception_type"] = type(error).__name__
        if isinstance(error, RuntimeError) and str(error).replace("_", "").isalnum():
            report["reason"] = str(error)
        raise
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
