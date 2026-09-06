#!/usr/bin/env python3
"""Validate the enduring GLAZE UI V1.3 Adaptive Resonance pre-promotion lifecycle boundary."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.2.0"
PLANNED_TARGET = "1.3.0-candidate"
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
ALLOWED_PHASES = {
    "phase-0-foundation",
    "phase-1-token-architecture",
    "phase-2-dynamic-color",
    "phase-3-living-material-2",
    "phase-4-human-reachability",
    "phase-5-expressive-shape",
    "phase-6-variable-responsive-typography",
    "phase-7-adaptive-navigation",
    "phase-8-multi-pane-foldable-desktop",
    "phase-9-system-shell-and-control-center",
    "phase-10-contextual-intelligence",
    "phase-11-motion-and-continuity",
    "phase-12-accessibility-and-resilience",
}
ALLOWED_WORKSTREAM_STATUSES = {
    "planned",
    "implementation-in-progress",
    "implementation-complete-validation-pending",
    "implemented-and-validated",
}


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = (
        "GLAZE_UI_V1_3.md",
        "GLAZE_UI_V1_2.md",
        "contracts/v1.3/adaptive-resonance.plan.json",
        "contracts/v1.3/deferred-qualification.plan.json",
        "acceptance/v1.3-deferred-qualification.md",
        "registry/lifecycle.json",
        "VERSION",
        "css/glaze-v1.2.0.css",
        "js/glaze-v1.2.0.mjs",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing required pre-promotion authority file: {path}")

    if errors:
        print("GLAZE UI V1.3 pre-promotion boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req(
        (ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION,
        "V1.3 development must leave VERSION at 1.2.0 until governed Candidate activation",
    )

    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "V1.3 development must not activate Candidate before the governed gate")
    req(lifecycle.get("plannedNext") == PLANNED_TARGET, "plannedNext must remain 1.3.0-candidate")

    stable = next(
        (item for item in lifecycle.get("releases", []) if item.get("version") == STABLE_VERSION),
        None,
    )
    req(bool(stable) and stable.get("status") == "stable", "V1.2 must remain Stable")
    req(bool(stable) and stable.get("consumerEligible") is True, "V1.2 must remain consumer-eligible")

    plan = load("contracts/v1.3/adaptive-resonance.plan.json")
    req(plan.get("product") == PRODUCT, "V1.3 product/theme identity mismatch")
    req(plan.get("lifecycle") == "proposed", "Adaptive Resonance plan must remain Proposed")
    req(plan.get("sourceStable") == STABLE_VERSION, "V1.3 must derive from 1.2.0 Stable")
    req(plan.get("targetVersion") == PLANNED_TARGET, "V1.3 planned target mismatch")
    req(plan.get("phase") in ALLOWED_PHASES, "unexpected V1.3 development phase")
    req(
        plan.get("phaseEffect") in {
            "planning-readiness-only",
            "implementation-workstream-active-no-lifecycle-promotion",
        },
        "development phase effect must not imply lifecycle promotion",
    )

    gates = plan.get("gates", {})
    req(gates.get("candidateActivationRequiresImplementationEvidence") is True, "Candidate must require implementation evidence")
    req(gates.get("candidateActivationRequiresValidation") is True, "Candidate must require validation")
    req(gates.get("releaseCandidateRequiresExactRevisionAcceptance") is True, "RC must require exact-revision acceptance")
    req(gates.get("stableRequiresFormalPromotion") is True, "Stable must require formal promotion")
    req(gates.get("consumerConformanceAutomatic") is False, "consumer conformance must never be automatic")
    req(gates.get("deferredV1_2EvidenceCountsAsV1_3Pass") is False, "deferred V1.2 work must not count as V1.3 evidence")
    req(gates.get("accessibilityOutranksExpression") is True, "accessibility precedence must be explicit")
    req(gates.get("degradeEffectsBeforeCorrectness") is True, "effect degradation must precede correctness loss")

    protected = plan.get("protectedStableState", {})
    req(protected.get("versionFileMustRemain") == STABLE_VERSION, "protected VERSION boundary mismatch")
    req(protected.get("officialStableMustRemain") == STABLE_VERSION, "protected Stable boundary mismatch")
    req(protected.get("phase0MayChangeLifecycleRegistry") is False, "development must not inherit permission to change lifecycle authority")
    req(protected.get("phase0MayCreateCandidateEntrypoints") is False, "development must not inherit permission to create Candidate entrypoints")

    expected_workstreams = {
        "contract-and-token-architecture",
        "adaptive-dynamic-color",
        "expressive-shape",
        "variable-responsive-typography",
        "living-material-2",
        "human-reachability",
        "adaptive-navigation",
        "multi-pane-foldable-desktop",
        "system-shell-and-control-center",
        "contextual-intelligence",
        "motion-and-continuity",
        "accessibility-and-resilience",
        "personalization",
        "signature-components-and-reference-suite",
        "migration-and-consumer-boundary",
        "fresh-v1.3-qualification",
    }
    workstreams = plan.get("workstreams", [])
    ids = {item.get("id") for item in workstreams}
    req(ids == expected_workstreams, "V1.3 workstream set is incomplete or unexpected")
    req(
        all(item.get("status") in ALLOWED_WORKSTREAM_STATUSES for item in workstreams),
        "V1.3 workstream status escaped the pre-promotion development vocabulary",
    )

    known = set(ids)
    statuses = {item.get("id"): item.get("status") for item in workstreams}
    for item in workstreams:
        for dep in item.get("dependsOn", []):
            req(dep in known, f"unknown dependency {dep!r} in workstream {item.get('id')!r}")
        if item.get("status") != "planned":
            for dep in item.get("dependsOn", []):
                req(
                    statuses.get(dep) == "implemented-and-validated",
                    f"active workstream {item.get('id')!r} requires validated dependency {dep!r}",
                )

    deferred = load("contracts/v1.3/deferred-qualification.plan.json")
    req(deferred.get("lifecycle") == "planned", "deferred V1.3 qualification must remain planned")
    req(deferred.get("sourceStable") == STABLE_VERSION, "deferred qualification must remain anchored to V1.2 Stable")
    req(
        deferred.get("rules", {}).get("v1.3LifecyclePromotionAutomatic") is False,
        "deferred qualification must not auto-promote V1.3",
    )

    contract = (ROOT / "GLAZE_UI_V1_3.md").read_text(encoding="utf-8")
    req("**Lifecycle:** Proposed" in contract, "V1.3 human-readable contract must say Proposed")
    req("Lifecycle effect:** None" in contract, "V1.3 contract must preserve no-lifecycle-effect boundary")
    req("consumer-eligible" in contract, "V1.3 contract must describe the consumer boundary")

    req(not (ROOT / "css/glaze-v1.3.0-candidate.css").exists(), "pre-promotion development must not create a Candidate CSS entrypoint")
    req(not (ROOT / "js/glaze-v1.3.0-candidate.mjs").exists(), "pre-promotion development must not create a Candidate runtime entrypoint")

    if errors:
        print("GLAZE UI V1.3 pre-promotion boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Adaptive Resonance pre-promotion boundary: PASS")
    print("Boundary: V1.2 remains Stable, V1.3 remains Proposed, and active workstreams require validated dependencies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
