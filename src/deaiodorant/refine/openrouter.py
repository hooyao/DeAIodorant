"""Bounded, private OpenRouter inference for development experiments.

The caller supplies frozen catalog prices in USD per token. Only text requests
are supported; models with additional per-request or other non-token charges
must not use this client. Provider price ceilings use USD per million tokens.
Reservations use UTF-8 bytes plus conservative message overhead, not a measured
token count. Unexpected provider billing can only be detected after a response;
the ledger records it and stops instead of claiming a guaranteed external cap.

Artifacts are private caches, not operational logs. They contain final answer
text, but never input text, raw HTTP bodies, credentials, or reasoning content.
An interrupted request retains its whole reservation across process restarts.
The same cache directory must be used for all calls sharing one spending cap.
An OS lock prevents simultaneous writers; inherited filesystem permissions
remain the operator's responsibility on Windows.

Client 1.1 honors Retry-After on HTTP 429/503. Waits longer than 60 seconds
return RetryDeferredError with a durable not-before deadline; callers must
schedule a later invocation rather than starting an early retry. Existing
successful caches and ledger accounting remain readable without migration.
"""

from __future__ import annotations

from contextlib import contextmanager
import datetime as dt
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Iterator
import uuid

import requests


MODELS_URL = "https://openrouter.ai/api/v1/models"
COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
SCHEMA_VERSION = "compact-refiner-openrouter-1.0"
CLIENT_VERSION = "compact-refiner-openrouter-1.1"
RETRY_POLICY_VERSION = "openrouter-retry-after-1.0"
MAX_RETRY_SLEEP_SECONDS = 60
TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
_SECRET_PATTERN = re.compile(r"sk-or-v1-[A-Za-z0-9_-]+")
_LABEL_PATTERN = re.compile(r"[A-Za-z0-9 ._:/()+@-]{1,200}\Z")


class OpenRouterError(RuntimeError):
    """An inference failure with a bounded, secret-free reason code."""

    def __init__(self, reason: str, metadata: dict[str, Any] | None = None):
        self.reason = reason
        self.metadata = metadata or {}
        super().__init__(f"OpenRouter request failed: {reason}.")


class BudgetError(OpenRouterError):
    """A request cannot safely proceed under the durable spending cap."""


class ConcurrentUseError(OpenRouterError):
    """Another process or client currently owns the same private cache."""


class CompletionError(OpenRouterError):
    """A paid attempt did not yield an admissible final answer."""


class RetryDeferredError(OpenRouterError):
    """A server deadline requires a later invocation instead of an early retry."""


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_now() -> str:
    return _now_utc().isoformat()


def _retry_plan(status: int | None, headers: Any, attempt_index: int) -> dict[str, Any]:
    """Normalize a retry deadline without retaining arbitrary header text."""

    now = _now_utc()
    delay = min(15 * 2 ** attempt_index, MAX_RETRY_SLEEP_SECONDS)
    source = "default_backoff"
    header = headers.get("Retry-After") if status in {429, 503} else None
    if header is not None:
        source = "invalid_retry_after_default"
        if isinstance(header, str):
            value = header.strip()
            if re.fullmatch(r"[0-9]+", value):
                # A syntactically valid enormous interval must defer, never
                # degrade to a short default wait after a conversion overflow.
                digits = value.lstrip("0") or "0"
                if len(digits) > 12:
                    return {
                        "retry_policy_version": RETRY_POLICY_VERSION,
                        "source": "server_seconds_outside_datetime_range",
                        "delay_seconds": None,
                        "retry_not_before_utc": None,
                        "manual_retry_required": True,
                        "deferred": True,
                    }
                seconds = int(digits)
                try:
                    now + dt.timedelta(seconds=seconds)
                except OverflowError:
                    return {
                        "retry_policy_version": RETRY_POLICY_VERSION,
                        "source": "server_seconds_outside_datetime_range",
                        "delay_seconds": None,
                        "retry_not_before_utc": None,
                        "manual_retry_required": True,
                        "deferred": True,
                    }
                delay = seconds or delay
                source = "server_seconds"
            elif len(value) <= 200:
                try:
                    deadline = parsedate_to_datetime(value)
                    if deadline.tzinfo is None:
                        raise ValueError
                    seconds = max(0, math.ceil((deadline - now).total_seconds()))
                except (TypeError, ValueError, OverflowError):
                    pass
                else:
                    delay = seconds or delay
                    source = "server_http_date"
    return {
        "retry_policy_version": RETRY_POLICY_VERSION,
        "source": source,
        "delay_seconds": delay,
        "retry_not_before_utc": (now + dt.timedelta(seconds=delay)).isoformat(),
        "manual_retry_required": False,
        "deferred": delay > MAX_RETRY_SLEEP_SECONDS,
    }


