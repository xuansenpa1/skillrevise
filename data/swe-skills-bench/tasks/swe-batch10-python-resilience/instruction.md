# SWE-Skills-Bench: python-resilience (batch10)

# Task: Add Resilient Retry and Timeout Layer to httpx Transport

## Background

The httpx library (https://github.com/encode/httpx) provides async and sync HTTP clients for Python. External HTTP calls in real-world usage frequently encounter transient failures — connection resets, DNS timeouts, 429/502/503/504 responses — that benefit from automatic retry with backoff. A new resilience module should be added alongside the existing transport layer, providing configurable retry, timeout, and fault-tolerance capabilities that integrate with httpx's `Client` and `AsyncClient`.

## Files to Create/Modify

- `httpx/_resilience.py` (new) — Core resilience module containing retry transport wrappers, backoff configuration, and timeout decorators
- `tests/test_resilience.py` (new) — Unit tests covering retry behavior, timeout enforcement, backoff timing, and error classification

## Requirements

### Retry Transport Wrapper

- Implement a `ResilientTransport` class that wraps an existing httpx `BaseTransport` and adds retry logic on transient failures
- Constructor parameters: `transport` (the wrapped transport), `max_retries` (int, default 3), `max_retry_delay` (float, default 30.0 seconds), `initial_delay` (float, default 1.0 second), `retryable_status_codes` (set of ints, default `{429, 502, 503, 504}`)
- The wrapper must implement `handle_request` to intercept responses and retry when the status code is in `retryable_status_codes`
- Wait time between retries must increase exponentially from `initial_delay` up to `max_retry_delay`, with random jitter of ±25%

### Async Retry Transport Wrapper

- Implement `AsyncResilientTransport` wrapping `AsyncBaseTransport` with identical retry semantics as `ResilientTransport`
- Must implement `handle_async_request` using `asyncio.sleep` for delays

### Exception Classification

- Retry on: `httpx.ConnectTimeout`, `httpx.ReadTimeout`, `httpx.ConnectError`, `ConnectionError`, `TimeoutError`
- Do NOT retry on: `httpx.DecodingError`, `httpx.InvalidURL`, `ValueError`, `TypeError`
- The set of retryable exception types must be configurable via a `retryable_exceptions` constructor parameter

### Timeout Enforcement

- Both transport wrappers must accept an optional `total_timeout` (float, seconds) parameter
- If total elapsed time across all attempts (including sleep) exceeds `total_timeout`, stop retrying and raise the last encountered exception or return the last error response
- Default `total_timeout` is 60.0 seconds

### Retry Callback

- Accept an optional `on_retry` callback: `Callable[[int, float, Exception | httpx.Response], None]` invoked before each retry sleep with `(attempt_number, sleep_duration, error_or_response)`
- If no callback provided, retries happen silently

### Edge Cases

- If `max_retries` is 0, no retries occur — the first response or exception is returned/raised immediately
- If the server returns `Retry-After` header (integer seconds) on a 429 response, use that value as the sleep duration instead of the computed backoff, but still respect `max_retry_delay` as an upper cap
- A response with status code 200 on any attempt must be returned immediately without further retries
- Connection failures that occur before any response is received must be retried (not just status-code failures)

### Expected Functionality

- `ResilientTransport` wrapping a transport that returns 503 three times then 200 → returns the 200 response after 3 retries
- `ResilientTransport` wrapping a transport that always returns 503 with `max_retries=3` → returns the final 503 response after exhausting retries
- `AsyncResilientTransport` with `total_timeout=2.0` wrapping a transport that always times out → raises the timeout exception within ~2 seconds regardless of `max_retries`
- Transport that raises `httpx.ConnectError` twice then succeeds → returns success after 2 retries
- Transport that raises `ValueError` → raises immediately without retry
- 429 response with `Retry-After: 5` header and `max_retry_delay=3` → sleeps 3 seconds (capped)
- `on_retry` callback receives correct attempt number and sleep duration on each retry

## Acceptance Criteria

- `ResilientTransport` and `AsyncResilientTransport` classes exist in `httpx/_resilience.py` and are importable from the module
- Retries occur only for exceptions and status codes in the configured retryable sets; permanent errors propagate immediately
- Exponential backoff with jitter is applied between retry attempts, capped at `max_retry_delay`
- `total_timeout` halts further retries once elapsed time exceeds the limit
- `Retry-After` header on 429 responses overrides computed backoff up to `max_retry_delay`
- `on_retry` callback is invoked with correct arguments before each retry sleep
- All unit tests in `tests/test_resilience.py` pass, covering: successful retry after transient failure, retry exhaustion, timeout enforcement, non-retryable exception propagation, Retry-After header handling, zero-retry configuration, and callback invocation
