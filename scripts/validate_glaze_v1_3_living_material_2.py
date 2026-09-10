#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Living Material 2.0 implementation workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
CURRENT_STABLE_VERSION = "1.3.0"
SOURCE_STABLE_VERSION = "1.2.0"
CONTRACT = "contracts/v1.3/living-material-2.candidate.json"
TOKENS = "tokens/glaze-v1.3-material.candidate.json"
RUNTIME = "js/glaze-v1.3-living-material-2.candidate.mjs"
TESTS = "tests/glaze-v1.3-living-material-2.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer in ("", "/"):
        return document
    current = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = (
        CONTRACT,
        TOKENS,
        RUNTIME,
        TESTS,
        PLAN,
        "VERSION",
        "registry/lifecycle.json",
        "contracts/v1.2/living-glaze.candidate.json",
        "contracts/v1.2/performance-adaptation.candidate.json",
        "contracts/v1.3/dynamic-color.candidate.json",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing Living Material 2.0 artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Living Material 2.0 validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == CURRENT_STABLE_VERSION, "VERSION must remain 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == CURRENT_STABLE_VERSION, "currentStable must remain 1.3.0")
    req(lifecycle.get("currentOfficial") == CURRENT_STABLE_VERSION, "currentOfficial must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "Living Material 2.0 must not activate release lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    dynamic = workstreams.get("adaptive-dynamic-color", {})
    material_workstream = workstreams.get("living-material-2", {})
    req(dynamic.get("status") == "implemented-and-validated", "Living Material 2.0 requires validated dynamic-color dependency")
    req(
        material_workstream.get("status") in {
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "Living Material 2.0 workstream must be active in the plan",
    )
    req(
        set(material_workstream.get("dependsOn", [])) == {"contract-and-token-architecture", "adaptive-dynamic-color"},
        "Living Material 2.0 dependency set mismatch",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "Living Material 2.0 product identity mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "Living Material 2.0 target version mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "Living Material 2.0 release lifecycle must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "Living Material 2.0 artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "Living Material 2.0 must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "Living Material 2.0 must not be consumer eligible")
    req(contract.get("sourceStable") == SOURCE_STABLE_VERSION, "Living Material 2.0 must preserve the V1.2 source baseline")

    expected_extends = {
        "contracts/v1.2/living-glaze.candidate.json",
        "contracts/v1.2/performance-adaptation.candidate.json",
        "contracts/v1.3/dynamic-color.candidate.json",
    }
    req(set(contract.get("extends", [])) == expected_extends, "Living Material 2.0 inheritance set mismatch")

    expected_roles = {"soft-glaze", "glaze", "deep-glaze", "live-glaze"}
    thickness = contract.get("materialThickness", {})
    req(expected_roles.issubset(thickness), "Living Material 2.0 is missing required material thickness roles")

    responsive = contract.get("responsiveInputs", {})
    required_inputs = {
        "underlying-luminance",
        "underlying-complexity",
        "hover",
        "press",
        "focus",
        "drag",
        "selection",
        "expansion",
        "scroll-position",
        "hierarchy",
        "interaction-velocity",
    }
    req(required_inputs.issubset(set(responsive.get("materialMayRespondTo", []))), "responsive material input set is incomplete")
    req(responsive.get("boundedAndDeterministic") is True, "material response must be bounded and deterministic")
    req(responsive.get("sourceImageryRequired") is False, "material response must not require source imagery")
    req(responsive.get("sourceImageryTransmissionAllowed") is False, "material response must not transmit source imagery")

    physical = contract.get("physicalInteractionResponse", {})
    req(physical.get("mustRemainSubtle") is True, "physical interaction response must remain subtle")
    req(physical.get("continuousRestlessAnimationAllowed") is False, "restless continuous material animation must be prohibited")
    req(physical.get("semanticStateMustRemainIndependentOfEffect") is True, "semantic state must remain independent of material effect")

    specular = contract.get("adaptiveSpecularLighting", {})
    req(specular.get("geometryAware") is True, "specular lighting must be geometry-aware")
    req(specular.get("genericWhiteBorderAsUniversalHighlight") is False, "generic white-border highlight must not become universal specular authority")
    req(specular.get("focusOutranksSpecular") is True, "focus must outrank specular lighting")
    req(specular.get("accessibilityOutranksSpecular") is True, "accessibility must outrank specular lighting")

    transmission = contract.get("environmentalTransmission", {})
    req(transmission.get("materialColorDistinctFromTransmittedColor") is True, "material color and transmitted color must remain distinct")
    req(transmission.get("materialRemainsPrimarilyNeutral") is True, "Living Material must remain primarily neutral")
    req(transmission.get("contextInfluenceMustRemainBounded") is True, "environmental transmission must remain bounded")
    req(transmission.get("consequentialSemanticSurfacesMayBeRecoloredByTransmission") is False, "transmission must not recolor consequential semantic surfaces")

    degradation = contract.get("degradation", {})
    req(degradation.get("order") == [3, 2, 1, 0], "material degradation order must remain Tier 3 → 2 → 1 → 0")
    tiers = degradation.get("tiers", {})
    req(tiers.get("3", {}).get("name") == "living-glaze", "Tier 3 must be Living Glaze")
    req(tiers.get("2", {}).get("name") == "responsive-glaze", "Tier 2 must be Responsive Glaze")
    req(tiers.get("1", {}).get("name") == "static-glaze", "Tier 1 must be Static Glaze")
    req(tiers.get("0", {}).get("name") == "solid", "Tier 0 must be Solid")
    never = set(degradation.get("neverSacrifice", []))
    req({"text", "interactive-target-size", "focus", "semantic-state", "semantic-meaning", "reading-order", "required-actions", "task-completion"}.issubset(never), "degradation never-sacrifice set is incomplete")

    governor = contract.get("performanceGovernor", {})
    req(governor.get("name") == "Glaze Performance Governor", "performance governor naming mismatch")
    req(governor.get("decisionScope") == "local-only", "performance governor must remain local-only")
    req(governor.get("telemetryRequired") is False, "performance governor must not require telemetry")
    req(governor.get("analyticsRequired") is False, "performance governor must not require analytics")
    req(governor.get("productionThresholdsEstablished") is False, "workstream must not invent production thresholds")
    req(governor.get("numericPerformanceBudgetsEstablished") is False, "workstream must not claim numeric performance budgets")
    expected_signals = {
        "frameTiming",
        "renderingCapability",
        "glazeRegionLoad",
        "windowLoad",
        "powerSaving",
        "animationPreference",
        "compositorCapability",
    }
    req(set(governor.get("acceptedQualitativeSignals", {})) == expected_signals, "performance governor qualitative signal set mismatch")
    rules = governor.get("rules", {})
    for key in (
        "forcedSolidMayBeSelectedByAccessibility",
        "reducedAnimationCapsConnectedMaterialMotion",
        "unknownSignalsUseDeterministicConservativeFallback",
    ):
        req(rules.get(key) is True, f"performance governor rule must be true: {key}")
    req(rules.get("governorMayUpgradeAboveRequestedTier") is False, "performance governor may not upgrade above requested tier")

    accessibility = contract.get("accessibility", {})
    precedence = accessibility.get("precedence", [])
    req(precedence[:4] == ["forced-colors", "reduced-transparency", "increased-contrast", "reduced-motion"], "material accessibility precedence is incomplete or reordered")

    tokens = load(TOKENS)
    req(tokens.get("product") == PRODUCT, "material token product identity mismatch")
    req(tokens.get("releaseLifecycle") == "proposed", "material tokens must remain Proposed")
    req(tokens.get("lifecycleAuthority") is False, "material tokens must not carry lifecycle authority")
    req(tokens.get("consumerEligible") is False, "material tokens must not be consumer eligible")
    req(tokens.get("namespace") == "material", "material token namespace mismatch")
    semantic = tokens.get("semanticTokens", {})
    for token in (
        "material.softGlaze",
        "material.glaze",
        "material.deepGlaze",
        "material.liveGlaze",
        "material.response.interaction",
        "material.specular",
        "material.transmission.environment",
        "material.performanceTier",
    ):
        req(token in semantic, f"missing Living Material 2.0 semantic token: {token}")

    implementations = tokens.get("implementationValues", {})
    for key, entry in implementations.items():
        if not isinstance(entry, dict):
            errors.append(f"material implementation entry {key!r} must be an object")
            continue
        source = entry.get("source")
        pointer = entry.get("pointer")
        if source:
            source_path = ROOT / source
            req(source_path.is_file(), f"material token source does not exist: {source}")
            if source_path.is_file() and pointer is not None:
                try:
                    resolve_pointer(load(source), pointer)
                except (KeyError, IndexError, ValueError, TypeError) as exc:
                    errors.append(f"material token pointer {pointer!r} does not resolve in {source}: {exc}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket("):
        req(forbidden not in runtime, f"Living Material runtime must remain local-only; forbidden network primitive found: {forbidden}")
    for required_symbol in (
        "resolveGlazePerformanceTier",
        "resolveLivingMaterial2",
        "applyLivingMaterial2",
        "createGlazePerformanceGovernor",
        "livingMaterial2Candidate",
    ):
        req(required_symbol in runtime, f"Living Material runtime missing required API: {required_symbol}")

    evidence = contract.get("evidenceBoundary", {})
    not_established = set(evidence.get("notEstablished", []))
    req("physical-device-performance" in not_established, "physical-device performance must remain explicitly unestablished")
    req("human-optical-acceptance" in not_established, "human optical acceptance must remain explicitly unestablished")
    req("stable" in not_established, "candidate artifact Stable claim must remain explicitly unestablished")
    req("consumer-conformance" in not_established, "consumer conformance must remain explicitly unestablished")

    if errors:
        print("GLAZE UI V1.3 Living Material 2.0 validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Living Material 2.0: PASS")
    print("Boundary: V1.3.0 remains current Stable; responsive material source provenance remains V1.2-derived while production-performance and V1.3.1 qualification claims remain unestablished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