def _enforce_pending_server_retry(plans: list[dict[str, Any]]) -> None:
    """Prevent fresh calls from bypassing a persisted server cooldown."""

    pending = []
    for plan in plans:
        if not isinstance(plan, dict):
            raise OpenRouterError("persisted_retry_state_invalid")
        if not plan.get("source", "").startswith("server_"):
            continue
        if plan.get("manual_retry_required"):
            raise RetryDeferredError("retry_after_requires_manual_resolution", {
                "retry": plan, "retry_not_before_utc": None,
            })
        try:
            deadline = dt.datetime.fromisoformat(plan["retry_not_before_utc"])
            if deadline.tzinfo is None:
                raise ValueError
        except (TypeError, ValueError, KeyError):
            raise OpenRouterError("persisted_retry_state_invalid") from None
        if deadline > _now_utc():
            pending.append((deadline, plan))
    if pending:
        _, plan = max(pending, key=lambda item: item[0])
        raise RetryDeferredError("retry_not_before_deadline", {
            "retry": plan, "retry_not_before_utc": plan["retry_not_before_utc"],
        })


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _money(value: Any, reason: str = "invalid_price") -> Decimal:
    if isinstance(value, bool):
        raise OpenRouterError(reason)
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise OpenRouterError(reason) from None
    if not amount.is_finite() or amount < 0:
        raise OpenRouterError(reason)
    return amount


