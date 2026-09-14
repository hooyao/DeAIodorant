# OpenRouter Client Maintenance: Retry-After

Date: 2026-09-14  
Client version: `compact-refiner-openrouter-1.1`  
Retry policy: `openrouter-retry-after-1.0`

This maintenance follows completion of CR-001 and CR-001B inference. Their
pre-maintenance code and inputs were archived with hashes under
`feature_runs/compact_refiner/cr001-code-snapshot/`. No historical result,
reservation, source exclusion, or model assessment is recalculated by this
change. No network request or training was performed for this maintenance.

The previous client retried transient responses after short fixed delays and
ignored `Retry-After`. Future calls now follow these rules:

| Response condition | Behavior |
|---|---|
| HTTP 429 or 503 with positive integer seconds | Wait at least that interval before another attempt. |
| HTTP 429 or 503 with a valid HTTP date | Compute the UTC interval and round upward to avoid an early retry. |
| Required interval exceeds 60 seconds | Finish the transaction and raise `RetryDeferredError`; never shorten the server interval to fit the sleep limit. |
| Missing, malformed, zero, or past header | Use bounded deterministic delays of 15, 30, then 60 seconds, subject to the configured retry count. |
| Valid numeric interval outside the datetime range | Defer with `manual_retry_required=true`; do not substitute a short retry. |
| Nontransient HTTP failure | Stop; a header does not make that failure retryable. |

`RetryDeferredError.metadata` includes `retry_not_before_utc`, normalized retry
information, and the underlying safe failure reason when a request just failed.
The exception can also occur with `max_retries=0`, because a later invocation
still needs the server deadline. An unrepresentable deadline is explicitly null
and requires manual resolution. No raw header or HTTP error body is persisted.

Server deadlines are durable. A fresh completion request using the same cache
cannot bypass an active deadline by changing its prompt, model, or seed.
Because the server does not reliably expose the rate-limit scope, the cooldown
applies conservatively to all new completion requests sharing that ledger.
Successful cached answers remain available without a network call. Catalog
requests use a separate private retry-state file and never consume the spending
ledger. A deferred invocation does not schedule itself; the caller must arrange
a later invocation.

Ambiguous failed attempts retain their full conservative cost reservation.
When a retry is deferred, unattempted allowance is released and the transaction
is marked finished; a later call does not incur another reservation while the
server deadline remains active. An actual interrupted in-flight request retains
the existing conservative interruption behavior.

The ledger schema remains `compact-refiner-openrouter-1.0`, and old transaction
records require no migration. New transactions and responses record client and
retry-policy versions. The request-body hash and successful cache identity stay
unchanged because this maintenance does not change the model request or prompt.
Reused old results keep their original metadata and gain only a returned
`cache_read_client_version` field; their on-disk records are not rewritten.

Validation uses mocked transport and a controllable UTC clock. The focused
offline suite covers seconds, HTTP dates, upward rounding, the 60-second
boundary, long-delay deferral, malformed and enormous headers, bounded default
backoff, catalog behavior, resumed cooldowns, cost settlement, and legacy cache
and ledger compatibility:

```powershell
python -m pytest tests/test_refiner_openrouter.py
```

All 56 focused tests passed. HTTP-date interpretation assumes a correct local
UTC clock. Cooldowns do not coordinate separate cache directories or external
clients. The client still cannot guarantee that a remote provider obeys its
declared billing limits; unexpected charges remain recorded and rejected under
the existing accounting policy. These changes have not been validated against
a live rate-limited service.
