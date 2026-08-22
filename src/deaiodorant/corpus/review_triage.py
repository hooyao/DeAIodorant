"""Reproducible model-assisted triage for human translation review."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterable

import requests

from deaiodorant.corpus.benchmark import file_sha256, write_jsonl


TRIAGE_PROMPT_VERSIONS = {
    "primary": "translation-review-triage-primary-v2",
    "verifier": "translation-review-triage-verifier-v2",
    "safeguard": "translation-review-triage-foreign-source-safeguard-v2",
}
TRIAGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "enum": ["translated_or_compiled", "original", "uncertain"],
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "evidence": {
            "type": "array",
            "items": {"type": "string", "maxLength": 72},
            "maxItems": 3,
        },
    },
    "required": ["label", "confidence", "evidence"],
}


class ReviewTriageClassifier:
    """Classify review candidates through a versioned, cached local model call."""

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
        if profile not in TRIAGE_PROMPT_VERSIONS:
            raise ValueError(f"Unknown review triage profile: {profile}")
        self.model = model
        self.cache_path = cache_path
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.profile = profile
        if backend not in {"ollama", "openai"}:
            raise ValueError(f"Unknown review triage backend: {backend}")
        self.backend = backend
        self.prompt_version = TRIAGE_PROMPT_VERSIONS[profile]
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
        beginning = text[:700]
        ending = text[-1100:] if len(text) > 1100 else text
        marker_re = re.compile(
            r"(?:译|编译|整理|作者|原文|来源|参考|链接|https?://|采访|访谈|播客|"
            r"现场|报道|研究组|发布会|分享嘉宾|本文|论文地址|文章链接)",
            re.IGNORECASE,
        )
        evidence_lines: list[str] = []
        evidence_chars = 0
        for line in (re.sub(r"\s+", " ", value).strip() for value in text.splitlines()):
            if not line or not marker_re.search(line):
                continue
            clipped = line[:260]
            if clipped in evidence_lines:
                continue
            if evidence_chars + len(clipped) > 1100:
                break
            evidence_lines.append(clipped)
            evidence_chars += len(clipped)
        evidence = "\n".join(evidence_lines) or "（未发现显式来源标记）"
        return (
            f"标题：{record.get('title') or ''}\n"
            f"来源平台：{record.get('source') or ''}\n"
            f"署名：{'、'.join(record.get('authors') or [])}\n"
            f"文章类型：{record.get('article_type') or ''}\n"
            f"正文开头：\n{beginning}\n"
            f"来源证据候选行：\n{evidence}\n"
            f"正文结尾：\n{ending}"
        )

    def prompt_primary(self, record: dict[str, Any]) -> str:
        return f"""任务：对中文文章做翻译来源分诊，判断它是否属于需要排除的翻译或外文编译内容。

这里只判断来源，不判断是否由 AI 写作。

标签：
- translated_or_compiled：正文主要翻译、整理或复述一篇或少数几篇具体外文原作。包括译者/编译署名、外国作者加原文链接、外文访谈或播客的中文转写，以及以“整理”署名并在结尾给出唯一外媒参考链接、正文主要复述该报道的情况。
- original：存在明确中文采写或独立创作证据，例如中国大陆事件的现场报道、中文采访、国内团队第一方实践、项目复盘，或综合多个来源后形成的独立分析。
- uncertain：证据不足、证据冲突，或无法判断正文是否主要依赖某一具体外文原作。

判断规则：
1. 内容发生在中国大陆是很强的 original 信号，但不是绝对规则，不能覆盖明确的外文来源反证。
2. 单独出现英文术语、外国公司、论文、GitHub 或普通参考链接，不足以判为编译。
3. 如果全文围绕外国事件，开头是“整理 | 某编辑”，结尾只有一个 Financial Times 等外媒原文链接，且正文主要复述该报道，应判 translated_or_compiled。
4. 如果中文作者采访国内人士、参加国内活动或讲述自己团队的实践，应判 original。
5. high 必须引用输入中可复核的具体短语；只要有合理疑问就用 uncertain，不要凑高置信度。

