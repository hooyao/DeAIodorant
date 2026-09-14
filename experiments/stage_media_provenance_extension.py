"""Run a frozen, translation-inclusive, 24-GET InfoQ extension."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))
from bs4 import BeautifulSoup
from experiments import stage_media_contrast_candidates as prior
from experiments.audit_media_staging_overlap import PRIOR_DATASETS
from experiments.contrast_context_audit import concentration
from deaiodorant.analysis.reading_burden import _CJK_RE, _LITERAL_ERSHI_RE
from deaiodorant.corpus.benchmark import ExclusionIndex
from pilot_collect import DIRECT_TRANSLATION_RE, canonical_url, stable_order

VERSION = "media-provenance-extension-1.0"
SEED = "media-provenance-extension-v1-20260914"
OUTPUT = ROOT / "data/local/media-provenance-extension-v1"
OLD = ROOT / "data/local/media-contrast-staging-v1"
PROTOCOL = ROOT / "docs/routes/compact-refiner/media-provenance-extension.md"
HELPERS = (
    "AGENTS.md", "docs/target-feature-discovery.md",
    "docs/routes/compact-refiner/media-provenance-extension.md",
    "experiments/stage_media_provenance_extension.py",
    "experiments/stage_media_contrast_candidates.py", "pilot_collect.py",
    "experiments/audit_media_source_capture.py",
    "experiments/audit_media_staging_overlap.py",
    "src/deaiodorant/corpus/benchmark.py",
    "src/deaiodorant/analysis/reading_burden.py",
    "experiments/contrast_context_audit.py", "experiments/ershi_cohort_statistics.py",
    "src/deaiodorant/refine/records.py",
)
CHALLENGE_TITLE = re.compile(r"captcha|access denied|访问受限|安全验证|人机验证|机器人验证", re.I)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path: Path) -> str:
    return prior.sha(path.read_bytes())


def save(name: str, value) -> None:
    path = OUTPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite a phase artifact: {name}")
    prior.write_json(path, value)


def progress(stage: str, **details) -> None:
    prior.write_json(OUTPUT / "progress.json", {
        "version": VERSION, "pid": os.getpid(), "stage": stage,
        "updated_at": prior.now(), **details,
    })


def check_hashes(mapping: dict) -> None:
    for name, expected in mapping.items():
        if not (ROOT / name).is_file() or digest(ROOT / name) != expected:
            raise RuntimeError(f"Frozen input identity changed: {name}")


def fixed_inputs() -> tuple[dict, dict]:
    old_manifest = read_json(OLD / "selection-manifest-index-v1.json")
    exclusion = read_json(OLD / "identity-exclusions.json")
    export = read_json(prior.EXCLUSION_EXPORT)
    inputs = {name: digest(ROOT / name) for name in HELPERS}
    for name in ("selection-manifest-index-v1.json", "identity-exclusions.json", "requests.jsonl", "article-attempts.jsonl"):
        inputs[(OLD / name).relative_to(ROOT).as_posix()] = digest(OLD / name)
    inputs[prior.EXCLUSION_EXPORT.relative_to(ROOT).as_posix()] = digest(prior.EXCLUSION_EXPORT)
    for source in exclusion["source_files"] + export["sources"]:
        path = ROOT / source["path"]
        if digest(path) != source["sha256"]:
            raise RuntimeError("An identity-only exclusion export is stale")
        inputs[source["path"]] = source["sha256"]
    expected_annotations = {item["path"] for item in exclusion["source_files"] if item["path"].startswith("data/annotations/")}
    current_annotations = {p.relative_to(ROOT).as_posix() for p in (ROOT / "data/annotations").glob("*.json")}
    if current_annotations != expected_annotations:
        raise RuntimeError("Annotation identities need a fresh identity-only export")
    ids, urls, hashes = set(exclusion["doc_ids"]), set(exclusion["urls"]), set(exclusion["content_hashes"])
    for identity in export["identities"]:
        ids.add(identity["doc_id"])
        urls.add(canonical_url(identity["url"]))
        if identity.get("content_hash"):
            hashes.add(identity["content_hash"])
    prior_requests = rows(OLD / "requests.jsonl")
    for item in old_manifest["selections"] + prior_requests:
        url = canonical_url(item["url"])
        if urlsplit(url).path.startswith("/article/"):
            urls.add(url)
            ids.add(prior.sha(url)[:24])
    guard_sources = []
    for name in PRIOR_DATASETS:
        path = ROOT / name
        item = {"path": name, "status": "available" if path.is_file() else "missing"}
        if path.is_file():
            item["sha256"] = digest(path)
            inputs[name] = item["sha256"]
        guard_sources.append(item)
    old_bodies = []
    for attempt in rows(OLD / "article-attempts.jsonl"):
        if not attempt.get("body_path"):
            continue
        path = OLD / attempt["body_path"]
        if digest(path) != attempt["body_file_sha256"]:
            raise RuntimeError("Prior staging body identity mismatch")
        relative = path.relative_to(ROOT).as_posix()
        inputs[relative] = digest(path)
        hashes.add(attempt["content_hash"])
        old_bodies.append({"path": relative, "sha256": digest(path), "doc_id": attempt["doc_id"], "url": attempt["url"]})
    for period, frame in old_manifest["frames"].items():
        request = frame["request"]
        path = OLD / request["capture_file"]
        if request["url"] != prior.FRAMES[period] or request["status"] != 200 or not request["complete_response"] or digest(path) != request["sha256"]:
            raise RuntimeError("Cached public sitemap provenance failed verification")
        inputs[path.relative_to(ROOT).as_posix()] = digest(path)
    return inputs, {
        "doc_ids": sorted(ids), "urls": sorted(urls), "content_hashes": sorted(hashes),
        "guard_sources": guard_sources, "prior_staging_bodies": old_bodies,
        "scope": "Verified identity-only pilot, annotation, benchmark export, all prior staging selections and requests; protected text is used only by the subsequent mechanical guard.",
        "benchmark_labels_exposed": False,
        "identity_export_missing_content_hash": sum(not item.get("content_hash") for item in export["identities"]),
    }


def freeze() -> dict:
    if OUTPUT.exists():
        raise RuntimeError("Use a new version; this run directory already exists")
    inputs, exclusion = fixed_inputs()
    OUTPUT.mkdir(parents=True)
    save("identity-exclusions.json", exclusion)
    save("preflight-history.json", [{"status": "failed_before_freeze_and_before_network", "error_type": "KeyError",
                                      "reason": "Some existing identity-export records have no content_hash; ID/URL exclusions remain available.",
                                      "resolution": "Handle optional hashes explicitly and report their missingness; no article selection or result was observed."}])
    save("preparation.json", {"protocol": VERSION, "created_at": prior.now(), "seed": SEED, "input_hashes": inputs,
                              "command": "python experiments/stage_media_provenance_extension.py freeze"})
    client = prior.BoundedClient(OUTPUT)
    progress("refreshing_robots_before_freeze", article_attempts=0)
    robot_request = client.get(prior.ROBOTS, "raw/robots-freeze.txt", 512 * 1024)
    if client.stop_reason:
        raise RuntimeError(client.stop_reason)
    robot = prior.robot_parser(OUTPUT, robot_request)
    delay = prior.robot_delay(robot)
    selected_urls, selections, frames = set(), [], {}
    old_manifest = read_json(OLD / "selection-manifest-index-v1.json")
    excluded_ids, excluded_urls = set(exclusion["doc_ids"]), set(exclusion["urls"])
    for period in ("pre", "post"):
        source = old_manifest["frames"][period]["request"]
        xml_bytes = (OLD / source["capture_file"]).read_bytes()
        copied = OUTPUT / f"raw/sitemap-{period}.xml"
        copied.write_bytes(xml_bytes)
        frame_rows, seen = [], set()
        for number, node in enumerate(ET.fromstring(xml_bytes)):
            values = {child.tag.split("}")[-1]: child.text for child in node}
            if not values.get("loc"):
                continue
            url = canonical_url(values["loc"])
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.netloc != "www.infoq.cn" or not parsed.path.startswith("/article/"):
                continue
            doc_id, reasons = prior.sha(url)[:24], []
            if url in seen:
                reasons.append("duplicate_frame_url")
            if url in excluded_urls or doc_id in excluded_ids:
                reasons.append("known_identity_or_previously_requested")
            if url in selected_urls:
                reasons.append("selected_in_other_frame")
            if not robot.can_fetch(prior.USER_AGENT, url):
                reasons.append("robots_disallowed")
            seen.add(url)
            frame_rows.append({"frame_index": number, "url": url, "doc_id": doc_id,
                               "intended_cohort": period, "sitemap_lastmod": values.get("lastmod"),
                               "publication_date": "unknown_until_article_capture", "exclusion_reasons": reasons})
        eligible = {item["url"]: item for item in frame_rows if not item["exclusion_reasons"]}
        chosen = stable_order(eligible, f"{SEED}-{period}")[:12]
        if len(chosen) != 12:
            raise RuntimeError("Fixed frame cannot supply 12 candidates; no fallback frame")
        for item in frame_rows:
            item["selected"] = item["url"] in chosen and not item["exclusion_reasons"]
            prior.append_jsonl(OUTPUT / f"frame-{period}.jsonl", item)
        selections.extend({**eligible[url], "selection_rank": number + 1} for number, url in enumerate(chosen))
        selected_urls.update(chosen)
        frames[period] = {"source_request": source, "cached_frame_sha256": digest(copied),
                          "article_entries": len(frame_rows), "unique_urls": len(seen), "eligible": len(eligible), "selected": len(chosen),
                          "exclusion_counts": dict(Counter(reason for item in frame_rows for reason in item["exclusion_reasons"])),
                          "frame_file_sha256": digest(OUTPUT / f"frame-{period}.jsonl")}
    check_hashes(inputs)
    manifest = {"protocol": VERSION, "frozen_at": prior.now(), "seed": SEED, "input_hashes": inputs,
                "identity_exclusions_sha256": digest(OUTPUT / "identity-exclusions.json"),
                "robots_request": robot_request, "minimum_request_interval_seconds": delay,
                "user_agent": prior.USER_AGENT, "article_get_limit": 24, "no_backfill": True,
                "frames": frames, "selections": selections,
                "runtime": {"python": sys.version.split()[0], "requests": importlib.metadata.version("requests"),
                            "beautifulsoup4": importlib.metadata.version("beautifulsoup4")},
                "selection_rule": "SHA-256(seed + '-' + intended_cohort + NUL + canonical_URL), after fixed exclusions; first 12 per index.",
                "corpus_admission": "none", "model_calls": 0, "gpu_used": False}
    save("selection-manifest.json", manifest)
    result = {"stage": "frozen_before_article_get", "selected": len(selections),
              "intended_cohorts": dict(Counter(item["intended_cohort"] for item in selections)),
              "frames": {period: {key: value for key, value in frame.items() if key not in {"source_request"}} for period, frame in frames.items()},
              "selection_manifest_sha256": digest(OUTPUT / "selection-manifest.json")}
    progress("frozen_before_article_get", article_attempts=0, selected=24)
    return result


def load_frozen() -> dict:
    manifest = read_json(OUTPUT / "selection-manifest.json")
    check_hashes(manifest["input_hashes"])
    if digest(OUTPUT / "identity-exclusions.json") != manifest["identity_exclusions_sha256"]:
        raise RuntimeError("Frozen exclusion map changed")
    return manifest


def inspect() -> dict:
    manifest = load_frozen()
    exclusion = read_json(OUTPUT / "identity-exclusions.json")
    selected = manifest["selections"]
    counts = Counter(item["intended_cohort"] for item in selected)
    overlap = [item["doc_id"] for item in selected if item["doc_id"] in exclusion["doc_ids"] or item["url"] in exclusion["urls"]]
    if counts != {"pre": 12, "post": 12} or len({item["url"] for item in selected}) != 24 or overlap:
        raise RuntimeError("Metadata-only quota or identity inspection failed")
    for period, frame in manifest["frames"].items():
        path = OUTPUT / f"frame-{period}.jsonl"
        if digest(path) != frame["frame_file_sha256"]:
            raise RuntimeError("Frame identity changed")
        eligible = {item["url"] for item in rows(path) if not item["exclusion_reasons"]}
        expected = stable_order(eligible, f"{SEED}-{period}")[:12]
        if expected != [item["url"] for item in selected if item["intended_cohort"] == period]:
            raise RuntimeError("Frozen selection cannot be reproduced")
    result = {"stage": "metadata_only_inspection_complete", "inspected_at": prior.now(), "inspector": "assistant_agent",
              "selected": 24, "intended_cohorts": dict(counts), "known_identity_overlap": 0,
              "ranking_reproduced": True, "article_gets_before_inspection": 0,
              "selection_manifest_sha256": digest(OUTPUT / "selection-manifest.json"),
              "command": "python experiments/stage_media_provenance_extension.py inspect"}
    if (OUTPUT / "fetch-start.json").exists():
        raise RuntimeError("Inspection must precede fetch")
    save("inspection.json", result)
    return result


def provenance(result: dict, text: str) -> dict:
    evidence = result["metadata"].get("translation_evidence", [])
    direct = [{"start_char": match.start(), "end_char": match.end(), "matched_literal": match.group()}
              for match in DIRECT_TRANSLATION_RE.finditer(text)]
    if "foreign_media_transcript" in evidence or any("编译" in item["matched_literal"] for item in direct):
        stratum = "mixed_adapted"
    elif "explicit_translator_field" in evidence or any(any(token in item["matched_literal"] for token in ("译自", "翻译", "译者")) for item in direct):
        stratum = "translated"
    else:
        stratum = "unresolved"
    return {"stratum": stratum, "method": "fixed_existing_deterministic_evidence_rules",
            "evidence": evidence, "direct_expression_matches": direct,
            "original_chinese_certified": False, "production_history_verified": False,
            "translation_is_research_exclusion": False}


def fetch() -> dict:
    manifest = load_frozen()
    inspection = read_json(OUTPUT / "inspection.json")
    if inspection["selection_manifest_sha256"] != digest(OUTPUT / "selection-manifest.json"):
        raise RuntimeError("Inspected selection changed")
    save("fetch-start.json", {"started_at": prior.now(), "pid": os.getpid(), "article_get_limit": 24,
                              "selection_manifest_sha256": digest(OUTPUT / "selection-manifest.json"),
                              "command": "python experiments/stage_media_provenance_extension.py fetch"})
    exclusions = read_json(OUTPUT / "identity-exclusions.json")
    client = prior.BoundedClient(OUTPUT, manifest["minimum_request_interval_seconds"])
    progress("refreshing_robots_at_fetch", article_attempts=0)
    request = client.get(prior.ROBOTS, "raw/robots-fetch.txt", 512 * 1024)
    robot = None
    if not client.stop_reason:
        try:
            robot = prior.robot_parser(OUTPUT, request)
            client.delay = max(client.delay, prior.robot_delay(robot))
        except RuntimeError:
            client.stop_reason = "robots_policy_unavailable_or_interval_exceeds_bound"
    save("fetch-policy.json", {"robots_request": request, "delay_seconds": client.delay, "stop_reason": client.stop_reason})
    results = []
    for number, selected in enumerate(manifest["selections"], 1):
        if client.stop_reason:
            result = {**selected, "status": "not_attempted_after_stop", "stop_reason": client.stop_reason}
        elif not robot.can_fetch(prior.USER_AGENT, selected["url"]):
            result = {**selected, "status": "not_attempted_robots_disallowed"}
        else:
            progress("fetching_articles", completed_selections=number - 1, article_attempts=sum("capture" in item for item in results), selected=24)
            capture = client.get(selected["url"], f"raw/{selected['doc_id']}.html", 8 * 1024 * 1024)
            if capture.get("error"):
                client.stop_reason = client.stop_reason or "network_or_capture_error"
            if capture.get("status") in (401, 403, 451):
                client.stop_reason = client.stop_reason or "source_access_restriction"
            raw_path = OUTPUT / capture["capture_file"]
            if raw_path.exists() and capture.get("status") == 200:
                soup = BeautifulSoup(raw_path.read_bytes().decode("utf-8", errors="replace"), "html.parser")
                title = soup.title.get_text() if soup.title else ""
                if not soup.select_one(".ProseMirror") and CHALLENGE_TITLE.search(title):
                    client.stop_reason = client.stop_reason or "public_access_challenge"
            try:
                result = prior.extract_candidate(OUTPUT, selected, capture, exclusions)
                if result.get("body_path"):
                    text = (OUTPUT / result["body_path"]).read_bytes().decode("utf-8")
                    result["legacy_extractor_exclusions"] = result.pop("exclusions_found", [])
                    result["exclusions_found"] = [reason for reason in result["legacy_extractor_exclusions"]
                                                  if reason not in {"deterministic_translation_evidence", "publication_period_mismatch_or_boundary_ambiguity"}]
                    if result["boundary_timezone_ambiguity"]:
                        result["exclusions_found"].append("publication_boundary_ambiguity")
                    result["provenance"] = provenance(result, text)
                    result["translation_status"] = result["provenance"]["stratum"]
                    result["research_retained"] = True
                    result["intended_period_mismatch_is_reassigned_by_actual_date"] = True
                    result.pop("legacy_quality_pass_diagnostic_only", None)
                    for key in ("line_count", "repeated_line_ratio"):
                        result["metadata"].pop(key, None)
                    if not text.strip():
                        result["status"] = "empty_extraction"
                    prior.write_json(OUTPUT / "documents" / selected["doc_id"] / "metadata.json", result)
            except Exception as exc:
                result = {**selected, "capture": capture, "status": "extraction_failed", "error_type": type(exc).__name__}
        prior.append_jsonl(OUTPUT / "article-attempts.jsonl", result)
        results.append(result)
        progress("fetching_articles", completed_selections=number, article_attempts=sum("capture" in item for item in results),
                 selected=24, statuses=dict(Counter(item["status"] for item in results)), stop_reason=client.stop_reason)
        print(json.dumps({"completed_selections": number, "article_attempts": sum("capture" in item for item in results),
                          "status": result["status"], "actual_cohort": result.get("actual_cohort")}), flush=True)
    summary = {"protocol": VERSION, "completed_at": prior.now(), "selected": 24,
               "article_attempts": sum("capture" in item for item in results), "stop_reason": client.stop_reason,
               "status_counts": dict(Counter(item["status"] for item in results)),
               "actual_cohort_counts": dict(Counter(item.get("actual_cohort", "unknown") for item in results)),
               "attempts_sha256": digest(OUTPUT / "article-attempts.jsonl"), "admitted_documents": 0,
               "model_calls": 0, "gpu_used": False}
    save("fetch-summary.json", summary)
    progress("fetch_complete", **{key: value for key, value in summary.items() if key != "protocol"})
    return summary


def summarize(items: list[dict]) -> dict:
    cjk = sum(item["cjk_chars"] for item in items)
    count = sum(item["ershi_occurrences"] for item in items)
    dates = sorted(item["published_date_asia_shanghai"] for item in items)
    return {"documents": len(items), "zero_count_documents": sum(item["ershi_occurrences"] == 0 for item in items),
            "cjk_chars": cjk, "ershi_occurrences": count,
            "pooled_per_1000_cjk": 1000 * count / cjk if cjk else None,
            "pooled_per_10000_cjk": 10000 * count / cjk if cjk else None,
            "publication_min": dates[0] if dates else None, "publication_max": dates[-1] if dates else None,
            "concentration_count_distributions": {str(width): dict(sorted(Counter(next(entry["max_occurrences"] for entry in item["concentration"] if entry["window_cjk"] == width) for item in items).items())) for width in (500, 1000)},
            "missing_visibility_fields": {name: sum(item["visibility"].get(name) is None for item in items) for name in ("views", "comments", "likes", "collects")}}


def analyze() -> dict:
    manifest = load_frozen()
    fetch_summary = read_json(OUTPUT / "fetch-summary.json")
    if digest(OUTPUT / "article-attempts.jsonl") != fetch_summary["attempts_sha256"]:
        raise RuntimeError("Fetch outcomes changed")
    save("analysis-start.json", {"started_at": prior.now(), "pid": os.getpid(),
                                 "command": "python experiments/stage_media_provenance_extension.py analyze"})
    exclusions = read_json(OUTPUT / "identity-exclusions.json")
    index = ExclusionIndex(near_duplicate_threshold=0.9)
    source_log = []
    for source in exclusions["guard_sources"]:
        item = dict(source)
        item.update({"records": 0, "body_indexed": 0})
        if source["status"] == "available":
            path = ROOT / source["path"]
            if digest(path) != source["sha256"]:
                raise RuntimeError("Protected dataset changed")
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    raw = json.loads(line)
                    record = {key: raw.get(key) for key in ("doc_id", "url", "canonical_url", "text")}
                    item["records"] += 1
                    if isinstance(record["text"], str) and record["text"]:
                        index.add(record)
                        item["body_indexed"] += 1
            if digest(path) != source["sha256"]:
                raise RuntimeError("Protected input changed during read-only indexing")
        item["missing_bodies"] = item["records"] - item["body_indexed"]
        source_log.append(item)
        progress("indexing_protected_inputs", source_files_completed=len(source_log), indexed_records=sum(row["body_indexed"] for row in source_log))
        print(json.dumps({"event": "indexed_protected_source", "source_files_completed": len(source_log), "records": item["records"], "body_indexed": item["body_indexed"]}), flush=True)
    for item in exclusions["prior_staging_bodies"]:
        path = ROOT / item["path"]
        if digest(path) != item["sha256"]:
            raise RuntimeError("Prior staging body changed")
        text = path.read_bytes().decode("utf-8")
        if text.strip():
            index.add({"doc_id": item["doc_id"], "url": item["url"], "text": text})
    within = ExclusionIndex(near_duplicate_threshold=0.9)
    diagnostics, guard = [], []
    attempts = rows(OUTPUT / "article-attempts.jsonl")
    for number, attempt in enumerate(attempts, 1):
        item = {"doc_id": attempt["doc_id"], "capture_status": attempt["status"], "known_match": None,
                "within_batch_match": None, "diagnostic_eligible": False}
        reasons = list(attempt.get("exclusions_found", []))
        if not attempt.get("body_path"):
            reasons.append("body_unavailable")
        else:
            path = OUTPUT / attempt["body_path"]
            if digest(path) != attempt["body_file_sha256"]:
                raise RuntimeError("Fresh source body changed")
            text = path.read_bytes().decode("utf-8")
            if not text.strip():
                reasons.append("empty_extraction")
            else:
                record = {"doc_id": attempt["doc_id"], "url": attempt["url"], "text": text}
                for key, match in (("known_match", index.match(record)), ("within_batch_match", within.match(record))):
                    if match:
                        item[key] = {"reason": match.reason, "existing_doc_id": match.existing_doc_id}
                        reasons.append(key)
                within.add(record)
                if not reasons:
                    count = len(_LITERAL_ERSHI_RE.findall(text))
                    cjk = len(_CJK_RE.findall(text))
                    if count != text.count("而是"):
                        raise RuntimeError("Literal count invariant failed")
                    diagnostic = {"doc_id": attempt["doc_id"], "source": "infoq", "actual_cohort": attempt["actual_cohort"],
                                  "intended_cohort": attempt["intended_cohort"], "provenance_stratum": attempt["provenance"]["stratum"],
                                  "source_sha256": attempt["body_file_sha256"], "cjk_chars": cjk, "ershi_occurrences": count,
                                  "per_1000_cjk": 1000 * count / cjk if cjk else None,
                                  "per_10000_cjk": 10000 * count / cjk if cjk else None,
                                  "concentration": [concentration(text, width) for width in (500, 1000)],
                                  "published_timestamp_utc": attempt["published_timestamp_utc"],
                                  "published_date_asia_shanghai": attempt["published_date_asia_shanghai"],
                                  "visibility": {name: attempt["metadata"].get(name) for name in ("views", "comments", "likes", "collects")}}
                    diagnostics.append(diagnostic)
                    item["diagnostic_eligible"] = True
        item["reasons"] = reasons
        guard.append(item)
        prior.append_jsonl(OUTPUT / "duplicate-guard.jsonl", item)
        progress("checking_fresh_bodies", completed_selections=number, diagnostic_documents=len(diagnostics))
    for item in diagnostics:
        prior.append_jsonl(OUTPUT / "document-diagnostics.jsonl", item)
    groups = []
    for period in ("pre", "transition", "post"):
        selected = [item for item in diagnostics if item["actual_cohort"] == period]
        for stratum in ("all", "original_chinese", "translated", "mixed_adapted", "unresolved"):
            subset = selected if stratum == "all" else [item for item in selected if item["provenance_stratum"] == stratum]
            groups.append({"actual_cohort": period, "source": "infoq", "provenance_stratum": stratum, **summarize(subset)})
    summary = {"protocol": VERSION, "completed_at": prior.now(), "status": "descriptive_unmatched_available_frame_extension",
               "selected": 24, "article_attempts": fetch_summary["article_attempts"], "fetch_stop_reason": fetch_summary["stop_reason"],
               "fetch_status_counts": fetch_summary["status_counts"], "diagnostic_documents": len(diagnostics),
               "intended_to_actual": dict(Counter(f"{item['intended_cohort']}->{item.get('actual_cohort', 'unknown')}" for item in attempts)),
               "exclusion_counts": dict(Counter(reason for item in guard for reason in item["reasons"])),
               "known_overlap_count": sum(item["known_match"] is not None for item in guard),
               "within_batch_overlap_count": sum(item["within_batch_match"] is not None for item in guard),
               "guard_sources": source_log, "prior_staging_bodies_indexed": sum(bool((ROOT / item["path"]).read_bytes().strip()) for item in exclusions["prior_staging_bodies"]),
               "groups": groups, "original_chinese_certifications": 0, "human_smell_labels": 0, "admitted_documents": 0,
               "external_model_api_calls": 0, "gpu_used": False,
               "limitations": ["Available cached sitemap frames are not a population sample.", "Actual periods, topic, genre, length, and visibility are unmatched.", "Provenance evidence can be incomplete; unresolved is not original.", "The duplicate heuristic does not prove semantic independence.", "Media references are retained but not downloaded or visually verified.", "Cue counts and concentration do not establish authorship, reading harm, or temporal causation."]}
    check_hashes(manifest["input_hashes"])
    save("analysis-summary.json", summary)
    save("result-manifest.json", {"protocol": VERSION, "completed_at": prior.now(), "input_hashes": manifest["input_hashes"],
                                  "selection_manifest_sha256": digest(OUTPUT / "selection-manifest.json"),
                                  "output_hashes": {path.relative_to(OUTPUT).as_posix(): digest(path) for path in sorted(OUTPUT.rglob("*")) if path.is_file() and path.name != "progress.json"},
                                  "commands": [f"python experiments/stage_media_provenance_extension.py {phase}" for phase in ("freeze", "inspect", "fetch", "analyze")]})
    progress("complete", selected=24, article_attempts=fetch_summary["article_attempts"], diagnostic_documents=len(diagnostics))
    return {key: value for key, value in summary.items() if key not in {"guard_sources", "groups", "limitations"}} | {"groups": [item for item in groups if item["documents"]]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "inspect", "fetch", "analyze"))
    args = parser.parse_args()
    try:
        result = {"freeze": freeze, "inspect": inspect, "fetch": fetch, "analyze": analyze}[args.phase]()
    except Exception as exc:
        if OUTPUT.is_dir():
            failure = {"protocol": VERSION, "phase": args.phase, "stopped_at": prior.now(), "pid": os.getpid(),
                       "error_type": type(exc).__name__, "error_message": str(exc),
                       "command": f"python experiments/stage_media_provenance_extension.py {args.phase}"}
            path = OUTPUT / f"failed-{args.phase}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f')}.json"
            prior.write_json(path, failure)
            progress("failed", phase=args.phase, error_type=type(exc).__name__)
        raise
    print(json.dumps(result, ensure_ascii=True, indent=2), flush=True)


if __name__ == "__main__":
    main()
