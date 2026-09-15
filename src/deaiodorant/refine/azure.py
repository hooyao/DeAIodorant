"""Private, single-attempt Azure Responses calls with durable budget estimates.

The default 10/30 USD per million tokens are conservative planning prices,
not verified Azure billing rates. Actual billed cost remains unknown. All
caches beside one dotenv configuration share its .azure-responses-budget
ledger; other clients, dotenv locations, or Azure account spending are outside
this local cap. No prompt, raw response body, or reasoning is persisted.
"""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
import json
import math
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterator
from urllib.parse import urlsplit
import uuid

import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from .openrouter import (
    OpenRouterError, _canonical, _money, _require_ignored_in_repository,
    _sha256, _utc_now, _write_json,
)


SCHEMA_VERSION = "compact-refiner-azure-responses-1.0"
_SETTINGS = ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_BASE_URL", "AZURE_OPENAI_DEPLOYMENT")
_SECRET_PATTERN = re.compile(r"sk-or-[A-Za-z0-9_-]+")
_LABEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,199}\Z")
_HASH_PATTERN = re.compile(r"[a-f0-9]{64}\Z")


class AzureResponsesError(RuntimeError):
    """A bounded failure that never includes SDK exception text or HTTP bodies."""

    def __init__(self, reason: str, metadata: dict[str, Any] | None = None):
        self.reason = reason
        self.metadata = metadata or {}
        super().__init__(f"Azure Responses request failed: {reason}.")


class BudgetError(AzureResponsesError):
    """The persistent local spending estimate cannot safely admit a request."""


class CompletionError(AzureResponsesError):
    """One paid attempt did not produce an admissible final answer."""


class ConcurrentUseError(AzureResponsesError):
    """Another client owns the deployment ledger lock."""


def _amount(value: Any, reason: str) -> Decimal:
    try:
        amount = _money(value, reason)
    except OpenRouterError:
        raise AzureResponsesError(reason) from None
    if amount <= 0:
        raise AzureResponsesError(reason)
    return amount


def _require_private_path(path: Path, *, directory: bool = False) -> None:
    """Require a Git ignored path and reject tracked files within directories."""
    path = path.resolve()
    repository = next((p for p in (path.parent, *path.parents) if (p / ".git").exists()), None)
    if repository is None:
        raise AzureResponsesError("cannot_verify_private_artifact_path")
    try:
        _require_ignored_in_repository(path / "privacy-check" if directory else path)
        if directory:
            tracked = subprocess.run(
                ["git", "ls-files", "-z", "--", str(path)], cwd=repository,
                capture_output=True, check=False, timeout=10,
            )
            if tracked.returncode != 0:
                raise AzureResponsesError("cannot_verify_private_artifact_path")
            if tracked.stdout:
                raise AzureResponsesError("artifact_path_contains_tracked_files")
    except OpenRouterError:
        raise AzureResponsesError("artifact_path_is_not_git_ignored") from None
    except (OSError, subprocess.SubprocessError):
        raise AzureResponsesError("cannot_verify_private_artifact_path") from None


def _load_settings(path: Path) -> dict[str, str]:
    if path.name.lower() != ".env":
        raise AzureResponsesError("credential_file_must_be_dotenv")
    _require_private_path(path)
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        raise AzureResponsesError("credential_file_unreadable") from None
    settings: dict[str, str] = {}
    for line in lines:
        match = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)(.*)$", line)
        if not match or match[1] not in _SETTINGS:
            continue
        name, assignment = match[1], match[2].strip()
        if name in settings:
            raise AzureResponsesError("duplicate_azure_setting")
        if not assignment.startswith("="):
            raise AzureResponsesError("invalid_azure_setting")
        value = assignment[1:].strip()
        if value[:1] in {"'", '"'}:
            closing = value.find(value[0], 1)
            remainder = value[closing + 1:].strip() if closing >= 1 else ""
            if closing < 1 or (remainder and not remainder.startswith("#")):
                raise AzureResponsesError("invalid_azure_setting")
            value = value[1:closing]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        if not value or any(c.isspace() or ord(c) < 32 for c in value):
            raise AzureResponsesError("invalid_azure_setting")
        settings[name] = value
    if set(settings) != set(_SETTINGS):
        raise AzureResponsesError("missing_azure_setting")
    return settings


