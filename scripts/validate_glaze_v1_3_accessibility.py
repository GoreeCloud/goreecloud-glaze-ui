#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Accessibility and Resilience workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
CURRENT_STABLE_VERSION = "1.3.0"
SOURCE_STABLE_VERSION = "1.2.0"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
CONTRACT = "contracts/v1.3/accessibility.candidate.json"
RUNTIME = "js/glaze-v1.3-accessibility.candidate.mjs"
TESTS = "tests/glaze-v1.3-accessibility.test.mjs"
MATRIX = "contracts/accessibility/resolution-matrix.json"
V12_ADAPTATION = "contracts/v1.2/accessibility-adaptation.candidate.json"
V12_TESTING = "contracts/v1.2/accessibility-testing.candidate.json"
V12_AT = "contracts/v1.2/assistive-technology-qualification.candidate.json"
DEPENDENCIES = {
    "adaptive-dynamic-color": "contracts/v1.3/dynamic-color.candidate.json",
    "variable-responsive-typography": "contracts/v1.3/typography.candidate.json",
    "living-material-2": "contracts/v1.3/living-material-2.candidate.json",
    "human-reachability": "contracts/v1.3/reachability.candidate.json",
    "motion-and-continuity": "contracts/v1.3/motion-semantics.candidate.json",
}
EXPECTED_ORDER = [
    "protected-semantic-meaning",
    "forced-colors",
    "reduced-motion",
    "reduced-transparency",
    "increased-contrast-and-show-boundaries",
    "large-text-and-touch-assistance",
    "material-clarity",
    "expression-and-accent",
]


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = [
        CONTRACT, RUNTIME, TESTS, PLAN, MATRIX, V12_ADAPTATION, V12_TESTING, V12_AT,
        *DEPENDENCIES.values(), "VERSION", "registry/lifecycle.json",
    ]
    for path in required:
        req((ROOT / path).is_file(), f"missing accessibility artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Accessibility and Resilience validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == CURRENT_STABLE_VERSION, "VERSION must remain 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == CURRENT_STABLE_VERSION, "currentStable must remain 1.3.0")
    req(lifecycle.get("currentOfficial") == CURRENT_STABLE_VERSION, "currentOfficial must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "Accessibility work must not activate lifecycle Candidate")

    plan = load(PLAN)
    # Phase 0 owns overall phase sequencing. This workstream validator must remain
    # reusable as a dependency revalidation gate in later governed V1.3 phases.
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    for dep in DEPENDENCIES:
        req(workstreams.get(dep, {}).get("status") == "implemented-and-validated", f"Accessibility requires validated dependency {dep}")
    req(
        workstreams.get("accessibility-and-resilience", {}).get("status") in {
            "implementation-in-progress", "implementation-complete-validation-pending", "implemented-and-validated"
        },
        "Accessibility workstream must be active or validated",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "accessibility product mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "accessibility target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "accessibility lifecycle must remain Proposed")
    req(contract.get("lifecycleAuthority") is False, "accessibility contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "accessibility contract must not be consumer eligible")
    req(contract.get("sourceStable") == SOURCE_STABLE_VERSION, "accessibility must preserve the V1.2 source baseline")

    extends = set(contract.get("extends", []))
    for path in [MATRIX, V12_ADAPTATION, V12_TESTING, V12_AT, *DEPENDENCIES.values()]:
        req(path in extends, f"accessibility inheritance missing {path}")

    authority = contract.get("authority", {})
    req(authority.get("canonicalResolutionMatrix") == MATRIX, "canonical accessibility matrix must remain authoritative")
    req(authority.get("parallelAccessibilityAuthorityIntroduced") is False, "V1.3 must not introduce parallel accessibility authority")
    for key in ("accessibilityOutranksExpression", "accessibilityOutranksContextualAdaptation", "protectedSemanticMeaningOutranksRenderingPreference", "effectsDegradeBeforeCorrectness"):
        req(authority.get(key) is True, f"accessibility authority rule must be true: {key}")

    matrix = load(MATRIX)
    req(matrix.get("resolutionOrder") == EXPECTED_ORDER, "canonical resolution matrix order changed unexpectedly")
    req(contract.get("resolutionOrder") == EXPECTED_ORDER, "V1.3 accessibility resolution order must reuse canonical authority")

    interaction = contract.get("interaction", {})
    req(interaction.get("minimumInteractiveTargetPx") == 48, "default interaction floor must remain 48px")
    req(interaction.get("touchAssistanceMinimumInteractiveTargetPx") == 56, "Touch Assistance floor must remain 56px")
    req(interaction.get("farViewMinimumInteractiveTargetPx") == 56, "far-view interaction floor must remain 56px")
    req(interaction.get("visibleGeometryMayBeSmallerThanHitArea") is True, "hit area may exceed visible geometry")
    req(interaction.get("adjacentHitAreasMayOverlapAmbiguously") is False, "target hit areas may not overlap ambiguously")
    req(interaction.get("targetFloorMayShrinkToPreserveLayout") is False, "layout may not shrink accessibility target floors")

    text = contract.get("textAndLayout", {})
    req(text.get("acceptanceTextScalePercent") == 200, "accessibility acceptance scale must remain 200 percent")
    for key in ("largeTextRequiresReflow", "paneCountMayCollapseBeforeTargetShrinkage", "navigationMayRecomposeBeforeTargetShrinkage", "shellMayRecomposeBeforeCriticalTextClipping"):
        req(text.get(key) is True, f"text/layout rule must be true: {key}")
    for key in ("criticalTextClippingAllowed", "horizontalPageOverflowAllowed", "compactDensityMayDefeatLegibility", "importantContentMayBeHiddenOnlyToPreserveDecoration"):
        req(text.get(key) is False, f"text/layout rule must be false: {key}")

    rendering = contract.get("renderingPreferences", {})
    forced = rendering.get("forcedColors", {})
    for key in ("usesPlatformColorRoles", "forcesSolidMaterial", "semanticMeaningMustRemain"):
        req(forced.get(key) is True, f"Forced Colors rule must be true: {key}")
    for key in ("ambientColorAllowed", "customAccentMayOverridePlatformRoles"):
        req(forced.get(key) is False, f"Forced Colors rule must be false: {key}")

    transparency = rendering.get("reducedTransparency", {})
    req(transparency.get("forcesSolidMaterial") is True, "Reduced Transparency must force Solid material")
    for key in ("backdropBlurAllowed", "refractionAllowed", "distortionAllowed"):
        req(transparency.get(key) is False, f"Reduced Transparency must disable {key}")

    motion = rendering.get("reducedMotion", {})
    for key in ("removeNonessentialTranslation", "removeNonessentialScale", "nonessentialMotionMayBecomeImmediate", "directManipulationTrackingPreserved", "semanticStatePreserved", "focusPreserved"):
        req(motion.get(key) is True, f"Reduced Motion rule must be true: {key}")
    req(motion.get("taskCompletionMayWaitForAnimation") is False, "task completion may not wait for motion")
    req(motion.get("mayMerelySpeedUpOriginalMotion") is False, "Reduced Motion may not merely accelerate original motion")

    semantics = contract.get("semanticAccessibility", {})
    for key in ("accessibleNameRequiredForInteractiveControls", "semanticRoleRequiredForInteractiveControls", "stateValueAndRelationshipExposedWhenApplicable", "focusOrderMustRemainLogical", "visibleFocusRequired", "generatedContentMustRemainDistinctFromSystemTruth", "productIdentityMustRemainDistinctFromAccountIdentity"):
        req(semantics.get(key) is True, f"semantic accessibility rule must be true: {key}")
    for key in ("semanticStateMayRelyOnColorOnly", "authorityMayRelyOnColorOnly", "motionMayBeOnlyStateSignal", "materialEffectMayBeOnlyBoundarySignal"):
        req(semantics.get(key) is False, f"semantic accessibility rule must be false: {key}")

    directionality = contract.get("directionality", {})
    req(directionality.get("rtlUsesLogicalOrder") is True, "RTL must use logical order")
    for key in ("rtlMayReverseSemanticHistory", "rtlMayChangeCurrentDestinationIdentity", "directionChangeMayResetFocus", "directionChangeMayDiscardInput"):
        req(directionality.get(key) is False, f"directionality rule must be false: {key}")

    continuity = contract.get("continuity", {})
    preserved = set(continuity.get("preserve", []))
    for item in ("current-task", "current-destination", "selection", "draft-state", "typed-input", "unsaved-work", "focus", "logical-focus-order", "media-state"):
        req(item in preserved, f"accessibility continuity must preserve {item}")
    req(continuity.get("recompositionMustPreserveTaskState") is True, "accessibility recomposition must preserve task state")
    for key in ("accessibilityPreferenceChangeMayReloadPage", "accessibilityPreferenceChangeMayResetSelection", "accessibilityPreferenceChangeMayDiscardDraft", "accessibilityPreferenceChangeMayResetFocus"):
        req(continuity.get(key) is False, f"continuity rule must be false: {key}")

    automated = contract.get("automatedScope", {})
    for key in ("machineObservableSemanticChecksAllowed", "accessibleNameRoleStateChecksAllowed", "targetGeometryChecksAllowed", "reflowAndOverflowChecksAllowed", "preferencePrecedenceChecksAllowed", "rtlLogicalOrderChecksAllowed", "continuityChecksAllowed"):
        req(automated.get(key) is True, f"automated scope must allow {key}")
    for key in ("automatedEvidenceEstablishesHumanAcceptance", "automatedEvidenceEstablishesScreenReaderAcceptance", "automatedEvidenceEstablishesAssistiveTechnologyAcceptance", "automatedEvidenceEstablishesPhysicalDeviceAcceptance", "automatedEvidenceEstablishesNativePlatformParity", "automatedEvidenceEstablishesProductionPerformanceAcceptance"):
        req(automated.get(key) is False, f"automated evidence boundary must be false: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "setInterval(", "requestAnimationFrame("):
        req(forbidden not in runtime, f"accessibility runtime contains forbidden network/autonomous primitive: {forbidden}")
    for symbol in ("resolveAccessibilityProfile", "auditAccessibleNode", "resolveResilientComposition", "createAccessibilityResolver", "accessibilityResilienceCandidate"):
        req(symbol in runtime, f"accessibility runtime missing API: {symbol}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("human-accessibility-acceptance", "screen-reader-acceptance", "talkback-acceptance", "voiceover-acceptance", "switch-control-acceptance", "voice-access-acceptance", "physical-device-accessibility-acceptance", "complete-native-platform-accessibility-parity", "production-performance-acceptance", "release-candidate", "stable", "consumer-conformance"):
        req(item in not_established, f"accessibility evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Accessibility and Resilience validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Accessibility + Resilience: PASS")
    print("Boundary: V1.3.0 remains current Stable; automated accessibility composition preserves V1.2 source provenance without claiming manual assistive-technology, physical-device, native-platform, human, production, or V1.3.1 acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
