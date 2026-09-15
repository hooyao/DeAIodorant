"""执行维护者指定的一次 GPT-4 Turbo 全文改写，保留未经编辑的输出。"""
from datetime import datetime, timezone
from decimal import Decimal
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

source_path = "data/local/style-intervention-v1/original-article.md"
source_bytes = (ROOT / source_path).read_bytes()
source = source_bytes.decode("utf-8")
instruction = (
    "请把下面这篇面向普通读者的游戏资讯文章完整改写一遍，写成自然、通顺、便于阅读的中文。"
    "用词朴素，把事情说明白。保留原意、事实、数字、版本号、来源归属、引文和建议的适用条件；"
    "不要补充事实、经历或来源。可以重组句子和段落、修改标题、去掉重复的铺垫和夸张渲染。"
    "不要把文章缩成摘要。资料的时间范围沿用原文，不更新为今天。"
    "只输出改写后的完整文章，不解释修改。\n\n"
)
request = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "authorization": "维护者明确提到 GPT-4 Turbo，要求尝试全文改写，并要求控制成本。仅执行一次；不扩展到模型对比。",
    "source_url": "https://post.smzdm.com/p/a6zdv5o0/",
    "source_path": source_path,
    "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "input_choice": "使用完整原文，包括标题；不用第一版失败稿充当原文。",
    "model": "openai/gpt-4-turbo",
    "messages": [{"role": "user", "content": instruction + source}],
    "prompt_version": "gpt4_turbo_full_article_1.0",
    "temperature": 0,
    "seed": 20260915,
    "max_tokens": 8192,
    "budget_usd": "0.50",
    "max_retries": 0,
    "license_and_dependencies": "沿用现有 OpenRouter 商业 API 与客户端，不下载模型权重，不引入新的软件依赖。",
    "cost_plan": "按当前目录输入每百万 token 10 美元、输出 30 美元预估，实际费用以响应 usage.cost 为准；客户端先预留保守预算。",
    "failure_behavior": "禁止自动重试、模型回退和跨模型批量调用；中断保留预算占用，错误另存。",
    "evidence_limit": "一次已暴露文章的开发试写；未建立读者收益，也不能证明 GPT-4 系列整体风格更好或解释训练成因。",
    "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
try:
    with OpenRouterClient(ROOT / ".env", RUN / "api-cache", request["budget_usd"], timeout_seconds=180, max_retries=0) as client:
        catalog = client.fetch_models()
        selected = next((item for item in catalog["data"] if item["id"] == request["model"]), None)
        if selected is None:
            raise SystemExit("目录没有指定的 GPT-4 Turbo；未发起付费请求。")
        prices = selected["pricing"]
        if Decimal(prices["prompt"]) > Decimal("0.00001") or Decimal(prices["completion"]) > Decimal("0.00003"):
            raise SystemExit("目录价格高于本次计划；未发起付费请求。")
        save("model-catalog-selection.json", {
            "url": catalog["url"], "fetched_at_utc": catalog["fetched_at_utc"],
            "full_catalog_sha256": catalog["snapshot_sha256"], "selected": selected,
            "note": "目录可见只表示列出型号，成功响应才表明本次请求实际可用；不声称是 GPT-4 0314/0613。",
        })
        request["pricing"] = prices
        save("request.json", request)
        print("GPT-4 Turbo 全文请求已准备；最多一次付费尝试。", flush=True)
        result = client.complete(model=request["model"], messages=request["messages"],
                                 prompt_price_per_token=prices["prompt"],
                                 completion_price_per_token=prices["completion"],
                                 max_tokens=request["max_tokens"], temperature=0,
                                 seed=request["seed"], purpose="gpt4_turbo_article_v1")
        save("response.json", result)
        with (RUN / "rewritten-article.md").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(result["text"])
        save("budget-status.json", client.budget_status())
        print(json.dumps({"metadata": result["metadata"], "characters": len(result["text"]),
                          "output": "data/local/gpt4-turbo-article-v1/rewritten-article.md"}, ensure_ascii=False, indent=2))
except OpenRouterError as error:
    save("failure.json", {"reason": error.reason, "metadata": error.metadata})
    raise SystemExit("请求失败：" + error.reason)
