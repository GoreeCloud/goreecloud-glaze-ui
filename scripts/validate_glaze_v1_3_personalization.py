#!/usr/bin/env python3
"""Validate the preserved GLAZE UI V1.3 Personalization workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.2.0"  # Historical V1.3 source baseline.
V13_VERSION = "1.3.0"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
CONTRACT = "contracts/v1.3/personalization.candidate.json"
RUNTIME = "js/glaze-v1.3-personalization.candidate.mjs"
TESTS = "tests/glaze-v1.3-personalization.test.mjs"
V12 = "contracts/v1.2/personalization-appearance.candidate.json"
DEPENDENCIES = {
    "adaptive-dynamic-color": "contracts/v1.3/dynamic-color.candidate.json",
    "expressive-shape": "contracts/v1.3/expressive-shape.candidate.json",
    "variable-responsive-typography": "contracts/v1.3/typography.candidate.json",
    "accessibility-and-resilience": "contracts/v1.3/accessibility.candidate.json",
}
EXPECTED_PRECEDENCE = [
    "accessibility",
    "platform-system",
    "goreecloud-user",
    "application-specific-when-allowed",
    "glaze-default",
]


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


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = [CONTRACT, RUNTIME, TESTS, PLAN, V12, *DEPENDENCIES.values(), "VERSION", "registry/lifecycle.json"]
    for path in required:
        req((ROOT / path).is_file(), f"missing Personalization artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Personalization validation FAILED:")
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
    # Phase 0 owns global development-phase sequencing. Personalization must
    # remain reusable as a dependency revalidation gate in later V1.3 phases.
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    for dep in DEPENDENCIES:
        req(workstreams.get(dep, {}).get("status") == "implemented-and-validated", f"Personalization requires validated dependency {dep}")
    req(
        workstreams.get("personalization", {}).get("status") in {
            "implementation-in-progress", "implementation-complete-validation-pending", "implemented-and-validated"
        },
        "Personalization workstream must be active or validated",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "Personalization product mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "Personalization target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "Personalization lifecycle must remain Proposed")
    req(contract.get("lifecycleAuthority") is False, "Personalization contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "Personalization contract must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "Personalization must extend V1.2 Stable")
    req(contract.get("principle") == "Personalize expression, not truth or control semantics.", "Personalization principle changed")
    req(contract.get("preferencePrecedence") == EXPECTED_PRECEDENCE, "Personalization precedence changed")

    extends = set(contract.get("extends", []))
    for path in [V12, *DEPENDENCIES.values()]:
        req(path in extends, f"Personalization inheritance missing {path}")

    appearance = contract.get("appearance", {})
    req(appearance.get("allowed") == ["follow-system", "light", "dark", "deep-dark"], "appearance modes mismatch")
    req(appearance.get("platformAdapterOwnsSystemResolution") is True, "platform adapter must own system appearance resolution")
    req(appearance.get("nativeSystemAdapterAcceptanceRequired") is True, "native system adapter acceptance must remain separate")

    accent = contract.get("accent", {})
    req(accent.get("derivationAuthority") == DEPENDENCIES["adaptive-dynamic-color"], "Dynamic Color must own user accent derivation")
    for key in ("semanticRoleOverrideAllowed", "productIdentityReplacementAllowed", "forcedColorsOverrideAllowed", "unsafeRawSemanticPaletteEditingAllowed"):
        req(accent.get(key) is False, f"accent safety rule must be false: {key}")
    req(accent.get("networkRequired") is False, "user accent derivation must remain local")

    expression = contract.get("expressionProfiles", {})
    req(expression.get("allowed") == ["calm", "balanced", "expressive"], "expression profiles mismatch")
    req(expression.get("shapeCeilings") == {"calm": "soft", "balanced": "rounded", "expressive": "expressive"}, "shape expression ceilings mismatch")
    for key in ("shapeCeilingMayReplaceComponentSemanticRole", "arbitraryGeometryAllowed", "arbitraryTypographyAxisValuesAllowed", "continuousDecorativeExpressionAllowed"):
        req(expression.get(key) is False, f"expression safety rule must be false: {key}")

    density = contract.get("density", {})
    req(density.get("minimumInteractiveTargetPx") == 48, "default target floor must remain 48px")
    req(density.get("touchAssistanceMinimumInteractiveTargetPx") == 56, "Touch Assistance target floor must remain 56px")
    req(density.get("largeTextMayRelaxDensity") is True, "large text must be able to relax density")
    req(density.get("touchAssistanceMayRelaxDensity") is True, "Touch Assistance must be able to relax density")
    req(density.get("mayChangeSemantics") is False, "density may not change semantics")
    req(density.get("mayHideEssentialNavigation") is False, "density may not hide essential navigation")

    wallpaper = contract.get("wallpaperAtmosphere", {})
    req(wallpaper.get("sourceAuthority") == "consumer-platform-adapter", "consumer/platform adapter must own wallpaper source acquisition")
    req(wallpaper.get("acceptedInput") == "producer-supplied-local-rgb-summary", "wallpaper input must remain a bounded local RGB summary")
    req(wallpaper.get("maximumAlpha") == 0.12, "wallpaper atmosphere alpha cap must remain 0.12")
    req(wallpaper.get("maximumChromaRetention") == 0.28, "wallpaper chroma retention cap must remain 0.28")
    for key in ("directPixelAcquisitionOwnedByGlaze", "remoteContentRequired", "telemetryAllowed", "rawWallpaperPixelsRetained", "wallpaperImageTransmissionAllowed"):
        req(wallpaper.get(key) is False, f"wallpaper privacy rule must be false: {key}")
    for key in ("reducedTransparencyDisables", "forcedColorsDisables", "invalidInputFailsClosedToTransparent"):
        req(wallpaper.get(key) is True, f"wallpaper accessibility/fallback rule must be true: {key}")

    accessibility = contract.get("accessibilityOverrides", {})
    for key in ("accessibilityOutranksPersonalization", "forcedColorsOverridesAccentRendering", "forcedColorsForcesSolidMaterial", "reducedTransparencyDisablesWallpaperAtmosphere", "reducedTransparencyForcesSolidMaterial", "reducedMotionOverridesDecorativeMotion", "largeTextMayRelaxDensity", "touchAssistanceRaisesHitAreaFloor"):
        req(accessibility.get(key) is True, f"accessibility precedence rule must be true: {key}")
    for key in ("personalizationMayCounteractLargeText", "personalizationMayHideVisibleFocus"):
        req(accessibility.get(key) is False, f"accessibility precedence rule must be false: {key}")

    persistence = contract.get("persistenceAndSync", {})
    req(persistence.get("persistenceAuthority") == "consumer-platform-adapter", "consumer adapter must own persistence")
    req(persistence.get("adapterInterfaceImplemented") is True, "bounded persistence adapter interface must be implemented")
    req(persistence.get("directPersistenceOwnedByGlaze") is False, "Glaze must not own direct persistence")
    req(persistence.get("crossDeviceSyncImplementedByThisWorkstream") is False, "Personalization must not claim cross-device sync")
    req(persistence.get("privacyReviewRequiredBeforeCrossDeviceSync") is True, "cross-device sync must retain a privacy gate")

    continuity = contract.get("continuity", {})
    preserved = set(continuity.get("preserve", []))
    for item in ("current-task", "selection", "typed-input", "unsaved-work", "focus", "product-identity"):
        req(item in preserved, f"Personalization continuity must preserve {item}")
    for key in ("preferenceChangeMayReloadPage", "preferenceChangeMayResetSelection", "preferenceChangeMayDiscardDraft", "preferenceChangeMayResetFocus"):
        req(continuity.get(key) is False, f"Personalization continuity rule must be false: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for symbol in ("normalizePersonalization", "resolveAppearance", "deriveWallpaperAtmosphere", "resolvePersonalization", "serializePersonalization", "deserializePersonalization", "createPersonalizationController", "personalizationCandidate"):
        req(symbol in runtime, f"Personalization runtime missing API: {symbol}")
    for required_import in ("glaze-v1.3-dynamic-color.candidate.mjs", "glaze-v1.3-accessibility.candidate.mjs"):
        req(required_import in runtime, f"Personalization runtime must compose {required_import}")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "localStorage", "sessionStorage", "indexedDB", "getImageData(", "drawImage(", "FileReader("):
        req(forbidden not in runtime, f"Personalization runtime contains forbidden direct network/storage/pixel primitive: {forbidden}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("native-system-appearance-adapter-acceptance", "native-wallpaper-source-adapter-acceptance", "consumer-platform-persistence-acceptance", "cross-device-preference-sync", "human-optical-personalization-acceptance", "assistive-technology-acceptance", "physical-device-acceptance", "complete-native-platform-parity", "production-performance-acceptance", "release-candidate", "stable", "consumer-conformance"):
        req(item in not_established, f"Personalization evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Personalization validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Personalization: PASS")
    print(f"Boundary: preserved V1.3 bounded local personalization remains validated against its 1.2.0 source baseline; live current Stable is {version}. Native adapter, persistence, sync, physical-device, human, and production acceptance remain separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
