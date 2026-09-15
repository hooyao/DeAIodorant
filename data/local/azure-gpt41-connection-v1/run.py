"""执行唯一的 Azure 连接检查；请求和响应冻结，账本留在私有目录。"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.azure import AzureResponsesClient, AzureResponsesError

def save(name, value):
    with (RUN / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

if (RUN / "request.json").exists():
    raise SystemExit("已记录过此连接请求，不覆盖或再次调用。")
settings_path = ROOT / "configs/azure-gpt41-research-v1.json"
settings = json.loads(settings_path.read_text(encoding="utf-8"))
request = {
    "version": "azure-gpt41-connection-1.0",
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "model_deployment": settings["deployment"],
    "input": "请只回复：连接成功",
    "max_output_tokens": 16,
    "temperature": 0,
    "store": False,
    "max_retries": 0,
    "purpose": "connection_check",
    "settings_path": settings_path.relative_to(ROOT).as_posix(),
    "settings_sha256": hashlib.sha256(settings_path.read_bytes()).hexdigest(),
    "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "evidence_scope": "仅验证部署可连接并返回文字；不验证改写质量。",
}
save("request.json", request)
try:
    with AzureResponsesClient(
        ROOT / settings["env_path"],
        ROOT / settings["shared_cache_dir"],
        budget_usd=settings["client_budget_usd"],
        input_usd_per_million=settings["input_usd_per_million_for_budget"],
        output_usd_per_million=settings["output_usd_per_million_for_budget"],
        timeout_seconds=45,
    ) as client:
        save("budget-before.json", client.budget_status())
        try:
            response = client.complete(
                request["input"], max_output_tokens=request["max_output_tokens"],
                temperature=request["temperature"], purpose=request["purpose"],
            )
        finally:
            save("budget-after.json", client.budget_status())
    save("response.json", response)
    check = {
        "connection_status": "success",
        "response_matches_smoke_instruction": response["text"].strip() == "连接成功",
        "text": response["text"],
        "metadata": response["metadata"],
        "actual_billed_usd": None,
        "note": "账单未知，预算计划价估算和token用量分别保留；不声称读取了Azure余额。",
    }
    save("connection-check.json", check)
    print(json.dumps(check, ensure_ascii=False, indent=2))
except AzureResponsesError as error:
    reason = error.reason if re.fullmatch(r"[a-zA-Z0-9_.:-]{1,120}", error.reason) else "azure_request_failed"
    save("failure.json", {"reason": reason, "metadata": error.metadata})
    raise SystemExit("Azure连接检查失败：" + reason)
except Exception as error:
    save("failure.json", {"reason": "local_failure", "exception_type": type(error).__name__})
    raise SystemExit("连接检查遇到本地错误，详见已脱敏记录。")
