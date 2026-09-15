"""固定到BF16服务复核托管异常；两篇原始消息不变，不依赖此API部署产品。"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import requests

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.openrouter import OpenRouterClient, OpenRouterError

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

if (RUN / "manifest.json").exists():
    raise SystemExit("本次路由诊断已经启动，不重复请求。")
url = "https://openrouter.ai/api/v1/models/qwen/qwen3.5-9b/endpoints"
response = requests.get(url, timeout=30)
response.raise_for_status()
endpoints = response.json()
save(RUN / "endpoints.json", {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "url": url, "response": endpoints})
endpoint = next(e for e in endpoints["data"]["endpoints"] if e.get("provider_name") == "DeepInfra" and e.get("quantization") == "bf16")
source_run = ROOT / "data/local/student-baseline-v1"
save(RUN / "manifest.json", {"version": "student-hosted-routing-check-1.0", "model": "qwen/qwen3.5-9b",
     "provider_only": ["DeepInfra"], "quantizations": ["bf16"], "pricing": endpoint["pricing"],
     "budget_usd": "0.10", "max_calls": 2, "source_requests_dir": source_run.relative_to(ROOT).as_posix(),
     "changed": "只修改provider/precision路由约束；其余消息、temperature、reasoning、seed和max_tokens沿用前次。",
     "limit": "服务商和精度同时变化；不能将差异单独归因于FP4。API目录的精度声明不是实测精度，也不替代未来锁定权重的本地基线。",
     "client_sha256": hashlib.sha256((ROOT / "src/deaiodorant/refine/openrouter.py").read_bytes()).hexdigest(),
     "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "training_started": False})
with OpenRouterClient(ROOT / ".env", RUN / "api-cache", "0.10", timeout_seconds=120, max_retries=0) as client:
    for case_id in ["microduck", "translation"]:
        directory = RUN / case_id
        directory.mkdir(exist_ok=True)
        request = json.loads((source_run / case_id / "request.json").read_text(encoding="utf-8"))
        save(directory / "request.json", {**request, "provider_only": ["DeepInfra"], "quantizations": ["bf16"]})
        print(json.dumps({"event": "bf16_request_start", "case": case_id}), flush=True)
        try:
            result = client.complete(model=request["model"], messages=request["messages"],
                prompt_price_per_token=endpoint["pricing"]["prompt"], completion_price_per_token=endpoint["pricing"]["completion"],
                max_tokens=request["max_tokens"], temperature=request["temperature"], reasoning=request["reasoning"],
                seed=request["seed"], purpose="student_bf16_check_v1_" + case_id,
                provider_only=["DeepInfra"], quantizations=["bf16"])
        except OpenRouterError as error:
            save(directory / "failure.json", {"reason": error.reason, "metadata": error.metadata,
                  "budget_after": client.budget_status()})
            raise SystemExit("路由诊断停止：" + error.reason)
        save(directory / "response.json", result)
        with (directory / "candidate.md").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(result["text"])
        print(json.dumps({"event": "bf16_response_complete", "case": case_id, "characters": len(result["text"]),
             "provider": result["metadata"]["provider"], "usage": result["metadata"]["usage"],
             "cost": result["metadata"]["cost"]}, ensure_ascii=False), flush=True)
    save(RUN / "completion.json", {"cases_completed": 2, "budget_after": client.budget_status(),
                                  "human_feedback": None, "training_started": False})
