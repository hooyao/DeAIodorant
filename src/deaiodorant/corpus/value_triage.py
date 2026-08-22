"""Model-assisted research-value triage for corpus candidates."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterable

import requests

from deaiodorant.corpus.benchmark import file_sha256, write_jsonl
from deaiodorant.corpus.review_triage import ollama_model_digest


VALUE_PROMPT_VERSIONS = {
    "primary": "research-value-primary-v3",
    "verifier": "research-value-verifier-v3",
}
VALUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "enum": ["substantive", "low_value", "uncertain"],
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "evidence": {
            "type": "array",
            "items": {"type": "string", "maxLength": 56},
            "maxItems": 2,
        },
    },
    "required": ["label", "confidence", "evidence"],
}


class ResearchValueClassifier:
    """Run a versioned local quality judgment with durable caching."""

    def __init__(
        self,
        model: str,
        cache_path: Path,
        *,
        endpoint: str = "http://127.0.0.1:11434",
        timeout: float = 600.0,
        profile: str = "primary",
        backend: str = "ollama",
    ) -> None:
        if profile not in VALUE_PROMPT_VERSIONS:
            raise ValueError(f"Unknown research-value profile: {profile}")
        self.model = model
        self.cache_path = cache_path
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.profile = profile
        if backend not in {"ollama", "openai"}:
            raise ValueError(f"Unknown research-value backend: {backend}")
        self.backend = backend
        self.prompt_version = VALUE_PROMPT_VERSIONS[profile]
        self._cache_lock = threading.Lock()
        self.cache: dict[str, dict[str, Any]] = {}
        if cache_path.exists():
            for line in cache_path.read_text(encoding="utf-8").splitlines():
                try:
                    item = json.loads(line)
                    self.cache[item["cache_key"]] = item
                except (json.JSONDecodeError, KeyError):
                    continue

    @staticmethod
    def excerpt(record: dict[str, Any]) -> str:
        text = str(record["text"])
        window = 700
        positions = [0]
        if len(text) > window * 2:
            positions.append(len(text) // 2)
        positions.append(max(0, len(text) - window))
        sections: list[str] = []
        seen: set[str] = set()
        for position in positions:
            sample = text[position : position + window].strip()
            if sample and sample not in seen:
                sections.append(sample)
                seen.add(sample)
        samples = "\n\n--- 正文抽样 ---\n".join(sections)
        return (
            f"标题：{record.get('title') or ''}\n"
            f"来源平台：{record.get('source') or ''}\n"
            f"署名：{'、'.join(record.get('authors') or [])}\n"
            f"发布日期：{record.get('published_at') or ''}\n"
            f"中文字符数：{record.get('cjk_chars') or ''}\n"
            f"正文抽样：\n{samples}"
        )

    def prompt_primary(self, record: dict[str, Any]) -> str:
        return f"""任务：判断一篇中文技术或商业文章是否具有足够研究价值，可用于高质量语料分析。

这里只判断内容价值，不判断翻译来源，也不判断是否由 AI 写作。

标签：
- substantive：包含可复核事实、深入采访、技术原理、实现细节、架构权衡、方法与实验、第一方项目经验、独立分析或有信息密度的行业调查。
- low_value：主要是会议报名、嘉宾确认出席、议程广告、直播预约、课程招生、招聘或购票推广；主要复述品牌营销口号或产品卖点而缺少技术与事实细节；或只是信息稀薄的宣传稿。
- uncertain：正文抽样不足以判断，宣传与实质内容并存，或价值高度依赖未展示部分。

规则：
1. 不能仅凭篇幅判断价值，长广告仍是 low_value，短而具体的技术说明可以是 substantive。
2. 热度、知名公司和高管身份不等于内容价值。
3. 产品发布文章若包含具体架构、数据、方法、实验或用户实践，可以是 substantive。
4. 周报和资讯聚合若提供多项具体事实、来源与分析，可以是 substantive；只有标题罗列或流量导语则偏 low_value。
5. high 必须引用输入中的具体内容证据，不能只复述标题。

