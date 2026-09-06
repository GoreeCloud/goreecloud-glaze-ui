#!/usr/bin/env python3
"""Fail-closed validator for the GLAZE UI V1.1.1 corrective Stable release."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.1.1"
BASE_STABLE = "1.1.0"
PATCH_RC = "1.1.1-rc.1"
PRODUCT = "GLAZE UI V1.1"
SELECTED_MERGED_REVISION = "1af31aa69a40e740cfcaaca7fd5eee340da98c22"
POST_MERGE_QUALIFICATION_RUN = 34034770603


def load(path: str):
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(
        (ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION,
        "VERSION must be 1.1.1",
    )

    lifecycle = load("registry/lifecycle.json")
    require(
        lifecycle.get("officialProductLabel") == PRODUCT,
        "lifecycle official product must remain GLAZE UI V1.1",
    )
    require(
        lifecycle.get("currentOfficial") == VERSION,
        "lifecycle currentOfficial must be 1.1.1",
    )
    require(
        lifecycle.get("currentStable") == VERSION,
        "lifecycle currentStable must be 1.1.1",
    )
    require(
        lifecycle.get("activePatchReleaseCandidate") is None,
        "no patch Release Candidate may remain active after 1.1.1 Stable promotion",
    )
    require(
        lifecycle.get("activeCandidate") == "1.2.0-candidate",
        "V1.2 must remain the separate next-version Candidate",
    )

    releases = {
        item.get("version"): item
        for item in lifecycle.get("releases", [])
        if isinstance(item, dict) and item.get("version")
    }
    base_release = releases.get(BASE_STABLE, {})
    patch_rc = releases.get(PATCH_RC, {})
    stable_release = releases.get(VERSION, {})
    require(
        base_release.get("status") == "historical-stable"
        and base_release.get("consumerEligible") is False,
        "1.1.0 must remain historical immutable Stable evidence and not current consumer authority",
    )
    require(
        patch_rc.get("status") == "historical-release-candidate"
        and patch_rc.get("consumerEligible") is False,
        "1.1.1-rc.1 must remain historical non-consumer Release Candidate evidence",
    )
    require(
        stable_release.get("status") == "stable"
        and stable_release.get("consumerEligible") is True,
        "lifecycle must contain consumer-adoptable Stable 1.1.1",
    )
    require(
        stable_release.get("previousStable") == BASE_STABLE,
        "1.1.1 must identify 1.1.0 as its previous Stable",
    )
    require(
        stable_release.get("acceptance") == "acceptance/v1.1.1-stable.md",
        "1.1.1 lifecycle acceptance binding drifted",
    )

    for path in (
        "GLAZE_UI_V1_1.md",
        "css/glaze-v1.1.css",
        "css/glaze-v1.1-appearance.css",
        "css/glaze-v1.1.1.css",
        "js/glaze-v1.1.1.mjs",
        "acceptance/v1.1.1-stable.md",
        "contracts/v1.1/release.json",
        "contracts/v1.1/release-1.1.0.json",
        "contracts/v1.1/patch-1.1.1-candidate.json",
        "acceptance/v1.1.1-patch-candidate.md",
    ):
        require((ROOT / path).is_file(), f"missing V1.1.1 Stable authority artifact: {path}")

    # Optical semantics and approved pixels are inherited unchanged from 1.1.0.
    optical = load("contracts/v1.1/optical-refinement.json")
    require(
        optical.get("product") == PRODUCT
        and optical.get("version") == BASE_STABLE
        and optical.get("lifecycle") == "stable",
        "1.1.1 must inherit the approved 1.1.0 optical contract without relabeling it",
    )
    boundary = optical.get("releaseBoundary", {})
    require(
        boundary.get("downstreamConsumerConformanceAutomatic") is False,
        "Stable design-system release must not auto-conform consumers",
    )

    atmosphere = load("tokens/glaze-v1.1-atmosphere.json")
    require(
        atmosphere.get("product") == PRODUCT
        and atmosphere.get("version") == BASE_STABLE
        and atmosphere.get("lifecycle") == "stable",
        "1.1.1 must inherit the approved 1.1.0 atmosphere contract without relabeling it",
    )
    require(
        atmosphere.get("semanticPrecedence", {}).get("atmosphereIsLowestPriority") is True,
        "atmosphere must remain lower priority than protected semantic meaning",
    )

    entry = (ROOT / "css/glaze-v1.1.1.css").read_text(encoding="utf-8")
    for marker in (
        '@import url("./glaze-v1.0.0.css")',
        '@import url("./glaze-v1.1.css")',
        '@import url("./glaze-v1.1-appearance.css")',
    ):
        require(marker in entry, f"Stable 1.1.1 web entrypoint missing {marker}")
    require(
        "1.1.1" in entry,
        "Stable web entrypoint must identify the 1.1.1 patch release",
    )

    components = (ROOT / "css/glaze-v1.components.css").read_text(encoding="utf-8")
    require(
        '@import url("./glaze-v1.candidate.css")' not in components,
        "corrected Stable graph must not restore the stale Candidate import",
    )

    runtime = (ROOT / "js/glaze-v1.1.1.mjs").read_text(encoding="utf-8")
    require(
        'export * from "./glaze-v1.runtime.mjs"' in runtime,
        "Stable 1.1.1 runtime must preserve V1 runtime export",
    )
    require(
        'export * from "./glaze-v1.system-interactions.mjs"' in runtime,
        "Stable 1.1.1 runtime must preserve V1 system interaction export",
    )

    baseline = load("contracts/regression/visual-baselines-v1.json")
    require(
        baseline.get("product") == PRODUCT
        and baseline.get("version") == BASE_STABLE
        and baseline.get("status") == "stable-human-approved-source-pinned",
        "1.1.1 must inherit the source-pinned approved 1.1.0 visual baseline",
    )
    require(
        len(baseline.get("cases", {})) == 5,
        "V1.1 visual baseline must retain five approved cases",
    )

    release = load("contracts/v1.1/release.json")
    require(
        release.get("product") == PRODUCT and release.get("version") == VERSION,
        "current release metadata must identify GLAZE UI V1.1 / 1.1.1",
    )
    require(
        release.get("baseStableVersion") == BASE_STABLE,
        "1.1.1 release metadata must preserve the 1.1.0 base",
    )
    require(
        release.get("patchReleaseCandidate") == PATCH_RC,
        "1.1.1 release metadata must bind the qualified patch RC",
    )
    require(
        release.get("selectedMergedRevision") == SELECTED_MERGED_REVISION,
        "selected merged revision drifted",
    )
    require(
        release.get("postMergeQualification", {}).get("workflowRun")
        == POST_MERGE_QUALIFICATION_RUN,
        "post-merge qualification run drifted",
    )
    require(
        release.get("repair", {}).get("intentionalVisualChange") is False,
        "import-closure patch must not claim an intentional optical change",
    )
    finalization = release.get("finalization", {})
    require(
        finalization.get("immutableTagRequired") == "v1.1.1",
        "1.1.1 release metadata must require a new immutable v1.1.1 tag",
    )
    require(
        finalization.get("githubReleaseRequired") == "v1.1.1",
        "1.1.1 release metadata must require a new GitHub Release",
    )

    consumers = load("consumers/registry.json")
    require(
        consumers.get("officialBaseline") == VERSION
        and consumers.get("requiredConsumerVersion") == VERSION,
        "consumer registry must require current Stable 1.1.1",
    )
    require(
        all(
            item.get("requiredTargetVersion") == VERSION
            for item in consumers.get("consumers", [])
        ),
        "every listed consumer must require 1.1.1",
    )
    require(
        not any(
            item.get("productionEligible") is True
            for item in consumers.get("consumers", [])
        ),
        "Glaze promotion must not auto-mark downstream consumers production eligible",
    )

    evidence_schema = load("contracts/glaze.conformance-evidence.schema.json")
    target = evidence_schema.get("properties", {}).get("target", {}).get("properties", {})
    require(
        target.get("glaze_version", {}).get("const") == VERSION,
        "conformance evidence schema must target 1.1.1",
    )

    token_manifest = load("tokens/glaze-v1.json")
    require(
        token_manifest.get("product") == PRODUCT
        and token_manifest.get("version") == VERSION
        and token_manifest.get("status") == "stable",
        "current V1 token manifest must identify Stable 1.1.1",
    )

    v12_tokens = load("tokens/glaze-v1.2-frosted-neutral.candidate.json")
    require(
        v12_tokens.get("lifecycle") == "candidate"
        and v12_tokens.get("stableBaseline") == VERSION,
        "V1.2 Candidate must remain Candidate while rebasing its Stable baseline to 1.1.1",
    )
    v12_release = releases.get("1.2.0-candidate", {})
    require(
        v12_release.get("status") == "candidate"
        and v12_release.get("consumerEligible") is False
        and v12_release.get("stableBaseline") == VERSION,
        "V1.2 lifecycle must remain Candidate against the new 1.1.1 Stable baseline",
    )

    docs = {
        "README.md": (PRODUCT, VERSION, "current Stable"),
        "SPECIFICATIONS.md": (PRODUCT, VERSION, "Stable"),
        "BRANDING.md": (PRODUCT, VERSION, "Stable"),
        "ACCEPTANCE.md": (PRODUCT, VERSION, "Stable"),
        "GLAZE_UI_V1_1.md": (PRODUCT, VERSION, "Stable"),
        "CONSUMERS.md": (PRODUCT, VERSION),
        "website/index.html": (PRODUCT, VERSION, "current Stable"),
        "website/404.html": (PRODUCT, VERSION),
    }
    for path, markers in docs.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        for marker in markers:
            require(marker in text, f"{path} missing current 1.1.1 marker {marker!r}")

    require(
        (ROOT / "acceptance/v1.1-stable.md").is_file(),
        "historical 1.1.0 Stable acceptance must remain available for audit",
    )
    require(
        (ROOT / "contracts/v1.1/patch-1.1.1-candidate.json").is_file(),
        "patch Release Candidate contract must remain historical audit evidence",
    )

    if errors:
        print("GLAZE UI V1.1.1 Stable source validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.1.1 corrective Stable source authority: PASS")
    print(
        "Boundary: 1.1.1 corrects Stable import closure without new optical semantics; "
        "downstream consumers must re-pin and revalidate independently."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
