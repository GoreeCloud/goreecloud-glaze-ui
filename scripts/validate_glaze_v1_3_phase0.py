#!/usr/bin/env python3
"""Validate the enduring GLAZE UI V1.3 Stable release boundary.

The filename is retained because V1.3 implementation workflows already depend on
it. After the 2026-09-08 owner release directive, its responsibility is to guard
the official V1.3.0 authority rather than the historical pre-promotion state.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.3.0"
BASELINE_VERSION = "1.2.0"
PLANNED_NEXT = "1.3.1-candidate"
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


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
        "consumers/registry.json",
        "VERSION",
        "css/glaze-v1.3.0.css",
        "js/glaze-v1.3.0.mjs",
        "css/glaze-v1.2.0.css",
        "js/glaze-v1.2.0.mjs",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing required V1.3 Stable authority file: {path}")

    if errors:
        print("GLAZE UI V1.3 Stable boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req(
        (ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION,
        "VERSION must be 1.3.0",
    )

    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must be 1.3.0")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must be 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "no V1.3 Candidate may remain active after Stable release")
    req(lifecycle.get("plannedNext") == PLANNED_NEXT, "plannedNext must be 1.3.1-candidate")
    req(lifecycle.get("officialProductLabel") == PRODUCT, "official product label mismatch")

    release = next(
        (item for item in lifecycle.get("releases", []) if item.get("version") == STABLE_VERSION),
        None,
    )
    req(bool(release), "lifecycle registry must contain a 1.3.0 release record")
    req(bool(release) and release.get("status") == "stable", "V1.3.0 release record must be Stable")
    req(bool(release) and release.get("consumerEligible") is True, "V1.3.0 must be consumer-eligible")
    req(bool(release) and release.get("stableBaseline") == BASELINE_VERSION, "V1.3.0 baseline must be 1.2.0")
    req(bool(release) and release.get("webEntrypoint") == "css/glaze-v1.3.0.css", "Stable web entrypoint mismatch")
    req(bool(release) and release.get("runtimeEntrypoint") == "js/glaze-v1.3.0.mjs", "Stable runtime entrypoint mismatch")
    req(bool(release) and release.get("acceptance") == "acceptance/v1.3-stable.md", "Stable acceptance path mismatch")

    consumers = load("consumers/registry.json")
    req(consumers.get("officialBaseline") == STABLE_VERSION, "consumer officialBaseline must be 1.3.0")
    req(consumers.get("requiredConsumerVersion") == STABLE_VERSION, "requiredConsumerVersion must be 1.3.0")
    req(consumers.get("officialProductLabel") == PRODUCT, "consumer official product label mismatch")

    plan = load("contracts/v1.3/adaptive-resonance.plan.json")
    req(plan.get("product") == PRODUCT, "V1.3 product/theme identity mismatch")
    req(plan.get("sourceStable") == BASELINE_VERSION, "V1.3 implementation provenance must remain anchored to 1.2.0")
    workstreams = plan.get("workstreams", [])
    req(bool(workstreams), "V1.3 implementation workstreams must remain recorded")
    req(
        all(item.get("status") == "implemented-and-validated" for item in workstreams),
        "all V1.3 implementation workstreams must remain implemented-and-validated",
    )

    contract = (ROOT / "GLAZE_UI_V1_3.md").read_text(encoding="utf-8")
    req("**Lifecycle:** Official Stable" in contract, "V1.3 contract must say Official Stable")
    req("**Machine version:** `1.3.0`" in contract, "V1.3 contract must name machine version 1.3.0")
    req("**Consumer eligible:** Yes" in contract, "V1.3 contract must be consumer-eligible")

    acceptance = (ROOT / "acceptance/v1.3-stable.md").read_text(encoding="utf-8")
    req("**Status:** Official Stable release" in acceptance, "V1.3 Stable acceptance must be active")
    req("V1.3.1 deferred obligations" in acceptance, "V1.3 Stable acceptance must preserve deferred V1.3.1 work")
    req("not be represented as passed" in acceptance, "V1.3 Stable acceptance must preserve evidence integrity")

    hardening = (ROOT / "GLAZE_UI_V1_3_1_HARDENING.md").read_text(encoding="utf-8")
    req("**Current Stable:** GLAZE UI V1.3" in hardening, "V1.3.1 hardening must anchor to V1.3 Stable")
    req("evidence pass" in hardening, "V1.3.1 hardening must reject fabricated evidence passes")

    if errors:
        print("GLAZE UI V1.3 Stable boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Adaptive Resonance Stable boundary: PASS")
    print("Authority: 1.3.0 is Official/Stable/consumer-eligible; unresolved qualification remains V1.3.1 follow-up without fabricated passes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
