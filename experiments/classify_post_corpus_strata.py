"""Classify post candidates into frozen format and topic strata."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests

from deaiodorant.corpus.benchmark import file_sha256, read_jsonl, write_jsonl


PROTOCOL_VERSION = "post-corpus-strata-1.0"
PROMPT_VERSION = "post-corpus-format-topic-primary-v1"
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "format_stratum": {
            "type": "string",
            "enum": [
                "technical_practice",
                "research_summary",
                "industry_reporting",
                "other",
            ],
        },
        "topic_stratum": {
            "type": "string",
            "enum": [
                "ai_models_agents",
                "data_infrastructure",
                "software_engineering",
                "business_industry",
                "other",
            ],
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "evidence": {
            "type": "array",
            "items": {"type": "string", "maxLength": 64},
            "maxItems": 2,
        },
    },
    "required": ["format_stratum", "topic_stratum", "confidence", "evidence"],
}


class StratumClassifier:
    """Run one cached deterministic model-assisted stratum measurement."""

    def __init__(
        self,
        *,
        model: str,
        model_digest: str,
        endpoint: str,
        cache_path: Path,
        timeout: float,
    ) -> None:
        self.model = model
        self.model_digest = model_digest
        self.endpoint = endpoint.rstrip("/")
        self.cache_path = cache_path
        self.timeout = timeout
        self.lock = threading.Lock()
        self.cache: dict[str, dict[str, Any]] = {}
        if cache_path.is_file():
            for line in cache_path.read_text(encoding="utf-8").splitlines():
                try:
                    item = json.loads(line)
                    self.cache[item["cache_key"]] = item
                except (json.JSONDecodeError, KeyError):
                    continue

    @staticmethod
    def excerpt(record: dict[str, Any]) -> str:
        """Build a bounded source excerpt for document-level stratification."""

        text = str(record["text"])
        width = 900
        sections = [text[:width]]
        if len(text) > width * 2:
            middle = max(0, len(text) // 2 - width // 2)
            sections.append(text[middle : middle + width])
        sections.append(text[-width:])
        unique: list[str] = []
        for section in sections:
            normalized = section.strip()
            if normalized and normalized not in unique:
                unique.append(normalized)
        return "\n\n---\n".join(unique)

    def prompt(self, record: dict[str, Any]) -> str:
        return f"""任务：给一篇已经通过来源与研究价值筛选的中文文章分配一个格式类别和一个主题类别。

这里只做语料分层，不判断是否由 AI 写作，也不评价文风。

格式类别：
- technical_practice：第一方工程实践、架构设计、实现过程、故障复盘、教程或明确的技术权衡。
- research_summary：主要解释论文、研究方法、实验、评测基准或模型技术报告。
- industry_reporting：主要报道公司、产品、人物、政策、会议、融资、市场或产业变化，可包含深入采访。
- other：以上三类都不适合，或主要是聚合、报名、宣传。

主题类别：
- ai_models_agents：模型、智能体、生成式 AI、机器人学习或 AI 评测。
- data_infrastructure：数据库、数据平台、云基础设施、存储、计算、网络或安全。
- software_engineering：编程语言、开发工具、测试、软件架构、前后端或研发流程。
- business_industry：公司经营、产品市场、政策、组织、投资或产业趋势。
- other：以上主题都不适合。

规则：
1. 根据正文的主要信息目的分类，不要只看标题中的单个词。
2. 产品发布若正文主要讲架构、实验和实现，可判 technical_practice 或 research_summary；若主要讲发布事件、公司和市场影响，判 industry_reporting。
3. high 必须有明确正文证据；无法稳定归类时使用 other 或较低置信度。

