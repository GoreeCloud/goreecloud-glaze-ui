#!/usr/bin/env python3
"""Exact-head emulator evidence for V1.2 Android window/foldable adaptation.

The gate proves compact/wide Android window-size adaptation and an optional
producer-supplied hinge exclusion. It intentionally does not claim physical hinge
sensing, OEM posture parity, physical-device qualification, RC, or Stable.
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
SOURCE = ROOT / "reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/FoldableAdaptationActivity.java"
MANIFEST = ROOT / "reference/v1.2/native/android/app/src/main/AndroidManifest.xml"
PACKAGE = "com.goreecloud.glazeui.reference.v12"
ACTIVITY = f"{PACKAGE}/.FoldableAdaptationActivity"
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
    source = SOURCE.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    for marker in (
        "WIDE_THRESHOLD_DP = 780",
        "configuration.screenWidthDp",
        'getIntExtra("hingeWidthDp", 0)',
        "producer-provided",
        "Single-panel complete environment",
        "Wide space adds detail rather than only scaling",
        "No hinge sensor",
    ):
        if marker not in source:
            raise SystemExit(f"Android foldable source contract missing: {marker}")
    for forbidden in (
        "androidx.window",
        "FoldingFeature",
        "WindowInfoTracker",
        "SensorManager",
        "TYPE_HINGE_ANGLE",
    ):
        if forbidden in source:
            raise SystemExit(f"bounded foldable reference introduced unverified platform authority: {forbidden}")
    if 'android:name=".FoldableAdaptationActivity"' not in manifest:
        raise SystemExit("FoldableAdaptationActivity registration missing")
    return {
        "wideThresholdDp": 780,
        "windowWidthSource": "Android Configuration.screenWidthDp",
        "hingeExclusionSource": "optional producer-supplied intent extra",
        "hingeSensorRead": False,
        "oemPostureApiUsed": False,
    }


def dump_ui(serial: str) -> ET.Element:
    path = "/sdcard/glaze-v12-foldable.xml"
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


def wait_for(serial: str, marker: str, timeout: float = 12.0) -> ET.Element:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        root = dump_ui(serial)
        last = ui_text(root)
        if marker in last:
            return root
        time.sleep(0.25)
    raise SystemExit(f"Android foldable UI did not reach {marker!r}; last UI={last!r}")


def launch(serial: str, *, hinge_width_dp: int = 0) -> None:
    adb(serial, "shell", "am", "force-stop", PACKAGE)
    args = ["shell", "am", "start", "-W", "-n", ACTIVITY]
    if hinge_width_dp:
        args += ["--ei", "hingeWidthDp", str(hinge_width_dp)]
    result = adb(serial, *args).stdout
    if "Status: ok" not in result:
        raise SystemExit(f"FoldableAdaptationActivity launch failed:\n{result}")
    time.sleep(0.4)


def screenshot(serial: str, name: str) -> dict[str, str]:
    path = OUT / name
    result = adb(serial, "exec-out", "screencap", "-p", text=False)
    path.write_bytes(result.stdout)
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"invalid screenshot PNG: {path}")
    return {"file": path.name, "sha256": hashlib.sha256(payload).hexdigest()}


def set_size(serial: str, size: str) -> None:
    adb(serial, "shell", "wm", "size", size)
    time.sleep(0.5)


def compact_case(serial: str) -> dict[str, object]:
    set_size(serial, "1080x2400")
    launch(serial)
    root = wait_for(serial, "Foldable adaptation: compact")
    text = ui_text(root)
    for marker in ("Panels: 1", "Hinge exclusion: none", "Single-panel complete environment"):
        if marker not in text:
            raise SystemExit(f"compact adaptation evidence missing: {marker}")
    return {
        "id": "android-compact-window",
        "overridePx": [1080, 2400],
        "singlePanel": True,
        "screenshot": screenshot(serial, "android-v1.2-foldable-compact.png"),
    }


def wide_case(serial: str) -> dict[str, object]:
    set_size(serial, "2208x1840")
    launch(serial, hinge_width_dp=16)
    root = wait_for(serial, "Foldable adaptation: wide")
    text = ui_text(root)
    for marker in (
        "Panels: 2",
        "Hinge exclusion: 16 dp (producer-provided)",
        "Wide space adds detail rather than only scaling",
    ):
        if marker not in text:
            raise SystemExit(f"wide adaptation evidence missing: {marker}")
    return {
        "id": "android-wide-window-with-producer-hinge-exclusion",
        "overridePx": [2208, 1840],
        "twoPanels": True,
        "producerHingeExclusionDp": 16,
        "screenshot": screenshot(serial, "android-v1.2-foldable-wide.png"),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source_contract = validate_source_contract()
    revision = exact_revision()
    serial = serial_from_adb()
    try:
        cases = [compact_case(serial), wide_case(serial)]
    finally:
        adb(serial, "shell", "wm", "size", "reset", check=False)
        adb(serial, "shell", "am", "force-stop", PACKAGE, check=False)
    evidence = {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2 Android window/foldable adaptation reference",
        "lifecycle": "Candidate emulator evidence",
        "sourceRevision": revision,
        "platform": "Android handheld emulator with deterministic window-size overrides",
        "sdk": adb(serial, "shell", "getprop", "ro.build.version.sdk").stdout.strip(),
        "buildFingerprint": adb(serial, "shell", "getprop", "ro.build.fingerprint").stdout.strip(),
        "sourceContract": source_contract,
        "cases": cases,
        "androidWindowSizeAdaptationEstablished": True,
        "producerHingeExclusionRenderingEstablished": True,
        "realHingeSensorAcceptanceEstablished": False,
        "oemPostureAcceptanceEstablished": False,
        "physicalFoldableAcceptanceEstablished": False,
        "nativePlatformParityEstablished": False,
        "productionAcceptanceEstablished": False,
        "releaseCandidateAcceptanceEstablished": False,
        "stableAcceptanceEstablished": False,
        "boundaries": [
            "Android emulator window-size adaptation only",
            "hinge exclusion is producer-supplied, not sensor-derived",
            "not OEM posture semantics",
            "not physical foldable qualification",
            "not cross-platform native parity",
            "not production acceptance",
            "not Release Candidate acceptance",
            "not V1.2 Stable promotion",
        ],
    }
    path = OUT / "android-foldable-adaptation-evidence.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print("GLAZE UI V1.2 Android window/foldable emulator evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
