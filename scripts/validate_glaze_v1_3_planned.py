#!/usr/bin/env python3
"""Validate the planned GLAZE UI V1.3 deferred-qualification control plane."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.2.0"
TARGET_VERSION = "1.3.0-candidate"
PRODUCT = "GLAZE UI V1.3"

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


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION,
        "V1.3 planning must not change current VERSION from 1.2.0")

    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION,
        "V1.3 planning must preserve currentOfficial 1.2.0")
    req(lifecycle.get("currentStable") == STABLE_VERSION,
        "V1.3 planning must preserve currentStable 1.2.0")
    req(lifecycle.get("activeCandidate") is None,
        "V1.3 planning must not create an active Candidate")
    req(lifecycle.get("plannedNext") == TARGET_VERSION,
        "plannedNext must remain 1.3.0-candidate")

    required = (
        "acceptance/v1.3-deferred-qualification.md",
        "contracts/v1.3/deferred-qualification.plan.json",
        "contracts/v1.3/qualification-matrix.json",
        "contracts/v1.3/qualification-evidence.schema.json",
        "evidence/v1.3/README.md",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing V1.3 planning authority: {path}")

    plan = load("contracts/v1.3/deferred-qualification.plan.json")
    req(plan.get("product") == PRODUCT, "V1.3 plan product mismatch")
    req(plan.get("targetVersion") == TARGET_VERSION, "V1.3 plan target mismatch")
    req(plan.get("lifecycle") == "planned", "V1.3 plan must remain planned")
    req(plan.get("sourceStable") == STABLE_VERSION, "V1.3 plan must inherit from Stable 1.2.0")
    req(set(plan.get("items", [])) == EXPECTED_WORKSTREAMS,
        "V1.3 plan workstream IDs must match the deferred qualification set")
    plan_rules = plan.get("rules", {})
    req(plan_rules.get("v1.2StableImpliesThesePassed") is False,
        "V1.2 Stable must not imply V1.3 qualification pass")
    req(plan_rules.get("freshExactRevisionEvidenceRequired") is True,
        "V1.3 must require fresh exact-revision evidence")
    req(plan_rules.get("consumerConformanceAutomatic") is False,
        "V1.3 planning must not auto-accept consumers")
    req(plan_rules.get("v1.3LifecyclePromotionAutomatic") is False,
        "V1.3 lifecycle promotion must remain governed")

    matrix = load("contracts/v1.3/qualification-matrix.json")
    req(matrix.get("product") == PRODUCT, "qualification matrix product mismatch")
    req(matrix.get("targetVersion") == TARGET_VERSION, "qualification matrix target mismatch")
    req(matrix.get("lifecycle") == "planned", "qualification matrix must remain planned")
    req(matrix.get("sourceStable") == STABLE_VERSION, "qualification matrix source Stable mismatch")
    workstreams = matrix.get("workstreams", [])
    ids = {item.get("id") for item in workstreams}
    req(ids == EXPECTED_WORKSTREAMS, "qualification matrix workstream IDs mismatch")
    req(len(workstreams) == len(EXPECTED_WORKSTREAMS), "qualification matrix must not duplicate workstreams")
    req(all(item.get("status") == "planned" for item in workstreams),
        "all V1.3 workstreams must remain planned until evidence is intentionally recorded")
    req(all(item.get("blockingForLifecyclePromotion") is True for item in workstreams),
        "all carried-forward workstreams must remain lifecycle blockers for V1.3")
    req(all(isinstance(item.get("requiredEvidence"), list) and item.get("requiredEvidence")
            for item in workstreams),
        "every V1.3 workstream must define required evidence")

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

    evidence_dir = ROOT / "evidence" / "v1.3"
    for record_path in sorted(evidence_dir.glob("*.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - surfaced in CI
            errors.append(f"invalid V1.3 evidence JSON {record_path.name}: {exc}")
            continue
        req(record.get("workstream_id") in EXPECTED_WORKSTREAMS,
            f"{record_path.name}: unknown workstream_id")
        target = record.get("target", {})
        req(target.get("product") == PRODUCT and target.get("target_version") == TARGET_VERSION,
            f"{record_path.name}: target must be GLAZE UI V1.3 / 1.3.0-candidate")
        source_revision = target.get("source_revision", "")
        req(isinstance(source_revision, str) and len(source_revision) == 40 and
            all(ch in "0123456789abcdef" for ch in source_revision),
            f"{record_path.name}: source_revision must be a lowercase 40-character Git SHA")
        req(record.get("status") != "passed",
            f"{record_path.name}: passed evidence is not allowed while V1.3 lifecycle remains planned")
        req(record.get("disposition", {}).get("accepted_for_lifecycle_gate") is not True,
            f"{record_path.name}: planned V1.3 evidence may not be accepted for lifecycle gate")

    acceptance = (ROOT / "acceptance/v1.3-deferred-qualification.md").read_text(encoding="utf-8")
    req("does not imply" in acceptance.lower(),
        "V1.3 acceptance record must preserve the no-implied-promotion boundary")
    req("fresh evidence" in acceptance.lower() and "exact" in acceptance.lower(),
        "V1.3 acceptance record must require fresh exact-revision evidence")

    if errors:
        print("GLAZE UI V1.3 planned qualification control-plane validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 planned qualification control plane: PASS")
    print("Boundary: V1.2 remains Stable; V1.3 has no active Candidate and no qualification passes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
