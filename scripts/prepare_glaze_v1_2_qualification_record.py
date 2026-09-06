#!/usr/bin/env python3
"""Create fail-closed exact-head GLAZE UI V1.2 qualification record drafts.

This helper only initializes separate evidence records from governed templates. It never
marks human review, manual assistive-technology execution, physical-device identity,
scenario success, performance acceptance, RC readiness, or Stable readiness as passed.
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
HEX40 = re.compile(r"^[0-9a-f]{40}$")
TEMPLATES = {
    "human-optical": ROOT / "acceptance/v1.2-human-optical-review-record.template.json",
    "assistive-technology": ROOT / "acceptance/v1.2-assistive-technology-qualification.template.json",
    "device-performance": ROOT / "acceptance/v1.2-device-performance-qualification.template.json",
}


class PreparationError(RuntimeError):
    pass


def req(ok: bool, message: str) -> None:
    if not ok:
        raise PreparationError(message)


def head_revision() -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    req(bool(HEX40.fullmatch(value)), f"Git HEAD is not an immutable 40-character lowercase SHA: {value!r}")
    return value


def load_template(kind: str) -> dict[str, Any]:
    path = TEMPLATES[kind]
    req(path.is_file(), f"missing governed template: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    req(isinstance(value, dict), f"template is not a JSON object: {path.relative_to(ROOT)}")
    return value


def stamp_revision(value: Any, revision: str) -> Any:
    if isinstance(value, dict):
        return {key: stamp_revision(item, revision) for key, item in value.items()}
    if isinstance(value, list):
        return [stamp_revision(item, revision) for item in value]
    if isinstance(value, str) and value == "REPLACE_WITH_EXACT_40_CHAR_SOURCE_SHA":
        return revision
    return value


def prepare(kind: str, operator: str, role: str | None, platform: str | None) -> dict[str, Any]:
    revision = head_revision()
    record = stamp_revision(load_template(kind), revision)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if kind == "human-optical":
        record["reviewedAt"] = now
        record["reviewer"] = operator
        if role:
            record["reviewerRole"] = role
    elif kind == "assistive-technology":
        record["capturedAt"] = now
        record["operator"] = operator
        if platform:
            record["platform"] = platform
    else:
        record["capturedAt"] = now
        record["capturedBy"] = operator

    # Assert that initialization remains fail-closed.
    if kind == "human-optical":
        req(record.get("decision") == "rejected", "human optical draft must initialize rejected")
        req(all(item.get("reviewed") is False for item in record.get("evidenceArtifacts", [])), "human optical artifacts must initialize unreviewed")
    elif kind == "assistive-technology":
        req(record.get("manualExecution") is False, "assistive-technology draft must initialize non-manual")
        req(record.get("sessionDecision") == "session-fail", "assistive-technology draft must initialize failed")
        req(record.get("device", {}).get("physicalDevice") is False, "assistive-technology draft must not assert physical hardware")
    else:
        req(record.get("device", {}).get("physicalDevice") is False, "device-performance draft must not assert physical hardware")
        req(record.get("decision") != "accepted", "device-performance draft must not initialize accepted")

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(TEMPLATES))
    parser.add_argument("--output", type=Path, required=True, help="Path for the new separate evidence-record draft")
    parser.add_argument("--operator", required=True, help="Human operator/reviewer name to place in the draft")
    parser.add_argument("--role", help="Reviewer role for human-optical records")
    parser.add_argument("--platform", help="Platform label for assistive-technology records")
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing draft path")
    args = parser.parse_args()

    req(args.operator.strip() != "", "--operator must not be empty")
    if args.kind == "human-optical":
        req(bool(args.role and args.role.strip()), "human-optical initialization requires --role")
    if args.kind == "assistive-technology":
        req(bool(args.platform and args.platform.strip()), "assistive-technology initialization requires --platform")

    output = args.output.expanduser().resolve()
    req(args.force or not output.exists(), f"refusing to overwrite existing record draft: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    record = prepare(args.kind, args.operator.strip(), args.role.strip() if args.role else None, args.platform.strip() if args.platform else None)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"Created fail-closed {args.kind} qualification draft: {output}")
    print(f"Exact source revision: {record['sourceRevision']}")
    print("This draft is not acceptance evidence until the required real human/manual/physical observations are completed and separately validated.")


if __name__ == "__main__":
    try:
        main()
    except PreparationError as exc:
        raise SystemExit(f"GLAZE UI V1.2 qualification record preparation failed: {exc}")
