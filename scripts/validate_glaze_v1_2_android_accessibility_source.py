#!/usr/bin/env python3
"""Fail-closed exact-head source readiness for V1.2 Android accessibility.

This source gate does not run an emulator or assistive technology. It proves
that the checked-out Candidate revision retains the Android accessibility
source contract, the bounded runtime validator, and CI ownership without
converting source evidence into human, physical-device, RC, or Stable claims.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/MainActivity.java"
MANIFEST = ROOT / "reference/v1.2/native/android/app/src/main/AndroidManifest.xml"
RUNTIME = ROOT / "scripts/validate_glaze_v1_2_android_accessibility_runtime.py"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-android-native.yml"
ARTIFACT = ROOT / "artifacts/glaze-v1.2-android-accessibility-source-readiness.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def exact_revision() -> str:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(SHA40.fullmatch(revision) is not None, f"invalid Git HEAD: {revision!r}")
    expected = os.environ.get("GLAZE_SOURCE_REVISION", "").strip()
    if expected:
        require(expected == revision, f"exact source mismatch: checkout={revision}, expected={expected}")
    return revision


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, object]:
    for path in (SOURCE, MANIFEST, RUNTIME, WORKFLOW):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    source = SOURCE.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    revision = exact_revision()

    for marker in (
        "MIN_TOUCH_DP = 48",
        "TOUCH_ASSISTANCE_DP = 56",
        'primary.setContentDescription("Primary action")',
        'secondaryAction.setContentDescription("Secondary action")',
        "button.setContentDescription(name + \": \" + state",
        "Reduced Transparency: enabled",
        "physical-device",
        "TalkBack",
    ):
        require(marker in source, f"Android accessibility source marker missing: {marker}")

    joined = source + "\n" + manifest
    for forbidden in (
        "AccessibilityService",
        "BIND_ACCESSIBILITY_SERVICE",
        "enabled_accessibility_services",
    ):
        require(forbidden not in joined, f"bounded reference may not own accessibility service authority: {forbidden}")

    for marker in (
        '"Wi-Fi"',
        '"Bluetooth"',
        '"Night Light"',
        '"Performance"',
        '"Airplane Mode"',
        '"Focus"',
        '"Primary action"',
        '"Secondary action"',
        "contentDescriptionPresent",
        "48 dp default target floor",
        "56 dp Touch Assistance target floor",
        "200% text-scale task and control reachability",
        "Reduced Transparency semantic-state reachability",
        "TalkBack acceptance or certification",
        "physical-device accessibility qualification",
    ):
        require(marker in runtime, f"Android accessibility runtime gate marker missing: {marker}")

    require(
        "python3 scripts/validate_glaze_v1_2_android_accessibility_runtime.py" in workflow,
        "Android native workflow no longer runs machine accessibility evidence",
    )
    require(
        ".artifacts/glaze-v1.2-android-native/android-accessibility-evidence.json" in workflow,
        "Android native workflow no longer uploads accessibility evidence",
    )

    paths = (SOURCE, MANIFEST, RUNTIME, WORKFLOW)
    return {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2",
        "version": "1.2.0-candidate",
        "lifecycle": "candidate-source-readiness",
        "sourceRevision": revision,
        "consumerEligible": False,
        "promotionReady": False,
        "rcReady": False,
        "stableReady": False,
        "productionReady": False,
        "evidenceKind": "android-machine-accessibility-source-readiness",
        "sourceContract": {
            "defaultTargetFloorDp": 48,
            "touchAssistanceTargetFloorDp": 56,
            "stateBearingQuickSettingsContentDescriptionsRequired": True,
            "reducedTransparencySemanticStateRequired": True,
            "accessibilityServiceOwned": False,
        },
        "runtimeGateRequired": True,
        "sourceDigestsSha256": {str(path.relative_to(ROOT)): digest(path) for path in paths},
        "notEstablished": [
            "android-emulator-runtime-pass-by-this-source-gate",
            "TalkBack acceptance or certification",
            "Switch Access acceptance",
            "Voice Access acceptance",
            "human accessibility review",
            "physical-device accessibility qualification",
            "OEM accessibility-service interoperability",
            "complete native accessibility parity",
            "downstream consumer conformance",
            "Release Candidate designation",
            "Stable promotion",
        ],
    }


def main() -> int:
    try:
        evidence = validate()
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        require(ARTIFACT.stat().st_size > 1000, "Android accessibility source-readiness artifact unexpectedly small")
        print(
            "PASS: GLAZE UI V1.2 Android accessibility source readiness is exact-head bound; "
            "runtime, AT, physical-device, RC, Stable, production, and consumer claims remain blocked."
        )
        return 0
    except Exception as error:
        print(f"Android accessibility source readiness failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
