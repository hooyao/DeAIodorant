"""Reproducible local entry point for the diagnostic acquisition pipeline."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pilot_collect import (
    POST_END,
    POST_START,
    PRE_END,
    PRE_START,
    TRANSLATION_PROMPT_VERSIONS,
)

from .integrity import validate_monthly_corpus


PIPELINE_VERSION = "local-corpus-pipeline-1"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _command_output(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _ollama_json(endpoint: str, route: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(f"{endpoint.rstrip('/')}{route}", timeout=10) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama preflight failed for {endpoint}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Ollama returned an unexpected response")
    return payload


def _ollama_model_metadata(endpoint: str, model: str) -> dict[str, Any]:
    payload = _ollama_json(endpoint, "/api/tags")
    for item in payload.get("models", []):
        if item.get("name") == model or item.get("model") == model:
            return {
                key: item.get(key)
                for key in ("name", "model", "modified_at", "size", "digest", "details")
            }
    raise RuntimeError(f"Ollama model is not installed: {model}")


def _repository_metadata(root: Path) -> dict[str, Any]:
    status = _command_output(["git", "-C", str(root), "status", "--porcelain"])
    return {
        "commit": _command_output(["git", "-C", str(root), "rev-parse", "HEAD"]),
        "branch": _command_output(["git", "-C", str(root), "branch", "--show-current"]),
        "dirty": bool(status) if status is not None else None,
    }


def _hardware_metadata() -> dict[str, Any]:
    query = _command_output(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    return {"nvidia_smi": query}


def _tee_process(command: list[str], cwd: Path, log_path: Path) -> int:
    with log_path.open("w", encoding="utf-8", newline="\n") as log_handle:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log_handle.write(line)
            log_handle.flush()
        return process.wait()


def _collection_completeness(output_dir: Path, target: int) -> dict[str, Any]:
    report_path = output_dir / "report.json"
    errors: list[str] = []
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"Cannot read collector report: {exc}"]}

    expected_cells = ("infoq_pre", "infoq_post", "jiqizhixin_pre")
    counts: dict[str, int | None] = {}
    for cell in expected_cells:
        value = report.get("cells", {}).get(cell, {}).get("documents")
        counts[cell] = value if isinstance(value, int) else None
        if not isinstance(value, int) or value < target:
            errors.append(f"{cell} produced {value!r} documents; expected at least {target}")
    return {"valid": not errors, "document_counts": counts, "errors": errors}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the diagnostic corpus collector and validate its monthly output."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target-per-cell", type=int, default=2)
    parser.add_argument("--max-attempts", type=int, default=80)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--http-timeout", type=float, default=45.0)
    parser.add_argument("--translation-timeout", type=float, default=600.0)
    parser.add_argument("--translation-model", default="qwen3.5:9b")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument(
        "--without-translation-model",
        action="store_true",
        help="Run deterministic translation checks only; suitable for diagnostics, not admission.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if sys.prefix == sys.base_prefix:
        raise SystemExit("The corpus pipeline must run inside a Python virtual environment")
    if args.target_per_cell < 1 or args.max_attempts < 1:
        raise SystemExit("Targets and attempt limits must be positive")

    repository_root = Path(__file__).resolve().parents[3]
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite a non-empty run directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    model = None if args.without_translation_model else args.translation_model
    model_metadata = _ollama_model_metadata(args.ollama_endpoint, model) if model else None
    collector_command = [
        sys.executable,
        str(repository_root / "pilot_collect.py"),
        "--target-per-cell",
        str(args.target_per_cell),
        "--output-dir",
        str(output_dir),
        "--delay",
        str(args.delay),
        "--max-attempts",
        str(args.max_attempts),
        "--http-timeout",
        str(args.http_timeout),
        "--translation-timeout",
        str(args.translation_timeout),
    ]
    if model:
        collector_command.extend(
            [
                "--translation-model",
                model,
                "--ollama-endpoint",
                args.ollama_endpoint,
                "--translation-cache",
                str(output_dir / "translation_model_cache.jsonl"),
            ]
        )

    manifest_path = output_dir / "run_manifest.json"
    manifest: dict[str, Any] = {
        "schema_version": PIPELINE_VERSION,
        "corpus_stage": "diagnostic_pilot",
        "status": "running",
        "started_at": _utc_now(),
        "completed_at": None,
        "repository": _repository_metadata(repository_root),
        "environment": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "virtual_environment": sys.prefix,
            "platform": platform.platform(),
            "hardware": _hardware_metadata(),
        },
        "configuration": {
            "target_per_cell": args.target_per_cell,
            "max_attempts": args.max_attempts,
            "delay_seconds": args.delay,
            "http_timeout_seconds": args.http_timeout,
            "translation_timeout_seconds": args.translation_timeout,
            "translation_model": model,
            "ollama_endpoint": args.ollama_endpoint if model else None,
            "translation_prompt_versions": TRANSLATION_PROMPT_VERSIONS if model else None,
            "selection_seeds": ["infoq-pre", "infoq-post", "jiqizhixin-url-sha256"],
            "windows": {
                "pre": [PRE_START.isoformat(), PRE_END.isoformat()],
                "post": [POST_START.isoformat(), POST_END.isoformat()],
                "transition_period_excluded": ["2023-01-01", "2025-06-30"],
            },
        },
        "ollama_model": model_metadata,
        "collector_command": collector_command,
        "integrity_report": "integrity_report.json",
        "limitations": [
            "This run is diagnostic pilot material, not a clean or final corpus.",
            "Manual quality and visibility review remains required.",
            "Machine Heart historical documents lack article-level visibility evidence.",
        ],
    }
    _write_json(manifest_path, manifest)

    dependencies = _command_output([sys.executable, "-m", "pip", "freeze", "--all"])
    (output_dir / "environment.txt").write_text((dependencies or "") + "\n", encoding="utf-8")

    try:
        return_code = _tee_process(
            collector_command, repository_root, output_dir / "collection.log"
        )
        if return_code:
            manifest["status"] = "collector_failed"
            manifest["collector_exit_code"] = return_code
            return return_code

        collection_gate = _collection_completeness(output_dir, args.target_per_cell)
        integrity = validate_monthly_corpus(
            output_dir / "monthly", required_translation_model=model
        )
        _write_json(output_dir / "integrity_report.json", integrity)
        manifest["collection_completeness"] = collection_gate
        manifest["integrity"] = {
            "valid": integrity["valid"],
            "documents": integrity["documents"],
            "months": integrity["months"],
            "unverified_visibility_documents": integrity[
                "unverified_visibility_documents"
            ],
            "model_gated_documents": integrity["model_gated_documents"],
        }
        if model:
            manifest["ollama_runtime"] = _ollama_json(args.ollama_endpoint, "/api/ps")
        succeeded = integrity["valid"] and collection_gate["valid"]
        manifest["status"] = (
            "complete"
            if succeeded
            else "integrity_failed"
            if not integrity["valid"]
            else "collection_incomplete"
        )
        return 0 if succeeded else 1
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        manifest["completed_at"] = _utc_now()
        _write_json(manifest_path, manifest)


if __name__ == "__main__":
    raise SystemExit(main())
