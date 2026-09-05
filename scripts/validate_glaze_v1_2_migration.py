#!/usr/bin/env python3
"""Validate the GLAZE UI V1.1 -> V1.2 migration control plane.

This validator is intentionally lifecycle-conservative. It proves that the Candidate
migration contracts remain internally coherent and that V1.1 Stable authority has not
moved. It does not establish rendered, RC, Stable, or downstream consumer acceptance.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "VERSION"
LIFECYCLE_PATH = ROOT / "registry/lifecycle.json"
OPTICAL_PATH = ROOT / "tokens/glaze-v1.2-optical-foundation.candidate.json"
MIGRATION_PATH = ROOT / "contracts/v1.2/migration.candidate.json"
GATES_PATH = ROOT / "acceptance/v1.2-promotion-gates.candidate.md"
CI_PATH = ROOT / ".github/workflows/ci.yml"
V11_CSS_PATH = ROOT / "css/glaze-v1.1.0.css"
V11_JS_PATH = ROOT / "js/glaze-v1.1.0.mjs"
COMPONENT_CONTRACT_PATH = ROOT / "contracts/v1.2/component-materials.candidate.json"
SYSTEM_SHELL_CONTRACT_PATH = ROOT / "contracts/v1.2/system-shell-materials.candidate.json"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"GLAZE UI V1.2 migration validation failed: {message}")


def text(path: Path) -> str:
    req(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def obj(path: Path) -> dict:
    value = json.loads(text(path))
    req(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def main() -> None:
    version = text(VERSION_PATH).strip()
    lifecycle = obj(LIFECYCLE_PATH)
    optical = obj(OPTICAL_PATH)
    migration = obj(MIGRATION_PATH)
    gates = text(GATES_PATH)
    ci = text(CI_PATH)
    components = obj(COMPONENT_CONTRACT_PATH)
    shell = obj(SYSTEM_SHELL_CONTRACT_PATH)

    # G0: Stable authority must remain V1.1 throughout this Candidate control-plane change.
    req(version == "1.1.0", "VERSION must remain 1.1.0 during Candidate migration planning")
    req(lifecycle.get("currentStable") == "1.1.0", "currentStable must remain 1.1.0")
    req(lifecycle.get("currentOfficial") == "1.1.0", "currentOfficial must remain 1.1.0")
    req(lifecycle.get("activeCandidate") == "1.2.0-candidate", "activeCandidate must remain 1.2.0-candidate")
    req(V11_CSS_PATH.is_file(), "V1.1 Stable CSS entrypoint is missing")
    req(V11_JS_PATH.is_file(), "V1.1 Stable runtime entrypoint is missing")

    releases = lifecycle.get("releases", [])
    req(isinstance(releases, list), "lifecycle releases must be an array")
    candidate = next(
        (item for item in releases if isinstance(item, dict) and item.get("version") == "1.2.0-candidate"),
        None,
    )
    req(candidate is not None, "V1.2 Candidate lifecycle record is missing")
    assert candidate is not None
    req(candidate.get("status") == "candidate", "V1.2 lifecycle status must remain candidate")
    req(candidate.get("consumerEligible") is False, "V1.2 Candidate must remain non-consumer-eligible")
    req(candidate.get("stableBaseline") == "1.1.0", "V1.2 Candidate Stable baseline drifted")
    req(
        candidate.get("opticalFoundation") == "tokens/glaze-v1.2-optical-foundation.candidate.json",
        "lifecycle Candidate opticalFoundation binding missing or incorrect",
    )
    req(
        candidate.get("migration") == "contracts/v1.2/migration.candidate.json",
        "lifecycle Candidate migration binding missing or incorrect",
    )
    req(
        candidate.get("promotionGates") == "acceptance/v1.2-promotion-gates.candidate.md",
        "lifecycle Candidate promotion-gate binding missing or incorrect",
    )

    # G1: Contract the exact proposed Frosted Optical identity without claiming it is Stable.
    req(optical.get("product") == "GLAZE UI V1.2", "optical foundation product mismatch")
    req(optical.get("version") == "1.2.0-candidate", "optical foundation version mismatch")
    req(optical.get("lifecycle") == "candidate", "optical foundation lifecycle must remain candidate")
    req(optical.get("stableBaseline") == "1.1.0", "optical foundation Stable baseline drifted")
    req(optical.get("currentStableToken") is False, "optical foundation must not claim Stable token authority")
    req(
        optical.get("extends") == "tokens/glaze-v1.2-frosted-neutral.candidate.json",
        "optical foundation must explicitly extend the existing Frosted Neutral Candidate layer",
    )

    identity = optical.get("identity", {})
    req(identity.get("primaryMaterial") == "frost-white", "Frost White must remain the primary material")
    req(identity.get("primaryAtmosphere") == "ice-blue", "Ice Blue must remain the primary atmosphere")
    req(identity.get("secondaryAtmosphere") == "glacier-blue", "Glacier Blue must remain the secondary atmosphere")
    req(identity.get("darkNeutral") == "cool-graphite", "Cool Graphite must remain the dark neutral")
    req(identity.get("deepDarkBase") == "blue-black", "Blue-Black must remain the Deep Dark base")
    req(identity.get("colorPhilosophy") == "atmospheric-not-decorative", "color philosophy drifted")

    expected_palette = {
        "frostWhite": "#F4F8FA",
        "crystalWhite": "#FBFDFE",
        "iceBlue": "#DCECF6",
        "glacierBlue": "#8FC4E8",
        "clearSkyBlue": "#68AEE0",
        "cloudGray": "#DCE3E8",
        "slateGray": "#7E8D99",
        "coolGraphite": "#151C22",
        "deepGraphite": "#0E1419",
        "blueBlack": "#070C11",
    }
    req(optical.get("opticalPalette") == expected_palette, "initial V1.2 optical palette references drifted")

    expected_frost = ["clear", "mist", "frost", "dense-frost", "opaque-frost"]
    frost_levels = optical.get("frostLevels", {})
    req(isinstance(frost_levels, dict), "frostLevels must be an object")
    req(list(frost_levels) == expected_frost, "frost levels must remain Clear/Mist/Frost/Dense Frost/Opaque Frost in order")

    distribution = optical.get("visualDistribution", {})
    req(distribution.get("neutralPercent") == {"min": 65, "max": 80}, "neutral distribution guidance drifted")
    req(
        distribution.get("frostedTranslucentPercent") == {"min": 15, "max": 25},
        "frosted translucent distribution guidance drifted",
    )
    req(
        distribution.get("iceBlueAtmospherePercent") == {"min": 3, "max": 10},
        "Ice Blue atmosphere distribution guidance drifted",
    )

    aura = optical.get("auraFamilies", {})
    req(
        set(aura) == {"frostAura", "iceAura", "crystalAura", "contentAura"},
        "Aura families must be exactly Frost/Ice/Crystal/Content",
    )
    aura_policy = optical.get("auraPolicy", {})
    req(aura_policy.get("defaultAtmosphere") == "ice-blue", "Aura default atmosphere must remain Ice Blue")
    req(aura_policy.get("tealDefaultAtmosphereAllowed") is False, "teal must not be allowed as default V1.2 atmosphere")
    req(aura_policy.get("purpleDefaultAtmosphereAllowed") is False, "purple must not be allowed as default V1.2 atmosphere")
    req(aura_policy.get("highSaturationGlowAllowed") is False, "high-saturation glow must remain prohibited")
    req(
        aura_policy.get("legacyAuraPromotionRequirement") == "retire-or-map-to-frost-ice-before-rc",
        "legacy V1.1 Aura compatibility must remain release-blocking before RC",
    )

    profiles = optical.get("performanceProfiles", {})
    req(set(profiles) == {"full", "reduced", "minimal"}, "performance profiles must be Full/Reduced/Minimal")
    req(profiles.get("minimal", {}).get("blur") is False, "Minimal profile must disable blur")
    req(profiles.get("minimal", {}).get("preserveHierarchy") is True, "Minimal profile must preserve hierarchy")

    anti_patterns = set(optical.get("antiPatterns", []))
    for required in {
        "purple-default-atmosphere",
        "teal-default-atmosphere",
        "neon-effects",
        "bright-cyan-glow",
        "blur-behind-dense-reading-content",
        "strong-gradients-on-routine-controls",
        "liquid-like-distortion-that-harms-readability",
    }:
        req(required in anti_patterns, f"required V1.2 anti-pattern missing: {required}")

    boundary = optical.get("promotionBoundary", {})
    req(boundary.get("stableVersionRemains") == "1.1.0", "optical promotion boundary must preserve V1.1 Stable")
    req(boundary.get("consumerMigrationTarget") is False, "optical Candidate must not be a consumer migration target")

    # Migration control plane must preserve exact baseline identity and ordered gate progression.
    stable = migration.get("stableBaseline", {})
    req(stable.get("version") == "1.1.0", "migration Stable baseline version drifted")
    req(
        stable.get("commit") == "15cc76d2bcd4065552dc31c77145b63f34d9e7b2",
        "migration Stable baseline commit drifted",
    )
    req(stable.get("tag") == "v1.1.0", "migration Stable baseline tag drifted")
    req(stable.get("consumerEligible") is True, "V1.1 Stable must remain consumer eligible")

    target = migration.get("target", {})
    req(target.get("version") == "1.2.0-candidate", "migration target must remain Candidate")
    req(target.get("consumerEligible") is False, "migration target must remain non-consumer-eligible")
    req(target.get("optInOnly") is True, "Candidate migration must remain explicit opt-in")
    req(target.get("stablePromotionRequiredBeforeProductionMigration") is True, "production migration must require Stable promotion")

    governance = migration.get("governance", {})
    req(governance.get("exactHeadValidationRequired") is True, "exact-head validation must remain required")
    req(governance.get("stableAuthorityMayNotMoveInThisChangeSet") is True, "this change set must not move Stable authority")
    req(governance.get("versionFileMayNotChangeInThisChangeSet") is True, "this change set must not change VERSION")
    req(governance.get("downstreamConformanceClaimsAllowed") is False, "downstream Candidate conformance claims must remain prohibited")

    expected_stages = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"]
    stages = migration.get("implementationStages", [])
    req(isinstance(stages, list), "implementationStages must be an array")
    req([item.get("id") for item in stages if isinstance(item, dict)] == expected_stages, "migration stages are missing or out of order")
    req([item.get("exitGate") for item in stages if isinstance(item, dict)] == [f"G{i}" for i in range(8)], "stage-to-gate mapping drifted")

    gates_data = migration.get("acceptanceGates", [])
    req(isinstance(gates_data, list), "acceptanceGates must be an array")
    req([item.get("id") for item in gates_data if isinstance(item, dict)] == [f"G{i}" for i in range(8)], "acceptance gates must remain G0 through G7")
    req(all(item.get("blocking") is True for item in gates_data if isinstance(item, dict)), "all migration gates must remain blocking")

    prohibitions = set(migration.get("promotionProhibitions", []))
    for required in {
        "do-not-set-VERSION-to-1.2.0-before-G6",
        "do-not-set-currentStable-to-1.2.0-before-G6",
        "do-not-mark-1.2.0-candidate-consumerEligible",
        "do-not-claim-downstream-consumer-conformance-from-design-system-evidence",
    }:
        req(required in prohibitions, f"promotion prohibition missing: {required}")

    # Existing Candidate component/shell contracts must stay in scope while the optical layer evolves.
    req(components.get("version") == "1.2.0-candidate", "component material contract version drifted")
    req(len(components.get("components", {})) == 32, "component material contract must retain 32 components")
    req(shell.get("version") == "1.2.0-candidate", "System Shell material contract version drifted")
    req(len(shell.get("regions", {})) == 5, "System Shell material contract must retain five regions")

    # Human-readable gates and CI wiring are part of the contract surface.
    for gate_id in [f"G{i}" for i in range(8)]:
        req(f"## {gate_id} " in gates, f"human-readable promotion gate {gate_id} missing")
    req(
        "python scripts/validate_glaze_v1_2_migration.py" in ci,
        "CI must execute the V1.2 migration control-plane validator",
    )

    print("GLAZE UI V1.2 migration control-plane validation passed")
    print("Stable authority: 1.1.0")
    print("Active Candidate: 1.2.0-candidate (non-consumer-eligible)")
    print("Optical foundation: Frost White + Ice Blue + Clear-to-Frosted Glaze")
    print("Migration gates: G0-G7 contracted and blocking")


if __name__ == "__main__":
    main()
