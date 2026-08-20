from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import gzip
import hashlib
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


PRE_START = dt.date(2021, 7, 1)
PRE_END = dt.date(2022, 6, 30)
POST_START = dt.date(2025, 7, 1)
POST_END = dt.date(2026, 6, 30)

USER_AGENT = (
    "Mozilla/5.0 (compatible; cn-corpus-research-pilot/0.1; "
    "+non-commercial low-rate research)"
)

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
DATE_RE = re.compile(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})")
DIRECT_TRANSLATION_RE = re.compile(
    r"(?:译自|编译自|翻译自|原文作者)|(?:^|\n)\s*(?:翻译|编译)\s*[/：:]",
    re.MULTILINE,
)
ORIGINAL_LINK_RE = re.compile(r"(?:原文链接|原文地址|原文出处)")
AUTHOR_BIO_RE = re.compile(r"(?:作者简介|作者介绍)[：:\s]*(.{0,400})", re.DOTALL)
ENGLISH_PERSON_RE = re.compile(
    r"\b[A-Z][A-Za-z'’-]{1,30}(?:\s+[A-Z][A-Za-z'’-]{1,30}){1,3}\b"
)
MEDIA_ADAPTATION_RE = re.compile(
    r"(?:基于|根据).{0,50}(?:播客|视频|访谈).{0,50}(?:整理|转写)",
    re.DOTALL,
)
ORIGINAL_MEDIA_LINK_RE = re.compile(
    r"(?:(?:访谈|播客|视频).{0,8}原(?:始)?链接|原(?:始)?(?:访谈|播客|视频)链接)"
)
FOREIGN_DIALOGUE_SPEAKER_RE = re.compile(
    r"(?m)^\s*([A-Z][A-Za-z'’. -]{1,40})[：:]\s*$"
)
LOCAL_INTERVIEW_RE = re.compile(
    r"(?:采访嘉宾|受访嘉宾|独家对话|嘉宾介绍|演讲嘉宾|本期.{0,20}邀请|"
    r"本文整理自.{0,120}(?:分享|演讲)|(?:专场)?直播中|线上分享会)",
    re.DOTALL,
)
CHINESE_REPRINT_RE = re.compile(
    r"(?:mp\.weixin\.qq\.com|微信公众号).{0,300}(?:来源[：:]|原文[：:])|"
    r"(?:来源[：:]|原文[：:]).{0,300}(?:mp\.weixin\.qq\.com|微信公众号)",
    re.DOTALL,
)
CHINESE_ORG_SUFFIX_RE = re.compile(
    r"(?:集团|技术团队|研究院|实验室|信通院|银行|社区|大会|中文站|云|公司)$"
)


@dataclasses.dataclass
class FetchStats:
    attempted: int = 0
    fetched: int = 0
    eligible: int = 0
    wrong_period: int = 0
    translated_filtered: int = 0
    translation_uncertain_filtered: int = 0
    low_quality: int = 0
    failed: int = 0


class HttpClient:
    def __init__(self, delay: float = 0.35, timeout: float = 45.0) -> None:
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            }
        )
        self._last_request = 0.0

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> requests.Response:
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        merged = dict(headers or {})
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.session.get(
                    url,
                    headers=merged,
                    params=params,
                    timeout=self.timeout,
                )
                self._last_request = time.monotonic()
                if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                self._last_request = time.monotonic()
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
        assert last_error is not None
        raise last_error


TRANSLATION_PROMPT_VERSIONS = {
    "strict": "translation-strict-v3",
    "verifier": "translation-original-verifier-v2",
}
TRANSLATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": ["translation", "original", "uncertain"]},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    },
    "required": ["label", "confidence", "evidence"],
}


