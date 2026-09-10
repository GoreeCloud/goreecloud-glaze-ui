#!/usr/bin/env python3
"""Validate the historical GLAZE UI V1.3 System Shell and Control Center workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
SOURCE_STABLE_VERSION = "1.2.0"
CURRENT_STABLE_VERSION = "1.3.0"
SHELL = "contracts/v1.3/system-shell.candidate.json"
CONTROL = "contracts/v1.3/control-center.candidate.json"
RUNTIME = "js/glaze-v1.3-system-shell.candidate.mjs"
TESTS = "tests/glaze-v1.3-system-shell.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
V12_NAV = "contracts/v1.2/system-shell-navigation.candidate.json"
V12_MATERIAL = "contracts/v1.2/system-shell-materials.candidate.json"
V12_CONTROL = "contracts/v1.2/control-center-customization.candidate.json"
NAVIGATION = "contracts/v1.3/adaptive-navigation.candidate.json"
MATERIAL = "contracts/v1.3/living-material-2.candidate.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (SHELL, CONTROL, RUNTIME, TESTS, PLAN, V12_NAV, V12_MATERIAL, V12_CONTROL, NAVIGATION, MATERIAL, "VERSION", "registry/lifecycle.json"):
        req((ROOT / path).is_file(), f"missing system-shell artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 System Shell validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == CURRENT_STABLE_VERSION, "VERSION must identify current Stable 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == CURRENT_STABLE_VERSION, "currentStable must remain 1.3.0")
    req(lifecycle.get("currentOfficial") == CURRENT_STABLE_VERSION, "currentOfficial must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "System Shell validation must not activate lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("adaptive-navigation", {}).get("status") == "implemented-and-validated", "System Shell requires validated Adaptive Navigation")
    req(workstreams.get("living-material-2", {}).get("status") == "implemented-and-validated", "System Shell requires validated Living Material 2.0")
    req(
        workstreams.get("system-shell-and-control-center", {}).get("status") in {
            "planned",
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "System Shell workstream must use governed status vocabulary",
    )

    shell = load(SHELL)
    req(shell.get("product") == PRODUCT, "system-shell product mismatch")
    req(shell.get("targetVersion") == "1.3.0-candidate", "system-shell target mismatch")
    req(shell.get("releaseLifecycle") == "proposed", "historical system-shell artifact lifecycle must remain Proposed")
    req(shell.get("lifecycleAuthority") is False, "system-shell contract must not carry lifecycle authority")
    req(shell.get("consumerEligible") is False, "historical system-shell candidate artifact must not be consumer eligible")
    req(shell.get("sourceStable") == SOURCE_STABLE_VERSION, "historical system-shell artifact must preserve its V1.2 Stable source baseline")
    req(set(shell.get("extends", [])) == {V12_NAV, V12_MATERIAL, NAVIGATION, MATERIAL}, "system-shell inheritance set mismatch")

    regions = shell.get("shellRegions", {})
    req(set(regions) == {"workspace", "navigation", "universal-search", "control-center", "critical-system"}, "five-region system-shell model mismatch")
    req(regions.get("navigation", {}).get("presentationAuthority") == "adaptive-navigation", "shell navigation must delegate to Adaptive Navigation")
    req(regions.get("universal-search", {}).get("scopeMustBeVisible") is True, "universal-search scope must be visible")
    req(regions.get("critical-system", {}).get("backdropDependent") is False, "critical-system region may not be backdrop dependent")
    req(regions.get("critical-system", {}).get("producerAuthoritative") is True, "critical-system region must be producer authoritative")

    rules = shell.get("rules", {})
    for key in (
        "shellFramesApplicationWithoutDominating",
        "stableSpatialMemoryRequired",
        "currentDestinationRequiresStructuralCue",
        "applicationIdentityDistinctFromAccountIdentity",
        "globalAndLocalActionsRemainDistinct",
        "criticalStateProducerAuthoritative",
        "universalSearchScopeVisible",
        "destructiveSearchActionRequiresConfirmation",
        "searchGeneratedResultsDistinctFromSystemTruth",
        "adaptiveNavigationOwnsPrimaryNavigationPresentation",
    ):
        req(rules.get(key) is True, f"system-shell rule must be true: {key}")
    for key in (
        "predictionMayReorderPrimaryNavigation",
        "currentDestinationMayDependOnColorAlone",
        "criticalDecisionsBackdropDependent",
        "criticalDecisionsMayUseContextAccentAsAuthority",
        "denseNotificationHistoryBackdropDependent",
        "rawViewportWidthIsShellCompositionAuthority",
        "deviceBrandBreakpointsCanonical",
    ):
        req(rules.get(key) is False, f"system-shell rule must be false: {key}")

    communication = shell.get("systemCommunication", {})
    req(set(communication.get("notificationRequiredFields", [])) >= {"source", "event", "time", "priority"}, "notification communication fields incomplete")
    req(communication.get("criticalRegionRequiresAuthoritativeSource") is True, "critical region must require authoritative source")
    req(communication.get("routineStatusMayFlashOrPulseContinuously") is False, "routine status may not continuously flash or pulse")
    req(communication.get("criticalFailureMayBeToastOnly") is False, "critical failure may not be toast-only")

    material = shell.get("materialPolicy", {})
    req(material.get("criticalSystem") == "high-opacity-raised-or-solid", "critical system material must remain high-opacity")
    req(material.get("nestedBackdropBlurDefaultAllowed") is False, "nested shell backdrop blur must remain off by default")
    req(material.get("neutralMaterialFoundationRequired") is True, "neutral material foundation must remain required")

    accessibility = shell.get("accessibility", {})
    req(accessibility.get("minimumInteractiveTargetPx") >= 48, "shell target minimum must remain at least 48px")
    req(accessibility.get("touchAssistanceTargetPx") >= 56, "shell touch-assistance target must remain at least 56px")
    req(accessibility.get("farViewMinimumInteractiveTargetPx") >= 56, "far-view shell target must remain at least 56px")
    req(accessibility.get("largeTextMayPromoteOverlayToDedicatedView") is True, "large text must be allowed to promote shell overlays")
    req(accessibility.get("reducedTransparencyUsesSolidNeutralShell") is True, "Reduced Transparency must provide solid shell fallback")
    req(accessibility.get("forcedColorsUsesPlatformMapping") is True, "Forced Colors must use platform mapping")

    control = load(CONTROL)
    req(control.get("product") == PRODUCT, "control-center product mismatch")
    req(control.get("releaseLifecycle") == "proposed", "historical control-center artifact lifecycle must remain Proposed")
    req(control.get("consumerEligible") is False, "historical control-center candidate artifact must not be consumer eligible")
    req(set(control.get("extends", [])) == {V12_CONTROL, V12_MATERIAL, MATERIAL}, "control-center inheritance set mismatch")
    req(control.get("parentSurface", {}).get("nestedBackdropBlurDefaultAllowed") is False, "control-center nested backdrop blur must remain off by default")
    req(control.get("parentSurface", {}).get("parentRemainsSubstantiallyNeutral") is True, "control-center parent must remain substantially neutral")

    module_rules = control.get("moduleRules", {})
    req(module_rules.get("stableModuleIdRequired") is True, "Control Center modules require stable ids")
    req(module_rules.get("semanticIdentitySurvivesResize") is True, "module identity must survive resize")
    req(module_rules.get("semanticIdentitySurvivesReorder") is True, "module identity must survive reorder")
    req(module_rules.get("resizeMayChangeMeaning") is False, "module resize may not change meaning")
    req(module_rules.get("activeStateMayDependOnColorAlone") is False, "module state may not depend on color alone")
    req(module_rules.get("producerAuthoritativeStatusCannotBeOverriddenByAccent") is True, "accent may not override producer-authoritative status")

    editing = control.get("editing", {})
    req(editing.get("dragIsSoleReorderMechanism") is False, "drag may not be the sole reorder mechanism")
    req(editing.get("accessibleReorderAlternativeRequired") is True, "accessible reorder alternative must be required")
    req(editing.get("resetRequired") is True, "Control Center reset must be required")
    req(editing.get("semanticAnnouncementsRequired") is True, "editing must require semantic announcements")
    req(editing.get("cancelWithoutStateCorruptionRequired") is True, "editing cancel must not corrupt state")
    req(editing.get("persistentStorageEstablished") is False, "persistent Control Center storage must remain unestablished")
    req(editing.get("crossDeviceSyncEstablished") is False, "Control Center cross-device sync must remain unestablished")

    cc_accessibility = control.get("accessibility", {})
    req(cc_accessibility.get("minimumInteractiveTargetPx") >= 48, "Control Center target minimum must remain at least 48px")
    req(cc_accessibility.get("touchAssistanceTargetPx") >= 56, "Control Center touch-assistance target must remain at least 56px")
    req(cc_accessibility.get("largeTextMustReflow") is True, "Control Center must reflow for large text")
    req(cc_accessibility.get("targetsMayShrinkForDensity") is False, "Control Center targets may not shrink for density")
    req(cc_accessibility.get("keyboardCompleteEditingRequired") is True, "Control Center editing must be keyboard complete")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "innerWidth", "outerWidth", "matchMedia(", "localStorage", "sessionStorage", "indexedDB"):
        req(forbidden not in runtime, f"system-shell runtime contains forbidden network/viewport/persistence primitive: {forbidden}")
    req("resolveNavigationPresentation" in runtime, "system-shell runtime must consume Adaptive Navigation runtime")
    for symbol in (
        "resolveSystemShell",
        "resolveControlCenterPresentation",
        "normalizeControlCenterModules",
        "moveControlCenterModule",
        "resizeControlCenterModule",
        "resetControlCenterModules",
        "applySystemShellPresentation",
        "systemShellCandidate",
        "controlCenterCandidate",
    ):
        req(symbol in runtime, f"system-shell runtime missing required API: {symbol}")

    shell_not = set(shell.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("full-notification-center-runtime", "multi-window-native-shell-runtime", "native-window-control-parity", "physical-device-shell-acceptance", "release-candidate", "stable", "consumer-conformance"):
        req(item in shell_not, f"system-shell evidence boundary must leave {item!r} unestablished")
    control_not = set(control.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("persistent-user-layout-storage", "cross-device-layout-sync", "physical-device-editing-acceptance", "native-control-center-parity", "release-candidate", "stable", "consumer-conformance"):
        req(item in control_not, f"control-center evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 System Shell validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 System Shell + Control Center: PASS")
    print("Boundary: historical V1.3 candidate artifacts preserve their V1.2 source provenance while repository lifecycle authority remains current V1.3.0 Stable; shell and Control Center contracts are revalidated without native-shell, persistence, physical-device, lifecycle, or consumer claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
