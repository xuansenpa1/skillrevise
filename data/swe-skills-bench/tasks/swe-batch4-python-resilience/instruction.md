# SWE-Skills-Bench: python-resilience (batch4)

# Task: Add Resilient HTTP Transport Layer to httpx

## Background

The httpx library (https://github.com/encode/httpx) is an HTTP client for Python. Users frequently need to make requests to unreliable external services that may experience transient failures (network timeouts, 502/503/504 responses, connection resets). A new resilient transport layer is needed that wraps httpx's existing transport and provides automatic retry logic with configurable backoff, timeout enforcement, and fail-safe defaults — without requiring users to write custom retry loops around every request.

## Files to Create/Modify

- `httpx/_resilience.py` (create) — Resilient transport wrapper with retry, backoff, timeout, and fail-safe logic
- `httpx/_config.py` (modify) — Add resilience-related configuration defaults and validation
- `tests/test_resilience.py` (create) — Comprehensive tests for the resilient transport layer

## Requirements

### Resilient Transport API

- Implement a `ResilientTransport` class that wraps any `httpx.BaseTransport` instance
- Constructor accepts: `transport` (required), `max_retries` (int, default 3), `backoff_base` (float, default 1.0), `backoff_max` (float, default 30.0), `backoff_jitter` (bool, default True), `timeout_per_attempt` (float or None, default 30.0), `retryable_status_codes` (set of ints, default `{429, 502, 503, 504}`), `retryable_exceptions` (tuple of exception types, default `(ConnectError, ReadTimeout)`)
- The class must implement `handle_request(request) -> Response` following httpx's transport interface

### Retry Logic

- On a retryable exception or a response with a retryable status code, the transport must retry up to `max_retries` additional times
- Wait time between retries must follow exponential backoff: `min(backoff_base * 2^attempt, backoff_max)`, plus random jitter in `[0, 0.5 * wait)` when `backoff_jitter` is True
- Non-retryable exceptions (`ValueError`, `TypeError`, `httpx.InvalidURL`) must propagate immediately without retry
- HTTP 4xx responses other than 429 must not be retried
- After exhausting all retries, the last exception or response must be returned/raised to the caller

### Timeout Enforcement

- Each individual attempt must be bounded by `timeout_per_attempt` seconds
- If an attempt exceeds the timeout, it must be treated as a retryable failure
- A total operation timeout can optionally be specified via `total_timeout` (float or None); when set, the entire retry sequence (including waits) must not exceed this duration, and a `TimeoutError` must be raised if it does

### Fail-Safe Defaults

- When a `fallback` callable is provided to the constructor, it is invoked with the original request after all retries are exhausted, and its return value is used instead of raising an exception
- The fallback must receive the last exception as a second argument so it can decide what to return

### 429 Rate-Limit Handling

- When a 429 response includes a `Retry-After` header, the transport must respect that value as the minimum wait before the next retry (overriding the calculated backoff if `Retry-After` is larger)
- `Retry-After` values may be an integer (seconds) or an HTTP-date; both formats must be parsed correctly

### Logging

- Each retry attempt must log a warning-level message including the attempt number, wait duration, the triggering status code or exception type, and the request URL
- The logger name must be `httpx._resilience`

### Expected Functionality

- A request to a service returning 503 three times then 200 succeeds after 3 retries
- A request to a service returning 400 fails immediately without retrying
- A request that raises `ConnectError` twice then succeeds returns the successful response
- A request that always times out exhausts retries and raises `TimeoutError`
- A request to a 429 endpoint with `Retry-After: 5` waits at least 5 seconds before retrying
- A transport with a `fallback` callable returns the fallback result after all retries fail
- A transport with `total_timeout=10` raises `TimeoutError` if the cumulative time (attempts + waits) exceeds 10 seconds

## Acceptance Criteria

- `ResilientTransport` correctly retries on configured retryable status codes and exceptions, up to `max_retries` times
- Backoff timing follows exponential growth with optional jitter and respects `Retry-After` headers
- Non-retryable errors (4xx except 429, `ValueError`, `InvalidURL`) propagate immediately
- Per-attempt and total timeouts are enforced correctly
- Fallback callable is invoked with the request and last exception when all retries are exhausted
- All retry attempts produce warning-level log messages with the required fields
- Test suite covers normal retry success, immediate failure, timeout exhaustion, 429 handling, fallback invocation, and jitter behavior
