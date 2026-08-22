"""Local Label Studio integration for translation-provenance review."""

from __future__ import annotations

import csv
import getpass
import html
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from deaiodorant.corpus.benchmark import (
    BENCHMARK_PROTOCOL_VERSION,
    REVIEW_FIELDS,
    file_sha256,
    read_jsonl,
)


LABEL_STUDIO_VERSION = "1.23.0"
LABEL_STUDIO_REQUIREMENT = f"label-studio=={LABEL_STUDIO_VERSION}"
PROJECT_TITLE = "DeAIodorant translation review v2"

ORIGINAL_RATIONALES = {
    "Original reporting or interview": (
        "Chinese original reporting or interview; no specific translated foreign "
        "work identified."
    ),
    "First-party practice or case study": (
        "First-party Chinese practice or case study; no specific translated foreign "
        "work identified."
    ),
    "Independent synthesis": (
        "Independent Chinese synthesis with original analysis; no specific translated "
        "foreign work identified."
    ),
}
EXCLUSION_RATIONALES = {
    "Translation or compilation marker": (
        "Explicit translation or compilation marker identified."
    ),
    "Specific foreign source work": "Specific translated foreign source work identified.",
    "Reproduced foreign transcript": (
        "Foreign interview, podcast, or video reproduced as a Chinese transcript."
    ),
    "Insufficient or ambiguous evidence": (
        "Evidence is insufficient or ambiguous; excluded under the fail-closed policy."
    ),
    "Low research value or promotional material": (
        "Excluded because the document has insufficient research value or is primarily "
        "promotional material."
    ),
}

LABEL_CONFIG = r"""
<View>
  <Style>
    .htx-text { white-space: pre-wrap; font-size: 17px; line-height: 1.85; }
    .lsf-main-view__annotation { max-width: 1500px; }
  </Style>
  <View style="padding: 8px 16px 18px; border-bottom: 1px solid #ddd;">
    <Header value="$title" size="2" />
    <HyperText name="source_metadata" value="$source_html" inline="true"
      clickableLinks="true" selectionEnabled="false" />
  </View>
  <View style="display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 26px; align-items: start;">
    <View style="padding: 20px 30px; max-width: 900px;">
      <Text name="article" value="$text" selectionEnabled="false" />
    </View>
    <View style="position: sticky; top: 12px; padding: 20px; border-left: 1px solid #ddd; background: #fafafa;">
      <Header value="Human decision" size="3" />
      <Text name="decision_policy"
        value="Accept only independently authored Chinese reporting, interviews, first-party practice, or original synthesis with no specific translated foreign work." />
      <Choices name="decision" toName="article" choice="single-radio" required="true"
        requiredMessage="Select a review decision.">
        <Choice value="Reviewed original" hotkey="1" />
        <Choice value="Exclude or uncertain" hotkey="2" />
      </Choices>
      <View visibleWhen="choice-selected" whenTagName="decision" whenChoiceValue="Reviewed original">
        <Header value="Evidence for original authorship" size="4" />
        <Choices name="original_rationale" toName="article" choice="single-radio"
          required="true" requiredMessage="Select the evidence supporting original authorship.">
          <Choice value="Original reporting or interview" hotkey="3" />
          <Choice value="First-party practice or case study" hotkey="4" />
          <Choice value="Independent synthesis" hotkey="5" />
        </Choices>
      </View>
      <View visibleWhen="choice-selected" whenTagName="decision" whenChoiceValue="Exclude or uncertain">
        <Header value="Reason to exclude" size="4" />
        <Choices name="exclusion_rationale" toName="article" choice="single-radio"
          required="true" requiredMessage="Select an exclusion reason.">
          <Choice value="Translation or compilation marker" hotkey="6" />
          <Choice value="Specific foreign source work" hotkey="7" />
          <Choice value="Reproduced foreign transcript" hotkey="8" />
          <Choice value="Insufficient or ambiguous evidence" hotkey="9" />
          <Choice value="Low research value or promotional material" hotkey="0" />
        </Choices>
      </View>
      <TextArea name="review_notes" toName="article" label="Additional notes"
        placeholder="Optional supporting details, quotations, or source clues"
        rows="4" maxSubmissions="1" showSubmitButton="false" />
    </View>
  </View>
</View>
""".strip()

