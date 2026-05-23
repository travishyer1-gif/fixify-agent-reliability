---
incident_id: fix-2026-01-01-synthetic-preview-false-success
created: 2026-01-01
workflow: synthetic-email-preview
failure_type: preview
severity: high
recommended_fix_class: guardrail
status: patched
---

# Synthetic Preview False Success

## Summary
An agent reported an approval preview as ready even though the preview record lacked callback routing.

## Expected invariant
Approval previews must include callback routing and rendered content before they are approval-ready.

## Expected behavior
The workflow refuses to surface approval buttons until callback routing exists.

## Observed behavior
The workflow produced a success-like message with incomplete preview state.

## Evidence
Synthetic fixture `preview_missing_callback.json` reproduced the missing callback route.

