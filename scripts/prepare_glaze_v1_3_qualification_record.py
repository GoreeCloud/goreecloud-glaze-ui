#!/usr/bin/env python3
"""Prepare fail-closed GLAZE UI V1.3 qualification evidence drafts.

The helper binds a draft to an immutable source revision and initializes it as
``in_progress`` with lifecycle acceptance disabled. It does not perform a human
review, assistive-technology session, physical-device test, performance run,
native-adapter review, lifecycle promotion, or consumer-conformance decision.

Drafts are intentionally restricted to ``artifacts/v1.3/qualification-drafts``.
Accepted qualification records remain governed separately under ``evidence/v1.3``.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROOT = (ROOT / "artifacts" / "v1.3" / "qualification-drafts").resolve()
HEX40 = re.compile(r"^[0-9a-f]{40}$")

WORKSTREAMS = {
    "human-optical": "human-optical-and-icon-collision-qualification",
    "assistive-technology": "manual-assistive-technology-qualification",
    "physical-device": "physical-device-native-platform-qualification",
    "physical-performance": "physical-device-production-performance-qualification",
    "personalization-adapter": "native-personalization-adapter-qualification",
    "stable-activation": "stable-activation-and-source-namespace-cleanup",
}

WORKSTREAM_NOTES = {
    "human-optical": (
        "Real human optical review is incomplete. Before a pass is possible, review all "
        "55 rules in contracts/v1.3/quality-rules.candidate.json and record the required "
        "quality_review object with truthful observations."
    ),
    "assistive-technology": (
        "Real manual assistive-technology execution is incomplete. Automated accessibility "
        "checks do not substitute for the required manual session."
    ),
    "physical-device": (
        "Real physical-device/native-platform execution is incomplete. Simulation and "
        "emulation do not satisfy this blocking qualification track."
    ),
    "physical-performance": (
        "Real physical-device production-performance execution is incomplete. Synthetic "
        "or simulated results do not satisfy the required physical performance evidence."
    ),
    "personalization-adapter": (
        "Native Personalization adapter qualification is incomplete. Only adapters actually "
        "claimed by the source revision may be reviewed and accepted."
    ),
    "stable-activation": (
        "Stable activation/source-namespace cleanup review is incomplete. This draft grants "
        "no Candidate activation, Stable promotion, source cleanup, or consumer conformance."
    ),
}


class PreparationError(RuntimeError):
    """Raised when a draft would violate fail-closed preparation rules."""


def req(ok: bool, message: str) -> None:
    if not ok:
        raise PreparationError(message)


def validate_revision(value: str) -> str:
    value = value.strip()
    req(bool(HEX40.fullmatch(value)), f"source revision must be an immutable 40-character lowercase SHA: {value!r}")
    return value


def head_revision() -> str:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PreparationError("unable to resolve Git HEAD; pass --source-revision explicitly") from exc
    return validate_revision(value)


def observed_at_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_record(
    kind: str,
    operator: str,
    source_revision: str,
    *,
    platform: str | None = None,
    device: str | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    req(kind in WORKSTREAMS, f"unsupported qualification workstream alias: {kind}")
    operator = operator.strip()
    req(bool(operator), "operator/reviewer authority must not be empty")
    revision = validate_revision(source_revision)

    environment: dict[str, Any] = {
        "draft": True,
        "summary": "DRAFT ONLY — replace with the exact real qualification environment before acceptance.",
    }
    if platform and platform.strip():
        environment["platform"] = platform.strip()
    if device and device.strip():
        environment["device"] = device.strip()

    record: dict[str, Any] = {
        "schema_version": 2,
        "workstream_id": WORKSTREAMS[kind],
        "target": {
            "product": "GLAZE UI V1.3",
            "target_version": "1.3.0-candidate",
            "source_revision": revision,
        },
        "status": "in_progress",
        "observed_at": observed_at or observed_at_now(),
        "review_authority": {
            "mode": "human",
            "authority": operator,
        },
        "environment": environment,
        "evidence_references": [
            "DRAFT: replace with concrete immutable evidence references from the real qualification session"
        ],
        "issues": [
            {
                "summary": WORKSTREAM_NOTES[kind],
                "severity": "info",
                "resolved": False,
                "reference": None,
            }
        ],
        "disposition": {
            "accepted_for_lifecycle_gate": False,
            "notes": (
                "DRAFT ONLY. No lifecycle promotion, Candidate activation, Stable activation, "
                "source cleanup, or consumer conformance is granted by this record."
            ),
        },
    }

    assert_fail_closed(record)
    return record


def assert_fail_closed(record: dict[str, Any]) -> None:
    req(record.get("status") == "in_progress", "prepared V1.3 record must initialize in_progress")
    disposition = record.get("disposition", {})
    req(disposition.get("accepted_for_lifecycle_gate") is False, "prepared V1.3 record must not be lifecycle-accepted")
    req(record.get("quality_review") is None, "prepared V1.3 record must not claim completed 55-rule human review")
    target = record.get("target", {})
    validate_revision(str(target.get("source_revision", "")))
    references = record.get("evidence_references", [])
    req(len(references) == 1 and str(references[0]).startswith("DRAFT:"), "prepared evidence reference must remain an explicit draft placeholder")
    issues = record.get("issues", [])
    req(bool(issues) and any(item.get("resolved") is False for item in issues), "prepared V1.3 record must retain an unresolved session-incomplete issue")


def resolve_output(path: Path) -> Path:
    output = path.expanduser()
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    try:
        output.relative_to(DRAFT_ROOT)
    except ValueError as exc:
        raise PreparationError(
            f"draft output must stay under {DRAFT_ROOT.relative_to(ROOT)}; accepted evidence belongs in evidence/v1.3 only after real qualification"
        ) from exc
    req(output.suffix == ".json", "qualification draft output must use a .json suffix")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(WORKSTREAMS), help="Blocking qualification workstream to prepare")
    parser.add_argument("--output", type=Path, required=True, help="Draft JSON path under artifacts/v1.3/qualification-drafts")
    parser.add_argument("--operator", required=True, help="Human reviewer/operator authority for the future real session")
    parser.add_argument("--source-revision", help="Exact 40-character source SHA; defaults to the checked-out Git HEAD")
    parser.add_argument("--platform", help="Optional expected platform label; verify it during the real session")
    parser.add_argument("--device", help="Optional expected device label; verify it during the real session")
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing draft only")
    args = parser.parse_args()

    output = resolve_output(args.output)
    req(args.force or not output.exists(), f"refusing to overwrite existing qualification draft: {output}")
    revision = validate_revision(args.source_revision) if args.source_revision else head_revision()
    record = build_record(
        args.kind,
        args.operator,
        revision,
        platform=args.platform,
        device=args.device,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Created fail-closed V1.3 qualification draft: {output.relative_to(ROOT)}")
    print(f"Workstream: {record['workstream_id']}")
    print(f"Exact source revision: {record['target']['source_revision']}")
    print("Status: in_progress; accepted_for_lifecycle_gate: false")
    print("This file is a preparation aid only. It is not accepted qualification evidence and grants no lifecycle promotion.")


if __name__ == "__main__":
    try:
        main()
    except PreparationError as exc:
        raise SystemExit(f"GLAZE UI V1.3 qualification draft preparation failed: {exc}")
