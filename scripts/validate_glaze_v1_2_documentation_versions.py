#!/usr/bin/env python3
"""Audit current V1.2 Stable lifecycle/version language across tracked text sources."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / "registry" / "lifecycle.json"
VERSION = ROOT / "VERSION"

CURRENT_AUTHORITY_DOCS = {
    "README.md": ("current Stable",),
    "CONTRIBUTING.md": ("current Stable", "Proposed / qualification-active"),
    "GLAZE_UI_V1_2.md": ("Stable",),
    "CONFORMANCE.md": ("conformance target",),
    "ACCEPTANCE.md": ("current Stable",),
    "ADOPTION.md": ("adoption target",),
    "ENFORCEMENT.md": ("consumer-conformance target",),
    "website/README.md": ("current Stable",),
    "ICON_CONSTRUCTION.md": ("Current Stable product authority",),
    "ICON_IDENTITY.md": ("Current Stable product authority",),
}

HISTORICAL_DOCS = (
    "GLAZE_UI_V1_0.md",
    "GLAZE_UI_V1_1.md",
    "GLAZE_UI_V1_1_CANDIDATE.md",
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
    "historical", "at the time", "at publication", "then-current", "superseded",
    "not current", "does not define the current", "does not override the current",
    "was current", "was the current", "previous stable", "prior stable", "rollback",
)
STRONG_CURRENT_CLAIMS = (
    "sole current", "current official target", "current stable", "current product identity",
    "current product version", "current product baseline", "current application target",
    "current adoption target", "current conformance target", "current target",
    "all current glaze ui work targets",
    "currentstable", "currentofficial", "officialproductlabel",
)


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


def historical_record(relative: str, text: str) -> bool:
    """Return whether a tracked source is explicitly historical/provenance-only."""
    if relative in HISTORICAL_DOCS or relative in HISTORICAL_SOURCE_PATHS:
        return True

    path = Path(relative)
    lowered = relative.lower()
    name = path.name.lower()

    if relative.startswith("acceptance/v1.1") or relative.startswith("contracts/v1.1/"):
        return True
    if relative.startswith("releases/1.1") or relative.startswith("reference/v1.1/"):
        return True
    if relative.startswith("scripts/") and name in HISTORICAL_PREPROMOTION_VALIDATORS:
        return True
    if "candidate" in name or ".candidate." in lowered or "release-candidate" in lowered:
        return True
    if name.endswith("_legacy.py") or name.endswith("-legacy.py"):
        return True

    preamble = text[:1600].lower()
    return "historical record" in preamble or "historical status" in preamble or "superseded" in preamble


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

    if current_stable != "1.2.0" or current_official != "1.2.0" or version != "1.2.0":
        fail("VERSION/currentStable/currentOfficial must agree on V1.2 Stable / 1.2.0")
    if active_candidate is not None:
        fail("V1.2 Stable must not retain an active V1.2 Candidate")
    if planned_next != "1.3.0-candidate":
        fail("plannedNext must identify the deferred V1.3 Candidate track")

    stable_release = release_for(lifecycle, "1.2.0")
    previous_release = release_for(lifecycle, "1.1.0")
    if stable_release.get("status") != "stable" or stable_release.get("consumerEligible") is not True:
        fail("V1.2 must remain Stable and consumer-eligible at the design-system release level")
    if stable_release.get("stableBaseline") != "1.1.0":
        fail("V1.2 rollback baseline must remain 1.1.0")
    if previous_release.get("status") != "stable" or previous_release.get("consumerEligible") is not True:
        fail("V1.1 rollback release record must remain intact")

    stable_label = stable_release.get("label")
    if not isinstance(stable_label, str) or not stable_label:
        fail("V1.2 Stable release label is missing")

    for relative, required_phrases in CURRENT_AUTHORITY_DOCS.items():
        text = read_text(relative)
        if "1.2.0" not in text and "GLAZE UI V1.2" not in text:
            fail(f"{relative} does not identify V1.2 current authority")
        for phrase in required_phrases:
            if phrase.lower() not in text.lower():
                fail(f"{relative} missing lifecycle phrase {phrase!r}")

    for relative in HISTORICAL_DOCS:
        text = read_text(relative)
        preamble = text[:1400].lower()
        if "historical" not in preamble and "superseded" not in preamble:
            fail(f"{relative} must identify itself as historical or superseded near its preamble")
        if "GLAZE UI V1.2" not in text[:2200] and "1.2.0" not in text[:2200]:
            fail(f"{relative} must point to V1.2 as the current Stable successor near its preamble")

    sources = tracked_text_sources()
    stale_findings: list[dict[str, Any]] = []
    historical_markers = ("glaze ui v1.0", "glaze ui v1.1", "1.0.0", "1.1.0", "1.2.0-candidate")
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
            stale_findings.append({"path": relative, "line": line_number, "text": line.strip()[:240]})

    if stale_findings:
        preview = "; ".join(f"{item['path']}:{item['line']} {item['text']}" for item in stale_findings[:20])
        fail(f"obsolete lifecycle/version authority language found: {preview}")

    report = {
        "schemaVersion": 6,
        "status": "pass",
        "currentOfficial": current_official,
        "currentStable": current_stable,
        "currentStableLabel": stable_label,
        "activeCandidate": active_candidate,
        "plannedNext": planned_next,
        "previousStableRollback": "1.1.0",
        "auditedTrackedUtf8TextFiles": len(sources),
        "currentAuthorityDocuments": sorted(CURRENT_AUTHORITY_DOCS),
        "historicalDocumentsExplicitlyQualified": list(HISTORICAL_DOCS),
        "historicalPrePromotionValidators": sorted(HISTORICAL_PREPROMOTION_VALIDATORS),
        "obsoleteLifecycleAuthorityFindings": 0,
        "scopeRule": "Historical Candidate/RC/release and superseded pre-promotion qualification records are preserved as provenance, while current V1.2 authority surfaces remain fail-closed against superseded lifecycle claims.",
        "contributingRule": "CONTRIBUTING.md is a current authority surface and must identify V1.2 / 1.2.0 as Stable while V1.3 remains Proposed / qualification-active until governed promotion.",
        "deferredQualificationRule": "V1.3 deferral does not convert unperformed V1.2 human/manual/physical qualification into passed evidence.",
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
