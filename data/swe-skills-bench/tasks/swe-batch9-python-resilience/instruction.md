# SWE-Skills-Bench: python-resilience (batch9)

# Task: Add Resilient HTTP Transport with Retry and Circuit Breaker to httpx

## Background

The httpx library (https://github.com/encode/httpx) provides an HTTP client for Python with sync and async support. Its current `HTTPTransport` supports a basic `retries` parameter that only handles `ConnectError` and `ConnectTimeout`. Production applications need more sophisticated resilience — retries on specific HTTP status codes (429, 502, 503, 504), exponential backoff with jitter, per-request timeout budgets, and a circuit breaker that stops sending requests to a failing upstream. This task adds a new `ResilientTransport` class that wraps any existing transport with these capabilities.

## Files to Create/Modify

- `httpx/_transports/resilient.py` (create) — New `ResilientTransport` and `AsyncResilientTransport` classes implementing `BaseTransport` and `AsyncBaseTransport` respectively, with retry, backoff, and circuit breaker logic
- `httpx/_config.py` (modify) — Add `RetryConfig` dataclass with fields: `max_retries`, `backoff_base`, `backoff_max`, `backoff_jitter`, `retryable_status_codes`, `retryable_exceptions`
- `httpx/__init__.py` (modify) — Export `ResilientTransport`, `AsyncResilientTransport`, and `RetryConfig` from the public API
- `tests/test_resilient_transport.py` (create) — Tests covering retry on status codes, exponential backoff timing, circuit breaker state transitions, timeout budget exhaustion, and non-retryable error pass-through

## Requirements

### RetryConfig

- `max_retries: int` — Maximum number of retry attempts (default: 3, must be ≥ 0)
- `backoff_base: float` — Base delay in seconds for exponential backoff (default: 0.5)
- `backoff_max: float` — Maximum delay cap in seconds (default: 30.0)
- `backoff_jitter: float` — Maximum additional random jitter in seconds (default: 0.25)
- `retryable_status_codes: tuple[int, ...]` — HTTP status codes that trigger a retry (default: `(429, 502, 503, 504)`)
- `retryable_exceptions: tuple[type[Exception], ...]` — Exception types that trigger a retry (default: `(ConnectError, ConnectTimeout, ReadTimeout)`)

### ResilientTransport

- Wraps any `BaseTransport` instance as the underlying transport
- On each request, iterates up to `max_retries + 1` attempts (1 initial + N retries)
- If the response status code is in `retryable_status_codes`, waits with exponential backoff and retries
- If an exception in `retryable_exceptions` is raised, waits with exponential backoff and retries
- The backoff delay for attempt `n` is `min(backoff_base * (2 ** n) + random(0, backoff_jitter), backoff_max)`
- If a `Retry-After` header is present in a 429 response and its value is a valid integer, use that value as the delay instead of the computed backoff (capped at `backoff_max`)
- After all retries are exhausted, return the last response or re-raise the last exception
- Must not retry on 4xx status codes other than 429

### Circuit Breaker

- The transport maintains a failure counter and state: `CLOSED` (normal), `OPEN` (failing), `HALF_OPEN` (testing)
- After `failure_threshold` (default: 5) consecutive failures (retryable status codes or retryable exceptions), transition to `OPEN`
- In `OPEN` state, immediately raise `CircuitBreakerOpenError` (a new subclass of `httpx.TransportError`) without sending the request; the circuit stays open for `recovery_timeout` seconds (default: 30)
- After `recovery_timeout` elapses, transition to `HALF_OPEN` and allow one probe request
- If the probe succeeds (non-retryable status code), transition to `CLOSED` and reset the failure counter
- If the probe fails, transition back to `OPEN` for another `recovery_timeout` period

### AsyncResilientTransport

- Provides the same behavior as `ResilientTransport` but implements `AsyncBaseTransport`
- Uses `asyncio.sleep` for backoff delays instead of `time.sleep`

### Edge Cases

- A request that succeeds on the first attempt incurs no delay and does not increment the failure counter
- If `max_retries` is 0, the transport behaves as a pass-through with circuit breaker only
- Retries must not re-send the request body if the body stream has already been consumed; if the request has a streaming body, the transport must not retry (return the response or raise immediately)

### Expected Functionality

- A request receiving 503, 503, 200 with `max_retries=3` succeeds on the third attempt after two backoff delays
- A request receiving 429 with `Retry-After: 2` waits exactly 2 seconds before retrying
- A request receiving 400 is not retried regardless of `max_retries`
- After 5 consecutive 503 responses, the next request raises `CircuitBreakerOpenError` immediately
- After `recovery_timeout` elapses, one request is allowed through; if it returns 200, normal operation resumes

## Acceptance Criteria

- `ResilientTransport` and `AsyncResilientTransport` are importable from `httpx` and function as drop-in transports with `httpx.Client(transport=...)` and `httpx.AsyncClient(transport=...)`
- Retry logic correctly respects `retryable_status_codes`, `retryable_exceptions`, and `max_retries` — non-retryable errors are raised immediately
- Backoff delays follow the exponential formula with jitter, capped at `backoff_max`
- `Retry-After` header on 429 responses overrides the computed backoff
- Circuit breaker transitions through CLOSED → OPEN → HALF_OPEN → CLOSED correctly based on consecutive failure counts and recovery timeout
- Streaming request bodies are not retried
- All tests in `tests/test_resilient_transport.py` pass with `python -m pytest tests/test_resilient_transport.py -v`
