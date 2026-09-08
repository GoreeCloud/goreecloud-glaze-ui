#!/usr/bin/env python3
"""Validate the GLAZE UI V1.3 Adaptive Resonance dynamic-color workstream."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.2.0"
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
CONTRACT_PATH = "contracts/v1.3/dynamic-color.candidate.json"
TOKEN_PATH = "tokens/glaze-v1.3-color.candidate.json"
RUNTIME_PATH = "js/glaze-v1.3-dynamic-color.candidate.mjs"
TEST_PATH = "tests/glaze-v1.3-dynamic-color.test.mjs"
EXPECTED_AUTHORITIES = [
    "neutral-material-palette",
    "user-accent-palette",
    "product-identity-palette",
    "semantic-palette",
    "context-palette",
]
EXPECTED_PRECEDENCE = [
    "accessibility",
    "semantic",
    "product-identity",
    "user-accent",
    "context-accent",
    "default-glaze-accent",
]
EXPECTED_ROLES = [
    "primary",
    "secondary",
    "tertiary",
    "subtle-container",
    "high-emphasis-container",
    "on-accent",
    "focus",
    "selection",
]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (
        CONTRACT_PATH,
        TOKEN_PATH,
        RUNTIME_PATH,
        TEST_PATH,
        "contracts/v1.3/adaptive-resonance.candidate.json",
        "contracts/v1.3/adaptive-resonance.plan.json",
        "tokens/semantic-colors.json",
        "tokens/glaze-v1.2-optical-foundation.candidate.json",
        "tokens/glaze-v1.json",
        "registry/lifecycle.json",
        "VERSION",
    ):
        req((ROOT / path).is_file(), f"missing required dynamic-color artifact: {path}")

    if errors:
        print("GLAZE UI V1.3 dynamic color validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must remain 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "dynamic-color work must not activate V1.3 lifecycle Candidate")

    plan = load("contracts/v1.3/adaptive-resonance.plan.json")
    req(plan.get("lifecycle") == "proposed", "V1.3 plan must remain Proposed")
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("contract-and-token-architecture", {}).get("status") == "implemented-and-validated", "token architecture must be validated before dynamic color")
    req(
        workstreams.get("adaptive-dynamic-color", {}).get("status") in {
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "dynamic-color workstream must remain implemented within governed status vocabulary",
    )

    contract = load(CONTRACT_PATH)
    req(contract.get("product") == PRODUCT, "dynamic-color product identity mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "dynamic-color releaseLifecycle must remain proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "unexpected dynamic-color artifact lifecycle")
    req(contract.get("lifecycleAuthority") is False, "dynamic-color contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "dynamic-color contract must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "dynamic-color sourceStable must remain 1.2.0")
    req(contract.get("authorities") == EXPECTED_AUTHORITIES, "dynamic-color five-authority model mismatch")
    req(contract.get("precedence") == EXPECTED_PRECEDENCE, "dynamic-color precedence mismatch")
    req(contract.get("userAccentFamily") == EXPECTED_ROLES, "user accent family roles mismatch")
    req(contract.get("appearanceModes") == ["light", "dark", "deep-dark"], "appearance coverage mismatch")

    decision = contract.get("implementationDecision", {})
    req(decision.get("perceptualModel") == "OKLCH", "perceptual implementation decision must be explicit")
    req(decision.get("naiveRgbTransformationIsAuthority") is False, "naive RGB may not be the derivation authority")
    req(decision.get("fallbackSeed") == "#68AEE0", "unexpected default Glaze accent fallback")

    contrast = contract.get("contrast", {})
    req(float(contrast.get("onAccentMinimumRatio", 0)) >= 4.5, "on-accent minimum contrast must be at least 4.5")
    req(float(contrast.get("focusAgainstCanvasMinimumRatio", 0)) >= 3.0, "focus minimum contrast must be at least 3.0")
    req(contrast.get("validateAfterDerivation") is True, "contrast must be validated after derivation")

    local = contract.get("localFirst", {})
    req(local.get("directImageUploadRequired") is False, "dynamic color must not require image upload")
    req(local.get("networkDependency") is False, "dynamic color must not require network access")
    req(local.get("invalidOrMissingInputFallsBack") is True, "missing/invalid input must fall back")
    req(local.get("completeDefaultThemeRequired") is True, "complete default theme is required")

    semantic = contract.get("semanticProtection", {})
    req(semantic.get("producerTruthRemainsAuthoritative") is True, "producer truth must remain authoritative")
    req(semantic.get("personalizationMayRedefineSemanticRoles") is False, "personalization must not redefine semantic roles")
    req(semantic.get("productIdentityMayRedefineSemanticRoles") is False, "product identity must not redefine semantic roles")
    req(semantic.get("contextMayRedefineSemanticRoles") is False, "context must not redefine semantic roles")
    req(semantic.get("colorOnlyStateCommunicationAllowed") is False, "color-only state communication must remain forbidden")

    context = contract.get("contextPalette", {})
    req(context.get("localSummaryInputOnly") is True, "context palette must use local summary input")
    req(context.get("networkUploadRequired") is False, "context palette must not require network upload")
    req(context.get("telemetryAuthorized") is False, "dynamic-color telemetry must not be authorized")
    forbidden = set(context.get("forbiddenRoles", []))
    req({"warning", "danger", "protected", "security-status", "privacy-status"}.issubset(forbidden), "context forbidden roles are incomplete")

    token = load(TOKEN_PATH)
    req(token.get("product") == PRODUCT, "V1.3 color token product mismatch")
    req(token.get("releaseLifecycle") == "proposed", "V1.3 color token releaseLifecycle must remain proposed")
    req(token.get("lifecycleAuthority") is False, "V1.3 color token must not carry lifecycle authority")
    req(token.get("consumerEligible") is False, "V1.3 color token must not be consumer eligible")
    req(token.get("dynamicColorContract") == CONTRACT_PATH, "V1.3 color token dynamic-color contract link mismatch")
    req(token.get("runtimeBinding") == RUNTIME_PATH, "V1.3 color token runtime link mismatch")
    req(token.get("authorities") == EXPECTED_AUTHORITIES, "V1.3 color token authority list mismatch")
    req(token.get("precedence") == EXPECTED_PRECEDENCE, "V1.3 color token precedence mismatch")
    req(token.get("appearanceModes") == ["light", "dark", "deep-dark"], "V1.3 color token appearance list mismatch")
    req(token.get("rules", {}).get("contextMayRecolorConsequentialDialogs") is False, "context must not recolor consequential dialogs")
    req(token.get("rules", {}).get("contextMayRecolorSemanticStatus") is False, "context must not recolor semantic status")
    req(token.get("rules", {}).get("networkRequiredForDerivation") is False, "dynamic color must remain local-first")

    stable_manifest = load("tokens/glaze-v1.json")
    req(stable_manifest.get("version") == STABLE_VERSION, "Stable token manifest version changed")
    req(stable_manifest.get("status") == "stable", "Stable token manifest status changed")
    req("adaptive-colors.json" not in stable_manifest.get("sources", []), "legacy adaptive-colors.json must not silently become current Stable authority")

    runtime = (ROOT / RUNTIME_PATH).read_text(encoding="utf-8")
    for export_name in contract.get("runtimeExports", []):
        req(export_name in runtime, f"runtime export missing: {export_name}")
    for forbidden_pattern in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon("):
        req(forbidden_pattern not in runtime, f"dynamic-color runtime contains forbidden network primitive: {forbidden_pattern}")
    req("OKLCH" in runtime, "runtime must identify its perceptual model")
    req("PROTECTED_SEMANTIC_ROLES" in runtime, "runtime must encode protected semantic roles")
    req("CONTEXT_ALLOWED_ROLES" in runtime, "runtime must encode bounded context roles")

    if errors:
        print("GLAZE UI V1.3 dynamic color validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Adaptive Resonance dynamic color contract: PASS")
    print("Boundary: local-first perceptual accent derivation remains valid in later V1.3 phases; semantic truth and V1.2 Stable authority remain protected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
