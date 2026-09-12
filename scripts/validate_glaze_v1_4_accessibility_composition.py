#!/usr/bin/env python3
"""Fail-closed validation for the Glaze UI V1.4 accessibility composition candidate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "v1.4" / "accessibility-composition.candidate.json"
RUNTIME = ROOT / "js" / "glaze-v1.4-accessibility-runtime.candidate.mjs"
BASE_RUNTIME = ROOT / "js" / "glaze-v1.4-optical-runtime.candidate.mjs"
BROWSER = ROOT / "js" / "glaze-v1.4-browser-capabilities.candidate.mjs"
WEB = ROOT / "js" / "glaze-v1.4-optical-web.candidate.mjs"
CSS = ROOT / "css" / "glaze-v1.4-optical-runtime.candidate.css"
REGRESSION = ROOT / "tests" / "glaze-v1.4-accessibility-composition.test.mjs"
VERSION = ROOT / "VERSION"

EXPECTED_REQUIREMENTS = [
    "reduced-transparency",
    "increased-contrast",
    "reduced-motion",
    "forced-colors",
    "large-text",
    "color-vision-accommodation",
    "low-power-performance-constrained",
]
EXPECTED_PRECEDENCE = [
    "reduced-transparency",
    "forced-colors",
    "increased-contrast",
    "reduced-motion",
    "low-power-performance-constrained",
    "large-text",
    "color-vision-accommodation",
    "standard",
]
EXPECTED_SOURCE_ARTIFACTS = {
    "semanticRuntime": "js/glaze-v1.4-optical-runtime.candidate.mjs",
    "compositionRuntime": "js/glaze-v1.4-accessibility-runtime.candidate.mjs",
    "browserAdapter": "js/glaze-v1.4-browser-capabilities.candidate.mjs",
    "webAdapter": "js/glaze-v1.4-optical-web.candidate.mjs",
    "webRenderer": "css/glaze-v1.4-optical-runtime.candidate.css",
    "regression": "tests/glaze-v1.4-accessibility-composition.test.mjs",
}


def fail(message: str) -> None:
    raise SystemExit(f"Glaze UI V1.4 accessibility composition validation failed: {message}")


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


def validate_contract(contract: dict) -> None:
    expected = {
        "schemaVersion": 1,
        "id": "goreecloud.glaze-ui.v1.4.accessibility-composition.candidate",
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
            fail(f"{key} drifted from candidate lifecycle boundary")

    if contract.get("sourceArtifacts") != EXPECTED_SOURCE_ARTIFACTS:
        fail("sourceArtifacts drifted")

    compatibility = contract.get("compatibility", {})
    for key in (
        "legacyAccessibilityProfileStillAccepted",
        "legacyAccessibilityProfileRemainsSummaryOnlyWhenRequirementsArePresent",
        "baseSemanticResolverRemainsAvailable",
        "v1_3EntrypointsPreserved",
        "stableVersionUnchangedByCandidate",
        "consumerAdoptionRequiresIndependentAcceptance",
    ):
        require_true(compatibility, key, "compatibility")

    request = contract.get("requestContract", {})
    if request.get("composableDimension") != "accessibilityRequirements":
        fail("accessibilityRequirements must remain the composable request dimension")
    for key in ("runtimeAcceptsArrayOrSet", "duplicateRequirementsCollapsed", "legacyProfileMergedIntoRequirements"):
        require_true(request, key, "requestContract")
    if request.get("unknownRequirementDisposition") != "substituted-and-ignored":
        fail("unknown requirements must fail closed through explicit substitution")

    if contract.get("supportedRequirements") != EXPECTED_REQUIREMENTS:
        fail("supported accessibility requirement vocabulary drifted")

    policy = contract.get("compositionPolicy", {})
    if policy.get("legacySummaryPrecedence") != EXPECTED_PRECEDENCE:
        fail("legacy summary precedence drifted")
    for key in (
        "simultaneousRequirementsPreserved",
        "requirementsAreBehaviorAuthority",
        "reducedTransparencyForcesDesignedSolidMaterial",
        "increasedContrastSuppressesOptionalAtmosphericEffects",
        "forcedColorsIncludesIncreasedContrastSemantics",
        "forcedColorsUsesSystemColorCompatibleWebTreatment",
        "reducedMotionDisablesOptionalMaterialMotion",
        "lowPowerPerformanceConstrainsToEfficientLevel",
        "largeTextMayNotHideOrClipRequiredContent",
        "colorVisionAccommodationRequiresNonChromaticStateCues",
        "contentCorrectnessPrecedesOptionalOptics",
        "allActiveRequirementsSurviveResolution",
    ):
        require_true(policy, key, "compositionPolicy")
    require_false(policy, "legacySummaryProfileIsBehaviorAuthority", "compositionPolicy")

    browser = contract.get("browserIntegration", {})
    for key in (
        "activeRequirementsRecordedIndependently",
        "forcedColorsPreservedAsIndependentRequirement",
        "recommendedLegacyProfileIsCompatibilitySummaryOnly",
    ):
        require_true(browser, key, "browserIntegration")
    require_false(browser, "knownMultipleRequirementsRequireConsumerSelection", "browserIntegration")
    require_false(browser, "preferenceDetectionIsQualificationEvidence", "browserIntegration")

    privacy = contract.get("privacyBoundary", {})
    if not privacy or any(value is not False for value in privacy.values()):
        fail("accessibility composition must not add privacy-invasive dependencies")

    qualification = contract.get("qualificationBoundary", {})
    for key in (
        "browserMatrixQualificationEstablished",
        "assistiveTechnologyQualificationEstablished",
        "physicalDeviceQualificationEstablished",
        "productionPerformanceQualificationEstablished",
    ):
        require_false(qualification, key, "qualificationBoundary")

    required_not_established = {
        "stable-v1.4-release",
        "consumer-v1.4-conformance",
        "frozen-v1.4-accessibility-composition-api",
        "browser-matrix-v1.4-qualification",
        "assistive-technology-v1.4-qualification",
        "physical-device-v1.4-qualification",
        "production-v1.4-performance-budgets",
        "native-v1.4-renderer-parity",
        "ecosystem-wide-v1.4-adoption",
    }
    values = contract.get("notEstablished")
    if not isinstance(values, list) or not required_not_established.issubset(values):
        fail("non-established lifecycle and qualification boundaries drifted")


def validate_sources() -> None:
    for path in (CONTRACT, RUNTIME, BASE_RUNTIME, BROWSER, WEB, CSS, REGRESSION, VERSION):
        if not path.is_file():
            fail(f"governed artifact missing: {path.relative_to(ROOT)}")
    if VERSION.read_text(encoding="utf-8").strip() != "1.3.0":
        fail("Stable VERSION must remain 1.3.0")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for required in (
        "export function resolveAccessibleOpticalRuntime",
        "export function createAccessibleOpticalRuntimeResolver",
        "export const accessibilityCompositionCandidate",
        "accessibilityRequirements",
        "forced-colors",
        "low-power-performance-constrained",
        "legacySummaryIsBehaviorAuthority: false",
    ):
        if required not in runtime:
            fail(f"composition runtime missing required boundary: {required}")

    browser = BROWSER.read_text(encoding="utf-8")
    if "activeAccessibilityRequirements" not in browser or "forced-colors" not in browser:
        fail("browser adapter must preserve independent accessibility requirements")

    web = WEB.read_text(encoding="utf-8")
    for required in (
        "resolveAccessibleOpticalRuntime",
        "glazeV14A11yReducedTransparency",
        "glazeV14A11yIncreasedContrast",
        "glazeV14A11yReducedMotion",
        "glazeV14A11yForcedColors",
        "glazeV14A11yPerformanceConstrained",
    ):
        if required not in web:
            fail(f"web adapter missing composable accessibility projection: {required}")

    css = CSS.read_text(encoding="utf-8")
    if '[data-glaze-v14-a11y-forced-colors="on"]' not in css:
        fail("web renderer must include forced-colors system-color-compatible treatment")
    if '[data-glaze-v14-a11y-increased-contrast="on"]' not in css:
        fail("web renderer must include independent increased-contrast treatment")


def main() -> None:
    validate_contract(load_json(CONTRACT))
    validate_sources()
    print("Glaze UI V1.4 accessibility composition candidate validation passed")


if __name__ == "__main__":
    main()
