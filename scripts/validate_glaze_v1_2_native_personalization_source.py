#!/usr/bin/env python3
"""Fail-closed exact-head source readiness for GLAZE UI V1.2 native Personalization adapters.

This validator proves source presence, contract alignment, authority boundaries, and
CI wiring for the Android and Linux Candidate adapter references. It does not claim
that the native CI jobs passed, that physical devices were qualified, or that V1.2
is Release Candidate or Stable.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/glaze-v1.2-native-personalization-source-readiness.json"
VERSION = ROOT / "VERSION"
LIFECYCLE = ROOT / "registry/lifecycle.json"
CONTRACT = ROOT / "contracts/v1.2/personalization-appearance.candidate.json"

ANDROID_SOURCE = ROOT / "reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/PersonalizationActivity.java"
ANDROID_MANIFEST = ROOT / "reference/v1.2/native/android/app/src/main/AndroidManifest.xml"
ANDROID_VALIDATOR = ROOT / "scripts/validate_glaze_v1_2_android_personalization_runtime.py"
ANDROID_WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-android-native.yml"
ANDROID_ACCEPTANCE = ROOT / "acceptance/v1.2-android-native-candidate.md"

LINUX_SOURCE = ROOT / "reference/v1.2/native/linux-gtk/personalization.py"
LINUX_VALIDATOR = ROOT / "scripts/validate_glaze_v1_2_linux_personalization_runtime.py"
LINUX_WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-linux-native.yml"
LINUX_ACCEPTANCE = ROOT / "acceptance/v1.2-linux-native-candidate.md"


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_revision() -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, "HEAD is not an immutable revision")
    return value


def require_markers(text: str, markers: tuple[str, ...], label: str) -> None:
    for marker in markers:
        require(marker in text, f"{label} missing source marker: {marker}")


def validate_contract() -> dict[str, object]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract.get("version") == "1.2.0-candidate", "Personalization contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Personalization contract lifecycle boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Personalization Stable baseline drifted")

    appearance = contract.get("appearance", {})
    require(appearance.get("platformAdapterOwnsSystemResolution") is True, "platform system-resolution authority drifted")
    require(appearance.get("nativeSystemAdapterReferencesImplemented") is True, "native system adapter reference status drifted")
    require(appearance.get("nativeSystemAdapterReferencePlatforms") == ["android", "linux-gtk"], "native system adapter platform list drifted")
    require(appearance.get("nativeSystemAdapterAcceptanceRequired") is True, "native system adapter acceptance gate disappeared")

    wallpaper = contract.get("atmosphereProfiles", {}).get("wallpaperSampling", {})
    require(wallpaper.get("inputAuthority") == "consumer-platform-adapter", "wallpaper input authority drifted")
    require(wallpaper.get("acceptedInput") == "producer-supplied-local-rgb-summary", "wallpaper native input broadened")
    require(wallpaper.get("directPixelAcquisitionOwnedByGlaze") is False, "Glaze took wallpaper acquisition ownership")
    require(wallpaper.get("nativeRgbSummaryAdapterReferencesImplemented") is True, "native RGB-summary adapter reference status drifted")
    require(wallpaper.get("nativeRgbSummaryAdapterReferencePlatforms") == ["android", "linux-gtk"], "native wallpaper adapter platform list drifted")
    require(wallpaper.get("nativeWallpaperSourceAdapterAcceptanceRequired") is True, "native wallpaper-source acceptance gate disappeared")
    require(wallpaper.get("maximumAlpha") == 0.12 and wallpaper.get("maximumChromaRetention") == 0.28, "wallpaper bounds drifted")

    persistence = contract.get("persistenceAndSync", {})
    require(persistence.get("persistenceAuthority") == "consumer-platform-adapter", "persistence authority drifted")
    require(persistence.get("directPersistenceOwnedByGlaze") is False, "Glaze took persistence ownership")
    require(persistence.get("syncAuthority") == "separate-governed-goreecloud-sync-integration", "sync authority drifted")
    require(persistence.get("crossDeviceSyncImplementedByThisCandidate") is False, "native adapter work overclaimed cross-device sync")

    runtime = contract.get("runtimeContract", {})
    require(runtime.get("nativeReferenceFollowSystemAdaptersImplemented") is True, "native Follow System runtime declaration drifted")
    require(runtime.get("nativeReferenceReducedTransparencySuppressesWallpaperAtmosphere") is True, "native Reduced Transparency precedence declaration drifted")

    implementation = contract.get("implementation", {}).get("nativeAdapterReferences", {})
    require(implementation.get("android", {}).get("source") == str(ANDROID_SOURCE.relative_to(ROOT)), "Android native source path declaration drifted")
    require(implementation.get("android", {}).get("validator") == str(ANDROID_VALIDATOR.relative_to(ROOT)), "Android native validator path declaration drifted")
    require(implementation.get("linuxGtk", {}).get("source") == str(LINUX_SOURCE.relative_to(ROOT)), "Linux native source path declaration drifted")
    require(implementation.get("linuxGtk", {}).get("validator") == str(LINUX_VALIDATOR.relative_to(ROOT)), "Linux native validator path declaration drifted")
    require(implementation.get("sourceReadinessValidator") == str(Path(__file__).resolve().relative_to(ROOT)), "native source-readiness validator declaration drifted")

    implemented = set(contract.get("evidenceBoundary", {}).get("implemented", []))
    require({
        "android-follow-system-adapter-reference",
        "linux-gtk-follow-system-adapter-reference",
        "native-rgb-summary-atmosphere-adapter-references",
        "native-reduced-transparency-atmosphere-precedence-source",
    }.issubset(implemented), "native implementation evidence declarations are incomplete")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({
        "native-follow-system-platform-adapter-acceptance",
        "consumer-platform-persistence-acceptance",
        "cross-device-preference-sync",
        "native-wallpaper-source-adapter-acceptance",
        "assistive-technology-acceptance",
        "native-platform-parity",
        "physical-device-acceptance",
        "release-candidate",
        "stable",
        "consumer-conformance",
    }.issubset(not_established), "native adapter contract overclaimed an open evidence class")
    return contract


def validate() -> dict[str, object]:
    sources = [
        VERSION,
        LIFECYCLE,
        CONTRACT,
        ANDROID_SOURCE,
        ANDROID_MANIFEST,
        ANDROID_VALIDATOR,
        ANDROID_WORKFLOW,
        ANDROID_ACCEPTANCE,
        LINUX_SOURCE,
        LINUX_VALIDATOR,
        LINUX_WORKFLOW,
        LINUX_ACCEPTANCE,
    ]
    for path in sources:
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    require(VERSION.read_text(encoding="utf-8").strip() == "1.1.0", "Stable VERSION moved")
    lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
    require(lifecycle.get("currentStable") == "1.1.0" and lifecycle.get("currentOfficial") == "1.1.0", "Stable lifecycle authority moved")
    require(lifecycle.get("activeCandidate") == "1.2.0-candidate", "V1.2 Candidate identity drifted")
    validate_contract()

    android = ANDROID_SOURCE.read_text(encoding="utf-8")
    manifest = ANDROID_MANIFEST.read_text(encoding="utf-8")
    require_markers(android, (
        "normalizeAppearancePreference",
        "resolveAppearance",
        "Configuration.UI_MODE_NIGHT_MASK",
        "normalizeClarity",
        "deriveWallpaperAtmosphere",
        "WALLPAPER_MAX_ALPHA = 0.12f",
        "WALLPAPER_MAX_CHROMA_RETENTION = 0.28f",
        "wallpaperAtmosphere = reducedTransparency ? null : readWallpaperAtmosphere()",
        "atmosphericMaterial",
        "MIN_TOUCH_DP = 48",
        "TOUCH_ASSISTANCE_DP = 56",
        "no persistence, synchronization, wallpaper acquisition, telemetry, network",
    ), "Android Personalization adapter")
    require('android:name=".PersonalizationActivity"' in manifest, "Android Personalization activity registration missing")
    for forbidden in (
        "android.permission.INTERNET",
        "WallpaperManager",
        "SharedPreferences",
        "BitmapFactory",
        "getPixels(",
        "HttpURLConnection",
        "WebView",
    ):
        require(forbidden not in android and forbidden not in manifest, f"Android adapter acquired prohibited authority: {forbidden}")

    android_validator = ANDROID_VALIDATOR.read_text(encoding="utf-8")
    require_markers(android_validator, (
        "case_follow_system_light",
        "case_follow_system_dark_touch",
        "case_manual_deep_dark",
        "case_reduced_transparency",
        "case_invalid_fallback",
        "not physical-device qualification",
        "not TalkBack acceptance",
        "not consumer persistence acceptance",
        "not cross-device synchronization",
        "not Release Candidate acceptance",
        "not V1.2 Stable promotion",
    ), "Android Personalization validator")
    android_workflow = ANDROID_WORKFLOW.read_text(encoding="utf-8")
    require("github.event.pull_request.head.sha || github.sha" in android_workflow, "Android native workflow lost exact-head checkout")
    require("validate_glaze_v1_2_android_runtime.py" in android_workflow and "validate_glaze_v1_2_android_personalization_runtime.py" in android_workflow, "Android native workflow does not run both native evidence classes")
    require("android-personalization-evidence.json" in android_workflow, "Android native workflow does not upload Personalization evidence")

    linux = LINUX_SOURCE.read_text(encoding="utf-8")
    require_markers(linux, (
        "org.gnome.desktop.interface",
        "color-scheme",
        "Gtk.Settings/gtk-application-prefer-dark-theme",
        "normalize_appearance",
        "normalize_clarity",
        "derive_wallpaper_atmosphere",
        "WALLPAPER_MAX_ALPHA = 0.12",
        "WALLPAPER_MAX_CHROMA_RETENTION = 0.28",
        "self.atmosphere = None if self.args.reduced_transparency else derived",
        "neutral_surface_channel",
        "composite_atmosphere",
        "MIN_TARGET_PX = 48",
        "TOUCH_ASSISTANCE_PX = 56",
        "owns no persistence",
    ), "Linux Personalization adapter")
    for forbidden in (
        "requests.",
        "urllib.",
        "socket.",
        "WebKit",
        "GdkPixbuf",
        "Image.open",
        "settings.set_",
    ):
        require(forbidden not in linux, f"Linux adapter acquired prohibited authority: {forbidden}")

    linux_validator = LINUX_VALIDATOR.read_text(encoding="utf-8")
    require_markers(linux_validator, (
        "follow-system-light-clear",
        "follow-system-dark-dense-touch",
        "manual-deep-dark",
        "reduced-transparency",
        "invalid-input-fallback",
        "not compositor-wide Wayland backdrop blur fidelity",
        "not physical-display qualification",
        "not assistive-technology acceptance",
        "not cross-device synchronization",
        "not Release Candidate acceptance",
        "not V1.2 Stable promotion",
    ), "Linux Personalization validator")
    linux_workflow = LINUX_WORKFLOW.read_text(encoding="utf-8")
    require("github.event.pull_request.head.sha || github.sha" in linux_workflow, "Linux native workflow lost exact-head checkout")
    require("validate_glaze_v1_2_linux_runtime.py" in linux_workflow and "validate_glaze_v1_2_linux_personalization_runtime.py" in linux_workflow, "Linux native workflow does not run both native evidence classes")
    require("linux-personalization-evidence.json" in linux_workflow, "Linux native workflow does not upload Personalization evidence")

    for acceptance_path in (ANDROID_ACCEPTANCE, LINUX_ACCEPTANCE):
        acceptance = acceptance_path.read_text(encoding="utf-8")
        require("Candidate" in acceptance, f"{acceptance_path.name} lost Candidate boundary")
        require("Stable" in acceptance and "physical" in acceptance.lower(), f"{acceptance_path.name} lost Stable/physical-device boundary")
        require("cross-device" in acceptance.lower(), f"{acceptance_path.name} lost cross-device sync boundary")

    revision = head_revision()
    return {
        "schemaVersion": 1,
        "kind": "glaze-v1.2-native-personalization-source-readiness",
        "sourceRevision": revision,
        "observedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "version": "1.2.0-candidate",
        "stableBaseline": "1.1.0",
        "consumerEligible": False,
        "contractAligned": True,
        "androidAdapterSourceEstablished": True,
        "androidExactHeadCiWiringEstablished": True,
        "linuxAdapterSourceEstablished": True,
        "linuxExactHeadCiWiringEstablished": True,
        "boundedNativeFollowSystemSourceEvidence": True,
        "boundedNativeClaritySourceEvidence": True,
        "boundedNativeRgbSummaryAtmosphereSourceEvidence": True,
        "reducedTransparencyPrecedenceSourceEvidence": True,
        "directWallpaperAcquisitionOwnedByGlaze": False,
        "consumerPersistenceOwnedByGlaze": False,
        "crossDeviceSyncImplementedByGlaze": False,
        "nativeCiPassEstablishedByThisArtifact": False,
        "nativePlatformAcceptanceEstablished": False,
        "physicalDeviceAcceptanceEstablished": False,
        "assistiveTechnologyAcceptanceEstablished": False,
        "humanOpticalAcceptanceEstablished": False,
        "rcReady": False,
        "stableReady": False,
        "productionReady": False,
        "sourceDigestsSha256": {str(path.relative_to(ROOT)): sha256(path) for path in sources},
        "openEvidence": [
            "android-exact-head-emulator-pass",
            "linux-exact-head-headless-native-pass",
            "physical-device-native-personalization-acceptance",
            "oem-and-compositor-optical-acceptance",
            "assistive-technology-native-acceptance",
            "consumer-platform-persistence-acceptance",
            "cross-device-preference-sync",
            "native-wallpaper-source-adapter-acceptance",
            "human-optical-acceptance",
            "release-candidate",
            "stable",
            "consumer-conformance",
        ],
        "boundary": "Exact-head native adapter contract, source, and CI wiring only. Native job success, physical-device/platform qualification, accessibility acceptance, persistence/sync, human approval, RC, Stable, production, and consumer conformance remain independent.",
    }


def main() -> int:
    try:
        report = validate()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        require(OUT.stat().st_size > 1700, "native Personalization source-readiness artifact unexpectedly small")
        print(f"PASS: bounded native Personalization source readiness emitted at {report['sourceRevision']}; native CI/physical/RC/Stable claims remain false.")
        return 0
    except (ValidationError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"FAIL: V1.2 native Personalization source readiness failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
