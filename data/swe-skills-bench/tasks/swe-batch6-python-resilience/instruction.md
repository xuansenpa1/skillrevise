# SWE-Skills-Bench: python-resilience (batch6)

# Task: Add Resilient HTTP Transport with Retry and Circuit Breaker to httpx

## Background

The httpx library (https://github.com/encode/httpx) is a modern HTTP client for Python. External service calls frequently encounter transient failures such as connection resets, DNS timeouts, and HTTP 502/503 responses. A new resilient transport layer is needed that wraps httpx's existing transport to automatically retry transient failures with exponential backoff, enforce per-request timeouts, and implement a circuit breaker that stops sending requests to a persistently failing backend.

## Files to Create/Modify

- `httpx/_resilience.py` (create) — Resilient transport wrapper implementing retry logic, exponential backoff with jitter, and circuit breaker state machine
- `httpx/_types.py` (modify) — Add type aliases for retry configuration and circuit breaker state if needed
- `tests/test_resilience.py` (create) — Unit tests covering retry behavior, backoff timing, circuit breaker state transitions, and edge cases

## Requirements

### Retry Logic

- The `ResilientTransport` class must wrap any `httpx.BaseTransport` instance.
- It must accept configuration for: `max_retries` (int, default 3), `backoff_base` (float, default 1.0), `backoff_max` (float, default 30.0), `backoff_jitter` (float, default 0.5).
- Retries must use exponential backoff: delay = min(`backoff_base` × 2^attempt + random(0, `backoff_jitter`), `backoff_max`).
- Only transient errors must be retried:
  - `httpx.ConnectError`, `httpx.ConnectTimeout`, `httpx.ReadTimeout`
  - HTTP responses with status codes 429, 502, 503, 504
- Permanent errors must NOT be retried:
  - HTTP 400, 401, 403, 404, 422 responses
  - `httpx.DecodingError`, `httpx.TooManyRedirects`
- For HTTP 429 responses with a `Retry-After` header, the backoff delay must respect the header value (in seconds) instead of the computed exponential delay.

### Circuit Breaker

- The circuit breaker must have three states: `CLOSED` (normal), `OPEN` (failing, reject requests), `HALF_OPEN` (testing recovery).
- Configuration: `failure_threshold` (int, default 5), `recovery_timeout` (float, default 30.0 seconds), `success_threshold` (int, default 2).
- State transitions:
  - `CLOSED → OPEN`: when consecutive failures reach `failure_threshold`
  - `OPEN → HALF_OPEN`: after `recovery_timeout` seconds have elapsed since opening
  - `HALF_OPEN → CLOSED`: when `success_threshold` consecutive successes occur
  - `HALF_OPEN → OPEN`: on any failure
- When the circuit is `OPEN`, all requests must immediately raise a `CircuitBreakerOpenError` (a new exception class inheriting from `httpx.TransportError`) without contacting the remote server.
- When `HALF_OPEN`, only one probe request at a time should be allowed through.

### Logging and Observability

- Every retry attempt must log at `WARNING` level with: attempt number, exception type or status code, computed backoff delay.
- Circuit breaker state transitions must log at `WARNING` level with: old state, new state, failure count, and timestamp.
- A `stats()` method must return a dictionary with keys: `total_requests`, `total_retries`, `total_failures`, `circuit_state`, `consecutive_failures`.

### Expected Functionality

- A request to a server returning HTTP 503 three times then 200 → succeeds on the fourth attempt, `stats()` shows `total_retries: 3`.
- A request to a server that always returns 503 with `max_retries=3` → raises the last `httpx.HTTPStatusError` after 4 total attempts (1 initial + 3 retries).
- Five consecutive connection timeouts with `failure_threshold=5` → circuit opens, next request immediately raises `CircuitBreakerOpenError`.
- After `recovery_timeout` seconds with an open circuit → next request goes through as a probe (HALF_OPEN); if it succeeds, and a second probe succeeds, circuit closes.
- HTTP 429 response with `Retry-After: 10` header → retry waits approximately 10 seconds regardless of computed backoff.
- HTTP 401 response → no retry, error propagates immediately.
- `ResilientTransport(transport, max_retries=0)` → disables retries entirely; errors propagate after first attempt.

## Acceptance Criteria

- `ResilientTransport` wraps any `httpx.BaseTransport` and retries only transient failures with exponential backoff and jitter.
- Permanent HTTP errors (4xx except 429) and non-transient exceptions propagate immediately without retry.
- The circuit breaker transitions through CLOSED → OPEN → HALF_OPEN → CLOSED based on the configured thresholds.
- `CircuitBreakerOpenError` is raised immediately when the circuit is open, without making a network call.
- `Retry-After` header on HTTP 429 responses overrides the computed backoff delay.
- The `stats()` method returns accurate counters reflecting retry and failure history.
- All retry attempts and circuit state transitions are logged with sufficient detail for debugging.
