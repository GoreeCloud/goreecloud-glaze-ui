#!/usr/bin/env python3
"""Validate the preserved GLAZE UI V1.3 Multi-Pane/Foldable/Desktop workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.2.0"  # Historical V1.3 source baseline.
V13_VERSION = "1.3.0"
CONTRACT = "contracts/v1.3/multi-pane.candidate.json"
TOKENS = "tokens/glaze-v1.3-layout.candidate.json"
RUNTIME = "js/glaze-v1.3-multi-pane.candidate.mjs"
TESTS = "tests/glaze-v1.3-multi-pane.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
V12_FOLDABLE = "contracts/v1.2/foldable-adaptation.candidate.json"
V12_RESPONSIVE = "contracts/v1.2/responsive-adaptation-reference.candidate.json"
REACHABILITY = "contracts/v1.3/reachability.candidate.json"
NAVIGATION = "contracts/v1.3/adaptive-navigation.candidate.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(value: str) -> tuple[int, int, int] | None:
    try:
        parts = value.split(".")
        if len(parts) != 3:
            return None
        return tuple(int(part) for part in parts)  # type: ignore[return-value]
    except (AttributeError, ValueError):
        return None


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (
        CONTRACT,
        TOKENS,
        RUNTIME,
        TESTS,
        PLAN,
        V12_FOLDABLE,
        V12_RESPONSIVE,
        REACHABILITY,
        NAVIGATION,
        "VERSION",
        "registry/lifecycle.json",
    ):
        req((ROOT / path).is_file(), f"missing multi-pane artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Multi-Pane validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    lifecycle = load("registry/lifecycle.json")
    current_stable = lifecycle.get("currentStable")
    current_official = lifecycle.get("currentOfficial")
    req(version == current_stable == current_official, "VERSION/currentStable/currentOfficial must agree on the live current Stable release")
    current_tuple = version_tuple(version)
    v13_tuple = version_tuple(V13_VERSION)
    req(current_tuple is not None and v13_tuple is not None and current_tuple >= v13_tuple, "live current Stable may not regress below V1.3.0")
    retained_v13 = next((item for item in lifecycle.get("releases", []) if isinstance(item, dict) and item.get("version") == V13_VERSION), None)
    req(bool(retained_v13) and retained_v13.get("status") == "stable", "V1.3.0 retained release record must remain Stable")
    req(bool(retained_v13) and retained_v13.get("consumerEligible") is True, "V1.3.0 retained release record must preserve consumer eligibility")
    req(bool(retained_v13) and retained_v13.get("stableBaseline") == STABLE_VERSION, "V1.3.0 retained release baseline must remain 1.2.0")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("human-reachability", {}).get("status") == "implemented-and-validated", "Multi-Pane requires validated Human Reachability")
    req(workstreams.get("adaptive-navigation", {}).get("status") == "implemented-and-validated", "Multi-Pane requires validated Adaptive Navigation")
    req(
        workstreams.get("multi-pane-foldable-desktop", {}).get("status") in {
            "planned",
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "Multi-Pane workstream must use governed status vocabulary",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "multi-pane product identity mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "multi-pane target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "multi-pane lifecycle must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "multi-pane artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "multi-pane contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "multi-pane contract must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "multi-pane must extend V1.2 Stable")
    req(set(contract.get("extends", [])) == {V12_FOLDABLE, V12_RESPONSIVE, REACHABILITY, NAVIGATION}, "multi-pane inheritance set mismatch")

    expected_roles = {"primary", "secondary", "inspector", "navigation", "utility"}
    pane_roles = contract.get("paneRoles", {})
    req(set(pane_roles) == expected_roles, "semantic pane role set mismatch")
    req(pane_roles.get("primary", {}).get("required") is True, "primary pane must be required")
    for role in expected_roles - {"primary"}:
        req(pane_roles.get(role, {}).get("required") is False, f"{role} pane must remain optional")

    states = contract.get("compositionStates", {})
    req(set(states) == {"singlePane", "dualPane", "triplePane", "dualRegionHinge"}, "composition-state set mismatch")
    req(states.get("singlePane", {}).get("maximumContentPanes") == 1, "singlePane capacity mismatch")
    req(states.get("dualPane", {}).get("maximumContentPanes") == 2, "dualPane capacity mismatch")
    req(states.get("triplePane", {}).get("maximumContentPanes") == 3, "triplePane capacity mismatch")
    req(states.get("dualRegionHinge", {}).get("criticalTargetsMayIntersectHinge") is False, "critical targets may not intersect hinge")

    environments = contract.get("environmentPolicy", {})
    req(set(environments) == {"compact", "medium", "expanded", "workspace", "farView", "wearable"}, "environment-policy set mismatch")
    req(environments.get("compact", {}).get("defaultComposition") == "singlePane", "compact default must be singlePane")
    req(environments.get("compact", {}).get("multiPaneAllowed") is False, "compact must not require multi-pane")
    req(environments.get("medium", {}).get("defaultComposition") == "dualPane", "medium default composition mismatch")
    req(environments.get("expanded", {}).get("alternateComposition") == "triplePane", "expanded alternate composition mismatch")
    req(environments.get("workspace", {}).get("defaultComposition") == "triplePane", "workspace default must be triplePane")
    req(environments.get("wearable", {}).get("multiPaneAllowed") is False, "wearable must remain single-focus")

    posture = contract.get("posturePolicy", {})
    req(posture.get("folded", {}).get("defaultComposition") == "singlePane", "folded posture must default to singlePane")
    req(posture.get("unfolded", {}).get("mayAddInformation") is True, "unfolded posture must permit information gain")
    req(posture.get("unfolded", {}).get("mustNotOnlyScaleSinglePane") is True, "unfolded posture must not be scale-only")
    req(posture.get("halfOpen", {}).get("platformRegionsRequiredForDualRegionUse") is True, "half-open dual-region use requires platform regions")
    req(posture.get("halfOpen", {}).get("mustNotInferHingeGeometry") is True, "hinge geometry must not be inferred")

    hinge = contract.get("hingeAndObstruction", {})
    req(hinge.get("platformProvidedUnsafeRegionsRequired") is True, "platform-provided unsafe regions must be required")
    req(hinge.get("hardCodedDeviceHingeGeometryProhibited") is True, "hard-coded hinge geometry must be prohibited")
    req(hinge.get("criticalTargetsAvoidUnsafeRegions") is True, "critical targets must avoid unsafe regions")
    req(hinge.get("textMustNotBeSplitAcrossUnsafeRegion") is True, "text must not split across unsafe regions")

    gain = contract.get("informationGain", {})
    req(gain.get("largerLayoutsMustAddTaskValueRatherThanOnlyScale") is True, "large layouts must add task value")
    req(gain.get("secondaryPaneMayBeEmptyDecoration") is False, "secondary panes may not be decorative emptiness")
    req(gain.get("inspectorPaneMayBeEmptyDecoration") is False, "inspector panes may not be decorative emptiness")

    rules = contract.get("selectionRules", {})
    for key in (
        "rawViewportWidthRequired",
        "numericBreakpointsCanonical",
        "deviceBrandBreakpointsCanonical",
        "deviceIdentityInferenceAllowed",
        "touchTargetSizeMayShrinkToPreservePaneCount",
        "paneCountMayIncreaseWithoutTaskValue",
    ):
        req(rules.get(key) is False, f"multi-pane selection rule must be false: {key}")
    for key in (
        "environmentAdapterOwnsCapabilitySelection",
        "productDeclaresWhetherExtraPaneAddsTaskValue",
        "accessibilityMayCollapseMultiPane",
    ):
        req(rules.get(key) is True, f"multi-pane selection rule must be true: {key}")

    continuity = contract.get("continuity", {})
    preserved = set(continuity.get("preserve", []))
    for item in ("current-task", "selection", "typed-input", "unsaved-work", "media-state", "logical-back-history"):
        req(item in preserved, f"recomposition continuity must preserve {item}")
    req(continuity.get("recompositionMayReloadPage") is False, "recomposition may not require page reload")
    req(continuity.get("recompositionMayDiscardUnsavedWork") is False, "recomposition may not discard unsaved work")
    req(continuity.get("paneCollapseMayLoseCurrentSelection") is False, "pane collapse may not lose selection")

    accessibility = contract.get("accessibility", {})
    req(accessibility.get("minimumInteractiveTargetPx") >= 48, "minimum interactive target must remain at least 48px")
    req(accessibility.get("touchAssistanceTargetPx") >= 56, "touch assistance target must remain at least 56px")
    req(accessibility.get("largeTextMayCollapseInspector") is True, "large text must be allowed to collapse inspector")
    req(accessibility.get("largeTextMayCollapseSecondary") is True, "large text must be allowed to collapse secondary pane")
    req(accessibility.get("rtlLogicalPaneOrderRequired") is True, "RTL logical pane order must be required")
    req(accessibility.get("horizontalPageOverflowToPreservePaneCountProhibited") is True, "page overflow may not preserve pane count")

    tokens = load(TOKENS)
    req(tokens.get("product") == PRODUCT, "layout-token product mismatch")
    req(tokens.get("releaseLifecycle") == "proposed", "layout tokens must remain Proposed")
    req(tokens.get("consumerEligible") is False, "layout tokens must not be consumer eligible")
    implementations = tokens.get("implementationValues", {})
    req(implementations.get("workspaceEnvironment", {}).get("status") == "implemented-candidate-runtime", "workspace environment must be implemented")
    req(implementations.get("paneRoles", {}).get("status") == "implemented-candidate-runtime", "pane roles must be implemented")
    req(implementations.get("compositionStates", {}).get("status") == "implemented-candidate-runtime", "composition states must be implemented")
    req(implementations.get("posturePolicy", {}).get("status") == "implemented-candidate-runtime", "posture policy must be implemented")
    req(implementations.get("unsafeRegionPolicy", {}).get("hardCodedDeviceHingeGeometryAllowed") is False, "layout tokens must prohibit hard-coded hinge geometry")

    token_rules = tokens.get("rules", {})
    for key in (
        "reachableNotMerelyResponsive",
        "additionalSpaceShouldImproveTaskCompletion",
        "additionalPaneRequiresTaskValue",
        "taskAndSelectionContinuityRequiredAcrossTransformation",
        "unsavedWorkMustSurviveRecomposition",
        "safeAreasAndPostureMustBeRespected",
        "accessibilityReflowMayOverrideDensityAndPresentation",
        "accessibilityMayCollapsePaneCount",
    ):
        req(token_rules.get(key) is True, f"layout token rule must be true: {key}")
    for key in (
        "layoutMayStretchMobileCompositionOntoDesktop",
        "layoutMayCompressDesktopCompositionIntoPhone",
        "hardCodedDeviceHingeGeometryAllowed",
        "rawViewportWidthIsCompositionAuthority",
        "deviceBrandBreakpointsCanonical",
        "targetSizeMayShrinkToPreservePaneCount",
        "semanticTokensMayContainRawSpacingOrBreakpointValues",
    ):
        req(token_rules.get(key) is False, f"layout token rule must be false: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "innerWidth", "outerWidth", "matchMedia("):
        req(forbidden not in runtime, f"multi-pane runtime must not use forbidden network/viewport authority: {forbidden}")
    for symbol in ("resolvePaneComposition", "recomposePaneModel", "applyPaneComposition", "multiPaneCandidate"):
        req(symbol in runtime, f"multi-pane runtime missing required API: {symbol}")
    for state in ("singlePane", "dualPane", "triplePane", "dualRegionHinge"):
        req(state in runtime, f"multi-pane runtime missing governed composition: {state}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in (
        "oem-hinge-matrix",
        "physical-foldable-acceptance",
        "production-window-manager-integration",
        "platform-environment-threshold-calibration",
        "human-large-screen-acceptance",
        "assistive-technology-human-acceptance",
        "native-form-factor-parity",
        "release-candidate",
        "stable",
        "consumer-conformance",
    ):
        req(item in not_established, f"multi-pane evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Multi-Pane validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Multi-Pane/Foldable/Desktop: PASS")
    print(f"Boundary: preserved V1.3 capability-driven pane composition, continuity, posture policy, and unsafe-region handling remain validated against their 1.2.0 source baseline; live current Stable is {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
