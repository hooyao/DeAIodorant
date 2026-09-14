"""Stage a fixed, bounded public InfoQ frame without admitting a corpus.

Run ``freeze`` to capture robots and two published sitemaps and select URLs.
Inspect its metadata-only counts before running ``fetch``. No model is called.
Every article remains unreviewed staging, including complete captures.
"""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pilot_collect import canonical_url, dereference, extract_infoq, stable_order  # noqa: E402
from experiments.audit_media_source_capture import block_map, media_map  # noqa: E402

VERSION = "media-contrast-staging-v1"
SEED = "media-contrast-staging-v1-20260914"
USER_AGENT = "DeAIodorantMediaStaging/1.0 (bounded non-commercial public research)"
ROBOTS = "https://www.infoq.cn/robots.txt"
FRAMES = {"post": "https://www.infoq.cn/sitemap/index_1.xml",
          "pre": "https://www.infoq.cn/sitemap/index_3.xml"}
LIMIT_PER_FRAME = 12
PRE_END = dt.date(2023, 1, 1)
POST_START = dt.date(2025, 7, 1)
ID_RE = re.compile(r"^[0-9a-f]{24}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
EXCLUSION_EXPORT = ROOT / "data/local/media-identity-exclusions-v1.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def write_json(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_jsonl(path: Path, value: object) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def progress(output: Path, stage: str, **details: object) -> None:
    write_json(output / "progress.json", {"version": VERSION, "pid": os.getpid(),
               "updated_at": now(), "stage": stage, **details})


def validated_output(path: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to((ROOT / "data/local").resolve())
    return resolved


def identities() -> dict:
    """Read allowlisted identity metadata; never open benchmark bodies/labels."""
    files = sorted((ROOT / "data/pilot/monthly").glob("*/meta.jsonl"))
    files += sorted((ROOT / "data/annotations").glob("*.json"))
    files.append(EXCLUSION_EXPORT)
    ids, urls, hashes = set(), set(), set()
    provenance = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "doc_id" and isinstance(item, str) and ID_RE.fullmatch(item):
                    ids.add(item)
                elif key in {"url", "canonical_url"} and isinstance(item, str) and item.startswith("http"):
                    urls.add(canonical_url(item))
                elif key == "content_hash" and isinstance(item, str) and HASH_RE.fullmatch(item):
                    hashes.add(item)
                elif isinstance(item, (dict, list)):
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for path in files:
        raw = path.read_bytes()
        data = ([json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
                if path.suffix == ".jsonl" else json.loads(raw))
        visit(data)
        provenance.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha(raw)})
    ids.update(sha(url)[:24] for url in urls)
    return {"doc_ids": sorted(ids), "urls": sorted(urls), "content_hashes": sorted(hashes),
            "source_files": provenance,
            "scope": "Pilot monthly metadata, reader annotation identities, root-exported benchmark identity metadata only.",
            "near_duplicate_check": "pending; identity checks do not establish independent holdout eligibility"}


class BoundedClient:
    def __init__(self, output: Path, delay: float = 2.0):
        self.output = output
        self.delay = max(2.0, delay)
        self.last_end = 0.0
        self.stop_reason = None

    def get(self, url: str, relative_path: str, limit: int) -> dict:
        if self.stop_reason:
            raise RuntimeError("Further requests prohibited after the stop condition.")
        wait = self.delay - (time.monotonic() - self.last_end)
        if wait > 0:
            time.sleep(wait)
        result = {"url": url, "requested_at": now(), "capture_file": relative_path}
        destination = self.output / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise RuntimeError("Refusing to overwrite an existing raw response.")
        length = 0
        complete = False
        try:
            with requests.Session() as session:
                session.trust_env = False
                session.cookies.clear()
                with session.get(url, headers={"User-Agent": USER_AGENT,
                                 "Accept": "text/html,application/xml,text/plain;q=0.9"},
                                 timeout=(15, 45), allow_redirects=False, stream=True) as response:
                    result.update({"status": response.status_code, "response_url": response.url,
                        "headers": {key: response.headers[key] for key in (
                            "Content-Type", "Content-Length", "Date", "ETag", "Last-Modified",
                            "Retry-After", "Location") if key in response.headers}})
                    if response.status_code == 429 or response.headers.get("Retry-After"):
                        self.stop_reason = "server_requested_delay"
                    with destination.open("xb") as handle:
                        for chunk in response.iter_content(65536):
                            available = max(0, limit - length)
                            handle.write(chunk[:available])
                            length += min(len(chunk), available)
                            if len(chunk) > available:
                                result["error"] = "response_size_limit"
                                self.stop_reason = self.stop_reason or "response_size_limit"
                                break
                        else:
                            complete = True
        except requests.RequestException as exc:
            result["error"] = type(exc).__name__
        finally:
            self.last_end = time.monotonic()
        result.update({"completed_at": now(), "complete_response": complete})
        if destination.exists():
            raw = destination.read_bytes()
            result.update({"bytes": len(raw), "sha256": sha(raw)})
        append_jsonl(self.output / "requests.jsonl", result)
        return result


def robot_parser(output: Path, request: dict) -> RobotFileParser:
    parser = RobotFileParser(ROBOTS)
    if request.get("status") == 200 and request.get("complete_response"):
        parser.parse((output / request["capture_file"]).read_text(encoding="utf-8", errors="replace").splitlines())
    elif request.get("status") == 404:
        parser.allow_all = True
    else:
        raise RuntimeError("Robots policy unavailable; no further requests allowed.")
    return parser


def robot_delay(parser: RobotFileParser) -> float:
    delay = max(2.0, float(parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*") or 0))
    rate = parser.request_rate(USER_AGENT) or parser.request_rate("*")
    if rate and rate.requests:
        delay = max(delay, rate.seconds / rate.requests)
    if delay > 60:
        raise RuntimeError("Crawl interval exceeds this bounded run.")
    return delay


def cohort(date: dt.date) -> str:
    if date < PRE_END:
        return "pre"
    return "post" if date >= POST_START else "transition"


def freeze(output: Path) -> dict:
    if output.exists():
        raise RuntimeError("Refusing an existing staging directory; use a fresh version.")
    exclusion = identities()
    output.mkdir(parents=True)
    write_json(output / "identity-exclusions.json", exclusion)
    manifest = {"version": VERSION, "seed": SEED, "created_at": now(), "user_agent": USER_AGENT,
        "source_frames": FRAMES, "limit_per_intended_cohort": LIMIT_PER_FRAME,
        "selection_rule": "Rank canonical article URLs by SHA-256(seed + cohort + NUL + URL), after identity/robots and same-cohort sitemap lastmod hint filtering; take at most 12. Lastmod is not publication evidence.",
        "primary_dates": {"pre_exclusive_end": PRE_END.isoformat(), "post_inclusive_start": POST_START.isoformat()},
        "identity_exclusions_sha256": sha((output / "identity-exclusions.json").read_bytes()),
        "root_identity_export_sha256": sha(EXCLUSION_EXPORT.read_bytes()),
        "script_sha256_at_freeze": sha(Path(__file__).read_bytes()),
        "collector_sha256": sha((ROOT / "pilot_collect.py").read_bytes()),
        "presentation_script_sha256": sha((ROOT / "experiments/audit_media_source_capture.py").read_bytes()),
        "runtime": {"python": sys.version.split()[0], "requests": importlib.metadata.version("requests"),
                    "beautifulsoup4": importlib.metadata.version("beautifulsoup4"), "parser": "html.parser"},
        "frames": {}, "selections": [], "corpus_admission": "none_unreviewed_acquisition_staging",
        "network_policy": "Unauthenticated public GET only; no environment credentials, redirects, cookies, hidden endpoints, retries, or referenced-media requests; stop on 429/Retry-After."}
    client = BoundedClient(output)
    progress(output, "capturing_robots", article_attempts=0)
    robots = client.get(ROBOTS, "raw/robots.txt", 512 * 1024)
    manifest["robots_request"] = robots
    if client.stop_reason:
        raise RuntimeError(client.stop_reason)
    parser = robot_parser(output, robots)
    client.delay = robot_delay(parser)
    manifest["minimum_request_interval_seconds"] = client.delay
    excluded_ids, excluded_urls = set(exclusion["doc_ids"]), set(exclusion["urls"])
    already_selected = set()
    for intended, url in FRAMES.items():
        if not parser.can_fetch(USER_AGENT, url):
            raise RuntimeError("Sitemap path disallowed by robots.")
        progress(output, "capturing_sitemap", intended_cohort=intended, article_attempts=0)
        capture = client.get(url, f"raw/sitemap-{intended}.xml", 12 * 1024 * 1024)
        if client.stop_reason or capture.get("status") != 200 or not capture.get("complete_response"):
            raise RuntimeError(client.stop_reason or "sitemap_capture_failed")
        xml = ET.fromstring((output / capture["capture_file"]).read_bytes())
        rows, seen = [], set()
        for index, node in enumerate(xml):
            values = {child.tag.split("}")[-1]: child.text for child in node}
            location = values.get("loc")
            if not location:
                continue
            candidate = canonical_url(location)
            parsed = urlsplit(candidate)
            if parsed.scheme != "https" or parsed.netloc != "www.infoq.cn" or not parsed.path.startswith("/article/"):
                continue
            doc_id = sha(candidate)[:24]
            hint = None
            try:
                hint = dt.date.fromisoformat(str(values.get("lastmod"))[:10])
            except ValueError:
                pass
            reasons = []
            if candidate in seen:
                reasons.append("duplicate_frame_url")
            if doc_id in excluded_ids or candidate in excluded_urls:
                reasons.append("known_identity_exclusion")
            if candidate in already_selected:
                reasons.append("selected_in_other_frame")
            if not parser.can_fetch(USER_AGENT, candidate):
                reasons.append("robots_disallowed")
            if hint is None or cohort(hint) != intended:
                reasons.append("lastmod_hint_outside_intended_cohort_or_missing")
            seen.add(candidate)
            rows.append({"frame_index": index, "url": candidate, "doc_id": doc_id,
                         "sitemap_lastmod": values.get("lastmod"), "intended_cohort": intended,
                         "publication_date": "unknown_until_article_capture", "exclusion_reasons": reasons})
        eligible = {row["url"]: row for row in rows if not row["exclusion_reasons"]}
        chosen = stable_order(eligible, f"{SEED}-{intended}")[:LIMIT_PER_FRAME]
        chosen_set = set(chosen)
        for row in rows:
            row["selected"] = row["url"] in chosen_set and not row["exclusion_reasons"]
            append_jsonl(output / f"frame-{intended}.jsonl", row)
        selected_rows = [{**eligible[value], "selection_rank": index + 1} for index, value in enumerate(chosen)]
        manifest["selections"].extend(selected_rows)
        already_selected.update(chosen)
        hints = [str(row["sitemap_lastmod"]) for row in rows if row["sitemap_lastmod"]]
        manifest["frames"][intended] = {"request": capture, "article_entries": len(rows),
            "unique_article_urls": len(seen), "eligible_lastmod_hint_frame": len(eligible),
            "selected": len(chosen), "lastmod_min": min(hints) if hints else None,
            "lastmod_max": max(hints) if hints else None,
            "exclusion_counts": dict(Counter(reason for row in rows for reason in row["exclusion_reasons"])),
            "frame_file_sha256": sha((output / f"frame-{intended}.jsonl").read_bytes())}
    manifest["frozen_at"] = now()
    write_json(output / "selection-manifest.json", manifest)
    progress(output, "frozen_before_article_fetch", article_attempts=0,
             selected=len(manifest["selections"]), frames=manifest["frames"])
    return {"stage": "frozen_before_article_fetch", "frames": manifest["frames"],
            "selection_manifest_sha256": sha((output / "selection-manifest.json").read_bytes())}


def extract_candidate(output: Path, selected: dict, capture: dict, exclusions: dict) -> dict:
    result = {**selected, "capture": capture, "admission_status": "unreviewed_staging_not_admitted",
        "smell_label": None, "authorship_label": None, "training_rights": "unverified",
        "quality_status": "unreviewed_no_quality_admission", "visibility_status": "unreviewed_snapshot_only",
        "exposure_status": "identity_checked_near_duplicate_and_missing_historical_handoffs_pending"}
    if capture.get("status") != 200 or not capture.get("complete_response"):
        result["status"] = "capture_failed_or_incomplete"
        return result
    raw = (output / capture["capture_file"]).read_bytes()
    html = raw.decode("utf-8", errors="replace")
    extracted = extract_infoq(html, selected["url"], capture["requested_at"])
    if extracted is None:
        result["status"] = "not_extractable_from_ordinary_public_response"
        return result
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one("article .ProseMirror") or soup.select_one(".ProseMirror")
    state = json.loads(soup.select_one("#__NUXT_DATA__").string)
    article_state = next(item for item in state if isinstance(item, dict) and
                         all(key in item for key in ("article_title", "publish_time", "content")))
    milliseconds = dereference(state, article_state.get("publish_time"))
    published = dt.datetime.fromtimestamp(milliseconds / 1000, tz=dt.timezone.utc)
    local_date = published.astimezone(dt.timezone(dt.timedelta(hours=8))).date()
    actual_cohort = cohort(published.date())
    ambiguous = actual_cohort != cohort(local_date)
    text = extracted.pop("text")
    pilot_quality_pass = extracted.pop("quality_pass")
    collector_translation_flag = extracted.pop("is_translation")
    content_hash = sha(text)
    doc_id = selected["doc_id"]
    folder = output / "documents" / doc_id
    folder.mkdir(parents=True)
    (folder / "body.txt").write_bytes(text.encode("utf-8"))
    (folder / "article.dom.html").write_text(str(body), encoding="utf-8")
    blocks, joined = block_map(body)
    if joined != text:
        raise ValueError("Paragraph mapping does not preserve the complete normalized body.")
    write_json(folder / "blocks.json", {"version": "media-source-presentation-v1", "blocks": blocks,
               "collector_text_sha256": content_hash, "block_concatenation_matches_collector": True})
    media = media_map(body)
    links = [{"text": node.get_text("", strip=False), "href": node.get("href")} for node in body.select("a")]
    figures = [{"html": str(node), "caption": node.get_text("", strip=False)} for node in body.select("figure,figcaption")]
    write_json(folder / "structure.json", {"media": media, "links": links, "figures": figures,
        "element_counts": {tag: len(body.select(tag)) for tag in (
            "p", "h1", "h2", "h3", "ul", "ol", "li", "img", "figure", "figcaption", "table", "pre", "a")},
        "multimedia_completeness": "References preserved; no referenced media downloaded or visually inspected.",
        "raw_html_path": capture["capture_file"], "raw_html_sha256": sha(raw)})
    timestamp_fields = {name: dereference(state, article_state[name]) for name in article_state
                        if ("time" in name or "date" in name) and name not in {"content"}}
    scalar_timestamps = {name: value for name, value in timestamp_fields.items()
                         if value is None or isinstance(value, (str, int, float, bool))}
    canonical_nodes = [node.get("href") for node in soup.select('link[rel="canonical"]') if node.get("href")]
    canonical_mismatch = any(canonical_url(value) != selected["url"] for value in canonical_nodes)
    exact_overlap = content_hash in set(exclusions["content_hashes"])
    period_match = not ambiguous and actual_cohort == selected["intended_cohort"]
    exclusions_found = []
    if not period_match:
        exclusions_found.append("publication_period_mismatch_or_boundary_ambiguity")
    if exact_overlap:
        exclusions_found.append("known_exact_content_overlap")
    if collector_translation_flag:
        exclusions_found.append("deterministic_translation_evidence")
    if canonical_mismatch:
        exclusions_found.append("declared_canonical_url_mismatch")
    result.update({"status": "captured_unreviewed", "metadata": extracted,
        "body_path": (folder / "body.txt").relative_to(output).as_posix(), "content_hash": content_hash,
        "body_file_sha256": sha((folder / "body.txt").read_bytes()),
        "embedded_publication_milliseconds": milliseconds, "published_timestamp_utc": published.isoformat(),
        "published_date_asia_shanghai": local_date.isoformat(), "actual_cohort": actual_cohort,
        "boundary_timezone_ambiguity": ambiguous, "intended_period_match": period_match,
        "sitemap_lastmod_is_publication_date": False, "embedded_scalar_time_fields": scalar_timestamps,
        "declared_canonical_urls": canonical_nodes, "canonical_url_mismatch": canonical_mismatch,
        "known_exact_content_overlap": exact_overlap, "exclusions_found": exclusions_found,
        "translation_status": "excluded_deterministic_evidence" if collector_translation_flag else "unresolved_no_originality_pass",
        "legacy_quality_pass_diagnostic_only": pilot_quality_pass,
        "block_count": len(blocks), "media_reference_count": len(media), "link_count": len(links),
        "multimedia_status": "full_captured_text_only_media_references_uninspected",
        "utf8_decode_replacement_count": html.count("\ufffd")})
    write_json(folder / "metadata.json", result)
    return result


def select_index_frame(output: Path) -> dict:
    """Explicitly amend an empty missing-lastmod selection before any bodies."""
    old_path = output / "selection-manifest.json"
    path = output / "selection-manifest-index-v1.json"
    if path.exists() or (output / "fetch-start.json").exists():
        raise RuntimeError("Refusing to change a selection that already started or was amended.")
    manifest = json.loads(old_path.read_text(encoding="utf-8"))
    if manifest["selections"]:
        raise RuntimeError("This amendment applies only to the initial empty selection.")
    manifest["amendment"] = {
        "version": "index-frame-selection-amendment-v1", "authorized_at": now(),
        "authority": "Parent agent approved before any article GET; fixed original indexes and quota retained.",
        "reason": "Both captured sitemaps provide only loc/changefreq/priority; no per-URL date exists.",
        "superseded_empty_selection_manifest_sha256": sha(old_path.read_bytes()),
        "no_backfill": True,
    }
    manifest["selection_rule"] = (
        "Use each specified sitemap index as an intended-period frame without inferring URL publication dates. "
        "Exclude known identities and robots-disallowed URLs, rank canonical URLs by SHA-256(seed + '-' + "
        "cohort + NUL + URL), and select exactly 12 per index. Actual publication dates come from captured "
        "article state; keep all wrong-period/failure outcomes without backfill."
    )
    selected_urls = set()
    for intended in FRAMES:
        rows = [json.loads(line) for line in (output / f"frame-{intended}.jsonl").read_text(encoding="utf-8").splitlines()]
        for row in rows:
            row["exclusion_reasons"] = [reason for reason in row["exclusion_reasons"]
                                        if reason != "lastmod_hint_outside_intended_cohort_or_missing"]
            if row["url"] in selected_urls:
                row["exclusion_reasons"].append("selected_in_other_frame")
        eligible = {row["url"]: row for row in rows if not row["exclusion_reasons"]}
        chosen = stable_order(eligible, f"{SEED}-{intended}")[:LIMIT_PER_FRAME]
        if len(chosen) != LIMIT_PER_FRAME:
            raise RuntimeError("The amended index frame does not meet its frozen URL quota.")
        chosen_set = set(chosen)
        for row in rows:
            row["selected"] = row["url"] in chosen_set and not row["exclusion_reasons"]
            append_jsonl(output / f"frame-index-{intended}.jsonl", row)
        manifest["selections"].extend({**eligible[value], "selection_rank": index + 1}
                                       for index, value in enumerate(chosen))
        selected_urls.update(chosen)
        frame = manifest["frames"][intended]
        frame.pop("eligible_lastmod_hint_frame")
        frame.update({"eligible_index_frame": len(eligible), "selected": len(chosen),
                      "exclusion_counts": dict(Counter(reason for row in rows for reason in row["exclusion_reasons"])),
                      "frame_file_sha256": sha((output / f"frame-index-{intended}.jsonl").read_bytes())})
    manifest["script_sha256_at_freeze"] = sha(Path(__file__).read_bytes())
    manifest["frozen_at"] = now()
    write_json(path, manifest)
    progress(output, "amended_index_frame_frozen_before_article_fetch", article_attempts=0,
             selected=len(manifest["selections"]), frames=manifest["frames"])
    return {"stage": "amended_index_frame_frozen_before_article_fetch", "frames": manifest["frames"],
            "selection_manifest_sha256": sha(path.read_bytes())}


def fetch(output: Path) -> dict:
    manifest_path = output / "selection-manifest-index-v1.json"
    if not manifest_path.exists():
        manifest_path = output / "selection-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (output / "article-attempts.jsonl").exists() or (output / "fetch-start.json").exists():
        raise RuntimeError("This frozen selection already started; no automatic retry or overwrite.")
    if manifest["script_sha256_at_freeze"] != sha(Path(__file__).read_bytes()):
        raise RuntimeError("Script changed after the selection was frozen.")
    exclusions = json.loads((output / "identity-exclusions.json").read_text(encoding="utf-8"))
    if sha((output / "identity-exclusions.json").read_bytes()) != manifest["identity_exclusions_sha256"]:
        raise RuntimeError("Frozen identity exclusions changed.")
    parser = robot_parser(output, manifest["robots_request"])
    client = BoundedClient(output, manifest["minimum_request_interval_seconds"])
    selections = manifest["selections"]
    if len(selections) > 24 or any(value > LIMIT_PER_FRAME for value in Counter(row["intended_cohort"] for row in selections).values()):
        raise RuntimeError("Frozen article quota exceeded.")
    write_json(output / "fetch-start.json", {"started_at": now(), "pid": os.getpid(),
               "selection_manifest_sha256": sha(manifest_path.read_bytes()), "article_get_limit": len(selections)})
    results = []
    for index, selected in enumerate(selections):
        if client.stop_reason:
            result = {**selected, "status": "not_attempted_after_stop", "stop_reason": client.stop_reason}
        elif not parser.can_fetch(USER_AGENT, selected["url"]):
            result = {**selected, "status": "not_attempted_robots_disallowed"}
        else:
            progress(output, "fetching_articles", completed_selections=index,
                     article_attempts=sum("capture" in row for row in results), selected=len(selections),
                     current_doc_id=selected["doc_id"], current_intended_cohort=selected["intended_cohort"])
            capture = client.get(selected["url"], f"raw/{selected['doc_id']}.html", 8 * 1024 * 1024)
            try:
                result = extract_candidate(output, selected, capture, exclusions)
            except Exception as exc:
                result = {**selected, "capture": capture, "status": "extraction_failed",
                          "error": type(exc).__name__, "admission_status": "not_admitted"}
        append_jsonl(output / "article-attempts.jsonl", result)
        results.append(result)
        progress(output, "fetching_articles", completed_selections=index + 1, selected=len(selections),
                 article_attempts=sum("capture" in row for row in results),
                 statuses=dict(Counter(row["status"] for row in results)), stop_reason=client.stop_reason)
        print(json.dumps({"completed_selections": index + 1, "selected": len(selections),
                          "doc_id": selected["doc_id"], "status": result["status"],
                          "actual_cohort": result.get("actual_cohort")}), flush=True)
    summary = {"version": VERSION, "completed_at": now(), "article_attempts": sum("capture" in row for row in results),
        "selected": len(selections), "status_counts": dict(Counter(row["status"] for row in results)),
        "actual_cohort_counts": dict(Counter(row.get("actual_cohort", "unknown") for row in results)),
        "period_match_count": sum(row.get("intended_period_match", False) for row in results),
        "exclusion_counts": dict(Counter(reason for row in results for reason in row.get("exclusions_found", []))),
        "stop_reason": client.stop_reason, "admitted_documents": 0, "smell_labels": 0, "model_calls": 0,
        "selection_manifest_sha256": sha(manifest_path.read_bytes()),
        "article_attempts_sha256": sha((output / "article-attempts.jsonl").read_bytes())}
    write_json(output / "summary.json", summary)
    progress(output, "complete", **{key: value for key, value in summary.items() if key != "version"})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "select-index-frame", "fetch"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = validated_output(args.output_dir)
    try:
        result = {"freeze": freeze, "select-index-frame": select_index_frame, "fetch": fetch}[args.phase](output)
    except Exception as exc:
        if output.is_dir():
            progress(output, "stopped", error_type=type(exc).__name__)
        raise
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
