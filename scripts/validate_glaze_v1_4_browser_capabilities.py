#!/usr/bin/env python3
"""Fail-closed validation for the Glaze UI V1.4 browser capability candidate."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "v1.4" / "browser-capabilities.candidate.json"
SEMANTIC_RUNTIME = ROOT / "contracts" / "v1.4" / "semantic-optical-runtime.candidate.json"
ADAPTER = ROOT / "js" / "glaze-v1.4-browser-capabilities.candidate.mjs"
REGRESSION = ROOT / "tests" / "glaze-v1.4-browser-capabilities.test.mjs"
HARNESS_HTML = ROOT / "reference" / "glaze-v1.4-browser-qualification.candidate.html"
HARNESS_RUNTIME = ROOT / "reference" / "glaze-v1.4-browser-qualification.candidate.mjs"
STABLE_CSS = ROOT / "css" / "glaze-v1.3.0.css"
STABLE_JS = ROOT / "js" / "glaze-v1.3.0.mjs"
VERSION = ROOT / "VERSION"

EXPECTED_SOURCE_ARTIFACTS = {
    "semanticRuntime": "contracts/v1.4/semantic-optical-runtime.candidate.json",
    "browserAdapter": "js/glaze-v1.4-browser-capabilities.candidate.mjs",
    "browserRegression": "tests/glaze-v1.4-browser-capabilities.test.mjs",
    "qualificationHarness": "reference/glaze-v1.4-browser-qualification.candidate.html",
    "qualificationHarnessRuntime": "reference/glaze-v1.4-browser-qualification.candidate.mjs",
}
EXPECTED_COMPATIBILITY = {
    "v1_3EntrypointsPreserved": True,
    "stableVersionUnchangedByCandidate": True,
    "automaticStableImportAllowed": False,
    "consumerAdoptionRequiresIndependentAcceptance": True,
}
EXPECTED_NEVER_AUTO = ["environmental-sampling", "reflection", "hdr-aware-luminance"]
EXPECTED_QUERIES = {
    "reducedTransparency": "(prefers-reduced-transparency: reduce)",
    "reducedMotion": "(prefers-reduced-motion: reduce)",
    "increasedContrast": "(prefers-contrast: more)",
    "forcedColors": "(forced-colors: active)",
    "darkAppearance": "(prefers-color-scheme: dark)",
}
EXPECTED_PRECEDENCE = [
    "reduced-transparency",
    "increased-contrast",
    "reduced-motion",
    "standard",
]
FORBIDDEN_SOURCE_PATTERNS = {
    "user-agent identity access": r"\.userAgent\b",
    "device-memory fingerprinting": r"\.deviceMemory\b",
    "hardware-concurrency fingerprinting": r"\.hardwareConcurrency\b",
    "battery-state access": r"getBattery\s*\(",
    "display capture": r"getDisplayMedia\s*\(",
    "camera or microphone access": r"getUserMedia\s*\(",
    "local persistent storage": r"\blocalStorage\b",
    "session storage": r"\bsessionStorage\b",
    "network fetch": r"\bfetch\s*\(",
    "XHR network access": r"\bXMLHttpRequest\b",
    "beacon transmission": r"\bsendBeacon\b",
    "websocket transmission": r"\bWebSocket\b",
}


def fail(message: str) -> None:
    raise SystemExit(f"Glaze UI V1.4 browser capability validation failed: {message}")


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
    expected_lifecycle = {
        "schemaVersion": 1,
        "id": "goreecloud.glaze-ui.v1.4.browser-capabilities.candidate",
        "targetVersion": "1.4.0-candidate",
        "releaseLifecycle": "proposed",
        "artifactLifecycle": "implementation-candidate-artifact",
        "lifecycleAuthority": False,
        "consumerEligible": False,
        "sourceStable": "1.3.0",
        "semanticApiStability": "candidate-not-frozen",
    }
    for key, value in expected_lifecycle.items():
        if contract.get(key) != value:
            fail(f"{key} drifted from the browser candidate lifecycle boundary")

    if contract.get("sourceArtifacts") != EXPECTED_SOURCE_ARTIFACTS:
        fail("sourceArtifacts drifted from governed browser candidate artifacts")
    if contract.get("compatibility") != EXPECTED_COMPATIBILITY:
        fail("V1.3 compatibility boundary drifted")

    detection = contract.get("detectionPolicy")
    if not isinstance(detection, dict):
        fail("detectionPolicy missing")
    for key in ("localOnly", "synchronousFeatureDetectionOnly", "failClosed", "unknownCapabilityIsUnsupported"):
        require_true(detection, key, "detectionPolicy")
    for key in (
        "userAgentSniffingAllowed",
        "hardwareFingerprintingAllowed",
        "batteryApiAllowed",
        "networkProbingAllowed",
        "screenCaptureAllowed",
        "cameraOrMicrophoneAccessAllowed",
        "persistentStorageAllowed",
        "telemetryAllowed",
        "analyticsAllowed",
    ):
        require_false(detection, key, "detectionPolicy")

    automatic = contract.get("automaticCapabilityDetection")
    if not isinstance(automatic, dict):
        fail("automaticCapabilityDetection missing")
    if automatic.get("neverAutoDeclare") != EXPECTED_NEVER_AUTO:
        fail("high-risk or non-provable capabilities must remain never-auto-declared")
    if automatic.get("derivedCapabilities", {}).get("adaptive-frost") != [
        "translucency", "backdrop-blur", "dynamic-opacity"
    ]:
        fail("adaptive-frost derivation boundary drifted")

    preferences = contract.get("accessibilityPreferenceDetection")
    if not isinstance(preferences, dict):
        fail("accessibilityPreferenceDetection missing")
    if preferences.get("queries") != EXPECTED_QUERIES:
        fail("browser preference query contract drifted")
    if preferences.get("recommendedProfilePrecedence") != EXPECTED_PRECEDENCE:
        fail("accessibility recommendation precedence drifted")
    require_true(preferences, "activePreferencesRecordedIndependently", "accessibilityPreferenceDetection")
    require_true(preferences, "forcedColorsMapsToIncreasedContrastRecommendation", "accessibilityPreferenceDetection")
    require_false(preferences, "recommendationIsQualificationEvidence", "accessibilityPreferenceDetection")
    require_true(preferences, "multipleActivePreferencesMayRequireConsumerPolicy", "accessibilityPreferenceDetection")

    privacy = contract.get("privacyBoundary")
    if not isinstance(privacy, dict):
        fail("privacyBoundary missing")
    for key, value in privacy.items():
        if value is not False:
            fail(f"privacyBoundary.{key} must remain false")

    harness = contract.get("qualificationHarness")
    if not isinstance(harness, dict) or harness.get("status") != "source-candidate":
        fail("qualificationHarness must remain source-candidate")
    if harness.get("purpose") != "local manual browser inspection and diagnostics":
        fail("qualification harness purpose drifted")
    for key in (
        "automaticQualificationDecision",
        "recordsBrowserIdentity",
        "recordsDeviceIdentity",
        "persistsResults",
        "transmitsResults",
        "browserMatrixQualificationEstablished",
        "assistiveTechnologyQualificationEstablished",
        "physicalDeviceQualificationEstablished",
        "productionPerformanceQualificationEstablished",
    ):
        require_false(harness, key, "qualificationHarness")

    required_not_established = {
        "stable-v1.4-release",
        "consumer-v1.4-conformance",
        "frozen-v1.4-browser-capability-api",
        "browser-matrix-v1.4-qualification",
        "assistive-technology-v1.4-qualification",
        "physical-device-v1.4-qualification",
        "production-v1.4-performance-budgets",
        "native-v1.4-renderer-parity",
        "ecosystem-wide-v1.4-adoption",
    }
    values = contract.get("notEstablished")
    if not isinstance(values, list) or not required_not_established.issubset(values):
        fail("browser candidate must preserve every non-established V1.4 boundary")


def validate_source_boundaries() -> None:
    for path in (
        CONTRACT,
        SEMANTIC_RUNTIME,
        ADAPTER,
        REGRESSION,
        HARNESS_HTML,
        HARNESS_RUNTIME,
        STABLE_CSS,
        STABLE_JS,
        VERSION,
    ):
        if not path.is_file():
            fail(f"governed artifact missing: {path.relative_to(ROOT)}")

    if VERSION.read_text(encoding="utf-8").strip() != "1.3.0":
        fail("Stable VERSION must remain 1.3.0 while V1.4 browser support is a candidate")

    semantic = load_json(SEMANTIC_RUNTIME)
    if semantic.get("id") != "goreecloud.glaze-ui.v1.4.semantic-optical-runtime.candidate":
        fail("browser adapter must build on the governed semantic optical runtime")
    if semantic.get("releaseLifecycle") != "proposed" or semantic.get("consumerEligible") is not False:
        fail("browser adapter cannot build on a semantic runtime claiming release authority")

    adapter_text = ADAPTER.read_text(encoding="utf-8")
    for required_export in (
        "export function detectBrowserOpticalCapabilities",
        "export function createBrowserOpticalCapabilityAdapter",
        "export const browserCapabilityCandidate",
    ):
        if required_export not in adapter_text:
            fail(f"browser adapter missing required export: {required_export}")

    harness_html = HARNESS_HTML.read_text(encoding="utf-8")
    harness_runtime = HARNESS_RUNTIME.read_text(encoding="utf-8")
    source = f"{adapter_text}\n{harness_runtime}"
    for label, pattern in FORBIDDEN_SOURCE_PATTERNS.items():
        if re.search(pattern, source):
            fail(f"browser candidate introduced forbidden {label}")

    if re.search(r"https?://", harness_html, flags=re.IGNORECASE):
        fail("qualification harness must not depend on remote resources")
    if "Candidate diagnostic only" not in harness_html or "does not establish browser qualification" not in harness_html:
        fail("qualification harness must visibly preserve its non-qualification boundary")
    if "glaze-v1.4-optical-runtime.candidate.css" not in harness_html:
        fail("qualification harness must use the bounded V1.4 candidate renderer")
    if "glaze-v1.4-browser-qualification.candidate.mjs" not in harness_html:
        fail("qualification harness runtime is not wired")

    for stable_path in (STABLE_CSS, STABLE_JS):
        if "glaze-v1.4" in stable_path.read_text(encoding="utf-8"):
            fail(f"Stable V1.3 entrypoint must not import V1.4 browser candidate: {stable_path.relative_to(ROOT)}")


def main() -> None:
    validate_contract(load_json(CONTRACT))
    validate_source_boundaries()
    print("Glaze UI V1.4 browser capability candidate validation passed")


if __name__ == "__main__":
    main()
