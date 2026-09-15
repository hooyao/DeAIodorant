"""Offline contracts for isolated Azure auth, private output, and durable spend."""

from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

httpx = pytest.importorskip("httpx")
openai = pytest.importorskip("openai")

from deaiodorant.refine import azure
from deaiodorant.refine.azure import (
    AzureResponsesClient, AzureResponsesError, BudgetError, CompletionError, ConcurrentUseError,
)


SECRET = "azure-offline-test-credential-never-real"
OTHER_SECRET = "sk-or-v1-offline-unrelated-credential"
BASE_URL = "https://offline-fixture.services.ai.azure.com/openai/v1/"
INPUT = "请保留这段原文中的信息。"
REASONING = "Private reasoning must not be retained."


def dotenv_content(**changes):
    settings = {
        "AZURE_OPENAI_API_KEY": SECRET,
        "AZURE_OPENAI_BASE_URL": BASE_URL,
        "AZURE_OPENAI_DEPLOYMENT": "gpt-4.1",
        "OPENAI_API_KEY": OTHER_SECRET,
    }
    settings.update(changes)
    return "\n".join(f'{key}="{value}" # fixture' for key, value in settings.items())


def success(**changes):
    response = {
        "id": "resp_offline", "model": "gpt-4.1-2025-04-14", "status": "completed",
        "output_text": "原有信息保留。",
        "output": [{"type": "message", "status": "completed", "content": [{"type": "output_text", "text": "原有信息保留。"}]},
                   {"type": "reasoning", "summary": REASONING}],
        "usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
        "reasoning": REASONING,
    }
    response.update(changes)
    return SimpleNamespace(**response)


@pytest.fixture
def private_root(tmp_path, monkeypatch):
    # Simulate Git inspection; neither this fixture nor any test changes Git state.
    (tmp_path / ".git").mkdir()
    original_run = subprocess.run

    def git_inspect(command, **kwargs):
        if command[:2] == ["git", "check-ignore"]:
            return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
        if command[:2] == ["git", "ls-files"]:
            return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
        return original_run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", git_inspect)
    (tmp_path / ".env").write_text(dotenv_content(), encoding="utf-8")
    return tmp_path


@pytest.fixture
def setup_client(private_root, monkeypatch):
    created = []
    pending = []
    calls = []

    class FakeSDK:
        def __init__(self, **kwargs):
            self.options = kwargs
            self.closed = False
            self.responses = SimpleNamespace(create=self.create)
            created.append(self)

        def create(self, **kwargs):
            calls.append(kwargs)
            result = pending.pop(0)
            if isinstance(result, BaseException):
                raise result
            if callable(result):
                return result()
            return result

        def close(self):
            self.closed = True

    monkeypatch.setattr(azure, "OpenAI", FakeSDK)
    clients = []

    def factory(**kwargs):
        client = AzureResponsesClient(
            private_root / ".env", kwargs.pop("cache_dir", private_root / "private"), **kwargs,
        )
        clients.append(client)
        return client

    yield SimpleNamespace(factory=factory, root=private_root, created=created, calls=calls, pending=pending)
    for client in clients:
        client.close()


def complete(client, **changes):
    return client.complete(INPUT, max_output_tokens=100, **changes)


