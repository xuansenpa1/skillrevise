# SWE-Skills-Bench: python-resilience (batch7)

# Task: Add Resilient HTTP Client Wrapper with Retry and Timeout to httpx

## Background

The httpx library (https://github.com/encode/httpx) is a fully-featured HTTP client for Python. External HTTP calls are inherently unreliable — transient network failures, server overloads, and DNS hiccups can cause requests to fail intermittently. The task is to create a resilient HTTP client module within the httpx repository that wraps `httpx.AsyncClient` with configurable retry logic, exponential backoff, per-request timeouts, and a circuit breaker to protect against cascading failures when downstream services are persistently unhealthy.

## Files to Create/Modify

- `httpx/_resilience.py` (create) — Core resilience module containing the resilient async client wrapper, retry logic, backoff calculation, and circuit breaker state machine
- `httpx/_config.py` (modify) — Add default configuration constants for retry count, backoff base/max, timeout, and circuit breaker thresholds
- `tests/test_resilience.py` (create) — Comprehensive tests for retry behavior, backoff timing, timeout enforcement, circuit breaker state transitions, and error classification

## Requirements

### Resilient Client API

- Provide a class `ResilientAsyncClient` that wraps `httpx.AsyncClient` and exposes the same `get`, `post`, `put`, `patch`, `delete`, `request` methods
- Each method must accept an optional `max_retries` parameter (default: 3) and `timeout` parameter (default: 10.0 seconds)
- The constructor must accept `retry_config` (max_retries, backoff_base, backoff_max, retryable_status_codes) and `circuit_breaker_config` (failure_threshold, recovery_timeout)

### Retry with Exponential Backoff

- Retries must apply only to transient failures: connection errors (`httpx.ConnectError`, `httpx.ConnectTimeout`), HTTP 429, HTTP 502, HTTP 503, HTTP 504
- HTTP 4xx errors other than 429 must NOT be retried
- Backoff delay between retries must follow the formula: `min(backoff_base * 2^attempt + jitter, backoff_max)` where jitter is a random value between 0 and 1 second
- Default `backoff_base` = 0.5 seconds, default `backoff_max` = 30 seconds
- After exhausting all retries, the last exception must be re-raised to the caller

### Timeout Enforcement

- Each individual request attempt (not the total retry sequence) must enforce the configured timeout
- If a single attempt times out, it counts as a retryable failure and triggers the next retry (if retries remain)
- The total wall-clock time for a retried request is NOT capped — only per-attempt timeout applies

### Circuit Breaker

- The circuit breaker has three states: `CLOSED` (normal), `OPEN` (failing fast), `HALF_OPEN` (probing)
- In `CLOSED` state: requests proceed normally; consecutive failures increment a failure counter
- When the failure counter reaches `failure_threshold` (default: 5): transition to `OPEN`
- In `OPEN` state: all requests immediately raise `CircuitBreakerOpenError` without making any network call; after `recovery_timeout` seconds (default: 30), transition to `HALF_OPEN`
- In `HALF_OPEN` state: allow one probe request; if it succeeds → transition to `CLOSED` and reset failure counter; if it fails → transition back to `OPEN`
- Successful requests in `CLOSED` state reset the consecutive failure counter to zero

### Error Classification

- `httpx.ConnectError`, `httpx.ConnectTimeout`, `httpx.ReadTimeout` → transient (retryable)
- HTTP 429, 502, 503, 504 → transient (retryable)
- HTTP 400, 401, 403, 404, 422 → permanent (not retryable, raise immediately)
- HTTP 500 → permanent by default, retryable only if explicitly added to `retryable_status_codes` config

## Expected Functionality

- A GET request to an endpoint returning HTTP 503 three times then HTTP 200 → succeeds on the 4th attempt with the correct response, with exponential backoff delays between attempts
- A GET request to an unreachable host with `max_retries=2` → raises `httpx.ConnectError` after 3 total attempts (1 initial + 2 retries)
- A POST request returning HTTP 400 → raises immediately without retry
- After 5 consecutive failures, the next request raises `CircuitBreakerOpenError` without network activity
- After the recovery timeout elapses, one probe request is allowed; if it succeeds, normal flow resumes
- A request with `timeout=2.0` to a server that takes 5 seconds → times out at 2 seconds, retries with backoff

## Acceptance Criteria

- `ResilientAsyncClient` wraps `httpx.AsyncClient` and supports `get`, `post`, `put`, `patch`, `delete`, `request` with retry and timeout parameters
- Transient failures (connection errors, 429, 502, 503, 504) trigger retries with exponential backoff and jitter
- Permanent failures (4xx other than 429) are raised immediately without retry
- The circuit breaker transitions correctly between CLOSED, OPEN, and HALF_OPEN states based on consecutive failure counts and recovery timeout
- Per-attempt timeout is enforced independently of total retry duration
- Tests verify retry counts, backoff behavior, circuit breaker state transitions, error classification, and timeout enforcement
