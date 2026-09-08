#!/usr/bin/env python3
"""Validate GLAZE UI V1.3 physical qualification support packets.

This validator is intentionally non-promotional. It checks packet integrity,
exact frozen-source binding, structural completeness, and fail-closed fields.
A successful validation means only that a packet is suitable for authorized
combined review; it never grants qualification credit or lifecycle acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

SOURCE_SHA = "72ad63bf32d80420b25dc98bfd2def47bcc2a427"
PACKET_SCHEMA = "goreecloud.glaze-ui.v1.3.qualification-support-packet.v1"
VALID_MODES = {"physical-device", "performance", "personalization", "native-host"}
MANIFEST_RE = re.compile(r"^([0-9a-f]{64})  (.+)$")


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def packet_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }


def parse_manifest(root: Path) -> dict[str, str]:
    manifest_path = root / "SHA256SUMS.txt"
    require(manifest_path.is_file(), "missing SHA256SUMS.txt")
    entries: dict[str, str] = {}
    for lineno, raw in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        match = MANIFEST_RE.fullmatch(raw)
        require(match is not None, f"invalid manifest line {lineno}")
        digest, name = match.groups()
        rel = Path(name)
        require(not rel.is_absolute(), f"manifest path must be relative: {name}")
        require(".." not in rel.parts, f"manifest path traversal is forbidden: {name}")
        normalized = rel.as_posix()
        require(normalized != "SHA256SUMS.txt", "manifest must not self-hash")
        require(normalized not in entries, f"duplicate manifest entry: {normalized}")
        entries[normalized] = digest
    require(entries, "manifest is empty")
    return entries


def verify_manifest(root: Path) -> None:
    entries = parse_manifest(root)
    actual = packet_files(root)
    require(set(entries) == actual, f"manifest/file-set mismatch: missing={sorted(actual-set(entries))}, extra={sorted(set(entries)-actual)}")
    for name, expected in entries.items():
        path = root / name
        require(path.is_file(), f"manifested file missing: {name}")
        actual_digest = sha256(path)
        require(actual_digest == expected, f"SHA-256 mismatch: {name}")


def load_report(root: Path) -> dict[str, Any]:
    path = root / "report.json"
    require(path.is_file(), "missing report.json")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid report.json: {exc}") from exc
    require(isinstance(report, dict), "report.json must contain an object")
    return report


def require_file(root: Path, name: str) -> None:
    require((root / name).is_file(), f"required evidence file missing: {name}")


def validate_common(root: Path, report: dict[str, Any]) -> str:
    require_file(root, "README.txt")
    require(report.get("schema") == PACKET_SCHEMA, "unexpected packet schema")
    require(report.get("frozen_source_revision") == SOURCE_SHA, "packet is not bound to the frozen V1.3 source SHA")
    mode = report.get("mode")
    require(mode in VALID_MODES, f"unsupported packet mode: {mode!r}")
    captured_at = report.get("captured_at")
    require(isinstance(captured_at, str) and captured_at.endswith("Z") and "T" in captured_at, "captured_at must be a UTC ISO-8601 timestamp")
    require(report.get("qualification_credit") is False, "support packet must not claim qualification credit")
    require(report.get("accepted_for_lifecycle_gate") is False, "support packet must not claim lifecycle acceptance")
    require(report.get("manual_or_combined_review_required") is True, "support packet must require manual/combined review")
    details = report.get("details")
    require(isinstance(details, dict), "report details must be an object")
    return str(mode)


def validate_android_inventory(value: Any, context: str) -> None:
    require(isinstance(value, dict), f"{context} Android inventory missing")
    for field in ("manufacturer", "model", "device", "android_release", "build_fingerprint"):
        entry = value.get(field)
        require(isinstance(entry, str) and entry.strip(), f"{context} Android inventory missing {field}")


def validate_physical_device(root: Path, report: dict[str, Any]) -> None:
    details = report["details"]
    validate_android_inventory(details.get("android"), "physical-device")
    require(details.get("manual_observation_required") is True, "physical-device packet must preserve manual-observation requirement")
    required = [
        "android/device-inventory.json",
        "android/wm-size.txt",
        "android/wm-density.txt",
        "android/display.txt",
        "android/window-displays.txt",
        "android/input.txt",
        "android/uimode.txt",
        "android/font-scale.txt",
        "android/animator-duration-scale.txt",
        "android/transition-animation-scale.txt",
        "android/window-animation-scale.txt",
    ]
    for name in required:
        require_file(root, name)


def validate_performance(root: Path, report: dict[str, Any]) -> None:
    details = report["details"]
    validate_android_inventory(details.get("android"), "performance")
    package = details.get("package_under_test")
    require(isinstance(package, str) and package.strip(), "performance packet must name package_under_test")
    count = details.get("sample_count")
    require(isinstance(count, int) and 1 <= count <= 120, "performance sample_count must be 1..120")
    interval = details.get("sample_interval_seconds")
    require(isinstance(interval, (int, float)) and 0 <= interval <= 60, "invalid performance sample interval")
    require(details.get("performance_budget_acceptance_required") is True, "performance budget acceptance must remain required")
    require(details.get("human_review_required") is True, "performance human review must remain required")
    for name in (
        "performance/device-inventory.json",
        "performance/battery.txt",
        "performance/thermal.txt",
        "performance/thermal-final.txt",
        "performance/battery-final.txt",
        "performance/surfaceflinger-list.txt",
        "performance/cpuinfo-initial.txt",
    ):
        require_file(root, name)
    for i in range(1, count + 1):
        stem = f"performance/samples/{i:02d}"
        for suffix in ("meminfo.txt", "gfxinfo-framestats.txt", "cpuinfo.txt"):
            require_file(root, f"{stem}-{suffix}")


def validate_personalization(root: Path, report: dict[str, Any]) -> str:
    details = report["details"]
    validate_android_inventory(details.get("android"), "personalization")
    phase = details.get("phase")
    require(phase in {"before", "after"}, "personalization phase must be before or after")
    require(details.get("raw_wallpaper_captured") is False, "raw wallpaper capture is forbidden")
    require(details.get("adapter_behavior_manual_observation_required") is True, "adapter behavior review must remain required")
    require(details.get("accessibility_precedence_manual_observation_required") is True, "accessibility precedence review must remain required")
    base = f"personalization/{phase}"
    for name in (
        "device-inventory.json",
        "uimode.txt",
        "font-scale.txt",
        "animator-duration-scale.txt",
        "transition-animation-scale.txt",
        "window-animation-scale.txt",
        "wallpaper-metadata-only.txt",
    ):
        require_file(root, f"{base}/{name}")
    forbidden = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}]
    require(not forbidden, "personalization packet must not contain wallpaper/image bytes")
    return str(phase)


def validate_native_host(root: Path, report: dict[str, Any]) -> None:
    details = report["details"]
    host = details.get("host")
    require(isinstance(host, dict), "native-host packet missing host details")
    for field in ("platform", "system", "release", "machine"):
        value = host.get(field)
        require(isinstance(value, str) and value.strip(), f"native-host details missing {field}")
    require(details.get("manual_native_behavior_observation_required") is True, "native-host behavior review must remain required")
    require_file(root, "native-host/environment.json")


def validate_packet(root: Path, expected_mode: str | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    require(root.is_dir(), f"packet directory does not exist: {root}")
    verify_manifest(root)
    report = load_report(root)
    mode = validate_common(root, report)
    if expected_mode:
        require(mode == expected_mode, f"expected {expected_mode} packet, got {mode}")
    if mode == "physical-device":
        validate_physical_device(root, report)
    elif mode == "performance":
        validate_performance(root, report)
    elif mode == "personalization":
        validate_personalization(root, report)
    else:
        validate_native_host(root, report)
    return report


def validate_personalization_pair(before: Path, after: Path) -> None:
    before_report = validate_packet(before, "personalization")
    after_report = validate_packet(after, "personalization")
    require(before_report["details"].get("phase") == "before", "first personalization packet must be phase=before")
    require(after_report["details"].get("phase") == "after", "second personalization packet must be phase=after")
    before_device = before_report["details"].get("android")
    after_device = after_report["details"].get("android")
    for key in ("manufacturer", "model", "device", "build_fingerprint"):
        require(before_device.get(key) == after_device.get(key), f"personalization before/after device mismatch: {key}")


def write_text(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_manifest(root: Path) -> None:
    lines = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"):
        lines.append(f"{sha256(path)}  {path.relative_to(root).as_posix()}")
    write_text(root, "SHA256SUMS.txt", "\n".join(lines) + "\n")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "packet"
        root.mkdir()
        inventory = {
            "manufacturer": "TEST",
            "model": "TEST",
            "device": "test",
            "android_release": "0",
            "security_patch": "1970-01-01",
            "build_fingerprint": "test/fingerprint",
        }
        details = {"android": inventory, "manual_observation_required": True}
        report = {
            "schema": PACKET_SCHEMA,
            "collector_version": 1,
            "frozen_source_revision": SOURCE_SHA,
            "mode": "physical-device",
            "captured_at": "1970-01-01T00:00:00Z",
            "details": details,
            "qualification_credit": False,
            "accepted_for_lifecycle_gate": False,
            "manual_or_combined_review_required": True,
            "notice": "TEST FIXTURE ONLY",
        }
        write_text(root, "report.json", json.dumps(report, indent=2) + "\n")
        write_text(root, "README.txt", "TEST FIXTURE ONLY\n")
        write_text(root, "android/device-inventory.json", json.dumps(inventory) + "\n")
        for name in (
            "wm-size.txt", "wm-density.txt", "display.txt", "window-displays.txt", "input.txt",
            "uimode.txt", "font-scale.txt", "animator-duration-scale.txt",
            "transition-animation-scale.txt", "window-animation-scale.txt",
        ):
            write_text(root, f"android/{name}", "test\n")
        write_manifest(root)
        validate_packet(root, "physical-device")
        # A lifecycle-accepting packet must be rejected even if its hashes are valid.
        report["accepted_for_lifecycle_gate"] = True
        write_text(root, "report.json", json.dumps(report, indent=2) + "\n")
        write_manifest(root)
        try:
            validate_packet(root)
        except ValidationError:
            pass
        else:
            raise AssertionError("validator accepted a promotional support packet")
    print("device qualification packet validator self-test: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("packet", help="validate one physical/native support packet")
    one.add_argument("path", type=Path)
    one.add_argument("--mode", choices=sorted(VALID_MODES))
    pair = sub.add_parser("personalization-pair", help="validate a before/after personalization packet pair")
    pair.add_argument("before", type=Path)
    pair.add_argument("after", type=Path)
    sub.add_parser("self-test", help="run non-qualification synthetic validator tests")
    args = parser.parse_args()

    try:
        if args.command == "self-test":
            self_test()
        elif args.command == "personalization-pair":
            validate_personalization_pair(args.before, args.after)
            print("VALID: personalization before/after packets are structurally and cryptographically ready for combined review; no qualification credit granted.")
        else:
            report = validate_packet(args.path, args.mode)
            print(f"VALID: {report['mode']} packet is structurally and cryptographically ready for combined review; no qualification credit granted.")
    except ValidationError as exc:
        raise SystemExit(f"INVALID qualification support packet: {exc}") from exc


if __name__ == "__main__":
    main()
