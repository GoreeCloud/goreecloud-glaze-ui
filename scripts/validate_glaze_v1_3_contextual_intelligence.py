#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Contextual Intelligence workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.2.0"
CONTRACT = "contracts/v1.3/contextual-intelligence.candidate.json"
RUNTIME = "js/glaze-v1.3-contextual-intelligence.candidate.mjs"
TESTS = "tests/glaze-v1.3-contextual-intelligence.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
V12_INTELLIGENCE = "contracts/v1.2/intelligence-components.candidate.json"
V12_CONTINUITY = "contracts/v1.2/context-continuity.candidate.json"
DYNAMIC_COLOR = "contracts/v1.3/dynamic-color.candidate.json"
NAVIGATION = "contracts/v1.3/adaptive-navigation.candidate.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (CONTRACT, RUNTIME, TESTS, PLAN, V12_INTELLIGENCE, V12_CONTINUITY, DYNAMIC_COLOR, NAVIGATION, "VERSION", "registry/lifecycle.json"):
        req((ROOT / path).is_file(), f"missing contextual-intelligence artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Contextual Intelligence validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must remain 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "Contextual Intelligence must not activate lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("adaptive-dynamic-color", {}).get("status") == "implemented-and-validated", "Contextual Intelligence requires validated Dynamic Color")
    req(workstreams.get("adaptive-navigation", {}).get("status") == "implemented-and-validated", "Contextual Intelligence requires validated Adaptive Navigation")
    req(
        workstreams.get("contextual-intelligence", {}).get("status") in {
            "planned", "implementation-in-progress", "implementation-complete-validation-pending", "implemented-and-validated"
        },
        "Contextual Intelligence workstream status is invalid",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "contextual-intelligence product mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "contextual-intelligence target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "contextual-intelligence lifecycle must remain Proposed")
    req(contract.get("lifecycleAuthority") is False, "contextual-intelligence must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "contextual-intelligence must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "contextual-intelligence must extend V1.2 Stable")
    req(set(contract.get("extends", [])) == {V12_INTELLIGENCE, V12_CONTINUITY, DYNAMIC_COLOR, NAVIGATION}, "contextual-intelligence inheritance mismatch")

    snapshot = contract.get("contextSnapshot", {})
    allowed = set(snapshot.get("allowedSignalFamilies", []))
    req(allowed == {"current-task", "current-destination", "selected-object-kind", "available-source-kind", "interaction-mode", "local-environment-summary", "producer-declared-state"}, "context signal family set mismatch")
    req(snapshot.get("rawPrivateActivityRequired") is False, "raw private activity must not be required")
    req(snapshot.get("rawContentRequired") is False, "raw content must not be required")
    req(snapshot.get("networkAcquisitionRequired") is False, "network context acquisition must not be required")
    req(snapshot.get("telemetryAuthorized") is False, "context contract must not authorize telemetry")
    req(snapshot.get("runtimePersistenceAuthorized") is False, "context contract must not authorize runtime persistence")

    ranking = contract.get("ranking", {})
    req(ranking.get("appliesTo") == "optional-contextual-suggestions-only", "ranking must be limited to optional contextual suggestions")
    req(ranking.get("producerProvidedStableSuggestionIdRequired") is True, "stable suggestion ids must be required")
    req(ranking.get("stableTieBreak") == "original-order", "suggestion tie-break must preserve original order")
    for key in ("mayReorderPrimaryNavigation", "mayReorderRequiredSafetyActions", "mayHideRequiredSystemTruth", "mayPromoteSuggestionToSystemTruth"):
        req(ranking.get(key) is False, f"ranking rule must be false: {key}")
    req(ranking.get("dismissedSuggestionRemovedFromActiveFlow") is True, "dismissed suggestions must leave active flow")

    safety = contract.get("actionSafety", {})
    req(safety.get("automaticConsequentialExecutionAllowed") is False, "automatic consequential execution must be prohibited")
    req(safety.get("consequentialActionRequiresExplicitConfirmation") is True, "consequential actions require confirmation")
    req(safety.get("destructiveActionRequiresExplicitConfirmation") is True, "destructive actions require confirmation")
    req(safety.get("authenticationRecoveryPrivacySecurityActionsRemainProducerAuthoritative") is True, "consequential system domains must remain producer authoritative")
    req(safety.get("suggestionMayBeSoleAuthorityForConsequentialDecision") is False, "suggestions may not be sole consequential authority")
    req(safety.get("generatedResultMayBePresentedAsVerifiedSystemTruth") is False, "generated results may not be system truth")

    color = contract.get("dynamicColorBoundary", {})
    req(color.get("contextPaletteMayBeConsumed") is True, "context palette consumption should be explicit")
    req(color.get("contextMayRedefineSemanticColor") is False, "context may not redefine semantic color")
    req(color.get("contextMayEraseProductIdentity") is False, "context may not erase product identity")
    req(color.get("contextColorMayBeOnlySuggestionSignal") is False, "context color may not be the sole suggestion signal")
    dynamic = load(DYNAMIC_COLOR)
    req(set(color.get("allowedContextColorRoles", [])) == set(dynamic.get("contextPalette", {}).get("allowedRoles", [])), "contextual-intelligence color roles must match Dynamic Color authority")

    navigation = contract.get("navigationBoundary", {})
    req(navigation.get("adaptiveNavigationOwnsPrimaryDestinationModel") is True, "Adaptive Navigation must own primary destinations")
    req(navigation.get("contextMayReorderPrimaryDestinations") is False, "context may not reorder primary destinations")
    req(navigation.get("contextMayInventPrimaryDestination") is False, "context may not invent primary destinations")
    req(navigation.get("contextMayChangeCurrentDestinationIdentity") is False, "context may not change current destination identity")

    continuity = contract.get("continuity", {})
    preserved = set(continuity.get("preserve", []))
    for item in ("current-task", "current-destination", "selection", "draft-state", "typed-input", "unsaved-work", "media-state"):
        req(item in preserved, f"context continuity must preserve {item}")
    req(continuity.get("contextRefreshMayResetTaskState") is False, "context refresh may not reset task state")
    req(continuity.get("contextLossMayResetTaskState") is False, "context loss may not reset task state")
    req(continuity.get("contextChangeRequiresPageReload") is False, "context change must not require page reload")

    accessibility = contract.get("accessibility", {})
    req(accessibility.get("minimumInteractiveTargetPx") >= 48, "minimum target must be at least 48px")
    req(accessibility.get("touchAssistanceTargetPx") >= 56, "touch-assistance target must be at least 56px")
    req(accessibility.get("generatedStatusMayDependOnColorAlone") is False, "generated status may not depend on color alone")
    req(accessibility.get("uncertaintyMayDependOnColorAlone") is False, "uncertainty may not depend on color alone")
    req(accessibility.get("largeTextMustReflowWithoutHidingProvenance") is True, "large text must preserve provenance")

    privacy = contract.get("privacyAndRuntime", {})
    req(privacy.get("localFirst") is True, "contextual runtime must remain local-first")
    for key in ("remoteInferenceRequired", "telemetryRequired", "runtimeNetworkRequestRequired", "runtimePersistenceRequired", "rawContextLoggingAllowed", "modelOrProviderSelectionOwnedByGlaze"):
        req(privacy.get(key) is False, f"privacy/runtime rule must be false: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "localStorage", "sessionStorage", "indexedDB", "console.log("):
        req(forbidden not in runtime, f"contextual runtime contains forbidden network/persistence/raw-log primitive: {forbidden}")
    for symbol in ("normalizeContextSnapshot", "rankOptionalSuggestions", "resolveContextualPresentation", "actionSafetyForSuggestion", "dismissContextualSuggestion", "applyContextualPresentation", "contextualIntelligenceCandidate"):
        req(symbol in runtime, f"contextual runtime missing API: {symbol}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("model-provider-authority", "remote-inference-service", "telemetry-based-personalization", "production-recommendation-quality", "autonomous-consequential-actions", "native-intelligence-parity", "human-intelligence-acceptance", "release-candidate", "stable", "consumer-conformance"):
        req(item in not_established, f"contextual evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Contextual Intelligence validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Contextual Intelligence: PASS")
    print("Boundary: bounded context-aware optional suggestions, provenance, continuity and action safety are implemented without model/provider, remote inference, telemetry, autonomous-action, lifecycle or consumer claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
