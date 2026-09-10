#!/usr/bin/env python3
"""Validate GLAZE UI V1.3.1 accessibility + interaction hardening without changing lifecycle authority."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.3.0"
CONTRACT = "contracts/v1.3.1/accessibility-interaction-hardening.candidate.json"
RUNTIME = "js/glaze-v1.3.1-accessibility-interaction-hardening.candidate.mjs"
STYLESHEET = "css/glaze-v1.3.1-accessibility-interaction-hardening.candidate.css"
REFERENCE = "reference/v1.3/accessibility-interaction-hardening.html"
TESTS = "tests/glaze-v1.3.1-accessibility-interaction-hardening.test.mjs"
DEPENDENCIES = [
    "contracts/v1.3/accessibility.candidate.json",
    "contracts/v1.3/component-experience.candidate.json",
    "contracts/v1.3/motion-semantics.candidate.json",
    "contracts/v1.3/reachability.candidate.json",
]

def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in [CONTRACT, RUNTIME, STYLESHEET, REFERENCE, TESTS, *DEPENDENCIES, "VERSION", "registry/lifecycle.json"]:
        req((ROOT / path).is_file(), f"missing hardening artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3.1 accessibility + interaction hardening validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must remain 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.3.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "hardening work must not activate a lifecycle Candidate")
    req(lifecycle.get("plannedNext") == "1.3.1-candidate", "plannedNext must retain the governed V1.3.1 candidate line")

    contract = load(CONTRACT)
    req(contract.get("hardeningTrack") == "V1.3.1", "hardening track must be V1.3.1")
    req(contract.get("releaseLifecycle") == "development-only", "hardening artifact must remain development-only")
    req(contract.get("lifecycleAuthority") is False, "hardening artifact must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "hardening artifact must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "hardening artifact must build from current V1.3.0 Stable")
    for path in DEPENDENCIES:
        req(path in set(contract.get("extends", [])), f"hardening inheritance missing {path}")

    presentation = contract.get("interactionPresentation", {})
    req(presentation.get("statePriority") == ["disabled", "focus-visible", "pressed", "hover", "current-or-selected", "rest"], "interaction state priority mismatch")
    req(presentation.get("focusVisible", {}).get("focusIndicatorMustRemainDistinctFromCurrentOrSelectedState") is True, "focus must remain distinct from semantic state")
    req(presentation.get("hover", {}).get("requiredToDiscoverAction") is False, "hover may not be required to discover an action")
    req(presentation.get("pressed", {}).get("semanticActivationMustNotWaitForAnimation") is True, "activation may not wait for animation")
    req(presentation.get("disabled", {}).get("activationAllowed") is False, "disabled controls may not activate")

    reachability = contract.get("inputAndReachability", {})
    req(reachability.get("defaultMinimumInteractiveTargetPx") == 48, "default target floor must be 48px")
    req(reachability.get("coarsePointerReferenceMinimumInteractiveTargetPx") == 56, "coarse-pointer reference floor must be 56px")
    req(reachability.get("hoverOnlyCriticalActionAllowed") is False, "hover-only critical actions must be prohibited")

    implementation = contract.get("implementation", {})
    for key, expected in {
        "runtime": RUNTIME,
        "stylesheet": STYLESHEET,
        "reference": REFERENCE,
        "tests": TESTS,
        "validator": "scripts/validate_glaze_v1_3_1_accessibility_interaction_hardening.py",
        "workflow": ".github/workflows/glaze-v1.3.1-accessibility-interaction-hardening.yml",
    }.items():
        req(implementation.get(key) == expected, f"implementation path mismatch: {key}")

    css = (ROOT / STYLESHEET).read_text(encoding="utf-8")
    for marker in (
        ":focus-visible",
        "@media (hover: hover) and (pointer: fine)",
        ":disabled",
        '[aria-disabled="true"]',
        "@media (pointer: coarse)",
        "min-block-size: 56px",
        "@media (prefers-reduced-motion: reduce)",
        "@media (prefers-reduced-transparency: reduce)",
        "@media (forced-colors: active)",
        "outline: 3px solid Highlight",
    ):
        req(marker in css, f"hardening stylesheet missing marker: {marker}")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    req("data-glaze-v1-3-1-hardening" in reference, "reference must opt into the scoped hardening layer")
    req("../../css/glaze-v1.3.0.css" in reference, "reference must use the current V1.3.0 Stable rendering baseline")
    req("../../css/glaze-v1.3.1-accessibility-interaction-hardening.candidate.css" in reference, "reference must load the hardening stylesheet")
    req('aria-current="page"' in reference, "reference must demonstrate current-state separation")
    req('aria-pressed="false"' in reference, "reference must demonstrate a pressed/toggle semantic state")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for symbol in (
        "resolveHardeningTargetFloor",
        "resolveInteractionPresentation",
        "auditInteractionPresentation",
        "createInteractionHardeningResolver",
        "accessibilityInteractionHardeningCandidate",
    ):
        req(symbol in runtime, f"hardening runtime missing API: {symbol}")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "setInterval(", "requestAnimationFrame(", "localStorage", "sessionStorage", "indexedDB"):
        req(forbidden not in runtime, f"hardening runtime contains forbidden network/autonomous/storage primitive: {forbidden}")

    tests = (ROOT / TESTS).read_text(encoding="utf-8")
    for phrase in ("forced colors", "Reduced Motion", "disabled state", "coarse-pointer", "current state"):
        req(phrase in tests, f"hardening tests missing coverage phrase: {phrase}")

    for release_path in (
        "css/glaze-v1.3.1.css",
        "js/glaze-v1.3.1.mjs",
    ):
        req(not (ROOT / release_path).exists(), f"hardening work must not create V1.3.1 release entrypoint: {release_path}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in (
        "manual-keyboard-acceptance",
        "manual-screen-reader-acceptance",
        "manual-switch-or-voice-access-acceptance",
        "human-optical-acceptance",
        "physical-device-acceptance",
        "native-platform-parity",
        "production-performance-acceptance",
        "retroactive-v1.3.0-qualification-claim",
        "v1.3.1-release-candidate",
        "v1.3.1-stable",
        "consumer-conformance",
    ):
        req(item in not_established, f"hardening evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3.1 accessibility + interaction hardening validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3.1 accessibility + interaction hardening: PASS")
    print("Boundary: current V1.3.0 Stable remains unchanged; V1.3.1 focus-visible, microstate, Reduced Motion, Forced Colors, coarse-pointer, and semantic-state hardening are machine-validated without V1.3.1 lifecycle promotion or manual acceptance claims.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