VALUE_LABEL_CONFIG = r"""
<View>
  <Style>
    .htx-text { white-space: pre-wrap; font-size: 17px; line-height: 1.85; }
    .lsf-main-view__annotation { max-width: 1500px; }
  </Style>
  <View style="padding: 8px 16px 18px; border-bottom: 1px solid #ddd;">
    <Header value="$title" size="2" />
    <HyperText name="source_metadata" value="$source_html" inline="true"
      clickableLinks="true" selectionEnabled="false" />
  </View>
  <View style="display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 26px; align-items: start;">
    <View style="padding: 20px 30px; max-width: 900px;">
      <Text name="article" value="$text" selectionEnabled="false" />
    </View>
    <View style="position: sticky; top: 12px; padding: 20px; border-left: 1px solid #ddd; background: #fafafa;">
      <Header value="Research-value decision" size="3" />
      <Text name="value_policy"
        value="Keep documents with concrete facts, technical details, implementation experience, evidence-rich interviews, or independent analysis. Exclude promotion and information-thin material." />
      <Choices name="value_decision" toName="article" choice="single-radio"
        required="true" requiredMessage="Select a research-value decision.">
        <Choice value="Keep substantive" hotkey="1" />
        <Choice value="Exclude low value" hotkey="2" />
      </Choices>
      <View visibleWhen="choice-selected" whenTagName="value_decision" whenChoiceValue="Keep substantive">
        <Header value="Evidence of value" size="4" />
        <Choices name="substantive_rationale" toName="article" choice="single-radio"
          required="true" requiredMessage="Select the substantive-content evidence.">
          <Choice value="In-depth reporting or interview" hotkey="3" />
          <Choice value="Technical or methodological detail" hotkey="4" />
          <Choice value="First-party practice or concrete data" hotkey="5" />
        </Choices>
      </View>
      <View visibleWhen="choice-selected" whenTagName="value_decision" whenChoiceValue="Exclude low value">
        <Header value="Reason to exclude" size="4" />
        <Choices name="low_value_rationale" toName="article" choice="single-radio"
          required="true" requiredMessage="Select a low-value reason.">
          <Choice value="Promotional or event announcement" hotkey="6" />
          <Choice value="Thin news aggregation" hotkey="7" />
          <Choice value="Marketing claims without useful detail" hotkey="8" />
          <Choice value="Insufficient usable content" hotkey="9" />
        </Choices>
      </View>
      <TextArea name="value_notes" toName="article" label="Additional notes"
        placeholder="Optional details supporting the value decision"
        rows="4" maxSubmissions="1" showSubmitButton="false" />
    </View>
  </View>
</View>
""".strip()

