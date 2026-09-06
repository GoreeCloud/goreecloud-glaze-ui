#!/usr/bin/env python3
"""Fail-closed exact-head source readiness for the V1.2 Linux window reference.

This validator intentionally does not import GTK or claim rendered/native device
acceptance. It proves that the exact checked-out Candidate revision retains the
bounded desktop recomposition source contract and its non-claims. Full GTK/Xvfb
runtime evidence remains owned by validate_glaze_v1_2_linux_window_adaptation_runtime.py.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "reference/v1.2/native/linux-gtk/window_adaptation.py"
RESPONSIVE = ROOT / "contracts/v1.2/responsive-adaptation-reference.candidate.json"
RUNTIME_VALIDATOR = ROOT / "scripts/validate_glaze_v1_2_linux_window_adaptation_runtime.py"
LINUX_WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-linux-native.yml"
ARTIFACT = ROOT / "artifacts/glaze-v1.2-linux-window-adaptation-source-readiness.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class SourceReadinessError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SourceReadinessError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def exact_revision() -> str:
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    require(SHA40.fullmatch(revision) is not None, f"invalid Git HEAD: {revision!r}")
    expected = os.environ.get("GLAZE_SOURCE_REVISION", "").strip()
    if expected:
        require(expected == revision, f"exact source mismatch: checkout={revision}, expected={expected}")
    return revision


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment_int(module: ast.Module, name: str) -> int | None:
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != name:
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
            return node.value.value
    return None


def validate() -> dict[str, Any]:
    for path in (APP, RESPONSIVE, RUNTIME_VALIDATOR, LINUX_WORKFLOW):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    revision = exact_revision()
    contract = load_json(RESPONSIVE)
    source = APP.read_text(encoding="utf-8")
    runtime_validator = RUNTIME_VALIDATOR.read_text(encoding="utf-8")
    workflow = LINUX_WORKFLOW.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(APP))

    require(contract.get("version") == "1.2.0-candidate", "responsive version drifted")
    require(contract.get("lifecycle") == "candidate", "responsive lifecycle must remain Candidate")
    require(contract.get("consumerEligible") is False, "responsive Candidate became consumer-eligible")
    require(contract.get("stableBaseline") == "1.1.0", "Stable baseline drifted")

    authority = contract.get("authority", {})
    require(
        authority.get("principle") == "Adapt the experience, not merely the dimensions.",
        "responsive adaptation principle drifted",
    )
    mapping = contract.get("layoutClassMapping", {})
    require(mapping.get("narrow-desktop") == "compact", "narrow desktop must remain compact")
    require(mapping.get("standard-desktop") == "expanded", "standard desktop must remain expanded")

    authority_boundary = contract.get("authorityBoundary", {})
    require(authority_boundary.get("runtimeInfersDeviceIdentity") is False, "runtime device-identity inference became allowed")
    require(authority_boundary.get("runtimeSelectsProductionCapabilityClass") is False, "runtime production capability selection became allowed")
    require(authority_boundary.get("platformAdapterRemainsCapabilitySelectionAuthority") is True, "platform adapter capability authority drifted")

    missing = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for required in (
        "real-foldable-hinge-posture-runtime-acceptance",
        "native-form-factor-parity",
        "release-candidate",
        "stable",
        "consumer-conformance",
    ):
        require(required in missing, f"responsive source overclaimed boundary: {required}")

    threshold = assignment_int(module, "WIDE_THRESHOLD_PX")
    require(threshold == 900, f"Linux reference wide threshold drifted: {threshold!r}")

    required_source_markers = (
        "Adapt the experience, not merely the dimensions.",
        'self.layout_class = "expanded" if wide else "compact"',
        "self.panel_count = 2 if wide else 1",
        "Research Library · current task preserved",
        "width does not infer device identity",
        "not hinge sensor or posture semantics",
        "not physical foldable qualification",
        "not automatic production capability selection",
        "not native form-factor parity",
        "not release candidate",
        "not V1.2 Stable promotion",
    )
    for marker in required_source_markers:
        require(marker in source, f"Linux window reference missing source marker: {marker}")

    for marker in (
        '"window-compact"',
        '"window-expanded"',
        '760,',
        '1180,',
        '"compact"',
        '"expanded"',
        '"Research Library · current task preserved"',
        '"not native form-factor parity"',
    ):
        require(marker in runtime_validator, f"Linux runtime validator lost gate marker: {marker}")

    require(
        "validate_glaze_v1_2_linux_window_adaptation_runtime.py" in workflow,
        "Linux workflow no longer runs the bounded window adaptation runtime gate",
    )
    require(
        "linux-window-adaptation-evidence.json" in workflow,
        "Linux workflow no longer uploads window-adaptation evidence",
    )

    paths = (APP, RESPONSIVE, RUNTIME_VALIDATOR, LINUX_WORKFLOW)
    return {
        "schemaVersion": 1,
        "product": "GLAZE UI V1.2",
        "version": "1.2.0-candidate",
        "lifecycle": "candidate-source-readiness",
        "sourceRevision": revision,
        "status": "bounded-source-evidence-present",
        "consumerEligible": False,
        "promotionReady": False,
        "rcReady": False,
        "stableReady": False,
        "productionReady": False,
        "evidenceKind": "linux-gtk-window-adaptation-source-readiness",
        "principle": authority["principle"],
        "wideThresholdPx": threshold,
        "fixtureSemantics": {
            "compact": {"requestedWidthPx": 760, "expectedPanels": 1},
            "expanded": {"requestedWidthPx": 1180, "expectedPanels": 2},
            "primaryTaskContinuityRequired": True,
            "expandedAddsContextRatherThanOnlyScaling": True,
        },
        "authorityBoundary": {
            "widthIsDeviceIdentity": False,
            "productionCapabilitySelectionEstablished": False,
            "hingeOrPostureRuntimeAcceptanceEstablished": False,
            "physicalFoldableQualificationEstablished": False,
            "nativeFormFactorParityEstablished": False,
        },
        "sourceDigestsSha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in paths
        },
        "notEstablished": [
            "rendered-gtk-window-adaptation-evidence-by-this-source-gate",
            "physical-foldable-qualification",
            "real-hinge-or-posture-runtime-acceptance",
            "automatic-production-capability-selection",
            "native-form-factor-parity",
            "production-desktop-shell-integration",
            "release-candidate",
            "stable",
            "consumer-conformance",
        ],
    }


def main() -> int:
    try:
        evidence = validate()
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        require(ARTIFACT.stat().st_size > 1000, "source readiness artifact unexpectedly small")
        print(
            "PASS: GLAZE UI V1.2 Linux bounded window adaptation source readiness "
            f"is exact-head bound at {evidence['sourceRevision']}; native device, RC, "
            "Stable, production, and consumer claims remain false."
        )
        return 0
    except Exception as error:
        print(f"Linux window adaptation source readiness failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
