from __future__ import annotations

from datetime import date

from fixify_reliability.core import capture_incident, close_check, generate_repair_brief, scaffold_eval_and_smoke, triage_incident


def test_capture_triage_and_brief(tmp_path):
    incident = capture_incident(
        output_dir=tmp_path,
        title="Preview false success",
        summary="Preview was reported ready without callback routing.",
        invariant="Approval previews must include callback routing before approval.",
        observed="The preview showed success while callback data was missing.",
        evidence="Synthetic fixture reproduced the missing callback.",
        workflow="preview-first-email",
        status="patched",
        today=date(2026, 1, 1),
    )

    triage = triage_incident(incident)
    assert triage["failure_type"] == "preview"
    assert triage["recommended_fix_class"] == "guardrail"

    brief = generate_repair_brief(output_dir=tmp_path, incident_path=incident)
    eval_file, smoke_file = scaffold_eval_and_smoke(output_dir=tmp_path, incident_path=incident)

    assert brief.exists()
    assert eval_file.exists()
    assert smoke_file.exists()
    assert close_check(output_dir=tmp_path, incident_path=incident).closeable is True


def test_close_check_fails_without_evidence(tmp_path):
    incident = capture_incident(
        output_dir=tmp_path,
        title="Missing evidence",
        summary="The workflow had no proof.",
        invariant="Workflow success must include proof.",
        status="patched",
        today=date(2026, 1, 2),
    )
    generate_repair_brief(output_dir=tmp_path, incident_path=incident)
    scaffold_eval_and_smoke(output_dir=tmp_path, incident_path=incident)

    result = close_check(output_dir=tmp_path, incident_path=incident)

    assert result.closeable is False
    assert result.requirements["evidence_present"] is False

