#!/usr/bin/env python3
"""Validate the bounded GLAZE UI V1.3.0 Stable lifecycle authority."""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.3.0"
LABEL = "GLAZE UI V1.3 — Adaptive Resonance"
SOURCE_ANCHOR = "fc7cc91d2eace8da2371371c2855c24cbcb326a1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = (
        "VERSION",
        "registry/lifecycle.json",
        "GLAZE_UI_V1_3.md",
        "STABILITY.md",
        "acceptance/v1.3-stable.md",
        "acceptance/v1.3.1-hardening.md",
        "tokens/glaze-v1.3.json",
        "js/glaze-v1.3.0.mjs",
        "css/glaze-v1.2.0.css",
        "MIGRATION_V1_2_TO_V1_3.md",
        "consumers/registry.json",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing V1.3 Stable authority artifact: {path}")

    if errors:
        print("GLAZE UI V1.3 Stable validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION, "VERSION must be 1.3.0")

    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("officialProductLabel") == LABEL, "official product label mismatch")
    req(lifecycle.get("currentOfficial") == VERSION, "currentOfficial must be 1.3.0")
    req(lifecycle.get("currentStable") == VERSION, "currentStable must be 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "Stable lifecycle must not retain an active Candidate")
    req(lifecycle.get("plannedNext") == "1.3.1", "plannedNext must be 1.3.1 hardening")

    releases = lifecycle.get("releases", [])
    current = [item for item in releases if isinstance(item, dict) and item.get("version") == VERSION]
    req(len(current) == 1, "exactly one 1.3.0 lifecycle record is required")
    if current:
        record = current[0]
        req(record.get("status") == "stable", "1.3.0 lifecycle status must be stable")
        req(record.get("consumerEligible") is True, "1.3.0 must be consumer-eligible")
        req(record.get("stableBaseline") == "1.2.0", "1.3.0 rollback baseline must be 1.2.0")
        req(record.get("contract") == "GLAZE_UI_V1_3.md", "1.3.0 contract authority mismatch")
        req(record.get("tokens") == "tokens/glaze-v1.3.json", "1.3.0 token authority mismatch")
        req(record.get("runtimeEntrypoint") == "js/glaze-v1.3.0.mjs", "1.3.0 runtime authority mismatch")
        req(record.get("inheritedWebEntrypoint") == "css/glaze-v1.2.0.css", "inherited web base mismatch")
        req(record.get("acceptance") == "acceptance/v1.3-stable.md", "1.3.0 acceptance authority mismatch")
        req(record.get("hardening") == "acceptance/v1.3.1-hardening.md", "V1.3.1 hardening authority mismatch")
        anchor = record.get("sourceQualificationAnchor")
        req(isinstance(anchor, str) and SHA40.fullmatch(anchor) is not None, "1.3.0 source anchor must be a 40-character SHA")
        req(anchor == SOURCE_ANCHOR, "1.3.0 must remain anchored to the integrated pre-promotion V1.3 source")

    tokens = load("tokens/glaze-v1.3.json")
    req(tokens.get("version") == VERSION and tokens.get("lifecycle") == "stable", "V1.3 token manifest must be Stable 1.3.0")
    families = tokens.get("families", {})
    expected_families = {"color", "layout", "material", "motion", "shape", "type"}
    req(isinstance(families, dict) and set(families) == expected_families, "V1.3 token family set mismatch")
    for path in families.values() if isinstance(families, dict) else ():
        req(isinstance(path, str) and (ROOT / path).is_file(), f"missing promoted V1.3 token source: {path}")

    runtime = (ROOT / "js/glaze-v1.3.0.mjs").read_text(encoding="utf-8")
    for module in (
        "glaze-v1.2.0.mjs",
        "glaze-v1.3-accessibility.candidate.mjs",
        "glaze-v1.3-adaptive-navigation.candidate.mjs",
        "glaze-v1.3-component-experience.candidate.mjs",
        "glaze-v1.3-contextual-intelligence.candidate.mjs",
        "glaze-v1.3-dynamic-color.candidate.mjs",
        "glaze-v1.3-living-material-2.candidate.mjs",
        "glaze-v1.3-motion.candidate.mjs",
        "glaze-v1.3-multi-pane.candidate.mjs",
        "glaze-v1.3-personalization.candidate.mjs",
        "glaze-v1.3-reachability.candidate.mjs",
        "glaze-v1.3-shape.candidate.mjs",
        "glaze-v1.3-system-shell.candidate.mjs",
        "glaze-v1.3-typography.candidate.mjs",
    ):
        req(module in runtime, f"Stable runtime missing promoted implementation module: {module}")
    req("glaze-v1.3-qualification.candidate.mjs" not in runtime, "consumer runtime must not export qualification policy evaluator")
    req("glaze-v1.3-stable-readiness.candidate.mjs" not in runtime, "consumer runtime must not export Stable-readiness policy evaluator")

    contract = (ROOT / "GLAZE_UI_V1_3.md").read_text(encoding="utf-8")
    req("**Lifecycle:** Stable" in contract and "**Version:** `1.3.0`" in contract, "V1.3 contract must declare Stable 1.3.0")
    req("acceptance/v1.3.1-hardening.md" in contract, "V1.3 contract must preserve hardening handoff")

    acceptance = (ROOT / "acceptance/v1.3-stable.md").read_text(encoding="utf-8")
    req("does **not** convert" in acceptance, "Stable acceptance must preserve missing-evidence boundary")
    req(SOURCE_ANCHOR in acceptance, "Stable acceptance must name the integrated source anchor")

    hardening = (ROOT / "acceptance/v1.3.1-hardening.md").read_text(encoding="utf-8")
    for lane in ("H1", "H2", "H3", "H4", "H5", "H6"):
        req(f"### {lane}" in hardening, f"V1.3.1 hardening ledger missing {lane}")
    req("V1.3.0 remains Stable" in hardening, "hardening ledger must not revoke V1.3.0 Stable")

    consumers = load("consumers/registry.json")
    req(consumers.get("officialBaseline") == VERSION, "consumer registry officialBaseline must be 1.3.0")
    req(consumers.get("requiredConsumerVersion") == VERSION, "consumer registry target must be 1.3.0")
    req(consumers.get("officialProductLabel") == LABEL, "consumer registry label mismatch")
    req(all(item.get("requiredTargetVersion") == VERSION for item in consumers.get("consumers", [])), "all consumer records must require 1.3.0")
    req(all(item.get("productionEligible") is False for item in consumers.get("consumers", [])), "Glaze registry must not auto-grant product production eligibility")

    req(not (ROOT / "css/glaze-v1.3.0.css").exists(), "do not fabricate a V1.3 CSS aggregate absent from the integrated implementation")

    if errors:
        print("GLAZE UI V1.3 Stable validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3.0 Stable lifecycle authority: PASS")
    print("Boundary: V1.3 is current Stable; unresolved qualification remains truthful V1.3.1 hardening; consumers require independent acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
