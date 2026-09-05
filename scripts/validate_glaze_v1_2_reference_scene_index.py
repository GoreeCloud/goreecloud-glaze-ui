#!/usr/bin/env python3
"""Validate the bounded GLAZE UI V1.2 Phase 5 reference-scene index."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "contracts/v1.2/reference-scenes.candidate.json"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-reference-scenes.yml"
EXPECTED_IDS = [
    "canonical-light",
    "canonical-dark",
    "canonical-deep-dark",
    "desktop-dashboard",
    "mobile",
    "tablet",
    "productive-table",
    "settings-form",
    "universal-search",
    "modal-sheet",
    "loading-error-recovery",
    "reduced-transparency",
    "increased-contrast",
    "large-text",
    "rtl",
    "application-icon-ecosystem-wall",
]
ESTABLISHED_STATUS = "bounded-reference-established"
OPEN_STATUS = "planned-open"


class ValidationError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def nested_get(value: dict[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        require(isinstance(current, dict) and part in current, f"missing owner state {dotted}")
        current = current[part]
    return current


def validate_manifest() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = load_json(MANIFEST)
    require(manifest.get("schemaVersion") == 1, "reference-scene schema drifted")
    require(manifest.get("id") == "glaze-v1.2-reference-scenes-candidate", "reference-scene id drifted")
    require(manifest.get("product") == "GLAZE UI", "reference-scene product drifted")
    require(manifest.get("version") == "1.2.0-candidate", "reference-scene version drifted")
    require(manifest.get("lifecycle") == "candidate", "reference-scene lifecycle drifted")
    require(manifest.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    require(manifest.get("consumerEligible") is False, "V1.2 reference scenes became consumer eligible")
    require(manifest.get("phase") == "Phase 5 — Reference Scenes", "Phase 5 label drifted")
    require(manifest.get("requiredSceneCount") == 16, "required scene count drifted")
    require(manifest.get("boundedEstablishedCount") == 15, "bounded established count drifted")
    require(manifest.get("phase5ReferenceScenesComplete") is False, "Phase 5 must fail closed while Ecosystem Wall is open")
    require(manifest.get("openSceneIds") == ["application-icon-ecosystem-wall"], "open scene set drifted")

    scenes = manifest.get("scenes")
    require(isinstance(scenes, list), "scenes must be an array")
    require([scene.get("id") for scene in scenes if isinstance(scene, dict)] == EXPECTED_IDS, "reference scene set/order drifted")
    established = [scene for scene in scenes if isinstance(scene, dict) and scene.get("status") == ESTABLISHED_STATUS]
    opened = [scene for scene in scenes if isinstance(scene, dict) and scene.get("status") == OPEN_STATUS]
    require(len(established) == 15, f"expected 15 bounded established scenes, found {len(established)}")
    require(len(opened) == 1 and opened[0].get("id") == "application-icon-ecosystem-wall", "planned-open scene drifted")
    require(len(established) + len(opened) == 16, "unexpected reference-scene status introduced")

    boundary = manifest.get("evidenceBoundary", {})
    require("bounded-v1.2-reference-scene-accounting" in boundary.get("established", []), "bounded accounting evidence missing")
    for item in (
        "phase5-reference-scenes-complete",
        "application-icon-ecosystem-wall",
        "v1.2-human-approved-visual-baseline",
        "full-visual-regression",
        "human-optical-acceptance",
        "assistive-technology-acceptance",
        "production-performance-acceptance",
        "complete-native-parity",
        "release-candidate",
        "stable",
        "consumer-conformance",
    ):
        require(item in boundary.get("notEstablished", []), f"evidence boundary missing: {item}")
    return manifest, scenes


def validate_established_scenes(scenes: list[dict[str, Any]]) -> None:
    for scene in scenes:
        if scene.get("status") != ESTABLISHED_STATUS:
            continue
        scene_id = str(scene.get("id"))
        source_path = scene.get("sourcePath")
        validator_path = scene.get("validatorPath")
        source_markers = scene.get("sourceMarkers")
        validator_markers = scene.get("validatorMarkers")
        require(isinstance(source_path, str) and source_path.startswith("reference/v1.2/"), f"{scene_id}: source must stay in reference/v1.2")
        require("v1.1" not in source_path and "candidate-2.1" not in source_path, f"{scene_id}: foreign reference authority bound")
        require(isinstance(validator_path, str) and validator_path.startswith("scripts/validate_glaze_v1_2_"), f"{scene_id}: validator must be V1.2 scoped")
        require(isinstance(source_markers, list) and source_markers, f"{scene_id}: source markers missing")
        require(isinstance(validator_markers, list) and validator_markers, f"{scene_id}: validator markers missing")

        source = ROOT / source_path
        validator = ROOT / validator_path
        require(source.is_file(), f"{scene_id}: missing {source_path}")
        require(validator.is_file(), f"{scene_id}: missing {validator_path}")
        source_text = source.read_text(encoding="utf-8")
        validator_text = validator.read_text(encoding="utf-8")
        for marker in source_markers:
            require(isinstance(marker, str) and marker in source_text, f"{scene_id}: source marker missing: {marker}")
        for marker in validator_markers:
            require(isinstance(marker, str) and marker in validator_text, f"{scene_id}: validator marker missing: {marker}")


def validate_open_scene(scenes: list[dict[str, Any]]) -> None:
    scene = next(scene for scene in scenes if scene.get("id") == "application-icon-ecosystem-wall")
    require(scene.get("status") == OPEN_STATUS, "Ecosystem Wall must remain planned-open until owner evidence changes")
    owner_path = scene.get("ownerPath")
    require(owner_path == "tokens/icon-identity.json", "Ecosystem Wall owner path drifted")
    owner = load_json(ROOT / owner_path)
    required = scene.get("requiredOwnerState")
    require(isinstance(required, dict) and required, "Ecosystem Wall owner-state requirements missing")
    for dotted, expected in required.items():
        require(nested_get(owner, dotted) == expected, f"Ecosystem Wall owner state drifted: {dotted}")
    require(owner.get("meta", {}).get("status") == "stable", "icon identity owner is not Stable")


def validate_regression_boundaries(manifest: dict[str, Any]) -> None:
    excluded = manifest.get("excludedRegressionAuthorities")
    require(isinstance(excluded, list) and [item.get("path") for item in excluded] == [
        "contracts/regression/visual-baselines-v1.json",
        "contracts/regression/reference-invariants.json",
    ], "excluded regression authority set/order drifted")

    stable = load_json(ROOT / "contracts/regression/visual-baselines-v1.json")
    require(stable.get("product") == "GLAZE UI V1.1", "V1 visual baseline product drifted")
    require(stable.get("version") == "1.1.0", "V1 visual baseline version drifted")
    require(stable.get("status") == "stable-human-approved-source-pinned", "V1 visual baseline status drifted")
    require(stable.get("newOpticalPixelsRequireNewHumanApproval") is True, "human approval boundary drifted")

    future = load_json(ROOT / "contracts/regression/reference-invariants.json")
    require(future.get("id") == "glaze-ui-2.1-reference-regression", "future regression id drifted")
    require(future.get("lifecycle") == "candidate", "future regression lifecycle drifted")
    require(future.get("since") == "2.1.0-candidate.1", "future regression version drifted")
    require(future.get("promotionBoundary", {}).get("humanVisualExcellenceRequired") is True, "future human visual boundary drifted")


def validate_workflow() -> None:
    require(WORKFLOW.is_file(), f"missing {WORKFLOW.relative_to(ROOT)}")
    text = WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "Glaze V1.2 Reference Scene Index Candidate",
        "github.event.pull_request.head.sha || github.sha",
        "persist-credentials: false",
        "python scripts/validate_glaze_v1.py",
        "python scripts/validate_glaze_v1_2_candidate.py",
        "python scripts/validate_glaze_v1_2_reference_scene_index.py",
    ):
        require(marker in text, f"reference-scene workflow marker missing: {marker}")


def main() -> int:
    try:
        manifest, scenes = validate_manifest()
        validate_established_scenes(scenes)
        validate_open_scene(scenes)
        validate_regression_boundaries(manifest)
        validate_workflow()
    except (ValidationError, json.JSONDecodeError, OSError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: V1.2 Phase 5 reference-scene index is bounded, source-bound, and fail-closed at 15/16; Ecosystem Wall remains planned-open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
