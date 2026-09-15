"""顺序执行冻结的Azure开发批次，失败停止，不重试或覆盖模型输出。"""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from deaiodorant.refine.azure import AzureResponsesClient, AzureResponsesError
from deaiodorant.refine.openrouter import _canonical

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = load(RUN / "manifest.json")
settings_path = ROOT / manifest["azure_settings_path"]
settings = load(settings_path)
instructions = (RUN / "instructions.txt").read_text(encoding="utf-8")
assert digest(RUN / "instructions.txt") == manifest["instructions_sha256"]
assert digest(RUN / "prepare.py") == manifest["generator_sha256"]
for case in manifest["cases"]:
    directory = RUN / "cases" / case["id"]
    assert digest(directory / "input.txt") == case["input_sha256"]
    assert digest(directory / "original.md") == case["original_view_sha256"]
    assert digest(ROOT / case["source_dir"] / "body.txt") == case["source_body_sha256"]

with AzureResponsesClient(
    ROOT / settings["env_path"], ROOT / settings["shared_cache_dir"],
    budget_usd=settings["client_budget_usd"],
    input_usd_per_million=settings["input_usd_per_million_for_budget"],
    output_usd_per_million=settings["output_usd_per_million_for_budget"],
    timeout_seconds=120,
) as client:
    start_path = RUN / "batch-start.json"
    if not start_path.exists():
        save(start_path, {"started_at_utc": datetime.now(timezone.utc).isoformat(),
                          "budget_before": client.budget_status(),
                          "settings_sha256": digest(settings_path), "runner_sha256": digest(Path(__file__)),
                          "timeout_seconds": 120, "batch_plan_budget_usd": manifest["batch_plan_budget_usd"]})
    start = load(start_path)
    assert start["settings_sha256"] == digest(settings_path)
    assert start["runner_sha256"] == digest(Path(__file__))
    start_accounted = Decimal(start["budget_before"]["accounted_usd"])
    if list((RUN / "cases").glob("*/failure.json")):
        raise SystemExit("已有失败记录，停止批次；不自动恢复或重试。")
    for case in manifest["cases"]:
        directory = RUN / "cases" / case["id"]
        if (directory / "completion.json").exists():
            continue
        if (directory / "request.json").exists():
            raise SystemExit("已有未完成请求记录，需核查账本和缓存，不自动重复调用。")
        input_text = (directory / "input.txt").read_text(encoding="utf-8")
        body = {"model": manifest["model_deployment"], "input": input_text,
                "max_output_tokens": case["max_output_tokens"], "temperature": 0, "store": False,
                "instructions": instructions}
        reserve_tokens = len(_canonical(body)) + 4096 + 512
        reserve = (Decimal(settings["input_usd_per_million_for_budget"]) * reserve_tokens
                   + Decimal(settings["output_usd_per_million_for_budget"]) * case["max_output_tokens"]) / 1_000_000
        before = client.budget_status()
        delta = Decimal(before["accounted_usd"]) - start_accounted
        if delta + reserve > Decimal(manifest["batch_plan_budget_usd"]):
            raise SystemExit("本批保守预算不足，不发出下一请求。")
        save(directory / "request.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(),
             "deployment": manifest["model_deployment"], "input_sha256": case["input_sha256"],
             "instructions_sha256": manifest["instructions_sha256"],
             "max_output_tokens": case["max_output_tokens"], "temperature": 0, "store": False,
             "purpose": "azure_readable_batch_v1_" + case["id"],
             "budget_before": before, "batch_planned_delta_before": str(delta),
             "planned_reservation_usd": str(reserve), "max_automatic_retries": 0})
        print(json.dumps({"event": "request_start", "case": case["id"], "planned_reservation_usd": str(reserve)}, ensure_ascii=False), flush=True)
        try:
            response = client.complete(input_text, instructions=instructions,
                                      max_output_tokens=case["max_output_tokens"], temperature=0,
                                      purpose="azure_readable_batch_v1_" + case["id"])
        except AzureResponsesError as error:
            save(directory / "failure.json", {"reason": error.reason, "metadata": error.metadata,
                                               "budget_after": client.budget_status()})
            raise SystemExit("批次停止：" + error.reason)
        save(directory / "response.json", response)
        with (directory / "candidate-v1.md").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(response["text"])
        code = load(directory / "protected-code.json")
        number = re.compile(r"\d+(?:[.~–-]\d+)*(?:[xX])?")
        original = (directory / "original.md").read_text(encoding="utf-8")
        output_numbers = set(number.findall(response["text"]))
        check = {"source_view_sha256": case["original_view_sha256"],
                 "candidate_sha256": digest(directory / "candidate-v1.md"),
                 "response_text_matches_candidate": True,
                 "input_characters": len(original), "output_characters": len(response["text"]),
                 "code_blocks_exactly_preserved": all(c["text"] in response["text"] for c in code),
                 "protected_code_blocks": len(code),
                 "source_numeric_strings_absent_in_output": sorted(set(number.findall(original)) - output_numbers),
                 "note": "代码和数字只是诊断，不代替含义或读者效果检查。", "human_feedback": None}
        save(directory / "completion.json", {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
             "checks": check, "budget_after": client.budget_status()})
        print(json.dumps({"event": "response_complete", "case": case["id"],
              "characters": check["output_characters"], "codes_exact": check["code_blocks_exactly_preserved"],
              "usage": response["metadata"]["usage"],
              "planned_cost_usd": response["metadata"]["budget_estimate"]["accounted_usd"]}, ensure_ascii=False), flush=True)
    if not (RUN / "batch-completion.json").exists():
        after = client.budget_status()
        save(RUN / "batch-completion.json", {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
             "cases_complete": len(manifest["cases"]), "budget_after": after,
             "batch_accounted_delta_usd": str(Decimal(after["accounted_usd"]) - start_accounted),
             "actual_billed_usd": None, "human_feedback": None})
        print(json.dumps({"event": "batch_completed", "budget_after": after}, ensure_ascii=False), flush=True)
