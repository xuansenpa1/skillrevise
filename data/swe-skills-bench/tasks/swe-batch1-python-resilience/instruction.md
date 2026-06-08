# SWE-Skills-Bench: python-resilience (batch1)

# Task: Implement Resilient Transport Layer for httpx

## Background

We need to add a resilient transport module to the httpx library that provides automatic retry and circuit breaker capabilities directly within the httpx transport layer.

## Files to Create/Modify

- `httpx/_transports/resilient.py` - Resilient transport implementation (new)

## Requirements

### ResilientTransport Class

Implement a `ResilientTransport` class in `httpx/_transports/resilient.py` that wraps an existing `httpx.BaseTransport` and adds:

**Retry Logic:**
- Maximum 3 retry attempts on transient failures
- Exponential backoff between retries: 1s → 2s → 4s
- Retry only on: HTTP 5xx responses, `ConnectError`, `TimeoutException`
- Do NOT retry on: HTTP 4xx responses (client errors)
- Configurable timeout settings per request

**Circuit Breaker:**
- Three states: `CLOSED`, `OPEN`, `HALF_OPEN`
- Transition to `OPEN` after 5 consecutive failures
- 30-second cooldown before transitioning to `HALF_OPEN`
- Single success in `HALF_OPEN` restores to `CLOSED`
- Raise custom `CircuitOpenError` when circuit is open

### Expected Functionality

- Retry logic exhausts attempts and raises the final exception appropriately
- Circuit breaker opens when the failure threshold is reached
- Circuit transitions from `HALF_OPEN` to `CLOSED` on a successful request
- 4xx client errors are not retried (only 5xx and connection errors)

## Acceptance Criteria

- `httpx/_transports/resilient.py` compiles without syntax errors
- `ResilientTransport` correctly implements retry and circuit breaker behavior
- Error handling covers all specified scenarios
