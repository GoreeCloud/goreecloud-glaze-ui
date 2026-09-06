#!/usr/bin/env python3
"""Validate fail-closed GLAZE UI V1.2 G5/G6 release-promotion records.

The protocol and self-test are not lifecycle approval. Real G5/G6 decisions must be
separate governed records tied to immutable revisions and authorized human approval.
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
CONTRACT = ROOT / "contracts/v1.2/release-promotion.candidate.json"
RC_TEMPLATE = ROOT / "acceptance/v1.2-rc-acceptance.template.json"
STABLE_TEMPLATE = ROOT / "acceptance/v1.2-stable-promotion.template.json"
LIFECYCLE = ROOT / "registry/lifecycle.json"
VERSION = ROOT / "VERSION"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
PLACEHOLDER_MARKERS = ("REPLACE_WITH_", "Template placeholder")
EMPTY_WORDS = {"", "todo", "tbd", "unknown", "placeholder", "example", "none", "null"}


class PromotionError(RuntimeError):
    pass


def req(ok: bool, message: str) -> None:
    if not ok:
        raise PromotionError(message)


def read_json(path: Path, *, external: bool = False) -> dict[str, Any]:
    label = str(path) if external else str(path.relative_to(ROOT))
    req(path.is_file(), f"missing required JSON file: {label}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PromotionError(f"invalid JSON file {label}: {exc}") from exc
    req(isinstance(value, dict), f"expected JSON object: {label}")
    return value


def head_revision() -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    req(bool(HEX40.fullmatch(value)), f"invalid Git revision: {value!r}")
    return value


def meaningful(value: Any, label: str) -> str:
    req(isinstance(value, str), f"{label} must be a string")
    text = value.strip()
    req(text.lower() not in EMPTY_WORDS, f"{label} contains an empty/placeholder value")
    req(not any(marker in text for marker in PLACEHOLDER_MARKERS), f"{label} contains an unresolved template placeholder")
    return text


def timestamp(value: Any, label: str) -> str:
    text = meaningful(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PromotionError(f"{label} must be ISO-8601: {text!r}") from exc
    req(parsed.tzinfo is not None, f"{label} must include a timezone")
    return text


def exact_revision(value: Any, label: str) -> str:
    text = meaningful(value, label)
    req(bool(HEX40.fullmatch(text)), f"{label} must be 40 lowercase hex characters")
    return text


def source_validation() -> dict[str, Any]:
    contract = read_json(CONTRACT)
    lifecycle = read_json(LIFECYCLE)
    rc = read_json(RC_TEMPLATE)
    stable = read_json(STABLE_TEMPLATE)

    req(VERSION.read_text(encoding="utf-8").strip() == "1.1.0", "VERSION must remain V1.1 Stable while V1.2 is Candidate")
    req(lifecycle.get("currentStable") == "1.1.0", "currentStable drifted before governed V1.2 Stable promotion")
    req(lifecycle.get("currentOfficial") == "1.1.0", "currentOfficial drifted before governed V1.2 Stable promotion")
    req(lifecycle.get("activeCandidate") == "1.2.0-candidate", "active V1.2 Candidate authority drifted")
    req(contract.get("version") == "1.2.0-candidate" and contract.get("lifecycle") == "candidate", "release-promotion contract lifecycle drifted")
    req(contract.get("consumerEligible") is False, "Candidate release-promotion protocol cannot be consumer eligible")

    boundary = contract.get("currentBoundary", {})
    for field in ("rcAcceptanceEstablished", "releaseCandidateEstablished", "stableApprovalEstablished", "stableEstablished", "consumerEligibilityEstablished"):
        req(boundary.get(field) is False, f"Candidate protocol may not pre-claim {field}")

    req(rc.get("decision") == "rejected", "RC template must fail closed")
    req(rc.get("pullRequest") == 0, "RC template must not pre-bind a passing PR identity")
    req(all(item.get("status") == "fail" for item in rc.get("gates", [])), "RC template gates must default to fail")
    req(all(item.get("status") == "missing" for item in rc.get("evidenceClasses", [])), "RC template evidence must default to missing")
    req(rc.get("migrationRollback", {}).get("reviewed") is False, "RC template rollback review must default false")
    req(rc.get("releaseBlockers", {}).get("reviewed") is False, "RC template blocker review must default false")

    req(stable.get("decision") == "rejected", "Stable template must fail closed")
    req(stable.get("consumerEligible") is False, "Stable template must not pre-authorize consumers")
    req(stable.get("lifecycleApproval", {}).get("approved") is False, "Stable template lifecycle approval must default false")
    req(stable.get("rollback", {}).get("preserved") is False, "Stable template rollback preservation must default false")
    req(stable.get("releaseBlockers", {}).get("reviewed") is False, "Stable template blocker review must default false")
    req(not stable.get("postMergeValidation"), "Stable template must not contain fabricated post-merge validation")
    req(not stable.get("releaseArtifacts"), "Stable template must not contain fabricated release artifacts")
    return contract


def validate_rc(record: dict[str, Any], contract: dict[str, Any], expected_revision: str) -> None:
    required = ("schemaVersion", "recordType", "candidateRevision", "repository", "candidateVersion", "reviewedAt", "reviewer", "reviewerRole", "pullRequest", "gates", "evidenceClasses", "migrationRollback", "releaseBlockers", "decision", "summary")
    for field in required:
        req(field in record, f"RC record missing {field}")
    req(record.get("schemaVersion") == 1, "RC schemaVersion must be 1")
    req(record.get("recordType") == contract["rcAcceptance"]["recordType"], "RC recordType mismatch")
    revision = exact_revision(record.get("candidateRevision"), "candidateRevision")
    req(revision == expected_revision, f"RC evidence is stale: {revision}; expected {expected_revision}")
    req(record.get("repository") == "GoreeCloud/goreecloud-glaze-ui", "RC repository mismatch")
    req(record.get("candidateVersion") == contract["rcAcceptance"]["candidateVersion"], "RC candidateVersion mismatch")
    timestamp(record.get("reviewedAt"), "reviewedAt")
    meaningful(record.get("reviewer"), "reviewer")
    meaningful(record.get("reviewerRole"), "reviewerRole")
    meaningful(record.get("summary"), "summary")
    req(isinstance(record.get("pullRequest"), int) and record["pullRequest"] > 0, "RC pullRequest must be a positive integer")

    required_gates = set(contract["rcAcceptance"]["requiredGateIds"])
    gates = record.get("gates")
    req(isinstance(gates, list), "RC gates must be an array")
    by_gate: dict[str, dict[str, Any]] = {}
    for item in gates:
        req(isinstance(item, dict), "each RC gate must be an object")
        gate_id = meaningful(item.get("id"), "gate.id")
        req(gate_id in required_gates and gate_id not in by_gate, f"unexpected or duplicate RC gate {gate_id}")
        req(item.get("status") in contract["rcAcceptance"]["gateStatusValues"], f"{gate_id} has invalid status")
        evidence = item.get("evidence")
        req(isinstance(evidence, list), f"{gate_id}.evidence must be an array")
        if item.get("status") == "pass":
            req(bool(evidence), f"{gate_id} pass requires evidence")
            for index, ref in enumerate(evidence):
                meaningful(ref, f"{gate_id}.evidence[{index}]")
        by_gate[gate_id] = item
    req(set(by_gate) == required_gates, "RC record must contain exactly G0-G4")

    required_classes = set(contract["rcAcceptance"]["requiredEvidenceClasses"])
    classes = record.get("evidenceClasses")
    req(isinstance(classes, list), "RC evidenceClasses must be an array")
    by_class: dict[str, dict[str, Any]] = {}
    for item in classes:
        req(isinstance(item, dict), "each RC evidence class must be an object")
        evidence_id = meaningful(item.get("id"), "evidenceClass.id")
        req(evidence_id in required_classes and evidence_id not in by_class, f"unexpected or duplicate RC evidence class {evidence_id}")
        req(item.get("status") in contract["rcAcceptance"]["evidenceStatusValues"], f"{evidence_id} has invalid status")
        refs = item.get("references")
        req(isinstance(refs, list), f"{evidence_id}.references must be an array")
        if item.get("status") == "current":
            req(bool(refs), f"{evidence_id} current status requires references")
            for index, ref in enumerate(refs):
                meaningful(ref, f"{evidence_id}.references[{index}]")
        by_class[evidence_id] = item
    req(set(by_class) == required_classes, "RC record must contain every required evidence class")

    rollback = record.get("migrationRollback")
    req(isinstance(rollback, dict), "migrationRollback must be an object")
    req(rollback.get("rollbackTargetVersion") == "1.1.0", "RC rollback target version must remain 1.1.0")
    req(rollback.get("rollbackTargetTag") == "v1.1.0", "RC rollback target tag must remain v1.1.0")
    blockers = record.get("releaseBlockers")
    req(isinstance(blockers, dict) and isinstance(blockers.get("open"), list), "releaseBlockers must contain an open array")

    decision = record.get("decision")
    req(decision in contract["rcAcceptance"]["decisionValues"], "invalid RC decision")
    if decision == "approved-for-rc":
        req(all(item["status"] == "pass" for item in by_gate.values()), "approved RC requires G0-G4 pass")
        req(all(item["status"] == "current" for item in by_class.values()), "approved RC requires every evidence class current")
        req(rollback.get("reviewed") is True, "approved RC requires migration/rollback review")
        meaningful(rollback.get("reference"), "migrationRollback.reference")
        req(blockers.get("reviewed") is True, "approved RC requires release-blocker review")
        req(blockers.get("open") == [], "approved RC cannot contain open release blockers")


def validate_stable(record: dict[str, Any], contract: dict[str, Any], expected_revision: str) -> None:
    required = ("schemaVersion", "recordType", "repository", "targetVersion", "reviewedAt", "approver", "approverRole", "selectedRcRevision", "rcAcceptanceRecord", "promotionPullRequest", "mergeRevision", "releaseRevision", "immutableTag", "githubReleaseIdentity", "postMergeValidation", "releaseArtifacts", "lifecycleApproval", "documentationSync", "rollback", "releaseBlockers", "consumerEligible", "decision", "summary")
    for field in required:
        req(field in record, f"Stable record missing {field}")
    req(record.get("schemaVersion") == 1, "Stable schemaVersion must be 1")
    req(record.get("recordType") == contract["stablePromotion"]["recordType"], "Stable recordType mismatch")
    req(record.get("repository") == "GoreeCloud/goreecloud-glaze-ui", "Stable repository mismatch")
    req(record.get("targetVersion") == contract["stablePromotion"]["targetVersion"], "Stable targetVersion mismatch")
    timestamp(record.get("reviewedAt"), "reviewedAt")
    meaningful(record.get("approver"), "approver")
    meaningful(record.get("approverRole"), "approverRole")
    exact_revision(record.get("selectedRcRevision"), "selectedRcRevision")
    meaningful(record.get("rcAcceptanceRecord"), "rcAcceptanceRecord")
    req(isinstance(record.get("promotionPullRequest"), int) and record["promotionPullRequest"] > 0, "promotionPullRequest must be a positive integer")
    exact_revision(record.get("mergeRevision"), "mergeRevision")
    release_revision = exact_revision(record.get("releaseRevision"), "releaseRevision")
    req(release_revision == expected_revision, f"Stable release revision {release_revision} does not match expected {expected_revision}")
    req(record.get("immutableTag") == contract["stablePromotion"]["immutableTag"], "Stable immutable tag must be v1.2.0")
    req(record.get("githubReleaseIdentity") == contract["stablePromotion"]["githubReleaseIdentity"], "Stable GitHub Release identity must be v1.2.0")
    meaningful(record.get("summary"), "summary")

    validations = record.get("postMergeValidation")
    req(isinstance(validations, list), "postMergeValidation must be an array")
    for index, item in enumerate(validations):
        req(isinstance(item, dict), f"postMergeValidation[{index}] must be an object")
        meaningful(item.get("workflow"), f"postMergeValidation[{index}].workflow")
        run_id = item.get("runId")
        req(isinstance(run_id, int) and run_id > 0, f"postMergeValidation[{index}].runId must be positive")
        req(item.get("status") == "passed", f"postMergeValidation[{index}] must have status passed")
        req(exact_revision(item.get("sourceRevision"), f"postMergeValidation[{index}].sourceRevision") == release_revision, "post-merge validation must bind releaseRevision")

    artifacts = record.get("releaseArtifacts")
    req(isinstance(artifacts, list), "releaseArtifacts must be an array")
    for index, item in enumerate(artifacts):
        req(isinstance(item, dict), f"releaseArtifacts[{index}] must be an object")
        meaningful(item.get("name"), f"releaseArtifacts[{index}].name")
        req(exact_revision(item.get("sourceRevision"), f"releaseArtifacts[{index}].sourceRevision") == release_revision, "release artifact must bind releaseRevision")
        digest = meaningful(item.get("digest"), f"releaseArtifacts[{index}].digest")
        req(bool(SHA256.fullmatch(digest)), f"releaseArtifacts[{index}].digest must be sha256:<64 lowercase hex>")

    approval = record.get("lifecycleApproval")
    req(isinstance(approval, dict), "lifecycleApproval must be an object")
    docs = record.get("documentationSync")
    req(isinstance(docs, dict), "documentationSync must be an object")
    rollback = record.get("rollback")
    req(isinstance(rollback, dict), "rollback must be an object")
    blockers = record.get("releaseBlockers")
    req(isinstance(blockers, dict) and isinstance(blockers.get("open"), list), "releaseBlockers must contain an open array")

    decision = record.get("decision")
    req(decision in contract["stablePromotion"]["decisionValues"], "invalid Stable decision")
    if decision == "approved-stable":
        req(bool(validations), "approved Stable requires post-merge exact-revision validation")
        req(bool(artifacts), "approved Stable requires traceable release artifacts")
        req(approval.get("approved") is True, "approved Stable requires explicit lifecycle approval")
        timestamp(approval.get("approvedAt"), "lifecycleApproval.approvedAt")
        meaningful(approval.get("approvedBy"), "lifecycleApproval.approvedBy")
        for field in contract["stablePromotion"]["requiredDocumentationSync"]:
            req(docs.get(field) is True, f"approved Stable requires documentationSync.{field}=true")
        req(rollback.get("version") == contract["stablePromotion"]["previousStableVersion"], "Stable rollback version mismatch")
        req(rollback.get("tag") == contract["stablePromotion"]["previousStableTag"], "Stable rollback tag mismatch")
        req(rollback.get("preserved") is True, "approved Stable requires prior Stable rollback preservation")
        req(blockers.get("reviewed") is True, "approved Stable requires final blocker review")
        req(blockers.get("open") == [], "approved Stable cannot contain open release blockers")
        req(record.get("consumerEligible") is True, "approved Stable must explicitly establish consumer eligibility")


def sample_rc(head: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1, "recordType": contract["rcAcceptance"]["recordType"], "candidateRevision": head,
        "repository": "GoreeCloud/goreecloud-glaze-ui", "candidateVersion": "1.2.0-candidate",
        "reviewedAt": "2026-09-06T18:00:00Z", "reviewer": "synthetic-self-test", "reviewerRole": "validator-self-test", "pullRequest": 136,
        "gates": [{"id": gate, "status": "pass", "evidence": [f"synthetic-{gate}"]} for gate in contract["rcAcceptance"]["requiredGateIds"]],
        "evidenceClasses": [{"id": item, "status": "current", "references": [f"synthetic-{item}"]} for item in contract["rcAcceptance"]["requiredEvidenceClasses"]],
        "migrationRollback": {"reviewed": True, "rollbackTargetVersion": "1.1.0", "rollbackTargetTag": "v1.1.0", "reference": "synthetic-migration-rollback"},
        "releaseBlockers": {"reviewed": True, "open": []}, "decision": "approved-for-rc",
        "summary": "Synthetic format-only G5 self-test; not Release Candidate approval."
    }


def sample_stable(head: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1, "recordType": contract["stablePromotion"]["recordType"], "repository": "GoreeCloud/goreecloud-glaze-ui", "targetVersion": "1.2.0",
        "reviewedAt": "2026-09-06T18:00:00Z", "approver": "synthetic-self-test", "approverRole": "validator-self-test",
        "selectedRcRevision": "1" * 40 if head != "1" * 40 else "2" * 40, "rcAcceptanceRecord": "synthetic-g5-record", "promotionPullRequest": 999,
        "mergeRevision": head, "releaseRevision": head, "immutableTag": "v1.2.0", "githubReleaseIdentity": "v1.2.0",
        "postMergeValidation": [{"workflow": "synthetic", "runId": 1, "status": "passed", "sourceRevision": head}],
        "releaseArtifacts": [{"name": "synthetic-source", "sourceRevision": head, "digest": "sha256:" + "a" * 64}],
        "lifecycleApproval": {"approved": True, "approvedAt": "2026-09-06T18:00:00Z", "approvedBy": "synthetic-self-test"},
        "documentationSync": {"projectSpecification": True, "changeLog": True, "lifecycleRegistry": True, "releaseRecord": True},
        "rollback": {"version": "1.1.0", "tag": "v1.1.0", "preserved": True}, "releaseBlockers": {"reviewed": True, "open": []},
        "consumerEligible": True, "decision": "approved-stable", "summary": "Synthetic format-only G6 self-test; not Stable approval."
    }


def must_reject(fn: Any, record: dict[str, Any], contract: dict[str, Any], head: str, label: str) -> None:
    try:
        fn(record, contract, head)
    except PromotionError:
        return
    raise PromotionError(f"self-test expected rejection but accepted {label}")


def self_test(contract: dict[str, Any], head: str) -> None:
    rc = sample_rc(head, contract)
    validate_rc(rc, contract, head)
    stale = copy.deepcopy(rc); stale["candidateRevision"] = "0" * 40 if head != "0" * 40 else "1" * 40
    must_reject(validate_rc, stale, contract, head, "stale RC revision")
    missing = copy.deepcopy(rc); missing["evidenceClasses"][0]["status"] = "missing"
    must_reject(validate_rc, missing, contract, head, "RC with missing required evidence")
    blocker = copy.deepcopy(rc); blocker["releaseBlockers"]["open"] = ["synthetic blocker"]
    must_reject(validate_rc, blocker, contract, head, "RC with open blocker")

    stable = sample_stable(head, contract)
    validate_stable(stable, contract, head)
    no_consumer = copy.deepcopy(stable); no_consumer["consumerEligible"] = False
    must_reject(validate_stable, no_consumer, contract, head, "Stable without consumer eligibility")
    bad_run = copy.deepcopy(stable); bad_run["postMergeValidation"][0]["status"] = "failed"
    must_reject(validate_stable, bad_run, contract, head, "Stable with failed post-merge validation")
    bad_digest = copy.deepcopy(stable); bad_digest["releaseArtifacts"][0]["digest"] = "sha256:bad"
    must_reject(validate_stable, bad_digest, contract, head, "Stable with invalid artifact digest")
    stable_blocker = copy.deepcopy(stable); stable_blocker["releaseBlockers"]["open"] = ["synthetic blocker"]
    must_reject(validate_stable, stable_blocker, contract, head, "Stable with open blocker")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rc-record", type=Path)
    parser.add_argument("--stable-record", type=Path)
    parser.add_argument("--expected-revision", help="Exact 40-character revision that a real record must bind")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    contract = source_validation()
    head = head_revision()
    expected = args.expected_revision or head
    req(bool(HEX40.fullmatch(expected)), "--expected-revision must be 40 lowercase hex characters")

    if args.rc_record:
        validate_rc(read_json(args.rc_record.expanduser().resolve(), external=True), contract, expected)
        print(f"Validated G5 RC decision record for exact revision {expected}")
    if args.stable_record:
        validate_stable(read_json(args.stable_record.expanduser().resolve(), external=True), contract, expected)
        print(f"Validated G6 Stable promotion record for exact revision {expected}")
    if args.self_test:
        self_test(contract, head)
        print("G5/G6 release-promotion protocol self-test passed")
        print("Synthetic self-test records are not RC or Stable acceptance evidence")
    if not args.rc_record and not args.stable_record and not args.self_test:
        print("G5/G6 release-promotion source protocol validation passed")

    print("Lifecycle authority unchanged by validation: V1.1 / 1.1.0 Stable; V1.2 Candidate")
    print("A completed record still requires the applicable governed human approval and lifecycle action")


if __name__ == "__main__":
    try:
        main()
    except PromotionError as exc:
        raise SystemExit(f"GLAZE UI V1.2 release-promotion validation failed: {exc}")
