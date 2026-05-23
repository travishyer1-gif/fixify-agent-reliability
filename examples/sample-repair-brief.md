# Sample Repair Brief

- Incident: `fix-2026-01-01-synthetic-preview-false-success`
- Failure type: `preview`
- Severity: `high`
- Owner layer: `code_guardrail`
- Invariant: Approval previews must include callback routing and rendered content before they are approval-ready.

## Repair Actions

1. Add a preview validator before approval buttons render.
2. Return a blocked status when callback routing is missing.
3. Record the validator result in the preview artifact.

## Regression Checks

1. Missing callback routing fails closed.
2. Complete preview record passes.

## Smoke Checks

1. Run synthetic preview creation with a complete fixture.
2. Run synthetic preview creation with a missing callback route.

