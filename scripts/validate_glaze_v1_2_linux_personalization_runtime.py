#!/usr/bin/env python3
"""Headless GTK4 evidence for the GLAZE UI V1.2 Linux Personalization adapter.

The gate proves bounded local system-appearance resolution, Clarity normalization,
RGB-summary wallpaper atmosphere, Reduced Transparency, target geometry, and exact
revision evidence. It is not compositor, physical-display, assistive-technology,
persistence, synchronization, production, RC, or Stable acceptance.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "reference/v1.2/native/linux-gtk/personalization.py"
OUT = ROOT / ".artifacts/glaze-v1.2-linux-native"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def run(*args: str, check: bool = True, text: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, text=text, capture_output=True, env=env)


def exact_revision() -> str:
    revision = run("git", "-C", str(ROOT), "rev-parse", "HEAD").stdout.strip()
    if not SHA40.fullmatch(revision):
        raise SystemExit(f"could not resolve exact source revision: {revision!r}")
    expected = os.environ.get("GLAZE_SOURCE_REVISION", "").strip()
    if expected and expected != revision:
        raise SystemExit(f"exact source mismatch: checkout={revision}, expected={expected}")
    return revision


def validate_source_contract() -> dict:
    source = APP.read_text(encoding="utf-8")
    required = (
        "org.gnome.desktop.interface",
        "color-scheme",
        "Gtk.Settings/gtk-application-prefer-dark-theme",
        "normalize_appearance",
        "normalize_clarity",
        "derive_wallpaper_atmosphere",
        "WALLPAPER_ALPHA = 0.08",
        "WALLPAPER_MAX_ALPHA = 0.12",
        "WALLPAPER_CHROMA_RETENTION = 0.24",
        "WALLPAPER_MAX_CHROMA_RETENTION = 0.28",
        "MIN_TARGET_PX = 48",
        "TOUCH_ASSISTANCE_PX = 56",
        "self.atmosphere = None if self.args.reduced_transparency else derived",
        "neutral_surface_channel",
        "composite_atmosphere",
        "owns no persistence",
    )
    for marker in required:
        if marker not in source:
            raise SystemExit(f"Linux Personalization source contract missing: {marker}")
    for forbidden in (
        "requests.",
        "urllib.",
        "socket.",
        "http.client",
        "WebKit",
        "GdkPixbuf",
        "PIL",
        "Image.open",
        "open(\"/usr/share/backgrounds",
        "dconf write",
        "settings.set_",
    ):
        if forbidden in source:
            raise SystemExit(f"Linux Personalization adapter introduced prohibited authority/API: {forbidden}")
    return {
        "systemAppearanceResolution": True,
        "gtkFallbackResolution": True,
        "clarityNormalization": True,
        "localRgbSummaryDerivation": True,
        "neutralMaterialRetainedUnderAtmosphere": True,
        "reducedTransparencySuppressesAtmosphere": True,
        "wallpaperMaximumAlpha": 0.12,
        "wallpaperMaximumChromaRetention": 0.28,
        "directWallpaperAcquisition": False,
        "persistenceOwnedByReference": False,
        "crossDeviceSyncOwnedByReference": False,
        "networkTransport": False,
    }


def gsettings_available() -> None:
    result = run("gsettings", "list-keys", "org.gnome.desktop.interface", check=False)
    if result.returncode != 0 or "color-scheme" not in result.stdout.split():
        raise SystemExit("org.gnome.desktop.interface color-scheme is unavailable for native Follow System evidence")


def get_color_scheme(env: dict[str, str]) -> str:
    result = run("gsettings", "get", "org.gnome.desktop.interface", "color-scheme", env=env)
    return result.stdout.strip()


def set_color_scheme(value: str, env: dict[str, str]) -> None:
    run("gsettings", "set", "org.gnome.desktop.interface", "color-scheme", value, env=env)
    observed = get_color_scheme(env)
    if value not in observed:
        raise SystemExit(f"could not set GNOME color-scheme to {value}: {observed}")


def wait_for_file(path: Path, process: subprocess.Popen, timeout: float = 15.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size > 0:
            return json.loads(path.read_text(encoding="utf-8"))
        code = process.poll()
        if code is not None:
            stdout, stderr = process.communicate(timeout=2)
            raise SystemExit(f"Linux Personalization adapter exited before evidence was ready ({code})\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        time.sleep(0.1)
    process.terminate()
    stdout, stderr = process.communicate(timeout=4)
    raise SystemExit(f"timed out waiting for Linux Personalization evidence\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")


def screenshot(path: Path, env: dict[str, str]) -> str:
    result = run("import", "-window", "root", str(path), check=False, env=env)
    if result.returncode != 0:
        raise SystemExit(f"ImageMagick root screenshot failed:\n{result.stderr}")
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"invalid Linux Personalization screenshot PNG: {path}")
    return hashlib.sha256(payload).hexdigest()


def run_case(case_id: str, args: list[str], *, floor: int, expected: dict[str, object], env: dict[str, str], screenshot_required: bool = False) -> dict:
    case_dir = OUT / f"personalization-{case_id}"
    case_dir.mkdir(parents=True, exist_ok=True)
    runtime = case_dir / "runtime.json"
    if runtime.exists():
        runtime.unlink()
    command = [sys.executable, str(APP), *args, "--evidence-file", str(runtime), "--auto-interact"]
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        evidence = wait_for_file(runtime, process)
        if evidence.get("lifecycle") != "Candidate native evidence" or evidence.get("ready") is not True:
            raise SystemExit(f"{case_id} lifecycle/readiness drifted: {evidence}")
        if evidence.get("interactionState") != "Action: Complete":
            raise SystemExit(f"{case_id} interaction did not complete")
        if int(evidence.get("targetHeightPx", 0)) < floor:
            raise SystemExit(f"{case_id} target below {floor}px: {evidence.get('targetHeightPx')}")
        neutral = evidence.get("neutralSurfaceRgb")
        if not isinstance(neutral, list) or len(neutral) != 3 or len(set(neutral)) != 1:
            raise SystemExit(f"{case_id} neutral material authority drifted: {neutral}")
        for key, value in expected.items():
            if evidence.get(key) != value:
                raise SystemExit(f"{case_id} expected {key}={value!r}, got {evidence.get(key)!r}")
        atmosphere = evidence.get("wallpaperAtmosphere")
        if atmosphere is not None:
            if float(atmosphere.get("alpha", 99)) > 0.12 or float(atmosphere.get("chromaRetention", 99)) > 0.28:
                raise SystemExit(f"{case_id} wallpaper atmosphere exceeded bounds: {atmosphere}")
        shot_name = None
        digest = None
        if screenshot_required:
            shot = OUT / f"linux-v1.2-personalization-{case_id}.png"
            digest = screenshot(shot, env)
            shot_name = shot.name
        return {
            "id": case_id,
            "appearancePreference": evidence["appearancePreference"],
            "resolvedAppearance": evidence["resolvedAppearance"],
            "systemAppearanceSource": evidence["systemAppearanceSource"],
            "clarity": evidence["clarity"],
            "reducedTransparency": evidence["reducedTransparency"],
            "touchAssistance": evidence["touchAssistance"],
            "wallpaperAtmosphere": atmosphere,
            "neutralSurfaceRgb": neutral,
            "compositedSurfaceRgb": evidence["compositedSurfaceRgb"],
            "targetHeightPx": evidence["targetHeightPx"],
            "gtkVersion": evidence["gtkVersion"],
            "screenshot": shot_name,
            "sha256": digest,
        }
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source_contract = validate_source_contract()
    revision = exact_revision()
    env = os.environ.copy()
    env.setdefault("GDK_BACKEND", "x11")
    if not env.get("DISPLAY"):
        raise SystemExit("DISPLAY is required; run under xvfb-run or an X11 session")
    gsettings_available()
    original = get_color_scheme(env)
    try:
        set_color_scheme("default", env)
        light = run_case(
            "follow-system-light-clear",
            ["--appearance", "follow-system", "--clarity", "clear", "--wallpaper-r", "255", "--wallpaper-g", "0", "--wallpaper-b", "96"],
            floor=48,
            expected={
                "appearancePreference": "follow-system",
                "resolvedAppearance": "light",
                "clarity": "clear",
                "reducedTransparency": False,
                "touchAssistance": False,
            },
            env=env,
            screenshot_required=True,
        )
        if light["wallpaperAtmosphere"] is None:
            raise SystemExit("Follow System Light did not retain valid bounded wallpaper atmosphere")

        set_color_scheme("prefer-dark", env)
        dark = run_case(
            "follow-system-dark-dense-touch",
            ["--appearance", "follow-system", "--clarity", "dense", "--touch-assistance", "--wallpaper-r", "10", "--wallpaper-g", "190", "--wallpaper-b", "245"],
            floor=56,
            expected={
                "appearancePreference": "follow-system",
                "resolvedAppearance": "dark",
                "clarity": "dense",
                "reducedTransparency": False,
                "touchAssistance": True,
            },
            env=env,
            screenshot_required=True,
        )
        if dark["wallpaperAtmosphere"] is None:
            raise SystemExit("Follow System Dark did not retain valid bounded wallpaper atmosphere")

        set_color_scheme("default", env)
        deep_dark = run_case(
            "manual-deep-dark",
            ["--appearance", "deep-dark", "--clarity", "balanced"],
            floor=48,
            expected={
                "appearancePreference": "deep-dark",
                "resolvedAppearance": "deep-dark",
                "systemAppearanceSource": "manual",
                "clarity": "balanced",
                "reducedTransparency": False,
            },
            env=env,
        )

        set_color_scheme("prefer-dark", env)
        reduced = run_case(
            "reduced-transparency",
            ["--appearance", "follow-system", "--clarity", "clear", "--reduced-transparency", "--wallpaper-r", "255", "--wallpaper-g", "40", "--wallpaper-b", "80"],
            floor=48,
            expected={
                "appearancePreference": "follow-system",
                "resolvedAppearance": "dark",
                "clarity": "clear",
                "reducedTransparency": True,
                "wallpaperAtmosphere": None,
            },
            env=env,
            screenshot_required=True,
        )

        set_color_scheme("default", env)
        invalid = run_case(
            "invalid-input-fallback",
            ["--appearance", "invalid-mode", "--clarity", "neon", "--wallpaper-r", "300", "--wallpaper-g", "-1", "--wallpaper-b", "2"],
            floor=48,
            expected={
                "appearancePreference": "follow-system",
                "resolvedAppearance": "light",
                "clarity": "balanced",
                "wallpaperAtmosphere": None,
            },
            env=env,
        )
    finally:
        if "prefer-dark" in original:
            set_color_scheme("prefer-dark", env)
        elif "prefer-light" in original:
            set_color_scheme("prefer-light", env)
        else:
            set_color_scheme("default", env)

    evidence = {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2 Personalization Linux adapter reference",
        "lifecycle": "Candidate native evidence",
        "sourceRevision": revision,
        "platform": "Linux GTK4 under Xvfb",
        "sourceContract": source_contract,
        "cases": [light, dark, deep_dark, reduced, invalid],
        "boundaries": [
            "not compositor-wide Wayland backdrop blur fidelity",
            "not physical-display qualification",
            "not assistive-technology acceptance",
            "not consumer persistence ownership",
            "not wallpaper-source acquisition",
            "not cross-device synchronization",
            "not production acceptance",
            "not Release Candidate acceptance",
            "not V1.2 Stable promotion",
        ],
    }
    path = OUT / "linux-personalization-evidence.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print("GLAZE UI V1.2 Linux Personalization adapter headless evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
