Fixify generally solves the problem of an agent making the same mistake twice. 

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

