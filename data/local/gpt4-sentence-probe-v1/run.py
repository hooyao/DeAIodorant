"""记录维护者指定的单句 GPT-4 改写；冻结输入，不覆盖结果或自动重试。"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.openrouter import OpenRouterClient, OpenRouterError

def save(name, value):
    with (RUN / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

if (RUN / "request.json").exists():
    raise SystemExit("该次请求已有记录；不覆盖或再次付费。")

sentence = "2.7.x的第一个稳定版什么时候来，已经有玩家在评论区问“不知道今年过年能不能玩到亡灵遗产稳定版”"
prompt = "请将下面这句话改写得自然、通顺，保留原意，不补充原文没有的信息。只输出改写结果。\n\n" + sentence
model_id = "openai/gpt-4"
request = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "维护者明确要求查找 OpenRouter 上的 GPT-4 并改写这一句话。",
    "authorization": "本次明确指定 GPT-4 是对通常仅使用便宜小模型约定的单次例外；不调用外部 Astra。",
    "input_sentence": sentence,
    "messages": [{"role": "user", "content": prompt}],
    "model": model_id,
    "temperature": 0,
    "seed": 20260915,
    "max_tokens": 256,
    "budget_usd": "0.10",
    "max_retries": 0,
    "license_and_cost": "现有 OpenRouter 商业 API 服务，无新增模型权重或软件依赖；按目录 token 价格收费。",
    "failure_behavior": "一次付费尝试；失败保留原因及预算占用，不更换模型、不自动重试。",
    "scope": "已暴露开发样句；不比较模型整体能力，不推断早期与后期训练机制。",
}
try:
    with OpenRouterClient(ROOT / ".env", RUN / "api-cache", "0.10", timeout_seconds=50, max_retries=0) as client:
        catalog = client.fetch_models()
        selected = next((item for item in catalog["data"] if item["id"] == model_id), None)
        if selected is None:
            raise SystemExit("当前目录没有 openai/gpt-4；未发起改写请求。")
        save("model-catalog-selection.json", {
            "url": catalog["url"], "fetched_at_utc": catalog["fetched_at_utc"],
            "full_catalog_sha256": catalog["snapshot_sha256"], "selected": selected,
            "dated_gpt4_0314_present": any(item["id"] == "openai/gpt-4-0314" for item in catalog["data"]),
            "note": "目录别名不能证明路由到 2023 年某个历史快照；实际路由以响应 metadata 为准。",
        })
        request["pricing"] = selected["pricing"]
        request["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        save("request.json", request)
        result = client.complete(model=model_id, messages=request["messages"],
                                 prompt_price_per_token=selected["pricing"]["prompt"],
                                 completion_price_per_token=selected["pricing"]["completion"],
                                 max_tokens=request["max_tokens"], temperature=0,
                                 seed=request["seed"], purpose="gpt4_single_sentence_v1")
        save("response.json", result)
        with (RUN / "response.txt").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(result["text"])
        save("budget-status.json", client.budget_status())
        print(json.dumps(result, ensure_ascii=False, indent=2))
except OpenRouterError as error:
    save("failure.json", {"reason": error.reason, "metadata": error.metadata})
    raise SystemExit("请求失败：" + error.reason)
