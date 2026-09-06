#!/usr/bin/env python3
"""Validate Glaze lifecycle/version language across tracked text sources."""

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
    "README.md": ("current Stable",),
    "GLAZE_UI_V1_1.md": ("current Stable",),
    "CONFORMANCE.md": ("sole current", "conformance target"),
    "ACCEPTANCE.md": ("current Stable",),
    "ADOPTION.md": ("sole current", "adoption target"),
    "ENFORCEMENT.md": ("sole current", "consumer-conformance target"),
    "website/README.md": ("current Stable",),
    "ICON_CONSTRUCTION.md": ("Current Stable product authority", "subsystem-contract revision"),
    "ICON_IDENTITY.md": ("Current Stable product authority", "subsystem-contract revision"),
    "MIGRATION_V1_1_TO_V1_2.md": ("Stable authority", "Production migration target"),
    "GLAZE_UI_V1_2_CANDIDATE.md": ("Stable baseline", "Not Stable"),
}

HISTORICAL_DOCS = (
    "GLAZE_UI_V1_0.md",
    "GLAZE_UI_V1_1_CANDIDATE.md",
    "releases/1.0.0.md",
    "acceptance/v1.1-release-candidate.md",
    "acceptance/v1.1-specification-candidate.md",
)

# These retained non-Markdown sources contain exact historical lifecycle literals
# that are intentionally preserved for provenance or reproducibility. Their
# presence does not make the superseded text current authority.
HISTORICAL_SOURCE_PATHS = {
    "acceptance/v1.1-rendered-web-evidence.json",
    "scripts/promote_glaze_v1_1_stable.py",
    "scripts/validate_evidence_presentation.py",
    "scripts/validate_glaze_motion.py",
    "scripts/validate_glaze_v1_0_reset.py",
}

KNOWN_STALE_FORMS = (
    re.compile(r"GLAZE UI V1\.0 is the sole current Glaze UI product version", re.I),
    re.compile(r"GLAZE UI V1\.0 is the sole current Glaze UI product baseline", re.I),
    re.compile(r"No other Glaze UI version is a current application target", re.I),
    re.compile(r"Current official target:\s*\*{0,2}GLAZE UI V1\.0", re.I),
    re.compile(r"GLAZE UI V1\.0 establishes the sole current Glaze UI product identity", re.I),
)

