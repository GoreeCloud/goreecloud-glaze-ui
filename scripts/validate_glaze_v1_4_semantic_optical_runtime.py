#!/usr/bin/env python3
"""Fail-closed validation for the Glaze UI V1.4 semantic optical runtime candidate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "v1.4" / "semantic-optical-runtime.candidate.json"
OPTICAL = ROOT / "tokens" / "glaze-v1.4-optical-material.candidate.json"
RUNTIME = ROOT / "js" / "glaze-v1.4-optical-runtime.candidate.mjs"
RUNTIME_TEST = ROOT / "tests" / "glaze-v1.4-optical-runtime.test.mjs"
WEB_ADAPTER = ROOT / "js" / "glaze-v1.4-optical-web.candidate.mjs"
WEB_RENDERER = ROOT / "css" / "glaze-v1.4-optical-runtime.candidate.css"
WEB_TEST = ROOT / "tests" / "glaze-v1.4-optical-web.test.mjs"
STABLE_WEB_ENTRYPOINT = ROOT / "css" / "glaze-v1.3.0.css"
VERSION = ROOT / "VERSION"

EXPECTED_REQUEST_DIMENSIONS = [
    "materialRole",
    "elevationRole",
    "interactionState",
    "appearanceMode",
    "accessibilityProfile",
    "performanceLevel",
    "environmentalResponse",
    "platformCapabilities",
]
EXPECTED_RESULT_FIELDS = [
    "requested",
    "accepted",
    "disposition",
    "reasons",
    "effectiveOpticalProfile",
    "capabilityEvidence",
    "fallbacks",
]
EXPECTED_DISPOSITIONS = ["accepted", "downgraded", "substituted", "rejected"]
EXPECTED_MATERIAL_ROLES = {
    "glz.material.canvas",
    "glz.material.surface",
    "glz.material.softGlaze",
    "glz.material.glaze",
    "glz.material.deepGlaze",
    "glz.material.liveGlaze",
}
EXPECTED_FROST_ROLES = {
    "glz.frost.clear",
    "glz.frost.mist",
    "glz.frost.standard",
    "glz.frost.dense",
    "glz.frost.opaque",
}
EXPECTED_ELEVATION_ROLES = {
    "glz.elevation.embedded",
    "glz.elevation.raised",
    "glz.elevation.interactive",
    "glz.elevation.floating",
    "glz.elevation.modal",
    "glz.elevation.focus",
}
EXPECTED_CAPABILITIES = {
    "backdrop-blur",
    "translucency",
    "dynamic-opacity",
    "environmental-sampling",
    "reflection",
    "adaptive-frost",
    "aura",
    "edge-illumination",
    "material-aware-motion",
    "connected-transformation",
    "shadow-diffusion",
    "hdr-aware-luminance",
    "reduced-transparency",
    "increased-contrast",
    "reduced-motion",
}
EXPECTED_ACCESSIBILITY_PROFILES = {
    "standard",
    "reduced-transparency",
    "increased-contrast",
    "reduced-motion",
    "large-text",
    "color-vision-accommodation",
    "low-power-performance-constrained",
}
EXPECTED_PERFORMANCE_LEVELS = {"full", "balanced", "efficient"}
EXPECTED_TRUTH_AUTHORITIES = {
    "security": "Wardveil Security",
    "privacy": "Privacy Shield",
    "identity": "GoreeCloud Identity",
    "recovery": "Everkeep",
    "applicationState": "owning GoreeCloud application or service",
}
EXPECTED_SOURCE_ARTIFACTS = {
    "opticalMaterial": "tokens/glaze-v1.4-optical-material.candidate.json",
    "runtimeResolver": "js/glaze-v1.4-optical-runtime.candidate.mjs",
    "runtimeRegression": "tests/glaze-v1.4-optical-runtime.test.mjs",
    "webAdapter": "js/glaze-v1.4-optical-web.candidate.mjs",
    "webRenderer": "css/glaze-v1.4-optical-runtime.candidate.css",
    "webRegression": "tests/glaze-v1.4-optical-web.test.mjs",
}
EXPECTED_WEB_RENDERER = {
    "implementationStatus": "source-candidate",
    "runtimeAdapter": "js/glaze-v1.4-optical-web.candidate.mjs",
    "stylesheet": "css/glaze-v1.4-optical-runtime.candidate.css",
    "activation": "accepted-runtime-data-attributes",
    "importsStableV1_3": True,
    "automaticallyIncludedByStableEntrypoint": False,
    "directRawOpticalConsumerContract": False,
    "remoteAssetsRequired": False,
    "environmentalSamplingImplemented": False,
    "browserQualificationEstablished": False,
    "assistiveTechnologyQualificationEstablished": False,
    "productionPerformanceQualificationEstablished": False,
    "nativeRendererParityEstablished": False,
}


def fail(message: str) -> None:
    raise SystemExit(f"Glaze UI V1.4 semantic optical runtime validation failed: {message}")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)} is unreadable or invalid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require_true(container: dict, key: str, scope: str) -> None:
    if container.get(key) is not True:
        fail(f"{scope}.{key} must remain true")


def require_false(container: dict, key: str, scope: str) -> None:
    if container.get(key) is not False:
        fail(f"{scope}.{key} must remain false")


def validate_lifecycle(contract: dict) -> None:
    expected = {
        "schemaVersion": 1,
        "id": "goreecloud.glaze-ui.v1.4.semantic-optical-runtime.candidate",
        "targetVersion": "1.4.0-candidate",
        "releaseLifecycle": "proposed",
        "artifactLifecycle": "implementation-candidate-artifact",
        "lifecycleAuthority": False,
        "consumerEligible": False,
        "sourceStable": "1.3.0",
        "semanticApiStability": "candidate-not-frozen",
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            fail(f"{key} drifted from the candidate lifecycle boundary")

    compatibility = contract.get("compatibility")
    if not isinstance(compatibility, dict):
        fail("compatibility contract missing")
    expected_compatibility = {
        "v1_3ContractsPreserved": True,
        "v1_3TokensRenamed": False,
        "v1_3TokensRemoved": False,
        "stableVersionUnchangedByCandidate": True,
        "consumerAdoptionRequiresIndependentAcceptance": True,
    }
    if compatibility != expected_compatibility:
        fail("V1.3 compatibility boundary drifted")


def validate_resolution(contract: dict) -> None:
    resolution = contract.get("resolutionContract")
    if not isinstance(resolution, dict):
        fail("resolutionContract missing")
    if resolution.get("requestDimensions") != EXPECTED_REQUEST_DIMENSIONS:
        fail("semantic request dimensions drifted")
    if resolution.get("resultFields") != EXPECTED_RESULT_FIELDS:
        fail("runtime result fields drifted")
    if resolution.get("dispositions") != EXPECTED_DISPOSITIONS:
        fail("runtime disposition vocabulary drifted")
    for key in (
        "noImplicitAcceptance",
        "unknownCapabilityIsUnsupported",
        "contentCorrectnessPrecedesOptics",
        "accessibilityPrecedesOptionalOptics",
        "acceptedStateMustReflectRuntimeReality",
    ):
        require_true(resolution, key, "resolutionContract")


def validate_semantic_roles(contract: dict, optical_profiles: set[str]) -> None:
    material_roles = contract.get("semanticMaterialRoles")
    if not isinstance(material_roles, dict) or set(material_roles) != EXPECTED_MATERIAL_ROLES:
        fail("semantic material role vocabulary is incomplete")
    for role, definition in material_roles.items():
        if not isinstance(definition, dict):
            fail(f"material role {role} must be an object")
        if definition.get("opticalProfile") not in optical_profiles:
            fail(f"material role {role} references an unknown optical profile")
        if not isinstance(definition.get("intent"), str) or not definition["intent"]:
            fail(f"material role {role} must declare intent")
    live = material_roles["glz.material.liveGlaze"]
    optional = set(live.get("optionalCapabilities", []))
    if optional != {"environmental-sampling", "dynamic-opacity", "adaptive-frost"}:
        fail("liveGlaze optional capability boundary drifted")

    frost_roles = contract.get("frostRoles")
    if not isinstance(frost_roles, dict) or set(frost_roles) != EXPECTED_FROST_ROLES:
        fail("frost role vocabulary is incomplete")
    for role, definition in frost_roles.items():
        if not isinstance(definition, dict):
            fail(f"frost role {role} must be an object")
        rendering_class = definition.get("renderingClass")
        if role == "glz.frost.opaque":
            if rendering_class != "solid" or definition.get("fallback") != "solid-semantic-surface":
                fail("opaque frost must remain a designed solid semantic material")
        elif rendering_class != "optical" or definition.get("opticalProfile") not in optical_profiles:
            fail(f"frost role {role} must reference a known optical profile")

    elevation_roles = contract.get("elevationRoles")
    if not isinstance(elevation_roles, dict) or set(elevation_roles) != EXPECTED_ELEVATION_ROLES:
        fail("elevation role vocabulary is incomplete")
    for role, definition in elevation_roles.items():
        if not isinstance(definition, dict) or definition.get("profileInfluence") not in optical_profiles:
            fail(f"elevation role {role} references an unknown optical profile")


def validate_capabilities(contract: dict) -> None:
    capabilities = contract.get("runtimeCapabilities")
    if not isinstance(capabilities, list) or set(capabilities) != EXPECTED_CAPABILITIES:
        fail("runtime capability vocabulary is incomplete")
    if len(capabilities) != len(EXPECTED_CAPABILITIES):
        fail("runtime capability vocabulary contains duplicates")

    rules = contract.get("capabilityRules")
    if not isinstance(rules, dict):
        fail("capabilityRules missing")
    require_true(rules, "runtimeMustDeclareCapabilities", "capabilityRules")
    require_false(rules, "undeclaredCapabilitiesAccepted", "capabilityRules")
    require_true(rules, "requiredContentMayNotDependOnOptionalOptics", "capabilityRules")
    require_true(rules, "fullOpticalStatusRequiresAcceptedRuntimeCapabilities", "capabilityRules")
    if rules.get("unsupportedFeatureDisposition") != "downgraded-or-substituted":
        fail("unsupported feature disposition must remain fail-soft and explicit")


def validate_accessibility_and_performance(contract: dict) -> None:
    profiles = contract.get("accessibilityProfiles")
    if not isinstance(profiles, dict) or set(profiles) != EXPECTED_ACCESSIBILITY_PROFILES:
        fail("accessibility profile vocabulary is incomplete")
    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            fail(f"accessibility profile {name} must be an object")
        if not isinstance(profile.get("mode"), str) or not profile["mode"]:
            fail(f"accessibility profile {name} must declare a mode")
        if not isinstance(profile.get("requiredBehavior"), str) or not profile["requiredBehavior"]:
            fail(f"accessibility profile {name} must declare required behavior")
    if profiles["reduced-transparency"].get("mode") != "force-solid-capable":
        fail("reduced transparency must preserve a designed solid path")
    if profiles["reduced-motion"].get("mode") != "continuity-without-decorative-motion":
        fail("reduced motion must preserve continuity without decorative motion")

    levels = contract.get("performanceLevels")
    if not isinstance(levels, dict) or set(levels) != EXPECTED_PERFORMANCE_LEVELS:
        fail("performance level vocabulary drifted")
    qualification = contract.get("performanceQualification")
    if not isinstance(qualification, dict):
        fail("performanceQualification missing")
    for key in (
        "productionNumericBudgetsEstablished",
        "physicalDeviceQualificationEstablished",
        "nativeRendererParityEstablished",
    ):
        require_false(qualification, key, "performanceQualification")
    downgrade = qualification.get("downgradeOrder")
    if not isinstance(downgrade, list) or not downgrade or downgrade[-1] != "translucency":
        fail("performance downgrade order must preserve a final solid-material escape hatch")


def validate_privacy_and_compositor(contract: dict) -> None:
    sampling = contract.get("environmentalSampling")
    if not isinstance(sampling, dict):
        fail("environmentalSampling policy missing")
    if sampling.get("defaultDisposition") != "disabled-until-accepted":
        fail("environmental sampling must fail closed by default")
    for key in ("localOnly", "ephemeral", "purposeLimited", "minimumPracticalRegion"):
        require_true(sampling, key, "environmentalSampling")
    for key in (
        "remotePixelTransmissionAllowed",
        "remoteDerivedColorTransmissionAllowed",
        "persistentHistoryAllowed",
        "analyticsCaptureAllowed",
        "generalScreenshotPermissionRequired",
        "generalScreenRecordingPermissionRequired",
        "protectedSurfaceSamplingAllowed",
        "privacyRestrictedSurfaceSamplingAllowed",
    ):
        require_false(sampling, key, "environmentalSampling")
    if sampling.get("fallbackWhenUnavailable") != "governed-static-semantic-material":
        fail("environmental sampling must have a governed static fallback")

    compositor = contract.get("compositorPolicy")
    if not isinstance(compositor, dict):
        fail("compositorPolicy missing")
    require_false(compositor, "nestedBackdropBlurDefaultAllowed", "compositorPolicy")
    require_false(compositor, "automaticFullStrengthChildMaterialAllowed", "compositorPolicy")
    require_true(compositor, "contentCorrectnessPrecedesEffects", "compositorPolicy")
    require_true(compositor, "accessibilityPrecedesEffects", "compositorPolicy")
    require_false(compositor, "productionNumericLayerBudgetEstablished", "compositorPolicy")


def validate_web_renderer(contract: dict) -> None:
    renderer = contract.get("webReferenceRenderer")
    if renderer != EXPECTED_WEB_RENDERER:
        fail("webReferenceRenderer boundary drifted")

    for path in (WEB_ADAPTER, WEB_RENDERER, WEB_TEST, STABLE_WEB_ENTRYPOINT):
        if not path.is_file():
            fail(f"governed web artifact missing: {path.relative_to(ROOT)}")

    adapter_text = WEB_ADAPTER.read_text(encoding="utf-8")
    for required_export in (
        "export function applyResolvedOpticalWebState",
        "export function applyOpticalWebRuntime",
        "export function createOpticalWebAdapter",
        "export const opticalWebCandidate",
    ):
        if required_export not in adapter_text:
            fail(f"web adapter is missing required export: {required_export}")

    renderer_text = WEB_RENDERER.read_text(encoding="utf-8")
    if '@import url("./glaze-v1.3.0.css");' not in renderer_text:
        fail("web renderer must build on the Stable V1.3 web entrypoint")
    if "http://" in renderer_text or "https://" in renderer_text:
        fail("web renderer must not require remote assets or styles")
    for profile in ("subdued", "standard", "elevated", "transient", "deep"):
        if f'[data-glaze-v14-profile="{profile}"]' not in renderer_text:
            fail(f"web renderer is missing profile selector: {profile}")
    for mode in ("optical-glaze", "static-glaze", "solid-semantic-surface"):
        if f'[data-glaze-v14-rendering="{mode}"]' not in renderer_text:
            fail(f"web renderer is missing rendering-mode selector: {mode}")

    stable_text = STABLE_WEB_ENTRYPOINT.read_text(encoding="utf-8")
    if "glaze-v1.4" in stable_text:
        fail("Stable V1.3 web entrypoint must not import the V1.4 candidate renderer")


def validate_truth_authority(contract: dict) -> None:
    truth = contract.get("truthAuthority")
    if not isinstance(truth, dict):
        fail("truthAuthority missing")
    require_false(truth, "visualLayerIsOperationalAuthority", "truthAuthority")
    if truth.get("authorities") != EXPECTED_TRUTH_AUTHORITIES:
        fail("operational truth authority mapping drifted")
    rules = truth.get("rules")
    if not isinstance(rules, list) or len(rules) < 5 or any(not isinstance(rule, str) or not rule for rule in rules):
        fail("truth authority rules are incomplete")


def validate_not_established(contract: dict) -> None:
    values = contract.get("notEstablished")
    required = {
        "stable-v1.4-release",
        "consumer-v1.4-conformance",
        "frozen-v1.4-semantic-api",
        "production-v1.4-performance-budgets",
        "physical-device-v1.4-qualification",
        "browser-v1.4-renderer-qualification",
        "native-v1.4-renderer-parity",
        "ecosystem-wide-v1.4-adoption",
    }
    if not isinstance(values, list) or not required.issubset(values):
        fail("candidate must explicitly preserve all non-established V1.4 boundaries")


def validate_runtime_artifacts() -> None:
    for path in (RUNTIME, RUNTIME_TEST):
        if not path.is_file():
            fail(f"governed runtime artifact missing: {path.relative_to(ROOT)}")
    runtime_text = RUNTIME.read_text(encoding="utf-8")
    for required_export in (
        "export function resolveOpticalRuntime",
        "export function applyOpticalRuntime",
        "export function createOpticalRuntimeResolver",
        "export const opticalRuntimeCandidate",
    ):
        if required_export not in runtime_text:
            fail(f"runtime resolver is missing required export: {required_export}")


def validate_contract(contract: dict, optical: dict) -> None:
    validate_lifecycle(contract)
    source = contract.get("sourceArtifacts")
    if source != EXPECTED_SOURCE_ARTIFACTS:
        fail("semantic runtime source artifact authority drifted")
    profiles = optical.get("opticalProfiles")
    if not isinstance(profiles, dict) or not profiles:
        fail("optical-material source has no profiles")
    validate_resolution(contract)
    validate_semantic_roles(contract, set(profiles))
    validate_capabilities(contract)
    validate_accessibility_and_performance(contract)
    validate_privacy_and_compositor(contract)
    validate_web_renderer(contract)
    validate_truth_authority(contract)
    validate_not_established(contract)


def validate_repository_boundary(optical: dict) -> None:
    try:
        version = VERSION.read_text(encoding="utf-8").strip()
    except OSError as exc:
        fail(f"VERSION is unreadable: {exc}")
    if version != "1.3.0":
        fail("stable VERSION must remain 1.3.0 while V1.4 is a candidate")
    if optical.get("id") != "goreecloud.glaze-ui.v1.4.optical-material.tokens.candidate":
        fail("canonical V1.4 optical-material source identity drifted")
    if optical.get("releaseLifecycle") != "proposed" or optical.get("consumerEligible") is not False:
        fail("semantic runtime cannot build on an optical source claiming release authority")


def main() -> None:
    optical = load_json(OPTICAL)
    validate_repository_boundary(optical)
    validate_runtime_artifacts()
    validate_contract(load_json(CONTRACT), optical)
    print("Glaze UI V1.4 semantic optical runtime candidate validation passed")


if __name__ == "__main__":
    main()
