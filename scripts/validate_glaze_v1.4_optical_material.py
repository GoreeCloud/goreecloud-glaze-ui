#!/usr/bin/env python3
"""Fail-closed source validation for the Glaze UI V1.4 optical-material candidate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "tokens" / "glaze-v1.4-optical-material.candidate.json"
VERSION = ROOT / "VERSION"
V13_MATERIAL = ROOT / "tokens" / "glaze-v1.3-material.candidate.json"

EXPECTED_RANGES = {
    "surface.opticalDepth": (0.18, 0.36),
    "surface.diffusion": (0.42, 0.68),
    "surface.refraction": (0.20, 0.48),
    "surface.colorBleed": (0.08, 0.22),
    "surface.highlightRim": (0.06, 0.14),
    "surface.shadowDepth": (0.14, 0.28),
}
EXPECTED_PROPERTIES = set(EXPECTED_RANGES) | {
    "surface.ambientTint",
    "surface.concentration",
}
EXPECTED_LAYERS = [
    "base-surface",
    "ambient-tint",
    "diffusion",
    "concentration",
    "depth",
]
EXPECTED_COMPONENTS = {
    "surface",
    "elevated-surface",
    "panel",
    "side-panel",
    "shelf",
    "menu",
    "popover",
    "menu-bar",
    "card",
    "list-row",
    "search-field",
    "selector",
    "toolbar",
    "header",
    "footer",
    "dialog",
    "toast",
}


def fail(message: str) -> None:
    raise SystemExit(f"Glaze UI V1.4 optical-material validation failed: {message}")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)} is unreadable or invalid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def validate_candidate(candidate: dict) -> None:
    if candidate.get("schemaVersion") != 1:
        fail("schemaVersion must remain 1 for this candidate contract")
    if candidate.get("id") != "goreecloud.glaze-ui.v1.4.optical-material.tokens.candidate":
        fail("candidate identity drifted")
    if candidate.get("targetVersion") != "1.4.0-candidate":
        fail("targetVersion must remain 1.4.0-candidate")
    if candidate.get("releaseLifecycle") != "proposed":
        fail("candidate cannot claim a stable lifecycle")
    if candidate.get("artifactLifecycle") != "implementation-candidate-artifact":
        fail("candidate artifact lifecycle drifted")
    if candidate.get("lifecycleAuthority") is not False:
        fail("candidate cannot grant lifecycle authority")
    if candidate.get("consumerEligible") is not False:
        fail("candidate cannot grant consumer eligibility")
    if candidate.get("sourceStable") != "1.3.0":
        fail("V1.4 candidate must build from stable 1.3.0")

    compatibility = candidate.get("compatibility")
    if not isinstance(compatibility, dict):
        fail("compatibility contract missing")
    expected_compatibility = {
        "v1_3ContractsPreserved": True,
        "v1_3TokensRenamed": False,
        "v1_3TokensRemoved": False,
        "consumerAdoptionRequired": True,
        "stableVersionUnchangedByCandidate": True,
    }
    if compatibility != expected_compatibility:
        fail("V1.3 compatibility boundary drifted")

    optical_engine = candidate.get("opticalEngine")
    if not isinstance(optical_engine, dict):
        fail("opticalEngine is missing")
    if optical_engine.get("layers") != EXPECTED_LAYERS:
        fail("optical-engine layer order drifted")
    if optical_engine.get("orderIsNormative") is not True:
        fail("optical-engine layer order must remain normative")
    if optical_engine.get("nestedBackdropBlurDefaultAllowed") is not False:
        fail("nested backdrop blur must remain disabled by default")
    if optical_engine.get("accessibilityMayForceSolidFallback") is not True:
        fail("accessibility must be able to force a solid fallback")
    if optical_engine.get("materialEffectsDegradeBeforeContentCorrectness") is not True:
        fail("material effects must degrade before content correctness")

    properties = candidate.get("propertyContracts")
    if not isinstance(properties, dict) or set(properties) != EXPECTED_PROPERTIES:
        fail("optical property vocabulary drifted")
    for name, (minimum, maximum) in EXPECTED_RANGES.items():
        contract = properties.get(name)
        if not isinstance(contract, dict):
            fail(f"{name} contract missing")
        if contract.get("type") != "number":
            fail(f"{name} must remain numeric")
        if contract.get("minimum") != minimum or contract.get("maximum") != maximum:
            fail(f"{name} initial target range drifted")
    if properties["surface.ambientTint"].get("type") != "context-derived-color":
        fail("surface.ambientTint must remain context-derived")
    if properties["surface.concentration"].get("type") != "derived-number":
        fail("surface.concentration must remain derived")

    profiles = candidate.get("opticalProfiles")
    if not isinstance(profiles, dict) or not profiles:
        fail("opticalProfiles must be non-empty")
    numeric_profile_fields = {
        "opticalDepth": "surface.opticalDepth",
        "diffusion": "surface.diffusion",
        "refraction": "surface.refraction",
        "colorBleed": "surface.colorBleed",
        "highlightRim": "surface.highlightRim",
        "shadowDepth": "surface.shadowDepth",
    }
    expected_profile_fields = set(numeric_profile_fields) | {"ambientTint", "concentration"}
    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict) or set(profile) != expected_profile_fields:
            fail(f"optical profile {profile_name} fields drifted")
        for field, contract_name in numeric_profile_fields.items():
            value = profile.get(field)
            minimum, maximum = EXPECTED_RANGES[contract_name]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                fail(f"optical profile {profile_name}.{field} must be numeric")
            if not minimum <= float(value) <= maximum:
                fail(f"optical profile {profile_name}.{field} is outside its candidate range")
        if profile.get("ambientTint") != "context-derived":
            fail(f"optical profile {profile_name} ambientTint must be context-derived")
        if profile.get("concentration") != "derived-from-optical-depth":
            fail(f"optical profile {profile_name} concentration must derive from opticalDepth")

    components = candidate.get("componentProfiles")
    if not isinstance(components, dict) or set(components) != EXPECTED_COMPONENTS:
        fail("component optical-profile coverage is incomplete")
    for component, profile in components.items():
        if not isinstance(profile, dict) or set(profile) != {
            "opticalProfile", "cornerRadiusToken", "motionProfile"
        }:
            fail(f"component profile {component} fields drifted")
        if profile.get("opticalProfile") not in profiles:
            fail(f"component profile {component} references an unknown optical profile")
        if profile.get("cornerRadiusToken") != "inherited-v1.3":
            fail(f"component profile {component} must preserve V1.3 radius semantics")
        if profile.get("motionProfile") != "inherited-v1.3":
            fail(f"component profile {component} must preserve V1.3 motion semantics")

    fallbacks = candidate.get("fallbacks")
    if not isinstance(fallbacks, dict):
        fail("fallback contract missing")
    for key in ("reducedTransparency", "reducedMotion", "lowPerformanceTier", "unsupportedRefraction"):
        value = fallbacks.get(key)
        if not isinstance(value, str) or not value:
            fail(f"fallback {key} must be declared")

    not_established = candidate.get("notEstablished")
    if not isinstance(not_established, list) or "stable-v1.4-release" not in not_established:
        fail("candidate must explicitly deny stable V1.4 release status")
    if "consumer-v1.4-conformance" not in not_established:
        fail("candidate must explicitly deny consumer V1.4 conformance")


def validate_repository_boundary() -> None:
    try:
        version = VERSION.read_text(encoding="utf-8").strip()
    except OSError as exc:
        fail(f"VERSION is unreadable: {exc}")
    if version != "1.3.0":
        fail("stable VERSION must remain 1.3.0 while V1.4 is only a candidate")
    v13 = load_json(V13_MATERIAL)
    if v13.get("id") != "goreecloud.glaze-ui.v1.3.material.tokens.candidate":
        fail("V1.3 material predecessor identity drifted")
    if v13.get("targetVersion") != "1.3.0-candidate":
        fail("V1.3 material predecessor targetVersion drifted")


def main() -> None:
    validate_repository_boundary()
    validate_candidate(load_json(CANDIDATE))
    print("Glaze UI V1.4 optical-material candidate validation passed")


if __name__ == "__main__":
    main()
