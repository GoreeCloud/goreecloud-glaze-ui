#!/usr/bin/env python3
"""Validate the bounded GLAZE UI V1.1.1 import-closure patch Release Candidate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from validate_css_import_closure import CSS_ROOT, ENTRYPOINT, validate_import_closure

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/v1.1/patch-1.1.1-candidate.json"
COMPONENTS = ROOT / "css/glaze-v1.components.css"
V1_ENTRY = ROOT / "css/glaze-v1.0.0.css"
LIFECYCLE = ROOT / "registry/lifecycle.json"


def main() -> int:
    errors: list[str] = []

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
    components = COMPONENTS.read_text(encoding="utf-8")
    entry = V1_ENTRY.read_text(encoding="utf-8")

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    candidate_version = contract.get("candidateVersion")
    require(candidate_version == "1.1.1-rc.1", "patch candidate must be 1.1.1-rc.1")
    require(contract.get("lifecycle") == "release-candidate", "patch lifecycle must be release-candidate")
    require(contract.get("intendedStableVersion") == "1.1.1", "intended patch Stable version must be 1.1.1")
    require(contract.get("baseStableVersion") == "1.1.0", "patch must remain based on Stable 1.1.0")
    require(contract.get("baseStableRevision") == "15cc76d2bcd4065552dc31c77145b63f34d9e7b2", "base Stable revision drifted")
    require(contract.get("currentAuthorityUnchanged") is True, "patch candidate must not claim current Stable authority changed")

    # The next-version Candidate and the Stable-line patch RC are independent lifecycle tracks.
    require(lifecycle.get("activeCandidate") == "1.2.0-candidate", "next-version activeCandidate must remain V1.2 Candidate")
    require(lifecycle.get("activePatchReleaseCandidate") == candidate_version, "activePatchReleaseCandidate must match the V1.1.1 patch RC")
    require(lifecycle.get("currentStable") == "1.1.0", "current Stable must remain 1.1.0 while the patch is a Release Candidate")
    require(lifecycle.get("currentOfficial") == "1.1.0", "current official version must remain 1.1.0 while the patch is a Release Candidate")

    patch_release = next(
        (
            item
            for item in lifecycle.get("releases", [])
            if isinstance(item, dict) and item.get("version") == candidate_version
        ),
        None,
    )
    require(patch_release is not None, "patch Release Candidate lifecycle record missing")
    if isinstance(patch_release, dict):
        require(patch_release.get("status") == "release-candidate", "patch lifecycle record must remain release-candidate")
        require(patch_release.get("consumerEligible") is False, "patch Release Candidate must not be consumer eligible")
        require(patch_release.get("stableBaseline") == "1.1.0", "patch lifecycle Stable baseline drifted")
        require(patch_release.get("contract") == "contracts/v1.1/patch-1.1.1-candidate.json", "patch lifecycle contract binding drifted")
        require(patch_release.get("acceptance") == "acceptance/v1.1.1-patch-candidate.md", "patch lifecycle acceptance binding drifted")

    require('@import url("./glaze-v1.candidate.css")' not in components, "stale Candidate dependency remains")

    checkpoint = contract.get("qualificationCheckpoint", {})
    require(checkpoint.get("revision") == "874f8542ba60d37d2b847fd547a0b976e788bbab", "qualification checkpoint revision drifted")
    require(checkpoint.get("result") == "passed", "qualification checkpoint must record a passed source checkpoint")
    require(checkpoint.get("releaseEvidenceRun") == 33887608407, "release-evidence checkpoint run drifted")
    require(checkpoint.get("webArtifact", {}).get("digest") == "sha256:3bd135b77cce0379e58b5b3c3eb80b0c0ff63d0ab786edd056f46039fb66a12e", "web evidence checkpoint digest drifted")
    require(checkpoint.get("androidArtifact", {}).get("digest") == "sha256:a4e73879871369340c881f4694a503c28f32ec063d1f03549c64cdef9fff019c", "Android evidence checkpoint digest drifted")

    foundation = '@import url("./glaze-v1.foundation.css");'
    component = '@import url("./glaze-v1.components.css");'
    require(foundation in entry and component in entry, "official V1 entrypoint must load foundation and components")
    if foundation in entry and component in entry:
        require(entry.index(foundation) < entry.index(component), "foundation must load before components")

    closure_errors, visited = validate_import_closure(ENTRYPOINT, CSS_ROOT)
    errors.extend(closure_errors)
    require(len(visited) >= 3, "Stable web graph closure unexpectedly small")

    if errors:
        print("GLAZE UI V1.1.1 patch-candidate validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.1.1 patch Release Candidate: PASS")
    print("Boundary: V1.1.1-rc.1 is the active Stable-line patch RC; V1.2 remains the separate next-version Candidate; current Stable/current official authority remain immutable 1.1.0 until separate patch release finalization.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
