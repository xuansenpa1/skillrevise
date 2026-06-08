# SWE-Skills-Bench: python-resilience (batch3)

# Task: Add Resilient HTTP Transport Layer to HTTPX

## Background

The HTTPX library (https://github.com/encode/httpx) is a fully featured HTTP client for Python with sync and async support. The project needs a resilient transport wrapper that adds automatic retry capabilities for transient failures, configurable timeouts, and structured logging of retry attempts. This transport layer should integrate cleanly with HTTPX's existing transport architecture and be usable with both sync and async clients.

## Files to Create/Modify

- `httpx/_transports/resilient.py` (create) — Resilient transport wrapper with retry logic, timeout enforcement, and failure classification
- `httpx/_client.py` (modify) — Expose a convenience parameter to enable resilient transport wrapping on `Client` and `AsyncClient`
- `tests/test_resilient_transport.py` (create) — Test suite covering retry behavior, timeout handling, failure classification, and edge cases

## Requirements

### Resilient Transport Wrapper

- Implement a `ResilientTransport` class that wraps any existing HTTPX transport (both `httpcore.interfaces.Transport` and `httpcore.interfaces.AsyncTransport`)
- The wrapper must intercept `handle_request` / `handle_async_request` calls and add retry behavior around them
- Accept configuration parameters: `max_retries` (int, default 3), `max_retry_delay` (float, seconds, default 60.0), `initial_backoff` (float, seconds, default 1.0), `max_backoff` (float, seconds, default 30.0), and `retryable_status_codes` (set of ints, default `{429, 502, 503, 504}`)

### Failure Classification

- Retry only on transient failures: `ConnectionError`, `TimeoutError`, `httpcore.ConnectError`, `httpcore.ReadTimeout`, and responses with status codes in `retryable_status_codes`
- Never retry on permanent failures: HTTP 4xx errors (except 429), `httpcore.ProtocolError`, or any exception not in the transient error set
- If a response has a `Retry-After` header, honor its value as the wait time (capped by `max_backoff`), supporting both integer seconds and HTTP-date formats

### Backoff and Jitter

- Wait times between retries must increase exponentially from `initial_backoff` up to `max_backoff`
- Add random jitter (±25% of the computed delay) to each wait to prevent synchronized retry storms
- The total cumulative retry time must not exceed `max_retry_delay`; if the next retry would exceed this budget, raise the last exception immediately

### Logging and Observability

- Log each retry attempt at WARNING level, including: attempt number, exception type or HTTP status code, computed wait time, and the request method + URL
- Log final failure (all retries exhausted) at ERROR level
- Use Python's standard `logging` module with logger name `httpx._transports.resilient`

### Client Integration

- Add an optional `resilient` parameter (bool or dict) to `Client.__init__` and `AsyncClient.__init__`
- When `resilient=True`, wrap the active transport with `ResilientTransport` using default settings
- When `resilient` is a dict, pass its keys as configuration to `ResilientTransport`

### Expected Functionality

- A `GET` request to a server that returns 503 twice then 200 should succeed on the third attempt and return the 200 response
- A `POST` request to a server that returns 400 should fail immediately without retrying
- A `GET` request that raises `ConnectionError` three times in a row (with `max_retries=3`) should raise the original `ConnectionError` after all retries are exhausted
- A request to a server returning 429 with `Retry-After: 2` should wait approximately 2 seconds (±25% jitter) before the next attempt
- A request to a server returning 429 with `Retry-After: 120` and `max_backoff=30` should cap the wait at 30 seconds
- When cumulative retry time would exceed `max_retry_delay`, the transport should raise immediately without further retries
- The async variant (`AsyncClient` with `resilient=True`) should behave identically to the sync variant for all scenarios above

## Acceptance Criteria

- `ResilientTransport` retries transient HTTP status codes and network exceptions, and does not retry permanent client errors or protocol errors
- Backoff delays increase exponentially with jitter, and are capped by `max_backoff`
- Total retry duration is bounded by `max_retry_delay`; exceeding the budget raises immediately
- `Retry-After` header values are honored and capped by `max_backoff`
- Each retry attempt is logged at WARNING level with attempt number, error details, wait time, and request info
- Final failure after exhausted retries is logged at ERROR level
- Both `Client` and `AsyncClient` accept a `resilient` parameter that wraps the underlying transport
- All retry, timeout, backoff, and logging behaviors are covered by tests using mocked transports