def test_azure_auth_is_separate_and_success_cache_is_private(setup_client, monkeypatch):
    fixture = setup_client
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "also-not-used")
    client = fixture.factory()
    fixture.pending.append(success())
    result = complete(client, instructions="保持原意。", purpose="first-call")
    before = (client.ledger_dir / "ledger.json").read_bytes()
    cached = complete(client, instructions="保持原意。", purpose="cache-read")
    assert cached["metadata"]["cache_hit"] is True
    assert len(fixture.calls) == 1
    assert fixture.calls[0] == {
        "model": "gpt-4.1", "input": INPUT, "instructions": "保持原意。",
        "max_output_tokens": 100, "temperature": 0, "store": False,
    }
    assert fixture.created[0].options["api_key"] == SECRET
    assert fixture.created[0].options["max_retries"] == 0
    assert fixture.created[0].options["base_url"] == BASE_URL
    assert fixture.created[0].options["http_client"].follow_redirects is False
    assert fixture.created[0].options["http_client"]._trust_env is False
    assert result["metadata"]["actual_billed_usd"] is None
    assert result["metadata"]["usage"] == {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}
    assert result["metadata"]["budget_estimate"]["accounted_usd"] == "0.0016"
    assert result["metadata"]["budget_estimate"]["rates_are_verified_billing"] is False
    assert before == (client.ledger_dir / "ledger.json").read_bytes()
    private = "\n".join(p.read_text(encoding="utf-8") for directory in (client.cache_dir, client.ledger_dir) for p in directory.glob("*.json"))
    for sensitive in (SECRET, OTHER_SECRET, BASE_URL, INPUT, REASONING, "保持原意。"):
        assert sensitive not in private
    assert os.environ["OPENAI_API_KEY"] == "must-not-be-used"


def test_reservation_is_written_before_request_and_survives_restart_across_caches(setup_client):
    fixture = setup_client
    client = fixture.factory(budget_usd="0.07")

    def interrupt():
        ledger = json.loads((client.ledger_dir / "ledger.json").read_text(encoding="utf-8"))
        assert ledger["transactions"][0]["status"] == "reserved"
        assert Decimal(ledger["transactions"][0]["accounted_usd"]) > 0
        raise KeyboardInterrupt

    fixture.pending.append(interrupt)
    with pytest.raises(KeyboardInterrupt):
        complete(client)
    client.close()
    reopened = fixture.factory(budget_usd="0.07", cache_dir=fixture.root / "other-experiment")
    assert reopened.budget_status()["unfinished_reservations"] == 1
    assert Decimal(reopened.budget_status()["accounted_usd"]) > Decimal("0.04")
    with pytest.raises(BudgetError, match="insufficient_budget"):
        reopened.complete("另一段文字。", max_output_tokens=100)
    assert len(fixture.calls) == 1


def test_success_cache_and_measured_plan_cost_survive_restart(setup_client):
    fixture = setup_client
    client = fixture.factory()
    fixture.pending.append(success())
    complete(client)
    client.close()
    reopened = fixture.factory()
    assert complete(reopened)["metadata"]["cache_hit"] is True
    assert reopened.budget_status()["accounted_usd"] == "0.0016"
    assert reopened.budget_status()["actual_billed_usd"] is None
    assert len(fixture.calls) == 1


@pytest.mark.parametrize("field,value", [
    ("AZURE_OPENAI_DEPLOYMENT", "different-deployment"),
    ("AZURE_OPENAI_BASE_URL", "https://another.openai.azure.com/openai/v1/"),
])
def test_deployment_account_change_cannot_reuse_ledger(setup_client, field, value):
    fixture = setup_client
    fixture.factory()
    (fixture.root / ".env").write_text(dotenv_content(**{field: value}), encoding="utf-8")
    with pytest.raises(BudgetError, match="configuration_differs"):
        fixture.factory()


@pytest.mark.parametrize("change", [{"budget_usd": "46"}, {"input_usd_per_million": "11"}, {"output_usd_per_million": "31"}])
def test_budget_plan_change_cannot_reuse_ledger(setup_client, change):
    setup_client.factory()
    with pytest.raises(BudgetError, match="configuration_differs"):
        setup_client.factory(**change)


def test_budget_refusal_has_no_paid_attempt(setup_client):
    client = setup_client.factory(budget_usd="0.001")
    with pytest.raises(BudgetError, match="insufficient_budget"):
        complete(client)
    assert client.budget_status()["accounted_usd"] == "0"
    assert setup_client.calls == []


