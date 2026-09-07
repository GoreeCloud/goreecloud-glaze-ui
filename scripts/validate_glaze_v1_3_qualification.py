#!/usr/bin/env python3
"""Validate GLAZE UI V1.3 fresh qualification readiness without lifecycle promotion."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.2.0"
TARGET_VERSION = "1.3.0-candidate"
TARGET_PRODUCT = "GLAZE UI V1.3"
THEME_PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
PHASE = "phase-16-fresh-v1.3-qualification"

CONTRACT = "contracts/v1.3/qualification-readiness.candidate.json"
RUNTIME = "js/glaze-v1.3-qualification.candidate.mjs"
TESTS = "tests/glaze-v1.3-qualification.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
DEFERRED = "contracts/v1.3/deferred-qualification.plan.json"
MATRIX = "contracts/v1.3/qualification-matrix.json"
SCHEMA = "contracts/v1.3/qualification-evidence.schema.json"
MIGRATION = "contracts/v1.3/migration.candidate.json"
CANDIDATE_DOC = "GLAZE_UI_V1_3_CANDIDATE.md"
ACCEPTANCE = "acceptance/v1.3-candidate.md"

EXPECTED_WORKSTREAMS = {
    "human-optical-and-icon-collision-qualification",
    "manual-assistive-technology-qualification",
    "physical-device-native-platform-qualification",
    "physical-device-production-performance-qualification",
    "native-personalization-adapter-qualification",
    "stable-activation-and-source-namespace-cleanup",
}


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def valid_sha(value) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = (
        CONTRACT, RUNTIME, TESTS, PLAN, DEFERRED, MATRIX, SCHEMA, MIGRATION,
        CANDIDATE_DOC, ACCEPTANCE, "acceptance/v1.3-deferred-qualification.md",
        "evidence/v1.3/README.md", "registry/lifecycle.json", "VERSION",
        "css/glaze-v1.2.0.css", "js/glaze-v1.2.0.mjs",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing V1.3 qualification artifact or authority: {path}")

    if errors:
        print("GLAZE UI V1.3 fresh qualification validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION,
        "fresh qualification must leave VERSION at 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "fresh qualification must not activate Candidate")
    req(lifecycle.get("plannedNext") == TARGET_VERSION, "plannedNext must remain 1.3.0-candidate")

    plan = load(PLAN)
    req(plan.get("product") == THEME_PRODUCT, "Adaptive Resonance plan product mismatch")
    req(plan.get("lifecycle") == "proposed", "Adaptive Resonance product lifecycle must remain Proposed")
    req(plan.get("phase") == PHASE, "Adaptive Resonance plan must be in Phase 16 fresh qualification")
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("migration-and-consumer-boundary", {}).get("status") == "implemented-and-validated",
        "fresh qualification requires validated Migration/Consumer Boundary")
    req(workstreams.get("fresh-v1.3-qualification", {}).get("status") in {
        "implementation-in-progress", "implementation-complete-validation-pending", "implemented-and-validated"
    }, "fresh-v1.3-qualification workstream must be active or validated")
    gates = plan.get("gates", {})
    req(gates.get("candidateActivationRequiresImplementationEvidence") is True,
        "Candidate activation must still require implementation evidence")
    req(gates.get("candidateActivationRequiresValidation") is True,
        "Candidate activation must still require validation")
    req(gates.get("candidateActivationRequiresFreshDeferredQualificationPasses") is True,
        "Candidate activation must explicitly require fresh deferred-qualification passes")
    req(gates.get("consumerConformanceAutomatic") is False,
        "consumer conformance must remain non-automatic")

    deferred = load(DEFERRED)
    req(deferred.get("product") == TARGET_PRODUCT, "deferred qualification product mismatch")
    req(deferred.get("targetVersion") == TARGET_VERSION, "deferred qualification target mismatch")
    req(deferred.get("lifecycle") == "qualification-active",
        "Phase 16 requires qualification-active deferred control plane")
    req(set(deferred.get("items", [])) == EXPECTED_WORKSTREAMS,
        "deferred qualification workstream set mismatch")
    rules = deferred.get("rules", {})
    for key in (
        "freshExactRevisionEvidenceRequired",
        "allBlockingWorkstreamsMustPassSameExactRevision",
        "passedEvidenceAllowedDuringQualificationActive",
        "qualificationReadinessDoesNotPromoteLifecycle",
    ):
        req(rules.get(key) is True, f"deferred qualification active rule must be true: {key}")
    req(rules.get("v1.2StableImpliesThesePassed") is False,
        "V1.2 Stable must not imply fresh V1.3 qualification")
    req(rules.get("v1.3LifecyclePromotionAutomatic") is False,
        "qualification must not auto-promote lifecycle")

    matrix = load(MATRIX)
    req(matrix.get("product") == TARGET_PRODUCT, "qualification matrix product mismatch")
    req(matrix.get("targetVersion") == TARGET_VERSION, "qualification matrix target mismatch")
    req(matrix.get("lifecycle") == "qualification-active", "qualification matrix must be active")
    matrix_workstreams = matrix.get("workstreams", [])
    req({item.get("id") for item in matrix_workstreams} == EXPECTED_WORKSTREAMS,
        "qualification matrix workstream IDs mismatch")
    req(all(item.get("blockingForLifecyclePromotion") is True for item in matrix_workstreams),
        "all six qualification tracks must remain lifecycle blockers")
    matrix_rules = matrix.get("globalRules", {})
    for key in (
        "v1.2EvidenceMayNotBeReclassifiedAsV1.3Pass",
        "exactSourceRevisionRequired",
        "allBlockingWorkstreamsMustPassBeforeLifecyclePromotion",
        "allBlockingWorkstreamsMustPassSameExactRevision",
        "passedEvidenceAllowedWhileQualificationActive",
        "qualificationReadinessDoesNotPromoteLifecycle",
        "consumerEligibilityIsSeparate",
        "downstreamProductionAcceptanceIsSeparate",
        "plannedStatusIsNotEvidence",
    ):
        req(matrix_rules.get(key) is True, f"qualification matrix global rule must be true: {key}")

    schema = load(SCHEMA)
    schema_ids = set(schema.get("properties", {}).get("workstream_id", {}).get("enum", []))
    req(schema_ids == EXPECTED_WORKSTREAMS, "qualification evidence schema workstreams mismatch")
    target_props = schema.get("properties", {}).get("target", {}).get("properties", {})
    req(target_props.get("product", {}).get("const") == TARGET_PRODUCT,
        "qualification schema must pin target product")
    req(target_props.get("target_version", {}).get("const") == TARGET_VERSION,
        "qualification schema must pin target version")

    contract = load(CONTRACT)
    req(contract.get("product") == THEME_PRODUCT, "qualification readiness contract product mismatch")
    req(contract.get("targetProduct") == TARGET_PRODUCT, "qualification readiness target product mismatch")
    req(contract.get("targetVersion") == TARGET_VERSION, "qualification readiness target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "qualification readiness must preserve Proposed release lifecycle")
    req(contract.get("qualificationLifecycle") == "qualification-active", "qualification readiness must mark qualification active")
    req(contract.get("lifecycleAuthority") is False, "qualification readiness contract must not own lifecycle")
    req(contract.get("consumerEligible") is False, "qualification readiness contract must not be consumer eligible")
    required_ids = {item.get("id") for item in contract.get("requiredWorkstreams", [])}
    req(required_ids == EXPECTED_WORKSTREAMS, "qualification readiness required workstreams mismatch")
    record_rules = contract.get("recordAcceptance", {})
    req(record_rules.get("requiredStatus") == "passed", "accepted qualification status must be passed")
    req(record_rules.get("acceptedForLifecycleGateMustBe") is True, "passed record must be accepted for lifecycle gate")
    req(record_rules.get("exactSourceRevisionRequired") is True, "qualification contract must require exact revision")
    req(record_rules.get("singleSharedExactRevisionRequired") is True, "qualification contract must require one shared exact revision")
    req(record_rules.get("expiredEvidenceAllowed") is False, "expired evidence must remain blocked")
    req(record_rules.get("unresolvedIssuesAllowed") is False, "unresolved issues must remain blocked")
    permissions = contract.get("permissions", {})
    for key in (
        "mayActivateCandidate", "mayChangeVersionFile", "mayChangeLifecycleRegistry",
        "mayCreateConsumerEligibility", "mayGrantConsumerConformance",
        "mayTreatAutomatedCIAsHumanOrPhysicalEvidence",
    ):
        req(permissions.get(key) is False, f"qualification permission must remain false: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for symbol in ("QUALIFICATION_WORKSTREAMS", "evaluateQualificationReadiness", "qualificationCandidate"):
        req(symbol in runtime, f"qualification runtime missing API: {symbol}")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "localStorage", "sessionStorage", "indexedDB", "child_process", "node:fs"):
        req(forbidden not in runtime, f"qualification readiness runtime contains forbidden side-effect primitive: {forbidden}")

    accepted_revisions: set[str] = set()
    for record_path in sorted((ROOT / "evidence" / "v1.3").glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        req(record.get("workstream_id") in EXPECTED_WORKSTREAMS,
            f"{record_path.name}: unknown qualification workstream")
        target = record.get("target", {})
        req(target.get("product") == TARGET_PRODUCT and target.get("target_version") == TARGET_VERSION,
            f"{record_path.name}: qualification target mismatch")
        source_revision = target.get("source_revision")
        req(valid_sha(source_revision), f"{record_path.name}: invalid source revision")
        status = record.get("status")
        accepted = record.get("disposition", {}).get("accepted_for_lifecycle_gate") is True
        if status == "passed" and accepted and valid_sha(source_revision):
            accepted_revisions.add(source_revision)
        if status != "passed":
            req(not accepted, f"{record_path.name}: non-passed evidence may not be lifecycle-accepted")
    req(len(accepted_revisions) <= 1, "accepted qualification evidence may not mix exact source revisions")

    candidate_doc = (ROOT / CANDIDATE_DOC).read_text(encoding="utf-8")
    req("Candidate is NOT active" in candidate_doc,
        "Candidate qualification package must state Candidate is not active")
    req("current Candidate qualification outcome is **blocked**" in candidate_doc,
        "Candidate qualification package must state the current blocked outcome")
    req("lifecyclePromotionGranted: false" in candidate_doc,
        "Candidate qualification package must preserve non-promotion evaluator result")

    acceptance = (ROOT / ACCEPTANCE).read_text(encoding="utf-8")
    req("**Status:** BLOCKED" in acceptance, "Candidate acceptance ledger must remain blocked without accepted evidence")
    req("**No promotion decision is recorded.**" in acceptance,
        "Candidate acceptance ledger must explicitly record no promotion decision")

    req(not (ROOT / "css/glaze-v1.3.0-candidate.css").exists(),
        "fresh qualification must not create Candidate CSS entrypoint before formal promotion")
    req(not (ROOT / "js/glaze-v1.3.0-candidate.mjs").exists(),
        "fresh qualification must not create Candidate runtime entrypoint before formal promotion")

    if errors:
        print("GLAZE UI V1.3 fresh qualification validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 fresh qualification mechanism: PASS")
    print("Outcome: qualification control plane is active and fail-closed; Candidate remains unactivated pending fresh accepted human/device evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