待判断文章：
{self.excerpt(record)}
"""

    def prompt_verifier(self, record: dict[str, Any]) -> str:
        return f"""任务：独立复核一篇中文文章的来源属性。不要参考其他模型的结论。

标签：
- translated_or_compiled：正文实质上来自一篇或少数几篇具体外文原作的翻译、整理、转写或新闻编译。
- original：中文作者进行了本地采访、现场采写、第一方实践总结，或真正独立的多源综合分析。
- uncertain：无法用输入中的具体证据排除另一种可能。

重点防错：
- 中国大陆题材通常支持 original，但中国题材也可能来自外媒翻译，不能机械放行。
- 外国题材也可能是中文作者的独立报道，不能只因外国人名或英文链接就排除。
- “整理 | 编辑名”加单一外媒参考链接、且全文复述同一外国新闻，是 compiled 的强证据。
- 国内采访、国内会议、国内团队自述或项目复盘，是 original 的强证据。
- high 必须给出输入里的具体证据；证据冲突时输出 uncertain。

待判断文章：
{self.excerpt(record)}
"""

    def prompt_safeguard(self, record: dict[str, Any]) -> str:
        return f"""任务：执行外文来源护栏复核，只排除翻译或编译自非中文原始内容的文章。

标签：
- translated_or_compiled：正文主要来自一篇或少数几篇具体的非中文原作、外媒报道、外国播客或外国视频。
- original：中文作者进行了本地采访、现场采写、第一方实践总结、独立综合分析，或整理了原本以中文进行的国内演讲、会议、直播和对话。
- uncertain：无法确认原始内容的语言和来源，或证据相互冲突。

必须遵守：
1. “整理”不是自动排除信号。国内中文嘉宾演讲整理、国内企业中文对话整理、国内会议实录仍应判 original。
2. 中国大陆事件、国内机构、中文受访者、国内会议和国内团队实践是很强的 original 信号，除非存在明确的外文原作反证。
3. 论文、GitHub、arXiv 或英文官方链接本身不足以证明编译；中文作者的论文解读或中国团队成果报道可以是 original。
4. “整理 | 编辑名”加唯一外媒链接、且全文主要复述外国新闻；或明确声明翻译整理外文视频/文章，应判 translated_or_compiled。
5. 新闻周报若包含大量据外媒报道的外国新闻编译，可判 translated_or_compiled；主要是国内新闻和本地采写则不能仅凭“周报”排除。
6. high 必须引用能证明原始内容语言或采写方式的具体证据。不能确认时输出 uncertain。

