#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Human Reachability implementation workstream."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
CURRENT_STABLE_VERSION = "1.3.0"
SOURCE_STABLE_VERSION = "1.2.0"
CONTRACT = "contracts/v1.3/reachability.candidate.json"
RUNTIME = "js/glaze-v1.3-reachability.candidate.mjs"
TESTS = "tests/glaze-v1.3-reachability.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (
        CONTRACT,
        RUNTIME,
        TESTS,
        PLAN,
        "contracts/v1.2/ergonomic-layout.candidate.json",
        "VERSION",
        "registry/lifecycle.json",
    ):
        req((ROOT / path).is_file(), f"missing reachability artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Human Reachability validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == CURRENT_STABLE_VERSION, "VERSION must remain 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == CURRENT_STABLE_VERSION, "currentStable must remain 1.3.0")
    req(lifecycle.get("currentOfficial") == CURRENT_STABLE_VERSION, "currentOfficial must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "Reachability work must not activate release lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    architecture = workstreams.get("contract-and-token-architecture", {})
    reachability = workstreams.get("human-reachability", {})
    req(architecture.get("status") == "implemented-and-validated", "Reachability requires validated architecture dependency")
    req(
        reachability.get("status") in {
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "Reachability workstream must be active in the plan",
    )
    req(reachability.get("dependsOn") == ["contract-and-token-architecture"], "Reachability dependency set mismatch")

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "reachability product identity mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "reachability target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "reachability must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "reachability artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "reachability contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "reachability must not be consumer eligible")
    req(contract.get("sourceStable") == SOURCE_STABLE_VERSION, "reachability must preserve the V1.2 source baseline")
    req(contract.get("extends") == "contracts/v1.2/ergonomic-layout.candidate.json", "reachability must extend V1.2 ergonomic authority")

    zones = contract.get("zones", {})
    req(set(zones) == {"viewing", "transition", "interaction"}, "reachability must define exactly Viewing, Transition, and Interaction zones")
    req(zones.get("viewing", {}).get("frequentControlsPreferred") is False, "Viewing Zone must not prefer frequent controls")
    req(zones.get("interaction", {}).get("frequentControlsPreferred") is True, "Interaction Zone must prefer frequent controls")
    required_interaction = {"navigation", "primary-action", "frequent-tools", "media-controls", "contextual-toolbars", "safe-confirmation", "search-initiation"}
    req(required_interaction.issubset(set(zones.get("interaction", {}).get("semanticPurpose", []))), "Interaction Zone semantic priorities are incomplete")

    bands = contract.get("defaultCompactReviewBands", {})
    req(bands.get("status") == "provisional-implementation-default-not-anthropometric-authority", "default bands must remain explicitly provisional")
    req(bands.get("coordinateSystem") == "normalized-content-height-after-platform-safe-area-insets", "reachability coordinate system mismatch")
    req(bands.get("overlapIsIntentional") is True, "review zones should retain intentional overlap")
    req(bands.get("overrideAuthority") == "platform-product-or-physical-reachability-evidence", "evidence must be able to override provisional bands")
    for name in ("viewing", "transition", "interaction"):
        band = bands.get(name, {})
        start = band.get("start")
        end = band.get("end")
        req(isinstance(start, (int, float)) and isinstance(end, (int, float)), f"{name} band must be numeric")
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            req(0 <= start <= end <= 1, f"{name} band must fit normalized 0..1 coordinate space")

    v12 = load("contracts/v1.2/ergonomic-layout.candidate.json")
    floors = contract.get("inheritedTargetFloors", {})
    req(floors.get("touchTargetPx") == v12.get("requirements", {}).get("touchTargetPx") == 48, "touch target floor must inherit 48px")
    req(floors.get("touchAssistanceTargetPx") == v12.get("requirements", {}).get("touchAssistanceTargetPx") == 56, "touch-assistance target floor must inherit 56px")

    required_signals = {
        "frequentActionTooHigh",
        "primaryActionOutsideInteractionZone",
        "tinyEdgeTarget",
        "excessiveHandTravel",
        "safeAreaObstruction",
        "searchInitiationOutsideReach",
        "navigationOutsideReach",
    }
    signals = contract.get("developmentSignals", {})
    req(required_signals == {key for key, value in signals.items() if value is True}, "development reachability signal set mismatch")

    score = contract.get("scoreModel", {})
    req(score.get("purpose") == "prioritized-design-review-signal", "reachability score purpose mismatch")
    req(score.get("autonomousProductAuthority") is False, "reachability score must not be autonomous product authority")
    req(score.get("releaseGateByItself") is False, "reachability score alone must not become a release gate")
    req(score.get("physicalReachabilityEvidence") is False, "reachability score must not masquerade as physical evidence")
    req(score.get("range") == {"min": 0, "max": 100}, "reachability score range mismatch")
    req(score.get("startingScore") == 100, "reachability starting score mismatch")

    rules = contract.get("rules", {})
    for key in (
        "compactLayoutMustEvaluateReachability",
        "frequentActionsShouldPreferInteractionZone",
        "safeAreaObstructionMustBeReported",
        "targetFloorsMustNotShrinkToImproveScore",
        "scoreMayNotOverridePlatformAccessibilityOrProductSemantics",
        "scoreMayNotAutonomouslyMoveControls",
        "scoreMayNotEstablishPhysicalDeviceAcceptance",
        "rtlAndOrientationMustRemainInputs",
        "platformAdapterMayOverrideProvisionalBandsWithEvidence",
    ):
        req(rules.get(key) is True, f"reachability rule must be true: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket("):
        req(forbidden not in runtime, f"reachability reviewer must remain local-only; forbidden network primitive found: {forbidden}")
    for symbol in (
        "classifyReachabilityZone",
        "deriveNormalizedActionPosition",
        "reviewReachabilityAction",
        "scoreCompactReachability",
        "createReachabilityReviewer",
        "reachabilityCandidate",
    ):
        req(symbol in runtime, f"reachability runtime missing required API: {symbol}")

    evidence = contract.get("evidenceBoundary", {})
    not_established = set(evidence.get("notEstablished", []))
    for item in (
        "anthropometric-device-lab-acceptance",
        "physical-device-reachability-acceptance",
        "platform-specific-zone-calibration",
        "release-candidate",
        "stable",
        "consumer-conformance",
    ):
        req(item in not_established, f"reachability evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Human Reachability validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Human Reachability: PASS")
    print("Boundary: V1.3.0 remains current Stable; compact zones and development review scoring preserve their V1.2 source baseline without anthropometric, physical-device, V1.3.1, or consumer-conformance claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
