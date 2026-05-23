Fixify Agent Reliability is a portable Python package for converting AI-agent workflow failures into incidents, repair briefs, eval scaffolds, smoke checks, and close-check evidence. It satisfies the reliability need that agent systems often miss: a failure should become a testable invariant instead of a chat-only lesson. It demonstrates agent engineering capabilities around deterministic guardrails, CLI tooling, artifact contracts, triage heuristics, and verification-first workflow design.

## Install For Local Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

The package has no runtime dependencies outside the Python standard library.

## CLI

```bash
fixify capture --title "Preview false success" --summary "Preview was reported ready without callback routing." --invariant "Approval previews must include callback routing before they are approval-ready."
fixify triage artifacts/incidents/2026-01-01-preview-false-success.md
fixify repair-brief artifacts/incidents/2026-01-01-preview-false-success.md
fixify scaffold artifacts/incidents/2026-01-01-preview-false-success.md
fixify close-check artifacts/incidents/2026-01-01-preview-false-success.md
fixify report
```

Use `--output-dir` to place all generated artifacts somewhere other than `./artifacts`.

## Artifact Model

```text
artifacts/
  incidents/
  repair-briefs/
  generated-evals/
  generated-smoke/
  reports/
```

Close checks require a captured incident, generated repair brief, generated eval scaffold, generated smoke scaffold, a non-empty invariant, evidence, and a patched-or-later incident status.

