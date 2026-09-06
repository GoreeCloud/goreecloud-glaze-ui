#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Adaptive Navigation workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.2.0"
CONTRACT = "contracts/v1.3/adaptive-navigation.candidate.json"
RUNTIME = "js/glaze-v1.3-adaptive-navigation.candidate.mjs"
TESTS = "tests/glaze-v1.3-adaptive-navigation.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
REACHABILITY = "contracts/v1.3/reachability.candidate.json"
V12_ADAPTIVE = "contracts/v1.2/adaptive-navigation.candidate.json"
V12_SHELL = "contracts/v1.2/system-shell-navigation.candidate.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (CONTRACT, RUNTIME, TESTS, PLAN, REACHABILITY, V12_ADAPTIVE, V12_SHELL, "VERSION", "registry/lifecycle.json"):
        req((ROOT / path).is_file(), f"missing adaptive-navigation artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Adaptive Navigation validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must remain 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "Adaptive Navigation must not activate release lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("human-reachability", {}).get("status") == "implemented-and-validated", "Adaptive Navigation requires validated Human Reachability")
    req(
        workstreams.get("adaptive-navigation", {}).get("status") in {
            "planned",
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "Adaptive Navigation workstream must use governed status vocabulary",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "navigation product identity mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "navigation target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "navigation release lifecycle must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "navigation artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "navigation contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "navigation contract must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "navigation must extend V1.2 Stable")
    req(set(contract.get("extends", [])) == {V12_ADAPTIVE, V12_SHELL, REACHABILITY}, "navigation inheritance set mismatch")

    principles = contract.get("principles", {})
    for key in (
        "destinationsRemainStable",
        "presentationMayTransform",
        "currentLocationMustPersist",
        "destinationOrderMustPersist",
        "platformAdapterOwnsEnvironmentSelection",
        "reachabilityAffectsPlacementNotMeaning",
        "accessibilityMayForceInFlowPresentation",
    ):
        req(principles.get(key) is True, f"adaptive-navigation principle must be true: {key}")
    req(principles.get("predictionMayReorderPrimaryDestinations") is False, "prediction must not reorder primary destinations")
    req(principles.get("viewportWidthAloneIsCompositionAuthority") is False, "raw viewport width must not be composition authority")

    expected_environments = {"compact", "medium", "expanded", "workspace", "farView", "wearable"}
    environments = contract.get("environments", {})
    req(set(environments) == expected_environments, "adaptive-navigation environment set mismatch")
    req(environments.get("compact", {}).get("defaultPresentation") == "navigation-capsule", "compact default must be navigation capsule")
    req(environments.get("compact", {}).get("placement") == "lower-reachable-region", "compact navigation must prefer lower reachable region")
    req(environments.get("compact", {}).get("primaryDestinationMaximum") == 5, "compact primary destination maximum must remain five")
    req(environments.get("medium", {}).get("defaultPresentation") == "navigation-rail", "medium default must be navigation rail")
    req(environments.get("expanded", {}).get("defaultPresentation") == "persistent-sidebar", "expanded default must be persistent sidebar")
    req(environments.get("workspace", {}).get("defaultPresentation") == "persistent-sidebar-plus-toolbar", "workspace default mismatch")
    req(environments.get("farView", {}).get("defaultPresentation") == "directional-focus-navigation", "far-view default mismatch")
    req(environments.get("farView", {}).get("directionalFocusRequired") is True, "far-view must require directional focus")
    req(environments.get("wearable", {}).get("defaultPresentation") == "shallow-list", "wearable default mismatch")
    for name, entry in environments.items():
        req(isinstance(entry.get("minimumTargetPx"), (int, float)) and entry.get("minimumTargetPx") >= 48, f"{name} navigation target floor must be at least 48px")

    compact = contract.get("compactCapsule", {})
    req(compact.get("lowerReachabilityPreferred") is True, "compact capsule must prefer lower reachability")
    req(compact.get("frequentNavigationMustIntersectInteractionZone") is True, "compact navigation must intersect the interaction zone")
    req(compact.get("labelsMayCollapseWithoutShrinkingTargets") is True, "collapsed labels may not shrink targets")
    req(compact.get("currentDestinationRequiresStructuralCue") is True, "current destination requires a structural cue")
    req(compact.get("currentDestinationMayDependOnColorAlone") is False, "current destination must not depend on color alone")
    forced = set(compact.get("forcedInFlowConditions", []))
    for item in ("large-text-or-reflow", "touch-assistance", "safe-area-obstruction", "keyboard-occlusion", "visible-content-occlusion"):
        req(item in forced, f"compact navigation forced-in-flow condition missing: {item}")

    selector = contract.get("environmentSelection", {})
    req(selector.get("rawViewportWidthInputRequired") is False, "raw viewport width must not be required")
    req(selector.get("numericBreakpointsCanonical") is False, "numeric breakpoints must not be canonical")
    req(selector.get("deviceBrandBreakpointsCanonical") is False, "device-brand breakpoints must not be canonical")
    req(selector.get("unknownEnvironmentFallback") == "compact", "unknown environment fallback must be compact")
    req(selector.get("environmentChangeMayReorderDestinations") is False, "environment changes may not reorder destinations")
    req(selector.get("environmentChangeMayChangeDestinationIdentity") is False, "environment changes may not change destination identity")

    continuity = contract.get("continuity", {})
    preserved = set(continuity.get("preserve", []))
    for item in ("current-destination", "destination-order", "selection", "filters", "drafts", "logical-back-history"):
        req(item in preserved, f"navigation continuity must preserve {item}")
    req(continuity.get("presentationTransformationMayResetTaskState") is False, "presentation transformation may not reset task state")
    req(continuity.get("currentDestinationMustExistInDestinationModel") is True, "current destination must exist in semantic model")
    req(continuity.get("predictionMayInventDestination") is False, "prediction may not invent destinations")

    accessibility = contract.get("accessibility", {})
    req(accessibility.get("minimumInteractiveTargetPx") >= 48, "navigation minimum target must be at least 48px")
    req(accessibility.get("touchAssistanceTargetPx") >= 56, "touch assistance target must be at least 56px")
    req(accessibility.get("farViewMinimumInteractiveTargetPx") >= 56, "far-view target must be at least 56px")
    req(accessibility.get("forcedColorsRequiresStructuralCurrentCue") is True, "Forced Colors must preserve structural current-location cue")
    req(accessibility.get("reducedTransparencyMayUseSolidNavigationSurface") is True, "Reduced Transparency must allow solid navigation fallback")
    req(accessibility.get("reducedMotionMayUseImmediatePresentationChange") is True, "Reduced Motion must allow immediate navigation transform")
    req(accessibility.get("rtlLogicalOrderRequired") is True, "RTL logical order must be required")
    req(accessibility.get("targetSizeMayShrinkToPreserveDetachedCapsule") is False, "target size may not shrink to preserve detached capsule")
    precedence = accessibility.get("precedence", [])
    req(precedence[:3] == ["platform-accessibility", "large-text-and-reflow", "safe-area-and-occlusion"], "navigation accessibility precedence mismatch")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "innerWidth", "matchMedia("):
        req(forbidden not in runtime, f"navigation runtime must not use forbidden viewport/network authority: {forbidden}")
    for symbol in ("resolveNavigationPresentation", "transformNavigationModel", "applyNavigationPresentation", "adaptiveNavigationCandidate"):
        req(symbol in runtime, f"navigation runtime missing required API: {symbol}")
    for presentation in ("navigation-capsule", "navigation-rail", "persistent-sidebar", "persistent-sidebar-plus-toolbar", "directional-focus-navigation", "shallow-list"):
        req(presentation in runtime, f"navigation runtime missing governed presentation: {presentation}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in (
        "platform-specific-environment-threshold-calibration",
        "human-navigation-acceptance",
        "assistive-technology-human-acceptance",
        "physical-device-navigation-acceptance",
        "foldable-posture-physical-acceptance",
        "far-view-physical-distance-acceptance",
        "wearable-production-support",
        "release-candidate",
        "stable",
        "consumer-conformance",
    ):
        req(item in not_established, f"navigation evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Adaptive Navigation validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Adaptive Navigation: PASS")
    print("Boundary: stable semantic destinations and environment-aware reachable navigation presentation are implemented without platform-threshold, human, physical-device, lifecycle, or consumer acceptance claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
