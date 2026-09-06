#!/usr/bin/env python3
"""Validate and emit the fail-closed GLAZE UI V1.2 human optical review handoff."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/v1.2/human-optical-review-packet.candidate.json"
GUIDE = ROOT / "acceptance/v1.2-human-optical-review-packet.candidate.md"
VISUAL = ROOT / "contracts/v1.2/visual-regression.candidate.json"
ICON_WALL = ROOT / "contracts/v1.2/application-icon-ecosystem-wall.candidate.json"
REFERENCE_SCENES = ROOT / "contracts/v1.2/reference-scenes.candidate.json"
READINESS = ROOT / "contracts/v1.2/exact-head-readiness.candidate.json"
LIFECYCLE = ROOT / "registry/lifecycle.json"
VERSION = ROOT / "VERSION"
ARTIFACT = ROOT / "artifacts/glaze-v1.2-human-optical-review-manifest.json"

EXPECTED_EVIDENCE_IDS = [
    "provisional-visual-regression",
    "application-icon-ecosystem-wall",
    "reference-scene-index",
    "exact-head-readiness",
]
EXPECTED_WORKFLOWS = {
    "provisional-visual-regression": (
        "Glaze V1.2 Provisional Visual Regression Candidate",
        ".github/workflows/glaze-v1.2-visual-regression.yml",
        "glaze-v1.2-provisional-visual-regression-",
    ),
    "application-icon-ecosystem-wall": (
        "Glaze V1.2 Application Icon Ecosystem Wall Candidate",
        ".github/workflows/glaze-v1.2-application-icon-ecosystem-wall.yml",
        "glaze-v1.2-application-icon-ecosystem-wall-",
    ),
    "reference-scene-index": (
        "Glaze V1.2 Reference Scene Index Candidate",
        ".github/workflows/glaze-v1.2-reference-scenes.yml",
        "glaze-v1.2-reference-scenes-",
    ),
    "exact-head-readiness": (
        "Glaze V1.2 Exact-Head Readiness Candidate",
        ".github/workflows/glaze-v1.2-exact-head-readiness.yml",
        "glaze-v1.2-exact-head-readiness-",
    ),
}
EXPECTED_CLAIMS = {
    "humanOpticalAccepted": False,
    "referenceScenesComplete": False,
    "releaseCandidateReady": False,
    "stableReady": False,
    "productionReady": False,
    "consumerEligible": False,
    "promotionEligible": False,
    "reviewStatus": "pending",
}


class ReviewPacketError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReviewPacketError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_revision() -> str:
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None, "Git HEAD is not immutable")
    return revision


def validate_contract() -> tuple[dict[str, Any], list[Path]]:
    contract = load_json(CONTRACT)
    require(contract.get("schemaVersion") == 1, "review-packet schema drifted")
    require(contract.get("id") == "glaze-v1.2-human-optical-review-packet-candidate", "review-packet id drifted")
    require(contract.get("product") == "GLAZE UI", "review-packet product drifted")
    require(contract.get("version") == "1.2.0-candidate", "review-packet version drifted")
    require(contract.get("lifecycle") == "candidate", "review-packet lifecycle drifted")
    require(contract.get("stableBaseline") == "1.1.0", "review-packet Stable baseline drifted")
    require(contract.get("consumerEligible") is False, "review packet became consumer eligible")
    require(contract.get("status") == "machine-handoff-ready-human-review-pending", "review-packet status drifted")

    binding = contract.get("exactHeadBinding", {})
    require(binding == {
        "source": "git rev-parse HEAD",
        "sameRevisionRequiredAcrossArtifacts": True,
        "staticRevisionInContractProhibited": True,
    }, "exact-head review binding drifted")
    require(re.search(r"\b[0-9a-f]{40}\b", CONTRACT.read_text(encoding="utf-8")) is None,
            "review-packet contract must not embed a static Candidate revision")

    evidence = contract.get("evidenceClasses")
    require(isinstance(evidence, list), "evidenceClasses must be an array")
    require([item.get("id") for item in evidence if isinstance(item, dict)] == EXPECTED_EVIDENCE_IDS,
            "review evidence class order/set drifted")
    workflow_paths: list[Path] = []
    for item in evidence:
        evidence_id = item["id"]
        workflow_name, workflow_path, artifact_prefix = EXPECTED_WORKFLOWS[evidence_id]
        require(item.get("workflow") == workflow_name, f"{evidence_id}: workflow name drifted")
        require(item.get("workflowPath") == workflow_path, f"{evidence_id}: workflow path drifted")
        require(item.get("artifactNamePrefix") == artifact_prefix, f"{evidence_id}: artifact prefix drifted")
        require(item.get("required") is True, f"{evidence_id}: review evidence became optional")
        workflow_paths.append(ROOT / workflow_path)

    human = contract.get("humanReview", {})
    require(human == {
        "required": True,
        "status": "pending",
        "finalAuthority": True,
        "acceptedRevision": None,
        "reviewedAt": None,
        "reviewer": None,
    }, "human-review state must remain pending and authoritative")

    rules = contract.get("rules", {})
    for key in (
        "allReviewArtifactsMustResolveToOneExactCandidateRevision",
        "artifactAssemblyMayNotSetHumanReviewComplete",
        "machineEvidenceMayNotSubstituteHumanOpticalAcceptance",
        "humanReviewMayNotPromoteLifecycleByItself",
        "stableV11AuthorityMayNotMove",
        "consumerClaimBlocked",
    ):
        require(rules.get(key) is True, f"review-packet safety rule weakened: {key}")

    require(contract.get("requiredOutputClaims") == EXPECTED_CLAIMS,
            "review-packet fail-closed output claims drifted")
    require(len(contract.get("reviewDimensions", [])) == 9, "human review dimension set drifted")

    implementation = contract.get("implementation", {})
    require(implementation == {
        "guide": "acceptance/v1.2-human-optical-review-packet.candidate.md",
        "validator": "scripts/validate_glaze_v1_2_human_optical_review_packet.py",
        "manifestArtifact": "artifacts/glaze-v1.2-human-optical-review-manifest.json",
        "orchestratingWorkflow": ".github/workflows/glaze-v1.2-exact-head-readiness.yml",
    }, "review-packet implementation binding drifted")

    boundary = contract.get("evidenceBoundary", {})
    for marker in (
        "human-collision-review",
        "human-optical-acceptance",
        "human-approved-v1.2-canonical-screenshot-baseline",
        "phase5-reference-scenes-complete",
        "release-candidate",
        "stable",
        "production-acceptance",
        "consumer-conformance",
    ):
        require(marker in boundary.get("notEstablished", []), f"fail-closed review boundary missing: {marker}")

    sources = [CONTRACT, GUIDE, VISUAL, ICON_WALL, REFERENCE_SCENES, READINESS, LIFECYCLE, VERSION, *workflow_paths]
    for path in sources:
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    return contract, sources


def validate_authority_boundaries() -> None:
    lifecycle = load_json(LIFECYCLE)
    require(VERSION.read_text(encoding="utf-8").strip() == "1.1.0", "VERSION moved away from Stable 1.1.0")
    require(lifecycle.get("currentStable") == "1.1.0" and lifecycle.get("currentOfficial") == "1.1.0",
            "Stable lifecycle authority moved")
    require(lifecycle.get("activeCandidate") == "1.2.0-candidate", "active Candidate identity drifted")

    visual = load_json(VISUAL)
    provisional = visual.get("provisionalReference", {})
    require(provisional.get("humanApproved") is False, "provisional visual evidence became human approved")
    require(provisional.get("canonicalScreenshotBaseline") is False, "provisional visual evidence became canonical")
    require(provisional.get("acceptanceAuthority") is False, "provisional visual evidence gained acceptance authority")
    require(visual.get("comparison", {}).get("humanOpticalReviewRemainsAuthoritative") is True,
            "human optical authority drifted")

    wall = load_json(ICON_WALL)
    require(wall.get("humanReview") == {
        "required": True,
        "status": "pending",
        "finalAuthority": True,
        "acceptedRevision": None,
        "reviewedAt": None,
    }, "application icon wall human review must remain pending")

    scenes = load_json(REFERENCE_SCENES)
    require(scenes.get("phase5ReferenceScenesComplete") is False, "Reference Scenes unexpectedly completed")
    require(scenes.get("openSceneIds") == ["application-icon-ecosystem-wall"],
            "Reference Scene open set drifted")

    readiness = load_json(READINESS)
    claims = readiness.get("requiredOutputClaims", {})
    for key in ("promotionReady", "rcReady", "stableReady", "productionReady", "consumerEligible", "consumerConformanceClaim"):
        require(claims.get(key) is False, f"readiness claim overpromoted: {key}")


def validate_workflows(contract: dict[str, Any]) -> None:
    for item in contract["evidenceClasses"]:
        evidence_id = item["id"]
        path = ROOT / item["workflowPath"]
        text = path.read_text(encoding="utf-8")
        require(f"name: {item['workflow']}" in text, f"{evidence_id}: workflow identity drifted")
        require("actions/upload-artifact@" in text, f"{evidence_id}: workflow does not publish evidence")
        require(item["artifactNamePrefix"] in text, f"{evidence_id}: workflow artifact prefix missing")
        require("github.event.pull_request.head.sha || github.sha" in text,
                f"{evidence_id}: exact Candidate revision expression missing")

    visual_text = (ROOT / EXPECTED_WORKFLOWS["provisional-visual-regression"][1]).read_text(encoding="utf-8")
    require("path: artifacts/visual-regression/" in visual_text, "visual-regression screenshots are not uploaded")

    wall_text = (ROOT / EXPECTED_WORKFLOWS["application-icon-ecosystem-wall"][1]).read_text(encoding="utf-8")
    for marker in (
        "contracts/v1.2/application-icon-ecosystem-wall.candidate.json",
        "reference/v1.2/application-icon-ecosystem-wall.html",
        ".branding-sources/goreecloud-branding-assets/catalog.json",
        ".branding-sources/goreecloud-branding-assets/products/*/app-icon.svg",
    ):
        require(marker in wall_text, f"application icon review artifact path missing: {marker}")

    scenes_text = (ROOT / EXPECTED_WORKFLOWS["reference-scene-index"][1]).read_text(encoding="utf-8")
    for marker in (
        "contracts/v1.2/reference-scenes.candidate.json",
        "reference/v1.2/",
    ):
        require(marker in scenes_text, f"reference-scene review artifact path missing: {marker}")

    readiness_text = (ROOT / EXPECTED_WORKFLOWS["exact-head-readiness"][1]).read_text(encoding="utf-8")
    for marker in (
        "validate_glaze_v1_2_human_optical_review_packet.py",
        "artifacts/glaze-v1.2-human-optical-review-manifest.json",
    ):
        require(marker in readiness_text, f"exact-head review orchestration missing: {marker}")


def build_manifest(contract: dict[str, Any], sources: list[Path]) -> dict[str, Any]:
    revision = head_revision()
    evidence = []
    for item in contract["evidenceClasses"]:
        evidence.append({
            "id": item["id"],
            "workflow": item["workflow"],
            "workflowPath": item["workflowPath"],
            "artifactNamePrefix": item["artifactNamePrefix"],
            "kind": item["kind"],
            "required": True,
            "requiredRevision": revision,
            "revisionRule": "workflow run head_sha and reviewed artifact provenance must equal requiredRevision",
        })

    return {
        "schemaVersion": 1,
        "id": "glaze-v1.2-human-optical-review-manifest",
        "product": "GLAZE UI",
        "version": "1.2.0-candidate",
        "lifecycle": "candidate",
        "stableBaseline": "1.1.0",
        "revision": revision,
        "reviewStatus": "pending",
        "humanReviewRequired": True,
        "humanReviewComplete": False,
        "promotionEligible": False,
        "consumerEligible": False,
        "evidenceClasses": evidence,
        "reviewDimensions": contract["reviewDimensions"],
        "sourceDigests": {
            str(path.relative_to(ROOT)): f"sha256:{sha256(path)}"
            for path in sources
        },
        "claims": dict(EXPECTED_CLAIMS),
        "boundary": "Machine-assembled exact-revision review handoff only; human optical/collision acceptance, RC, Stable, production acceptance, and consumer conformance remain unestablished.",
    }


def main() -> int:
    try:
        contract, sources = validate_contract()
        validate_authority_boundaries()
        validate_workflows(contract)
        manifest = build_manifest(contract, sources)
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except (ReviewPacketError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}")
        return 1
    print(
        "PASS: V1.2 human optical review handoff is exact-revision-bound and fail closed; "
        "human review remains pending and authoritative."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
