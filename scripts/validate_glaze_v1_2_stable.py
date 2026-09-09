#!/usr/bin/env python3
"""Validate retained GLAZE UI V1.2 Stable source under current V1.3 authority."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETAINED_VERSION = "1.2.0"
CURRENT_VERSION = "1.3.0"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == CURRENT_VERSION,
        "live VERSION must remain current Stable 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("officialProductLabel") == "GLAZE UI V1.3 — Adaptive Resonance",
        "live official product label must remain GLAZE UI V1.3 — Adaptive Resonance")
    req(lifecycle.get("currentOfficial") == CURRENT_VERSION,
        "live currentOfficial must remain 1.3.0")
    req(lifecycle.get("currentStable") == CURRENT_VERSION,
        "live currentStable must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None,
        "live V1.3 Stable authority must not have an active Candidate")
    req(lifecycle.get("plannedNext") == "1.3.1-candidate",
        "plannedNext must remain the V1.3.1 hardening line")

    retained = next(
        (item for item in lifecycle.get("releases", []) if item.get("version") == RETAINED_VERSION),
        None,
    )
    req(bool(retained) and retained.get("status") == "stable",
        "lifecycle must retain Stable 1.2.0 history")
    req(bool(retained) and retained.get("consumerEligible") is True,
        "retained V1.2 must remain rollback/audit consumer-eligible")
    req(bool(retained) and retained.get("stableBaseline") == "1.1.0",
        "retained V1.2 baseline must remain V1.1")
    req(bool(retained) and retained.get("contract") == "GLAZE_UI_V1_2.md",
        "retained V1.2 contract binding drifted")

    required = (
        "GLAZE_UI_V1_2.md",
        "GLAZE_UI_V1_2_CANDIDATE.md",
        "css/glaze-v1.2.0.css",
        "css/glaze-v1.2.0-candidate.css",
        "js/glaze-v1.2.0.mjs",
        "acceptance/v1.2-stable.md",
        "acceptance/v1.3-deferred-qualification.md",
        "contracts/v1.3/deferred-qualification.plan.json",
        "contracts/v1.3/stable-readiness.plan.json",
        "GLAZE_UI_V1_1.md",
        "acceptance/v1.1-stable.md",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing retained Stable authority/audit file: {path}")

    css = (ROOT / "css/glaze-v1.2.0.css").read_text(encoding="utf-8")
    req('@import url("./glaze-v1.2.0-candidate.css")' in css,
        "retained V1.2 Stable CSS wrapper must freeze the promoted V1.2 rendering source")
    runtime = (ROOT / "js/glaze-v1.2.0.mjs").read_text(encoding="utf-8")
    req('export * from "./glaze-v1.1.0.mjs"' in runtime,
        "retained V1.2 runtime must preserve inherited V1 runtime")
    req("glaze-v1.2-living-glaze.candidate.mjs" in runtime,
        "retained V1.2 runtime must export Living Glaze")
    req("glaze-v1.2-personalization.candidate.mjs" in runtime,
        "retained V1.2 runtime must export Personalization")

    consumers = load("consumers/registry.json")
    req(consumers.get("requiredConsumerVersion") == CURRENT_VERSION,
        "current shared consumer target must remain 1.3.0")
    req(consumers.get("officialBaseline") == CURRENT_VERSION,
        "current shared consumer baseline must remain 1.3.0")

    deferred = load("contracts/v1.3/deferred-qualification.plan.json")
    deferred_rules = deferred.get("rules", {})
    req(deferred_rules.get("v1.2StableImpliesThesePassed") is False,
        "retained V1.2 Stable must not manufacture later qualification evidence")
    req(deferred_rules.get("freshExactRevisionEvidenceRequired") is True,
        "later qualification must require fresh exact-revision evidence")
    req(deferred_rules.get("consumerConformanceAutomatic") is False,
        "later qualification must not auto-accept consumers")
    req(deferred_rules.get("v1.3LifecyclePromotionAutomatic") is False,
        "later qualification must not auto-promote lifecycle")

    acceptance = (ROOT / "acceptance/v1.2-stable.md").read_text(encoding="utf-8")
    req("does not" in acceptance.lower() and "V1.3" in acceptance,
        "retained V1.2 acceptance must preserve the later-evidence boundary")

    if errors:
        print("GLAZE UI retained V1.2 Stable source validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("GLAZE UI retained V1.2 Stable source authority: PASS")
    print("Boundary: live V1.3 / 1.3.0 remains current Stable; V1.2 is retained rollback/audit source and does not manufacture V1.3.1 evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
