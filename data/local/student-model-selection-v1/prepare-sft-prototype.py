"""用官方模板检查一条开发pair的SFT边界；不下载权重、不启动训练。"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import jinja2
from jinja2.sandbox import ImmutableSandboxedEnvironment

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / "data/local/student-sft-preparation-v1"
if OUT.exists():
    raise SystemExit("SFT开发原型已存在，不覆盖。")
OUT.mkdir()

def save(name, value):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

source_path = ROOT / "data/local/reader-style-anchors-v1/smzdm/analysis-body.txt"
teacher_path = ROOT / "data/local/microduck-readable-transfer-v1/candidate-v2.md"
task = "你是中文信息文章编辑。请将原文完整改写为自然、清楚、便于阅读的中文，减少重复铺垫和机械化表达。保留有用事实、数字、版本、例证、说话者、条件、否定和不确定性，不增加新事实，不缩成摘要。原文代码逐字保留。只输出改写后的完整文章。"
messages = [{"role": "system", "content": task},
            {"role": "user", "content": source_path.read_text(encoding="utf-8")},
            {"role": "assistant", "content": teacher_path.read_text(encoding="utf-8")}]
save("development-pair-prototype.json", {
    "id": "microduck-development-prototype", "messages": messages,
    "source_path": source_path.relative_to(ROOT).as_posix(), "source_sha256": digest(source_path),
    "teacher_path": teacher_path.relative_to(ROOT).as_posix(), "teacher_sha256": digest(teacher_path),
    "teacher_provenance": "原生Astra全文编辑，经过独立内容复核；沿用已获维护者正向反馈的原样稿。",
    "teacher_is_gpt41": False, "split": "development_only", "training_eligible": False,
    "purpose": "验证序列化和loss边界，不把一个开发例子冒充训练集。"
})

def fail(message):
    raise ValueError(message)

environment = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"])
environment.filters["tojson"] = lambda value, **kwargs: json.dumps(value, ensure_ascii=False, **kwargs)
environment.globals["raise_exception"] = fail
checks = []
for model in ["Qwen3.5-4B", "Qwen3.5-9B"]:
    metadata_path = RUN / (model + "-metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    tokenizer = metadata["config"]["tokenizer_config"]
    template_text = tokenizer["chat_template"]
    assert isinstance(template_text, str) and template_text
    template = environment.from_string(template_text)
    arguments = {"tools": None, "enable_thinking": False, "add_vision_id": False,
                 "bos_token": tokenizer.get("bos_token"), "eos_token": tokenizer.get("eos_token")}
    prompt = template.render(messages=messages[:2], add_generation_prompt=True, **arguments)
    full = template.render(messages=messages, add_generation_prompt=False, **arguments)
    prefix_matches = full.startswith(prompt)
    for suffix, text in [("prompt.txt", prompt), ("full.txt", full)]:
        with (OUT / (model + "-" + suffix)).open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    checks.append({"model": metadata["id"], "revision": metadata["sha"],
                   "metadata_sha256": digest(metadata_path),
                   "template_sha256": hashlib.sha256(template_text.encode()).hexdigest(),
                   "prompt_is_exact_prefix_of_full": prefix_matches,
                   "prompt_characters": len(prompt), "full_characters": len(full),
                   "assistant_content_start_char": len(prompt) if prefix_matches else None,
                   "generation_markers_present": "{% generation" in template_text,
                   "token_count": None, "token_level_loss_mask_verified": False,
                   "reason_token_count_missing": "本机tokenizers wheel的官方下载发生TLS握手错误；未关闭证书验证或猜测token数。"})
save("template-check.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(),
     "jinja2_version": jinja2.__version__, "checks": checks,
     "gpu_used": False, "training_started": False,
     "remaining": "在具备tokenizer运行库的训练环境中测token长度，处理可能跨越正文边界的token，确认prompt/padding均为-100；禁用静默截断。"})
print(json.dumps({"checks": checks, "training_started": False}, ensure_ascii=False))