class LocalTranslationClassifier:
    def __init__(
        self,
        model: str,
        cache_path: Path,
        endpoint: str = "http://127.0.0.1:11434",
        timeout: float = 300.0,
        profile: str = "strict",
    ) -> None:
        if profile not in TRANSLATION_PROMPT_VERSIONS:
            raise ValueError(f"Unknown translation prompt profile: {profile}")
        self.model = model
        self.cache_path = cache_path
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.profile = profile
        self.prompt_version = TRANSLATION_PROMPT_VERSIONS[profile]
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
        text = record["text"]
        beginning = text[:500]
        ending = text[-850:] if len(text) > 850 else text
        marker_re = re.compile(
            r"(?:译|编译|作者|原文|原视频|原链接|https?://|采访|访谈|播客|现场|报道|整理|"
            r"研究组|发布会|分享嘉宾|本文|论文地址|文章链接)",
            re.IGNORECASE,
        )
        evidence_lines: list[str] = []
        evidence_chars = 0
        for line in (re.sub(r"\s+", " ", value).strip() for value in text.splitlines()):
            if not line or not marker_re.search(line):
                continue
            clipped = line[:220]
            if clipped in evidence_lines:
                continue
            if evidence_chars + len(clipped) > 750:
                break
            evidence_lines.append(clipped)
            evidence_chars += len(clipped)
        evidence = "\n".join(evidence_lines) or "（未发现显式来源标记）"
        return (
            f"标题：{record.get('title') or ''}\n"
            f"署名：{'、'.join(record.get('authors') or [])}\n"
            f"正文开头：\n{beginning}\n"
            f"来源证据候选行：\n{evidence}\n"
            f"正文结尾：\n{ending}"
        )

    def prompt_strict(self, record: dict[str, Any]) -> str:
        return f"""任务：判断一篇中文文章是否由非中文原文翻译或编译而来。

只判断翻译来源，不判断是否由 AI 写作，不要因为行文生硬或像 AI 就判为翻译。

标签：
- translation：存在可靠的外文原作线索，例如外国原作者及简介加原文链接、译自/编译自、外文访谈或播客的中文逐段对话稿。
- original：存在明确中文采写证据，例如中文作者的国内采访、现场报道、自有项目复盘或第一方技术实践。
- uncertain：只有英文术语、外国题材、论文/GitHub 链接，或者两类证据都不足。

高置信度必须引用输入中可复核的具体短语。只要无法排除翻译来源，就不要输出 original/high。

正例：
输入：标题：第一个全职 AI CEO 来了；正文：下文基于播客视频整理，经 InfoQ 编辑。Ashlee：…… Pedro：……；结尾：访谈视频原链接：https://www.youtube.com/watch?v=example
输出：{{"label":"translation","confidence":"high","evidence":["基于播客视频整理","Ashlee/Pedro 对话","访谈视频原链接"]}}

负例：
输入：标题：当 Agent 成为新的核心云用户；署名：李文朋；正文分析阿里云 Skills、RAM、STS 和国内云生态，无外文原作者或原始外文链接。
输出：{{"label":"original","confidence":"high","evidence":["中文作者李文朋","阿里云本地产品分析","无外文来源标记"]}}

待判断文章：
{self.excerpt(record)}
"""

    def prompt_verifier(self, record: dict[str, Any]) -> str:
        return f"""任务：判断一篇中文文章是否是把某一份非中文原始内容翻译或编译成中文。

只判断翻译来源，不判断是否由 AI 写作，不要因为行文生硬、像 AI 或出现英文术语就判为翻译。

关键边界：
- 中文作者阅读外文论文、产品公告或新闻后，重新总结、评论、报道，属于 original，不是 translation。
- 中文作者逐段/逐句转写外文文章、播客、视频或访谈，属于 translation。
- 论文链接、GitHub、arXiv、英文术语、外国人名、外国公司、英文标题，都不能单独作为 translation 证据。
- 中文现场采访、发布会回顾、国内团队项目总结，即使采用问答形式或含英文术语，仍属于 original。

标签：
- translation：有可复核证据表明正文是在翻译具体外文原作，例如译者/编译署名、译自声明、外国原作者简介加原文链接、外文访谈的中文逐段对话稿。
- original：有中文采写或再创作证据，例如中文署名的现场报道、采访、项目复盘、论文解读、发布会回顾、综合多源后的评论分析。
- uncertain：既没有具体外文原作证据，也没有足够中文采写证据。

只有证据直接支持标签时才能给 high。不得根据“看起来像翻译腔”判断。

正例：
输入：标题：第一个全职 AI CEO 来了；正文：下文基于播客视频整理，经 InfoQ 编辑。Ashlee：…… Pedro：……；结尾：访谈视频原链接：https://www.youtube.com/watch?v=example
输出：{{"label":"translation","confidence":"high","evidence":["基于播客视频整理","Ashlee/Pedro 对话","访谈视频原链接"]}}

负例：
输入：标题：当 Agent 成为新的核心云用户；署名：李文朋；正文分析阿里云 Skills、RAM、STS 和国内云生态，无外文原作者或原始外文链接。
输出：{{"label":"original","confidence":"high","evidence":["中文作者李文朋","阿里云本地产品分析","无外文来源标记"]}}

负例：
输入：标题：传统 GAN 修改后可解释；正文：论文地址为 AAAI 英文论文，作者单位为中国科学院与上海交通大学，中文正文解释研究背景、方法和实验。
输出：{{"label":"original","confidence":"high","evidence":["中国研究团队","中文论文解读","论文链接本身不是翻译证据"]}}

负例：
输入：标题：CentOS Stream 是什么；正文：本期《极客有约》邀请红帽首席架构师张家驹，InfoQ 与张家驹以中文问答讨论 CentOS。
输出：{{"label":"original","confidence":"high","evidence":["本期邀请张家驹","InfoQ 本地采访","中文受访者"]}}

待判断文章：
{self.excerpt(record)}
"""

    def prompt(self, record: dict[str, Any]) -> str:
        if self.profile == "strict":
            return self.prompt_strict(record)
        return self.prompt_verifier(record)

    def classify(self, record: dict[str, Any]) -> dict[str, Any]:
        content_hash = hashlib.sha256(record["text"].encode("utf-8")).hexdigest()
        cache_key = hashlib.sha256(
            f"{self.prompt_version}\0{self.model}\0{content_hash}".encode("utf-8")
        ).hexdigest()
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached["result"]
        response = requests.post(
            f"{self.endpoint}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": self.prompt(record)}],
                "stream": False,
                "think": False,
                "format": TRANSLATION_OUTPUT_SCHEMA,
                "options": {
                    "temperature": 0,
                    "seed": 42,
                    "num_ctx": 4096,
                    "num_predict": 160,
                },
                "keep_alive": "10m",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        result = json.loads(payload["message"]["content"])
        if result.get("label") not in {"translation", "original", "uncertain"}:
            raise ValueError("Local translation model returned an invalid label")
        item = {
            "cache_key": cache_key,
            "prompt_version": self.prompt_version,
            "model": self.model,
            "content_hash": content_hash,
            "result": result,
        }
        self.cache[cache_key] = item
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        return result