待判断文章：
{self.excerpt(record)}
"""

    def prompt(self, record: dict[str, Any]) -> str:
        if self.profile == "primary":
            return self.prompt_primary(record)
        if self.profile == "verifier":
            return self.prompt_verifier(record)
        return self.prompt_safeguard(record)

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
                "format": TRIAGE_OUTPUT_SCHEMA,
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
                "max_tokens": 320,
                "chat_template_kwargs": {"enable_thinking": False},
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "translation_review_triage",
                        "schema": TRIAGE_OUTPUT_SCHEMA,
                        "strict": True,
                    },
                },
            }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        content = (
            payload["message"]["content"]
            if self.backend == "ollama"
            else payload["choices"][0]["message"]["content"]
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
                "max_tokens": 512,
                "chat_template_kwargs": {"enable_thinking": False},
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "translation_review_triage",
                        "schema": TRIAGE_OUTPUT_SCHEMA,
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
        if result.get("label") not in {
            "translated_or_compiled",
            "original",
            "uncertain",
        }:
            raise ValueError("Local review triage model returned an invalid label")
        if result.get("confidence") not in {"high", "medium", "low"}:
            raise ValueError("Local review triage model returned invalid confidence")
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


def agreed_high_confidence_status(
    primary: dict[str, Any], verifier: dict[str, Any] | None
) -> str:
    """Return a model-assisted status only when two independent prompts agree."""
    if primary.get("confidence") != "high" or verifier is None:
        return "uncertain"
    if verifier.get("confidence") != "high":
        return "uncertain"
    if primary.get("label") != verifier.get("label"):
        return "uncertain"
    if primary["label"] == "original":
        return "model_assisted_original"
    if primary["label"] == "translated_or_compiled":
        return "model_assisted_exclusion"
    return "uncertain"


def apply_foreign_source_safeguard(
    provisional_status: str, safeguard: dict[str, Any] | None
) -> str:
    """Use a high-confidence source-language judgment for operational routing."""
    if safeguard is None:
        return "uncertain"
    if safeguard.get("confidence") != "high":
        return "uncertain"
    if safeguard.get("label") == "original":
        return "model_assisted_original"
    if safeguard.get("label") == "translated_or_compiled":
        return "model_assisted_exclusion"
    return "uncertain"


def ollama_model_digest(endpoint: str, model: str) -> str | None:
    response = requests.get(f"{endpoint.rstrip('/')}/api/tags", timeout=30.0)
    response.raise_for_status()
    for item in response.json().get("models", []):
        if item.get("name") == model or item.get("model") == model:
            return item.get("digest")
    return None


def _classify_many(
    classifier: ReviewTriageClassifier,
    records: list[dict[str, Any]],
    *,
    concurrency: int,
    stage: str,
) -> dict[str, dict[str, Any]]:
    if concurrency <= 1:
        values = [classifier.classify(record) for record in records]
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            values = list(executor.map(classifier.classify, records))
    print(
        f"[review-triage] stage={stage} completed={len(values)}",
        flush=True,
    )
    return {
        record["doc_id"]: value for record, value in zip(records, values)
    }


def run_review_triage(
    records: Iterable[dict[str, Any]],
    human_decisions: dict[str, dict[str, str]],
    *,
    primary: ReviewTriageClassifier,
    verifier: ReviewTriageClassifier,
    safeguard: ReviewTriageClassifier,
    output_dir: Path,
    candidate_paths: Iterable[Path],
    decisions_path: Path | None = None,
    concurrency: int = 1,
    model_digest: str | None = None,
    routing_only: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Triage pending originals without converting model output into human gold."""
    rows = list(records)
    output: list[dict[str, Any]] = []
    model_records = [
        record for record in rows if record["doc_id"] not in human_decisions
    ]
    if routing_only:
        skipped = {"label": None, "confidence": None, "evidence": []}
        primary_by_id = {record["doc_id"]: skipped for record in model_records}
        verifier_by_id = {record["doc_id"]: skipped for record in model_records}
        executed_profiles = ["safeguard"]
    else:
        primary_by_id = _classify_many(
            primary, model_records, concurrency=concurrency, stage="primary"
        )
        verifier_by_id = _classify_many(
            verifier, model_records, concurrency=concurrency, stage="verifier"
        )
        executed_profiles = ["primary", "verifier", "safeguard"]
    safeguard_by_id = _classify_many(
        safeguard, model_records, concurrency=concurrency, stage="safeguard"
    )
    model_index = 0
    for record in rows:
        decision = human_decisions.get(record["doc_id"])
        item: dict[str, Any] = {
            "doc_id": record["doc_id"],
            "source": record["source"],
            "published_at": record["published_at"],
            "title": record["title"],
            "url": record["url"],
        }
        if decision is not None:
            include = decision.get("review_include", "").strip().lower()
            item.update(
                {
                    "triage_status": (
                        "human_reviewed_original" if include == "yes" else "human_excluded"
                    ),
                    "provenance": "human_review",
                    "reviewer": decision.get("reviewer", "").strip(),
                    "reviewed_at": decision.get("reviewed_at", "").strip(),
                    "review_notes": decision.get("review_notes", "").strip(),
                }
            )
            output.append(item)
            continue

        model_index += 1
        primary_result = primary_by_id[record["doc_id"]]
        verifier_result = verifier_by_id[record["doc_id"]]
        provisional_status = agreed_high_confidence_status(
            primary_result, verifier_result
        )
        safeguard_result = safeguard_by_id[record["doc_id"]]
        status = apply_foreign_source_safeguard(
            provisional_status, safeguard_result
        )
        item.update(
            {
                "triage_status": status,
                "provenance": "model_assisted_measurement",
                "model": primary.model,
                "primary_prompt_version": primary.prompt_version,
                "primary_label": primary_result["label"],
                "primary_confidence": primary_result["confidence"],
                "primary_evidence": primary_result["evidence"],
                "verifier_prompt_version": verifier.prompt_version,
                "verifier_label": (
                    verifier_result["label"] if verifier_result is not None else None
                ),
                "verifier_confidence": (
                    verifier_result["confidence"] if verifier_result is not None else None
                ),
                "verifier_evidence": (
                    verifier_result["evidence"] if verifier_result is not None else []
                ),
                "safeguard_prompt_version": safeguard.prompt_version,
                "safeguard_label": (
                    safeguard_result["label"] if safeguard_result is not None else None
                ),
                "safeguard_confidence": (
                    safeguard_result["confidence"]
                    if safeguard_result is not None
                    else None
                ),
                "safeguard_evidence": (
                    safeguard_result["evidence"]
                    if safeguard_result is not None
                    else []
                ),
            }
        )
        output.append(item)
        print(
            f"[review-triage] {model_index}/{len(model_records)} "
            f"{record['doc_id']} {status}",
            flush=True,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "triage_results.jsonl"
    write_jsonl(results_path, output)
    artifact_paths: dict[str, Path] = {}
    for status in (
        "model_assisted_original",
        "model_assisted_exclusion",
        "uncertain",
        "human_reviewed_original",
        "human_excluded",
    ):
        path = output_dir / f"{status}.jsonl"
        write_jsonl(
            path, [item for item in output if item["triage_status"] == status]
        )
        artifact_paths[status] = path
    endpoint = primary.endpoint
    manifest = {
        "protocol_version": "translation-review-triage-1.1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": primary.model,
        "model_digest": (
            model_digest
            if model_digest is not None
            else (
                ollama_model_digest(endpoint, primary.model)
                if primary.backend == "ollama"
                else None
            )
        ),
        "backend": primary.backend,
        "endpoint": endpoint,
        "concurrency": concurrency,
        "prompt_versions": TRIAGE_PROMPT_VERSIONS,
        "executed_profiles": executed_profiles,
        "temperature": 0,
        "seed": 42,
        "decision_policy": (
            "Human decisions take precedence. Remaining records are operationally "
            "routed by a high-confidence foreign-source safeguard; weaker results "
            "remain uncertain. Primary and verifier outputs are retained as supporting "
            "measurements. Model-assisted results are not human gold."
        ),
        "parse_failure_policy": (
            "Malformed structured output is retried once with a larger token budget; "
            "a second failure becomes uncertain/low."
        ),
        "restriction": (
            "Model-assisted results are measurements, not human gold, and must not be "
            "passed to benchmark finalization as human review decisions."
        ),
        "candidate_files": [
            {"path": str(path.resolve()), "sha256": file_sha256(path)}
            for path in candidate_paths
        ],
        "human_decisions_file": (
            {
                "path": str(decisions_path.resolve()),
                "sha256": file_sha256(decisions_path),
            }
            if decisions_path is not None
            else None
        ),
        "results": str(results_path.resolve()),
        "results_sha256": file_sha256(results_path),
        "documents": len(output),
        "status_counts": dict(Counter(item["triage_status"] for item in output)),
        "artifacts": {
            status: {
                "path": str(path.resolve()),
                "sha256": file_sha256(path),
            }
            for status, path in artifact_paths.items()
        },
    }
    manifest_path = output_dir / "triage_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output, manifest
