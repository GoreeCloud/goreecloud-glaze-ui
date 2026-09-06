#!/usr/bin/env python3
"""Emit exact-head, fail-closed GLAZE UI V1.2 Personalization readiness evidence."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/v1.2/personalization-appearance.candidate.json"
RUNTIME = ROOT / "js/glaze-v1.2-personalization.candidate.mjs"
CSS = ROOT / "css/glaze-v1.2-personalization-appearance.candidate.css"
REFERENCE = ROOT / "reference/v1.2/personalization-appearance.html"
RENDERED_VALIDATOR = ROOT / "scripts/validate_glaze_v1_2_personalization_appearance_rendered.py"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-personalization-appearance.yml"
VERSION = ROOT / "VERSION"
LIFECYCLE = ROOT / "registry/lifecycle.json"
ARTIFACT = ROOT / "artifacts/glaze-v1.2-personalization-readiness.json"


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_revision() -> str:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None, "Git HEAD is not an immutable 40-character revision")
    return revision


def validate() -> dict[str, Any]:
    sources = [CONTRACT, RUNTIME, CSS, REFERENCE, RENDERED_VALIDATOR, WORKFLOW, VERSION, LIFECYCLE]
    for source in sources:
        require(source.is_file(), f"missing {source.relative_to(ROOT)}")

    require(VERSION.read_text(encoding="utf-8").strip() == "1.1.0", "Stable VERSION moved")
    lifecycle = load_json(LIFECYCLE)
    require(lifecycle.get("currentStable") == "1.1.0" and lifecycle.get("currentOfficial") == "1.1.0", "Stable lifecycle authority moved")
    require(lifecycle.get("activeCandidate") == "1.2.0-candidate", "active Candidate identity drifted")

    contract = load_json(CONTRACT)
    require(contract.get("version") == "1.2.0-candidate", "Personalization Candidate version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Personalization lifecycle boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Personalization Stable baseline drifted")

    appearance = contract.get("appearance", {})
    require(appearance.get("browserSystemAdapterImplemented") is True, "browser Follow System adapter missing")
    require(appearance.get("nativeSystemAdapterAcceptanceRequired") is True, "native Follow System acceptance was silently removed")

    persistence = contract.get("persistenceAndSync", {})
    require(persistence.get("persistenceAuthority") == "consumer-platform-adapter", "persistence authority drifted")
    require(persistence.get("adapterInterfaceImplemented") is True and persistence.get("webStorageAdapterHelperAvailable") is True, "consumer persistence adapter evidence missing")
    require(persistence.get("directPersistenceOwnedByGlaze") is False, "Glaze took persistence ownership")
    require(persistence.get("syncAuthority") == "separate-governed-goreecloud-sync-integration", "cross-device sync authority drifted")
    require(persistence.get("crossDeviceSyncImplementedByThisCandidate") is False, "Personalization overclaimed cross-device sync")

    wallpaper = contract.get("atmosphereProfiles", {}).get("wallpaperSampling", {})
    require(wallpaper.get("implementationStatus") == "bounded-local-derivation-implemented", "bounded wallpaper atmosphere status drifted")
    require(wallpaper.get("inputAuthority") == "consumer-platform-adapter", "wallpaper source authority drifted")
    require(wallpaper.get("acceptedInput") == "producer-supplied-local-rgb-summary", "wallpaper input broadened beyond RGB summary")
    require(wallpaper.get("directPixelAcquisitionOwnedByGlaze") is False, "Glaze took wallpaper pixel acquisition authority")
    require(wallpaper.get("maximumAlpha") == 0.12 and wallpaper.get("maximumChromaRetention") == 0.28, "wallpaper atmosphere bounds drifted")
    require(wallpaper.get("remoteContentRequired") is False and wallpaper.get("telemetryAllowed") is False and wallpaper.get("rawWallpaperPixelsRetained") is False, "wallpaper privacy boundary weakened")

    runtime_contract = contract.get("runtimeContract", {})
    for key in (
        "normalizationFailsClosedToGovernedDefaults",
        "browserFollowSystemUsesPrefersColorScheme",
        "systemChangesMayReResolveFollowSystem",
        "manualAppearanceDoesNotTrackSystemChanges",
        "persistenceAdapterIsOptional",
        "malformedStoredPreferenceFallsBackSafely",
        "wallpaperInputIsProducerSuppliedRgbOnly",
        "wallpaperInvalidInputFailsClosedToTransparent",
        "wallpaperAtmosphereIsLocallyDerived",
    ):
        require(runtime_contract.get(key) is True, f"runtime fail-closed rule drifted: {key}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for marker in (
        "export function createBrowserSystemAppearanceAdapter",
        "export function createWebStoragePreferenceAdapter",
        "export function deriveWallpaperAtmosphere",
        "export function applyWallpaperAtmosphere",
        "boundedWallpaperAtmosphereDerivationImplemented: true",
        "directWallpaperPixelAcquisitionImplemented: false",
        "directCrossDeviceSyncImplemented: false",
    ):
        require(marker in runtime, f"runtime evidence marker missing: {marker}")
    for forbidden in (
        "fetch(", "XMLHttpRequest", "navigator.sendBeacon", "WebSocket", "indexedDB.open",
        "drawImage(", "getImageData(", "createImageBitmap(", "FileReader(",
    ):
        require(forbidden not in runtime, f"ungoverned remote/pixel mechanism introduced: {forbidden}")

    css = CSS.read_text(encoding="utf-8")
    require("--glz12-wallpaper-atmosphere: transparent" in css and "var(--glz12-wallpaper-atmosphere)" in css, "wallpaper atmosphere CSS binding missing")
    require('data-glz-transparency="reduced"' in css and "background-image: none !important" in css, "Reduced Transparency no longer supersedes atmosphere")

    reference = REFERENCE.read_text(encoding="utf-8")
    for marker in (
        "Glaze never fetches, decodes, or inspects wallpaper pixels",
        "Cross-device sync remains separately governed by GoreeCloud Sync",
        "applyWallpaperAtmosphere",
        "deriveWallpaperAtmosphere",
    ):
        require(marker in reference, f"reference boundary marker missing: {marker}")

    rendered_validator = RENDERED_VALIDATOR.read_text(encoding="utf-8")
    for marker in (
        "wallpaper atmosphere exceeded bounded intensity/chroma",
        "invalid wallpaper input did not fail closed",
        "Reduced Transparency did not suppress decorative atmosphere including wallpaper-derived color",
        "Follow System did not react to system change",
        "persistence adapter round trip failed",
    ):
        require(marker in rendered_validator, f"rendered acceptance marker missing: {marker}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "Personalization workflow is not exact-head pinned")
    require("validate_glaze_v1_2_personalization_appearance_rendered.py" in workflow, "Personalization workflow lost rendered acceptance")
    require("actions/upload-artifact@" in workflow and "glaze-v1.2-personalization-appearance-" in workflow, "Personalization workflow no longer publishes review evidence")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    required_open = {
        "native-follow-system-platform-adapter-acceptance",
        "consumer-platform-persistence-acceptance",
        "cross-device-preference-sync",
        "native-wallpaper-source-adapter-acceptance",
        "human-visual-review",
        "assistive-technology-acceptance",
        "native-platform-parity",
        "physical-device-acceptance",
        "release-candidate",
        "stable",
        "consumer-conformance",
    }
    require(required_open.issubset(not_established), "Personalization evidence boundary overclaimed an open acceptance class")

    revision = head_revision()
    return {
        "schemaVersion": 1,
        "kind": "glaze-v1.2-personalization-candidate-readiness",
        "sourceRevision": revision,
        "observedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "version": "1.2.0-candidate",
        "stableBaseline": "1.1.0",
        "consumerEligible": False,
        "boundedBrowserSystemAdapterEvidence": True,
        "boundedConsumerPersistenceAdapterInterfaceEvidence": True,
        "boundedLocalWallpaperAtmosphereDerivationEvidence": True,
        "crossDeviceSyncImplementedByGlaze": False,
        "nativeSystemAdapterAccepted": False,
        "consumerPlatformPersistenceAccepted": False,
        "nativeWallpaperSourceAdapterAccepted": False,
        "humanVisualAccepted": False,
        "physicalDeviceAccepted": False,
        "nativePlatformParityEstablished": False,
        "rcReady": False,
        "stableReady": False,
        "productionReady": False,
        "sourceDigestsSha256": {str(path.relative_to(ROOT)): sha256(path) for path in sources},
        "openEvidence": sorted(required_open),
        "boundary": "Bounded exact-head browser/source readiness only; dedicated rendered workflow, native adapters, human review, physical-device acceptance, RC, Stable, production acceptance, and consumer conformance remain independent.",
    }


def main() -> int:
    try:
        report = validate()
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        require(ARTIFACT.stat().st_size > 1000, "Personalization readiness artifact unexpectedly small")
        print(f"PASS: bounded V1.2 Personalization readiness evidence emitted at {report['sourceRevision']}; native/human/RC/Stable claims remain false.")
        return 0
    except (ValidationError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"FAIL: V1.2 Personalization readiness validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
