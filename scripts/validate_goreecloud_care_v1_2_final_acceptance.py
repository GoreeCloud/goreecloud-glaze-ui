#!/usr/bin/env python3
"""Validate the GoreeCloud Care GLAZE UI V1.2 final acceptance lineage.

The original seven-dimensional human/native review remains exact to the frozen RC.
When the exact-source bridge exists, the registry may move its accepted-v1 reference to
Care 0.1.0 only if the bridge retains the accepted predecessor review, proves the
bounded non-material Glaze delta, and keeps production/stable authority fail-closed.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "acceptance/goreecloud-care-v1.2-final-human-native-review.template.json"
FINAL = ROOT / "acceptance/goreecloud-care-v1.2-final-human-native-review.json"
BRIDGE = ROOT / "acceptance/goreecloud-care-v1.2-0.1.0-exact-source-bridge.json"
REGISTRY = ROOT / "consumers/registry.json"

RC_SOURCE = "334b53102c5fe0bd5d348397ba8b13cc5608ada2"
RC_TREE = "4d8c243adb456913687045e67df509fb66736c28"
RC_PACKAGE = "b1bd308efd7803f6707f0b3ff2f41e56c46c6644094ba5a72d04b0b02bfe7a87"
FINAL_SOURCE = "bbc4779454c2887b810aa0ddc9e8a686a4c68ebd"
FINAL_TREE = "ebe028347c978b6d09fb1d2af011729249f63bc3"
FINAL_PACKAGE = "819cff6e0132bf6b09df0986682995c25b14c39e74982f725efd0b5a21b71160"
EXPECTED_GLAZE = "1.2.0"
EXPECTED_DIMENSIONS = {
    "orca-scan-completion-announcement-quality",
    "orca-cancellation-failure-success-announcement-quality",
    "orca-maintenance-insights-status-quality",
    "native-window-controls-and-compositor-optical-quality",
    "dark-and-preview-deep-dark-physical-optical-quality",
    "canonical-care-icon-physical-rendering-quality",
    "confirmation-empty-failure-success-and-applicable-controlled-task-ux",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Care V1.2 final-acceptance validation failed: {message}")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    req(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def care_registry_entry(registry: dict) -> dict:
    consumers = registry.get("consumers")
    req(isinstance(consumers, list), "consumer registry list")
    matches = [x for x in consumers if isinstance(x, dict) and x.get("name") == "GoreeCloud Care"]
    req(len(matches) == 1, "exactly one GoreeCloud Care registry entry")
    return matches[0]


def parse_timestamp(value: object) -> None:
    req(isinstance(value, str) and value.strip(), "reviewedAt must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit("Care V1.2 final-acceptance validation failed: reviewedAt must be ISO-8601") from exc
    req(parsed.tzinfo is not None, "reviewedAt must include a timezone")


def validate_human_record(record: dict) -> None:
    req(record.get("schemaVersion") == 1, "human review schema")
    req(record.get("recordType") == "goreecloud-care-glaze-v1.2-final-human-native-review", "human review record type")
    req(record.get("consumer") == "GoreeCloud Care", "consumer identity")
    req(record.get("repository") == "GoreeCloud/goreecloud-zorin-os", "repository identity")
    req(record.get("componentPath") == "apps/goreecloud-care/", "component path")
    req(record.get("glazeTargetVersion") == EXPECTED_GLAZE, "Glaze target version")
    req(record.get("consumerSourceRevision") == RC_SOURCE and SHA40.fullmatch(RC_SOURCE), "historical exact Care RC source")
    req(record.get("careTree") == RC_TREE and SHA40.fullmatch(RC_TREE), "historical exact Care tree")
    req(record.get("packageSha256") == RC_PACKAGE and SHA256.fullmatch(RC_PACKAGE), "historical exact package SHA-256")
    req(record.get("representativeTarget") == "Zorin OS 17.3", "representative target")
    req(record.get("productionEligible") is False, "Glaze must not grant overall production eligibility")
    req(record.get("stableProductPromotionAllowed") is False, "human review must not self-authorize Care Stable")

    dimensions = record.get("dimensions")
    req(isinstance(dimensions, list), "dimensions must be a list")
    ids = [item.get("id") for item in dimensions if isinstance(item, dict)]
    req(len(ids) == len(EXPECTED_DIMENSIONS), "dimension count")
    req(set(ids) == EXPECTED_DIMENSIONS, "required human/native dimensions")


def validate_pending(template: dict, care: dict) -> None:
    req(template.get("reviewedAt") is None, "template reviewedAt must remain null")
    req(all(item.get("status") == "pending" and item.get("finding") is None for item in template["dimensions"]), "all template dimensions must remain pending")
    req(template.get("decision") == "pending", "template decision must remain pending")
    req(template.get("acceptedV1Authorized") is False, "template cannot authorize accepted-v1")
    req(care.get("status") == "adoption-required", "registry must remain adoption-required before final record")
    req(care.get("targetVersion") is None and care.get("referenceRevision") is None and care.get("evidence") is None, "pending registry fields must remain null")
    req(care.get("productionEligible") is False, "registry cannot grant production eligibility")


def validate_final_human(record: dict) -> None:
    validate_human_record(record)
    parse_timestamp(record.get("reviewedAt"))
    req(isinstance(record.get("reviewer"), str) and record["reviewer"].strip(), "reviewer")
    req(isinstance(record.get("reviewerRole"), str) and record["reviewerRole"].strip(), "reviewerRole")
    for item in record["dimensions"]:
        req(item.get("status") == "pass", f"dimension {item.get('id')} must pass")
        req(isinstance(item.get("finding"), str) and item["finding"].strip(), f"dimension {item.get('id')} finding")
    req(record.get("decision") == "accepted", "final review decision")
    req(record.get("acceptedV1Authorized") is True, "final record must explicitly authorize accepted-v1")


def validate_bridge(bridge: dict, care: dict) -> None:
    req(bridge.get("schemaVersion") == 1, "bridge schema")
    req(bridge.get("recordType") == "goreecloud-care-glaze-v1.2-exact-source-bridge", "bridge record type")
    req(bridge.get("consumerSourceRevision") == FINAL_SOURCE and SHA40.fullmatch(FINAL_SOURCE), "bridge exact source")
    req(bridge.get("careTree") == FINAL_TREE and SHA40.fullmatch(FINAL_TREE), "bridge exact tree")
    req(bridge.get("packageSha256") == FINAL_PACKAGE and SHA256.fullmatch(FINAL_PACKAGE), "bridge exact package")
    req(bridge.get("glazeTargetVersion") == EXPECTED_GLAZE, "bridge Glaze target")
    req(bridge.get("decision") == "accepted-by-exact-source-bridge", "bridge decision")
    req(bridge.get("acceptedV1Authorized") is True, "bridge accepted-v1 authorization")
    req(bridge.get("productionEligible") is False, "bridge cannot grant production eligibility")
    req(bridge.get("stableProductPromotionAllowed") is False, "bridge cannot self-authorize Care Stable")

    predecessor = bridge.get("predecessorAcceptance") or {}
    req(predecessor.get("record") == "acceptance/goreecloud-care-v1.2-final-human-native-review.json", "bridge predecessor record")
    req(predecessor.get("sourceRevision") == RC_SOURCE, "bridge predecessor source")
    req(predecessor.get("careTree") == RC_TREE, "bridge predecessor tree")
    req(predecessor.get("packageSha256") == RC_PACKAGE, "bridge predecessor package")
    req(predecessor.get("allRequiredDimensionsPassed") is True, "bridge predecessor acceptance")

    delta = bridge.get("sourceDelta") or {}
    req(delta.get("compareBase") == RC_SOURCE and delta.get("compareHead") == FINAL_SOURCE, "bridge compare identity")
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
        req(delta.get(key) is False, f"non-material bridge violated by {key}")
    req(delta.get("lifecycleCopyChanged") is True, "lifecycle copy delta must stay explicit")

    representative = bridge.get("representativeExactCandidateEvidence") or {}
    req(representative.get("physicalTargetAcceptance") == "passed", "exact candidate physical acceptance")
    req(representative.get("physicalPackageMatchedCi") is True, "physical package identity")
    req(representative.get("packageLifecyclePassed") is True, "exact package lifecycle")
    req(representative.get("installedValidationPassed") is True, "installed validation")
    req(representative.get("realDesktopPolicyKitSuitePassed") is True, "current GUI PolicyKit exercise")
    req(representative.get("continuityState") == "ready", "current continuity state")

    rationale = bridge.get("bridgeRationale") or {}
    req(rationale.get("priorHumanNativeReviewTransferredByGovernance") is True, "bridge transfer authorization")
    req(rationale.get("transferLimitedToUnchangedGlazeBehavior") is True, "bridge transfer scope")
    req(rationale.get("newHumanFindingsFabricated") is False, "bridge must not fabricate new human findings")

    req(care.get("status") == "accepted-v1", "registry accepted-v1 state")
    req(care.get("requiredTargetVersion") == EXPECTED_GLAZE, "required target version")
    req(care.get("targetVersion") == EXPECTED_GLAZE, "accepted targetVersion")
    req(care.get("referenceRevision") == FINAL_SOURCE, "accepted exact Care 0.1.0 reference revision")
    req(care.get("evidence") == "acceptance/goreecloud-care-v1.2-0.1.0-exact-source-bridge.json", "bridge evidence reference")
    req(care.get("productionEligible") is False, "accepted-v1 cannot grant overall production eligibility")


def main() -> None:
    template = load(TEMPLATE)
    validate_human_record(template)
    registry = load(REGISTRY)
    care = care_registry_entry(registry)

    if not FINAL.exists():
        validate_pending(template, care)
        print("GoreeCloud Care V1.2 final acceptance protocol ready; registry remains adoption-required")
        return

    final = load(FINAL)
    validate_final_human(final)

    if BRIDGE.exists():
        validate_bridge(load(BRIDGE), care)
        print(
            "GoreeCloud Care V1.2 human/native acceptance lineage validated: frozen RC review remains exact, "
            "and exact Care 0.1.0 is validly bridged to accepted-v1 without fabricating a new human review."
        )
        return

    req(care.get("status") == "accepted-v1", "registry must be accepted-v1")
    req(care.get("referenceRevision") == RC_SOURCE, "accepted exact Care RC reference revision")
    req(care.get("evidence") == "acceptance/goreecloud-care-v1.2-final-human-native-review.json", "accepted RC evidence reference")
    req(care.get("productionEligible") is False, "accepted-v1 cannot grant overall production eligibility")
    print("GoreeCloud Care V1.2 final human/native acceptance validated for exact frozen RC")


if __name__ == "__main__":
    main()