def apply_local_translation_filter(
    record: dict[str, Any],
    classifier: LocalTranslationClassifier | None,
    verifier: LocalTranslationClassifier | None = None,
) -> str:
    if record["is_translation"] or classifier is None:
        return "translation" if record["is_translation"] else "pass"
    result = classifier.classify(record)
    record["translation_model"] = classifier.model
    record["translation_model_prompt_version"] = classifier.prompt_version
    record["translation_model_label"] = result["label"]
    record["translation_model_confidence"] = result["confidence"]
    record["translation_model_evidence"] = result["evidence"]
    confidently_original = result["label"] == "original" and result["confidence"] == "high"
    if confidently_original:
        record["translation_filter_pass"] = True
        record["translation_filter_path"] = "strict_original"
        return "pass"

    original_evidence = strong_original_evidence(record)
    record["strong_original_evidence"] = original_evidence
    if original_evidence and verifier is not None:
        verification = verifier.classify(record)
        record["translation_verifier_model"] = verifier.model
        record["translation_verifier_prompt_version"] = verifier.prompt_version
        record["translation_verifier_label"] = verification["label"]
        record["translation_verifier_confidence"] = verification["confidence"]
        record["translation_verifier_evidence"] = verification["evidence"]
        verifier_original = (
            verification["label"] == "original"
            and verification["confidence"] == "high"
        )
        if verifier_original:
            record["translation_filter_pass"] = True
            record["translation_filter_path"] = "structured_original_plus_verifier"
            return "pass"

    record["translation_filter_pass"] = False
    if result["label"] == "translation":
        record["is_translation"] = True
        record["translation_evidence"].append("local_model_translation")
        return "translation"
    return "uncertain"


def canonical_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, "", ""))


def stable_order(values: Iterable[str], seed: str) -> list[str]:
    unique = set(values)
    return sorted(
        unique,
        key=lambda value: hashlib.sha256(f"{seed}\0{value}".encode("utf-8")).digest(),
    )


def normalize_text(node: Any) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in node.get_text("\n").splitlines()]
    return "\n".join(line for line in lines if line)


