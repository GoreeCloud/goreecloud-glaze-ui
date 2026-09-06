#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Motion and Continuity workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.2.0"
CONTRACT = "contracts/v1.3/motion-semantics.candidate.json"
TOKENS = "tokens/glaze-v1.3-motion.candidate.json"
RUNTIME = "js/glaze-v1.3-motion.candidate.mjs"
TESTS = "tests/glaze-v1.3-motion.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
V12_MOTION = "contracts/v1.2/motion.candidate.json"
V12_CONTINUITY = "contracts/v1.2/context-continuity.candidate.json"
V12_TOKENS = "tokens/glaze-v1.2-motion.candidate.json"
MATERIAL = "contracts/v1.3/living-material-2.candidate.json"
NAVIGATION = "contracts/v1.3/adaptive-navigation.candidate.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (CONTRACT, TOKENS, RUNTIME, TESTS, PLAN, V12_MOTION, V12_CONTINUITY, V12_TOKENS, MATERIAL, NAVIGATION, "VERSION", "registry/lifecycle.json"):
        req((ROOT / path).is_file(), f"missing motion artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Motion validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must remain 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "Motion work must not activate lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("living-material-2", {}).get("status") == "implemented-and-validated", "Motion requires validated Living Material 2.0")
    req(workstreams.get("adaptive-navigation", {}).get("status") == "implemented-and-validated", "Motion requires validated Adaptive Navigation")
    req(
        workstreams.get("motion-and-continuity", {}).get("status") in {
            "planned", "implementation-in-progress", "implementation-complete-validation-pending", "implemented-and-validated"
        },
        "Motion workstream status is invalid",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "motion product mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "motion target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "motion lifecycle must remain Proposed")
    req(contract.get("lifecycleAuthority") is False, "motion contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "motion contract must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "motion must extend V1.2 Stable")
    req(set(contract.get("extends", [])) == {V12_MOTION, V12_CONTINUITY, MATERIAL, NAVIGATION}, "motion inheritance mismatch")

    principles = contract.get("principles", {})
    for key in (
        "respondImmediately", "moveWithPurpose", "preserveContinuity", "settleQuietly", "userControlFirst",
        "stateIndependentOfAnimationCompletion", "focusMustNotWaitForMotion", "connectedIdentityRequiresClearRelationship",
        "directManipulationTracksInputImmediately", "userDrivenMotionInterruptible", "reducedMotionPreservesSemanticState"
    ):
        req(principles.get(key) is True, f"motion principle must be true: {key}")
    for key in ("decorativeContinuousMotionAllowed", "routineWobblePulseOrBounceAllowed", "automaticSpringPhysicsRequired"):
        req(principles.get(key) is False, f"motion principle must be false: {key}")

    roles = contract.get("semanticRoles", {})
    req(set(roles) == {"direct", "micro", "standard", "connected", "expressive", "spatial", "reduced", "minimal"}, "motion semantic role set mismatch")
    req(roles.get("connected", {}).get("durationFamily") == "deliberate", "connected motion must use deliberate family")
    req(roles.get("spatial", {}).get("durationFamily") == "spatial", "spatial role must use spatial family")
    req(roles.get("spatial", {}).get("explicitJustificationRequired") is True, "spatial motion must require justification")

    transforms = contract.get("connectedTransformations", {})
    expected_transforms = {
        "search-capsule-to-search-panel", "navigation-item-to-destination-header", "quick-control-to-expanded-control",
        "mini-player-to-player", "notification-to-detail", "floating-toolbar-to-contextual-sheet", "thumbnail-to-detail"
    }
    req(set(transforms) == expected_transforms, "connected transformation matrix mismatch")
    req(all(item.get("identityMustPersist") is True for item in transforms.values()), "connected transformations must preserve identity")

    relationship = contract.get("relationshipRules", {})
    req(relationship.get("unclearRelationshipFallsBackToStandardTransition") is True, "unclear relationships must fall back to standard motion")
    for key in ("connectedTransformMayInventIdentity", "connectedTransformMayChangeSemanticMeaning", "connectedTransformMayResetCurrentTask", "connectedTransformMayDiscardUnsavedWork"):
        req(relationship.get(key) is False, f"relationship rule must be false: {key}")

    direct = contract.get("directManipulation", {})
    req(direct.get("trackingDurationMs") == 0, "direct manipulation tracking must be immediate")
    req(direct.get("tracksInputImmediately") is True, "direct manipulation must track input")
    req(direct.get("userMayInterrupt") is True, "direct manipulation must be interruptible")
    req(direct.get("settleMayBlockStateChange") is False, "settling may not block state")
    req(direct.get("reducedMotionStillTracksInput") is True, "Reduced Motion must preserve direct manipulation tracking")

    expression = contract.get("expression", {})
    req(expression.get("profiles") == ["calm", "balanced", "expressive"], "motion expression profiles mismatch")
    req(expression.get("profileMayChooseAmongGovernedSemanticRoles") is True, "expression may choose governed semantic roles")
    req(expression.get("profileMayInventRawDurationOrCurve") is False, "expression may not invent raw motion calibration")
    req(expression.get("profileMayIntroduceContinuousMotion") is False, "expression may not introduce continuous motion")
    req(expression.get("accessibilityOverridesExpression") is True, "accessibility must override motion expression")

    continuity = contract.get("continuity", {})
    preserved = set(continuity.get("preserve", []))
    for item in ("current-task", "current-destination", "selection", "draft-state", "typed-input", "unsaved-work", "media-state"):
        req(item in preserved, f"motion continuity must preserve {item}")
    req(continuity.get("motionRequiredForCorrectness") is False, "motion may not be required for correctness")
    req(continuity.get("animationCompletionRequiredForStateCommit") is False, "state may not wait for animation")
    req(continuity.get("animationCompletionRequiredForFocus") is False, "focus may not wait for animation")
    req(continuity.get("recompositionMayReloadPage") is False, "recomposition may not require reload")

    accessibility = contract.get("accessibility", {})
    reduced = accessibility.get("reducedMotion", {})
    for key in ("removeNonessentialTranslation", "removeNonessentialScale", "nonessentialMotionMayBecomeImmediate", "preserveDirectManipulationTracking", "preserveSemanticState", "preserveFocus", "mustNotDelayTaskCompletion"):
        req(reduced.get(key) is True, f"Reduced Motion rule must be true: {key}")
    req(accessibility.get("minimumInteractiveTargetPx") >= 48, "motion target floor must remain at least 48px")
    req(accessibility.get("motionMayBeOnlyStateSignal") is False, "motion may not be the only state signal")

    spring = contract.get("springBoundary", {})
    req(spring.get("newSpringRuntimeIntroduced") is False, "V1.3 motion must not introduce a spring runtime")
    req(spring.get("newSpringCalibrationIntroduced") is False, "V1.3 motion must not invent spring calibration")
    req(spring.get("settleSemanticsUseExistingGovernedEasing") is True, "settle semantics must use governed easing")
    req(spring.get("experimentalGlazeMotionPromoted") is False, "Experimental Glaze Motion must not be promoted")

    token = load(TOKENS)
    req(token.get("product") == PRODUCT, "motion token product mismatch")
    req(token.get("releaseLifecycle") == "proposed", "motion tokens must remain Proposed")
    req(token.get("namespace") == "motion", "motion token namespace mismatch")
    implementation = token.get("implementationValues", {})
    req(token.get("semanticTokens", {}).get("motion.connected", {}).get("implementation") == "connected", "motion.connected must bind to dedicated connected implementation")
    req(implementation.get("connected", {}).get("pointer") == "/durationsMs/deliberate", "connected token must inherit deliberate duration")
    req(implementation.get("spatial", {}).get("pointer") == "/durationsMs/spatial", "spatial token must inherit spatial duration")
    req(implementation.get("springSemantics", {}).get("newSpringRuntimeIntroduced") is False, "motion token policy must prohibit new spring runtime")
    req(implementation.get("connectedTransformations", {}).get("status") == "implemented-candidate-runtime", "connected transformation token policy must be implemented")

    token_rules = token.get("rules", {})
    for key in ("motionMustPreserveContext", "reducedMotionPreservesSemanticStateChange", "reducedMotionMayCollapseTravel", "directManipulationTrackingRemainsImmediate", "spatialMotionRequiresExplicitRelationshipJustification"):
        req(token_rules.get(key) is True, f"motion token rule must be true: {key}")
    for key in ("animationForAnimationSakeAllowed", "continuousRestlessAnimationAllowed", "routineWobblePulseOrBounceAllowed", "motionMayMisrepresentActualProgress", "stateMayWaitForAnimationCompletion", "focusMayWaitForAnimationCompletion", "newSpringRuntimeIntroduced", "semanticTokensMayContainRawDurationsOrCurves"):
        req(token_rules.get(key) is False, f"motion token rule must be false: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "requestAnimationFrame(", "setInterval("):
        req(forbidden not in runtime, f"motion semantic runtime contains forbidden network/autonomous loop primitive: {forbidden}")
    for symbol in ("resolveMotion", "resolveConnectedTransformation", "resolveDirectManipulation", "applyMotionSemantics", "motionContinuityCandidate"):
        req(symbol in runtime, f"motion runtime missing API: {symbol}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("v1.3-spring-calibration", "native-motion-parity", "physical-device-motion-acceptance", "representative-frame-pacing-acceptance", "production-compositor-window-motion-integration", "human-motion-optical-acceptance", "release-candidate", "stable", "consumer-conformance"):
        req(item in not_established, f"motion evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Motion validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Motion + Continuity: PASS")
    print("Boundary: semantic connected motion and continuity are implemented using governed calibration without new spring physics, native/device/performance acceptance, lifecycle promotion, or consumer claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
