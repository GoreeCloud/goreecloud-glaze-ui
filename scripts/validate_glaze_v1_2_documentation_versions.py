#!/usr/bin/env python3
"""Audit current lifecycle/version authority while preserving retained V1.2 history.

This validator originated while V1.2 was globally current. It now serves as a
retained-release integrity check: live current authority is derived from
`registry/lifecycle.json`/`VERSION`, while prior release documentation and
source remain historical Stable provenance. It must never move global authority
back to an older release.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / "registry" / "lifecycle.json"
VERSION = ROOT / "VERSION"

CURRENT_AUTHORITY_DOCS = {
    "README.md": ("current Official", "Stable"),
    "CONTRIBUTING.md": ("Stable",),
    "CONFORMANCE.md": ("conformance",),
    "ACCEPTANCE.md": ("Stable",),
    "ADOPTION.md": ("adoption",),
    "ENFORCEMENT.md": ("consumer",),
    "website/README.md": ("Stable",),
    "ICON_CONSTRUCTION.md": ("Stable",),
    "ICON_IDENTITY.md": ("Stable",),
}

RETAINED_V12_DOCS = (
    "GLAZE_UI_V1_2.md",
    "GLAZE_UI_V1_2_CANDIDATE.md",
    "MIGRATION_V1_1_TO_V1_2.md",
    "acceptance/v1.2-stable.md",
)

# These are release snapshots, migration records, acceptance records, or
# explicitly retained validators. Their "current" wording describes the
# authority at the time of the recorded release and must not be reinterpreted as
# live authority after later governed promotions.
HISTORICAL_SOURCE_PATHS = {
    "GLAZE_UI_V1_1.md",
    "GLAZE_UI_V1_3.md",
    "GLAZE_UI_V1_3_1_HARDENING.md",
    "GLAZE_UI_V1_4_1.md",
    "GLAZE_UI_V1_5_DEVELOPMENT.md",
    "MIGRATION_V1_2_TO_V1_3.md",
    "acceptance/v1.1-rendered-web-evidence.json",
    "acceptance/v1.1-stable.md",
    "acceptance/v1.3-deferred-qualification.md",
    "acceptance/v1.3-stable.md",
    "scripts/glaze_v1_2_promoted_source_runner.py",
    "scripts/promote_glaze_v1_1_stable.py",
    "scripts/validate_evidence_presentation.py",
    "scripts/validate_glaze_motion.py",
    "scripts/validate_glaze_v1_0_reset.py",
    "scripts/validate_glaze_v1_2_candidate_legacy.py",
    "scripts/validate_glaze_v1_2_contract_namespace_legacy.py",
    "scripts/validate_glaze_v1_2_core_tokens_legacy.py",
    "scripts/validate_glaze_v1_2_form_factor_tokens_legacy.py",
    "scripts/validate_glaze_v1_2_living_glaze_legacy.py",
    "scripts/validate_glaze_v1_2_file_naming_legacy.py",
    "scripts/validate_glaze_v1_2_source_inventory_legacy.py",
    "scripts/validate_glaze_v1_2_migration_legacy.py",
}

HISTORICAL_QUALIFIERS = (
    "historical", "at the time", "at publication", "then-current", "superseded",
    "not current", "does not define the current", "does not override the current",
    "was current", "was the current", "previous stable", "prior stable", "rollback",
    "retained", "provenance", "formerly current",
)
STRONG_CURRENT_CLAIMS = (
    "sole current", "current official target", "current stable", "current product identity",
    "current product version", "current product baseline", "current application target",
    "current adoption target", "current conformance target", "current target",
    "all current glaze ui work targets",
)
SEMVER = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?:-[0-9a-z.-]+)?(?!\d)", re.I)


def fail(message: str) -> None:
    raise SystemExit(f"lifecycle-version-integrity: {message}")


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        fail(f"required file missing: {relative}")
    return path.read_text(encoding="utf-8")


def tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    return sorted(part.decode("utf-8") for part in result.stdout.split(b"\0") if part)


def tracked_text_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    for relative in tracked_files():
        path = ROOT / relative
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        try:
            sources[relative] = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
    return sources


def release_for(lifecycle: dict[str, Any], version: str) -> dict[str, Any]:
    for release in lifecycle.get("releases", []):
        if isinstance(release, dict) and release.get("version") == version:
            return release
    fail(f"lifecycle release record missing for {version}")
    raise AssertionError("unreachable")


def version_tuple(value: str) -> tuple[int, int, int] | None:
    match = SEMVER.search(value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def current_family_prefix(value: str) -> str | None:
    """Return the family-level Glaze product-label prefix for a release version."""
    match = SEMVER.fullmatch(value)
    if not match:
        return None
    return f"GLAZE UI V{match.group(1)}.{match.group(2)}"


def historical_record(relative: str, text: str, current_version: str) -> bool:
    """Return whether a tracked source is explicitly retained/provenance-only."""
    if relative in HISTORICAL_SOURCE_PATHS or relative in RETAINED_V12_DOCS:
        return True

    lowered_path = relative.lower()
    name = Path(relative).name.lower()
    if name.endswith("_legacy.py") or name.endswith("-legacy.py"):
        return True
    if "candidate" in name or ".candidate." in lowered_path or "release-candidate" in lowered_path:
        return True
    if relative.startswith("acceptance/v1.") or relative.startswith("releases/1."):
        # Versioned acceptance/release records are provenance. Live authority is
        # checked independently through current front-door documents.
        return True
    if relative.startswith(("contracts/v1.0/", "contracts/v1.1/", "contracts/v1.2/", "contracts/v1.3/")):
        return True
    if relative.startswith(("reference/v1.0/", "reference/v1.1/", "reference/v1.2/", "reference/v1.3/")):
        return True
    if relative.startswith("scripts/validate_glaze_v1_") and not relative.startswith("scripts/validate_glaze_v1_4"):
        return True

    preamble = text[:1800].lower()
    return any(marker in preamble for marker in ("historical record", "historical status", "superseded", "retained stable"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
    version = VERSION.read_text(encoding="utf-8").strip()
    current_official = lifecycle.get("currentOfficial")
    current_stable = lifecycle.get("currentStable")
    active_candidate = lifecycle.get("activeCandidate")
    planned_next = lifecycle.get("plannedNext")

    if not isinstance(current_stable, str) or not current_stable:
        fail("currentStable must identify a live release")
    if version != current_stable or current_official != current_stable:
        fail("VERSION/currentStable/currentOfficial must agree on the live current Stable release")

    current_release = release_for(lifecycle, current_stable)
    if current_release.get("status") != "stable" or current_release.get("consumerEligible") is not True:
        fail("live currentStable release must be Stable and consumer-eligible")
    stable_label = current_release.get("label")
    if not isinstance(stable_label, str) or not stable_label:
        fail("live current Stable release label is missing")

    family_prefix = current_family_prefix(current_stable)
    official_product_label = lifecycle.get("officialProductLabel")
    if family_prefix is None:
        fail("currentStable must be a semantic release version")
    if (
        not isinstance(official_product_label, str)
        or not official_product_label.strip()
        or not official_product_label.startswith(family_prefix)
    ):
        fail("officialProductLabel must identify the live current Stable product family")

    retained_v12 = release_for(lifecycle, "1.2.0")
    if retained_v12.get("status") != "stable" or retained_v12.get("consumerEligible") is not True:
        fail("retained V1.2 release must remain an intact Stable release record")
    if retained_v12.get("stableBaseline") != "1.1.0":
        fail("retained V1.2 rollback baseline must remain 1.1.0")
    anchor = retained_v12.get("sourceQualificationAnchor")
    if not isinstance(anchor, str) or re.fullmatch(r"[0-9a-f]{40}", anchor) is None:
        fail("retained V1.2 sourceQualificationAnchor must remain a 40-character commit SHA")

    for relative, required_phrases in CURRENT_AUTHORITY_DOCS.items():
        text = read_text(relative)
        if current_stable not in text and stable_label not in text:
            fail(f"{relative} does not identify live current Stable authority {current_stable}")
        for phrase in required_phrases:
            if phrase.lower() not in text.lower():
                fail(f"{relative} missing lifecycle phrase {phrase!r}")

    for relative in RETAINED_V12_DOCS:
        text = read_text(relative)
        if "1.2.0" not in text and "GLAZE UI V1.2" not in text:
            fail(f"retained V1.2 provenance file lost its V1.2 identity: {relative}")

    sources = tracked_text_sources()
    stale_findings: list[dict[str, Any]] = []
    current_tuple = version_tuple(current_stable)
    for relative, text in sources.items():
        if relative == "scripts/validate_glaze_v1_2_documentation_versions.py":
            continue
        is_history = historical_record(relative, text, current_stable)
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if not any(claim in lowered for claim in STRONG_CURRENT_CLAIMS):
                continue
            if is_history or any(qualifier in lowered for qualifier in HISTORICAL_QUALIFIERS):
                continue
            versions = [version_tuple(match.group(0)) for match in SEMVER.finditer(line)]
            older_versions = [item for item in versions if item and current_tuple and item < current_tuple]
            if not older_versions:
                continue
            stale_findings.append({"path": relative, "line": line_number, "text": line.strip()[:240]})

    if stale_findings:
        preview = "; ".join(f"{item['path']}:{item['line']} {item['text']}" for item in stale_findings[:20])
        fail(f"obsolete current-authority language found: {preview}")

    report = {
        "schemaVersion": 9,
        "status": "pass",
        "currentOfficial": current_official,
        "currentStable": current_stable,
        "currentStableLabel": stable_label,
        "officialProductLabel": official_product_label,
        "activeCandidate": active_candidate,
        "plannedNext": planned_next,
        "retainedV12Status": retained_v12.get("status"),
        "retainedV12SourceQualificationAnchor": anchor,
        "auditedTrackedUtf8TextFiles": len(sources),
        "currentAuthorityDocuments": sorted(CURRENT_AUTHORITY_DOCS),
        "retainedV12Documents": list(RETAINED_V12_DOCS),
        "historicalSourcePaths": sorted(HISTORICAL_SOURCE_PATHS),
        "obsoleteLifecycleAuthorityFindings": 0,
        "scopeRule": "Live authority is derived from current lifecycle/VERSION state and a family-level officialProductLabel. Retained earlier Stable/release records are provenance and may not override the current Stable release.",
        "promotionRule": "This retained-release documentation audit does not promote V1.2, V1.4.1, or any other lifecycle state.",
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
