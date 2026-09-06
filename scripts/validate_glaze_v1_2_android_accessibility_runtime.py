#!/usr/bin/env python3
"""Exact-head Android machine-accessibility evidence for GLAZE UI V1.2 Candidate.

This gate inspects only machine-observable Android view hierarchy semantics,
target geometry, 200% text-scale reachability, and Reduced Transparency state.
It does not establish TalkBack, Switch Access, Voice Access, human review,
physical-device, OEM interoperability, downstream conformance, RC, or Stable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".artifacts" / "glaze-v1.2-android-native"
SOURCE = ROOT / "reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/MainActivity.java"
MANIFEST = ROOT / "reference/v1.2/native/android/app/src/main/AndroidManifest.xml"
PACKAGE = "com.goreecloud.glazeui.reference.v12"
ACTIVITY = f"{PACKAGE}/.MainActivity"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
SIZE = re.compile(r"(?:Override|Physical) size:\s*(\d+)x(\d+)")

EXPECTED_CONTROLS = {
    "Wi-Fi": "Wi-Fi:",
    "Bluetooth": "Bluetooth:",
    "Night Light": "Night Light:",
    "Performance": "Performance:",
    "Airplane Mode": "Airplane Mode:",
    "Focus": "Focus:",
    "Primary action": "Primary action",
    "Secondary action": "Secondary action",
}
QUICK_SETTINGS = {
    "Wi-Fi",
    "Bluetooth",
    "Night Light",
    "Performance",
    "Airplane Mode",
    "Focus",
}


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


def density(serial: str) -> int:
    output = adb(serial, "shell", "wm", "density").stdout
    matches = re.findall(r"(?:Override|Physical) density:\s*(\d+)", output)
    if matches:
        return int(matches[-1])
    fallback = adb(serial, "shell", "getprop", "ro.sf.lcd_density").stdout.strip()
    if fallback.isdigit():
        return int(fallback)
    raise SystemExit(f"could not resolve Android density from {output!r}")


def display_size(serial: str) -> tuple[int, int]:
    output = adb(serial, "shell", "wm", "size").stdout
    matches = SIZE.findall(output)
    if not matches:
        raise SystemExit(f"could not resolve Android display size from {output!r}")
    width, height = matches[-1]
    return int(width), int(height)


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    for char in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2212"):
        normalized = normalized.replace(char, "-")
    return " ".join(normalized.split())


def source_contract() -> dict[str, object]:
    source = SOURCE.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    required = (
        "MIN_TOUCH_DP = 48",
        "TOUCH_ASSISTANCE_DP = 56",
        'primary.setContentDescription("Primary action")',
        'secondaryAction.setContentDescription("Secondary action")',
        "button.setContentDescription(name + \": \" + state",
        "Reduced Transparency: enabled",
        "not OEM-wide blur fidelity",
        "physical-device",
        "TalkBack",
    )
    for marker in required:
        if marker not in source:
            raise SystemExit(f"Android accessibility source contract missing: {marker}")

    forbidden = (
        "AccessibilityService",
        "BIND_ACCESSIBILITY_SERVICE",
        "enabled_accessibility_services",
    )
    joined = source + "\n" + manifest
    for marker in forbidden:
        if marker in joined:
            raise SystemExit(
                f"bounded accessibility evidence must not own or enable an accessibility service: {marker}"
            )

    return {
        "minimumTouchTargetDp": 48,
        "touchAssistanceTargetDp": 56,
        "accessibilityServiceOwned": False,
        "assistiveTechnologyCertificationClaimed": False,
    }


def dump_ui(serial: str) -> ET.Element:
    remote = "/sdcard/glaze-v12-accessibility.xml"
    adb(serial, "shell", "uiautomator", "dump", remote)
    raw = adb(serial, "exec-out", "cat", remote).stdout
    diagnostic = OUT / "android-accessibility-last-hierarchy.xml"
    diagnostic.write_text(raw, encoding="utf-8")
    return ET.fromstring(raw)


def node_name(node: ET.Element) -> tuple[str, str]:
    content_description = node.attrib.get("content-desc", "").strip()
    text = node.attrib.get("text", "").strip()
    return normalize_name(content_description or text), content_description


def bounds(node: ET.Element) -> tuple[int, int, int, int]:
    match = BOUNDS.fullmatch(node.attrib.get("bounds", ""))
    if not match:
        raise SystemExit(f"invalid UI bounds: {node.attrib.get('bounds')!r}")
    return tuple(map(int, match.groups()))


def height_dp(node: ET.Element, dpi: int) -> float:
    _, y1, _, y2 = bounds(node)
    return (y2 - y1) * 160.0 / dpi


def app_nodes(root: ET.Element):
    for node in root.iter("node"):
        if node.attrib.get("package") == PACKAGE:
            yield node


def node_is_visible(node: ET.Element, display: tuple[int, int]) -> bool:
    """Treat missing UIAutomator visibility metadata as unknown, not invisible."""
    visibility = node.attrib.get("visible-to-user")
    if visibility == "false":
        return False
    try:
        x1, y1, x2, y2 = bounds(node)
    except SystemExit:
        return False
    if x2 <= x1 or y2 <= y1:
        return False
    width, height = display
    return x2 > 0 and y2 > 0 and x1 < width and y1 < height


def reset_scroll(serial: str) -> None:
    width, height = display_size(serial)
    x = width // 2
    start_y = max(1, round(height * 0.30))
    end_y = max(start_y + 1, round(height * 0.78))
    for _ in range(8):
        adb(serial, "shell", "input", "swipe", str(x), str(start_y), str(x), str(end_y), "160")
        time.sleep(0.08)


def advance_scroll(serial: str) -> None:
    width, height = display_size(serial)
    x = width // 2
    start_y = max(1, round(height * 0.76))
    end_y = max(1, round(height * 0.48))
    adb(serial, "shell", "input", "swipe", str(x), str(start_y), str(x), str(end_y), "190")
    time.sleep(0.12)


def launch(serial: str, *, appearance: str = "light", reduced: bool = False, touch: bool = False) -> None:
    adb(serial, "shell", "wm", "size", "reset", check=False)
    adb(serial, "shell", "am", "force-stop", PACKAGE)
    args = ["shell", "am", "start", "-W", "-n", ACTIVITY, "--es", "appearance", appearance]
    if reduced:
        args += ["--ez", "reducedTransparency", "true"]
    if touch:
        args += ["--ez", "touchAssistance", "true"]
    result = adb(serial, *args).stdout
    if "Status: ok" not in result:
        raise SystemExit(f"Android accessibility evidence activity launch failed:\n{result}")
    time.sleep(0.5)
    reset_scroll(serial)


def scan_hierarchy(serial: str, dpi: int, *, swipes: int = 14) -> dict[str, object]:
    controls: dict[str, dict[str, object]] = {}
    unnamed_clickables: list[dict[str, str]] = []
    display = display_size(serial)
    app_instances = 0
    clickable_instances = 0
    visible_clickable_instances = 0
    missing_visibility_metadata = 0

    for index in range(swipes + 1):
        root = dump_ui(serial)
        for node in app_nodes(root):
            app_instances += 1
            if node.attrib.get("clickable") != "true":
                continue
            clickable_instances += 1
            if "visible-to-user" not in node.attrib:
                missing_visibility_metadata += 1
            if not node_is_visible(node, display):
                continue
            visible_clickable_instances += 1
            name, content_description = node_name(node)
            if not name:
                unnamed_clickables.append(
                    {
                        "class": node.attrib.get("class", ""),
                        "bounds": node.attrib.get("bounds", ""),
                        "visibilityMetadata": node.attrib.get("visible-to-user", "absent"),
                    }
                )
                continue
            role = node.attrib.get("class", "")
            measured = height_dp(node, dpi)
            prior = controls.get(name)
            if prior is None or measured > float(prior["maxHeightDp"]):
                controls[name] = {
                    "role": role,
                    "maxHeightDp": round(measured, 2),
                    "enabled": node.attrib.get("enabled") == "true",
                    "focusable": node.attrib.get("focusable") == "true",
                    "contentDescriptionPresent": bool(content_description),
                    "visibilityMetadata": node.attrib.get("visible-to-user", "absent"),
                }
        if index < swipes:
            advance_scroll(serial)

    if unnamed_clickables:
        raise SystemExit(f"visible app clickables without accessible names: {unnamed_clickables}")

    return {
        "appNodeInstances": app_instances,
        "clickableAppNodeInstances": clickable_instances,
        "visibleClickableInstances": visible_clickable_instances,
        "clickablesMissingVisibilityMetadata": missing_visibility_metadata,
        "namedControls": controls,
    }


def resolve_expected(
    controls: dict[str, dict[str, object]], *, floor_dp: float
) -> dict[str, dict[str, object]]:
    resolved: dict[str, dict[str, object]] = {}
    for control_id, prefix in EXPECTED_CONTROLS.items():
        matches = [(name, info) for name, info in controls.items() if name.startswith(prefix)]
        if not matches:
            raise SystemExit(
                f"expected named Android control not observed: {control_id} ({prefix}); "
                f"observed={sorted(controls)}"
            )
        name, info = max(matches, key=lambda item: float(item[1]["maxHeightDp"]))
        if info["role"] != "android.widget.Button":
            raise SystemExit(f"{control_id} exposed unexpected native role {info['role']!r}")
        if control_id in QUICK_SETTINGS and not info["contentDescriptionPresent"]:
            raise SystemExit(f"{control_id} did not expose its state-bearing content description")
        measured = float(info["maxHeightDp"])
        if measured < floor_dp - 1.0:
            raise SystemExit(f"{control_id} below {floor_dp:.0f} dp target floor: {measured:.2f} dp")
        if not info["enabled"]:
            raise SystemExit(f"{control_id} unexpectedly disabled")
        resolved[control_id] = {"accessibleName": name, **info}
    return resolved


def contains(serial: str, fragment: str, *, swipes: int = 14) -> bool:
    expected = normalize_name(fragment)
    reset_scroll(serial)
    for index in range(swipes + 1):
        root = dump_ui(serial)
        for node in app_nodes(root):
            text = normalize_name(node.attrib.get("text", ""))
            content_description = normalize_name(node.attrib.get("content-desc", ""))
            if expected in text or expected in content_description:
                return True
        if index < swipes:
            advance_scroll(serial)
    return False


def font_scale(serial: str) -> str:
    value = adb(serial, "shell", "settings", "get", "system", "font_scale").stdout.strip()
    return value if value and value != "null" else "1.0"


def default_target_audit(serial: str, dpi: int) -> dict[str, object]:
    launch(serial, appearance="light")
    hierarchy = scan_hierarchy(serial, dpi)
    controls = resolve_expected(hierarchy["namedControls"], floor_dp=48.0)
    return {"targetFloorDp": 48, "hierarchy": hierarchy, "controls": controls}


def touch_assistance_audit(serial: str, dpi: int) -> dict[str, object]:
    launch(serial, appearance="deep-dark", touch=True)
    if not contains(serial, "Touch Assistance: 56 dp minimum target"):
        raise SystemExit("Touch Assistance semantic state not reachable")
    hierarchy = scan_hierarchy(serial, dpi)
    controls = resolve_expected(hierarchy["namedControls"], floor_dp=56.0)
    return {
        "targetFloorDp": 56,
        "semanticState": "Touch Assistance: 56 dp minimum target",
        "hierarchy": hierarchy,
        "controls": controls,
    }


def large_text_audit(serial: str, dpi: int) -> dict[str, object]:
    adb(serial, "shell", "settings", "put", "system", "font_scale", "2.0")
    launch(serial, appearance="deep-dark", touch=True)
    required = (
        "Appearance: Deep Dark",
        "Target floor: 56 dp",
        "Critical System high opacity non backdrop dependent surface",
        "Primary action",
        "Secondary action",
    )
    for marker in required:
        if not contains(serial, marker):
            raise SystemExit(f"200% text-scale content not reachable: {marker}")
    hierarchy = scan_hierarchy(serial, dpi)
    controls = resolve_expected(hierarchy["namedControls"], floor_dp=56.0)
    return {
        "fontScale": 2.0,
        "requiredContentReachable": list(required),
        "controls": controls,
    }


def reduced_transparency_audit(serial: str) -> dict[str, object]:
    launch(serial, appearance="dark", reduced=True)
    required = (
        "Appearance: Dark",
        "Material: Neutral opaque fallback",
        "Reduced Transparency: enabled",
    )
    for marker in required:
        if not contains(serial, marker):
            raise SystemExit(f"Reduced Transparency semantic state not reachable: {marker}")
    return {
        "appearance": "Dark",
        "material": "Neutral opaque fallback",
        "reducedTransparency": True,
        "semanticStateReachable": True,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    revision = exact_revision()
    source = source_contract()
    serial = serial_from_adb()
    dpi = density(serial)
    original_scale = font_scale(serial)

    try:
        default = default_target_audit(serial, dpi)
        touch = touch_assistance_audit(serial, dpi)
        large_text = large_text_audit(serial, dpi)
        reduced = reduced_transparency_audit(serial)
    finally:
        adb(serial, "shell", "wm", "size", "reset", check=False)
        adb(serial, "shell", "settings", "put", "system", "font_scale", original_scale, check=False)
        adb(serial, "shell", "am", "force-stop", PACKAGE, check=False)

    evidence = {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2",
        "lifecycle": "Candidate machine accessibility evidence",
        "sourceRevision": revision,
        "platform": "Android handheld emulator",
        "package": PACKAGE,
        "sdk": adb(serial, "shell", "getprop", "ro.build.version.sdk").stdout.strip(),
        "densityDpi": dpi,
        "sourceContract": source,
        "audits": {
            "defaultTargetsAndHierarchy": default,
            "touchAssistanceTargetsAndHierarchy": touch,
            "largeText200PercentReachability": large_text,
            "reducedTransparencySemantics": reduced,
        },
        "established": [
            "machine-observable Android accessibility names for expected interactive controls",
            "machine-observable native Button roles for expected interactive controls",
            "48 dp default target floor for expected interactive controls",
            "56 dp Touch Assistance target floor for expected interactive controls",
            "200% text-scale task and control reachability in the bounded emulator scene",
            "Reduced Transparency semantic-state reachability in the bounded emulator scene",
        ],
        "notEstablished": [
            "TalkBack acceptance or certification",
            "Switch Access acceptance",
            "Voice Access acceptance",
            "human accessibility review",
            "physical-device accessibility qualification",
            "OEM accessibility-service interoperability",
            "downstream consumer conformance",
            "Release Candidate designation",
            "Stable promotion",
        ],
    }

    path = OUT / "android-accessibility-evidence.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, ensure_ascii=False))
    print("GLAZE UI V1.2 Android machine accessibility evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