HISTORICAL_QUALIFIERS = (
    "historical",
    "at the time",
    "at publication",
    "at candidate publication",
    "at this recorded",
    "during recorded",
    "then-current",
    "superseded",
    "not current",
    "does not define the current",
    "does not override the current",
    "was current",
    "was the current",
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
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
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
        if release.get("version") == version:
            return release
    fail(f"lifecycle release record missing for {version}")
    raise AssertionError("unreachable")


def is_explicit_historical_record(relative: str, text: str) -> bool:
    if relative in HISTORICAL_DOCS or relative in HISTORICAL_SOURCE_PATHS:
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

    if not isinstance(current_stable, str) or not current_stable:
        fail("currentStable must be a non-empty version")
    if current_official != current_stable:
        fail(f"currentOfficial {current_official!r} must equal currentStable {current_stable!r}")
    if version != current_stable:
        fail(f"VERSION {version!r} must equal currentStable {current_stable!r}")
    if not isinstance(active_candidate, str) or not active_candidate.endswith("-candidate"):
        fail("activeCandidate must be an explicit Candidate version")
    if active_candidate == current_stable:
        fail("activeCandidate must remain distinct from current Stable")

    stable_release = release_for(lifecycle, current_stable)
    candidate_release = release_for(lifecycle, active_candidate)
    if stable_release.get("status") != "stable" or stable_release.get("consumerEligible") is not True:
        fail("current Stable release must be stable and consumer-eligible")
    if candidate_release.get("status") != "candidate" or candidate_release.get("consumerEligible") is not False:
        fail("active Candidate must remain candidate and non-consumer-eligible")
    if candidate_release.get("stableBaseline") != current_stable:
        fail("active Candidate stableBaseline must equal currentStable")

    stable_label = stable_release.get("label")
    if not isinstance(stable_label, str) or not stable_label:
        fail("current Stable release label is missing")

    for relative, required_phrases in CURRENT_AUTHORITY_DOCS.items():
        text = read_text(relative)
        if stable_label not in text or current_stable not in text:
            fail(f"{relative} does not identify current Stable {stable_label} / {current_stable}")
        for phrase in required_phrases:
            if phrase.lower() not in text.lower():
                fail(f"{relative} missing lifecycle phrase {phrase!r}")

    stability = read_text("STABILITY.md")
    if "historical" not in stability[:800].lower():
        fail("STABILITY.md must identify its V1.0 scope as historical")
    if stable_label not in stability[:1000] or current_stable not in stability[:1000]:
        fail("STABILITY.md must direct readers to the current Stable authority")

    for relative in HISTORICAL_DOCS:
        text = read_text(relative)
        preamble = text[:1200].lower()
        if "historical" not in preamble and "superseded" not in preamble:
            fail(f"{relative} must identify itself as historical or superseded near its preamble")
        if stable_label not in text[:1800] or current_stable not in text[:1800]:
            fail(f"{relative} must identify the current Stable successor without overriding history")

    text_sources = tracked_text_sources()
    markdown = sorted(path for path in text_sources if path.endswith(".md"))
    stale_findings: list[dict[str, Any]] = []

    historical_releases = [
        release
        for release in lifecycle.get("releases", [])
        if isinstance(release, dict) and str(release.get("status", "")).startswith("historical")
    ]
    historical_markers = [
        marker.lower()
        for release in historical_releases
        for marker in (release.get("label"), release.get("version"))
        if isinstance(marker, str) and marker
    ]

    validator_relative = "scripts/validate_glaze_v1_2_documentation_versions.py"
    for relative, text in text_sources.items():
        historical_record = is_explicit_historical_record(relative, text)
        # This validator necessarily embeds the prohibited phrases as regex test
        # definitions. Do not interpret those definitions as product claims.
        if relative != validator_relative:
            for pattern in KNOWN_STALE_FORMS:
                match = pattern.search(text)
                if match:
                    stale_findings.append(
                        {"path": relative, "kind": "known-stale-form", "text": match.group(0)}
                    )

        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if not any(marker in lowered for marker in historical_markers):
                continue
            if not any(claim in lowered for claim in STRONG_CURRENT_CLAIMS):
                continue
            if historical_record or any(qualifier in lowered for qualifier in HISTORICAL_QUALIFIERS):
                continue
            stale_findings.append(
                {
                    "path": relative,
                    "line": line_number,
                    "kind": "unqualified-historical-current-claim",
                    "text": line.strip()[:240],
                }
            )

    if stale_findings:
        preview = "; ".join(
            f"{item['path']}:{item.get('line', '?')} {item['text']}" for item in stale_findings[:16]
        )
        fail(f"obsolete lifecycle/version authority language found: {preview}")

    report = {
        "schemaVersion": 2,
        "status": "pass",
        "currentOfficial": current_official,
        "currentStable": current_stable,
        "currentStableLabel": stable_label,
        "activeCandidate": active_candidate,
        "activeCandidateConsumerEligible": candidate_release.get("consumerEligible"),
        "auditedTrackedMarkdownFiles": len(markdown),
        "auditedTrackedUtf8TextFiles": len(text_sources),
        "currentAuthorityDocuments": sorted(CURRENT_AUTHORITY_DOCS),
        "historicalDocumentsExplicitlyQualified": list(HISTORICAL_DOCS),
        "historicalTextSourcesExplicitlyClassified": sorted(HISTORICAL_SOURCE_PATHS),
        "obsoleteLifecycleAuthorityFindings": 0,
        "historicalIntegrityRule": "Historical records remain preserved but may not present superseded lifecycle state as current authority unless the record or statement is explicitly historical.",
        "subsystemVersionRule": "Subsystem contract revisions remain distinct from Glaze UI product lifecycle versions and do not alter currentStable/currentOfficial.",
        "scopeRule": "The audit covers every tracked UTF-8 text source at the exact checked-out Git revision; binary and non-UTF-8 tracked files are excluded from text-language analysis.",
    }

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output
        if not output.is_absolute():
            output = ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
