# SWE-Skills-Bench: python-resilience (batch2)

# Task: Implement a Resilient HTTP Transport Layer for httpx

## Background

The httpx library (https://github.com/encode/httpx) provides a modern HTTP client for Python. A new transport layer is needed that wraps the standard transport with resilience features — automatic retries with configurable backoff, request timeouts, and circuit-breaking — so that applications gain fault tolerance against transient network failures.

## Files to Create

- `httpx/_transports/resilient.py` — Custom transport class implementing resilience patterns

## Requirements

### Transport Interface

- Implement a transport class compatible with httpx's transport interface
- Wrap an underlying base transport, adding resilience behavior transparently

### Retry Logic

- Automatically retry on transient errors (connection errors, HTTP 502/503/504)
- Configurable maximum retry count
- Exponential backoff between retries with optional jitter

### Timeout Handling

- Per-request timeout enforcement
- Raise an appropriate exception on timeout rather than hanging

### Circuit Breaker

- Track consecutive failures and open the circuit after a configurable threshold
- While open, reject requests immediately without attempting the transport
- After a cooldown period, allow a trial request to test recovery

### Configuration

- All parameters (retry count, backoff base, timeout, circuit breaker thresholds) configurable at construction with sensible defaults

## Expected Functionality

- Healthy requests pass through normally
- Transient failures trigger retries with increasing delays
- Sustained failures trip the circuit breaker for fast failure
- After cooldown, the circuit transitions to half-open allowing recovery

## Acceptance Criteria

- The transport transparently wraps an underlying httpx transport and can be used in place of a normal transport implementation.
- Transient failures trigger retries with configurable backoff behavior instead of failing immediately.
- Requests that exceed the configured timeout fail clearly rather than hanging indefinitely.
- Repeated failures open the circuit breaker and temporarily reject further requests until the cooldown period expires.
- After the cooldown period, the transport supports a recovery attempt and returns to normal operation when the upstream dependency recovers.
