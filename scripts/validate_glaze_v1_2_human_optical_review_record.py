#!/usr/bin/env python3
"""Validate separate exact-revision human optical review records for GLAZE UI V1.2.

This validator proves record integrity only. Its self-test is synthetic and never counts
as human optical acceptance. A real accepted record must be supplied with --record and
must identify an authorized human reviewer plus the exact reviewed Candidate revision.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/v1.2/human-optical-review-packet.candidate.json"
TEMPLATE = ROOT / "acceptance/v1.2-human-optical-review-record.template.json"
LIFECYCLE = ROOT / "registry/lifecycle.json"
VERSION = ROOT / "VERSION"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDERS = {"", "todo", "tbd", "unknown", "n/a", "na", "placeholder", "example", "none", "null"}


class ReviewRecordError(RuntimeError):
    pass


def req(ok: bool, message: str) -> None:
    if not ok:
        raise ReviewRecordError(message)


def read_json(path: Path, *, external: bool = False) -> dict[str, Any]:
    label = str(path) if external else str(path.relative_to(ROOT))
    req(path.is_file(), f"missing required JSON file: {label}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewRecordError(f"invalid JSON file {label}: {exc}") from exc
    req(isinstance(value, dict), f"expected JSON object: {label}")
    return value


def revision() -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    req(bool(HEX40.fullmatch(value)), f"invalid Git revision: {value!r}")
    return value


def meaningful(value: Any, label: str) -> str:
    req(isinstance(value, str), f"{label} must be a string")
    text = value.strip()
    req(text.lower() not in PLACEHOLDERS, f"{label} contains a placeholder value")
    req("REPLACE_WITH_" not in text, f"{label} contains an unresolved template placeholder")
    return text


def valid_timestamp(value: Any, label: str) -> str:
    text = meaningful(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewRecordError(f"{label} must be ISO-8601: {text!r}") from exc
    req(parsed.tzinfo is not None, f"{label} must include an explicit timezone")
    return text


def validate_source() -> dict[str, Any]:
    contract = read_json(CONTRACT)
    lifecycle = read_json(LIFECYCLE)
    template = read_json(TEMPLATE)
    req(VERSION.read_text(encoding="utf-8").strip() == "1.1.0", "VERSION must remain V1.1 Stable")
    req(lifecycle.get("currentStable") == "1.1.0" and lifecycle.get("currentOfficial") == "1.1.0", "Stable/official lifecycle authority drifted")
    req(lifecycle.get("activeCandidate") == "1.2.0-candidate", "active Candidate authority drifted")
    req(contract.get("version") == "1.2.0-candidate" and contract.get("lifecycle") == "candidate", "human optical review lifecycle drifted")
    req(contract.get("humanReview", {}).get("status") == "pending", "machine source may not mark human review complete")
    req(contract.get("requiredOutputClaims", {}).get("humanOpticalAccepted") is False, "machine review packet may not claim human acceptance")
    req(contract.get("rules", {}).get("machineEvidenceMayNotSubstituteHumanOpticalAcceptance") is True, "human optical authority guard drifted")
    req(contract.get("rules", {}).get("humanReviewMayNotPromoteLifecycleByItself") is True, "human review improperly gained lifecycle promotion authority")

    source = template.get("sourceRevision", "")
    req(isinstance(source, str) and "REPLACE_WITH_" in source, "human optical review template must retain an unmistakable source-revision placeholder")
    req(template.get("decision") == "rejected", "human optical review template must fail closed")
    artifacts = template.get("evidenceArtifacts")
    req(isinstance(artifacts, list) and artifacts, "human optical review template must enumerate evidence artifacts")
    req(all(item.get("reviewed") is False for item in artifacts if isinstance(item, dict)), "human optical review template must default every artifact to unreviewed")
    dimensions = template.get("dimensions")
    req(isinstance(dimensions, list) and dimensions, "human optical review template must enumerate review dimensions")
    req(all(item.get("status") == "fail" for item in dimensions if isinstance(item, dict)), "human optical review template must default every dimension to fail")
    return contract


def validate_record(record: dict[str, Any], contract: dict[str, Any], head: str) -> None:
    for field in (
        "schemaVersion", "recordType", "sourceRevision", "repository", "reviewedAt",
        "reviewer", "reviewerRole", "evidenceArtifacts", "dimensions", "exceptions",
        "decision", "summary",
    ):
        req(field in record, f"record missing top-level field {field}")
    req(record.get("schemaVersion") == 1, "record schemaVersion must be 1")
    req(record.get("recordType") == "glaze-v1.2-human-optical-review", "recordType mismatch")
    source = meaningful(record.get("sourceRevision"), "sourceRevision")
    req(bool(HEX40.fullmatch(source)), "sourceRevision must be 40 lowercase hex characters")
    req(source == head, f"stale human optical evidence {source}; expected exact head {head}")
    req(record.get("repository") == "GoreeCloud/goreecloud-glaze-ui", "repository mismatch")
    valid_timestamp(record.get("reviewedAt"), "reviewedAt")
    meaningful(record.get("reviewer"), "reviewer")
    meaningful(record.get("reviewerRole"), "reviewerRole")
    meaningful(record.get("summary"), "summary")

    required_evidence = [item["id"] for item in contract.get("evidenceClasses", [])]
    artifacts = record.get("evidenceArtifacts")
    req(isinstance(artifacts, list), "evidenceArtifacts must be an array")
    artifacts_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(artifacts):
        req(isinstance(item, dict), f"evidenceArtifacts[{index}] must be an object")
        evidence_id = meaningful(item.get("id"), f"evidenceArtifacts[{index}].id")
        req(evidence_id in required_evidence and evidence_id not in artifacts_by_id, f"unexpected or duplicate evidence artifact {evidence_id}")
        artifact_revision = meaningful(item.get("sourceRevision"), f"{evidence_id}.sourceRevision")
        req(artifact_revision == head, f"{evidence_id} is bound to {artifact_revision}; expected {head}")
        meaningful(item.get("artifact"), f"{evidence_id}.artifact")
        req(item.get("reviewed") is True, f"{evidence_id} must be explicitly reviewed")
        artifacts_by_id[evidence_id] = item
    req(set(artifacts_by_id) == set(required_evidence), "record must contain the exact required evidence-artifact set")

    required_dimensions = list(contract.get("reviewDimensions", []))
    dimensions = record.get("dimensions")
    req(isinstance(dimensions, list), "dimensions must be an array")
    dimensions_by_id: dict[str, dict[str, Any]] = {}
    has_failure = False
    for index, item in enumerate(dimensions):
        req(isinstance(item, dict), f"dimensions[{index}] must be an object")
        dimension_id = meaningful(item.get("id"), f"dimensions[{index}].id")
        req(dimension_id in required_dimensions and dimension_id not in dimensions_by_id, f"unexpected or duplicate review dimension {dimension_id}")
        status = item.get("status")
        req(status in {"pass", "fail"}, f"{dimension_id}.status must be pass or fail")
        meaningful(item.get("finding"), f"{dimension_id}.finding")
        has_failure = has_failure or status == "fail"
        dimensions_by_id[dimension_id] = item
    req(set(dimensions_by_id) == set(required_dimensions), "record must contain the exact required review-dimension set")

    exceptions = record.get("exceptions")
    req(isinstance(exceptions, list), "exceptions must be an array")
    for index, exception in enumerate(exceptions):
        meaningful(exception, f"exceptions[{index}]")

    decision = record.get("decision")
    req(decision in {"accepted", "rejected"}, "decision must be accepted or rejected")
    if decision == "accepted":
        req(not has_failure, "accepted human review cannot contain a failed dimension")
        req(not exceptions, "accepted human review cannot contain unresolved exceptions")
    else:
        req(has_failure or exceptions, "rejected human review must identify a failed dimension or exception")


def sample(head: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "recordType": "glaze-v1.2-human-optical-review",
        "sourceRevision": head,
        "repository": "GoreeCloud/goreecloud-glaze-ui",
        "reviewedAt": "2026-09-06T18:00:00Z",
        "reviewer": "synthetic-review-record-self-test",
        "reviewerRole": "validator-self-test",
        "evidenceArtifacts": [
            {"id": item["id"], "sourceRevision": head, "artifact": f"synthetic-{item['id']}", "reviewed": True}
            for item in contract["evidenceClasses"]
        ],
        "dimensions": [
            {"id": dimension, "status": "pass", "finding": f"Synthetic format finding for {dimension}; not human evidence."}
            for dimension in contract["reviewDimensions"]
        ],
        "exceptions": [],
        "decision": "accepted",
        "summary": "Synthetic validator self-test only; not human optical acceptance."
    }


def reject(record: dict[str, Any], contract: dict[str, Any], head: str, label: str) -> None:
    try:
        validate_record(record, contract, head)
    except ReviewRecordError:
        return
    raise ReviewRecordError(f"self-test expected rejection but accepted {label}")


def self_test(contract: dict[str, Any], head: str) -> None:
    valid = sample(head, contract)
    validate_record(valid, contract, head)
    stale = copy.deepcopy(valid)
    stale["sourceRevision"] = "0" * 40 if head != "0" * 40 else "1" * 40
    reject(stale, contract, head, "stale revision")
    missing_review = copy.deepcopy(valid)
    missing_review["evidenceArtifacts"][0]["reviewed"] = False
    reject(missing_review, contract, head, "unreviewed artifact")
    failed_accept = copy.deepcopy(valid)
    failed_accept["dimensions"][0]["status"] = "fail"
    reject(failed_accept, contract, head, "accepted decision with failed dimension")
    exception_accept = copy.deepcopy(valid)
    exception_accept["exceptions"] = ["Synthetic unresolved exception"]
    reject(exception_accept, contract, head, "accepted decision with unresolved exception")
    placeholder = copy.deepcopy(valid)
    placeholder["reviewer"] = "REPLACE_WITH_AUTHORIZED_HUMAN_REVIEWER"
    reject(placeholder, contract, head, "placeholder reviewer")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    contract = validate_source()
    head = revision()
    if args.record:
        validate_record(read_json(args.record.expanduser().resolve(), external=True), contract, head)
        print(f"Validated separate human optical review record for exact revision {head}")
    if args.self_test:
        self_test(contract, head)
        print("Human optical review record protocol self-test passed")
        print("Synthetic self-test records are not human optical evidence")
    if not args.record and not args.self_test:
        print("Human optical review record source validation passed")
    print("Human optical acceptance remains pending until a real authorized exact-revision record is attached")
    print("Lifecycle authority unchanged: V1.1 / 1.1.0 Stable; V1.2 Candidate")


if __name__ == "__main__":
    try:
        main()
    except ReviewRecordError as exc:
        raise SystemExit(f"GLAZE UI V1.2 human optical review record validation failed: {exc}")
