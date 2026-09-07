#!/usr/bin/env python3
"""Validate the bounded GLAZE UI V1.2 Stable source authority."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.2.0"
PRODUCT = "GLAZE UI V1.2"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION, "VERSION must be 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("officialProductLabel") == PRODUCT, "official product label must be GLAZE UI V1.2")
    req(lifecycle.get("currentOfficial") == VERSION, "currentOfficial must be 1.2.0")
    req(lifecycle.get("currentStable") == VERSION, "currentStable must be 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "V1.2 Stable validation requires no active V1.3 Candidate before governed promotion")
    release = next((item for item in lifecycle.get("releases", []) if item.get("version") == VERSION), None)
    req(bool(release) and release.get("status") == "stable", "lifecycle must contain Stable 1.2.0")
    req(bool(release) and release.get("consumerEligible") is True, "Stable V1.2 must be consumer-adoptable")
    req(lifecycle.get("plannedNext") == "1.3.0-candidate", "V1.3 must be the planned follow-up target")

    required = (
        "GLAZE_UI_V1_2.md",
        "GLAZE_UI_V1_2_CANDIDATE.md",
        "css/glaze-v1.2.0.css",
        "css/glaze-v1.2.0-candidate.css",
        "js/glaze-v1.2.0.mjs",
        "acceptance/v1.2-stable.md",
        "acceptance/v1.3-deferred-qualification.md",
        "contracts/v1.3/deferred-qualification.plan.json",
        "tokens/glaze-v1.json",
        "GLAZE_UI_V1_1.md",
        "acceptance/v1.1-stable.md"
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing Stable authority/audit file: {path}")

    css = (ROOT / "css/glaze-v1.2.0.css").read_text(encoding="utf-8")
    req('@import url("./glaze-v1.2.0-candidate.css")' in css, "Stable CSS wrapper must freeze the promoted V1.2 rendering source")
    runtime = (ROOT / "js/glaze-v1.2.0.mjs").read_text(encoding="utf-8")
    req('export * from "./glaze-v1.1.0.mjs"' in runtime, "Stable runtime must preserve inherited V1 runtime")
    req("glaze-v1.2-living-glaze.candidate.mjs" in runtime, "Stable runtime must export Living Glaze")
    req("glaze-v1.2-personalization.candidate.mjs" in runtime, "Stable runtime must export Personalization")

    manifest = load("tokens/glaze-v1.json")
    req(manifest.get("product") == PRODUCT and manifest.get("version") == VERSION and manifest.get("status") == "stable", "current token manifest mismatch")

    consumers = load("consumers/registry.json")
    req(consumers.get("officialBaseline") == VERSION, "consumer baseline must be 1.2.0")
    req(consumers.get("requiredConsumerVersion") == VERSION, "consumer required version must be 1.2.0")
    req(consumers.get("officialProductLabel") == PRODUCT, "consumer product label mismatch")
    req(all(item.get("requiredTargetVersion") == VERSION for item in consumers.get("consumers", [])), "all consumers must require 1.2.0")
    req(not any(item.get("productionEligible") is True for item in consumers.get("consumers", [])), "Stable design-system promotion must not auto-accept consumers")

    deferred = load("contracts/v1.3/deferred-qualification.plan.json")
    deferred_lifecycle = deferred.get("lifecycle")
    req(deferred_lifecycle in {"planned", "qualification-active"}, "V1.3 deferred work must remain planned or qualification-active before Candidate promotion")
    deferred_rules = deferred.get("rules", {})
    req(deferred_rules.get("v1.2StableImpliesThesePassed") is False, "V1.2 Stable must not manufacture deferred evidence")
    req(deferred_rules.get("freshExactRevisionEvidenceRequired") is True, "V1.3 deferred qualification must require fresh exact-revision evidence")
    req(deferred_rules.get("consumerConformanceAutomatic") is False, "V1.3 deferred qualification must not auto-accept consumers")
    req(deferred_rules.get("v1.3LifecyclePromotionAutomatic") is False, "V1.3 deferred qualification must not auto-promote lifecycle")
    if deferred_lifecycle == "qualification-active":
        req(deferred_rules.get("allBlockingWorkstreamsMustPassSameExactRevision") is True, "qualification-active V1.3 must require all blocking workstreams on one exact revision")
        req(deferred_rules.get("passedEvidenceAllowedDuringQualificationActive") is True, "qualification-active V1.3 must explicitly govern fresh passed evidence")
        req(deferred_rules.get("qualificationReadinessDoesNotPromoteLifecycle") is True, "qualification readiness must not imply lifecycle promotion")

    acceptance = (ROOT / "acceptance/v1.2-stable.md").read_text(encoding="utf-8")
    req("does not" in acceptance.lower() and "V1.3" in acceptance, "Stable acceptance must preserve the deferred-evidence boundary")

    if errors:
        print("GLAZE UI V1.2 Stable source validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("GLAZE UI V1.2 Stable source authority: PASS")
    print("Boundary: V1.3 deferred qualifications and downstream consumer acceptance remain separate from V1.2 Stable authority.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
