"""便宜9B学生的两篇开发摸底；无旧强模型参考，不代表本地SFT前后对照。"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.openrouter import OpenRouterClient, OpenRouterError

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

if (RUN / "manifest.json").exists():
    raise SystemExit("这次摸底已启动，不覆盖或重复请求。")
policy = json.loads((ROOT / "configs/model-roles-v2.json").read_text(encoding="utf-8"))
assert not policy["azure_gpt41"]["automatic_generation_allowed"]
model = "qwen/qwen3.5-9b"
task = "你是中文信息文章编辑。请将原文完整改写为自然、清楚、便于阅读的中文，减少重复铺垫和机械化表达。保留有用事实、数字、版本、例证、说话者、条件、否定和不确定性，不增加新事实，不缩成摘要。原文代码逐字保留。只输出改写后的完整文章。"
source_rows = [
    ("microduck", "data/local/reader-style-anchors-v1/smzdm/analysis-body.txt"),
    ("translation", "data/local/azure-readable-batch-v1/cases/translation/original.md"),
]
with OpenRouterClient(ROOT / ".env", RUN / "api-cache", "0.10", timeout_seconds=120, max_retries=0) as client:
    catalog = client.fetch_models()
    selected = next(m for m in catalog["data"] if m["id"] == model)
    save(RUN / "selected-model.json", {"fetched_at_utc": catalog["fetched_at_utc"],
         "catalog_sha256": catalog["snapshot_sha256"], "model": selected})
    requests = []
    for case_id, source_path in source_rows:
        directory = RUN / case_id
        directory.mkdir(exist_ok=True)
        source = (ROOT / source_path).read_text(encoding="utf-8")
        messages = [{"role": "system", "content": task}, {"role": "user", "content": source}]
        request = {"id": case_id, "source_path": source_path, "source_sha256": digest(ROOT / source_path),
                   "messages": messages, "model": model, "temperature": 0.7,
                   "max_tokens": 8192, "reasoning": {"enabled": False, "exclude": True}, "seed": 20260915}
        save(directory / "request.json", request)
        requests.append({k:v for k,v in request.items() if k != "messages"})
    save(RUN / "manifest.json", {"version": "student-hosted-baseline-1.0", "started_at_utc": datetime.now(timezone.utc).isoformat(),
         "model": model, "budget_usd": "0.10", "max_calls": 2, "pricing": selected["pricing"],
         "cases": requests, "runner_sha256": digest(Path(__file__)), "policy_sha256": digest(ROOT / "configs/model-roles-v2.json"),
         "task_prompt": task, "teacher_or_reading_reference_in_input": False,
         "scope": "已暴露开发样例的学生能力摸底；托管后端revision、量化和部分采样默认值未知，不是未来本地SFT基线。",
         "generation_settings_note": "参考官方非思考通用任务的temperature=0.7；本客户端不传top_p/top_k等其余推荐设置，因此不是完整官方采样配方。",
         "training_started": False, "human_feedback": None})
    for item in requests:
        directory = RUN / item["id"]
        request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
        print(json.dumps({"event": "student_request_start", "case": item["id"], "model": model}), flush=True)
        try:
            response = client.complete(model=model, messages=request["messages"],
                prompt_price_per_token=selected["pricing"]["prompt"],
                completion_price_per_token=selected["pricing"]["completion"],
                max_tokens=8192, temperature=0.7, reasoning=request["reasoning"],
                seed=20260915, purpose="student_baseline_v1_" + item["id"])
        except OpenRouterError as error:
            save(directory / "failure.json", {"reason": error.reason, "metadata": error.metadata,
                                              "budget_after": client.budget_status()})
            raise SystemExit("学生摸底停止：" + error.reason)
        save(directory / "response.json", response)
        with (directory / "candidate.md").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(response["text"])
        save(directory / "completion.json", {"characters": len(response["text"]),
             "candidate_sha256": digest(directory / "candidate.md"), "budget_after": client.budget_status(),
             "meaning_and_readability": "pending", "training_eligible": False})
        print(json.dumps({"event": "student_response_complete", "case": item["id"],
             "characters": len(response["text"]), "metadata": response["metadata"]}, ensure_ascii=False), flush=True)
    save(RUN / "completion.json", {"cases_completed": 2, "budget_after": client.budget_status(),
                                  "human_feedback": None, "training_started": False})