@pytest.mark.parametrize("response,reason,unknown", [
    (success(usage=None), "missing_or_invalid_usage", True),
    (success(usage={"input_tokens": 100, "output_tokens": 20, "total_tokens": 119}), "missing_or_invalid_usage", True),
    (success(status="incomplete"), "incomplete_or_failed_response", False),
    (success(output_text=" "), "empty_or_nontext_output", False),
    (success(output=[{"content": [{"type": "refusal", "refusal": SECRET}]}]), "response_refused", False),
    (success(output_text=SECRET), "credential_in_response_content", False),
    (success(output_text=OTHER_SECRET), "credential_in_response_content", False),
    (success(output_text=f"<think>{REASONING}</think>文字。"), "reasoning_markup_in_final_content", False),
])
def test_failed_output_is_not_cached_or_retried(setup_client, response, reason, unknown):
    fixture = setup_client
    client = fixture.factory()
    fixture.pending.append(response)
    with pytest.raises(CompletionError, match=reason) as failure:
        complete(client)
    assert failure.value.metadata["actual_billed_usd"] is None
    assert client.budget_status()["retained_unknown_cost_reservations"] == int(unknown)
    assert len(fixture.calls) == 1
    assert not list(client.cache_dir.glob("result-*.json"))
    persisted = (client.ledger_dir / "ledger.json").read_text(encoding="utf-8")
    assert SECRET not in persisted and REASONING not in persisted
    reopened = fixture.factory()
    assert reopened.budget_status()["accounted_usd"] == client.budget_status()["accounted_usd"]


@pytest.mark.parametrize("kind", ["timeout", "http", "sdk"])
def test_sdk_failures_do_not_leak_or_erase_reservation(setup_client, kind):
    fixture = setup_client
    request = httpx.Request("POST", BASE_URL)
    failure = {
        "timeout": openai.APITimeoutError(request=request),
        "http": openai.APIStatusError(SECRET, response=httpx.Response(429, request=request, text=SECRET), body={"error": SECRET}),
        "sdk": RuntimeError(f"{SECRET} {BASE_URL} {REASONING}"),
    }[kind]
    fixture.pending.append(failure)
    client = fixture.factory()
    with pytest.raises(CompletionError) as error:
        complete(client)
    assert "billing_unknown" in error.value.reason
    assert client.budget_status()["retained_unknown_cost_reservations"] == 1
    assert len(fixture.calls) == 1
    for text in (str(error.value), json.dumps(error.value.metadata), (client.ledger_dir / "ledger.json").read_text(encoding="utf-8")):
        assert SECRET not in text and BASE_URL not in text and REASONING not in text


@pytest.mark.parametrize("content", [SECRET, OTHER_SECRET, "sk-or-any-obvious-token"])
@pytest.mark.parametrize("field", ["input_text", "instructions"])
def test_secret_in_input_is_blocked_before_reservation(setup_client, content, field):
    client = setup_client.factory()
    with pytest.raises(AzureResponsesError, match="credential_in_request_content"):
        client.complete(**{"input_text": INPUT, field: content})
    assert client.budget_status()["accounted_usd"] == "0"
    assert not setup_client.calls


@pytest.mark.parametrize("content,reason", [
    (f"OPENAI_API_KEY={OTHER_SECRET}", "missing_azure_setting"),
    (dotenv_content() + f"\nAZURE_OPENAI_API_KEY={SECRET}", "duplicate_azure_setting"),
    (dotenv_content(AZURE_OPENAI_API_KEY=""), "invalid_azure_setting"),
    (dotenv_content() + "\nAZURE_OPENAI_BASE_URL", "duplicate_azure_setting"),
    (dotenv_content(AZURE_OPENAI_API_KEY=OTHER_SECRET), "openrouter_key_is_not_azure_credential"),
])
def test_bad_dotenv_assignments_fail_with_safe_codes(private_root, content, reason):
    (private_root / ".env").write_text(content, encoding="utf-8")
    with pytest.raises(AzureResponsesError, match=reason) as error:
        AzureResponsesClient(private_root / ".env", private_root / "private")
    assert SECRET not in str(error.value) and OTHER_SECRET not in str(error.value)


