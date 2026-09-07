#!/usr/bin/env python3
"""Report GLAZE UI V1.3 qualification readiness without promoting lifecycle state.

This tool is intentionally observational. It reads the governed qualification
matrix and exact-revision evidence records, reports conflicts and missing gates,
and never writes lifecycle or evidence state. A clean report is not a promotion.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_STATUSES = {"in_progress", "passed", "failed", "superseded"}


class ReportError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReportError(f"{path} must contain a JSON object")
    return value


def resolve_source_revision(root: Path, explicit: str | None) -> str | None:
    if explicit:
        if not SHA40.fullmatch(explicit):
            raise ReportError("--source-revision must be a lowercase 40-character Git SHA")
        return explicit
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    revision = completed.stdout.strip()
    return revision if SHA40.fullmatch(revision) else None


def validate_record(record: dict[str, Any], path: Path, workstream_ids: set[str]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "workstream_id",
        "target",
        "status",
        "observed_at",
        "review_authority",
        "evidence_references",
        "disposition",
    }
    missing = sorted(required - set(record))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return errors

    if record.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    workstream_id = record.get("workstream_id")
    if workstream_id not in workstream_ids:
        errors.append(f"unknown workstream_id: {workstream_id!r}")

    target = record.get("target")
    if not isinstance(target, dict):
        errors.append("target must be an object")
    else:
        if target.get("product") != "GLAZE UI V1.3":
            errors.append("target.product must be GLAZE UI V1.3")
        if target.get("target_version") != "1.3.0-candidate":
            errors.append("target.target_version must be 1.3.0-candidate")
        revision = target.get("source_revision")
        if not isinstance(revision, str) or not SHA40.fullmatch(revision):
            errors.append("target.source_revision must be a lowercase 40-character Git SHA")

    status = record.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"unsupported status: {status!r}")

    references = record.get("evidence_references")
    if not isinstance(references, list) or not references or not all(isinstance(item, str) and item for item in references):
        errors.append("evidence_references must be a non-empty list of strings")

    disposition = record.get("disposition")
    accepted = None
    if not isinstance(disposition, dict):
        errors.append("disposition must be an object")
    else:
        accepted = disposition.get("accepted_for_lifecycle_gate")
        if not isinstance(accepted, bool):
            errors.append("disposition.accepted_for_lifecycle_gate must be boolean")

    if status == "passed":
        if accepted is not True:
            errors.append("passed records must be accepted_for_lifecycle_gate=true")
        if isinstance(references, list) and len(references) < 2:
            errors.append("passed records require at least two evidence references")
    elif status in {"in_progress", "failed", "superseded"} and accepted is not False:
        errors.append(f"{status} records must be accepted_for_lifecycle_gate=false")

    return [f"{path.name}: {error}" for error in errors]


def build_report(root: Path, source_revision: str | None = None) -> dict[str, Any]:
    matrix_path = root / "contracts" / "v1.3" / "qualification-matrix.json"
    evidence_dir = root / "evidence" / "v1.3"
    matrix = load_json(matrix_path)

    if matrix.get("schemaVersion") != 1:
        raise ReportError("qualification matrix schemaVersion must be 1")
    if matrix.get("targetVersion") != "1.3.0-candidate":
        raise ReportError("qualification matrix targetVersion is not 1.3.0-candidate")

    workstreams = matrix.get("workstreams")
    if not isinstance(workstreams, list) or not workstreams:
        raise ReportError("qualification matrix must declare workstreams")
    workstream_ids = {item.get("id") for item in workstreams if isinstance(item, dict)}
    if None in workstream_ids or len(workstream_ids) != len(workstreams):
        raise ReportError("qualification matrix workstream ids must be unique non-null values")

    record_entries: list[tuple[Path, dict[str, Any]]] = []
    invalid_records: list[str] = []
    if evidence_dir.is_dir():
        for path in sorted(evidence_dir.glob("*.json")):
            try:
                record = load_json(path)
            except ReportError as exc:
                invalid_records.append(str(exc))
                continue
            errors = validate_record(record, path, workstream_ids)
            invalid_records.extend(errors)
            record_entries.append((path, record))

    grouped: dict[str, list[tuple[Path, dict[str, Any]]]] = defaultdict(list)
    for entry in record_entries:
        workstream_id = entry[1].get("workstream_id")
        if workstream_id in workstream_ids:
            grouped[workstream_id].append(entry)

    summaries: list[dict[str, Any]] = []
    all_blocking_ready = True
    any_conflict = False
    for workstream in workstreams:
        workstream_id = workstream["id"]
        entries = grouped.get(workstream_id, [])
        active = [(path, record) for path, record in entries if record.get("status") != "superseded"]
        revisions = sorted({record.get("target", {}).get("source_revision") for _, record in active if isinstance(record.get("target"), dict) and record.get("target", {}).get("source_revision")})
        accepted_passes = [
            (path, record)
            for path, record in active
            if record.get("status") == "passed"
            and isinstance(record.get("disposition"), dict)
            and record["disposition"].get("accepted_for_lifecycle_gate") is True
        ]
        exact_passes = [
            (path, record)
            for path, record in accepted_passes
            if source_revision is not None
            and isinstance(record.get("target"), dict)
            and record["target"].get("source_revision") == source_revision
        ]
        conflicting_revisions = len(revisions) > 1
        multiple_active_accepted_passes = len(accepted_passes) > 1
        conflict = conflicting_revisions or multiple_active_accepted_passes
        any_conflict = any_conflict or conflict

        status_counts = Counter(str(record.get("status")) for _, record in entries)
        exact_revision_ready = source_revision is not None and len(exact_passes) == 1 and not conflict
        if workstream.get("blockingForLifecyclePromotion") is True and not exact_revision_ready:
            all_blocking_ready = False

        unresolved_issues = []
        for path, record in active:
            issues = record.get("issues")
            if not isinstance(issues, list):
                continue
            for issue in issues:
                if isinstance(issue, dict) and issue.get("resolved") is False:
                    unresolved_issues.append({
                        "record": path.name,
                        "severity": issue.get("severity"),
                        "summary": issue.get("summary"),
                    })

        summaries.append({
            "id": workstream_id,
            "title": workstream.get("title"),
            "mode": workstream.get("mode"),
            "blocking_for_lifecycle_promotion": bool(workstream.get("blockingForLifecyclePromotion")),
            "required_evidence_catalog": workstream.get("requiredEvidence", []),
            "record_count": len(entries),
            "active_record_count": len(active),
            "status_counts": dict(sorted(status_counts.items())),
            "active_source_revisions": revisions,
            "accepted_pass_record_count": len(accepted_passes),
            "exact_revision_accepted_pass_count": len(exact_passes),
            "exact_revision_ready": exact_revision_ready,
            "conflicting_source_revisions": conflicting_revisions,
            "multiple_active_accepted_passes": multiple_active_accepted_passes,
            "unresolved_issues": unresolved_issues,
            "records": [path.name for path, _ in entries],
        })

    lifecycle = matrix.get("lifecycle")
    promotion_authorized = False
    return {
        "schema_version": 1,
        "report_type": "glaze-v1.3-qualification-readiness",
        "target_product": matrix.get("product"),
        "target_version": matrix.get("targetVersion"),
        "matrix_lifecycle": lifecycle,
        "source_stable": matrix.get("sourceStable"),
        "evaluated_source_revision": source_revision,
        "evidence_record_count": len(record_entries),
        "invalid_records": invalid_records,
        "has_invalid_records": bool(invalid_records),
        "has_evidence_conflicts": any_conflict,
        "all_blocking_workstreams_ready_for_exact_revision": all_blocking_ready and not invalid_records and not any_conflict,
        "promotion_authorized": promotion_authorized,
        "promotion_authorization_reason": "This reporter is observational and cannot authorize lifecycle promotion.",
        "consumer_eligible": False,
        "downstream_production_acceptance_established": False,
        "workstreams": summaries,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "GLAZE UI V1.3 qualification readiness",
        f"Target: {report['target_version']} ({report['matrix_lifecycle']})",
        f"Evaluated source revision: {report['evaluated_source_revision'] or 'unresolved'}",
        f"Evidence records: {report['evidence_record_count']}",
        f"Invalid records: {len(report['invalid_records'])}",
        f"Evidence conflicts: {'yes' if report['has_evidence_conflicts'] else 'no'}",
        "",
    ]
    for workstream in report["workstreams"]:
        ready = "READY" if workstream["exact_revision_ready"] else "BLOCKED"
        lines.append(f"[{ready}] {workstream['id']}")
        lines.append(
            "  records={record_count} active={active_record_count} accepted_pass={accepted_pass_record_count} exact_pass={exact_revision_accepted_pass_count}".format(**workstream)
        )
        if workstream["active_source_revisions"]:
            lines.append("  source revisions: " + ", ".join(workstream["active_source_revisions"]))
        if workstream["conflicting_source_revisions"]:
            lines.append("  conflict: multiple active source revisions")
        if workstream["multiple_active_accepted_passes"]:
            lines.append("  conflict: multiple active accepted pass records")
        if workstream["unresolved_issues"]:
            lines.append(f"  unresolved issues: {len(workstream['unresolved_issues'])}")
    if report["invalid_records"]:
        lines.extend(["", "Invalid evidence records:"])
        lines.extend(f"- {item}" for item in report["invalid_records"])
    lines.extend([
        "",
        f"All blocking workstreams ready for exact revision: {report['all_blocking_workstreams_ready_for_exact_revision']}",
        "Promotion authorized: false",
        "Consumer eligible: false",
        "Downstream production acceptance established: false",
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-revision")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-invalid", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        source_revision = resolve_source_revision(root, args.source_revision)
        report = build_report(root, source_revision)
    except ReportError as exc:
        print(f"qualification readiness report failed: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n" if args.as_json else render_text(report)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    if args.fail_on_invalid and (report["has_invalid_records"] or report["has_evidence_conflicts"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