标题：{record.get('title') or ''}
来源：{record.get('source') or ''}
正文抽样：
{self.excerpt(record)}
"""

    def classify(self, record: dict[str, Any]) -> dict[str, Any]:
        content_hash = hashlib.sha256(record["text"].encode("utf-8")).hexdigest()
        cache_key = hashlib.sha256(
            f"{PROMPT_VERSION}\0{self.model}\0{content_hash}".encode("utf-8")
        ).hexdigest()
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached["result"]
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": self.prompt(record)}],
            "temperature": 0,
            "seed": 42,
            "max_tokens": 300,
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "post_corpus_strata",
                    "schema": OUTPUT_SCHEMA,
                    "strict": True,
                },
            },
        }
        response = requests.post(
            f"{self.endpoint}/chat/completions", json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        try:
            result = json.loads(response.json()["choices"][0]["message"]["content"])
        except (KeyError, IndexError, json.JSONDecodeError, TypeError):
            result = {
                "format_stratum": "other",
                "topic_stratum": "other",
                "confidence": "low",
                "evidence": ["Structured output was invalid."],
            }
        if (
            not isinstance(result, dict)
            or result.get("format_stratum")
            not in OUTPUT_SCHEMA["properties"]["format_stratum"]["enum"]
            or result.get("topic_stratum")
            not in OUTPUT_SCHEMA["properties"]["topic_stratum"]["enum"]
            or result.get("confidence") not in {"high", "medium", "low"}
            or not isinstance(result.get("evidence"), list)
        ):
            result = {
                "format_stratum": "other",
                "topic_stratum": "other",
                "confidence": "low",
                "evidence": ["Structured output violated the frozen schema."],
            }
        item = {
            "cache_key": cache_key,
            "prompt_version": PROMPT_VERSION,
            "model": self.model,
            "model_digest": self.model_digest,
            "content_hash": content_hash,
            "result": result,
        }
        with self.lock:
            self.cache[cache_key] = item
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure format and topic strata for admitted-value candidates."
    )
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--provenance-results", type=Path, required=True)
    parser.add_argument("--value-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="qwen3.8-27b")
    parser.add_argument("--model-digest", required=True)
    parser.add_argument("--endpoint", default="http://192.168.1.200:8000/v1")
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    candidate_paths = sorted(args.candidate_dir.glob("*_candidates.jsonl"))
    records = [record for path in candidate_paths for record in read_jsonl(path)]
    records_by_id = {record["doc_id"]: record for record in records}
    provenance = {
        row["doc_id"]: row for row in read_jsonl(args.provenance_results)
    }
    value = {row["doc_id"]: row for row in read_jsonl(args.value_results)}
    eligible_ids = sorted(
        doc_id
        for doc_id, row in value.items()
        if row.get("value_status") == "model_assisted_substantive"
        and provenance.get(doc_id, {}).get("triage_status")
        == "model_assisted_original"
    )
    eligible = [records_by_id[doc_id] for doc_id in eligible_ids]
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    classifier = StratumClassifier(
        model=args.model,
        model_digest=args.model_digest,
        endpoint=args.endpoint,
        cache_path=output_dir / "cache.jsonl",
        timeout=args.timeout,
    )
    if args.concurrency <= 1:
        measurements = [classifier.classify(record) for record in eligible]
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            measurements = list(executor.map(classifier.classify, eligible))

    rows: list[dict[str, Any]] = []
    for record, measurement in zip(eligible, measurements, strict=True):
        rows.append(
            {
                "doc_id": record["doc_id"],
                "source": record["source"],
                "published_at": record["published_at"],
                "title": record["title"],
                "format_stratum": measurement["format_stratum"],
                "topic_stratum": measurement["topic_stratum"],
                "confidence": measurement["confidence"],
                "evidence": measurement["evidence"],
                "model": args.model,
                "model_digest": args.model_digest,
                "prompt_version": PROMPT_VERSION,
            }
        )
    results_path = output_dir / "strata_results.jsonl"
    write_jsonl(results_path, rows)
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "model_assisted_measurement_not_human_gold",
        "model": args.model,
        "model_digest": args.model_digest,
        "endpoint": args.endpoint,
        "concurrency": args.concurrency,
        "temperature": 0,
        "seed": 42,
        "prompt_version": PROMPT_VERSION,
        "candidate_files": [
            {"path": str(path.resolve()), "sha256": file_sha256(path)}
            for path in candidate_paths
        ],
        "provenance_results": {
            "path": str(args.provenance_results.resolve()),
            "sha256": file_sha256(args.provenance_results),
        },
        "value_results": {
            "path": str(args.value_results.resolve()),
            "sha256": file_sha256(args.value_results),
        },
        "documents": len(rows),
        "confidence_counts": dict(Counter(row["confidence"] for row in rows)),
        "format_counts": dict(Counter(row["format_stratum"] for row in rows)),
        "topic_counts": dict(Counter(row["topic_stratum"] for row in rows)),
        "results": str(results_path),
        "results_sha256": file_sha256(results_path),
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
