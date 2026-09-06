#!/usr/bin/env python3
"""Emulator evidence for the GLAZE UI V1.2 Android Personalization adapter reference.

This proves bounded Android framework behavior only. It is not physical-device,
TalkBack, OEM visual, consumer persistence, wallpaper-source acquisition,
cross-device synchronization, production, RC, or Stable acceptance.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".artifacts" / "glaze-v1.2-android-native"
SOURCE = ROOT / "reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/PersonalizationActivity.java"
MANIFEST = ROOT / "reference/v1.2/native/android/app/src/main/AndroidManifest.xml"
PACKAGE = "com.goreecloud.glazeui.reference.v12"
ACTIVITY = f"{PACKAGE}/.PersonalizationActivity"
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def run(*args: str, text: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, text=text, capture_output=True)


def adb(serial: str, *args: str, text: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    return run("adb", "-s", serial, *args, text=text, check=check)


def exact_revision() -> str:
    revision = run("git", "-C", str(ROOT), "rev-parse", "HEAD").stdout.strip()
    if not SHA40.fullmatch(revision):
        raise SystemExit(f"could not resolve exact source revision: {revision!r}")
    expected = os.environ.get("GLAZE_SOURCE_REVISION", "").strip()
    if expected and expected != revision:
        raise SystemExit(f"exact source mismatch: checkout={revision}, expected={expected}")
    return revision


def serial_from_adb() -> str:
    explicit = os.environ.get("ANDROID_SERIAL", "").strip()
    if explicit:
        return explicit
    devices: list[str] = []
    for line in run("adb", "devices").stdout.splitlines()[1:]:
        columns = line.split()
        if len(columns) >= 2 and columns[1] == "device":
            devices.append(columns[0])
    if len(devices) != 1:
        raise SystemExit(f"expected exactly one ready Android target, found {devices}")
    return devices[0]


def validate_source_contract() -> dict:
    source = SOURCE.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    required = (
        "normalizeAppearancePreference",
        "resolveAppearance",
        "Configuration.UI_MODE_NIGHT_MASK",
        "Configuration.UI_MODE_NIGHT_YES",
        "normalizeClarity",
        "deriveWallpaperAtmosphere",
        "WALLPAPER_ALPHA = 0.08f",
        "WALLPAPER_MAX_ALPHA = 0.12f",
        "WALLPAPER_CHROMA_RETENTION = 0.24f",
        "WALLPAPER_MAX_CHROMA_RETENTION = 0.28f",
        "MIN_TOUCH_DP = 48",
        "TOUCH_ASSISTANCE_DP = 56",
        "no persistence, synchronization, wallpaper acquisition, telemetry, network",
    )
    for marker in required:
        if marker not in source:
            raise SystemExit(f"Android Personalization source contract missing: {marker}")
    for forbidden in (
        "SharedPreferences",
        "WallpaperManager",
        "BitmapFactory",
        "getPixels(",
        "HttpURLConnection",
        "URLConnection",
        "Socket(",
        "WebView",
        "android.permission.INTERNET",
    ):
        if forbidden in source or forbidden in manifest:
            raise SystemExit(f"Android Personalization source introduced prohibited authority/API: {forbidden}")
    if 'android:name=".PersonalizationActivity"' not in manifest:
        raise SystemExit("Android PersonalizationActivity is not registered")
    if "android.permission.INTERNET" in manifest:
        raise SystemExit("Android Candidate unexpectedly requests INTERNET permission")
    return {
        "systemAppearanceResolution": True,
        "clarityNormalization": True,
        "localRgbSummaryDerivation": True,
        "directWallpaperAcquisition": False,
        "persistenceOwnedByReference": False,
        "crossDeviceSyncOwnedByReference": False,
        "networkPermission": False,
        "wallpaperMaximumAlpha": 0.12,
        "wallpaperMaximumChromaRetention": 0.28,
    }


def density(serial: str) -> int:
    result = adb(serial, "shell", "wm", "density").stdout
    matches = re.findall(r"(?:Override|Physical) density:\s*(\d+)", result)
    if matches:
        return int(matches[-1])
    raw = adb(serial, "shell", "getprop", "ro.sf.lcd_density").stdout.strip()
    if raw.isdigit():
        return int(raw)
    raise SystemExit(f"could not resolve Android density: {result!r}")


def dump_ui(serial: str) -> ET.Element:
    path = "/sdcard/glaze-v12-personalization.xml"
    adb(serial, "shell", "uiautomator", "dump", path)
    raw = adb(serial, "exec-out", "cat", path).stdout
    return ET.fromstring(raw)


def contains(root: ET.Element, fragment: str) -> bool:
    for node in root.iter("node"):
        if fragment in node.attrib.get("text", "") or fragment in node.attrib.get("content-desc", ""):
            return True
    return False


def require_contains(root: ET.Element, fragment: str) -> None:
    if not contains(root, fragment):
        raise SystemExit(f"required Android Personalization UI fragment not found: {fragment}")


def find_desc(root: ET.Element, value: str) -> ET.Element | None:
    for node in root.iter("node"):
        if node.attrib.get("content-desc") == value:
            return node
    return None


def bounds(node: ET.Element) -> tuple[int, int, int, int]:
    match = BOUNDS.fullmatch(node.attrib.get("bounds", ""))
    if not match:
        raise SystemExit(f"invalid UI bounds: {node.attrib.get('bounds')!r}")
    return tuple(map(int, match.groups()))


def height_dp(node: ET.Element, dpi: int) -> float:
    _, y1, _, y2 = bounds(node)
    return (y2 - y1) * 160.0 / dpi


def launch(serial: str, *, appearance: str, clarity: str, touch: bool = False, wallpaper: tuple[int, int, int] | None = None) -> None:
    adb(serial, "shell", "am", "force-stop", PACKAGE)
    args = [
        "shell", "am", "start", "-W", "-n", ACTIVITY,
        "--es", "appearance", appearance,
        "--es", "clarity", clarity,
    ]
    if touch:
        args += ["--ez", "touchAssistance", "true"]
    if wallpaper is not None:
        r, g, b = wallpaper
        args += ["--ei", "wallpaperR", str(r), "--ei", "wallpaperG", str(g), "--ei", "wallpaperB", str(b)]
    result = adb(serial, *args).stdout
    if "Status: ok" not in result:
        raise SystemExit(f"Android Personalization activity launch failed:\n{result}")
    time.sleep(0.8)


def set_night_mode(serial: str, enabled: bool) -> None:
    adb(serial, "shell", "cmd", "uimode", "night", "yes" if enabled else "no")
    time.sleep(0.4)


def action_target(serial: str, dpi: int, floor: float) -> float:
    ui = dump_ui(serial)
    node = find_desc(ui, "Personalization action")
    if node is None:
        raise SystemExit("Personalization action is missing from Android UI hierarchy")
    measured = height_dp(node, dpi)
    if measured < floor - 1.0:
        raise SystemExit(f"Personalization action below {floor:.0f} dp floor: {measured:.2f} dp")
    return measured


def screenshot(serial: str, name: str) -> tuple[str, str]:
    path = OUT / name
    result = adb(serial, "exec-out", "screencap", "-p", text=False)
    path.write_bytes(result.stdout)
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"invalid screenshot PNG: {path}")
    return path.name, hashlib.sha256(payload).hexdigest()


def case_follow_system_light(serial: str, dpi: int) -> dict:
    set_night_mode(serial, False)
    launch(serial, appearance="follow-system", clarity="clear", wallpaper=(255, 0, 96))
    ui = dump_ui(serial)
    for fragment in (
        "Appearance preference: Follow System",
        "Resolved appearance: Light",
        "Clarity: Clear",
        "Target floor: 48 dp",
        "Wallpaper atmosphere: Local bounded RGB summary",
        "Wallpaper alpha: 0.08",
        "Wallpaper chroma retention: 0.24",
    ):
        require_contains(ui, fragment)
    target = action_target(serial, dpi, 48.0)
    name, digest = screenshot(serial, "android-v1.2-personalization-follow-system-light.png")
    return {"id": "follow-system-light-clear-wallpaper", "targetDp": round(target, 2), "screenshot": name, "sha256": digest}


def case_follow_system_dark_touch(serial: str, dpi: int) -> dict:
    set_night_mode(serial, True)
    launch(serial, appearance="follow-system", clarity="dense", touch=True, wallpaper=(10, 190, 245))
    ui = dump_ui(serial)
    for fragment in (
        "Appearance preference: Follow System",
        "Resolved appearance: Dark",
        "Clarity: Dense",
        "Target floor: 56 dp",
        "Wallpaper atmosphere: Local bounded RGB summary",
    ):
        require_contains(ui, fragment)
    target = action_target(serial, dpi, 56.0)
    name, digest = screenshot(serial, "android-v1.2-personalization-follow-system-dark-touch.png")
    return {"id": "follow-system-dark-dense-touch", "targetDp": round(target, 2), "screenshot": name, "sha256": digest}


def case_manual_deep_dark(serial: str, dpi: int) -> dict:
    set_night_mode(serial, False)
    launch(serial, appearance="deep-dark", clarity="balanced")
    ui = dump_ui(serial)
    for fragment in (
        "Appearance preference: Deep Dark",
        "Resolved appearance: Deep Dark",
        "Clarity: Balanced",
        "Wallpaper atmosphere: None",
    ):
        require_contains(ui, fragment)
    target = action_target(serial, dpi, 48.0)
    return {"id": "manual-deep-dark-independent-of-system", "targetDp": round(target, 2)}


def case_invalid_fallback(serial: str, dpi: int) -> dict:
    set_night_mode(serial, False)
    launch(serial, appearance="invalid-mode", clarity="neon", wallpaper=(300, -1, 2))
    ui = dump_ui(serial)
    for fragment in (
        "Appearance preference: Follow System",
        "Resolved appearance: Light",
        "Clarity: Balanced",
        "Wallpaper atmosphere: None",
    ):
        require_contains(ui, fragment)
    target = action_target(serial, dpi, 48.0)
    return {"id": "invalid-input-fail-closed", "targetDp": round(target, 2)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source_contract = validate_source_contract()
    revision = exact_revision()
    serial = serial_from_adb()
    dpi = density(serial)
    try:
        cases = [
            case_follow_system_light(serial, dpi),
            case_follow_system_dark_touch(serial, dpi),
            case_manual_deep_dark(serial, dpi),
            case_invalid_fallback(serial, dpi),
        ]
    finally:
        set_night_mode(serial, False)

    evidence = {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2 Personalization Android adapter reference",
        "lifecycle": "Candidate emulator evidence",
        "sourceRevision": revision,
        "platform": "Android handheld emulator",
        "package": PACKAGE,
        "sdk": adb(serial, "shell", "getprop", "ro.build.version.sdk").stdout.strip(),
        "buildFingerprint": adb(serial, "shell", "getprop", "ro.build.fingerprint").stdout.strip(),
        "densityDpi": dpi,
        "sourceContract": source_contract,
        "cases": cases,
        "boundaries": [
            "not physical-device qualification",
            "not OEM visual or compositor qualification",
            "not TalkBack acceptance",
            "not consumer persistence acceptance",
            "not wallpaper-source acquisition acceptance",
            "not cross-device synchronization",
            "not production acceptance",
            "not Release Candidate acceptance",
            "not V1.2 Stable promotion"
        ]
    }
    path = OUT / "android-personalization-evidence.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print("GLAZE UI V1.2 Android Personalization adapter emulator evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
