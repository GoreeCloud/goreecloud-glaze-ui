#!/usr/bin/env python3
"""Exact-head emulator evidence for the V1.2 Android consumer/platform adapter.

This validates Android system WallpaperColors summary execution and a bounded
reference-consumer persistence adapter. It does not grant Glaze core wallpaper or
storage authority and does not establish physical-device, production, RC, Stable,
or cross-platform acceptance.
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
JAVA_ROOT = ROOT / "reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12"
ADAPTER = JAVA_ROOT / "AndroidPersonalizationPlatformAdapter.java"
ACTIVITY_SOURCE = JAVA_ROOT / "PlatformAdapterActivity.java"
MANIFEST = ROOT / "reference/v1.2/native/android/app/src/main/AndroidManifest.xml"
PACKAGE = "com.goreecloud.glazeui.reference.v12"
ACTIVITY = f"{PACKAGE}/.PlatformAdapterActivity"
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
    devices = []
    for line in run("adb", "devices").stdout.splitlines()[1:]:
        columns = line.split()
        if len(columns) >= 2 and columns[1] == "device":
            devices.append(columns[0])
    if len(devices) != 1:
        raise SystemExit(f"expected exactly one ready Android target, found {devices}")
    return devices[0]


def validate_source_contract() -> dict[str, object]:
    adapter = ADAPTER.read_text(encoding="utf-8")
    activity = ACTIVITY_SOURCE.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    required_adapter = (
        "WallpaperManager.getInstance(appContext)",
        "getWallpaperColors(WallpaperManager.FLAG_SYSTEM)",
        "WallpaperColors",
        "SharedPreferences",
        "STORAGE_SCHEMA_VERSION = 1",
        "Context.MODE_PRIVATE",
        "clearCandidatePreferences",
        "reference consumer",
        "never reads raw wallpaper",
    )
    for marker in required_adapter:
        if marker not in adapter:
            raise SystemExit(f"Android platform adapter source contract missing: {marker}")
    for marker in (
        "new Thread",
        "runOnUiThread",
        "WallpaperColors adapter: Unavailable (fail-closed)",
        "Stored preferences: None",
        "No raw wallpaper pixels",
    ):
        if marker not in activity:
            raise SystemExit(f"Android platform adapter activity missing: {marker}")
    for forbidden in (
        "BitmapFactory",
        "getDrawable(",
        "getFastDrawable(",
        "getPixels(",
        "fromBitmap(",
        "fromDrawable(",
        "HttpURLConnection",
        "URLConnection",
        "Socket(",
        "WebView",
        "android.permission.INTERNET",
        "android.permission.SET_WALLPAPER",
    ):
        if forbidden in adapter or forbidden in activity or forbidden in manifest:
            raise SystemExit(f"Android platform adapter introduced prohibited API/authority: {forbidden}")
    if 'android:name=".PlatformAdapterActivity"' not in manifest:
        raise SystemExit("Android PlatformAdapterActivity registration missing")
    return {
        "systemWallpaperColorSummaryApi": "WallpaperManager.getWallpaperColors(FLAG_SYSTEM)",
        "rawWallpaperPixelsRead": False,
        "wallpaperContentTransmitted": False,
        "networkPermission": False,
        "referenceConsumerPersistence": "SharedPreferences MODE_PRIVATE",
        "storageSchemaVersion": 1,
        "glazeCorePersistenceOwnership": False,
        "glazeCoreWallpaperAcquisitionOwnership": False,
    }


def dump_ui(serial: str) -> ET.Element:
    path = "/sdcard/glaze-v12-platform-adapter.xml"
    adb(serial, "shell", "uiautomator", "dump", path)
    raw = adb(serial, "exec-out", "cat", path).stdout
    return ET.fromstring(raw)


def ui_text(root: ET.Element) -> str:
    values: list[str] = []
    for node in root.iter("node"):
        for key in ("text", "content-desc"):
            value = node.attrib.get(key, "")
            if value:
                values.append(value)
    return "\n".join(values)


def wait_for(serial: str, alternatives: tuple[str, ...], timeout: float = 12.0) -> tuple[ET.Element, str]:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        root = dump_ui(serial)
        last = ui_text(root)
        for candidate in alternatives:
            if candidate in last:
                return root, candidate
        time.sleep(0.25)
    raise SystemExit(f"Android platform adapter UI did not reach {alternatives}; last UI={last!r}")


def launch(serial: str, mode: str, *, appearance: str | None = None, clarity: str | None = None) -> None:
    adb(serial, "shell", "am", "force-stop", PACKAGE)
    args = ["shell", "am", "start", "-W", "-n", ACTIVITY, "--es", "mode", mode]
    if appearance is not None:
        args += ["--es", "appearance", appearance]
    if clarity is not None:
        args += ["--es", "clarity", clarity]
    result = adb(serial, *args).stdout
    if "Status: ok" not in result:
        raise SystemExit(f"Android platform adapter activity launch failed:\n{result}")
    time.sleep(0.3)


def screenshot(serial: str, name: str) -> dict[str, str]:
    path = OUT / name
    result = adb(serial, "exec-out", "screencap", "-p", text=False)
    path.write_bytes(result.stdout)
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"invalid screenshot PNG: {path}")
    return {"file": path.name, "sha256": hashlib.sha256(payload).hexdigest()}


def wallpaper_summary_case(serial: str) -> dict[str, object]:
    launch(serial, "wallpaper")
    _, observed = wait_for(
        serial,
        (
            "WallpaperColors adapter: Available",
            "WallpaperColors adapter: Unavailable (fail-closed)",
        ),
    )
    shot = screenshot(serial, "android-v1.2-platform-wallpaper-colors.png")
    return {
        "id": "android-system-wallpaper-colors-summary",
        "apiExecuted": True,
        "summaryAvailableOnThisEmulator": observed.endswith("Available"),
        "nullSummaryFailsClosed": observed.endswith("Unavailable (fail-closed)"),
        "screenshot": shot,
    }


def persistence_roundtrip_case(serial: str) -> dict[str, object]:
    launch(serial, "clear")
    wait_for(serial, ("Storage cleared",))

    launch(serial, "persist", appearance="dark", clarity="dense")
    wait_for(serial, ("Stored appearance: Dark",))
    persisted = ui_text(dump_ui(serial))
    for marker in ("Stored appearance: Dark", "Stored clarity: Dense", "Storage schema: 1"):
        if marker not in persisted:
            raise SystemExit(f"persistence write evidence missing: {marker}")

    launch(serial, "load")
    wait_for(serial, ("Stored appearance: Dark",))
    loaded = ui_text(dump_ui(serial))
    for marker in ("Stored appearance: Dark", "Stored clarity: Dense", "Storage schema: 1"):
        if marker not in loaded:
            raise SystemExit(f"persistence restart round-trip evidence missing: {marker}")
    shot = screenshot(serial, "android-v1.2-platform-persistence-roundtrip.png")

    launch(serial, "clear")
    wait_for(serial, ("Storage cleared",))
    launch(serial, "load")
    wait_for(serial, ("Stored preferences: None",))
    return {
        "id": "android-reference-consumer-persistence-roundtrip",
        "writeReadAcrossForceStop": True,
        "schemaVersion": 1,
        "clearFailsClosedToNoStoredPreferences": True,
        "screenshot": shot,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source_contract = validate_source_contract()
    revision = exact_revision()
    serial = serial_from_adb()
    cases = [wallpaper_summary_case(serial), persistence_roundtrip_case(serial)]
    evidence = {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2 Android consumer/platform adapter reference",
        "lifecycle": "Candidate emulator evidence",
        "sourceRevision": revision,
        "platform": "Android handheld emulator",
        "package": PACKAGE,
        "sdk": adb(serial, "shell", "getprop", "ro.build.version.sdk").stdout.strip(),
        "buildFingerprint": adb(serial, "shell", "getprop", "ro.build.fingerprint").stdout.strip(),
        "sourceContract": source_contract,
        "cases": cases,
        "boundedAndroidPlatformAdapterExecutionEstablished": True,
        "rawWallpaperAcquisitionEstablished": False,
        "glazeCorePersistenceOwnershipEstablished": False,
        "crossDeviceSyncEstablished": False,
        "physicalDeviceAcceptanceEstablished": False,
        "productionAcceptanceEstablished": False,
        "releaseCandidateAcceptanceEstablished": False,
        "stableAcceptanceEstablished": False,
        "boundaries": [
            "Android emulator platform-adapter execution only",
            "WallpaperColors null is a valid Android platform result and fails closed",
            "no raw wallpaper pixel acquisition",
            "reference-consumer persistence is not Glaze-core persistence authority",
            "not cross-platform native parity",
            "not physical-device qualification",
            "not production acceptance",
            "not Release Candidate acceptance",
            "not V1.2 Stable promotion",
        ],
    }
    path = OUT / "android-platform-adapter-evidence.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print("GLAZE UI V1.2 Android consumer/platform adapter emulator evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
