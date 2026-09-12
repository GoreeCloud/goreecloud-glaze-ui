#!/usr/bin/env python3
"""Fail-closed validation for the Glaze UI V1.4 accessibility qualification support slice."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json"
SCHEMA = ROOT / "contracts" / "v1.4" / "accessibility-qualification-evidence.schema.candidate.json"
COMPOSITION = ROOT / "contracts" / "v1.4" / "accessibility-composition.candidate.json"
EVALUATOR = ROOT / "scripts" / "evaluate_glaze_v1_4_accessibility_qualification.py"
PACKET_GENERATOR = ROOT / "scripts" / "prepare_glaze_v1_4_accessibility_qualification_packet.py"
OBSERVATION_CAPTURE = ROOT / "js" / "glaze-v1.4-accessibility-observation-capture.candidate.mjs"
OBSERVATION_REFERENCE = ROOT / "reference" / "glaze-v1.4-accessibility-observation-capture.candidate.html"
OBSERVATION_REFERENCE_RUNTIME = ROOT / "reference" / "glaze-v1.4-accessibility-observation-capture.candidate.mjs"
TEMPLATE = ROOT / "evidence" / "v1.4" / "templates" / "accessibility-qualification-record.candidate.json"
REGRESSION = ROOT / "tests" / "test_glaze_v1_4_accessibility_qualification.py"
PACKET_REGRESSION = ROOT / "tests" / "test_glaze_v1_4_accessibility_qualification_packet.py"
OBSERVATION_REGRESSION = ROOT / "tests" / "glaze-v1.4-accessibility-observation-capture.test.mjs"
VERSION = ROOT / "VERSION"

EXPECTED_REQUIRED_SCENARIOS = [
    "source-and-runtime-identity",
    "multi-preference-composition",
    "reduced-transparency-solid-fallback",
    "increased-contrast-separation",
    "reduced-motion-motion-suppression",
    "forced-colors-system-color-path",
    "large-text-zoom-reflow",
    "keyboard-focus-order",
    "color-independent-semantic-state",
]
EXPECTED_CONDITIONAL = {
    "screenReaderClaimed": "screen-reader-semantics-and-announcements",
    "voiceControlClaimed": "voice-control-purpose-and-operation",
    "switchControlClaimed": "switch-control-operability",
}
EXPECTED_SOURCE_ARTIFACTS = {
    "accessibilityComposition": "contracts/v1.4/accessibility-composition.candidate.json",
    "evidenceSchema": "contracts/v1.4/accessibility-qualification-evidence.schema.candidate.json",
    "evaluator": "scripts/evaluate_glaze_v1_4_accessibility_qualification.py",
    "packetGenerator": "scripts/prepare_glaze_v1_4_accessibility_qualification_packet.py",
    "observationCaptureRuntime": "js/glaze-v1.4-accessibility-observation-capture.candidate.mjs",
    "observationCaptureReference": "reference/glaze-v1.4-accessibility-observation-capture.candidate.html",
    "observationCaptureReferenceRuntime": "reference/glaze-v1.4-accessibility-observation-capture.candidate.mjs",
    "validator": "scripts/validate_glaze_v1_4_accessibility_qualification.py",
    "recordTemplate": "evidence/v1.4/templates/accessibility-qualification-record.candidate.json",
    "regression": "tests/test_glaze_v1_4_accessibility_qualification.py",
    "packetRegression": "tests/test_glaze_v1_4_accessibility_qualification_packet.py",
    "observationCaptureRegression": "tests/glaze-v1.4-accessibility-observation-capture.test.mjs",
}


def fail(message: str) -> None:
    raise SystemExit(f"Glaze UI V1.4 accessibility qualification validation failed: {message}")


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


def validate_plan(plan: dict) -> None:
    expected = {
        "schemaVersion": 1,
        "id": "goreecloud.glaze-ui.v1.4.accessibility-qualification.candidate",
        "targetVersion": "1.4.0-candidate",
        "releaseLifecycle": "proposed",
        "artifactLifecycle": "qualification-support-candidate",
        "lifecycleAuthority": False,
        "consumerEligible": False,
        "sourceStable": "1.3.0",
        "qualificationApiStability": "candidate-not-frozen",
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            fail(f"{key} drifted from candidate qualification boundary")
    if plan.get("sourceArtifacts") != EXPECTED_SOURCE_ARTIFACTS:
        fail("sourceArtifacts drifted from governed qualification support artifacts")
    if plan.get("evaluatorDispositions") != ["blocked", "review-ready", "failed", "accepted"]:
        fail("evaluator disposition vocabulary drifted")
    if plan.get("requiredScenarios") != EXPECTED_REQUIRED_SCENARIOS:
        fail("required scenario vocabulary drifted")
    if plan.get("claimConditionalScenarios") != EXPECTED_CONDITIONAL:
        fail("claim-conditional scenario mapping drifted")

    policy = plan.get("evaluationPolicy", {})
    for key in (
        "exactSourceRevisionRequired",
        "exactSourceTreeRevisionRequired",
        "sourceAndTreeMustBeNonPlaceholderForReviewReadyOrAccepted",
        "deterministicEvaluation",
        "failClosed",
        "humanOrCombinedReviewRequiredForAcceptance",
        "unresolvedHighOrCriticalIssueBlocksAcceptance",
        "passScenarioRequiresEvidenceReferences",
        "allRequiredScenariosMustPass",
        "allClaimedAssistiveTechnologyScenariosMustPass",
        "acceptedAccessibilityQualificationDoesNotGrantLifecycleGate",
    ):
        require_true(policy, key, "evaluationPolicy")
    for key in (
        "evaluatorMayMutateEvidence",
        "evaluatorMayGrantHumanAcceptance",
        "evaluatorMayGrantLifecycleStatus",
        "automatedFeatureDetectionIsQualificationEvidence",
        "automatedRegressionPassingIsQualificationEvidence",
    ):
        require_false(policy, key, "evaluationPolicy")

    packet = plan.get("packetPreparationPolicy", {})
    for key in (
        "exactSourceRevisionRequired",
        "exactSourceTreeRevisionRequired",
        "outputRestrictedToQualificationDraftArea",
        "claimedAssistiveTechnologyScenarioStartsNotTested",
        "unclaimedAssistiveTechnologyScenarioStartsNotApplicable",
        "acceptedEvidenceRequiresSeparateGovernedReview",
    ):
        require_true(packet, key, "packetPreparationPolicy")
    for key in (
        "preparedAcceptedForAccessibilityQualification",
        "preparedAcceptedForLifecycleGate",
        "preparedPacketMayFabricateEvidenceReferences",
        "preparedPacketMayFabricateScenarioPassOrFail",
    ):
        require_false(packet, key, "packetPreparationPolicy")
    if packet.get("preparedStatus") != "in-progress":
        fail("prepared packet status must remain in-progress")
    if packet.get("preparedHumanReviewStatus") != "pending":
        fail("prepared packet human review must remain pending")
    if packet.get("preparedEvaluatorDisposition") != "blocked":
        fail("prepared packet evaluator disposition must remain blocked")

    capture = plan.get("observationCapturePolicy", {})
    for key in (
        "preparedOrInProgressExactBoundRecordRequired",
        "localDetectionMayOnlyProvideHints",
        "reviewerConfirmationRequiredForTestedPreference",
        "reviewerEvidenceReferenceRequiredForTestedOrUnsupportedPreference",
        "reviewerEvidenceReferenceRequiredForScenarioPassOrFail",
        "exportRequiresExplicitUserAction",
    ):
        require_true(capture, key, "observationCapturePolicy")
    for key in (
        "sourceRevisionMutable",
        "sourceTreeRevisionMutable",
        "localDetectionIsQualificationEvidence",
        "automaticPreferenceAcceptanceAllowed",
        "automaticScenarioPassAllowed",
        "automaticHumanAcceptanceAllowed",
        "automaticAccessibilityQualificationAllowed",
        "automaticLifecycleAcceptanceAllowed",
        "browserIdentitySniffingAllowed",
        "networkAccessRequired",
        "telemetryRequired",
        "analyticsRequired",
        "persistentStorageRequired",
        "capturedAcceptedForAccessibilityQualification",
        "capturedAcceptedForLifecycleGate",
    ):
        require_false(capture, key, "observationCapturePolicy")
    if capture.get("capturedStatus") != "in-progress":
        fail("captured observation record status must remain in-progress")
    if capture.get("capturedHumanReviewStatus") != "pending":
        fail("captured observation record human review must remain pending")
    if capture.get("capturedEvaluatorDisposition") != "blocked":
        fail("captured observation record evaluator disposition must remain blocked")

    acceptance = plan.get("acceptanceRules", {})
    if acceptance.get("recordStatus") != "passed":
        fail("accepted evidence must require record status passed")
    if acceptance.get("reviewAuthorityModes") != ["human", "combined"]:
        fail("accepted evidence must require human or combined review")
    if acceptance.get("humanReviewStatus") != "accepted":
        fail("accepted evidence must require accepted human review")
    require_true(acceptance, "acceptedForAccessibilityQualification", "acceptanceRules")
    require_false(acceptance, "acceptedForLifecycleGate", "acceptanceRules")

    boundary = plan.get("nonPromotionBoundary", {})
    for key in (
        "acceptedAccessibilitySliceIsStableV1_4",
        "acceptedAccessibilitySliceIsConsumerConformance",
        "acceptedAccessibilitySliceIsBrowserMatrixQualification",
        "acceptedAccessibilitySliceIsPhysicalDeviceQualification",
        "acceptedAccessibilitySliceIsProductionPerformanceQualification",
        "acceptedAccessibilitySliceIsNativeRendererParity",
    ):
        require_false(boundary, key, "nonPromotionBoundary")
    for key in ("lifecyclePromotionRequiresSeparateGovernedDecision", "downstreamConsumerAcceptanceRemainsIndependent"):
        require_true(boundary, key, "nonPromotionBoundary")

    required_not_established = {
        "stable-v1.4-release",
        "consumer-v1.4-conformance",
        "frozen-v1.4-accessibility-qualification-api",
        "browser-matrix-v1.4-qualification",
        "assistive-technology-v1.4-qualification",
        "physical-device-v1.4-qualification",
        "production-v1.4-performance-budgets",
        "native-v1.4-renderer-parity",
        "ecosystem-wide-v1.4-adoption",
    }
    values = plan.get("notEstablished")
    if not isinstance(values, list) or not required_not_established.issubset(values):
        fail("qualification support must preserve every non-established boundary")


def validate_schema(schema: dict) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("evidence schema must remain JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail("evidence schema root must reject unknown properties")
    required = schema.get("required")
    for field in (
        "schemaVersion", "recordKind", "target", "status", "observedAt", "reviewAuthority",
        "environment", "supportClaims", "preferenceCoverage", "scenarioResults", "issues", "disposition",
    ):
        if not isinstance(required, list) or field not in required:
            fail(f"evidence schema missing required field {field}")
    properties = schema.get("properties", {})
    if properties.get("schemaVersion", {}).get("const") != 1:
        fail("evidence schema version drifted")
    if properties.get("recordKind", {}).get("const") != "glaze-v1.4-accessibility-qualification-evidence-candidate":
        fail("evidence record kind drifted")
    disposition = properties.get("disposition", {}).get("properties", {})
    if disposition.get("acceptedForLifecycleGate", {}).get("const") is not False:
        fail("evidence schema must make lifecycle-gate acceptance impossible")
    status_enum = properties.get("status", {}).get("enum")
    if status_enum != ["in-progress", "review-ready", "passed", "failed", "superseded"]:
        fail("evidence status vocabulary drifted")
    scenario_enum = schema.get("$defs", {}).get("scenarioResult", {}).get("properties", {}).get("id", {}).get("enum", [])
    expected_ids = EXPECTED_REQUIRED_SCENARIOS + list(EXPECTED_CONDITIONAL.values())
    if scenario_enum != expected_ids:
        fail("evidence schema scenario vocabulary drifted")


def validate_source_boundaries(plan: dict) -> None:
    governed_paths = (
        PLAN, SCHEMA, COMPOSITION, EVALUATOR, PACKET_GENERATOR,
        OBSERVATION_CAPTURE, OBSERVATION_REFERENCE, OBSERVATION_REFERENCE_RUNTIME,
        TEMPLATE, REGRESSION, PACKET_REGRESSION, OBSERVATION_REGRESSION, VERSION,
    )
    for path in governed_paths:
        if not path.is_file():
            fail(f"governed artifact missing: {path.relative_to(ROOT)}")
    if VERSION.read_text(encoding="utf-8").strip() != "1.3.0":
        fail("Stable VERSION must remain 1.3.0 while V1.4 qualification support is a candidate")

    composition = load_json(COMPOSITION)
    qualification = composition.get("qualificationBoundary", {})
    if qualification.get("sourceBehaviorVerifiedByAutomatedTests") is not True:
        fail("sourceBehaviorVerifiedByAutomatedTests must reflect the verified source-level automation")
    for key in (
        "browserMatrixQualificationEstablished",
        "assistiveTechnologyQualificationEstablished",
        "physicalDeviceQualificationEstablished",
        "productionPerformanceQualificationEstablished",
    ):
        require_false(qualification, key, "accessibilityComposition.qualificationBoundary")

    evaluator_text = EVALUATOR.read_text(encoding="utf-8")
    for required in (
        "def evaluate_record(",
        '"acceptedForLifecycleGate": False',
        '"review-ready"',
        '"accepted"',
        "human-review-acceptance-pending",
        "automated-only-review-cannot-accept-accessibility-qualification",
    ):
        if required not in evaluator_text:
            fail(f"evaluator missing governed boundary: {required}")

    generator_text = PACKET_GENERATOR.read_text(encoding="utf-8")
    for required in (
        "def build_record(",
        "def build_checklist(",
        "def assert_prepared_fail_closed(",
        "accessibility-qualification-drafts",
        '"humanReviewStatus": "pending"',
        '"evaluatorDisposition": "blocked"',
        '"acceptedForAccessibilityQualification": False',
        '"acceptedForLifecycleGate": False',
        "prepared scenarios may not claim pass/fail results",
        "prepared scenarios must not fabricate evidence references",
    ):
        if required not in generator_text:
            fail(f"packet generator missing governed fail-closed boundary: {required}")

    capture_text = OBSERVATION_CAPTURE.read_text(encoding="utf-8")
    for required in (
        "glaze-v1.4-accessibility-observation-capture-candidate",
        "localDetectionIsQualificationEvidence: false",
        "automaticPreferenceAcceptanceAllowed: false",
        "automaticScenarioPassAllowed: false",
        "automaticHumanAcceptanceAllowed: false",
        "automaticAccessibilityQualificationAllowed: false",
        "automaticLifecycleAcceptanceAllowed: false",
        "networkAccessRequired: false",
        "telemetryRequired: false",
        "analyticsRequired: false",
        "persistentStorageRequired: false",
        "browserIdentitySniffingAllowed: false",
        "acceptedForAccessibilityQualification: false",
        "acceptedForLifecycleGate: false",
        "humanReviewStatus = 'pending'",
        "scenarioResults must not contain duplicate scenario ids",
        "requires explicit reviewer evidence references",
    ):
        if required not in capture_text:
            fail(f"observation capture runtime missing governed boundary: {required}")

    reference_runtime_text = OBSERVATION_REFERENCE_RUNTIME.read_text(encoding="utf-8")
    reference_html_text = OBSERVATION_REFERENCE.read_text(encoding="utf-8")
    forbidden_patterns = (
        "fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket",
        "localStorage", "sessionStorage", "indexedDB",
        "navigator.userAgent", "navigator.userAgentData", "navigator.platform",
        "getUserMedia", "getDisplayMedia", "http://", "https://",
    )
    for pattern in forbidden_patterns:
        if pattern in capture_text or pattern in reference_runtime_text or pattern in reference_html_text:
            fail(f"observation capture must not introduce remote/persistent/identity/capture path: {pattern}")
    for required in (
        "file.text()",
        "new Blob",
        "URL.createObjectURL",
        "URL.revokeObjectURL",
        "no state is auto-confirmed",
        "no qualification or lifecycle acceptance was granted",
    ):
        if required not in reference_runtime_text:
            fail(f"observation capture reference runtime missing local/manual boundary: {required}")
    for required in (
        "Local capture aid only.",
        "does not auto-pass scenarios",
        "export happens only when you choose the export action",
    ):
        if required not in reference_html_text:
            fail(f"observation capture reference HTML missing disclosure: {required}")

    template = load_json(TEMPLATE)
    if template.get("status") != "in-progress":
        fail("qualification template must remain in-progress")
    template_disposition = template.get("disposition", {})
    require_false(template_disposition, "acceptedForAccessibilityQualification", "template.disposition")
    require_false(template_disposition, "acceptedForLifecycleGate", "template.disposition")

    spec = importlib.util.spec_from_file_location("glaze_v14_accessibility_qualification_evaluator", EVALUATOR)
    if not spec or not spec.loader:
        fail("qualification evaluator could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.evaluate_record(template, plan)
    if result.get("evaluatorDisposition") != "blocked":
        fail("draft qualification template must deterministically evaluate as blocked")
    if result.get("acceptedForAccessibilityQualification") is not False:
        fail("draft qualification template must not receive accessibility qualification")
    if result.get("acceptedForLifecycleGate") is not False:
        fail("qualification evaluator must never grant lifecycle-gate acceptance")


def main() -> None:
    plan = load_json(PLAN)
    validate_plan(plan)
    validate_schema(load_json(SCHEMA))
    validate_source_boundaries(plan)
    print("Glaze UI V1.4 accessibility qualification support validation passed")


if __name__ == "__main__":
    main()
