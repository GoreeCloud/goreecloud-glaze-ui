#!/usr/bin/env python3
"""Fail-closed validation for GoreeCloud Care GLAZE UI V1.2 RC prequalification.

The prequalification record is immutable historical machine evidence. Before a final
human/native acceptance record exists, Care must remain adoption-required. After the
exact final record exists, this validator permits the registry to advance only to the
exact-revision accepted-v1 state while preserving every original prequalification
boundary and keeping production eligibility false.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "acceptance/goreecloud-care-v1.2-final-human-native-review.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_SOURCE = "334b53102c5fe0bd5d348397ba8b13cc5608ada2"
EXPECTED_CARE_TREE = "4d8c243adb456913687045e67df509fb66736c28"
EXPECTED_PACKAGE_SHA = "b1bd308efd7803f6707f0b3ff2f41e56c46c6644094ba5a72d04b0b02bfe7a87"
EXPECTED_TARGET = "1.2.0"
FINAL_EVIDENCE = "acceptance/goreecloud-care-v1.2-final-human-native-review.json"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Care V1.2 prequalification validation failed: {message}")


def load(path: str) -> dict:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    req(isinstance(value, dict), f"{path} must contain an object")
    return value


def main() -> None:
    record = load("acceptance/goreecloud-care-v1.2-rc-prequalification.json")
    registry = load("consumers/registry.json")

    req(record.get("schemaVersion") == 1, "schemaVersion")
    req(record.get("consumer") == "GoreeCloud Care", "consumer identity")
    req(record.get("repository") == "GoreeCloud/goreecloud-zorin-os", "repository identity")
    req(record.get("componentPath") == "apps/goreecloud-care/", "component path")

    glaze = record.get("glazeTarget")
    req(isinstance(glaze, dict), "glazeTarget")
    req(glaze.get("product") == "GLAZE UI V1.2", "Glaze product")
    req(glaze.get("version") == EXPECTED_TARGET, "Glaze version")
    req(glaze.get("upstreamLifecycle") == "stable", "V1.2 must remain Stable upstream")
    req(glaze.get("consumerAcceptanceState") == "prequalified-human-review-pending", "historical prequalification state")

    candidate = record.get("careCandidate")
    req(isinstance(candidate, dict), "careCandidate")
    req(candidate.get("lifecycle") == "release-candidate", "Care lifecycle")
    req(candidate.get("conformance") == "nonconformant", "Care conformance must remain fail-closed")
    source = candidate.get("sourceRevision")
    care_tree = candidate.get("careTree")
    package_sha = candidate.get("packageSha256")
    req(source == EXPECTED_SOURCE and SHA40.fullmatch(source or "") is not None, "exact Care source revision")
    req(care_tree == EXPECTED_CARE_TREE and SHA40.fullmatch(care_tree or "") is not None, "exact Care source tree")
    req(package_sha == EXPECTED_PACKAGE_SHA and SHA256.fullmatch(package_sha or "") is not None, "exact Care package SHA-256")
    req(candidate.get("representativeTarget") == "Zorin OS 17.3", "representative target")

    automated = record.get("automatedEvidence")
    req(isinstance(automated, dict), "automatedEvidence")
    rc_workflow = automated.get("careReleaseCandidateWorkflow")
    req(isinstance(rc_workflow, dict) and rc_workflow.get("runId") == 34169330536, "canonical RC workflow")
    req(rc_workflow.get("testCount") == 144 and rc_workflow.get("conclusion") == "success", "RC workflow test result")
    for key in ("platformContractWorkflow", "themeValidationWorkflow"):
        item = automated.get(key)
        req(isinstance(item, dict) and item.get("conclusion") == "success", f"{key} success")
    checks = automated.get("checks")
    req(isinstance(checks, dict) and checks, "automated checks")
    req(all(value is True for value in checks.values()), "every declared automated check must pass")

    representative = record.get("representativeEvidence")
    req(isinstance(representative, dict), "representativeEvidence")
    for key in (
        "exactCandidatePackageLifecyclePassed",
        "physicalPackageMatchedCiSha256",
        "representativeTargetHandoffGenerated",
        "policyKitBoundaryGovernanceAccepted",
    ):
        req(representative.get(key) is True, f"representative evidence {key}")
    req(representative.get("careCleanupInvokedByAcceptanceRunner") is False, "acceptance runner must remain non-destructive")

    platform = record.get("platformGovernance")
    req(isinstance(platform, dict), "platformGovernance")
    expected_revisions = {
        "everkeep": "d6192dc2a38d5749df561f0638860c974faae8ff",
        "privacyShield": "d2ee2c626beb2ebc2d951d01db877fc8f46d3791",
        "wardveil": "e16fc489dbf98849601a198358863dffe7df81d4",
    }
    for name, revision in expected_revisions.items():
        item = platform.get(name)
        req(isinstance(item, dict) and item.get("accepted") is True, f"{name} acceptance")
        req(item.get("revision") == revision and SHA40.fullmatch(revision) is not None, f"{name} exact revision")
    req(platform["wardveil"].get("crossServiceExecutionAuthority") is False, "Wardveil must not gain cross-service execution authority")

    drift = record.get("sourceRecordDrift")
    req(isinstance(drift, dict) and drift.get("present") is True, "source-record drift must be explicit")
    req(drift.get("path") == "apps/goreecloud-care/GLAZE-UI-CONFORMANCE.md", "drift path")
    req(drift.get("blocksMachinePrequalification") is False, "isolated prose drift machine-prequalification treatment")
    req(drift.get("blocksFinalConsumerAcceptanceWithoutExplicitResolution") is True, "historical stale prose boundary")

    pending = record.get("pendingHumanNativeGates")
    req(isinstance(pending, dict) and pending, "pending human/native gates")
    req(all(value is False for value in pending.values()), "historical prequalification must not fabricate human/native passage")

    decision = record.get("governanceDecision")
    req(isinstance(decision, dict), "governanceDecision")
    req(decision.get("machinePrequalificationPassed") is True, "machine prequalification result")
    req(decision.get("acceptedV1Allowed") is False, "historical prequalification must not itself authorize accepted-v1")
    req(decision.get("registryStatusMustRemain") == "adoption-required", "historical prequalification registry boundary")
    req(decision.get("productionEligible") is False, "prequalification cannot grant product production eligibility")
    req(decision.get("stableProductPromotionAllowed") is False, "prequalification cannot authorize Stable promotion")

    consumers = registry.get("consumers")
    req(isinstance(consumers, list), "consumer registry list")
    care = [item for item in consumers if isinstance(item, dict) and item.get("name") == "GoreeCloud Care"]
    req(len(care) == 1, "exactly one Care registry entry")
    care = care[0]
    req(care.get("requiredTargetVersion") == EXPECTED_TARGET, "Care required target")
    req(care.get("productionEligible") is False, "Care registry cannot grant production eligibility")

    if not FINAL.exists():
        req(care.get("status") == "adoption-required", "Care must remain adoption-required before final review")
        req(care.get("targetVersion") is None and care.get("referenceRevision") is None and care.get("evidence") is None, "unaccepted Care registry fields must remain null")
        req("goreecloud-care-v1.2-rc-prequalification.json" in str(care.get("notes", "")), "Care registry notes must point to prequalification evidence")
        print(
            "GoreeCloud Care V1.2 prequalification validated: exact RC machine evidence passed; "
            "human/native acceptance is not yet present and registry remains adoption-required"
        )
        return

    final = load(FINAL_EVIDENCE)
    req(final.get("consumerSourceRevision") == EXPECTED_SOURCE, "final review exact Care source")
    req(final.get("careTree") == EXPECTED_CARE_TREE, "final review exact Care tree")
    req(final.get("packageSha256") == EXPECTED_PACKAGE_SHA, "final review exact package SHA")
    req(final.get("decision") == "accepted", "final human/native decision")
    req(final.get("acceptedV1Authorized") is True, "final record accepted-v1 authorization")
    req(final.get("productionEligible") is False, "final record cannot grant production eligibility")
    req(final.get("stableProductPromotionAllowed") is False, "final record cannot authorize Stable")

    req(care.get("status") == "accepted-v1", "Care registry must be accepted-v1 when final review exists")
    req(care.get("targetVersion") == EXPECTED_TARGET, "accepted Care target version")
    req(care.get("referenceRevision") == EXPECTED_SOURCE, "accepted Care exact reference revision")
    req(care.get("evidence") == FINAL_EVIDENCE, "accepted Care evidence reference")

    print(
        "GoreeCloud Care V1.2 prequalification preserved as historical machine evidence; "
        "exact final human/native acceptance exists and registry is validly advanced to accepted-v1"
    )


if __name__ == "__main__":
    main()