def quality_metrics(text: str) -> dict[str, Any]:
    lines = [line for line in text.splitlines() if line]
    unique_lines = set(lines)
    cjk_chars = len(CJK_RE.findall(text))
    repeated_line_ratio = 0.0 if not lines else 1.0 - len(unique_lines) / len(lines)
    passed = cjk_chars >= 500 and repeated_line_ratio <= 0.35
    return {
        "cjk_chars": cjk_chars,
        "text_chars": len(text),
        "line_count": len(lines),
        "repeated_line_ratio": round(repeated_line_ratio, 4),
        "quality_pass": passed,
    }


def parse_date(value: str) -> dt.date | None:
    match = DATE_RE.search(value)
    if not match:
        return None
    try:
        return dt.date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def dereference(array: list[Any], reference: Any) -> Any:
    if isinstance(reference, int) and 0 <= reference < len(array):
        return array[reference]
    return reference


def infoq_people(array: list[Any], root: dict[str, Any], field: str) -> list[str]:
    result: list[str] = []
    people_refs = dereference(array, root.get(field))
    if not isinstance(people_refs, list):
        return result
    for person_ref in people_refs:
        person = dereference(array, person_ref)
        if not isinstance(person, dict):
            continue
        nickname = dereference(array, person.get("nickname"))
        if isinstance(nickname, str) and nickname:
            result.append(nickname)
    return result


def translation_evidence(
    text: str,
    *,
    translators: list[str] | None = None,
    article_type: str | None = None,
) -> list[str]:
    evidence: list[str] = []
    if translators:
        evidence.append("explicit_translator_field")
    if article_type in {"翻译", "编译"}:
        evidence.append("translation_article_type")
    if DIRECT_TRANSLATION_RE.search(text):
        evidence.append("direct_translation_phrase")

    original_link = ORIGINAL_LINK_RE.search(text) is not None
    author_bio = AUTHOR_BIO_RE.search(text)
    english_author_bio = bool(
        author_bio and ENGLISH_PERSON_RE.search(author_bio.group(1))
    )
    if original_link:
        evidence.append("original_link_marker")
    if english_author_bio:
        evidence.append("english_name_in_author_bio")
    foreign_speakers = {
        match.group(1).strip()
        for match in FOREIGN_DIALOGUE_SPEAKER_RE.finditer(text)
    }
    if (
        MEDIA_ADAPTATION_RE.search(text)
        and ORIGINAL_MEDIA_LINK_RE.search(text)
        and len(foreign_speakers) >= 2
    ):
        evidence.append("foreign_media_transcript")
    return evidence


def is_translation_from_evidence(evidence: list[str]) -> bool:
    decisive = {
        "explicit_translator_field",
        "translation_article_type",
        "direct_translation_phrase",
        "foreign_media_transcript",
    }
    if decisive.intersection(evidence):
        return True
    return {
        "original_link_marker",
        "english_name_in_author_bio",
    }.issubset(evidence)


def strong_original_evidence(record: dict[str, Any]) -> list[str]:
    if record.get("is_translation"):
        return []
    evidence: list[str] = []
    text = record.get("text") or ""
    if record.get("article_type") == "原创":
        evidence.append("platform_original_label")
    if LOCAL_INTERVIEW_RE.search(text):
        evidence.append("local_interview_or_talk")
    if CHINESE_REPRINT_RE.search(text):
        evidence.append("chinese_source_reprint")
    authors = record.get("authors") or []
    if any(
        isinstance(author, str)
        and CJK_RE.search(author)
        and CHINESE_ORG_SUFFIX_RE.search(author)
        for author in authors
    ):
        evidence.append("chinese_first_party_org_byline")
    return evidence


