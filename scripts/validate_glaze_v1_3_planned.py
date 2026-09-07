#!/usr/bin/env python3
"""Validate the GLAZE UI V1.3 deferred/fresh qualification control plane."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.2.0"
TARGET_VERSION = "1.3.0-candidate"
PRODUCT = "GLAZE UI V1.3"
ALLOWED_QUALIFICATION_LIFECYCLES = {"planned", "qualification-active"}
ALLOWED_MATRIX_STATUSES = {"planned", "in_progress", "passed", "failed", "superseded"}

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
    req(plan.get("product") == PRODUCT, "V1.3 qualification plan product mismatch")
    req(plan.get("targetVersion") == TARGET_VERSION, "V1.3 qualification plan target mismatch")
    req(plan.get("lifecycle") in ALLOWED_QUALIFICATION_LIFECYCLES,
        "V1.3 qualification plan lifecycle must be planned or qualification-active")
    req(plan.get("sourceStable") == STABLE_VERSION, "V1.3 qualification plan must inherit from Stable 1.2.0")
    req(set(plan.get("items", [])) == EXPECTED_WORKSTREAMS,
        "V1.3 qualification plan workstream IDs must match the deferred qualification set")

    plan_rules = plan.get("rules", {})
    req(plan_rules.get("v1.2StableImpliesThesePassed") is False,
        "V1.2 Stable must not imply V1.3 qualification pass")
    req(plan_rules.get("freshExactRevisionEvidenceRequired") is True,
        "V1.3 must require fresh exact-revision evidence")
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
    req(matrix.get("product") == PRODUCT, "qualification matrix product mismatch")
    req(matrix.get("targetVersion") == TARGET_VERSION, "qualification matrix target mismatch")
    req(matrix.get("lifecycle") == plan.get("lifecycle"),
        "qualification matrix lifecycle must match deferred qualification plan")
    req(matrix.get("sourceStable") == STABLE_VERSION, "qualification matrix source Stable mismatch")
    workstreams = matrix.get("workstreams", [])
    ids = {item.get("id") for item in workstreams}
    req(ids == EXPECTED_WORKSTREAMS, "qualification matrix workstream IDs mismatch")
    req(len(workstreams) == len(EXPECTED_WORKSTREAMS), "qualification matrix must not duplicate workstreams")
    req(all(item.get("status") in ALLOWED_MATRIX_STATUSES for item in workstreams),
        "qualification matrix contains an unsupported workstream status")
    req(all(item.get("blockingForLifecyclePromotion") is True for item in workstreams),
        "all carried-forward workstreams must remain lifecycle blockers for V1.3")
    req(all(isinstance(item.get("requiredEvidence"), list) and item.get("requiredEvidence")
            for item in workstreams),
        "every V1.3 qualification workstream must define required evidence")

    global_rules = matrix.get("globalRules", {})
    req(global_rules.get("v1.2EvidenceMayNotBeReclassifiedAsV1.3Pass") is True,
        "matrix must forbid relabeling V1.2 evidence as V1.3 pass")
    req(global_rules.get("exactSourceRevisionRequired") is True,
        "matrix must require exact source revision")
    req(global_rules.get("allBlockingWorkstreamsMustPassBeforeLifecyclePromotion") is True,
        "matrix must require all blocking workstreams before promotion")
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

    schema = load("contracts/v1.3/qualification-evidence.schema.json")
    req(schema.get("title") == "GLAZE UI V1.3 Qualification Evidence Record",
        "qualification evidence schema title mismatch")
    target_properties = schema.get("properties", {}).get("target", {}).get("properties", {})
    req(target_properties.get("product", {}).get("const") == PRODUCT,
        "evidence schema must pin GLAZE UI V1.3")
    req(target_properties.get("target_version", {}).get("const") == TARGET_VERSION,
        "evidence schema must pin 1.3.0-candidate")
    schema_ids = set(schema.get("properties", {}).get("workstream_id", {}).get("enum", []))
    req(schema_ids == EXPECTED_WORKSTREAMS,
        "evidence schema workstream IDs must match qualification matrix")

    accepted_revisions: set[str] = set()
    evidence_dir = ROOT / "evidence" / "v1.3"
    for record_path in sorted(evidence_dir.glob("*.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - surfaced in CI
            errors.append(f"invalid V1.3 evidence JSON {record_path.name}: {exc}")
            continue

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

    if errors:
        print("GLAZE UI V1.3 qualification control-plane validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    state = plan.get("lifecycle")
    print("GLAZE UI V1.3 qualification control plane: PASS")
    print(f"Boundary: qualification state is {state}; V1.2 remains Stable and V1.3 Candidate is not activated by this validator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
