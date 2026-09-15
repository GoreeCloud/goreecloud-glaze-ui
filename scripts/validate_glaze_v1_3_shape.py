#!/usr/bin/env python3
"""Validate the preserved GLAZE UI V1.3 Expressive Shape workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.2.0"  # Historical V1.3 source baseline.
V13_VERSION = "1.3.0"
CONTRACT = "contracts/v1.3/expressive-shape.candidate.json"
TOKENS = "tokens/glaze-v1.3-shape.candidate.json"
RUNTIME = "js/glaze-v1.3-shape.candidate.mjs"
TESTS = "tests/glaze-v1.3-shape.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(value: str) -> tuple[int, int, int] | None:
    try:
        parts = value.split(".")
        if len(parts) != 3:
            return None
        return tuple(int(part) for part in parts)  # type: ignore[return-value]
    except (AttributeError, ValueError):
        return None


def resolve_pointer(document: Any, pointer: str) -> Any:
    current = document
    for raw_part in pointer.lstrip("/").split("/"):
        if not raw_part:
            continue
        part = raw_part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (CONTRACT, TOKENS, RUNTIME, TESTS, PLAN, "tokens/glaze-v1.2-geometry.candidate.json", "VERSION", "registry/lifecycle.json"):
        req((ROOT / path).is_file(), f"missing expressive-shape artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Expressive Shape validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    lifecycle = load("registry/lifecycle.json")
    current_stable = lifecycle.get("currentStable")
    current_official = lifecycle.get("currentOfficial")
    req(version == current_stable == current_official, "VERSION/currentStable/currentOfficial must agree on the live current Stable release")
    current_tuple = version_tuple(version)
    v13_tuple = version_tuple(V13_VERSION)
    req(current_tuple is not None and v13_tuple is not None and current_tuple >= v13_tuple, "live current Stable may not regress below V1.3.0")
    retained_v13 = next((item for item in lifecycle.get("releases", []) if isinstance(item, dict) and item.get("version") == V13_VERSION), None)
    req(bool(retained_v13) and retained_v13.get("status") == "stable", "V1.3.0 retained release record must remain Stable")
    req(bool(retained_v13) and retained_v13.get("consumerEligible") is True, "V1.3.0 retained release record must preserve consumer eligibility")
    req(bool(retained_v13) and retained_v13.get("stableBaseline") == STABLE_VERSION, "V1.3.0 retained release baseline must remain 1.2.0")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("contract-and-token-architecture", {}).get("status") == "implemented-and-validated", "Expressive Shape requires validated token architecture")
    req(
        workstreams.get("expressive-shape", {}).get("status") in {
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "Expressive Shape workstream must be active in governed status vocabulary",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "shape product identity mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "shape target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "shape release lifecycle must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "shape artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "shape contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "shape contract must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "shape must extend V1.2 Stable")
    req(contract.get("extends") == "tokens/glaze-v1.2-geometry.candidate.json", "shape inheritance mismatch")

    expected_roles = {"quiet", "soft", "rounded", "capsule", "expressive", "hero", "morphable"}
    roles = contract.get("semanticRoles", {})
    req(set(roles) == expected_roles, "semantic shape role set mismatch")
    req(roles.get("expressive", {}).get("defaultForAllControls") is False, "expressive shape must not be default everywhere")
    req(roles.get("hero", {}).get("rarityRequired") is True, "Hero shape must remain rare")
    req(roles.get("morphable", {}).get("meaningMustPersist") is True, "Morphable shape must preserve meaning")

    expressive = contract.get("expressiveLibrary", {})
    hero = contract.get("heroLibrary", {})
    req(expressive.get("representation") == "normalized-corner-weight-profile", "expressive profile representation mismatch")
    req(hero.get("representation") == "normalized-corner-weight-profile", "hero profile representation mismatch")
    req(expressive.get("rawPolygonOrArbitraryPathDefaultAllowed") is False, "arbitrary path geometry must not become default authority")
    req(hero.get("routineUtilityUseAllowed") is False, "Hero geometry must not be routine utility geometry")
    for library_name, library in (("expressive", expressive), ("hero", hero)):
        low = float(library.get("weightRange", {}).get("min", -1))
        high = float(library.get("weightRange", {}).get("max", 2))
        req(0 < low <= high <= 1, f"{library_name} shape weight range must stay normalized")
        for profile_name, weights in library.get("profiles", {}).items():
            req(isinstance(weights, list) and len(weights) == 4, f"{library_name} profile {profile_name!r} must have four corner weights")
            if isinstance(weights, list):
                req(all(isinstance(value, (int, float)) and low <= value <= high for value in weights), f"{library_name} profile {profile_name!r} escaped governed weight range")

    concentric = contract.get("concentricGeometry", {})
    req(concentric.get("required") is True, "concentric geometry must be required")
    req(concentric.get("referenceFormula") == "max(0, parentRadius - childInset + opticalCorrection)", "concentric reference formula mismatch")
    req(concentric.get("applicationsHandSelectUnrelatedRadii") is False, "applications should not hand-select unrelated radii")
    expected_pairs = {
        ("shape.container", "shape.containerInner"),
        ("shape.control", "shape.controlInset"),
        ("shape.overlay", "shape.overlayInner"),
    }
    req({tuple(pair) for pair in concentric.get("semanticPairs", [])} == expected_pairs, "concentric semantic pair set mismatch")

    morph = contract.get("morphCompatibility", {})
    req(morph.get("rules", {}).get("semanticRoleMustPersist") is True, "shape morphs must preserve semantic role")
    req(morph.get("rules", {}).get("unrelatedObjectMorphProhibited") is True, "unrelated object morphs must be prohibited")
    req(morph.get("rules", {}).get("continuousDecorativeMorphingAllowed") is False, "continuous decorative morphing must be prohibited")
    req(morph.get("rules", {}).get("reducedMotionMayUseImmediateGeometryChange") is True, "Reduced Motion must allow immediate geometry change")

    token = load(TOKENS)
    req(token.get("product") == PRODUCT, "shape token product mismatch")
    req(token.get("releaseLifecycle") == "proposed", "shape tokens must remain Proposed")
    req(token.get("lifecycleAuthority") is False, "shape tokens must not carry lifecycle authority")
    req(token.get("consumerEligible") is False, "shape tokens must not be consumer eligible")
    req(token.get("namespace") == "shape", "shape token namespace mismatch")
    expected_tokens = {
        "shape.quiet", "shape.soft", "shape.rounded", "shape.container", "shape.containerInner",
        "shape.control", "shape.controlInset", "shape.overlay", "shape.overlayInner", "shape.capsule",
        "shape.expressive", "shape.hero", "shape.morphable"
    }
    req(expected_tokens.issubset(token.get("semanticTokens", {})), "shape semantic token coverage incomplete")
    implementations = token.get("implementationValues", {})
    for name, entry in implementations.items():
        if not isinstance(entry, dict):
            errors.append(f"shape implementation entry {name!r} must be an object")
            continue
        source = entry.get("source")
        pointer = entry.get("pointer")
        if source:
            source_path = ROOT / source
            req(source_path.is_file(), f"shape token source missing: {source}")
            if source_path.is_file() and pointer:
                try:
                    resolve_pointer(load(source), pointer)
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    errors.append(f"shape token pointer {pointer!r} does not resolve in {source}: {exc}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket("):
        req(forbidden not in runtime, f"shape runtime must remain local-only; forbidden network primitive found: {forbidden}")
    for symbol in ("resolveConcentricRadius", "resolveConcentricCorners", "resolveShape", "canMorphShape", "resolveShapeMorph", "applyShape", "expressiveShapeCandidate"):
        req(symbol in runtime, f"shape runtime missing required API: {symbol}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("human-optical-shape-acceptance", "platform-specific-optical-correction-calibration", "physical-device-rendering-acceptance", "release-candidate", "stable", "consumer-conformance"):
        req(item in not_established, f"shape evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Expressive Shape validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Expressive Shape: PASS")
    print(f"Boundary: preserved V1.3 semantic shape roles, concentric construction, bounded expressive libraries, and compatible morphing remain validated against their 1.2.0 source baseline; live current Stable is {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