def extract_infoq(html: str, url: str, collected_at: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    state_script = soup.select_one("#__NUXT_DATA__")
    if state_script is None or not state_script.string:
        return None
    try:
        state = json.loads(state_script.string)
    except json.JSONDecodeError:
        return None
    root = next(
        (
            item
            for item in state
            if isinstance(item, dict)
            and "article_title" in item
            and "publish_time" in item
            and "content" in item
        ),
        None,
    )
    if root is None:
        return None
    body_node = soup.select_one("article .ProseMirror") or soup.select_one(".ProseMirror")
    if body_node is None:
        return None
    text = normalize_text(body_node)
    publish_ms = dereference(state, root.get("publish_time"))
    if not isinstance(publish_ms, (int, float)):
        return None
    published = dt.datetime.fromtimestamp(publish_ms / 1000, tz=dt.timezone.utc).date()

    def field(name: str) -> Any:
        return dereference(state, root.get(name))

    authors = infoq_people(state, root, "author")
    translators = infoq_people(state, root, "translator")
    evidence = translation_evidence(text, translators=translators)
    record = {
        "doc_id": hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()[:24],
        "source": "infoq",
        "period": None,
        "url": canonical_url(url),
        "title": field("article_title"),
        "authors": authors,
        "translators": translators,
        "is_translation": is_translation_from_evidence(evidence),
        "translation_evidence": evidence,
        "published_at": published.isoformat(),
        "modified_at": None,
        "collected_at": collected_at,
        "crawl_at": None,
        "date_confidence": "embedded_server_state",
        "text": text,
        "views": field("views") if isinstance(field("views"), int) else None,
        "comments": field("comment_count") if isinstance(field("comment_count"), int) else None,
        "likes": field("love") if isinstance(field("love"), int) else None,
        "collects": field("collect") if isinstance(field("collect"), int) else None,
        "visibility_evidence": "page_view_snapshot",
        "acquisition_method": "published_sitemap_and_live_public_page",
    }
    record.update(quality_metrics(text))
    return record


def extract_jiqizhixin(html: str, url: str, crawl_at: str, warc: dict[str, Any]) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    body_node = soup.select_one(".article__content")
    title_node = soup.select_one(".article__title")
    date_node = soup.select_one(".article__published")
    if body_node is None or title_node is None or date_node is None:
        return None
    published = parse_date(date_node.get_text(" ", strip=True))
    if published is None:
        published = parse_date(url)
    if published is None:
        return None
    text = normalize_text(body_node)
    author_node = soup.select_one(".article-author__name")
    type_node = soup.select_one(".article__type")
    article_type = type_node.get_text(" ", strip=True) if type_node else None
    evidence = translation_evidence(text, article_type=article_type)
    is_translation = is_translation_from_evidence(evidence)
    record = {
        "doc_id": hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()[:24],
        "source": "jiqizhixin",
        "period": None,
        "url": canonical_url(url),
        "title": title_node.get_text(" ", strip=True),
        "authors": [author_node.get_text(" ", strip=True)] if author_node else [],
        "translators": [],
        "article_type": article_type,
        "is_translation": is_translation,
        "translation_evidence": evidence,
        "published_at": published.isoformat(),
        "modified_at": None,
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "crawl_at": crawl_at,
        "date_confidence": "page_date_and_dated_url",
        "text": text,
        "views": None,
        "comments": None,
        "likes": None,
        "collects": None,
        "visibility_evidence": "editorial_source_only_unverified",
        "acquisition_method": "common_crawl_warc_range",
        "warc_filename": warc["filename"],
        "warc_offset": int(warc["offset"]),
        "warc_length": int(warc["length"]),
    }
    record.update(quality_metrics(text))
    return record


def infoq_sitemap_urls(client: HttpClient, indexes: Iterable[int]) -> list[str]:
    urls: list[str] = []
    for index in indexes:
        response = client.get(f"https://www.infoq.cn/sitemap/index_{index}.xml")
        for url in re.findall(r"<loc>(.*?)</loc>", response.text):
            if "/article/" in url:
                urls.append(canonical_url(url))
    return list(dict.fromkeys(urls))


def collect_infoq_period(
    client: HttpClient,
    period: str,
    start: dt.date,
    end: dt.date,
    sitemap_indexes: Iterable[int],
    target: int,
    max_attempts: int,
    translation_classifier: LocalTranslationClassifier | None = None,
    translation_verifier: LocalTranslationClassifier | None = None,
) -> tuple[list[dict[str, Any]], FetchStats]:
    collected_at = dt.datetime.now(dt.timezone.utc).isoformat()
    urls = stable_order(infoq_sitemap_urls(client, sitemap_indexes), f"infoq-{period}")
    eligible: list[dict[str, Any]] = []
    stats = FetchStats()
    desired_candidates = target * 2
    for url in urls:
        if stats.attempted >= max_attempts or len(eligible) >= desired_candidates:
            break
        stats.attempted += 1
        try:
            response = client.get(url)
            stats.fetched += 1
            record = extract_infoq(response.text, url, collected_at)
        except Exception as exc:  # network and source-shape failures are reported, not fatal
            stats.failed += 1
            print(f"[infoq/{period}] failed {url}: {type(exc).__name__}", flush=True)
            continue
        if record is None:
            stats.failed += 1
            continue
        published = dt.date.fromisoformat(record["published_at"])
        if not start <= published <= end:
            stats.wrong_period += 1
            continue
        translation_status = apply_local_translation_filter(
            record, translation_classifier, translation_verifier
        )
        if translation_status == "translation":
            stats.translated_filtered += 1
            continue
        if translation_status == "uncertain":
            stats.translation_uncertain_filtered += 1
            continue
        if not record["quality_pass"]:
            stats.low_quality += 1
            continue
        record["period"] = period
        eligible.append(record)
        stats.eligible += 1
        print(
            f"[infoq/{period}] eligible {len(eligible)}/{desired_candidates}: "
            f"{record['published_at']} views={record['views']} {record['title']}",
            flush=True,
        )
    eligible.sort(key=lambda item: (item.get("views") or -1, item["cjk_chars"]), reverse=True)
    selected = eligible[:target]
    add_visibility_percentiles(selected)
    return selected, stats


def common_crawl_records(client: HttpClient, index: str, pattern: str) -> list[dict[str, Any]]:
    endpoint = f"https://index.commoncrawl.org/{index}-index"
    # Query parameters are supplied explicitly because wildcard URL patterns need encoding.
    response = client.get(
        endpoint,
        params={"url": pattern, "output": "json", "page": "0", "pageSize": "1"},
        headers={"User-Agent": USER_AGENT, "Accept": "application/x-ndjson"},
    )
    records: list[dict[str, Any]] = []
    for line in response.text.splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("status") == "200" and "html" in str(item.get("mime", "")):
            records.append(item)
    latest_by_url: dict[str, dict[str, Any]] = {}
    for item in records:
        key = canonical_url(item["url"])
        previous = latest_by_url.get(key)
        if previous is None or item["timestamp"] < previous["timestamp"]:
            latest_by_url[key] = item
    return list(latest_by_url.values())


def warc_html(client: HttpClient, record: dict[str, Any]) -> str:
    offset = int(record["offset"])
    length = int(record["length"])
    response = client.get(
        "https://data.commoncrawl.org/" + record["filename"],
        headers={"Range": f"bytes={offset}-{offset + length - 1}"},
    )
    raw = gzip.decompress(response.content)
    parts = re.split(br"\r?\n\r?\n", raw, maxsplit=2)
    if len(parts) < 3:
        raise ValueError("WARC response did not contain HTTP headers and body")
    return parts[2].decode("utf-8", "replace")


def collect_jiqizhixin_pre(
    client: HttpClient,
    target: int,
    max_attempts: int,
    translation_classifier: LocalTranslationClassifier | None = None,
    translation_verifier: LocalTranslationClassifier | None = None,
) -> tuple[list[dict[str, Any]], FetchStats]:
    records = common_crawl_records(
        client,
        "CC-MAIN-2022-33",
        "www.jiqizhixin.com/articles/2022-06-*",
    )
    ordered = sorted(records, key=lambda item: hashlib.sha256(item["url"].encode()).digest())
    result: list[dict[str, Any]] = []
    stats = FetchStats()
    for item in ordered:
        if len(result) >= target or stats.attempted >= max_attempts:
            break
        stats.attempted += 1
        try:
            html = warc_html(client, item)
            stats.fetched += 1
            crawl_at = dt.datetime.strptime(item["timestamp"], "%Y%m%d%H%M%S").replace(
                tzinfo=dt.timezone.utc
            ).isoformat()
            record = extract_jiqizhixin(html, item["url"], crawl_at, item)
        except Exception as exc:
            stats.failed += 1
            print(f"[jiqizhixin/pre] failed {item['url']}: {type(exc).__name__}", flush=True)
            continue
        if record is None:
            stats.failed += 1
            continue
        translation_status = apply_local_translation_filter(
            record, translation_classifier, translation_verifier
        )
        if translation_status == "translation":
            stats.translated_filtered += 1
            continue
        if translation_status == "uncertain":
            stats.translation_uncertain_filtered += 1
            continue
        if not record["quality_pass"]:
            stats.low_quality += 1
            continue
        record["period"] = "pre"
        result.append(record)
        stats.eligible += 1
        print(
            f"[jiqizhixin/pre] eligible {len(result)}/{target}: "
            f"{record['published_at']} {record['title']}",
            flush=True,
        )
    add_visibility_percentiles(result)
    return result, stats


def probe_jiqizhixin_post(client: HttpClient) -> dict[str, Any]:
    sitemap = client.get("https://www.jiqizhixin.com/shared/sitemap.xml.gz")
    try:
        xml = gzip.decompress(sitemap.content).decode("utf-8", "replace")
    except OSError:
        xml = sitemap.text
    matches = re.findall(r"https://www\.jiqizhixin\.com/articles/(?:2025|2026)-[^<]+", xml)
    post_matches = []
    for match in matches:
        published = parse_date(match)
        if published is not None and POST_START <= published <= POST_END:
            post_matches.append(match)
    if not post_matches:
        return {"accessible": False, "reason": "no_post_period_url_in_sitemap"}
    url = canonical_url(sorted(set(post_matches))[0])
    response = client.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    visible = soup.get_text(" ", strip=True)
    blocked = "机器之心·数据服务" in title or "直接获取数据" in visible
    return {
        "accessible": not blocked and soup.select_one(".article__content") is not None,
        "url": url,
        "http_status": response.status_code,
        "page_title": title,
        "visible_text_chars": len(visible),
        "reason": "data_service_notice" if blocked else "article_shape_missing",
    }


def add_visibility_percentiles(records: list[dict[str, Any]]) -> None:
    with_views = sorted(
        ((index, record["views"]) for index, record in enumerate(records) if record.get("views") is not None),
        key=lambda pair: pair[1],
    )
    count = len(with_views)
    for rank, (index, _) in enumerate(with_views, start=1):
        records[index]["visibility_percentile_in_pilot_cell"] = (
            1.0 if count == 1 else round((rank - 1) / (count - 1), 4)
        )
    for record in records:
        record.setdefault("visibility_percentile_in_pilot_cell", None)


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_review_queue(path: Path, records: Iterable[dict[str, Any]]) -> None:
    fields = [
        "doc_id",
        "source",
        "period",
        "published_at",
        "title",
        "url",
        "cjk_chars",
        "views",
        "visibility_percentile_in_pilot_cell",
        "visibility_evidence",
        "article_type",
        "translators",
        "is_translation",
        "translation_evidence",
        "manual_quality_pass",
        "manual_visibility_pass",
        "suspected_promotion",
        "exclusion_reason",
        "reviewer_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            row.update(
                {
                    "manual_quality_pass": "",
                    "manual_visibility_pass": "",
                    "suspected_promotion": "",
                    "exclusion_reason": "",
                    "reviewer_notes": "",
                }
            )
            writer.writerow(row)


def write_monthly_corpus(root: Path, records: Iterable[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        month = str(record["published_at"])[:7]
        grouped[month].append(record)

    root.mkdir(parents=True, exist_ok=True)
    # Remove only exporter-owned files so reruns cannot retain documents that
    # have since been excluded. Any unrecognized user files are preserved.
    for month_dir in root.iterdir():
        if not month_dir.is_dir() or not re.fullmatch(r"\d{4}-\d{2}", month_dir.name):
            continue
        for generated in month_dir.iterdir():
            if generated.name == "meta.jsonl" or re.fullmatch(
                r"[0-9a-f]{24}\.txt", generated.name
            ):
                generated.unlink()
    for month, month_records in sorted(grouped.items()):
        month_dir = root / month
        month_dir.mkdir(parents=True, exist_ok=True)
        metadata: list[dict[str, Any]] = []
        for record in sorted(month_records, key=lambda item: (item["published_at"], item["doc_id"])):
            text_filename = f"{record['doc_id']}.txt"
            (month_dir / text_filename).write_text(record["text"] + "\n", encoding="utf-8")
            meta = {key: value for key, value in record.items() if key != "text"}
            meta["text_file"] = text_filename
            metadata.append(meta)
        write_jsonl(month_dir / "meta.jsonl", metadata)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    cjk = [record["cjk_chars"] for record in records]
    views = [record["views"] for record in records if record.get("views") is not None]
    return {
        "documents": len(records),
        "median_cjk_chars": statistics.median(cjk) if cjk else None,
        "min_cjk_chars": min(cjk) if cjk else None,
        "max_cjk_chars": max(cjk) if cjk else None,
        "median_views": statistics.median(views) if views else None,
        "visibility_verified_documents": len(views),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small Chinese web corpus acquisition pilot.")
    parser.add_argument("--target-per-cell", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=Path("data/pilot"))
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--max-attempts", type=int, default=80)
    parser.add_argument(
        "--translation-model",
        default=None,
        help="Optional local Ollama model, recommended: qwen3.5:4b (Q4_K_M).",
    )
    parser.add_argument(
        "--ollama-endpoint", default="http://127.0.0.1:11434"
    )
    parser.add_argument(
        "--translation-cache", type=Path, default=Path("data/translation_model_cache.jsonl")
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    if args.target_per_cell < 1:
        raise SystemExit("--target-per-cell must be positive")
    client = HttpClient(delay=args.delay)
    translation_classifier = (
        LocalTranslationClassifier(
            args.translation_model,
            args.translation_cache,
            endpoint=args.ollama_endpoint,
        )
        if args.translation_model
        else None
    )
    translation_verifier = None
    if args.translation_model:
        verifier_cache = args.translation_cache.with_name(
            f"{args.translation_cache.stem}_verifier{args.translation_cache.suffix}"
        )
        translation_verifier = LocalTranslationClassifier(
            args.translation_model,
            verifier_cache,
            endpoint=args.ollama_endpoint,
            profile="verifier",
        )
    cells: dict[str, list[dict[str, Any]]] = {}
    stats: dict[str, Any] = {}

    cells["infoq_pre"], infoq_pre_stats = collect_infoq_period(
        client,
        "pre",
        PRE_START,
        PRE_END,
        sitemap_indexes=[3],
        target=args.target_per_cell,
        max_attempts=args.max_attempts,
        translation_classifier=translation_classifier,
        translation_verifier=translation_verifier,
    )
    stats["infoq_pre"] = dataclasses.asdict(infoq_pre_stats)

    cells["infoq_post"], infoq_post_stats = collect_infoq_period(
        client,
        "post",
        POST_START,
        POST_END,
        sitemap_indexes=[1, 2],
        target=args.target_per_cell,
        max_attempts=args.max_attempts,
        translation_classifier=translation_classifier,
        translation_verifier=translation_verifier,
    )
    stats["infoq_post"] = dataclasses.asdict(infoq_post_stats)

    cells["jiqizhixin_pre"], jiqizhixin_pre_stats = collect_jiqizhixin_pre(
        client,
        args.target_per_cell,
        args.max_attempts,
        translation_classifier=translation_classifier,
        translation_verifier=translation_verifier,
    )
    stats["jiqizhixin_pre"] = dataclasses.asdict(jiqizhixin_pre_stats)

    post_probe = probe_jiqizhixin_post(client)
    cells["jiqizhixin_post"] = []
    stats["jiqizhixin_post"] = {"probe": post_probe, "documents": 0}

    merged: list[dict[str, Any]] = []
    for name, records in cells.items():
        for record in records:
            record["content_hash"] = hashlib.sha256(record["text"].encode("utf-8")).hexdigest()
        write_jsonl(args.output_dir / f"{name}.jsonl", records)
        merged.extend(records)
    write_jsonl(args.output_dir / "pilot_corpus.jsonl", merged)
    write_review_queue(args.output_dir / "manual_review_queue.csv", merged)
    write_monthly_corpus(args.output_dir / "monthly", merged)

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "windows": {
            "pre": [PRE_START.isoformat(), PRE_END.isoformat()],
            "post": [POST_START.isoformat(), POST_END.isoformat()],
        },
        "target_per_cell": args.target_per_cell,
        "cells": {name: summarize(records) for name, records in cells.items()},
        "fetch_stats": stats,
        "limitations": [
            "InfoQ visibility values are current page-view snapshots, not fixed-age historical counts.",
            "Machine Heart PRE documents lack article-level visibility evidence and are auxiliary only.",
            "Machine Heart POST article pages currently return a data-service notice; no bypass was attempted.",
            "The automated quality gate validates extraction and obvious repetition only; human review is still required.",
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
