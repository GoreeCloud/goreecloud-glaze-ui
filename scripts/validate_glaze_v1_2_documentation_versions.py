#!/usr/bin/env python3
"""Audit current V1.3 lifecycle/version language and retained V1.2 history."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / "registry" / "lifecycle.json"
VERSION = ROOT / "VERSION"
CURRENT_VERSION = "1.3.0"
PREVIOUS_STABLE = "1.2.0"
OLDER_STABLE = "1.1.0"
CURRENT_LABEL = "GLAZE UI V1.3 — Adaptive Resonance"

CURRENT_AUTHORITY_DOCS = {
    "README.md": ("current Official, Stable",),
    "CONTRIBUTING.md": ("current Official, Stable", "V1.3.1"),
    "GLAZE_UI_V1_3.md": ("Stable",),
    "CONFORMANCE.md": ("current Stable", "conformance target"),
    "ACCEPTANCE.md": ("current Official, Stable",),
    "ADOPTION.md": ("current Glaze UI adoption target",),
    "ENFORCEMENT.md": ("current Glaze UI enforcement",),
    "CONSUMERS.md": ("required target",),
    "website/README.md": ("current Stable",),
    "ICON_CONSTRUCTION.md": ("Current Stable product authority",),
    "ICON_IDENTITY.md": ("Current Stable product authority",),
}

HISTORICAL_DOCS = (
    "GLAZE_UI_V1_0.md",
    "GLAZE_UI_V1_1.md",
    "GLAZE_UI_V1_1_CANDIDATE.md",
    "GLAZE_UI_V1_2.md",
    "GLAZE_UI_V1_2_CANDIDATE.md",
    "MIGRATION_V1_1_TO_V1_2.md",
    "releases/1.0.0.md",
    "acceptance/v1.1-release-candidate.md",
    "acceptance/v1.1-specification-candidate.md",
)

HISTORICAL_SOURCE_PATHS = {
    "acceptance/v1.1-rendered-web-evidence.json",
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

HISTORICAL_PREPROMOTION_VALIDATORS = {
    "validate_glaze_v1_2_android_accessibility_source.py",
    "validate_glaze_v1_2_assistive_technology_qualification.py",
    "validate_glaze_v1_2_device_performance_qualification.py",
    "validate_glaze_v1_2_exact_head_readiness.py",
    "validate_glaze_v1_2_human_optical_review_packet.py",
    "validate_glaze_v1_2_human_optical_review_record.py",
    "validate_glaze_v1_2_linux_window_adaptation_source.py",
    "validate_glaze_v1_2_living_glaze_rendered.py",
    "validate_glaze_v1_2_native_optical.py",
    "validate_glaze_v1_2_native_personalization_source.py",
    "validate_glaze_v1_2_personalization_appearance_rendered.py",
    "validate_glaze_v1_2_personalization_readiness.py",
    "validate_glaze_v1_2_release_promotion.py",
}

HISTORICAL_QUALIFIERS = (
    "historical",
    "at the time",
    "at publication",
    "then-current",
    "superseded",
    "not current",
    "does not define the current",
    "does not override the current",
    "was current",
    "was the current",
    "previous stable",
    "prior stable",
    "rollback",
    "retained",
    "preceding",
)
STRONG_CURRENT_CLAIMS = (
    "sole current",
    "current official target",
    "current stable",
    "current product identity",
    "current product version",
    "current product baseline",
    "current application target",
    "current adoption target",
    "current conformance target",
    "current target",
    "all current glaze ui work targets",
    "currentstable",
    "currentofficial",
    "officialproductlabel",
)


def fail(message: str) -> None:
    raise SystemExit(f"lifecycle-version-integrity: {message}")


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        fail(f"required file missing: {relative}")
    return path.read_text(encoding="utf-8")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
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


def historical_record(relative: str, text: str) -> bool:
    """Return whether a tracked source is explicitly historical/provenance-only."""
    if relative in HISTORICAL_DOCS or relative in HISTORICAL_SOURCE_PATHS:
        return True

    path = Path(relative)
    lowered = relative.lower()
    name = path.name.lower()

    if relative.startswith("acceptance/v1.1") or relative.startswith("contracts/v1.1/"):
        return True
    if relative.startswith("acceptance/v1.2") or relative.startswith("contracts/v1.2/"):
        return True
    if relative.startswith("releases/1.1") or relative.startswith("reference/v1.1/"):
        return True
    if relative.startswith("reference/v1.2/"):
        return True
    if relative.startswith("scripts/") and name in HISTORICAL_PREPROMOTION_VALIDATORS:
        return True
    if "candidate" in name or ".candidate." in lowered or "release-candidate" in lowered:
        return True
    if name.endswith("_legacy.py") or name.endswith("-legacy.py"):
        return True

    preamble = text[:1600].lower()
    return (
        "historical record" in preamble
        or "historical status" in preamble
        or "historical stable" in preamble
        or "superseded" in preamble
        or "retained rollback" in preamble
    )


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

    if (
        current_stable != CURRENT_VERSION
        or current_official != CURRENT_VERSION
        or version != CURRENT_VERSION
    ):
        fail("VERSION/currentStable/currentOfficial must agree on V1.3 Stable / 1.3.0")
    if lifecycle.get("officialProductLabel") != CURRENT_LABEL:
        fail("officialProductLabel must identify GLAZE UI V1.3 — Adaptive Resonance")
    if active_candidate is not None:
        fail("V1.3 Stable authority must not retain an active Candidate")
    if planned_next != "1.3.1-candidate":
        fail("plannedNext must identify the V1.3.1 follow-up Candidate line")

    current_release = release_for(lifecycle, CURRENT_VERSION)
    previous_release = release_for(lifecycle, PREVIOUS_STABLE)
    older_release = release_for(lifecycle, OLDER_STABLE)
    if current_release.get("status") != "stable" or current_release.get("consumerEligible") is not True:
        fail("V1.3 must remain Stable and consumer-eligible at the design-system release level")
    if current_release.get("stableBaseline") != PREVIOUS_STABLE:
        fail("V1.3 rollback baseline must remain 1.2.0")
    if previous_release.get("status") != "stable" or previous_release.get("consumerEligible") is not True:
        fail("V1.2 retained rollback release record must remain intact")
    if previous_release.get("stableBaseline") != OLDER_STABLE:
        fail("V1.2 retained rollback baseline must remain 1.1.0")
    if older_release.get("status") != "stable" or older_release.get("consumerEligible") is not True:
        fail("V1.1 historical Stable release record must remain intact")

    for relative, required_phrases in CURRENT_AUTHORITY_DOCS.items():
        text = read_text(relative)
        if CURRENT_VERSION not in text and "GLAZE UI V1.3" not in text:
            fail(f"{relative} does not identify V1.3 current authority")
        for phrase in required_phrases:
            if phrase.lower() not in text.lower():
                fail(f"{relative} missing lifecycle phrase {phrase!r}")

    v12_contract = read_text("GLAZE_UI_V1_2.md")
    v12_preamble = v12_contract[:1400].lower()
    if "historical stable" not in v12_preamble and "retained rollback" not in v12_preamble:
        fail("GLAZE_UI_V1_2.md must identify V1.2 as retained historical Stable near its preamble")
    if CURRENT_VERSION not in v12_contract[:2200] and "GLAZE UI V1.3" not in v12_contract[:2200]:
        fail("GLAZE_UI_V1_2.md must point to V1.3 as current Stable near its preamble")

    sources = tracked_text_sources()
    stale_findings: list[dict[str, Any]] = []
    historical_markers = (
        "glaze ui v1.0",
        "glaze ui v1.1",
        "glaze ui v1.2",
        "1.0.0",
        "1.1.0",
        "1.2.0",
        "1.3.0-candidate",
    )
    validator_relative = "scripts/validate_glaze_v1_2_documentation_versions.py"
    for relative, text in sources.items():
        if relative == validator_relative:
            continue
        is_history = historical_record(relative, text)
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if not any(marker in lowered for marker in historical_markers):
                continue
            if not any(claim in lowered for claim in STRONG_CURRENT_CLAIMS):
                continue
            if is_history or any(qualifier in lowered for qualifier in HISTORICAL_QUALIFIERS):
                continue
            stale_findings.append(
                {"path": relative, "line": line_number, "text": line.strip()[:240]}
            )

    if stale_findings:
        preview = "; ".join(
            f"{item['path']}:{item['line']} {item['text']}" for item in stale_findings[:20]
        )
        fail(f"obsolete lifecycle/version authority language found: {preview}")

    report = {
        "schemaVersion": 7,
        "status": "pass",
        "currentOfficial": current_official,
        "currentStable": current_stable,
        "currentStableLabel": current_release.get("label"),
        "activeCandidate": active_candidate,
        "plannedNext": planned_next,
        "previousStableRollback": PREVIOUS_STABLE,
        "olderStableHistory": OLDER_STABLE,
        "auditedTrackedUtf8TextFiles": len(sources),
        "currentAuthorityDocuments": sorted(CURRENT_AUTHORITY_DOCS),
        "retainedV12Contract": "GLAZE_UI_V1_2.md",
        "historicalPrePromotionValidators": sorted(HISTORICAL_PREPROMOTION_VALIDATORS),
        "obsoleteLifecycleAuthorityFindings": 0,
        "scopeRule": "Current authority surfaces identify V1.3 / 1.3.0 as Official Stable; V1.2 is retained rollback/audit history and historical Candidate/RC records remain provenance.",
        "followUpRule": "V1.3.1 hardening and qualification obligations remain unresolved unless fresh accepted evidence exists; their transfer does not manufacture V1.3.0 passes.",
        "consumerRule": "V1.3 Stable consumer eligibility does not imply downstream conformance or product production acceptance.",
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