def _base_url(value: str) -> str:
    try:
        url = urlsplit(value)
        host = url.hostname or ""
        valid_host = all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part) for part in host.split("."))
        if (
            url.scheme != "https" or not valid_host or len(host) > 253
            or not host.endswith((".services.ai.azure.com", ".openai.azure.com"))
            or url.username is not None or url.password is not None
            or url.port not in {None, 443} or url.query or url.fragment
            or "?" in value or "#" in value or any(c.isspace() for c in value)
            or url.path not in {"/openai/v1", "/openai/v1/"}
        ):
            raise ValueError
    except ValueError:
        raise AzureResponsesError("invalid_azure_base_url") from None
    return f"https://{host}/openai/v1/"


def _field(value: Any, name: str) -> Any:
    return value.get(name) if isinstance(value, dict) else getattr(value, name, None)


def _usage(value: Any) -> dict[str, int] | None:
    counts = {name: _field(value, name) for name in ("input_tokens", "output_tokens", "total_tokens")}
    if any(isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= 10**12 for n in counts.values()):
        return None
    if counts["total_tokens"] != counts["input_tokens"] + counts["output_tokens"]:
        return None
    return counts


class AzureResponsesClient:
    """Send text through the configured Azure deployment without retries.

    ``purpose`` is a short audit label, excluded from model input and cache
    identity. Unknown usage retains the full reservation, including after a
    timeout or process interruption. Reusing the ledger requires the same
    endpoint, deployment, cap, and planning prices. API key rotation is allowed.
    """

    def __init__(
        self, env_path: str | Path, cache_dir: str | Path,
        budget_usd: str | float | Decimal = "45",
        input_usd_per_million: str | float | Decimal = "10",
        output_usd_per_million: str | float | Decimal = "30",
        timeout_seconds: float = 45,
    ) -> None:
        self.budget_usd = _amount(budget_usd, "invalid_budget")
        self.input_price = _amount(input_usd_per_million, "invalid_input_plan_price")
        self.output_price = _amount(output_usd_per_million, "invalid_output_plan_price")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 600:
            raise AzureResponsesError("invalid_timeout")
        env_path = Path(env_path).resolve()
        settings = _load_settings(env_path)
        self._api_key = settings["AZURE_OPENAI_API_KEY"]
        if _SECRET_PATTERN.search(self._api_key):
            raise AzureResponsesError("openrouter_key_is_not_azure_credential")
        self._base_url = _base_url(settings["AZURE_OPENAI_BASE_URL"])
        self.deployment = settings["AZURE_OPENAI_DEPLOYMENT"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.deployment) or self._contains_secret(self.deployment):
            raise AzureResponsesError("invalid_azure_deployment")
        self.cache_dir = Path(cache_dir).resolve()
        self.ledger_dir = (env_path.parent / ".azure-responses-budget").resolve()
        self._ledger_path = self.ledger_dir / "ledger.json"
        for directory in (self.cache_dir, self.ledger_dir):
            _require_private_path(directory, directory=True)
            try:
                directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            except OSError:
                raise AzureResponsesError("private_storage_unavailable") from None
        self._configuration = {
            "endpoint_sha256": _sha256(self._base_url),
            "deployment": self.deployment,
            "budget_usd": str(self.budget_usd),
            "input_usd_per_million": str(self.input_price),
            "output_usd_per_million": str(self.output_price),
        }
        self._configuration_hash = _sha256(self._configuration)
        with self._exclusive():
            self._read_ledger()
        self._http = httpx.Client(timeout=timeout_seconds, follow_redirects=False, trust_env=False)
        try:
            self._client = OpenAI(
                api_key=self._api_key, base_url=self._base_url,
                organization="", project="", max_retries=0,
                timeout=timeout_seconds, http_client=self._http,
            )
        except Exception:
            self._http.close()
            raise AzureResponsesError("sdk_initialization_failed") from None
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            try:
                try:
                    self._client.close()
                finally:
                    self._http.close()
            except Exception:
                raise AzureResponsesError("sdk_close_failed") from None
            finally:
                self._closed = True

    def __enter__(self) -> AzureResponsesClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _contains_secret(self, value: Any) -> bool:
        serialized = _canonical(value).decode("utf-8")
        return self._api_key in serialized or bool(_SECRET_PATTERN.search(serialized))

    def _label(self, value: Any) -> str | None:
        if isinstance(value, str) and _LABEL_PATTERN.fullmatch(value) and not self._contains_secret(value) and urlsplit(self._base_url).hostname not in value:
            return value
        return None

    @contextmanager
    def _exclusive(self) -> Iterator[None]:
        _require_private_path(self.ledger_dir, directory=True)
        _require_private_path(self.ledger_dir / "writer.lock")
        lock = None
        locked = False
        try:
            lock = (self.ledger_dir / "writer.lock").open("a+b")
            lock.seek(0, os.SEEK_END)
            if not lock.tell():
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                raise ConcurrentUseError("deployment_writer_is_busy") from None
            yield
        except OSError:
            raise AzureResponsesError("private_storage_unavailable") from None
        finally:
            if lock is not None:
                if locked:
                    lock.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                lock.close()

    def _estimated_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        return (self.input_price * input_tokens + self.output_price * output_tokens) / 1_000_000

    def _read_ledger(self) -> dict[str, Any]:
        _require_private_path(self._ledger_path)
        _require_private_path(self.ledger_dir / "initialized.json")
        if not self._ledger_path.exists():
            if any(self.cache_dir.glob("result-*.json")) or (self.ledger_dir / "initialized.json").exists():
                raise BudgetError("ledger_missing_after_initialization")
            ledger = {"schema_version": SCHEMA_VERSION, "configuration": self._configuration,
                      "configuration_sha256": self._configuration_hash, "transactions": []}
            _write_json(self._ledger_path, ledger)
            _write_json(self.ledger_dir / "initialized.json", {"schema_version": SCHEMA_VERSION})
            return ledger
        try:
            ledger = json.loads(self._ledger_path.read_text(encoding="utf-8"))
            if ledger["schema_version"] != SCHEMA_VERSION or not isinstance(ledger["transactions"], list):
                raise ValueError
            if ledger["configuration"] != self._configuration or ledger["configuration_sha256"] != self._configuration_hash:
                raise BudgetError("configuration_differs_from_persisted_ledger")
            seen = set()
            for item in ledger["transactions"]:
                if item["transaction_id"] in seen or item["status"] not in {"reserved", "success", "failed"}:
                    raise ValueError
                seen.add(item["transaction_id"])
                if not _HASH_PATTERN.fullmatch(item["request_sha256"]):
                    raise ValueError
                for name in ("purpose", "response_id", "returned_model", "response_status", "failure_reason"):
                    if item[name] is not None and self._label(item[name]) != item[name]:
                        raise ValueError
                reservation = self._estimated_cost(item["input_token_reserve"], item["max_output_tokens"])
                if reservation <= 0 or Decimal(item["initial_reservation_usd"]) != reservation:
                    raise ValueError
                usage = _usage(item["usage"])
                if item["cost_basis"] == "usage_at_plan_prices" and item["status"] != "reserved" and usage is not None:
                    expected = self._estimated_cost(usage["input_tokens"], usage["output_tokens"])
                elif item["cost_basis"] == "conservative_reservation" and usage is None:
                    expected = reservation
                else:
                    raise ValueError
                if Decimal(item["accounted_usd"]) != expected or (item["status"] == "success" and usage is None):
                    raise ValueError
        except BudgetError:
            raise
        except (OSError, ValueError, KeyError, TypeError, ArithmeticError):
            raise BudgetError("ledger_invalid") from None
        if self._accounted(ledger) > self.budget_usd:
            raise BudgetError("persisted_estimate_exceeds_cap")
        return ledger

    @staticmethod
    def _accounted(ledger: dict[str, Any]) -> Decimal:
        return sum((Decimal(item["accounted_usd"]) for item in ledger["transactions"]), Decimal(0))

    def budget_status(self) -> dict[str, Any]:
        with self._exclusive():
            ledger = self._read_ledger()
            accounted = self._accounted(ledger)
            return {
                "budget_usd": str(self.budget_usd), "accounted_usd": str(accounted),
                "remaining_usd": str(self.budget_usd - accounted), "actual_billed_usd": None,
                "basis": "local_budget_estimate_not_verified_billing",
                "unfinished_reservations": sum(t["status"] == "reserved" for t in ledger["transactions"]),
                "retained_unknown_cost_reservations": sum(t["cost_basis"] == "conservative_reservation" for t in ledger["transactions"]),
            }

    def _metadata(self, transaction: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION, "configuration_sha256": self._configuration_hash,
            "endpoint_sha256": self._configuration["endpoint_sha256"],
            "requested_deployment": self.deployment,
            **{name: transaction[name] for name in (
                "transaction_id", "request_sha256", "purpose", "created_at_utc", "finished_at_utc",
                "response_id", "returned_model", "response_status", "usage", "failure_reason",
                "max_output_tokens", "temperature",
            )},
            "budget_estimate": {
                "accounted_usd": transaction["accounted_usd"],
                "initial_reservation_usd": transaction["initial_reservation_usd"],
                "input_token_reserve": transaction["input_token_reserve"],
                "input_usd_per_million": str(self.input_price),
                "output_usd_per_million": str(self.output_price),
                "basis": transaction["cost_basis"], "rates_are_verified_billing": False,
            },
            "actual_billed_usd": None, "attempt_count": 1, "store": False, "cache_hit": False,
        }

    def complete(
        self, input_text: str, instructions: str | None = None,
        max_output_tokens: int = 4096, temperature: float = 0,
        purpose: str | None = None,
    ) -> dict[str, Any]:
        """Return final text and safe metadata; never automatically retry."""
        if self._closed:
            raise AzureResponsesError("client_is_closed")
        if not isinstance(input_text, str) or not input_text.strip() or (instructions is not None and not isinstance(instructions, str)):
            raise AzureResponsesError("only_nonempty_text_input_is_supported")
        if isinstance(max_output_tokens, bool) or not isinstance(max_output_tokens, int) or max_output_tokens < 1:
            raise AzureResponsesError("invalid_max_output_tokens")
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise AzureResponsesError("invalid_temperature")
        if purpose is not None and self._label(purpose) != purpose:
            raise AzureResponsesError("invalid_purpose_label")
        body = {"model": self.deployment, "input": input_text, "max_output_tokens": max_output_tokens,
                "temperature": temperature, "store": False}
        if instructions is not None:
            body["instructions"] = instructions
        if self._contains_secret(body):
            raise AzureResponsesError("credential_in_request_content")
        request_hash = _sha256({"configuration_sha256": self._configuration_hash, "body": body})
        input_reserve = len(_canonical(body)) + 4096 + 256 * (1 + (instructions is not None))
        reservation = self._estimated_cost(input_reserve, max_output_tokens)
        with self._exclusive():
            _require_private_path(self.cache_dir, directory=True)
            ledger = self._read_ledger()
            cache_path = self.cache_dir / f"result-{request_hash}.json"
            _require_private_path(cache_path)
            if cache_path.exists():
                try:
                    cached = json.loads(cache_path.read_text(encoding="utf-8"))
                    transaction = next(t for t in ledger["transactions"] if t["transaction_id"] == cached["metadata"]["transaction_id"])
                    if (set(cached) != {"text", "metadata"} or transaction["status"] != "success"
                            or transaction["request_sha256"] != request_hash or cached["metadata"] != self._metadata(transaction)
                            or not isinstance(cached["text"], str) or not cached["text"].strip()
                            or _sha256(cached["text"]) != transaction["text_sha256"] or self._contains_secret(cached)):
                        raise ValueError
                except (OSError, ValueError, KeyError, TypeError, StopIteration):
                    raise AzureResponsesError("cached_result_invalid") from None
                cached["metadata"]["cache_hit"] = True
                return cached
            if any(t["request_sha256"] == request_hash and t["status"] == "success" for t in ledger["transactions"]):
                raise AzureResponsesError("successful_result_cache_missing")
            if self._accounted(ledger) + reservation > self.budget_usd:
                raise BudgetError("insufficient_budget_for_reservation", {
                    "required_reservation_usd": str(reservation),
                    "remaining_usd": str(self.budget_usd - self._accounted(ledger)),
                })
            transaction = {
                "transaction_id": uuid.uuid4().hex, "request_sha256": request_hash,
                "purpose": purpose, "created_at_utc": _utc_now(), "finished_at_utc": None,
                "status": "reserved", "input_token_reserve": input_reserve,
                "max_output_tokens": max_output_tokens, "temperature": temperature,
                "initial_reservation_usd": str(reservation), "accounted_usd": str(reservation),
                "cost_basis": "conservative_reservation", "response_id": None, "returned_model": None,
                "response_status": None, "usage": None, "failure_reason": None,
            }
            ledger["transactions"].append(transaction)
            _write_json(self._ledger_path, ledger)
            text, reason = self._perform_attempt(body, transaction)
            transaction.update(status="success" if reason is None else "failed", failure_reason=reason, finished_at_utc=_utc_now())
            if reason is None:
                transaction["text_sha256"] = _sha256(text)
            _write_json(self._ledger_path, ledger)
            metadata = self._metadata(transaction)
            if self._accounted(ledger) > self.budget_usd:
                raise BudgetError("usage_estimate_exceeds_cap", metadata)
            if reason is not None:
                raise CompletionError(reason, metadata)
            result = {"text": text, "metadata": metadata}
            _write_json(cache_path, result)
            return result

    def _perform_attempt(self, body: dict[str, Any], transaction: dict[str, Any]) -> tuple[str | None, str | None]:
        try:
            response = self._client.responses.create(**body)
        except (APITimeoutError, httpx.TimeoutException):
            return None, "timeout_billing_unknown"
        except APIStatusError as error:
            status = error.status_code
            return None, f"http_{status}_billing_unknown" if isinstance(status, int) and 300 <= status <= 599 else "http_failure_billing_unknown"
        except (APIConnectionError, httpx.TransportError):
            return None, "transport_failure_billing_unknown"
        except Exception:
            return None, "sdk_failure_billing_unknown"
        try:
            transaction["response_id"] = self._label(_field(response, "id"))
            transaction["returned_model"] = self._label(_field(response, "model"))
            transaction["response_status"] = self._label(_field(response, "status"))
            usage = _usage(_field(response, "usage"))
            transaction["usage"] = usage
            if usage is not None:
                transaction["accounted_usd"] = str(self._estimated_cost(usage["input_tokens"], usage["output_tokens"]))
                transaction["cost_basis"] = "usage_at_plan_prices"
            output = _field(response, "output")
            if isinstance(output, list) and any(
                _field(part, "type") == "refusal" for item in output
                for part in (_field(item, "content") or [])
            ):
                return None, "response_refused"
            if transaction["response_status"] != "completed":
                return None, "incomplete_or_failed_response"
            text = response.output_text
            if not isinstance(text, str) or not text.strip():
                return None, "empty_or_nontext_output"
            if self._contains_secret(text):
                return None, "credential_in_response_content"
            if re.search(r"</?(?:think|analysis|reasoning)(?:\s[^>]*)?>", text, flags=re.IGNORECASE):
                return None, "reasoning_markup_in_final_content"
            if usage is None:
                return None, "missing_or_invalid_usage"
            if usage["input_tokens"] > transaction["input_token_reserve"] or usage["output_tokens"] > body["max_output_tokens"]:
                return None, "token_usage_exceeds_reservation"
            return text, None
        except Exception:
            return None, "invalid_response_billing_unknown"
