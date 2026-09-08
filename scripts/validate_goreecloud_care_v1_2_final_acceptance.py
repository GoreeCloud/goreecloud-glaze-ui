#!/usr/bin/env python3
"""Validate the GoreeCloud Care GLAZE UI V1.2 final consumer-acceptance protocol.

The protocol is intentionally two-mode and fail-closed:
1. If only the template exists, validate that every human/native dimension remains pending
   and the authoritative consumer registry remains adoption-required.
2. If the final non-template review record exists, require all human/native dimensions to
   pass, require explicit stale-record resolution, and require the registry to transition
   atomically to accepted-v1 for the exact frozen Care RC.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "acceptance/goreecloud-care-v1.2-final-human-native-review.template.json"
FINAL = ROOT / "acceptance/goreecloud-care-v1.2-final-human-native-review.json"
REGISTRY = ROOT / "consumers/registry.json"

EXPECTED_SOURCE = "334b53102c5fe0bd5d348397ba8b13cc5608ada2"
EXPECTED_CARE_TREE = "4d8c243adb456913687045e67df509fb66736c28"
EXPECTED_PACKAGE_SHA = "b1bd308efd7803f6707f0b3ff2f41e56c46c6644094ba5a72d04b0b02bfe7a87"
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


def validate_identity(record: dict) -> None:
    req(record.get("schemaVersion") == 1, "schemaVersion must be 1")
    req(record.get("recordType") == "goreecloud-care-glaze-v1.2-final-human-native-review", "recordType")
    req(record.get("consumer") == "GoreeCloud Care", "consumer identity")
    req(record.get("repository") == "GoreeCloud/goreecloud-zorin-os", "repository identity")
    req(record.get("componentPath") == "apps/goreecloud-care/", "component path")
    req(record.get("glazeTargetVersion") == EXPECTED_GLAZE, "Glaze target version")
    source = record.get("consumerSourceRevision")
    care_tree = record.get("careTree")
    package_sha = record.get("packageSha256")
    req(source == EXPECTED_SOURCE and SHA40.fullmatch(source or "") is not None, "exact Care RC source")
    req(care_tree == EXPECTED_CARE_TREE and SHA40.fullmatch(care_tree or "") is not None, "exact Care tree")
    req(package_sha == EXPECTED_PACKAGE_SHA and SHA256.fullmatch(package_sha or "") is not None, "exact package SHA-256")
    req(record.get("representativeTarget") == "Zorin OS 17.3", "representative target")
    req(record.get("productionEligible") is False, "Glaze must not grant overall production eligibility")
    req(record.get("stableProductPromotionAllowed") is False, "Glaze final consumer acceptance must not self-authorize Care Stable promotion")

    dimensions = record.get("dimensions")
    req(isinstance(dimensions, list), "dimensions must be a list")
    ids = [item.get("id") for item in dimensions if isinstance(item, dict)]
    req(len(ids) == len(EXPECTED_DIMENSIONS), "dimension count")
    req(set(ids) == EXPECTED_DIMENSIONS, "required human/native dimensions")

    governed = record.get("alreadyGovernedEvidence")
    req(isinstance(governed, dict), "alreadyGovernedEvidence")
    policykit = governed.get("policyKitRepresentativeBoundary")
    req(isinstance(policykit, dict), "PolicyKit governed evidence")
    req(policykit.get("status") == "accepted", "PolicyKit governed status")
    req(policykit.get("authority") == "GoreeCloud/goreecloud-wardveil-security", "PolicyKit authority")
    req(policykit.get("revision") == "e16fc489dbf98849601a198358863dffe7df81d4", "PolicyKit Wardveil revision")
    req(policykit.get("repeatRequiredByThisReview") is False, "PolicyKit review must not be redundantly required")
    lifecycle = governed.get("exactCandidatePackageLifecycle")
    req(isinstance(lifecycle, dict) and lifecycle.get("status") == "accepted", "exact package lifecycle governed status")
    req(lifecycle.get("packageSha256") == EXPECTED_PACKAGE_SHA, "exact package lifecycle SHA")
    req(lifecycle.get("repeatRequiredByThisReview") is False, "package lifecycle must not be redundantly required")


def care_registry_entry(registry: dict) -> dict:
    consumers = registry.get("consumers")
    req(isinstance(consumers, list), "consumer registry list")
    matches = [x for x in consumers if isinstance(x, dict) and x.get("name") == "GoreeCloud Care"]
    req(len(matches) == 1, "exactly one GoreeCloud Care registry entry")
    return matches[0]


def validate_pending(template: dict, care: dict) -> None:
    req(template.get("reviewedAt") is None, "template reviewedAt must remain null")
    req(template.get("reviewer") is None and template.get("reviewerRole") is None, "template reviewer fields must remain null")
    req(all(item.get("status") == "pending" and item.get("finding") is None for item in template["dimensions"]), "all template dimensions must remain pending")
    drift = template.get("sourceRecordDriftResolution")
    req(isinstance(drift, dict), "sourceRecordDriftResolution")
    req(drift.get("status") == "pending" and drift.get("resolution") is None, "template stale-record resolution must remain pending")
    req(template.get("decision") == "pending", "template decision must remain pending")
    req(template.get("acceptedV1Authorized") is False, "template cannot authorize accepted-v1")

    req(care.get("status") == "adoption-required", "registry must remain adoption-required before final record")
    req(care.get("requiredTargetVersion") == EXPECTED_GLAZE, "required target version")
    req(care.get("targetVersion") is None, "pending targetVersion must remain null")
    req(care.get("referenceRevision") is None, "pending referenceRevision must remain null")
    req(care.get("evidence") is None, "pending evidence must remain null")
    req(care.get("productionEligible") is False, "registry cannot grant production eligibility")


def parse_timestamp(value: object) -> None:
    req(isinstance(value, str) and value.strip(), "reviewedAt must be a non-empty ISO-8601 timestamp")
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SystemExit("Care V1.2 final-acceptance validation failed: reviewedAt must be ISO-8601") from exc
    req(parsed.tzinfo is not None, "reviewedAt must include a timezone")


def validate_final(record: dict, care: dict) -> None:
    validate_identity(record)
    parse_timestamp(record.get("reviewedAt"))
    req(isinstance(record.get("reviewer"), str) and record["reviewer"].strip(), "reviewer")
    req(isinstance(record.get("reviewerRole"), str) and record["reviewerRole"].strip(), "reviewerRole")
    for item in record["dimensions"]:
        req(item.get("status") == "pass", f"dimension {item.get('id')} must pass")
        req(isinstance(item.get("finding"), str) and item["finding"].strip(), f"dimension {item.get('id')} finding")

    drift = record.get("sourceRecordDriftResolution")
    req(isinstance(drift, dict), "sourceRecordDriftResolution")
    req(drift.get("path") == "apps/goreecloud-care/GLAZE-UI-CONFORMANCE.md", "stale-record path")
    allowed_resolution_states = {"resolved-by-governed-supersession", "source-corrected-and-requalified"}
    req(drift.get("status") in allowed_resolution_states, "stale-record resolution status")
    req(isinstance(drift.get("resolution"), str) and drift["resolution"].strip(), "stale-record resolution explanation")

    req(record.get("decision") == "accepted", "final review decision")
    req(record.get("acceptedV1Authorized") is True, "final record must explicitly authorize accepted-v1")
    req(record.get("productionEligible") is False, "final record cannot grant production eligibility")
    req(record.get("stableProductPromotionAllowed") is False, "final record cannot self-authorize Care Stable")

    req(care.get("status") == "accepted-v1", "registry must transition atomically to accepted-v1")
    req(care.get("requiredTargetVersion") == EXPECTED_GLAZE, "required target version")
    req(care.get("targetVersion") == EXPECTED_GLAZE, "accepted targetVersion")
    req(care.get("referenceRevision") == EXPECTED_SOURCE, "accepted exact Care reference revision")
    req(care.get("evidence") == "acceptance/goreecloud-care-v1.2-final-human-native-review.json", "accepted evidence reference")
    req(care.get("productionEligible") is False, "accepted-v1 cannot grant overall production eligibility")


def main() -> None:
    template = load(TEMPLATE)
    validate_identity(template)
    registry = load(REGISTRY)
    care = care_registry_entry(registry)

    if not FINAL.exists():
        validate_pending(template, care)
        print(
            "GoreeCloud Care V1.2 final acceptance protocol ready: human/native review record absent; "
            "registry correctly remains adoption-required"
        )
        return

    final = load(FINAL)
    validate_final(final, care)
    print(
        "GoreeCloud Care V1.2 final human/native acceptance validated for exact RC; "
        "registry transition to accepted-v1 is exact-revision bound and productionEligible remains false"
    )


if __name__ == "__main__":
    main()
