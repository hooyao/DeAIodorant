"""Offline checks for private inference, request identity, and bounded spend."""

from decimal import Decimal
import datetime as dt
from email.utils import format_datetime
import json
from pathlib import Path

import pytest
import requests

from deaiodorant.refine.openrouter import (
    BudgetError,
    CompletionError,
    ConcurrentUseError,
    OpenRouterClient,
    OpenRouterError,
    RetryDeferredError,
    CLIENT_VERSION,
    RETRY_POLICY_VERSION,
)


SECRET = "sk-or-v1-test-authentication-secret"
REASONING = "This private reasoning must never be persisted."


class FakeResponse:
    def __init__(self, status=200, payload=None, headers=None):
        self.status_code = status
        self.payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


def success(text="原有内容保持不变。", *, cost="0.00005", finish="stop"):
    return {
        "id": "gen-offline-fixture",
        "model": "example/editor-v1",
        "provider": "Example Provider",
        "choices": [{
            "finish_reason": finish,
            "message": {
                "content": text,
                "reasoning": REASONING,
                "reasoning_details": [{"text": REASONING}],
            },
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "cost": cost,
            "completion_tokens_details": {"reasoning_tokens": 5},
        },
    }


@pytest.fixture
def setup_client(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        f'UNRELATED_VALUE=must-not-load\nOPENAI_API_KEY="{SECRET}" # local\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("UNRELATED_VALUE", raising=False)
    monkeypatch.setattr("deaiodorant.refine.openrouter.time.sleep", lambda _: None)

    def factory(*, budget="1", retries=0):
        return OpenRouterClient(dotenv, tmp_path / "private", budget, max_retries=retries)

    return factory, tmp_path


def install_responses(client, monkeypatch, responses):
    calls = []
    iterator = iter(responses)

    def post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        response = next(iterator)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(client._session, "post", post)
    return calls


def complete(client, **overrides):
    arguments = {
        "model": "example/editor-v1",
        "messages": [{"role": "user", "content": "请保留原意。"}],
        "prompt_price_per_token": "0.0000001",
        "completion_price_per_token": "0.0000001",
        "max_tokens": 100,
    }
    arguments.update(overrides)
    return client.complete(**arguments)


def test_success_cache_reuses_exact_request_without_secret_or_reasoning(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory()
    calls = install_responses(client, monkeypatch, [FakeResponse(payload=success())])
    result = complete(client, purpose="first_call")
    again = complete(client, purpose="second_call")
    assert result["text"] == "原有内容保持不变。"
    assert again["metadata"]["cache_hit"] is True
    assert len(calls) == 1
    assert calls[0]["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert calls[0]["allow_redirects"] is False
    assert calls[0]["headers"]["Authorization"] == f"Bearer {SECRET}"
    assert calls[0]["json"]["provider"]["allow_fallbacks"] is False
    assert calls[0]["json"]["provider"]["max_price"]["prompt"] == 0.1
    assert client.budget_status()["accounted_usd"] == "0.00005"
    private = "\n".join(path.read_text(encoding="utf-8") for path in (root / "private").glob("*.json"))
    assert SECRET not in private
    assert REASONING not in private
    assert "请保留原意。" not in private
    assert result["metadata"]["usage"]["reasoning_tokens"] == 5
    import os

    assert "UNRELATED_VALUE" not in os.environ


@pytest.mark.parametrize("change", [
    {"model": "example/editor-v2"},
    {"messages": [{"role": "user", "content": "请保留全部原意。"}]},
    {"temperature": 0.4},
    {"max_tokens": 101},
    {"reasoning": {"enabled": False}},
    {"seed": 7},
    {"prompt_price_per_token": "0.0000002"},
])
def test_effective_request_changes_invalidate_cache(setup_client, monkeypatch, change):
    factory, _ = setup_client
    client = factory()
    calls = install_responses(client, monkeypatch, [FakeResponse(payload=success()), FakeResponse(payload=success())])
    first = complete(client)
    second = complete(client, **change)
    assert first["metadata"]["request_sha256"] != second["metadata"]["request_sha256"]
    assert len(calls) == 2


def test_budget_and_cache_survive_restart(setup_client, monkeypatch):
    factory, _ = setup_client
    client = factory(budget="0.0008")
    install_responses(client, monkeypatch, [FakeResponse(payload=success(cost="0.0004"))])
    complete(client)
    client.close()
    reopened = factory(budget="0.0008")
    calls = install_responses(reopened, monkeypatch, [])
    assert complete(reopened)["metadata"]["cache_hit"] is True
    assert reopened.budget_status()["accounted_usd"] == "0.0004"
    with pytest.raises(BudgetError, match="insufficient_budget"):
        complete(reopened, seed=8)
    assert not calls
    with pytest.raises(BudgetError, match="budget_differs"):
        factory(budget="2")


def test_reserves_all_retries_before_any_call(setup_client, monkeypatch):
    factory, _ = setup_client
    client = factory(budget="0.001", retries=2)
    calls = install_responses(client, monkeypatch, [])
    with pytest.raises(BudgetError, match="insufficient_budget"):
        complete(client)
    assert not calls
    assert client.budget_status()["accounted_usd"] == "0"


@pytest.mark.parametrize("payload,reason", [
    (success(finish="length"), "incomplete_or_filtered_output"),
    (success(text=" "), "empty_or_nontext_output"),
    ({**success(), "usage": None}, "missing_or_invalid_usage"),
    ({**success(), "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}}, "missing_or_invalid_usage"),
    (success(text=SECRET), "credential_in_response_content"),
    (success(text=f"<think>{REASONING}</think>原有内容保持不变。"), "reasoning_markup_in_final_content"),
    (ValueError(f"Unsafe response body {SECRET}"), "invalid_json_billing_unknown"),
])
def test_inadmissible_outputs_fail_without_retry_or_reasoning_leak(setup_client, monkeypatch, payload, reason):
    factory, root = setup_client
    client = factory(retries=2)
    calls = install_responses(client, monkeypatch, [FakeResponse(payload=payload)])
    with pytest.raises(CompletionError) as failure:
        complete(client)
    assert failure.value.reason == reason
    assert SECRET not in str(failure.value)
    assert len(calls) == 1
    assert not list((root / "private").glob("result-*.json"))
    ledger = json.loads((root / "private" / "ledger.json").read_text(encoding="utf-8"))
    transaction = ledger["transactions"][0]
    assert transaction["attempts"][0]["failure_reason"] == reason
    assert transaction["status"] == "finished"
    assert Decimal(transaction["accounted_usd"]) > 0
    assert SECRET not in json.dumps(ledger)
    assert REASONING not in json.dumps(ledger)
    assert len(transaction["attempts"]) == 1


def test_transient_retry_is_identical_and_unknown_cost_stays_reserved(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory(retries=2)
    calls = install_responses(client, monkeypatch, [requests.Timeout(SECRET), FakeResponse(payload=success())])
    result = complete(client)
    assert len(calls) == 2
    assert calls[0]["json"] == calls[1]["json"]
    assert result["metadata"]["attempt_count"] == 2
    ledger = json.loads((root / "private" / "ledger.json").read_text(encoding="utf-8"))
    transaction = ledger["transactions"][0]
    assert Decimal(transaction["accounted_usd"]) == Decimal(transaction["upper_per_attempt_usd"]) + Decimal("0.00005")
    assert transaction["attempts"][0]["cost_basis"] == "conservative_reservation"


@pytest.mark.parametrize("status,expected_calls", [(400, 1), (401, 1), (429, 3), (503, 3), (302, 1)])
def test_http_retries_are_bounded_and_error_body_is_never_retained(setup_client, monkeypatch, status, expected_calls):
    factory, root = setup_client
    client = factory(retries=2)
    calls = install_responses(client, monkeypatch, [FakeResponse(status, {"error": SECRET})] * expected_calls)
    with pytest.raises(CompletionError):
        complete(client)
    assert len(calls) == expected_calls
    assert SECRET not in (root / "private" / "ledger.json").read_text(encoding="utf-8")


def test_interrupted_request_keeps_upfront_reservation_after_restart(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory(budget="0.002", retries=2)

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(client._session, "post", interrupted)
    with pytest.raises(KeyboardInterrupt):
        complete(client)
    reopened = factory(budget="0.002", retries=2)
    status = reopened.budget_status()
    assert status["unfinished_reservations"] == 1
    assert Decimal(status["accounted_usd"]) > Decimal("0.001")
    with pytest.raises(BudgetError, match="insufficient_budget"):
        complete(reopened, seed=99)


def test_concurrent_writer_is_rejected(setup_client):
    factory, _ = setup_client
    first = factory()
    second = factory()
    with first._exclusive():
        with pytest.raises(ConcurrentUseError):
            second.budget_status()


def test_catalog_snapshot_has_identity_and_uses_no_auth(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory()
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(payload={"data": [{"id": "example/editor-v1", "pricing": {"prompt": "0.0000001"}}]})

    monkeypatch.setattr(client._session, "get", get)
    catalog = client.fetch_models()
    assert len(catalog["snapshot_sha256"]) == 64
    assert (root / "private" / f"catalog-{catalog['snapshot_sha256']}.json").exists()
    assert "headers" not in calls[0][1]
    assert calls[0][1]["allow_redirects"] is False
    assert client.budget_status()["accounted_usd"] == "0"


def test_credentials_in_messages_are_blocked_before_network(setup_client, monkeypatch):
    factory, _ = setup_client
    client = factory()
    calls = install_responses(client, monkeypatch, [])
    with pytest.raises(OpenRouterError, match="credential_in_request_content"):
        complete(client, messages=[{"role": "user", "content": SECRET}])
    assert not calls


def test_missing_and_duplicate_credentials_fail_safely(tmp_path):
    dotenv = tmp_path / ".env"
    for content in ("UNRELATED_VALUE=test\n", f"OPENAI_API_KEY={SECRET}\nOPENAI_API_KEY=another\n"):
        dotenv.write_text(content, encoding="utf-8")
        with pytest.raises(OpenRouterError, match="missing_or_duplicate_api_key") as failure:
            OpenRouterClient(dotenv, tmp_path / "private", "1")
        assert SECRET not in str(failure.value)


def test_provider_cost_over_reservation_is_recorded_and_stops(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory()
    calls = install_responses(client, monkeypatch, [FakeResponse(payload=success(cost="0.02"))])
    with pytest.raises(CompletionError, match="reported_cost_exceeds_attempt_reservation"):
        complete(client)
    assert len(calls) == 1
    assert client.budget_status()["accounted_usd"] == "0.02"


def test_over_cap_provider_charge_prevents_later_calls(setup_client, monkeypatch):
    factory, _ = setup_client
    client = factory(budget="0.01")
    calls = install_responses(client, monkeypatch, [FakeResponse(payload=success(cost="0.02"))])
    with pytest.raises(BudgetError, match="reported_cost_exceeds_cap"):
        complete(client)
    with pytest.raises(BudgetError, match="persisted_cost_exceeds_cap"):
        complete(client, seed=10)
    assert len(calls) == 1


def test_inconsistent_persisted_accounting_is_rejected(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory()
    install_responses(client, monkeypatch, [FakeResponse(payload=success())])
    complete(client)
    ledger_path = root / "private" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["transactions"][0]["accounted_usd"] = "0"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(BudgetError, match="ledger_invalid"):
        factory()


def test_deleted_ledger_does_not_reset_existing_success_cache(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory()
    install_responses(client, monkeypatch, [FakeResponse(payload=success())])
    complete(client)
    (root / "private" / "ledger.json").unlink()
    with pytest.raises(BudgetError, match="ledger_missing_but_cache_exists"):
        factory()


def test_missing_usage_still_records_available_finish_and_token_diagnostics(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory()
    payload = success(finish="length")
    del payload["usage"]["cost"]
    install_responses(client, monkeypatch, [FakeResponse(payload=payload)])
    with pytest.raises(CompletionError):
        complete(client)
    ledger = json.loads((root / "private" / "ledger.json").read_text(encoding="utf-8"))
    attempt = ledger["transactions"][0]["attempts"][0]
    assert attempt["finish_reason"] == "length"
    assert attempt["usage"]["completion_tokens"] == 20
    assert attempt["cost_basis"] == "conservative_reservation"


@pytest.fixture
def retry_clock(monkeypatch):
    clock = {"now": dt.datetime(2026, 9, 14, 12, 0, 0, 250000, tzinfo=dt.timezone.utc), "sleeps": []}

    def sleep(seconds):
        clock["sleeps"].append(seconds)
        clock["now"] += dt.timedelta(seconds=seconds)

    monkeypatch.setattr("deaiodorant.refine.openrouter._now_utc", lambda: clock["now"])
    monkeypatch.setattr("deaiodorant.refine.openrouter.time.sleep", sleep)
    return clock


@pytest.mark.parametrize("status", [429, 503])
@pytest.mark.parametrize("seconds", [7, 60])
def test_retry_after_seconds_waits_at_least_the_server_interval(setup_client, monkeypatch, retry_clock, status, seconds):
    factory, root = setup_client
    client = factory(retries=1)
    initial = retry_clock["now"]
    calls = install_responses(client, monkeypatch, [
        FakeResponse(status, headers={"Retry-After": str(seconds)}),
        FakeResponse(payload=success()),
    ])
    complete(client)
    assert len(calls) == 2
    assert retry_clock["sleeps"] == [seconds]
    assert retry_clock["now"] >= initial + dt.timedelta(seconds=seconds)
    ledger = json.loads((root / "private" / "ledger.json").read_text(encoding="utf-8"))
    attempt = ledger["transactions"][0]["attempts"][0]
    assert attempt["retry"]["source"] == "server_seconds"
    assert attempt["retry"]["retry_policy_version"] == RETRY_POLICY_VERSION
    assert attempt["cost_basis"] == "conservative_reservation"


@pytest.mark.parametrize("status", [429, 503])
def test_http_date_is_rounded_up_without_an_early_retry(setup_client, monkeypatch, retry_clock, status):
    factory, _ = setup_client
    client = factory(retries=1)
    deadline = retry_clock["now"].replace(microsecond=0) + dt.timedelta(seconds=43)
    calls = install_responses(client, monkeypatch, [
        FakeResponse(status, headers={"Retry-After": format_datetime(deadline, usegmt=True)}),
        FakeResponse(payload=success()),
    ])
    complete(client)
    assert len(calls) == 2
    assert retry_clock["sleeps"] == [43]
    assert retry_clock["now"] >= deadline


@pytest.mark.parametrize("header_kind", ["seconds", "http_date"])
def test_long_server_delay_defers_and_releases_only_unattempted_reservations(setup_client, monkeypatch, retry_clock, header_kind):
    factory, root = setup_client
    client = factory(retries=2)
    header = "90" if header_kind == "seconds" else format_datetime(retry_clock["now"].replace(microsecond=0) + dt.timedelta(seconds=90), usegmt=True)
    calls = install_responses(client, monkeypatch, [FakeResponse(429, headers={"Retry-After": header})])
    with pytest.raises(RetryDeferredError, match="retry_after_exceeds_wait_limit") as failure:
        complete(client)
    assert len(calls) == 1
    assert retry_clock["sleeps"] == []
    assert failure.value.metadata["retry_not_before_utc"] is not None
    assert failure.value.metadata["retry"]["delay_seconds"] == 90
    assert failure.value.metadata["upstream_failure_reason"] == "http_429_billing_unknown"
    ledger = json.loads((root / "private" / "ledger.json").read_text(encoding="utf-8"))
    transaction = ledger["transactions"][0]
    assert transaction["status"] == "finished"
    assert len(transaction["attempts"]) == 1
    assert Decimal(transaction["accounted_usd"]) == Decimal(transaction["upper_per_attempt_usd"])
    assert Decimal(transaction["initial_reservation_usd"]) == 3 * Decimal(transaction["accounted_usd"])
    assert client.budget_status()["unfinished_reservations"] == 0


def test_deferred_deadline_survives_restart_without_additional_spend(setup_client, monkeypatch, retry_clock):
    factory, root = setup_client
    client = factory(retries=2)
    install_responses(client, monkeypatch, [FakeResponse(503, headers={"Retry-After": "120"})])
    with pytest.raises(RetryDeferredError):
        complete(client)
    ledger_path = root / "private" / "ledger.json"
    before = ledger_path.read_bytes()
    reopened = factory(retries=2)
    calls = install_responses(reopened, monkeypatch, [FakeResponse(payload=success())])
    # A changed prompt/seed cannot bypass a server limit of unknown scope.
    with pytest.raises(RetryDeferredError, match="retry_not_before_deadline"):
        complete(reopened, seed=23)
    assert calls == []
    assert ledger_path.read_bytes() == before
    retry_clock["now"] += dt.timedelta(seconds=120)
    complete(reopened, seed=23)
    assert len(calls) == 1


@pytest.mark.parametrize("header", ["invalid", "-10", "1.5", SECRET])
def test_invalid_retry_after_uses_conservative_default_without_header_leak(setup_client, monkeypatch, retry_clock, header):
    factory, root = setup_client
    client = factory(retries=1)
    install_responses(client, monkeypatch, [FakeResponse(429, headers={"Retry-After": header}), FakeResponse(payload=success())])
    complete(client)
    assert retry_clock["sleeps"] == [15]
    ledger = json.loads((root / "private" / "ledger.json").read_text(encoding="utf-8"))
    assert ledger["transactions"][0]["attempts"][0]["retry"]["source"] == "invalid_retry_after_default"
    assert SECRET not in json.dumps(ledger)


def test_default_backoff_is_conservative_and_each_sleep_is_bounded(setup_client, monkeypatch, retry_clock):
    factory, _ = setup_client
    client = factory(retries=3)
    calls = install_responses(client, monkeypatch, [FakeResponse(503)] * 3 + [FakeResponse(payload=success())])
    complete(client)
    assert len(calls) == 4
    assert retry_clock["sleeps"] == [15, 30, 60]
    assert max(retry_clock["sleeps"]) <= 60


@pytest.mark.parametrize("header_kind", ["zero", "past_date"])
def test_nonfuture_retry_after_uses_backoff_instead_of_spinning(setup_client, monkeypatch, retry_clock, header_kind):
    factory, _ = setup_client
    client = factory(retries=1)
    header = "0" if header_kind == "zero" else format_datetime(retry_clock["now"] - dt.timedelta(days=1), usegmt=True)
    install_responses(client, monkeypatch, [FakeResponse(429, headers={"Retry-After": header}), FakeResponse(payload=success())])
    complete(client)
    assert retry_clock["sleeps"] == [15]


def test_enormous_valid_interval_never_falls_back_to_an_early_retry(setup_client, monkeypatch, retry_clock):
    factory, _ = setup_client
    client = factory(retries=2)
    calls = install_responses(client, monkeypatch, [FakeResponse(503, headers={"Retry-After": "9" * 1000})])
    with pytest.raises(RetryDeferredError) as failure:
        complete(client)
    assert len(calls) == 1
    assert retry_clock["sleeps"] == []
    assert failure.value.metadata["retry"]["manual_retry_required"] is True
    assert failure.value.metadata["retry_not_before_utc"] is None


def test_no_retry_budget_still_reports_the_server_deadline(setup_client, monkeypatch, retry_clock):
    factory, _ = setup_client
    client = factory(retries=0)
    calls = install_responses(client, monkeypatch, [FakeResponse(429, headers={"Retry-After": "90"})])
    with pytest.raises(RetryDeferredError) as failure:
        complete(client)
    assert len(calls) == 1
    assert failure.value.metadata["retry_not_before_utc"] is not None
    assert retry_clock["sleeps"] == []


def test_retry_after_does_not_make_a_permanent_http_error_retryable(setup_client, monkeypatch, retry_clock):
    factory, _ = setup_client
    client = factory(retries=2)
    calls = install_responses(client, monkeypatch, [FakeResponse(400, headers={"Retry-After": "90"})])
    with pytest.raises(CompletionError, match="http_400_billing_unknown"):
        complete(client)
    assert len(calls) == 1
    assert retry_clock["sleeps"] == []


@pytest.mark.parametrize("status", [429, 503])
def test_catalog_obeys_short_retry_after_without_spend(setup_client, monkeypatch, retry_clock, status):
    factory, _ = setup_client
    client = factory(retries=1)
    responses = iter([FakeResponse(status, headers={"Retry-After": "9"}), FakeResponse(payload={"data": []})])
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return next(responses)

    monkeypatch.setattr(client._session, "get", get)
    snapshot = client.fetch_models()
    assert len(calls) == 2
    assert retry_clock["sleeps"] == [9]
    assert snapshot["client_version"] == CLIENT_VERSION
    assert client.budget_status()["accounted_usd"] == "0"


def test_catalog_deferral_survives_restart_and_does_not_touch_spend(setup_client, monkeypatch, retry_clock):
    factory, root = setup_client
    client = factory(retries=2)
    deadline = retry_clock["now"].replace(microsecond=0) + dt.timedelta(seconds=180)
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return FakeResponse(503, headers={"Retry-After": format_datetime(deadline, usegmt=True)})

    monkeypatch.setattr(client._session, "get", get)
    ledger_before = (root / "private" / "ledger.json").read_bytes()
    with pytest.raises(RetryDeferredError, match="catalog_retry_after_exceeds_wait_limit"):
        client.fetch_models()
    reopened = factory(retries=2)
    monkeypatch.setattr(reopened._session, "get", get)
    with pytest.raises(RetryDeferredError, match="retry_not_before_deadline"):
        reopened.fetch_models()
    assert len(calls) == 1
    assert retry_clock["sleeps"] == []
    assert (root / "private" / "ledger.json").read_bytes() == ledger_before


def test_legacy_success_cache_and_accounting_remain_unchanged(setup_client, monkeypatch):
    factory, root = setup_client
    client = factory()
    install_responses(client, monkeypatch, [FakeResponse(payload=success())])
    original = complete(client)
    ledger_path = root / "private" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for field in ("client_version", "retry_policy_version"):
        ledger["transactions"][0].pop(field)
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    cache_path = root / "private" / ("result-" + original["metadata"]["request_sha256"] + ".json")
    cached = json.loads(cache_path.read_text(encoding="utf-8"))
    for field in ("client_version", "retry_policy_version", "retry", "retry_not_before_utc"):
        cached["metadata"].pop(field)
    cache_path.write_text(json.dumps(cached), encoding="utf-8")
    ledger_before, cache_before = ledger_path.read_bytes(), cache_path.read_bytes()
    reopened = factory()
    calls = install_responses(reopened, monkeypatch, [])
    result = complete(reopened)
    assert result["metadata"]["cache_hit"] is True
    assert result["metadata"]["cache_read_client_version"] == CLIENT_VERSION
    assert "client_version" not in result["metadata"]
    assert reopened.budget_status()["accounted_usd"] == "0.00005"
    assert calls == []
    assert ledger_path.read_bytes() == ledger_before
    assert cache_path.read_bytes() == cache_before
