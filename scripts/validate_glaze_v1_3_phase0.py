#!/usr/bin/env python3
"""Validate preserved GLAZE UI V1.3 Stable integrity.

The filename is retained for compatibility with historical V1.3 workflows. Once
a later Stable release exists, this validator proves that V1.3 remains a valid,
auditable rollback baseline; it does not claim V1.3 is still the current release.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.3.0"
BASELINE_VERSION = "1.2.0"
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def semver_tuple(value: str) -> tuple[int, int, int]:
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = (
        "GLAZE_UI_V1_3.md",
        "GLAZE_UI_V1_3_1_HARDENING.md",
        "acceptance/v1.3-stable.md",
        "acceptance/v1.3-deferred-qualification.md",
        "contracts/v1.3/adaptive-resonance.plan.json",
        "registry/lifecycle.json",
        "css/glaze-v1.3.0.css",
        "js/glaze-v1.3.0.mjs",
        "css/glaze-v1.2.0.css",
        "js/glaze-v1.2.0.mjs",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing required V1.3 historical authority file: {path}")

    if errors:
        print("GLAZE UI V1.3 historical integrity validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    lifecycle = load("registry/lifecycle.json")
    current = lifecycle.get("currentStable")
    req(isinstance(current, str), "lifecycle must declare currentStable")
    if isinstance(current, str):
        try:
            req(semver_tuple(current) >= semver_tuple(STABLE_VERSION), "current Stable may not regress below V1.3.0")
        except (ValueError, AttributeError):
            req(False, "currentStable must be semantic x.y.z")
    req(lifecycle.get("activeCandidate") is None or isinstance(lifecycle.get("activeCandidate"), str), "activeCandidate must be null or a version string")

    release = next((item for item in lifecycle.get("releases", []) if item.get("version") == STABLE_VERSION), None)
    req(bool(release), "lifecycle registry must retain the 1.3.0 release record")
    req(bool(release) and release.get("status") == "stable", "V1.3.0 historical release record must remain Stable")
    req(bool(release) and release.get("consumerEligible") is True, "V1.3.0 historical record must preserve consumer eligibility")
    req(bool(release) and release.get("stableBaseline") == BASELINE_VERSION, "V1.3.0 baseline must remain 1.2.0")
    req(bool(release) and release.get("webEntrypoint") == "css/glaze-v1.3.0.css", "V1.3 Stable web entrypoint drift")
    req(bool(release) and release.get("runtimeEntrypoint") == "js/glaze-v1.3.0.mjs", "V1.3 Stable runtime entrypoint drift")
    req(bool(release) and release.get("acceptance") == "acceptance/v1.3-stable.md", "V1.3 Stable acceptance path drift")

    plan = load("contracts/v1.3/adaptive-resonance.plan.json")
    req(plan.get("product") == PRODUCT, "V1.3 product/theme identity mismatch")
    req(plan.get("sourceStable") == BASELINE_VERSION, "V1.3 implementation provenance must remain anchored to 1.2.0")
    workstreams = plan.get("workstreams", [])
    req(bool(workstreams), "V1.3 implementation workstreams must remain recorded")
    req(all(item.get("status") == "implemented-and-validated" for item in workstreams), "all V1.3 implementation workstreams must remain implemented-and-validated")

    contract = (ROOT / "GLAZE_UI_V1_3.md").read_text(encoding="utf-8")
    req("**Lifecycle:** Official Stable" in contract, "V1.3 contract must preserve its Stable release record")
    req("**Machine version:** `1.3.0`" in contract, "V1.3 contract must name machine version 1.3.0")
    req("**Consumer eligible:** Yes" in contract, "V1.3 historical contract must preserve consumer eligibility")

    acceptance = (ROOT / "acceptance/v1.3-stable.md").read_text(encoding="utf-8")
    req("**Status:** Official Stable release" in acceptance, "V1.3 Stable acceptance must remain recorded")
    req("V1.3.1 deferred obligations" in acceptance, "V1.3 acceptance must preserve deferred V1.3.1 work")
    req(
        "not represented as passed" in acceptance or "not rewritten as a pass" in acceptance,
        "V1.3 acceptance must preserve evidence integrity",
    )

    hardening = (ROOT / "GLAZE_UI_V1_3_1_HARDENING.md").read_text(encoding="utf-8")
    req("evidence pass" in hardening, "V1.3.1 hardening must reject fabricated evidence passes")

    if errors:
        print("GLAZE UI V1.3 historical integrity validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 historical Stable integrity: PASS")
    print(f"V1.3.0 remains an auditable rollback baseline while current Stable is {current}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