def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _write_local_credentials(workspace: Path, reviewer: str, port: int) -> None:
    env_path = workspace / ".env"
    if not env_path.exists():
        username = f"{reviewer}@localhost"
        password = secrets.token_urlsafe(18)
        token = secrets.token_urlsafe(24)
        values = {
            "LABEL_STUDIO_USERNAME": username,
            "LABEL_STUDIO_PASSWORD": password,
            "LABEL_STUDIO_USER_TOKEN": token,
            "LABEL_STUDIO_PORT": str(port),
            "LABEL_STUDIO_SECRET_KEY": secrets.token_urlsafe(32),
        }
    else:
        values = _read_env(env_path)
    values.update(
        {
            "LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK": "true",
            "LABEL_STUDIO_COLLECT_ANALYTICS": "false",
            "LABEL_STUDIO_SENTRY_DSN": "",
            "LABEL_STUDIO_FRONTEND_SENTRY_DSN": "",
            "LABEL_STUDIO_LATEST_VERSION_CHECK": "false",
            "LABEL_STUDIO_FEATURE_FLAGS_OFFLINE": "true",
        }
    )
    env_path.write_text(
        "".join(f"{key}={value}\n" for key, value in values.items()),
        encoding="utf-8",
        newline="\n",
    )
    credentials_path = workspace / "OPEN_ME_credentials.txt"
    credentials_path.write_text(
        "\n".join(
            [
                "DeAIodorant local translation review",
                f"URL: http://127.0.0.1:{values['LABEL_STUDIO_PORT']}",
                f"Username: {values['LABEL_STUDIO_USERNAME']}",
                f"Password: {values['LABEL_STUDIO_PASSWORD']}",
                "",
                "These credentials are local-only. The service binds to 127.0.0.1.",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def _task(record: dict[str, Any]) -> dict[str, Any]:
    title = str(record["title"])
    url = str(record["url"])
    source = str(record["source"])
    published_at = str(record["published_at"])
    doc_id = str(record["doc_id"])
    evidence = record.get("label_evidence") or []
    source_html = (
        '<div style="line-height:1.7;color:#555">'
        f"<strong>Source:</strong> {html.escape(source)} &nbsp; "
        f"<strong>Published:</strong> {html.escape(published_at)} &nbsp; "
        f"<strong>Document ID:</strong> {html.escape(doc_id)}<br>"
        f"<strong>Candidate evidence:</strong> {html.escape(', '.join(evidence))}<br>"
        f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
        "Open the source page</a></div>"
    )
    return {
        "data": {
            "doc_id": doc_id,
            "source": source,
            "published_at": published_at,
            "title": title,
            "url": url,
            "candidate_label": record["candidate_label"],
            "label_evidence": evidence,
            "cjk_chars": record.get("cjk_chars"),
            "text": record["text"],
            "source_html": source_html,
        }
    }


def prepare_label_studio_workspace(
    candidate_paths: Iterable[Path],
    workspace: Path,
    *,
    reviewer: str | None = None,
    port: int = 8080,
) -> dict[str, Any]:
    """Create local review inputs, raw-text copies, and pinned service config."""
    paths = list(candidate_paths)
    records = [record for path in paths for record in read_jsonl(path)]
    pending = [
        record
        for record in records
        if record.get("candidate_label") == "original_pending_review"
    ]
    if not pending:
        raise RuntimeError("No original candidates are pending human review")

    reviewer = (reviewer or getpass.getuser()).strip()
    if not reviewer or any(character in reviewer for character in "\r\n="):
        raise ValueError("Reviewer identifier must be a non-empty single-line value")

    candidate_files = [
        {"path": str(path.resolve()), "sha256": file_sha256(path)} for path in paths
    ]
    manifest_path = workspace / "workspace_manifest.json"
    existing: dict[str, Any] = {}
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("candidate_files") != candidate_files:
            raise RuntimeError(
                "Candidate files changed after this review workspace was created; "
                "use a new workspace to avoid mixing review states"
            )

    workspace.mkdir(parents=True, exist_ok=True)
    tasks = [_task(record) for record in pending]
    tasks_path = workspace / "label_studio_tasks.json"
    tasks_path.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (workspace / "label_config.xml").write_text(
        LABEL_CONFIG + "\n", encoding="utf-8", newline="\n"
    )
    (workspace / "label_studio_requirements.txt").write_text(
        LABEL_STUDIO_REQUIREMENT + "\n", encoding="utf-8", newline="\n"
    )
    _write_local_credentials(workspace, reviewer, port)

    for record in pending:
        source = str(record["source"])
        doc_id = str(record["doc_id"])
        if not source.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Unsafe source identifier: {source!r}")
        if not doc_id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Unsafe document identifier: {doc_id!r}")
        text_dir = workspace / "texts" / source
        text_dir.mkdir(parents=True, exist_ok=True)
        (text_dir / f"{doc_id}.txt").write_text(
            str(record["text"]), encoding="utf-8", newline=""
        )

    manifest = {
        "protocol_version": BENCHMARK_PROTOCOL_VERSION,
        "tool": "Label Studio Community Edition",
        "tool_version": LABEL_STUDIO_VERSION,
        "tool_license": "Apache-2.0",
        "runtime": "isolated local Python virtual environment",
        "runtime_requirement": LABEL_STUDIO_REQUIREMENT,
        "estimated_runtime_disk_mib": 700,
        "review_scope": "original_pending_review",
        "documents": len(tasks),
        "sources": dict(Counter(record["source"] for record in pending)),
        "candidate_files": candidate_files,
        "tasks_path": str(tasks_path.resolve()),
        "tasks_sha256": file_sha256(tasks_path),
        "default_reviewer": reviewer,
        "label_studio_project_id": existing.get("label_studio_project_id"),
        "service": {
            "binding": "127.0.0.1",
            "port": port,
            "storage": str((workspace / "label_studio_data").resolve()),
            "failure_behavior": (
                "If the local service is unavailable, candidate JSONL and raw UTF-8 "
                "text remain intact; no document receives a decision automatically."
            ),
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def _api_request(
    url: str,
    token: str,
    *,
    method: str = "GET",
    body: Any | None = None,
    timeout: float = 30.0,
) -> Any:
    data = None
    headers = {"Authorization": f"Token {token}"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
            return json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Label Studio API returned HTTP {error.code} for {url}: {detail}"
        ) from error


def _workspace_connection(workspace: Path) -> tuple[str, str]:
    values = _read_env(workspace / ".env")
    url = f"http://127.0.0.1:{values['LABEL_STUDIO_PORT']}"
    return url, values["LABEL_STUDIO_USER_TOKEN"]


def bootstrap_label_studio_project(
    workspace: Path, *, timeout: float = 180.0
) -> dict[str, Any]:
    """Wait for Label Studio, create the review project, and import tasks once."""
    url, token = _workspace_connection(workspace)
    deadline = time.monotonic() + timeout
    projects: Any = None
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            projects = _api_request(f"{url}/api/projects?page_size=100", token)
            break
        except (OSError, urllib.error.HTTPError, urllib.error.URLError) as error:
            last_error = error
            time.sleep(2)
    if projects is None:
        raise RuntimeError(f"Label Studio did not become ready: {last_error}")

    project_rows = projects.get("results", projects) if isinstance(projects, dict) else projects
    matching = [row for row in project_rows if row.get("title") == PROJECT_TITLE]
    if matching:
        project = matching[0]
        project = _api_request(
            f"{url}/api/projects/{project['id']}",
            token,
            method="PATCH",
            body={"label_config": LABEL_CONFIG},
        )
    else:
        project = _api_request(
            f"{url}/api/projects",
            token,
            method="POST",
            body={
                "title": PROJECT_TITLE,
                "description": (
                    "Human review of Chinese translation provenance. Uncertainty is "
                    "excluded under the fail-closed admission policy."
                ),
                "label_config": LABEL_CONFIG,
                "show_instruction": True,
                "expert_instruction": (
                    "Review the complete article and source page when needed. Accept "
                    "only independently authored Chinese reporting, interviews, "
                    "first-party practice, or original synthesis."
                ),
            },
        )
        tasks = json.loads(
            (workspace / "label_studio_tasks.json").read_text(encoding="utf-8")
        )
        _api_request(
            f"{url}/api/projects/{project['id']}/import",
            token,
            method="POST",
            body=tasks,
            timeout=120.0,
        )

    manifest_path = workspace / "workspace_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["label_studio_project_id"] = project["id"]
    manifest["project_url"] = f"{url}/projects/{project['id']}/data"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def create_label_studio_subset_project(
    workspace: Path,
    records: list[dict[str, Any]],
    *,
    title: str,
    description: str,
    label_config: str = LABEL_CONFIG,
    instruction: str | None = None,
) -> dict[str, Any]:
    """Create a separate Label Studio project for a fixed review subset."""
    if not records:
        raise ValueError("Cannot create an empty Label Studio review project")
    if len(title) > 50:
        raise ValueError("Label Studio project titles cannot exceed 50 characters")
    url, token = _workspace_connection(workspace)
    projects = _api_request(f"{url}/api/projects?page_size=100", token)
    project_rows = projects.get("results", projects) if isinstance(projects, dict) else projects
    matching = [row for row in project_rows if row.get("title") == title]
    if matching:
        project = matching[0]
        task_count = project.get("task_number")
        if task_count is not None and int(task_count) != len(records):
            raise RuntimeError(
                f"Existing project {project['id']} has {task_count} tasks; "
                f"the fixed subset has {len(records)}"
            )
        project = _api_request(
            f"{url}/api/projects/{project['id']}",
            token,
            method="PATCH",
            body={"label_config": label_config, "description": description},
        )
    else:
        project = _api_request(
            f"{url}/api/projects",
            token,
            method="POST",
            body={
                "title": title,
                "description": description,
                "label_config": label_config,
                "show_instruction": True,
                "expert_instruction": (
                    instruction
                    or "These candidates remained uncertain after conservative local "
                    "model-assisted triage. Review the full article and source page."
                ),
            },
        )
        _api_request(
            f"{url}/api/projects/{project['id']}/import",
            token,
            method="POST",
            body=[_task(record) for record in records],
            timeout=120.0,
        )
    return {
        "project_id": project["id"],
        "documents": len(records),
        "project_url": f"{url}/projects/{project['id']}/data?labeling=1",
    }


def _result_value(results: list[dict[str, Any]], name: str, field: str) -> list[str]:
    for result in results:
        if result.get("from_name") == name:
            values = result.get("value", {}).get(field) or []
            return [str(value) for value in values]
    return []


def _latest_annotation(task: dict[str, Any]) -> dict[str, Any] | None:
    annotations = [
        annotation
        for annotation in task.get("annotations") or []
        if not annotation.get("was_cancelled")
    ]
    if not annotations:
        return None
    return max(
        annotations,
        key=lambda annotation: annotation.get("updated_at")
        or annotation.get("created_at")
        or "",
    )


def label_studio_export_to_review_csv(
    tasks: list[dict[str, Any]], output: Path, *, reviewer: str
) -> dict[str, int]:
    """Convert raw Label Studio JSON to the benchmark's fail-closed review CSV."""
    counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for task in tasks:
        data = task["data"]
        annotation = _latest_annotation(task)
        row = {field: data.get(field, "") for field in REVIEW_FIELDS}
        row["label_evidence"] = json.dumps(
            data.get("label_evidence") or [], ensure_ascii=False
        )
        if annotation is None:
            counts["unreviewed"] += 1
            rows.append(row)
            continue

        results = annotation.get("result") or []
        decisions = _result_value(results, "decision", "choices")
        if decisions == ["Reviewed original"]:
            rationales = _result_value(results, "original_rationale", "choices")
            if len(rationales) != 1 or rationales[0] not in ORIGINAL_RATIONALES:
                raise RuntimeError(
                    f"Missing or invalid original rationale for {data.get('doc_id')}"
                )
            row["review_include"] = "yes"
            row["review_gold_label"] = "original"
            rationale = ORIGINAL_RATIONALES[rationales[0]]
            counts["accepted"] += 1
        elif decisions == ["Exclude or uncertain"]:
            rationales = _result_value(results, "exclusion_rationale", "choices")
            if len(rationales) != 1 or rationales[0] not in EXCLUSION_RATIONALES:
                raise RuntimeError(
                    f"Missing or invalid exclusion rationale for {data.get('doc_id')}"
                )
            row["review_include"] = "no"
            row["review_gold_label"] = ""
            rationale = EXCLUSION_RATIONALES[rationales[0]]
            counts["excluded"] += 1
        else:
            raise RuntimeError(f"Invalid decision for {data.get('doc_id')}: {decisions}")

        additional_notes = _result_value(results, "review_notes", "text")
        row["reviewer"] = reviewer
        row["reviewed_at"] = annotation.get("updated_at") or annotation.get("created_at")
        row["review_notes"] = " ".join([rationale, *additional_notes]).strip()
        rows.append(row)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return {
        "documents": len(rows),
        "accepted": counts["accepted"],
        "excluded": counts["excluded"],
        "unreviewed": counts["unreviewed"],
    }


def export_label_studio_decisions(
    workspace: Path, output: Path, *, reviewer: str | None = None
) -> dict[str, Any]:
    """Download current annotations and write a finalization-compatible CSV."""
    manifest = json.loads(
        (workspace / "workspace_manifest.json").read_text(encoding="utf-8")
    )
    project_id = manifest.get("label_studio_project_id")
    if not project_id:
        raise RuntimeError("The Label Studio review project has not been initialized")
    reviewer_id = (reviewer or manifest.get("default_reviewer") or "").strip()
    if not reviewer_id:
        raise ValueError("A reviewer identifier is required")
    return export_label_studio_project_decisions(
        workspace, int(project_id), output, reviewer=reviewer_id
    )


def export_label_studio_project_decisions(
    workspace: Path, project_id: int, output: Path, *, reviewer: str
) -> dict[str, Any]:
    """Export one Label Studio project's human annotations to review CSV."""
    url, token = _workspace_connection(workspace)
    query = urllib.parse.urlencode(
        {"exportType": "JSON", "download_all_tasks": "true"}
    )
    tasks = _api_request(
        f"{url}/api/projects/{project_id}/export?{query}", token, timeout=120.0
    )
    summary = label_studio_export_to_review_csv(tasks, output, reviewer=reviewer)
    return {
        **summary,
        "project_id": project_id,
        "output": str(output.resolve()),
        "reviewer": reviewer,
    }


VALUE_REVIEW_FIELDS = [
    "doc_id",
    "source",
    "published_at",
    "title",
    "url",
    "value_include",
    "value_rationale",
    "reviewer",
    "reviewed_at",
    "value_notes",
]


def export_label_studio_value_decisions(
    workspace: Path, project_id: int, output: Path, *, reviewer: str
) -> dict[str, Any]:
    """Export a research-value Label Studio project to a compact CSV."""
    url, token = _workspace_connection(workspace)
    query = urllib.parse.urlencode(
        {"exportType": "JSON", "download_all_tasks": "true"}
    )
    tasks = _api_request(
        f"{url}/api/projects/{project_id}/export?{query}", token, timeout=120.0
    )
    counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for task in tasks:
        data = task["data"]
        row = {field: data.get(field, "") for field in VALUE_REVIEW_FIELDS}
        annotation = _latest_annotation(task)
        if annotation is None:
            counts["unreviewed"] += 1
            rows.append(row)
            continue
        results = annotation.get("result") or []
        decisions = _result_value(results, "value_decision", "choices")
        if decisions == ["Keep substantive"]:
            rationales = _result_value(results, "substantive_rationale", "choices")
            row["value_include"] = "yes"
            counts["kept"] += 1
        elif decisions == ["Exclude low value"]:
            rationales = _result_value(results, "low_value_rationale", "choices")
            row["value_include"] = "no"
            counts["excluded"] += 1
        else:
            raise RuntimeError(
                f"Invalid research-value decision for {data.get('doc_id')}: {decisions}"
            )
        if len(rationales) != 1:
            raise RuntimeError(
                f"Missing research-value rationale for {data.get('doc_id')}"
            )
        row["value_rationale"] = rationales[0]
        row["reviewer"] = reviewer
        row["reviewed_at"] = annotation.get("updated_at") or annotation.get("created_at")
        row["value_notes"] = " ".join(
            _result_value(results, "value_notes", "text")
        ).strip()
        rows.append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VALUE_REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "documents": len(rows),
        "kept": counts["kept"],
        "excluded": counts["excluded"],
        "unreviewed": counts["unreviewed"],
        "project_id": project_id,
        "output": str(output.resolve()),
        "reviewer": reviewer,
    }
