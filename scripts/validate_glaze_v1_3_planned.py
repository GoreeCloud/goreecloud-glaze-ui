#!/usr/bin/env python3
"""Validate the GLAZE UI V1.3 deferred/fresh qualification control plane."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.2.0"
TARGET_VERSION = "1.3.0-candidate"
PRODUCT = "GLAZE UI V1.3"
QUALITY_CONTRACT = "contracts/v1.3/quality-rules.candidate.json"
EVIDENCE_SCHEMA_VERSION = 2
ALLOWED_QUALIFICATION_LIFECYCLES = {"planned", "qualification-active"}
ALLOWED_MATRIX_STATUSES = {"planned", "in_progress", "passed", "failed", "superseded"}
HUMAN_OPTICAL = "human-optical-and-icon-collision-qualification"

EXPECTED_WORKSTREAMS = {
    HUMAN_OPTICAL,
    "manual-assistive-technology-qualification",
    "physical-device-native-platform-qualification",
    "physical-device-production-performance-qualification",
    "native-personalization-adapter-qualification",
    "stable-activation-and-source-namespace-cleanup",
}
EXPECTED_QUALITY_RULE_IDS = {f"quality-{index:02d}" for index in range(1, 56)}


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def valid_sha(value) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION,
        "V1.3 qualification must not change current VERSION from 1.2.0")

    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION,
        "V1.3 qualification must preserve currentOfficial 1.2.0")
    req(lifecycle.get("currentStable") == STABLE_VERSION,
        "V1.3 qualification must preserve currentStable 1.2.0")
    req(lifecycle.get("activeCandidate") is None,
        "qualification-active state must not itself create an active Candidate")
    req(lifecycle.get("plannedNext") == TARGET_VERSION,
        "plannedNext must remain 1.3.0-candidate before governed promotion")

    required = (
        "acceptance/v1.3-deferred-qualification.md",
        "contracts/v1.3/deferred-qualification.plan.json",
        "contracts/v1.3/qualification-matrix.json",
        "contracts/v1.3/qualification-evidence.schema.json",
        QUALITY_CONTRACT,
        "evidence/v1.3/README.md",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing V1.3 qualification authority: {path}")

    if errors:
        print("GLAZE UI V1.3 qualification control-plane validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    plan = load("contracts/v1.3/deferred-qualification.plan.json")
    req(plan.get("schemaVersion") == 3, "V1.3 qualification plan schemaVersion must be 3")
    req(plan.get("product") == PRODUCT, "V1.3 qualification plan product mismatch")
    req(plan.get("targetVersion") == TARGET_VERSION, "V1.3 qualification plan target mismatch")
    req(plan.get("lifecycle") in ALLOWED_QUALIFICATION_LIFECYCLES,
        "V1.3 qualification plan lifecycle must be planned or qualification-active")
    req(plan.get("sourceStable") == STABLE_VERSION, "V1.3 qualification plan must inherit from Stable 1.2.0")
    req(set(plan.get("items", [])) == EXPECTED_WORKSTREAMS,
        "V1.3 qualification plan workstream IDs must match the deferred qualification set")
    req(plan.get("qualificationMatrix") == "contracts/v1.3/qualification-matrix.json",
        "V1.3 qualification plan must identify the matrix authority")
    req(plan.get("evidenceSchema") == "contracts/v1.3/qualification-evidence.schema.json",
        "V1.3 qualification plan must identify the evidence schema authority")
    req(plan.get("evidenceDirectory") == "evidence/v1.3",
        "V1.3 qualification plan must identify the evidence directory")
    req(plan.get("qualityContract") == QUALITY_CONTRACT,
        "V1.3 qualification plan must identify the visual quality contract")
    req(plan.get("validator") == "scripts/validate_glaze_v1_3_planned.py",
        "V1.3 qualification plan must identify this validator")
    req(plan.get("readinessEvaluator") == "js/glaze-v1.3-qualification.candidate.mjs",
        "V1.3 qualification plan must identify the readiness evaluator")
    control_plane = plan.get("controlPlane", {})
    req(control_plane.get("status") == plan.get("lifecycle"),
        "V1.3 control-plane status must match the plan lifecycle")
    req(isinstance(control_plane.get("meaning"), str) and control_plane.get("meaning"),
        "V1.3 control-plane meaning must remain explicit")

    plan_rules = plan.get("rules", {})
    req(plan_rules.get("v1.2StableImpliesThesePassed") is False,
        "V1.2 Stable must not imply V1.3 qualification pass")
    req(plan_rules.get("freshExactRevisionEvidenceRequired") is True,
        "V1.3 must require fresh exact-revision evidence")
    req(plan_rules.get("humanOpticalEvidenceMustCoverQualityContract") is True,
        "V1.3 human optical evidence must cover the quality contract")
    req(plan_rules.get("automatedValidationMayReplaceHumanOpticalReview") is False,
        "automation must not replace human optical review")
    req(plan_rules.get("automatedValidationMayReplacePhysicalDeviceReview") is False,
        "automation must not replace physical-device review")
    req(plan_rules.get("consumerConformanceAutomatic") is False,
        "V1.3 qualification must not auto-accept consumers")
    req(plan_rules.get("v1.3LifecyclePromotionAutomatic") is False,
        "V1.3 lifecycle promotion must remain governed")
    if plan.get("lifecycle") == "qualification-active":
        req(plan_rules.get("passedEvidenceAllowedDuringQualificationActive") is True,
            "qualification-active plan must explicitly allow fresh passed evidence")
        req(plan_rules.get("allBlockingWorkstreamsMustPassSameExactRevision") is True,
            "qualification-active plan must require one shared exact revision")
        req(plan_rules.get("qualificationReadinessDoesNotPromoteLifecycle") is True,
            "qualification readiness must not imply lifecycle promotion")

    matrix = load("contracts/v1.3/qualification-matrix.json")
    req(matrix.get("schemaVersion") == 2, "qualification matrix schemaVersion must be 2")
    req(matrix.get("product") == PRODUCT, "qualification matrix product mismatch")
    req(matrix.get("targetVersion") == TARGET_VERSION, "qualification matrix target mismatch")
    req(matrix.get("lifecycle") == plan.get("lifecycle"),
        "qualification matrix lifecycle must match deferred qualification plan")
    req(matrix.get("sourceStable") == STABLE_VERSION, "qualification matrix source Stable mismatch")
    req(matrix.get("qualityContract") == QUALITY_CONTRACT,
        "qualification matrix must identify the quality contract")
    workstreams = matrix.get("workstreams", [])
    ids = {item.get("id") for item in workstreams if isinstance(item, dict)}
    req(ids == EXPECTED_WORKSTREAMS, "qualification matrix workstream IDs mismatch")
    req(len(workstreams) == len(EXPECTED_WORKSTREAMS), "qualification matrix must not duplicate workstreams")
    req(all(isinstance(item, dict) and item.get("status") in ALLOWED_MATRIX_STATUSES for item in workstreams),
        "qualification matrix contains an unsupported workstream status")
    req(all(isinstance(item, dict) and item.get("blockingForLifecyclePromotion") is True for item in workstreams),
        "all carried-forward workstreams must remain lifecycle blockers for V1.3")
    req(all(isinstance(item, dict) and isinstance(item.get("requiredEvidence"), list) and item.get("requiredEvidence")
            for item in workstreams),
        "every V1.3 qualification workstream must define required evidence")
    optical_matrix = next((item for item in workstreams if isinstance(item, dict) and item.get("id") == HUMAN_OPTICAL), {})
    optical_required = " ".join(optical_matrix.get("requiredEvidence", [])).lower()
    req("55" in optical_required and "visual finish" in optical_required and "blandness" in optical_required,
        "human optical matrix must require the 55-rule visual finish and blandness gates")

    global_rules = matrix.get("globalRules", {})
    req(global_rules.get("v1.2EvidenceMayNotBeReclassifiedAsV1.3Pass") is True,
        "matrix must forbid relabeling V1.2 evidence as V1.3 pass")
    req(global_rules.get("exactSourceRevisionRequired") is True,
        "matrix must require exact source revision")
    req(global_rules.get("allBlockingWorkstreamsMustPassBeforeLifecyclePromotion") is True,
        "matrix must require all blocking workstreams before promotion")
    req(global_rules.get("humanOpticalPassRequiresFullQualityRuleCoverage") is True,
        "matrix must require complete human optical quality coverage")
    req(global_rules.get("automatedValidationDoesNotReplaceHumanReview") is True,
        "matrix must preserve mandatory human review")
    req(global_rules.get("consumerEligibilityIsSeparate") is True,
        "consumer eligibility must remain separate")
    req(global_rules.get("downstreamProductionAcceptanceIsSeparate") is True,
        "downstream production acceptance must remain separate")
    req(global_rules.get("plannedStatusIsNotEvidence") is True,
        "planned status must not be treated as evidence")
    if matrix.get("lifecycle") == "qualification-active":
        req(global_rules.get("allBlockingWorkstreamsMustPassSameExactRevision") is True,
            "active qualification matrix must require a shared exact revision")
        req(global_rules.get("passedEvidenceAllowedWhileQualificationActive") is True,
            "active qualification matrix must explicitly allow passed evidence")
        req(global_rules.get("qualificationReadinessDoesNotPromoteLifecycle") is True,
            "active qualification matrix must preserve separate lifecycle promotion")

    quality = load(QUALITY_CONTRACT)
    req(quality.get("schemaVersion") == 1, "quality contract schemaVersion must be 1")
    req(quality.get("product") == "GLAZE UI V1.3 — Adaptive Resonance",
        "quality contract product mismatch")
    req(quality.get("targetVersion") == TARGET_VERSION, "quality contract target mismatch")
    req(quality.get("releaseLifecycle") == "proposed", "quality contract must preserve Proposed release lifecycle")
    req(quality.get("qualificationLifecycle") == "qualification-active",
        "quality contract must preserve qualification-active state")
    req(quality.get("sourceStable") == STABLE_VERSION, "quality contract source Stable mismatch")
    req(quality.get("humanReviewRequired") is True, "quality contract must require human review")
    req(quality.get("automatedValidationSufficient") is False,
        "quality contract must reject automation-only visual acceptance")
    quality_rules = quality.get("rules", [])
    quality_ids = {item.get("id") for item in quality_rules if isinstance(item, dict)}
    req(len(quality_rules) == 55 and quality_ids == EXPECTED_QUALITY_RULE_IDS,
        "quality contract must define exactly quality-01 through quality-55")
    req(all(isinstance(item, dict) and isinstance(item.get("title"), str) and item.get("title").strip()
            for item in quality_rules),
        "every quality rule must have a non-empty title")
    quality_disposition = quality.get("requiredHumanOpticalDisposition", {})
    for field in (
        "reviewAllRuleIds",
        "visualFinishAccepted",
        "blandnessRejected",
        "accessibilityBeautyReviewed",
        "responsiveBeautyReviewed",
        "criticalFinalQualityQuestionsAccepted",
    ):
        req(quality_disposition.get(field) is True, f"quality contract must require {field}")
    req(quality_disposition.get("unresolvedMaterialVisualDefectsAllowed") is False,
        "quality contract must block unresolved material visual defects")
    promotion_boundary = quality.get("promotionBoundary", {})
    req(all(promotion_boundary.get(field) is False for field in (
        "qualityReviewAlonePromotesLifecycle",
        "qualityReviewAloneActivatesCandidate",
        "qualityReviewAloneGrantsConsumerEligibility",
        "downstreamConformanceAutomatic",
    )), "quality contract must not grant lifecycle or consumer authority")

    schema = load("contracts/v1.3/qualification-evidence.schema.json")
    req(schema.get("title") == "GLAZE UI V1.3 Qualification Evidence Record",
        "qualification evidence schema title mismatch")
    schema_properties = schema.get("properties", {})
    req(schema_properties.get("schema_version", {}).get("const") == EVIDENCE_SCHEMA_VERSION,
        "qualification evidence schema must require schema_version 2")
    target_properties = schema_properties.get("target", {}).get("properties", {})
    req(target_properties.get("product", {}).get("const") == PRODUCT,
        "evidence schema must pin GLAZE UI V1.3")
    req(target_properties.get("target_version", {}).get("const") == TARGET_VERSION,
        "evidence schema must pin 1.3.0-candidate")
    schema_ids = set(schema_properties.get("workstream_id", {}).get("enum", []))
    req(schema_ids == EXPECTED_WORKSTREAMS,
        "evidence schema workstream IDs must match qualification matrix")
    quality_review_schema = schema_properties.get("quality_review", {}).get("properties", {})
    req(quality_review_schema.get("contract", {}).get("const") == QUALITY_CONTRACT,
        "evidence schema quality_review must pin the quality contract")
    schema_quality_ids = set(quality_review_schema.get("reviewed_rule_ids", {}).get("items", {}).get("enum", []))
    req(schema_quality_ids == EXPECTED_QUALITY_RULE_IDS,
        "evidence schema must enumerate all 55 governed quality rule IDs")
    req(quality_review_schema.get("reviewed_rule_ids", {}).get("minItems") == 55 and
        quality_review_schema.get("reviewed_rule_ids", {}).get("maxItems") == 55,
        "evidence schema must require exactly 55 quality rule IDs")

    accepted_revisions: set[str] = set()
    evidence_dir = ROOT / "evidence" / "v1.3"
    for record_path in sorted(evidence_dir.glob("*.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - surfaced in CI
            errors.append(f"invalid V1.3 evidence JSON {record_path.name}: {exc}")
            continue

        req(record.get("schema_version") == EVIDENCE_SCHEMA_VERSION,
            f"{record_path.name}: schema_version must be {EVIDENCE_SCHEMA_VERSION}")
        workstream_id = record.get("workstream_id")
        req(workstream_id in EXPECTED_WORKSTREAMS,
            f"{record_path.name}: unknown workstream_id")
        target = record.get("target", {})
        req(target.get("product") == PRODUCT and target.get("target_version") == TARGET_VERSION,
            f"{record_path.name}: target must be GLAZE UI V1.3 / 1.3.0-candidate")
        source_revision = target.get("source_revision")
        req(valid_sha(source_revision),
            f"{record_path.name}: source_revision must be a lowercase 40-character Git SHA")

        status = record.get("status")
        accepted = record.get("disposition", {}).get("accepted_for_lifecycle_gate") is True
        req(status in {"in_progress", "passed", "failed", "superseded"},
            f"{record_path.name}: unsupported evidence status")
        if status == "passed":
            req(accepted, f"{record_path.name}: passed evidence must be accepted for lifecycle gate")
            if valid_sha(source_revision) and accepted:
                accepted_revisions.add(source_revision)
        else:
            req(not accepted,
                f"{record_path.name}: non-passed evidence may not be accepted for lifecycle gate")

        if workstream_id == HUMAN_OPTICAL and status == "passed":
            review = record.get("quality_review", {})
            req(review.get("contract") == QUALITY_CONTRACT,
                f"{record_path.name}: passed human optical evidence must reference the quality contract")
            reviewed = review.get("reviewed_rule_ids", [])
            req(isinstance(reviewed, list) and len(reviewed) == 55 and len(set(reviewed)) == 55 and set(reviewed) == EXPECTED_QUALITY_RULE_IDS,
                f"{record_path.name}: passed human optical evidence must cover all 55 quality rule IDs exactly once")
            for field in (
                "visual_finish_accepted",
                "blandness_rejected",
                "accessibility_beauty_reviewed",
                "responsive_beauty_reviewed",
                "critical_final_quality_questions_accepted",
            ):
                req(review.get(field) is True,
                    f"{record_path.name}: passed human optical evidence must set {field}=true")

        if plan.get("lifecycle") == "planned":
            req(status != "passed",
                f"{record_path.name}: passed evidence requires qualification-active control plane")

    req(len(accepted_revisions) <= 1,
        "accepted qualification evidence may not mix source revisions")

    acceptance = (ROOT / "acceptance/v1.3-deferred-qualification.md").read_text(encoding="utf-8")
    req("does not imply" in acceptance.lower(),
        "V1.3 deferred acceptance must preserve the no-implied-promotion boundary")
    req("fresh" in acceptance.lower() and "exact" in acceptance.lower(),
        "V1.3 deferred acceptance must require fresh exact-revision evidence")

    evidence_readme = (ROOT / "evidence/v1.3/README.md").read_text(encoding="utf-8")
    req("all 55" in evidence_readme.lower() and "visual-finish" in evidence_readme.lower() and "blandness" in evidence_readme.lower(),
        "V1.3 evidence guidance must document the 55-rule visual-quality boundary")

    if errors:
        print("GLAZE UI V1.3 qualification control-plane validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    state = plan.get("lifecycle")
    print("GLAZE UI V1.3 qualification control plane: PASS")
    print("Visual quality contract: PASS — 55 governed human-review rules are fail-closed in schema and evidence validation.")
    print(f"Boundary: qualification state is {state}; V1.2 remains Stable and V1.3 Candidate is not activated by this validator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