@pytest.mark.parametrize("url", [
    "http://example.openai.azure.com/openai/v1/",
    "https://example.openai.azure.com.evil.test/openai/v1/",
    "https://example.services.ai.azure.com/", "https://example.openai.azure.com/openai/v1/?x=y",
    "https://example.openai.azure.com/openai/v1/#", "https://user:password@example.openai.azure.com/openai/v1/",
    "https://example.openai.azure.com:444/openai/v1/", "https://example.openai.azure.com/openai/v1/../v1/",
])
def test_endpoint_validation_precedes_sdk_creation(setup_client, url):
    fixture = setup_client
    (fixture.root / ".env").write_text(dotenv_content(AZURE_OPENAI_BASE_URL=url), encoding="utf-8")
    with pytest.raises(AzureResponsesError, match="invalid_azure_base_url"):
        fixture.factory()
    assert not fixture.created


def test_concurrent_writers_share_one_lock_even_with_different_caches(setup_client):
    first = setup_client.factory()
    second = setup_client.factory(cache_dir=setup_client.root / "another-private-cache")
    with first._exclusive():
        with pytest.raises(ConcurrentUseError):
            second.budget_status()


def test_deleted_or_tampered_ledger_does_not_reset_budget(setup_client):
    fixture = setup_client
    client = fixture.factory()
    fixture.pending.append(success())
    complete(client)
    ledger_path = client.ledger_dir / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["transactions"][0]["accounted_usd"] = "0"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(BudgetError, match="ledger_invalid"):
        fixture.factory()
    ledger_path.unlink()
    with pytest.raises(BudgetError, match="ledger_missing_after_initialization"):
        fixture.factory(cache_dir=fixture.root / "new-cache")


def test_changed_request_cannot_reuse_cached_text(setup_client):
    fixture = setup_client
    client = fixture.factory()
    fixture.pending.extend([success(), success()])
    first = complete(client)
    second = complete(client, temperature=0.5)
    assert first["metadata"]["request_sha256"] != second["metadata"]["request_sha256"]
    assert len(fixture.calls) == 2


def test_sdk_close_exception_is_sanitized(setup_client):
    client = setup_client.factory()

    def unsafe_close():
        raise RuntimeError(SECRET)

    client._client.close = unsafe_close
    with pytest.raises(AzureResponsesError, match="sdk_close_failed") as error:
        client.close()
    assert SECRET not in str(error.value)
    assert client._http.is_closed


def test_usage_above_reservation_is_accounted_and_blocks_success(setup_client):
    fixture = setup_client
    client = fixture.factory()
    fixture.pending.append(success(usage={"input_tokens": 100, "output_tokens": 101, "total_tokens": 201}))
    with pytest.raises(CompletionError, match="token_usage_exceeds_reservation"):
        complete(client)
    assert client.budget_status()["accounted_usd"] == "0.00403"
    assert not list(client.cache_dir.glob("result-*.json"))


@pytest.mark.parametrize("mode", ["not_ignored", "tracked_child"])
def test_private_paths_are_git_ignored_and_have_no_tracked_children(private_root, monkeypatch, mode):
    def inspect(command, **kwargs):
        return SimpleNamespace(
            returncode=1 if mode == "not_ignored" and command[1] == "check-ignore" else 0,
            stdout=b"private/tracked.json\0" if mode == "tracked_child" and command[1] == "ls-files" else b"",
        )

    monkeypatch.setattr(subprocess, "run", inspect)
    with pytest.raises(AzureResponsesError, match="artifact_path"):
        AzureResponsesClient(private_root / ".env", private_root / "private")


def test_real_sdk_transport_does_not_follow_redirect_or_retry(private_root, monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(307, headers={"location": "https://redirect.example/responses"}, text=SECRET)

    original_client = httpx.Client

    class OfflineHTTPClient(original_client):
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False
            assert kwargs["trust_env"] is False
            super().__init__(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(azure.httpx, "Client", OfflineHTTPClient)
    with AzureResponsesClient(private_root / ".env", private_root / "private") as client:
        with pytest.raises(CompletionError, match="http_307_billing_unknown"):
            complete(client)
        assert len(requests) == 1
        assert str(requests[0].url) == BASE_URL + "responses"
        assert requests[0].headers["authorization"] == f"Bearer {SECRET}"
        assert json.loads(requests[0].content)["store"] is False
        assert client.budget_status()["retained_unknown_cost_reservations"] == 1
