#!/usr/bin/env python3
"""Headless GTK4 window-adaptation acceptance for GLAZE UI V1.2 Candidate.

This gate proves bounded Linux desktop window recomposition at the exact source
revision. It intentionally does not claim physical foldable/hinge behavior,
automatic device identity, native form-factor parity, production, RC, or Stable.
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
REFERENCE = ROOT / "reference/v1.2/native/linux-gtk"
APP = REFERENCE / "window_adaptation.py"
RESPONSIVE_CONTRACT = ROOT / "contracts/v1.2/responsive-adaptation-reference.candidate.json"
OUT = ROOT / ".artifacts/glaze-v1.2-linux-native"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def run(
    *args: str,
    check: bool = True,
    text: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        check=check,
        text=text,
        capture_output=True,
        env=env,
    )


def exact_revision() -> str:
    revision = run("git", "-C", str(ROOT), "rev-parse", "HEAD").stdout.strip()
    if not SHA40.fullmatch(revision):
        raise SystemExit(f"could not resolve exact source revision: {revision!r}")
    expected = os.environ.get("GLAZE_SOURCE_REVISION", "").strip()
    if expected and expected != revision:
        raise SystemExit(
            f"exact source mismatch: checkout={revision}, expected={expected}"
        )
    return revision


def validate_source_contract() -> dict:
    contract = json.loads(RESPONSIVE_CONTRACT.read_text(encoding="utf-8"))
    source = APP.read_text(encoding="utf-8")

    if contract.get("lifecycle") != "candidate":
        raise SystemExit("responsive adaptation contract must remain Candidate")
    authority = contract.get("authority", {})
    if authority.get("principle") != "Adapt the experience, not merely the dimensions.":
        raise SystemExit("responsive adaptation principle drift")

    mapping = contract.get("layoutClassMapping", {})
    if mapping.get("narrow-desktop") != "compact":
        raise SystemExit("narrow-desktop must remain compact")
    if mapping.get("standard-desktop") != "expanded":
        raise SystemExit("standard-desktop must remain expanded")

    boundary = contract.get("authorityBoundary", {})
    if boundary.get("runtimeInfersDeviceIdentity") is not False:
        raise SystemExit("runtime must not infer device identity")
    if boundary.get("runtimeSelectsProductionCapabilityClass") is not False:
        raise SystemExit("runtime must not select production capability class")

    not_established = contract.get("evidenceBoundary", {}).get(
        "notEstablished",
        [],
    )
    if "native-form-factor-parity" not in not_established:
        raise SystemExit(
            "Linux window evidence must not erase native form-factor parity boundary"
        )
    if "real-foldable-hinge-posture-runtime-acceptance" not in not_established:
        raise SystemExit(
            "Linux window evidence must not claim real foldable hinge/posture acceptance"
        )

    required_source_phrases = (
        "Adapt the experience, not merely the dimensions.",
        "width does not infer device identity",
        "not hinge sensor or posture semantics",
        "not native form-factor parity",
        "not V1.2 Stable promotion",
    )
    for phrase in required_source_phrases:
        if phrase not in source:
            raise SystemExit(
                f"Linux window adaptation reference missing boundary phrase: {phrase}"
            )

    return {
        "principle": authority["principle"],
        "narrowDesktop": mapping["narrow-desktop"],
        "standardDesktop": mapping["standard-desktop"],
        "deviceIdentityInference": False,
        "productionCapabilitySelection": False,
        "nativeFormFactorParityEstablished": False,
        "foldableHingePostureAcceptanceEstablished": False,
    }


def wait_for_file(
    path: Path,
    process: subprocess.Popen,
    timeout: float = 15.0,
) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size > 0:
            return json.loads(path.read_text(encoding="utf-8"))
        code = process.poll()
        if code is not None:
            stdout, stderr = process.communicate(timeout=2)
            raise SystemExit(
                f"GTK window Candidate exited before evidence was ready ({code})\n"
                f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )
        time.sleep(0.1)

    process.terminate()
    stdout, stderr = process.communicate(timeout=4)
    raise SystemExit(
        "timed out waiting for GTK window adaptation evidence\n"
        f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    )


def screenshot(path: Path, env: dict[str, str]) -> str:
    result = run(
        "import",
        "-window",
        "root",
        str(path),
        check=False,
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"ImageMagick root screenshot failed:\n{result.stderr}"
        )
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"invalid Linux screenshot PNG: {path}")
    return hashlib.sha256(payload).hexdigest()


def run_case(
    case_id: str,
    width: int,
    height: int,
    expected_layout: str,
    expected_panels: int,
    *,
    env: dict[str, str],
) -> dict:
    case_dir = OUT / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = case_dir / "runtime.json"
    shot_path = OUT / f"linux-v1.2-{case_id}.png"
    if evidence_path.exists():
        evidence_path.unlink()

    command = [
        sys.executable,
        str(APP),
        "--window-width",
        str(width),
        "--window-height",
        str(height),
        "--evidence-file",
        str(evidence_path),
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        evidence = wait_for_file(evidence_path, process)
        if not evidence.get("ready"):
            raise SystemExit(f"{case_id} runtime did not report ready")
        if evidence.get("lifecycle") != "Candidate native evidence":
            raise SystemExit(
                f"{case_id} lifecycle drift: {evidence.get('lifecycle')}"
            )
        if evidence.get("evidenceKind") != "bounded-window-recomposition":
            raise SystemExit(f"{case_id} evidence kind drift")
        if evidence.get("capabilityAuthority") != (
            "window-width fixture only; width does not infer device identity"
        ):
            raise SystemExit(f"{case_id} capability authority drift")

        actual_width = int(evidence["window"]["width"])
        threshold = int(evidence["window"]["wideThresholdPx"])
        actual_layout = evidence.get("layoutClass")
        expected_from_runtime = (
            "expanded" if actual_width >= threshold else "compact"
        )
        if actual_layout != expected_from_runtime:
            raise SystemExit(
                f"{case_id} layout does not match runtime width: "
                f"width={actual_width}, threshold={threshold}, "
                f"layout={actual_layout}"
            )
        if actual_layout != expected_layout:
            raise SystemExit(
                f"{case_id} expected {expected_layout}, got {actual_layout}; "
                f"runtime width={actual_width}"
            )

        panels = int(evidence.get("panelCount", 0))
        runtime_children = int(evidence.get("runtimeWorkspaceChildren", 0))
        if panels != expected_panels or runtime_children != expected_panels:
            raise SystemExit(
                f"{case_id} panel recomposition mismatch: "
                f"declared={panels}, runtimeChildren={runtime_children}, "
                f"expected={expected_panels}"
            )

        if evidence.get("primaryTaskPresent") is not True:
            raise SystemExit(f"{case_id} primary task disappeared")
        if evidence.get("primaryTaskValue") != (
            "Research Library · current task preserved"
        ):
            raise SystemExit(f"{case_id} primary task value drift")

        added_context = evidence.get("addedContext")
        if added_context is not (expected_layout == "expanded"):
            raise SystemExit(
                f"{case_id} added-context semantics mismatch: {added_context}"
            )

        boundaries = evidence.get("boundaries", [])
        for required in (
            "not hinge sensor or posture semantics",
            "not physical foldable qualification",
            "not automatic production capability selection",
            "not native form-factor parity",
            "not V1.2 Stable promotion",
        ):
            if required not in boundaries:
                raise SystemExit(
                    f"{case_id} missing evidence boundary: {required}"
                )

        digest = screenshot(shot_path, env)
        return {
            "id": case_id,
            "requestedWindow": {"width": width, "height": height},
            "runtimeWindow": evidence["window"],
            "layoutClass": actual_layout,
            "panelCount": panels,
            "primaryTaskPresent": True,
            "addedContext": bool(added_context),
            "screenshot": shot_path.name,
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
        raise SystemExit(
            "DISPLAY is required; run under xvfb-run or an X11 session"
        )

    cases = [
        run_case(
            "window-compact",
            760,
            680,
            "compact",
            1,
            env=env,
        ),
        run_case(
            "window-expanded",
            1180,
            760,
            "expanded",
            2,
            env=env,
        ),
    ]

    evidence = {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2",
        "lifecycle": "Candidate native evidence",
        "sourceRevision": revision,
        "platform": "Linux GTK4 under Xvfb",
        "evidenceKind": "bounded-window-recomposition",
        "sourceContract": source_contract,
        "cases": cases,
        "boundaries": [
            "not hinge sensor or posture semantics",
            "not physical foldable qualification",
            "not automatic production capability selection",
            "not native form-factor parity",
            "not production desktop shell integration",
            "not release candidate",
            "not V1.2 Stable promotion",
        ],
    }
    evidence_path = OUT / "linux-window-adaptation-evidence.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2))
    print(
        "GLAZE UI V1.2 Linux GTK4 bounded window adaptation acceptance: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
