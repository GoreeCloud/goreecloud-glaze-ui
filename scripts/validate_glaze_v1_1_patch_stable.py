#!/usr/bin/env python3
"""Fail-closed validator for the GLAZE UI V1.1.1 maintenance Stable package."""
from __future__ import annotations

import json
from pathlib import Path

from validate_css_import_closure import CSS_ROOT, ENTRYPOINT, validate_import_closure

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.1.1"
PRODUCT = "GLAZE UI V1.1"


def load(relative: str):
    with (ROOT / relative).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require((ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION, "VERSION must be 1.1.1")

    lifecycle = load("registry/lifecycle.json")
    require(lifecycle.get("officialProductLabel") == PRODUCT, "official product label drifted")
    require(lifecycle.get("currentOfficial") == VERSION, "currentOfficial must be 1.1.1")
    require(lifecycle.get("currentStable") == VERSION, "currentStable must be 1.1.1")
    require(lifecycle.get("activePatchReleaseCandidate") is None, "patch RC must be retired after Stable promotion")
    require(lifecycle.get("activeCandidate") == "1.2.0-candidate", "V1.2 must remain the independent next-version Candidate")

    release = next((item for item in lifecycle.get("releases", []) if item.get("version") == VERSION), None)
    require(isinstance(release, dict), "Stable 1.1.1 lifecycle record missing")
    if isinstance(release, dict):
        require(release.get("status") == "stable", "1.1.1 lifecycle record must be stable")
        require(release.get("consumerEligible") is True, "current Stable package must be consumer eligible")
        require(release.get("contract") == "contracts/v1.1/patch-1.1.1.json", "Stable patch contract binding drifted")
        require(release.get("acceptance") == "acceptance/v1.1.1-stable.md", "Stable patch acceptance binding drifted")
        require(release.get("webEntrypoint") == "css/glaze-v1.1.1.css", "Stable web entrypoint binding drifted")
        require(release.get("runtimeEntrypoint") == "js/glaze-v1.1.1.mjs", "Stable runtime entrypoint binding drifted")

    previous = next((item for item in lifecycle.get("releases", []) if item.get("version") == "1.1.0"), None)
    require(isinstance(previous, dict) and previous.get("status") == "superseded-stable", "1.1.0 must remain immutable superseded Stable history")
    require(isinstance(previous, dict) and previous.get("consumerEligible") is False, "known-defective 1.1.0 package must not remain current-consumer eligible")

    patch = load("contracts/v1.1/patch-1.1.1.json")
    require(patch.get("product") == PRODUCT and patch.get("version") == VERSION, "Stable patch identity mismatch")
    require(patch.get("lifecycle") == "stable", "Stable patch lifecycle mismatch")
    require(patch.get("releaseType") == "maintenance-import-closure", "Stable patch release type mismatch")
    require(patch.get("baseStableVersion") == "1.1.0", "Stable patch baseline drifted")
    qualification = patch.get("qualification", {})
    require(qualification.get("postMergeRun") == 34034770603, "qualified post-merge evidence run drifted")
    require(qualification.get("result") == "passed", "post-merge qualification must remain passed")
    scope = patch.get("scope", {})
    for key in ("visualDesignChanged", "tokenValuesChanged", "semanticAuthorityChanged", "accessibilityContractChanged", "runtimeBehaviorChanged"):
        require(scope.get(key) is False, f"maintenance patch must not widen scope: {key}")
    require(scope.get("cssImportClosureCorrected") is True, "maintenance patch must record corrected import closure")

    for path in (
        "css/glaze-v1.1.1.css",
        "js/glaze-v1.1.1.mjs",
        "contracts/v1.1/patch-1.1.1.json",
        "acceptance/v1.1.1-stable.md",
        "css/glaze-v1.1.0.css",
        "js/glaze-v1.1.0.mjs",
        "acceptance/v1.1-stable.md",
        "contracts/regression/visual-baselines-v1.json",
    ):
        require((ROOT / path).is_file(), f"missing Stable/history artifact: {path}")

    web = (ROOT / "css/glaze-v1.1.1.css").read_text(encoding="utf-8")
    markers = (
        '@import url("./glaze-v1.0.0.css")',
        '@import url("./glaze-v1.1.css")',
        '@import url("./glaze-v1.1-appearance.css")',
    )
    for marker in markers:
        require(marker in web, f"1.1.1 web entrypoint missing {marker}")
    if all(marker in web for marker in markers):
        require(web.index(markers[0]) < web.index(markers[1]) < web.index(markers[2]), "1.1.1 web entrypoint import order drifted")

    runtime = (ROOT / "js/glaze-v1.1.1.mjs").read_text(encoding="utf-8")
    require('export * from "./glaze-v1.runtime.mjs"' in runtime, "1.1.1 runtime must preserve V1 runtime export")
    require('export * from "./glaze-v1.system-interactions.mjs"' in runtime, "1.1.1 runtime must preserve System interaction export")

    components = (ROOT / "css/glaze-v1.components.css").read_text(encoding="utf-8")
    require('@import url("./glaze-v1.candidate.css")' not in components, "stale Candidate dependency remains in current Stable component source")
    base_entry = (ROOT / "css/glaze-v1.0.0.css").read_text(encoding="utf-8")
    foundation = '@import url("./glaze-v1.foundation.css");'
    component = '@import url("./glaze-v1.components.css");'
    require(foundation in base_entry and component in base_entry, "V1 base entrypoint must load foundation and components")
    if foundation in base_entry and component in base_entry:
        require(base_entry.index(foundation) < base_entry.index(component), "foundation must load before components")

    closure_errors, visited = validate_import_closure(ENTRYPOINT, CSS_ROOT)
    errors.extend(closure_errors)
    require(len(visited) >= 3, "Stable web graph closure unexpectedly small")

    visual = load("contracts/regression/visual-baselines-v1.json")
    require(visual.get("product") == PRODUCT and visual.get("version") == "1.1.0", "maintenance patch must preserve the approved 1.1.0 visual baseline identity")
    require(visual.get("status") == "stable-human-approved-source-pinned", "visual baseline must remain human-approved and source-pinned")

    consumers = load("consumers/registry.json")
    require(consumers.get("officialBaseline") == VERSION, "consumer registry baseline must be 1.1.1")
    require(consumers.get("requiredConsumerVersion") == VERSION, "consumer registry required version must be 1.1.1")
    require(all(item.get("requiredTargetVersion") == VERSION for item in consumers.get("consumers", [])), "every registered consumer must target 1.1.1")
    require(not any(item.get("productionEligible") is True for item in consumers.get("consumers", [])), "shared Stable promotion must not auto-promote consumers")

    evidence_schema = load("contracts/glaze.conformance-evidence.schema.json")
    target = evidence_schema.get("properties", {}).get("target", {}).get("properties", {})
    require(target.get("glaze_version", {}).get("const") == VERSION, "conformance evidence must target 1.1.1")

    token_manifest = load("tokens/glaze-v1.json")
    require(token_manifest.get("product") == PRODUCT and token_manifest.get("version") == VERSION and token_manifest.get("status") == "stable", "current token manifest must identify 1.1.1 Stable package")

    candidate = next((item for item in lifecycle.get("releases", []) if item.get("version") == "1.2.0-candidate"), None)
    require(isinstance(candidate, dict) and candidate.get("status") == "candidate", "V1.2 Candidate must remain Candidate")
    require(isinstance(candidate, dict) and candidate.get("consumerEligible") is False, "V1.2 Candidate must not become consumer eligible")
    require(isinstance(candidate, dict) and candidate.get("stableBaseline") == VERSION, "V1.2 Candidate package baseline must follow current Stable 1.1.1")
    require(isinstance(candidate, dict) and candidate.get("visualBaseline") == "1.1.0", "V1.2 Candidate must preserve unchanged V1.1 visual baseline provenance")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for marker in (PRODUCT, "1.1.1", "current Stable"):
        require(marker in readme, f"README missing current Stable marker {marker!r}")

    if errors:
        print("GLAZE UI V1.1.1 Stable maintenance validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.1.1 Stable maintenance source authority: PASS")
    print("Boundary: shared design-system stability only; downstream consumers remain independently migration- and acceptance-gated. V1.2 remains Candidate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
