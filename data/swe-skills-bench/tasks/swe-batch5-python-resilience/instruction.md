# SWE-Skills-Bench: python-resilience (batch5)

# Task: Add Resilient Retry Logic to httpx Transport Layer

## Background

httpx (https://github.com/encode/httpx) is a modern Python HTTP client. Currently, transient failures (HTTP 429, 502, 503, 504 and connection errors) in `httpx.AsyncClient` and `httpx.Client` cause immediate exceptions with no automatic recovery. This task requires implementing a resilient transport wrapper that retries failed requests with configurable backoff behavior, so that applications using httpx can handle intermittent network issues gracefully.

## Files to Create/Modify

- `httpx/_transports/retry.py` (create) — A `RetryTransport` class wrapping any existing `httpx.BaseTransport` (sync) and `AsyncRetryTransport` wrapping `httpx.AsyncBaseTransport` (async), adding retry-on-failure logic.
- `httpx/_config.py` (modify) — Add a `RetryConfig` dataclass with configurable parameters: `max_retries`, `backoff_factor`, `retryable_status_codes`, `retryable_exceptions`.
- `tests/test_retry_transport.py` (create) — Tests covering retry behavior, backoff timing, max-retry exhaustion, non-retryable passthrough, and async variants.

## Requirements

### RetryTransport

- Wraps any `BaseTransport` and intercepts `handle_request`.
- On receiving a response with a status code in `retryable_status_codes` (default: `{429, 502, 503, 504}`), or on a caught exception in `retryable_exceptions` (default: `ConnectError`, `ReadTimeout`), the transport retries the request.
- Maximum number of retries is governed by `max_retries` (default: 3).
- Wait time between retries follows exponential backoff: `backoff_factor * 2^(attempt-1)` seconds, where `backoff_factor` defaults to `0.5`.
- If a `Retry-After` header is present in a 429 response, its value (integer seconds) overrides the calculated backoff, capped at 60 seconds.
- After exhausting all retries, the last received response is returned (for retryable status codes) or the last exception is re-raised (for retryable exceptions).
- Non-retryable status codes (e.g., 400, 401, 404, 500) are returned immediately without retry.

### AsyncRetryTransport

- Same behavior as `RetryTransport` but wraps `AsyncBaseTransport` and uses `asyncio.sleep` for backoff delays.

### RetryConfig

- Fields: `max_retries: int = 3`, `backoff_factor: float = 0.5`, `retryable_status_codes: set[int] = {429, 502, 503, 504}`, `retryable_exceptions: tuple[type[Exception], ...] = (ConnectError, ReadTimeout)`, `retry_after_max: int = 60`.
- Can be passed to `httpx.Client(transport=RetryTransport(base_transport, config=retry_config))`.
- `max_retries=0` disables retrying entirely (passthrough mode).

### Expected Functionality

- A request that gets HTTP 503 twice then 200 on the third attempt → `RetryTransport` returns the 200 response after two retries.
- A request that gets HTTP 429 with `Retry-After: 2` → transport waits 2 seconds before retrying, not the computed backoff.
- A request that gets HTTP 503 four times with `max_retries=3` → returns the fourth 503 response (all retries exhausted).
- A request that raises `ConnectError` twice then succeeds → `RetryTransport` returns the successful response.
- A request that gets HTTP 400 → returned immediately, no retry.
- `max_retries=0` → request passes through without any retry logic.

## Acceptance Criteria

- `RetryTransport` retries on configured status codes and exceptions up to `max_retries` times with exponential backoff.
- `Retry-After` header on 429 responses overrides the backoff duration, capped at `retry_after_max`.
- After exhausting retries, the transport returns the last response or re-raises the last exception.
- Non-retryable responses (4xx other than 429, 500) pass through immediately.
- `AsyncRetryTransport` provides identical behavior for async clients.
- All tests pass, covering success-after-retry, retry exhaustion, Retry-After handling, non-retryable passthrough, and async variants.
