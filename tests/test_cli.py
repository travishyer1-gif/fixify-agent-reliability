from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(*args: str, cwd=None):
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [sys.executable, "-m", "fixify_reliability.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_capture_and_report(tmp_path):
    output_dir = tmp_path / "artifacts"
    proc = run_cli(
        "--output-dir",
        str(output_dir),
        "capture",
        "--title",
        "Approval leak",
        "--summary",
        "External action was attempted without approval.",
        "--invariant",
        "Approval-required actions must fail closed without approval.",
        "--evidence",
        "Synthetic fixture blocked the missing approval marker.",
        "--status",
        "patched",
    )
    assert proc.returncode == 0, proc.stderr
    incident_path = json.loads(proc.stdout)["path"]

    assert run_cli("--output-dir", str(output_dir), "repair-brief", incident_path).returncode == 0
    assert run_cli("--output-dir", str(output_dir), "scaffold", incident_path).returncode == 0
    assert run_cli("--output-dir", str(output_dir), "close-check", incident_path).returncode == 0

    report = run_cli("--output-dir", str(output_dir), "report")
    assert report.returncode == 0
    payload = json.loads(report.stdout)
    assert payload["total_incidents"] == 1
