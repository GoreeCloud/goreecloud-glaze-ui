#!/usr/bin/env python3
"""Fail-closed validation for GoreeCloud Care GLAZE UI V1.2 acceptance lineage.

The frozen RC machine prequalification and seven-dimensional human/native review remain
immutable predecessor evidence. Exact Care 0.1.0 may be accepted-v1 only through the
explicit bridge record, which must prove a bounded non-material Glaze source delta and
must remain exact-source/package bound. The bridge does not grant generic product
production eligibility or Stable lifecycle authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

RC_SOURCE = "334b53102c5fe0bd5d348397ba8b13cc5608ada2"
RC_TREE = "4d8c243adb456913687045e67df509fb66736c28"
RC_PACKAGE = "b1bd308efd7803f6707f0b3ff2f41e56c46c6644094ba5a72d04b0b02bfe7a87"
FINAL_SOURCE = "bbc4779454c2887b810aa0ddc9e8a686a4c68ebd"
FINAL_TREE = "ebe028347c978b6d09fb1d2af011729249f63bc3"
FINAL_PACKAGE = "819cff6e0132bf6b09df0986682995c25b14c39e74982f725efd0b5a21b71160"
TARGET = "1.2.0"
HUMAN_REVIEW = "acceptance/goreecloud-care-v1.2-final-human-native-review.json"
BRIDGE_PATH = "acceptance/goreecloud-care-v1.2-0.1.0-exact-source-bridge.json"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Care V1.2 acceptance validation failed: {message}")


def load(path: str) -> dict:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    req(isinstance(value, dict), f"{path} must contain an object")
    return value


def main() -> None:
    prequal = load("acceptance/goreecloud-care-v1.2-rc-prequalification.json")
    human = load(HUMAN_REVIEW)
    bridge = load(BRIDGE_PATH)
    registry = load("consumers/registry.json")

    # Preserve the frozen RC lineage exactly; bridge evidence may not rewrite it.
    candidate = prequal.get("careCandidate") or {}
    req(candidate.get("sourceRevision") == RC_SOURCE, "historical RC source changed")
    req(candidate.get("careTree") == RC_TREE, "historical RC tree changed")
    req(candidate.get("packageSha256") == RC_PACKAGE, "historical RC package changed")
    req(candidate.get("lifecycle") == "release-candidate", "historical RC lifecycle changed")
    req(candidate.get("conformance") == "nonconformant", "historical RC conformance changed")

    req(human.get("schemaVersion") == 1, "historical human review schema")
    req(human.get("consumerSourceRevision") == RC_SOURCE, "historical human review source")
    req(human.get("careTree") == RC_TREE, "historical human review tree")
    req(human.get("packageSha256") == RC_PACKAGE, "historical human review package")
    req(human.get("glazeTargetVersion") == TARGET, "historical human review target")
    req(human.get("decision") == "accepted", "historical human review decision")
    req(human.get("acceptedV1Authorized") is True, "historical accepted-v1 authorization")
    req(human.get("productionEligible") is False, "historical review must not grant production eligibility")
    req(human.get("stableProductPromotionAllowed") is False, "historical review must not authorize Stable")
    dimensions = human.get("dimensions") or []
    req(len(dimensions) == 7, "seven historical human/native dimensions required")
    req(all(item.get("status") == "pass" for item in dimensions if isinstance(item, dict)), "all historical human/native dimensions must remain passed")

    # Validate the exact 0.1.0 bridge and its non-material Glaze-delta claim.
    req(bridge.get("schemaVersion") == 1, "bridge schema")
    req(bridge.get("recordType") == "goreecloud-care-glaze-v1.2-exact-source-bridge", "bridge record type")
    req(bridge.get("consumer") == "GoreeCloud Care", "bridge consumer")
    req(bridge.get("repository") == "GoreeCloud/goreecloud-zorin-os", "bridge repository")
    req(bridge.get("componentPath") == "apps/goreecloud-care/", "bridge component")
    req(bridge.get("glazeTargetVersion") == TARGET, "bridge target")
    req(bridge.get("consumerSourceRevision") == FINAL_SOURCE and SHA40.fullmatch(FINAL_SOURCE), "bridge exact source")
    req(bridge.get("careTree") == FINAL_TREE and SHA40.fullmatch(FINAL_TREE), "bridge exact tree")
    req(bridge.get("packageSha256") == FINAL_PACKAGE and SHA256.fullmatch(FINAL_PACKAGE), "bridge exact package")
    req(bridge.get("representativeTarget") == "Zorin OS 17.3", "bridge representative target")
    req(bridge.get("decision") == "accepted-by-exact-source-bridge", "bridge decision")
    req(bridge.get("acceptedV1Authorized") is True, "bridge accepted-v1 authorization")
    req(bridge.get("productionEligible") is False, "bridge must not grant generic production eligibility")
    req(bridge.get("stableProductPromotionAllowed") is False, "bridge must not independently authorize Stable")

    predecessor = bridge.get("predecessorAcceptance") or {}
    req(predecessor.get("record") == HUMAN_REVIEW, "bridge predecessor record")
    req(predecessor.get("sourceRevision") == RC_SOURCE, "bridge predecessor source")
    req(predecessor.get("careTree") == RC_TREE, "bridge predecessor tree")
    req(predecessor.get("packageSha256") == RC_PACKAGE, "bridge predecessor package")
    req(predecessor.get("decision") == "accepted", "bridge predecessor decision")
    req(predecessor.get("requiredHumanNativeDimensions") == 7, "bridge predecessor dimension count")
    req(predecessor.get("allRequiredDimensionsPassed") is True, "bridge predecessor review must be fully passed")

    delta = bridge.get("sourceDelta") or {}
    req(delta.get("compareBase") == RC_SOURCE, "bridge compare base")
    req(delta.get("compareHead") == FINAL_SOURCE, "bridge compare head")
    req(delta.get("commits") == 23, "bridge compare commit count")
    for key in (
        "glazeImplementationFilesChanged",
        "canonicalIconChanged",
        "uiContractChanged",
        "focusResilienceChanged",
        "accessibilityIdentityChanged",
        "glazeV12ContractTestsChanged",
        "glazeV13PreviewContractTestsChanged",
        "runtimeUiAcceptanceHarnessChanged",
    ):
        req(delta.get(key) is False, f"bridge cannot transfer acceptance when {key} is true")
    req(delta.get("lifecycleCopyChanged") is True, "lifecycle-copy delta must stay explicit")
    req(delta.get("desktopAndAppStreamLifecycleIdentityChanged") is True, "desktop/AppStream lifecycle identity delta must stay explicit")

    automation = bridge.get("exactCandidateAutomation") or {}
    req(automation.get("careQualificationRunId") == 34180765807, "exact Care qualification run")
    req(automation.get("careQualificationRunNumber") == 421, "exact Care qualification run number")
    req(automation.get("careTestCount", 0) >= 143, "143-test exact candidate checkpoint")
    req(automation.get("platformContractRunId") == 34180766156, "exact Platform Contract run")
    req(automation.get("themeValidationRunId") == 34180765817, "exact theme validation run")
    req(automation.get("themeValidationRunNumber") == 590, "exact theme validation run number")
    req(automation.get("packageArtifactId") == 10038827656, "exact package artifact")
    req(automation.get("crossEnvironmentArtifactId") == 10038821545, "exact cross-environment artifact")
    req(automation.get("packageSha256") == FINAL_PACKAGE, "automation package identity")
    req(automation.get("result") == "passed", "exact automation result")

    representative = bridge.get("representativeExactCandidateEvidence") or {}
    req(representative.get("physicalTargetAcceptance") == "passed", "physical exact-candidate acceptance")
    for key in (
        "physicalPackageMatchedCi",
        "packageLifecyclePassed",
        "installedValidationPassed",
        "realDesktopPolicyKitSuitePassed",
    ):
        req(representative.get(key) is True, f"representative exact-candidate evidence: {key}")
    req(representative.get("localTestCount", 0) >= 143, "representative exact-candidate test count")
    req(representative.get("continuityState") == "ready", "representative continuity state")
    req(representative.get("continuityStage") == "everkeep-promoted", "representative continuity stage")

    rationale = bridge.get("bridgeRationale") or {}
    req(rationale.get("priorHumanNativeReviewTransferredByGovernance") is True, "bridge transfer must be explicit")
    req(rationale.get("transferLimitedToUnchangedGlazeBehavior") is True, "bridge transfer scope must be bounded")
    req(rationale.get("newHumanFindingsFabricated") is False, "bridge must not fabricate a second human review")

    consumers = registry.get("consumers")
    req(isinstance(consumers, list), "consumer registry list")
    care = [item for item in consumers if isinstance(item, dict) and item.get("name") == "GoreeCloud Care"]
    req(len(care) == 1, "exactly one Care registry entry")
    care = care[0]
    req(registry.get("officialBaseline") == TARGET, "V1.2 must remain official baseline while this bridge is active")
    req(registry.get("requiredConsumerVersion") == TARGET, "V1.2 must remain required consumer version")
    req(care.get("status") == "accepted-v1", "Care registry status")
    req(care.get("targetVersion") == TARGET, "Care registry target")
    req(care.get("requiredTargetVersion") == TARGET, "Care required target")
    req(care.get("referenceRevision") == FINAL_SOURCE, "Care exact registry revision")
    req(care.get("evidence") == BRIDGE_PATH, "Care exact registry evidence")
    req(care.get("productionEligible") is False, "Care registry must not independently grant overall product eligibility")

    print(
        "GoreeCloud Care V1.2 acceptance lineage validated: frozen RC human/native acceptance is preserved, "
        "exact Care 0.1.0 is explicitly bridged for unchanged Glaze behavior, and the registry is exact-source accepted-v1."
    )


if __name__ == "__main__":
    main()
