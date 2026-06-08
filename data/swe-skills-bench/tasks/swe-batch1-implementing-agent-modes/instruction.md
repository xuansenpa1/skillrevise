# SWE-Skills-Bench: implementing-agent-modes (batch1)

# Task: Add Agent Batch Processing Mode for PostHog

## Background
   Add batch event processing
   capabilities for agent mode, enabling efficient bulk event capture
   with configurable batching parameters.

## Files to Create/Modify
   - posthog/api/capture.py (batch endpoint addition)
   - posthog/settings/batch_config.py (new configuration)
   - posthog/tests/test_batch_capture.py (new tests)

## Requirements
   
   Batch Capture Endpoint:
   - POST /batch endpoint for bulk events
   - Accept array of events in request body
   - Maximum batch size: 100 events
   - Validate each event in batch
   
   Configuration (batch_config.py):
   - BATCH_MAX_SIZE: Maximum events per batch
   - BATCH_TIMEOUT_MS: Timeout for batch processing
   - BATCH_RETRY_COUNT: Retry attempts on failure
   - Environment variable overrides
   
   Batch Processing Logic:
   - Atomic batch processing (all or nothing)
   - Individual event validation
   - Detailed error response for invalid events
   - Performance metrics logging

### Expected Functionality

   - Valid batch succeeds with 200 OK
   - Oversized batch returns 400 Bad Request
   - Invalid event in batch returns detailed error
   - Partial failure handling

## Acceptance Criteria
   - `python manage.py test posthog.tests.test_batch_capture` works correctly
   - Batch endpoint handles 100 events in <500ms
   - Configuration is properly documented