def _write_json(path: Path, data: Any) -> None:
    """Replace a JSON artifact atomically after flushing its contents."""

    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(_canonical(data) + b"\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _require_ignored_in_repository(path: Path) -> None:
    """Reject tracked/unignored artifacts when an enclosing checkout exists."""

    for parent in (path.parent, *path.parents):
        if (parent / ".git").exists():
            try:
                checked = subprocess.run(
                    ["git", "check-ignore", "-q", "--", str(path)],
                    cwd=parent, capture_output=True, check=False,
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError):
                raise OpenRouterError("cannot_verify_private_artifact_path") from None
            if checked.returncode != 0:
                raise OpenRouterError("artifact_path_is_not_git_ignored")
            return


def _load_api_key(path: Path) -> str:
    """Read only the named dotenv assignment without environment mutation."""

    if os.path.normcase(path.name) != os.path.normcase(".env"):
        raise OpenRouterError("credential_file_must_be_dotenv")
    _require_ignored_in_repository(path)
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        raise OpenRouterError("credential_file_unreadable") from None
    matches: list[str] = []
    for line in lines:
        match = re.match(r"^\s*(?:export\s+)?OPENAI_API_KEY\s*=\s*(.*?)\s*$", line)
        if not match:
            continue
        value = match.group(1)
        if value[:1] in {"'", '"'}:
            quote = value[0]
            closing = value.find(quote, 1)
            remainder = value[closing + 1 :].strip() if closing >= 1 else ""
            if closing < 1 or (remainder and not remainder.startswith("#")):
                raise OpenRouterError("invalid_credential_assignment")
            value = value[1:closing]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        if not value or any(character.isspace() for character in value):
            raise OpenRouterError("invalid_credential_assignment")
        matches.append(value)
    if len(matches) != 1:
        raise OpenRouterError("missing_or_duplicate_api_key")
    return matches[0]


class OpenRouterClient:
    """Single-writer client with full request identity and durable accounting.

    A changed cap requires a new explicitly budgeted cache directory; reopening
    an existing ledger with a different budget is rejected. ``max_retries`` is
    limited to 0-3. Transient retries repeat exactly the same request body.
    Failed attempts are retained and not reused as successful completions.
    """

    def __init__(
        self,
        env_path: str | Path,
        cache_dir: str | Path,
        budget_usd: str | float | Decimal,
        timeout_seconds: float = 120,
        max_retries: int = 2,
    ) -> None:
        self.budget_usd = _money(budget_usd, "invalid_budget")
        if self.budget_usd <= 0:
            raise BudgetError("budget_must_be_positive")
        if isinstance(max_retries, bool) or not isinstance(max_retries, int) or not 0 <= max_retries <= 3:
            raise OpenRouterError("invalid_retry_limit")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 600:
            raise OpenRouterError("invalid_timeout")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._api_key = _load_api_key(Path(env_path).resolve())
        self.cache_dir = Path(cache_dir).resolve()
        _require_ignored_in_repository(self.cache_dir / "ledger.json")
        self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._ledger_path = self.cache_dir / "ledger.json"
        self._session = requests.Session()
        self._session.trust_env = False
        with self._exclusive():
            self._read_ledger()

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> OpenRouterClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @contextmanager
    def _exclusive(self) -> Iterator[None]:
        lock = (self.cache_dir / "writer.lock").open("a+b")
        locked = False
        try:
            lock.seek(0, os.SEEK_END)
            if lock.tell() == 0:
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
                raise ConcurrentUseError("cache_writer_is_busy") from None
            yield
        finally:
            if locked:
                lock.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def _read_ledger(self) -> dict[str, Any]:
        if not self._ledger_path.exists():
            if any(self.cache_dir.glob("result-*.json")):
                raise BudgetError("ledger_missing_but_cache_exists")
            ledger: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "budget_usd": str(self.budget_usd),
                "created_at_utc": _utc_now(),
                "transactions": [],
            }
            _write_json(self._ledger_path, ledger)
            return ledger
        try:
            ledger = json.loads(self._ledger_path.read_text(encoding="utf-8"))
            if ledger["schema_version"] != SCHEMA_VERSION or not isinstance(ledger["transactions"], list):
                raise ValueError
            if _money(ledger["budget_usd"]) != self.budget_usd:
                raise BudgetError("budget_differs_from_persisted_cap")
            for transaction in ledger["transactions"]:
                accounted = _money(transaction["accounted_usd"])
                if transaction["status"] not in {"reserved", "finished"}:
                    raise ValueError
                reserved = _money(transaction["initial_reservation_usd"])
                attempts = transaction["attempts"]
                if not isinstance(attempts, list):
                    raise ValueError
                if transaction["status"] == "reserved" and accounted != reserved:
                    raise ValueError
                if transaction["status"] == "finished":
                    if not attempts or any(item["status"] not in {"success", "failed"} for item in attempts):
                        raise ValueError
                    actual = sum((_money(item["accounted_usd"]) for item in attempts), Decimal(0))
                    if accounted != actual:
                        raise ValueError
        except BudgetError:
            raise
        except (OSError, ValueError, KeyError, TypeError, OpenRouterError):
            raise BudgetError("ledger_invalid") from None
        if self._accounted(ledger) > self.budget_usd:
            raise BudgetError("persisted_cost_exceeds_cap")
        return ledger

    @staticmethod
    def _accounted(ledger: dict[str, Any]) -> Decimal:
        return sum((_money(item["accounted_usd"]) for item in ledger["transactions"]), Decimal(0))

    def budget_status(self) -> dict[str, Any]:
        """Return measured-or-reserved totals without exposing prompts or keys."""

        with self._exclusive():
            ledger = self._read_ledger()
            accounted = self._accounted(ledger)
            return {
                "budget_usd": str(self.budget_usd),
                "accounted_usd": str(accounted),
                "remaining_usd": str(self.budget_usd - accounted),
                "unfinished_reservations": sum(item["status"] == "reserved" for item in ledger["transactions"]),
            }

    def _contains_secret(self, value: Any) -> bool:
        serialized = _canonical(value).decode("utf-8")
        return self._api_key in serialized or bool(_SECRET_PATTERN.search(serialized))

    def _label(self, value: Any) -> str | None:
        if isinstance(value, str) and _LABEL_PATTERN.fullmatch(value) and not self._contains_secret(value):
            return value
        return None

    def fetch_models(self) -> dict[str, Any]:
        """Fetch and privately snapshot the public model catalog without auth."""

        with self._exclusive():
            retry_state_path = self.cache_dir / "catalog-retry-state.json"
            if retry_state_path.exists():
                try:
                    retry_state = json.loads(retry_state_path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    raise OpenRouterError("persisted_retry_state_invalid") from None
                _enforce_pending_server_retry([retry_state])
            for attempt in range(self.max_retries + 1):
                reason = "catalog_request_failed"
                transient = False
                retry = None
                try:
                    response = self._session.get(
                        MODELS_URL, timeout=self.timeout_seconds,
                        allow_redirects=False,
                    )
                    transient = response.status_code in TRANSIENT_STATUS_CODES
                    if response.status_code == 200:
                        try:
                            payload = response.json()
                        except (ValueError, TypeError):
                            raise OpenRouterError("catalog_invalid_json") from None
                        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list) or self._contains_secret(payload):
                            raise OpenRouterError("catalog_invalid_payload")
                        snapshot = {
                            "schema_version": SCHEMA_VERSION,
                            "client_version": CLIENT_VERSION,
                            "retry_policy_version": RETRY_POLICY_VERSION,
                            "url": MODELS_URL,
                            "fetched_at_utc": _utc_now(),
                            "snapshot_sha256": _sha256(payload),
                            "data": payload["data"],
                        }
                        _write_json(self.cache_dir / f"catalog-{snapshot['snapshot_sha256']}.json", snapshot)
                        return snapshot
                    reason = f"catalog_http_{response.status_code}"
                    if transient:
                        retry = _retry_plan(response.status_code, getattr(response, "headers", {}), attempt)
                except (requests.Timeout, requests.ConnectionError):
                    transient = True
                    reason = "catalog_transport_failure"
                except requests.RequestException:
                    reason = "catalog_request_failure"
                if transient:
                    retry = retry or _retry_plan(None, {}, attempt)
                    _write_json(retry_state_path, retry)
                    if retry["deferred"]:
                        raise RetryDeferredError("catalog_retry_after_exceeds_wait_limit", {
                            "retry": retry,
                            "retry_not_before_utc": retry["retry_not_before_utc"],
                            "upstream_failure_reason": reason,
                        })
                if not transient or attempt == self.max_retries:
                    raise OpenRouterError(reason, {"retry": retry})
                time.sleep(retry["delay_seconds"])
        raise AssertionError("Unreachable catalog retry state")

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        prompt_price_per_token: str | float | Decimal,
        completion_price_per_token: str | float | Decimal,
        max_tokens: int,
        temperature: float = 0,
        reasoning: dict[str, Any] | None = None,
        seed: int | None = 20260914,
        purpose: str | None = None,
    ) -> dict[str, Any]:
        """Return ``{text, metadata}``, or raise a safe typed failure.

        ``reasoning=None`` omits the field; it does not disable provider defaults.
        The response is accepted only with nonempty text, ``finish_reason=stop``,
        token usage, and an explicit nonnegative ``usage.cost``. Reasoning fields
        in the response are never retained. ``purpose`` is a short audit label,
        not model input, and does not change cache identity.
        """

        prompt_price = _money(prompt_price_per_token)
        completion_price = _money(completion_price_per_token)
        if self._label(model) != model or not model:
            raise OpenRouterError("invalid_model_id")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
            raise OpenRouterError("invalid_max_tokens")
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise OpenRouterError("invalid_temperature")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise OpenRouterError("invalid_seed")
        if purpose is not None and self._label(purpose) != purpose:
            raise OpenRouterError("invalid_purpose_label")
        if not isinstance(messages, list) or not messages:
            raise OpenRouterError("missing_messages")
        for message in messages:
            if not isinstance(message, dict) or set(message) != {"role", "content"} or message["role"] not in {"system", "user", "assistant"} or not isinstance(message["content"], str):
                raise OpenRouterError("only_text_messages_are_supported")
        if reasoning is not None:
            if not isinstance(reasoning, dict) or not set(reasoning) <= {"effort", "max_tokens", "exclude", "enabled"}:
                raise OpenRouterError("invalid_reasoning_configuration")
            if "effort" in reasoning and (not isinstance(reasoning["effort"], str) or reasoning["effort"] not in {"none", "minimal", "low", "medium", "high", "xhigh", "max"}):
                raise OpenRouterError("invalid_reasoning_configuration")
            for boolean_field in ("enabled", "exclude"):
                if boolean_field in reasoning and not isinstance(reasoning[boolean_field], bool):
                    raise OpenRouterError("invalid_reasoning_configuration")
            if "max_tokens" in reasoning and (isinstance(reasoning["max_tokens"], bool) or not isinstance(reasoning["max_tokens"], int) or not 0 < reasoning["max_tokens"] <= max_tokens):
                raise OpenRouterError("invalid_reasoning_configuration")
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "usage": {"include": True},
            "provider": {
                "allow_fallbacks": False,
                "max_price": {
                    "prompt": float(prompt_price * 1_000_000),
                    "completion": float(completion_price * 1_000_000),
                },
            },
        }
        if seed is not None:
            body["seed"] = seed
        if reasoning is not None:
            body["reasoning"] = reasoning
        if self._contains_secret(body):
            raise OpenRouterError("credential_in_request_content")
        identity = {"method": "POST", "url": COMPLETIONS_URL, "body": body}
        request_hash = _sha256(identity)
        # UTF-8 bytes deliberately overestimate text tokens; extra framing is
        # reserved because the hosted model's exact tokenizer is not available.
        estimated_input_tokens = len(_canonical(body)) + 4096 + 256 * len(messages)
        upper_per_attempt = prompt_price * estimated_input_tokens + completion_price * max_tokens
        reserved_usd = upper_per_attempt * (self.max_retries + 1)
        config = {key: value for key, value in body.items() if key != "messages"}
        with self._exclusive():
            ledger = self._read_ledger()
            cache_path = self.cache_dir / f"result-{request_hash}.json"
            if cache_path.exists():
                try:
                    cached = json.loads(cache_path.read_text(encoding="utf-8"))
                    if cached["metadata"]["request_sha256"] != request_hash or not cached["text"].strip() or self._contains_secret(cached):
                        raise ValueError
                    if not any(
                        item["transaction_id"] == cached["metadata"]["transaction_id"]
                        and item["request_sha256"] == request_hash
                        and item["status"] == "finished"
                        and item["attempts"][-1]["status"] == "success"
                        for item in ledger["transactions"]
                    ):
                        raise ValueError
                except (OSError, ValueError, KeyError, TypeError):
                    raise OpenRouterError("cached_result_invalid") from None
                cached["metadata"]["cache_hit"] = True
                cached["metadata"]["cache_read_client_version"] = CLIENT_VERSION
                return cached
            _enforce_pending_server_retry([
                attempt["retry"]
                for transaction in ledger["transactions"]
                for attempt in transaction["attempts"]
                if "retry" in attempt
            ])
            if self._accounted(ledger) + reserved_usd > self.budget_usd:
                raise BudgetError("insufficient_budget_for_all_attempts", {
                    "request_sha256": request_hash,
                    "required_reservation_usd": str(reserved_usd),
                    "remaining_usd": str(self.budget_usd - self._accounted(ledger)),
                })
            transaction = {
                "client_version": CLIENT_VERSION,
                "retry_policy_version": RETRY_POLICY_VERSION,
                "transaction_id": uuid.uuid4().hex,
                "request_sha256": request_hash,
                "messages_sha256": _sha256(messages),
                "request_config": config,
                "purpose": purpose,
                "created_at_utc": _utc_now(),
                "status": "reserved",
                "input_token_reserve": estimated_input_tokens,
                "prompt_price_per_token_usd": str(prompt_price),
                "completion_price_per_token_usd": str(completion_price),
                "upper_per_attempt_usd": str(upper_per_attempt),
                "initial_reservation_usd": str(reserved_usd),
                "accounted_usd": str(reserved_usd),
                "max_attempts": self.max_retries + 1,
                "attempts": [],
            }
            ledger["transactions"].append(transaction)
            _write_json(self._ledger_path, ledger)
            for attempt_index in range(self.max_retries + 1):
                attempt = {
                    "attempt_id": uuid.uuid4().hex,
                    "index": attempt_index,
                    "started_at_utc": _utc_now(),
                    "status": "in_flight",
                    "accounted_usd": str(upper_per_attempt),
                    "cost_basis": "conservative_reservation",
                    "requested_model": model,
                    "returned_model": None,
                    "provider": None,
                    "finish_reason": None,
                    "usage": None,
                }
                transaction["attempts"].append(attempt)
                _write_json(self._ledger_path, ledger)
                output, reason, transient = self._perform_attempt(body, attempt, upper_per_attempt, estimated_input_tokens)
                attempt["finished_at_utc"] = _utc_now()
                attempt["status"] = "success" if reason is None else "failed"
                attempt["failure_reason"] = reason
                if reason is not None and transient:
                    attempt["retry"] = attempt.get("retry") or _retry_plan(None, {}, attempt_index)
                _write_json(self._ledger_path, ledger)
                should_retry = reason is not None and transient and attempt_index < self.max_retries
                deferred = bool(attempt.get("retry", {}).get("deferred"))
                if should_retry and not deferred:
                    time.sleep(attempt["retry"]["delay_seconds"])
                    continue
                transaction["status"] = "finished"
                transaction["finished_at_utc"] = _utc_now()
                transaction["accounted_usd"] = str(sum((_money(item["accounted_usd"]) for item in transaction["attempts"]), Decimal(0)))
                _write_json(self._ledger_path, ledger)
                if self._accounted(ledger) > self.budget_usd:
                    raise BudgetError("reported_cost_exceeds_cap", {"request_sha256": request_hash})
                metadata = {
                    "schema_version": SCHEMA_VERSION,
                    "client_version": CLIENT_VERSION,
                    "retry_policy_version": RETRY_POLICY_VERSION,
                    "request_sha256": request_hash,
                    "messages_sha256": transaction["messages_sha256"],
                    "request_config": config,
                    "transaction_id": transaction["transaction_id"],
                    "purpose": purpose,
                    "requested_model": model,
                    "returned_model": attempt["returned_model"],
                    "provider": attempt["provider"],
                    "provider_missing_reason": None if attempt["provider"] else "not_exposed_by_response",
                    "checkpoint_revision": None,
                    "checkpoint_revision_missing_reason": "not_exposed_by_response",
                    "seed_supported": None,
                    "seed_support_note": "A requested seed does not establish provider support or deterministic replay.",
                    "started_at_utc": transaction["created_at_utc"],
                    "finished_at_utc": transaction["finished_at_utc"],
                    "finish_reason": attempt["finish_reason"],
                    "native_finish_reason": attempt.get("native_finish_reason"),
                    "response_id": attempt.get("response_id"),
                    "usage": attempt["usage"],
                    "cost": {
                        "reported_usd": attempt.get("reported_cost_usd"),
                        "accounted_usd": transaction["accounted_usd"],
                        "basis": attempt["cost_basis"],
                    },
                    "attempt_count": len(transaction["attempts"]),
                    "retry": attempt.get("retry"),
                    "retry_not_before_utc": attempt.get("retry", {}).get("retry_not_before_utc"),
                    "cache_hit": False,
                }
                if deferred:
                    metadata["upstream_failure_reason"] = reason
                    raise RetryDeferredError("retry_after_exceeds_wait_limit", metadata)
                if reason is not None:
                    raise CompletionError(reason, metadata)
                result = {"text": output, "metadata": metadata}
                _write_json(cache_path, result)
                return result
        raise AssertionError("Unreachable completion retry state")

    def _perform_attempt(
        self,
        body: dict[str, Any],
        attempt: dict[str, Any],
        upper_per_attempt: Decimal,
        estimated_input_tokens: int,
    ) -> tuple[str | None, str | None, bool]:
        try:
            response = self._session.post(
                COMPLETIONS_URL,
                json=body,
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                timeout=self.timeout_seconds,
                allow_redirects=False,
            )
        except (requests.Timeout, requests.ConnectionError):
            return None, "transport_failure_billing_unknown", True
        except requests.RequestException:
            return None, "request_failure_billing_unknown", False
        attempt["http_status"] = response.status_code
        if response.status_code != 200:
            if response.status_code in TRANSIENT_STATUS_CODES:
                attempt["retry"] = _retry_plan(response.status_code, getattr(response, "headers", {}), attempt["index"])
            return None, f"http_{response.status_code}_billing_unknown", response.status_code in TRANSIENT_STATUS_CODES
        try:
            payload = response.json()
        except (ValueError, TypeError):
            return None, "invalid_json_billing_unknown", False
        if not isinstance(payload, dict):
            return None, "invalid_payload_billing_unknown", False
        attempt["returned_model"] = self._label(payload.get("model"))
        attempt["provider"] = self._label(payload.get("provider"))
        attempt["response_id"] = self._label(payload.get("id"))
        choices = payload.get("choices")
        valid_choices = isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict)
        if valid_choices:
            attempt["finish_reason"] = self._label(choices[0].get("finish_reason"))
            attempt["native_finish_reason"] = self._label(choices[0].get("native_finish_reason"))
        usage = payload.get("usage")
        usage_ok = isinstance(usage, dict)
        safe_usage: dict[str, Any] = {}
        if usage_ok:
            for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
                value = usage.get(field)
                valid_count = isinstance(value, int) and not isinstance(value, bool) and value >= 0
                usage_ok = usage_ok and valid_count
                if valid_count:
                    safe_usage[field] = value
        reported_cost: Decimal | None = None
        if isinstance(usage, dict) and "cost" in usage:
            try:
                reported_cost = _money(usage["cost"])
            except OpenRouterError:
                pass
        if reported_cost is not None:
            attempt["reported_cost_usd"] = str(reported_cost)
            safe_usage["cost"] = str(reported_cost)
        if isinstance(usage, dict):
            details = usage.get("completion_tokens_details")
            if isinstance(details, dict) and isinstance(details.get("reasoning_tokens"), int) and not isinstance(details["reasoning_tokens"], bool) and details["reasoning_tokens"] >= 0:
                safe_usage["reasoning_tokens"] = details["reasoning_tokens"]
        attempt["usage"] = safe_usage or None
        if not usage_ok or reported_cost is None:
            if reported_cost is not None:
                attempt["accounted_usd"] = str(max(upper_per_attempt, reported_cost))
            return None, "missing_or_invalid_usage", False
        if usage["total_tokens"] < usage["prompt_tokens"] + usage["completion_tokens"]:
            attempt["accounted_usd"] = str(max(upper_per_attempt, reported_cost))
            return None, "inconsistent_token_usage", False
        attempt["accounted_usd"] = str(reported_cost)
        attempt["cost_basis"] = "reported_usage_cost"
        if reported_cost > upper_per_attempt:
            return None, "reported_cost_exceeds_attempt_reservation", False
        if usage["prompt_tokens"] > estimated_input_tokens or usage["completion_tokens"] > body["max_tokens"]:
            return None, "provider_token_usage_exceeds_reservation", False
        if not valid_choices:
            return None, "invalid_choices", False
        choice = choices[0]
        if choice.get("finish_reason") != "stop":
            return None, "incomplete_or_filtered_output", False
        message = choice.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            return None, "empty_or_nontext_output", False
        if self._contains_secret(content):
            return None, "credential_in_response_content", False
        if re.search(r"<\s*/?\s*(?:think|analysis|reasoning)\b|\[/?THINK\]", content, re.IGNORECASE):
            return None, "reasoning_markup_in_final_content", False
        if attempt["returned_model"] is None:
            return None, "missing_returned_model_identity", False
        return content, None, False
