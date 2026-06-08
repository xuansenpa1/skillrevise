# SWE-Skills-Bench: add-malli-schemas (batch1)

# Task: Add Malli Schema Validation for Metabase Alert API

## Background
   Add complete Malli Schema input validation for Metabase's Alert API endpoints
   to ensure type safety and proper validation of incoming requests.

## Files to Create/Modify
   - src/metabase/api/alert.clj
   - test/metabase/api/alert_malli_test.clj

## Requirements
   
   Endpoints to Add Schema:
   - POST /api/alert
   - PUT /api/alert/:id
   
   Schema Fields:
   - card_id: Positive integer, required
   - channels: Non-empty array, each item must contain channel_type string
   - alert_condition: Enum ("rows" or "goal"), required
   - alert_first_only: Boolean, optional, default false
   
   Implementation:
   - Use metabase.util.malli.schema existing base types
   - Proper constraint definitions
   - Clear error messages

### Expected Functionality

   1) Valid input → 200 OK
   2) Missing card_id → 400 Bad Request
   3) channels is empty array → 400 Bad Request
   4) Invalid alert_condition value → 400 Bad Request

## Acceptance Criteria

   - All validation errors return proper status codes
   - No schema validation bypasses