待判断文章：
{self.excerpt(record)}
"""

    def prompt_verifier(self, record: dict[str, Any]) -> str:
        return f"""任务：作为严格的语料质量审稿人，独立复核一篇文章是否有研究价值。

标签：
- substantive：读者能从中获得具体事实、技术知识、方法、实现经验、证据充分的采访或独立分析。
- low_value：核心目的为推广、报名、嘉宾官宣、课程/会议营销、品牌宣传或流量聚合，缺少可用于分析的实质信息。
- uncertain：有一定信息但宣传占比明显，或抽样无法支持高置信度结论。

重点防错：
- 不要把所有产品发布、会议报道或新闻周报都判为低价值；必须看是否有具体细节和独立信息。
- 不要因为文章很长就判为高价值。
- “某某确认出席大会”、报名优惠、嘉宾简介加演讲标题通常是 low_value。
- 包含架构设计、实验数据、技术路径、失败经验或深入问答通常是 substantive。
- high 必须给出正文中的具体证据。

待判断文章：
{self.excerpt(record)}
"""

    def prompt(self, record: dict[str, Any]) -> str:
        if self.profile == "primary":
            return self.prompt_primary(record)
        return self.prompt_verifier(record)

    def classify(self, record: dict[str, Any]) -> dict[str, Any]:
        content_hash = hashlib.sha256(record["text"].encode("utf-8")).hexdigest()
        cache_key = hashlib.sha256(
            f"{self.prompt_version}\0{self.model}\0{content_hash}".encode("utf-8")
        ).hexdigest()
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached["result"]
        if self.backend == "ollama":
            url = f"{self.endpoint}/api/chat"
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": self.prompt(record)}],
                "stream": False,
                "think": False,
                "format": VALUE_OUTPUT_SCHEMA,
                "options": {
                    "temperature": 0,
                    "seed": 42,
                    "num_ctx": 6144,
                    "num_predict": 512,
                },
                "keep_alive": "15m",
            }
        else:
            url = (
                f"{self.endpoint}/chat/completions"
                if self.endpoint.endswith("/v1")
                else f"{self.endpoint}/v1/chat/completions"
            )
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": self.prompt(record)}],
                "temperature": 0,
                "seed": 42,
                "max_tokens": 220,
                "chat_template_kwargs": {"enable_thinking": False},
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "research_value_triage",
                        "schema": VALUE_OUTPUT_SCHEMA,
                        "strict": True,
                    },
                },
            }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        response_payload = response.json()
        content = (
            response_payload["message"]["content"]
            if self.backend == "ollama"
            else response_payload["choices"][0]["message"]["content"]
        )
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            if self.backend != "openai":
                raise
            retry_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": self.prompt(record)}],
                "temperature": 0,
                "seed": 42,
                "max_tokens": 400,
                "chat_template_kwargs": {"enable_thinking": False},
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "research_value_triage",
                        "schema": VALUE_OUTPUT_SCHEMA,
                        "strict": True,
                    },
                },
            }
            retry = requests.post(url, json=retry_payload, timeout=self.timeout)
            retry.raise_for_status()
            try:
                result = json.loads(
                    retry.json()["choices"][0]["message"]["content"]
                )
            except json.JSONDecodeError:
                result = {
                    "label": "uncertain",
                    "confidence": "low",
                    "evidence": ["Structured output remained invalid after retry."],
                }
        if result.get("label") not in {"substantive", "low_value", "uncertain"}:
            raise ValueError("Local research-value model returned an invalid label")
        if result.get("confidence") not in {"high", "medium", "low"}:
            raise ValueError("Local research-value model returned invalid confidence")
        item = {
            "cache_key": cache_key,
            "prompt_version": self.prompt_version,
            "model": self.model,
            "content_hash": content_hash,
            "result": result,
        }
        with self._cache_lock:
            self.cache[cache_key] = item
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        return result


def agreed_research_value_status(
    primary: dict[str, Any], verifier: dict[str, Any]
) -> str:
    """Route only matching high-confidence value judgments."""
    if primary.get("confidence") != "high" or verifier.get("confidence") != "high":
        return "value_uncertain"
    if primary.get("label") != verifier.get("label"):
        return "value_uncertain"
    if primary["label"] == "substantive":
        return "model_assisted_substantive"
    if primary["label"] == "low_value":
        return "model_assisted_low_value"
    return "value_uncertain"


def run_value_triage(
    records: Iterable[dict[str, Any]],
    provenance: dict[str, dict[str, Any]],
    *,
    primary: ResearchValueClassifier,
    verifier: ResearchValueClassifier,
    output_dir: Path,
    candidate_paths: Iterable[Path],
    concurrency: int = 1,
    model_digest: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Screen provenance-eligible documents without changing provenance labels."""
    eligible_statuses = {"human_reviewed_original", "model_assisted_original"}
    eligible = [
        record
        for record in records
        if provenance.get(record["doc_id"], {}).get("triage_status")
        in eligible_statuses
    ]
    if concurrency <= 1:
        primary_values = [primary.classify(record) for record in eligible]
        verifier_values = [verifier.classify(record) for record in eligible]
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            primary_values = list(executor.map(primary.classify, eligible))
        print(f"[value-triage] stage=primary completed={len(eligible)}", flush=True)
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            verifier_values = list(executor.map(verifier.classify, eligible))
        print(f"[value-triage] stage=verifier completed={len(eligible)}", flush=True)
    output: list[dict[str, Any]] = []
    for index, (record, primary_result, verifier_result) in enumerate(
        zip(eligible, primary_values, verifier_values), start=1
    ):
        status = agreed_research_value_status(primary_result, verifier_result)
        output.append(
            {
                "doc_id": record["doc_id"],
                "source": record["source"],
                "published_at": record["published_at"],
                "title": record["title"],
                "url": record["url"],
                "provenance_status": provenance[record["doc_id"]]["triage_status"],
                "value_status": status,
                "model": primary.model,
                "primary_prompt_version": primary.prompt_version,
                "primary_label": primary_result["label"],
                "primary_confidence": primary_result["confidence"],
                "primary_evidence": primary_result["evidence"],
                "verifier_prompt_version": verifier.prompt_version,
                "verifier_label": verifier_result["label"],
                "verifier_confidence": verifier_result["confidence"],
                "verifier_evidence": verifier_result["evidence"],
            }
        )
        print(
            f"[value-triage] {index}/{len(eligible)} {record['doc_id']} {status}",
            flush=True,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "value_results.jsonl"
    write_jsonl(results_path, output)
    artifacts: dict[str, Path] = {}
    for status in (
        "model_assisted_substantive",
        "model_assisted_low_value",
        "value_uncertain",
    ):
        path = output_dir / f"{status}.jsonl"
        write_jsonl(path, [row for row in output if row["value_status"] == status])
        artifacts[status] = path
    manifest = {
        "protocol_version": "research-value-triage-1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": primary.model,
        "model_digest": (
            model_digest
            if model_digest is not None
            else (
                ollama_model_digest(primary.endpoint, primary.model)
                if primary.backend == "ollama"
                else None
            )
        ),
        "backend": primary.backend,
        "endpoint": primary.endpoint,
        "concurrency": concurrency,
        "prompt_versions": VALUE_PROMPT_VERSIONS,
        "temperature": 0,
        "seed": 42,
        "restriction": (
            "Research-value triage is separate from translation provenance. Model "
            "results are measurements and do not replace human quality review."
        ),
        "parse_failure_policy": (
            "Malformed structured output is retried once with a larger token budget; "
            "a second failure becomes uncertain/low."
        ),
        "candidate_files": [
            {"path": str(path.resolve()), "sha256": file_sha256(path)}
            for path in candidate_paths
        ],
        "provenance_results": str(
            (output_dir.parent / "triage_results.jsonl").resolve()
        ),
        "documents": len(output),
        "status_counts": dict(Counter(row["value_status"] for row in output)),
        "results": str(results_path.resolve()),
        "results_sha256": file_sha256(results_path),
        "artifacts": {
            status: {"path": str(path.resolve()), "sha256": file_sha256(path)}
            for status, path in artifacts.items()
        },
    }
    manifest_path = output_dir / "value_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output, manifest
