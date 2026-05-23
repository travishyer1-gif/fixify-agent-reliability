from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

STATUS_ORDER = {"captured": 0, "proposed": 1, "patched": 2, "verified": 3, "closed": 4}

FAILURE_KEYWORDS = {
    "approval": ["approval", "bypass", "unauthorized", "send"],
    "preview": ["preview", "callback", "draft"],
    "routing": ["routing", "wrong skill", "misroute", "owner"],
    "state": ["state", "duplicate", "transition", "status"],
    "tooling": ["cli", "attachment", "upload", "tool", "script"],
    "environment": ["dependency", "auth", "timeout", "environment"],
    "quality": ["quality", "tone", "summary", "wording"],
}

FIX_CLASS_BY_FAILURE = {
    "approval": "guardrail",
    "preview": "guardrail",
    "routing": "routing_patch",
    "state": "resolver",
    "tooling": "guardrail",
    "environment": "test",
    "quality": "eval",
}

SEVERITY_KEYWORDS = {
    "critical": ["security", "customer-impacting", "external state", "production"],
    "high": ["false success", "approval", "send", "submit", "mutate"],
    "medium": ["manual recovery", "missing evidence", "reliability"],
    "low": ["cosmetic", "minor"],
}


@dataclass(frozen=True)
class Incident:
    incident_id: str
    title: str
    summary: str
    invariant: str
    expected: str
    observed: str
    evidence: str
    workflow: str = "generic"
    failure_type: str = "quality"
    severity: str = "medium"
    recommended_fix_class: str = "guardrail"
    status: str = "captured"
    created: str = ""
    path: str = ""


@dataclass(frozen=True)
class RepairBrief:
    incident_id: str
    title: str
    invariant: str
    failure_type: str
    severity: str
    recommended_fix_class: str
    owner_layer: str
    repair_actions: list[str]
    regression_checks: list[str]
    smoke_checks: list[str]
    close_criteria: list[str]
    source_incident: str


@dataclass(frozen=True)
class CloseCheck:
    incident_id: str
    closeable: bool
    requirements: dict[str, bool]
    paths: dict[str, str]


