from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .core import capture_incident, close_check, generate_repair_brief, report, scaffold_eval_and_smoke, triage_incident


def output_dir_arg(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portable Fixify reliability CLI")
    parser.add_argument("--output-dir", type=output_dir_arg, default=Path("artifacts").resolve())
    sub = parser.add_subparsers(dest="command", required=True)

    capture = sub.add_parser("capture", help="Capture an incident artifact")
    capture.add_argument("--title", required=True)
    capture.add_argument("--summary", required=True)
    capture.add_argument("--invariant", required=True)
    capture.add_argument("--expected", default="")
    capture.add_argument("--observed", default="")
    capture.add_argument("--evidence", default="")
    capture.add_argument("--workflow", default="generic")
    capture.add_argument("--status", default="captured")

    triage = sub.add_parser("triage", help="Classify an incident")
    triage.add_argument("incident", type=Path)

    brief = sub.add_parser("repair-brief", help="Generate a repair brief")
    brief.add_argument("incident", type=Path)

    scaffold = sub.add_parser("scaffold", help="Generate eval and smoke scaffolds")
    scaffold.add_argument("incident", type=Path)

    check = sub.add_parser("close-check", help="Check whether an incident can close")
    check.add_argument("incident", type=Path)

    sub.add_parser("report", help="Summarize incidents")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "capture":
        path = capture_incident(
            output_dir=args.output_dir,
            title=args.title,
            summary=args.summary,
            invariant=args.invariant,
            expected=args.expected,
            observed=args.observed,
            evidence=args.evidence,
            workflow=args.workflow,
            status=args.status,
        )
        print(json.dumps({"ok": True, "path": str(path)}, indent=2))
        return 0
    if args.command == "triage":
        print(json.dumps(triage_incident(args.incident), indent=2))
        return 0
    if args.command == "repair-brief":
        path = generate_repair_brief(output_dir=args.output_dir, incident_path=args.incident)
        print(json.dumps({"ok": True, "path": str(path)}, indent=2))
        return 0
    if args.command == "scaffold":
        eval_file, smoke_file = scaffold_eval_and_smoke(output_dir=args.output_dir, incident_path=args.incident)
        print(json.dumps({"ok": True, "eval": str(eval_file), "smoke": str(smoke_file)}, indent=2))
        return 0
    if args.command == "close-check":
        result = close_check(output_dir=args.output_dir, incident_path=args.incident)
        print(json.dumps(asdict(result), indent=2))
        return 0 if result.closeable else 1
    if args.command == "report":
        print(json.dumps(report(args.output_dir), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
