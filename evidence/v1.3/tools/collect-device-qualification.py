#!/usr/bin/env python3
"""Collect review-support evidence for GLAZE UI V1.3 physical qualification.

This tool deliberately cannot create accepted qualification records. It captures
inspectable evidence for human/combined review while binding every packet to the
frozen source revision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

SOURCE_SHA = "72ad63bf32d80420b25dc98bfd2def47bcc2a427"
COLLECTOR_VERSION = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: list[str], *, timeout: int = 60, allow_failure: bool = False) -> str:
    try:
        proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        if allow_failure:
            return f"UNAVAILABLE: {exc}\n"
        raise SystemExit(f"Command failed to execute: {' '.join(cmd)}: {exc}") from exc
    text = (proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else "")
    if proc.returncode != 0 and not allow_failure:
        raise SystemExit(f"Command returned {proc.returncode}: {' '.join(cmd)}\n{text}")
    return text


def write_text(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(root: Path) -> None:
    lines: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"):
        lines.append(f"{sha256(path)}  {path.relative_to(root).as_posix()}")
    write_text(root, "SHA256SUMS.txt", "\n".join(lines) + "\n")


def adb_prefix(serial: str | None) -> list[str]:
    adb = shutil.which("adb")
    if not adb:
        raise SystemExit("adb is required for Android physical-device collection.")
    devices = run([adb, "devices"], allow_failure=False)
    ready: list[str] = []
    for line in devices.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            ready.append(parts[0])
    if serial:
        if serial not in ready:
            raise SystemExit("Requested adb device is not connected and authorized.")
        return [adb, "-s", serial]
    if len(ready) != 1:
        raise SystemExit(f"Exactly one authorized adb device is required unless --serial is supplied; found {len(ready)}.")
    return [adb, "-s", ready[0]]


def adb_shell(prefix: list[str], *args: str, timeout: int = 60, allow_failure: bool = True) -> str:
    return run(prefix + ["shell", *args], timeout=timeout, allow_failure=allow_failure)


def android_inventory(prefix: list[str]) -> dict[str, str]:
    props = {
        "manufacturer": "ro.product.manufacturer",
        "model": "ro.product.model",
        "device": "ro.product.device",
        "android_release": "ro.build.version.release",
        "security_patch": "ro.build.version.security_patch",
        "build_fingerprint": "ro.build.fingerprint",
    }
    return {name: adb_shell(prefix, "getprop", prop).strip() for name, prop in props.items()}


def collect_physical_device(root: Path, prefix: list[str]) -> dict:
    inventory = android_inventory(prefix)
    write_text(root, "android/device-inventory.json", json.dumps(inventory, indent=2) + "\n")
    commands = {
        "android/wm-size.txt": ["wm", "size"],
        "android/wm-density.txt": ["wm", "density"],
        "android/display.txt": ["dumpsys", "display"],
        "android/window-displays.txt": ["dumpsys", "window", "displays"],
        "android/input.txt": ["dumpsys", "input"],
        "android/uimode.txt": ["cmd", "uimode", "night"],
        "android/font-scale.txt": ["settings", "get", "system", "font_scale"],
        "android/animator-duration-scale.txt": ["settings", "get", "global", "animator_duration_scale"],
        "android/transition-animation-scale.txt": ["settings", "get", "global", "transition_animation_scale"],
        "android/window-animation-scale.txt": ["settings", "get", "global", "window_animation_scale"],
    }
    for filename, args in commands.items():
        write_text(root, filename, adb_shell(prefix, *args))
    return {"android": inventory, "manual_observation_required": True}


def collect_performance(root: Path, prefix: list[str], package: str, samples: int, interval: float) -> dict:
    if not package:
        raise SystemExit("--package is required for production-performance collection.")
    inventory = android_inventory(prefix)
    write_text(root, "performance/device-inventory.json", json.dumps(inventory, indent=2) + "\n")
    write_text(root, "performance/battery.txt", adb_shell(prefix, "dumpsys", "battery"))
    write_text(root, "performance/thermal.txt", adb_shell(prefix, "dumpsys", "thermalservice"))
    write_text(root, "performance/surfaceflinger-list.txt", adb_shell(prefix, "dumpsys", "SurfaceFlinger", "--list"))
    write_text(root, "performance/cpuinfo-initial.txt", adb_shell(prefix, "dumpsys", "cpuinfo"))
    adb_shell(prefix, "dumpsys", "gfxinfo", package, "reset")
    for i in range(samples):
        stem = f"performance/samples/{i + 1:02d}"
        write_text(root, f"{stem}-meminfo.txt", adb_shell(prefix, "dumpsys", "meminfo", package, timeout=90))
        write_text(root, f"{stem}-gfxinfo-framestats.txt", adb_shell(prefix, "dumpsys", "gfxinfo", package, "framestats", timeout=90))
        write_text(root, f"{stem}-cpuinfo.txt", adb_shell(prefix, "dumpsys", "cpuinfo", timeout=90))
        if i + 1 < samples:
            time.sleep(interval)
    write_text(root, "performance/thermal-final.txt", adb_shell(prefix, "dumpsys", "thermalservice"))
    write_text(root, "performance/battery-final.txt", adb_shell(prefix, "dumpsys", "battery"))
    return {
        "android": inventory,
        "package_under_test": package,
        "sample_count": samples,
        "sample_interval_seconds": interval,
        "performance_budget_acceptance_required": True,
        "human_review_required": True,
    }


def collect_personalization(root: Path, prefix: list[str], phase: str) -> dict:
    inventory = android_inventory(prefix)
    base = Path("personalization") / phase
    write_text(root, str(base / "device-inventory.json"), json.dumps(inventory, indent=2) + "\n")
    commands = {
        "uimode.txt": ["cmd", "uimode", "night"],
        "font-scale.txt": ["settings", "get", "system", "font_scale"],
        "animator-duration-scale.txt": ["settings", "get", "global", "animator_duration_scale"],
        "transition-animation-scale.txt": ["settings", "get", "global", "transition_animation_scale"],
        "window-animation-scale.txt": ["settings", "get", "global", "window_animation_scale"],
    }
    for filename, args in commands.items():
        write_text(root, str(base / filename), adb_shell(prefix, *args))
    # Metadata-only wallpaper evidence. No wallpaper image bytes are read or transmitted.
    wallpaper = adb_shell(prefix, "sh", "-c", "dumpsys wallpaper | grep -E 'mWallpaperId|mWidth|mHeight|mPrimaryColors|mColors' || true")
    write_text(root, str(base / "wallpaper-metadata-only.txt"), wallpaper)
    return {
        "android": inventory,
        "phase": phase,
        "raw_wallpaper_captured": False,
        "adapter_behavior_manual_observation_required": True,
        "accessibility_precedence_manual_observation_required": True,
    }


def collect_native_host(root: Path) -> dict:
    env_keys = ["XDG_SESSION_TYPE", "XDG_CURRENT_DESKTOP", "DESKTOP_SESSION", "WAYLAND_DISPLAY", "DISPLAY"]
    env = {key: os.environ.get(key) for key in env_keys}
    host = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "desktop_environment": env,
    }
    write_text(root, "native-host/environment.json", json.dumps(host, indent=2) + "\n")
    optional = {
        "native-host/uname.txt": ["uname", "-a"],
        "native-host/loginctl-session.txt": ["loginctl", "show-session", os.environ.get("XDG_SESSION_ID", "self"), "-p", "Type", "-p", "Desktop", "-p", "Remote"],
        "native-host/wayland-info.txt": ["wayland-info"],
        "native-host/xdpyinfo.txt": ["xdpyinfo"],
    }
    for filename, cmd in optional.items():
        if shutil.which(cmd[0]):
            write_text(root, filename, run(cmd, allow_failure=True))
    return {"host": host, "manual_native_behavior_observation_required": True}


def build_report(mode: str, details: dict) -> dict:
    return {
        "schema": "goreecloud.glaze-ui.v1.3.qualification-support-packet.v1",
        "collector_version": COLLECTOR_VERSION,
        "frozen_source_revision": SOURCE_SHA,
        "mode": mode,
        "captured_at": now_iso(),
        "details": details,
        "qualification_credit": False,
        "accepted_for_lifecycle_gate": False,
        "manual_or_combined_review_required": True,
        "notice": "This packet is supporting evidence only. It cannot activate Candidate, Stable, consumer conformance, or production eligibility.",
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_text(root, "a.txt", "glaze\n")
        write_manifest(root)
        manifest = (root / "SHA256SUMS.txt").read_text(encoding="utf-8")
        assert sha256(root / "a.txt") in manifest
        report = build_report("self-test", {"ok": True})
        assert report["frozen_source_revision"] == SOURCE_SHA
        assert report["qualification_credit"] is False
        assert report["accepted_for_lifecycle_gate"] is False
    print("device qualification collector self-test: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect fail-closed V1.3 physical qualification support evidence.")
    parser.add_argument("mode", choices=["physical-device", "performance", "personalization", "native-host", "self-test"])
    parser.add_argument("--output", default="artifacts/v1.3/device-qualification-packet")
    parser.add_argument("--serial", help="adb serial selector; the serial is used only for transport selection and is not written to evidence")
    parser.add_argument("--package", default="", help="Android package under performance test")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--phase", choices=["before", "after"], default="before")
    args = parser.parse_args()

    if args.mode == "self-test":
        self_test()
        return
    if args.samples < 1 or args.samples > 120:
        raise SystemExit("--samples must be between 1 and 120")
    if args.interval < 0 or args.interval > 60:
        raise SystemExit("--interval must be between 0 and 60 seconds")

    root = Path(args.output).resolve()
    if root.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence directory: {root}")
    root.mkdir(parents=True)

    if args.mode == "native-host":
        details = collect_native_host(root)
    else:
        prefix = adb_prefix(args.serial)
        if args.mode == "physical-device":
            details = collect_physical_device(root, prefix)
        elif args.mode == "performance":
            details = collect_performance(root, prefix, args.package, args.samples, args.interval)
        else:
            details = collect_personalization(root, prefix, args.phase)

    report = build_report(args.mode, details)
    write_text(root, "report.json", json.dumps(report, indent=2) + "\n")
    write_text(
        root,
        "README.txt",
        "GLAZE UI V1.3 physical qualification support packet\n"
        f"Frozen source: {SOURCE_SHA}\n"
        "Supporting evidence only; human/combined review and an immutable schema-v2 evidence record are still required.\n"
        "No raw wallpaper image bytes are collected. adb serial identifiers are not retained in the packet.\n",
    )
    write_manifest(root)
    print(root)


if __name__ == "__main__":
    main()