def slugify(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return clean or "incident"


def artifact_dirs(output_dir: Path) -> dict[str, Path]:
    return {
        "incidents": output_dir / "incidents",
        "repair_briefs": output_dir / "repair-briefs",
        "evals": output_dir / "generated-evals",
        "smoke": output_dir / "generated-smoke",
        "reports": output_dir / "reports",
    }


def ensure_artifact_dirs(output_dir: Path) -> dict[str, Path]:
    dirs = artifact_dirs(output_dir)
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    return dirs


def detect_first(text: str, options: dict[str, list[str]], default: str) -> str:
    lowered = text.lower()
    best = default
    best_score = 0
    for label, keywords in options.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best = label
            best_score = score
    return best


def triage_values(text: str, explicit_failure_type: str | None = None) -> tuple[str, str, str]:
    failure_type = explicit_failure_type or detect_first(text, FAILURE_KEYWORDS, "quality")
    severity = detect_first(text, SEVERITY_KEYWORDS, "medium")
    fix_class = FIX_CLASS_BY_FAILURE.get(failure_type, "guardrail")
    if "invariant" in text.lower() or "must not" in text.lower():
        fix_class = "guardrail"
    return failure_type, severity, fix_class


def render_front_matter(values: dict[str, str]) -> str:
    lines = ["---"]
    for key, value in values.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def capture_incident(
    *,
    output_dir: Path,
    title: str,
    summary: str,
    invariant: str,
    expected: str = "",
    observed: str = "",
    evidence: str = "",
    workflow: str = "generic",
    status: str = "captured",
    today: date | None = None,
) -> Path:
    dirs = ensure_artifact_dirs(output_dir)
    created = (today or date.today()).isoformat()
    slug = slugify(title)
    text_for_triage = " ".join([title, summary, invariant, expected, observed, evidence, workflow])
    failure_type, severity, fix_class = triage_values(text_for_triage)
    incident_id = f"fix-{created}-{slug}"
    path = dirs["incidents"] / f"{created}-{slug}.md"
    front_matter = render_front_matter(
        {
            "incident_id": incident_id,
            "created": created,
            "workflow": workflow,
            "failure_type": failure_type,
            "severity": severity,
            "recommended_fix_class": fix_class,
            "status": status,
        }
    )
    body = f"""# {title}

## Summary
{summary}

## Expected invariant
{invariant}

## Expected behavior
{expected or invariant}

## Observed behavior
{observed or summary}

## Evidence
{evidence or "TBD"}
"""
    path.write_text(front_matter + "\n\n" + body, encoding="utf-8")
    return path


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    lines = text.splitlines()
    values: dict[str, str] = {}
    end_index = 0
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values, "\n".join(lines[end_index + 1 :]).lstrip()


def section(body: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def load_incident(path: Path) -> Incident:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    summary = section(body, "Summary")
    invariant = section(body, "Expected invariant") or section(body, "Expected behavior")
    expected = section(body, "Expected behavior") or invariant
    observed = section(body, "Observed behavior") or summary
    evidence = section(body, "Evidence")
    triage_text = " ".join([title, summary, invariant, expected, observed, evidence, meta.get("workflow", "")])
    failure_type, severity, fix_class = triage_values(triage_text, meta.get("failure_type"))
    return Incident(
        incident_id=meta.get("incident_id", f"fix-{slugify(path.stem)}"),
        title=title,
        summary=summary,
        invariant=invariant,
        expected=expected,
        observed=observed,
        evidence=evidence,
        workflow=meta.get("workflow", "generic"),
        failure_type=failure_type,
        severity=meta.get("severity", severity),
        recommended_fix_class=meta.get("recommended_fix_class", fix_class),
        status=meta.get("status", "captured"),
        created=meta.get("created", ""),
        path=str(path),
    )


def triage_incident(path: Path) -> dict[str, str]:
    incident = load_incident(path)
    return {
        "incident_id": incident.incident_id,
        "workflow": incident.workflow,
        "failure_type": incident.failure_type,
        "severity": incident.severity,
        "recommended_fix_class": incident.recommended_fix_class,
        "status": incident.status,
    }


def owner_layer_for(incident: Incident) -> str:
    if incident.failure_type in {"approval", "preview", "state", "tooling"}:
        return "code_guardrail"
    if incident.failure_type == "routing":
        return "router_or_policy"
    if incident.failure_type == "quality":
        return "eval_and_prompt"
    return "workflow_contract"


def build_repair_brief(incident: Incident) -> RepairBrief:
    invariant = incident.invariant or "A named invariant must be recorded before close."
    return RepairBrief(
        incident_id=incident.incident_id,
        title=incident.title,
        invariant=invariant,
        failure_type=incident.failure_type,
        severity=incident.severity,
        recommended_fix_class=incident.recommended_fix_class,
        owner_layer=owner_layer_for(incident),
        repair_actions=[
            "Add a fail-closed check for the invariant.",
            "Record evidence before reporting workflow success.",
            "Update the owning workflow contract with the invariant.",
        ],
        regression_checks=[
            "Replay the failing scenario with the missing invariant evidence.",
            "Assert the workflow refuses success until evidence is present.",
        ],
        smoke_checks=[
            "Run the happy path and capture the evidence artifact.",
            "Run the blocked path and capture the refusal output.",
        ],
        close_criteria=[
            "incident status is patched, verified, or closed",
            "repair brief exists",
            "eval scaffold exists",
            "smoke scaffold exists",
            "invariant is non-empty",
            "evidence is non-empty",
        ],
        source_incident=incident.path,
    )


def repair_brief_path(output_dir: Path, incident_path: Path) -> Path:
    return artifact_dirs(output_dir)["repair_briefs"] / f"{incident_path.stem}-repair-brief.json"


def eval_path(output_dir: Path, incident_path: Path) -> Path:
    return artifact_dirs(output_dir)["evals"] / f"{incident_path.stem}-eval.json"


def smoke_path(output_dir: Path, incident_path: Path) -> Path:
    return artifact_dirs(output_dir)["smoke"] / f"{incident_path.stem}-smoke.md"


def generate_repair_brief(*, output_dir: Path, incident_path: Path) -> Path:
    dirs = ensure_artifact_dirs(output_dir)
    incident = load_incident(incident_path)
    brief = build_repair_brief(incident)
    path = dirs["repair_briefs"] / f"{incident_path.stem}-repair-brief.json"
    path.write_text(json.dumps(asdict(brief), indent=2) + "\n", encoding="utf-8")
    return path


def scaffold_eval_and_smoke(*, output_dir: Path, incident_path: Path) -> tuple[Path, Path]:
    ensure_artifact_dirs(output_dir)
    incident = load_incident(incident_path)
    brief = build_repair_brief(incident)
    epath = eval_path(output_dir, incident_path)
    spath = smoke_path(output_dir, incident_path)
    eval_payload = {
        "incident_id": incident.incident_id,
        "expected_failure_type": incident.failure_type,
        "expected_fix_class": incident.recommended_fix_class,
        "invariant": brief.invariant,
        "pass_conditions": brief.close_criteria,
    }
    epath.write_text(json.dumps(eval_payload, indent=2) + "\n", encoding="utf-8")
    smoke_lines = [
        f"# Smoke Check - {incident.title}",
        "",
        f"- Incident: `{incident.incident_id}`",
        f"- Invariant: {brief.invariant}",
        "",
        "## Steps",
        "1. Run the workflow fixture with invariant evidence present.",
        "2. Run the workflow fixture with invariant evidence missing.",
        "3. Confirm success appears only in the first case.",
        "",
        "## Evidence",
        "Record command output, artifact path, or screenshot reference here.",
    ]
    spath.write_text("\n".join(smoke_lines) + "\n", encoding="utf-8")
    return epath, spath


def close_check(*, output_dir: Path, incident_path: Path) -> CloseCheck:
    incident = load_incident(incident_path)
    paths = {
        "incident": str(incident_path),
        "repair_brief": str(repair_brief_path(output_dir, incident_path)),
        "eval": str(eval_path(output_dir, incident_path)),
        "smoke": str(smoke_path(output_dir, incident_path)),
    }
    requirements = {
        "incident_exists": incident_path.exists(),
        "repair_brief_exists": Path(paths["repair_brief"]).exists(),
        "eval_exists": Path(paths["eval"]).exists(),
        "smoke_exists": Path(paths["smoke"]).exists(),
        "invariant_present": bool(incident.invariant and incident.invariant != "TBD"),
        "evidence_present": bool(incident.evidence and incident.evidence != "TBD"),
        "status_patched_or_later": STATUS_ORDER.get(incident.status, -1) >= STATUS_ORDER["patched"],
    }
    return CloseCheck(incident_id=incident.incident_id, closeable=all(requirements.values()), requirements=requirements, paths=paths)


def iter_incidents(output_dir: Path) -> Iterable[Path]:
    incidents_dir = artifact_dirs(output_dir)["incidents"]
    if not incidents_dir.exists():
        return []
    return sorted(incidents_dir.glob("*.md"))


def report(output_dir: Path) -> dict[str, object]:
    incidents = [triage_incident(path) for path in iter_incidents(output_dir)]
    by_failure_type: dict[str, int] = {}
    for incident in incidents:
        key = incident["failure_type"]
        by_failure_type[key] = by_failure_type.get(key, 0) + 1
    return {"total_incidents": len(incidents), "by_failure_type": by_failure_type, "incidents": incidents}

