# SWE-Skills-Bench: python-resilience (batch8)

# Task: Implement Retry Transport Layer for HTTPX

## Background

HTTPX (https://github.com/encode/httpx) is a fully-featured HTTP client for Python 3 supporting both sync and async interfaces. Currently, HTTPX has no built-in retry mechanism — users needing automatic retries for transient network failures or server errors must implement wrapper logic themselves. A new `RetryTransport` is needed that wraps the existing httpcore transport with configurable retry behavior, enabling resilient HTTP calls without external dependencies.

## Files to Create/Modify

- `httpx/_retry.py` (create) — `RetryTransport` and `AsyncRetryTransport` classes wrapping httpcore transports with retry, backoff, and error classification logic
- `httpx/_config.py` (modify) — Add `RetryConfig` dataclass for retry parameters (max_attempts, backoff_factor, retryable status codes, jitter)
- `httpx/_client.py` (modify) — Accept optional `retry` parameter in `Client` and `AsyncClient`, wiring `RetryTransport` around the underlying transport when provided
- `httpx/__init__.py` (modify) — Export `RetryConfig` from the public API
- `tests/test_retry.py` (create) — Test suite covering retry behavior, backoff timing, error classification, Retry-After handling, and edge cases

## Requirements

### RetryTransport

- `RetryTransport` must wrap any `httpcore.BaseTransport`; `AsyncRetryTransport` must wrap any `httpcore.AsyncBaseTransport`
- On each request, if the response status code is in the retryable set OR a retryable network exception occurs, the transport retries up to `max_attempts` total attempts
- Default retryable status codes: `429`, `502`, `503`, `504`
- Default retryable exceptions: `httpcore.ConnectError`, `httpcore.ConnectTimeout`, `httpcore.ReadTimeout`
- Non-retryable errors (HTTP 4xx other than 429, `httpcore.UnsupportedProtocol`, SSL certificate errors) must propagate immediately without retry
- After exhausting all retry attempts, the last received response or raised exception must be returned/raised to the caller

### Backoff and Jitter

- Wait time between retries follows exponential backoff: `min(backoff_factor * (2 ** attempt), backoff_max)` where `attempt` starts at 0
- Default `backoff_factor` is `0.5` seconds; default `backoff_max` is `30.0` seconds
- Random jitter is applied to each backoff interval: actual wait is `calculated_backoff * uniform(0.5, 1.5)`
- When a response includes a `Retry-After` header (integer seconds or HTTP-date), it must be honored if the header value exceeds the calculated backoff

### RetryConfig

- `max_attempts`: `int`, default `3` (total attempts including the initial request)
- `backoff_factor`: `float`, default `0.5`
- `backoff_max`: `float`, default `30.0`
- `retryable_status_codes`: `frozenset[int]`, default `frozenset({429, 502, 503, 504})`
- `retryable_exceptions`: tuple of exception types, default `(httpcore.ConnectError, httpcore.ConnectTimeout, httpcore.ReadTimeout)`
- `respect_retry_after`: `bool`, default `True`
- `max_attempts` must be at least `1`; values less than `1` raise `ValueError` at construction time

### Client Integration

- `httpx.Client(retry=RetryConfig(...))` and `httpx.AsyncClient(retry=RetryConfig(...))` wrap the underlying transport with the corresponding retry transport
- When `retry` is not provided, behavior is identical to current HTTPX (no retries, no overhead)
- Connection pooling and keep-alive must not be disrupted by retry logic

### Edge Cases

- If `max_attempts` is `1`, no retries occur (single attempt only)
- Retries must not re-send non-rewindable streaming request bodies; if the request body is a non-rewindable stream and a retry is needed, raise `httpx.StreamConsumed`
- Each individual attempt respects the client's configured timeout settings independently

## Expected Functionality

- `httpx.Client(retry=RetryConfig(max_attempts=3)).get(url)` transparently retries up to 2 additional times on 503 responses, returning the final response
- A request receiving 429 with `Retry-After: 5` waits at least 5 seconds before the next attempt
- A request to an unreachable host raising `ConnectError` is retried with exponential backoff, ultimately raising the `ConnectError` if all attempts fail
- A request receiving 400 Bad Request is not retried and the 400 response is returned immediately
- `httpx.AsyncClient(retry=RetryConfig(max_attempts=2))` works identically in async mode
- A POST with a consumed streaming body raises `StreamConsumed` on retry instead of sending an empty or corrupted body

## Acceptance Criteria

- `RetryTransport` retries requests on configured status codes (429, 502, 503, 504) and configured network exceptions, up to `max_attempts` total attempts
- Exponential backoff with jitter is applied between retries, with timing governed by `backoff_factor` and `backoff_max`
- `Retry-After` header values are honored when enabled and the header value exceeds the calculated backoff
- Non-retryable errors (4xx other than 429, SSL errors, protocol errors) propagate immediately without retry
- Retry configuration integrates with both `httpx.Client` and `httpx.AsyncClient` via a `retry` parameter
- Non-rewindable streaming request bodies raise an appropriate error on retry rather than sending corrupted data
- The existing HTTPX test suite passes without regression when no retry configuration is provided
