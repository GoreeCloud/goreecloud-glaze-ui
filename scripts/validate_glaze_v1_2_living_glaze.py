#!/usr/bin/env python3
"""Validate the bounded GLAZE UI V1.2 Living Frosted Candidate tranche."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.2.0-candidate"
EXPECTED_STABLE = "1.1.0"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(f"Glaze V1.2 Living Glaze validation failed: {message}")


def load(path: str):
    p = ROOT / path
    require(p.is_file(), f"missing {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def text(path: str) -> str:
    p = ROOT / path
    require(p.is_file(), f"missing {path}")
    return p.read_text(encoding="utf-8")


def candidate_contract(path: str):
    value = load(path)
    require(value.get("version") == EXPECTED_VERSION, f"{path} version drifted")
    require(str(value.get("lifecycle", "")).startswith("candidate"), f"{path} lifecycle drifted")
    require(value.get("consumerEligible") is False, f"{path} became consumer eligible")
    require(value.get("stableBaseline") == EXPECTED_STABLE, f"{path} Stable baseline drifted")
    return value


def main() -> int:
    require(text("VERSION").strip() == EXPECTED_STABLE, "VERSION moved away from Stable 1.1.0")
    lifecycle = load("registry/lifecycle.json")
    require(lifecycle.get("currentStable") == EXPECTED_STABLE, "currentStable drifted")
    require(lifecycle.get("currentOfficial") == EXPECTED_STABLE, "currentOfficial drifted")
    require(lifecycle.get("activeCandidate") == EXPECTED_VERSION, "activeCandidate drifted")
    release = next((r for r in lifecycle.get("releases", []) if r.get("version") == EXPECTED_VERSION), None)
    require(release is not None and release.get("status") == "candidate", "Candidate lifecycle entry missing")
    require(release.get("consumerEligible") is False, "Candidate became consumer eligible")

    living = candidate_contract("contracts/v1.2/living-glaze.candidate.json")
    require(living.get("theme") == "Living Frosted", "theme identity drifted")
    require(living.get("interactionStates") == ["rest","hover","focus","pressed","dragged","selected","expanded","loading","disabled"], "interaction state set drifted")
    clarity = living.get("clarityProfiles", {})
    require([name for name in clarity if name != "accessibilityPrecedence"] == ["clear","balanced","dense"], "clarity profiles drifted")
    require(clarity.get("accessibilityPrecedence") == ["forced-colors","reduced-transparency","increased-contrast"], "clarity accessibility precedence drifted")
    require(living.get("performanceTiers", {}).get("degradationOrder") == [3,2,1,0], "performance fallback order drifted")
    require(living.get("stableCompatibleMotion", {}).get("experimentalGlazeMotionRequired") is False, "Experimental Glaze Motion became required")
    require("no-unrestricted-image-analysis" in living.get("opticalResponse", {}).get("privacyBoundary", ""), "privacy boundary weakened")

    adaptive = candidate_contract("contracts/v1.2/adaptive-navigation.candidate.json")
    ergonomic = candidate_contract("contracts/v1.2/ergonomic-layout.candidate.json")
    continuity = candidate_contract("contracts/v1.2/context-continuity.candidate.json")
    control = candidate_contract("contracts/v1.2/control-center-customization.candidate.json")
    foldable = candidate_contract("contracts/v1.2/foldable-adaptation.candidate.json")
    experience = candidate_contract("contracts/v1.2/component-experience.candidate.json")
    motion = candidate_contract("contracts/v1.2/motion-integration.candidate.json")
    require(adaptive.get("navigationCapsule", {}).get("minimumTargetPx") == 48, "navigation target floor weakened")
    require(ergonomic.get("requirements", {}).get("primaryActionsEvaluateReach") is True, "reachability stopped being first-class")
    require(continuity.get("motionRequiredForCorrectness") is False, "continuity became motion-dependent")
    require(control.get("parent", {}).get("nestedBackdropBlur") is False, "Control Center nested blur enabled")
    require(foldable.get("folded", {}).get("completeEnvironment") is True, "folded environment weakened")
    require("semantic-accent" in experience.get("requiredDimensions", []), "component experience matrix incomplete")
    require(motion.get("experimentalGlazeMotionPromotionImplied") is False, "Experimental Glaze Motion promotion implied")

    material = load("tokens/glaze-v1.2-living-material.candidate.json")
    interaction = load("tokens/glaze-v1.2-interaction.candidate.json")
    navigation = load("tokens/glaze-v1.2-navigation.candidate.json")
    ergonomics = load("tokens/glaze-v1.2-ergonomics.candidate.json")
    motion_tokens = load("tokens/glaze-v1.2-motion-integration.candidate.json")
    require(list(material.get("clarity", {}).keys()) == ["clear","balanced","dense"], "material clarity tokens drifted")
    require(material.get("clarity", {}).get("clear") == {"materialMixPercent":82,"blurDeltaPx":-4,"edgeSpecularPercent":28}, "Clear optical tokens drifted")
    require(material.get("clarity", {}).get("balanced") == {"materialMixPercent":92,"blurDeltaPx":0,"edgeSpecularPercent":45}, "Balanced optical tokens drifted")
    require(material.get("clarity", {}).get("dense") == {"materialMixPercent":98,"blurDeltaPx":6,"edgeSpecularPercent":68}, "Dense optical tokens drifted")
    require(material.get("backdrop", {}).get("simple", {}).get("materialMixDeltaPercent") == -4, "simple backdrop density delta drifted")
    require(material.get("backdrop", {}).get("complex", {}).get("materialMixDeltaPercent") == 2, "complex backdrop density delta drifted")
    require(material.get("backdrop", {}).get("unknown", {}).get("materialMixDeltaPercent") == 0, "unknown backdrop must fail closed")
    require(material.get("accessibilityPrecedence") == ["forced-colors","reduced-transparency","increased-contrast","clarity-personalization"], "material accessibility precedence drifted")
    require(material.get("performanceTiers") == {"0":"solid","1":"static-glaze","2":"responsive-glaze","3":"living-glaze"}, "material tier tokens drifted")
    require(interaction.get("states", {}).get("disabled", {}).get("opacityAloneForbidden") is True, "disabled state became opacity-only")
    require(navigation.get("semanticDestinationOrderStable") is True, "navigation destination semantics drifted")
    require(ergonomics.get("targets", {}).get("touchMinimumPx") == 48, "touch target floor weakened")
    require(ergonomics.get("targets", {}).get("touchAssistanceMinimumPx") == 56, "Touch Assistance target floor weakened")
    require(ergonomics.get("viewportWidthAloneDeterminesIntent") is False, "viewport width became sole intent proxy")
    require(motion_tokens.get("experimentalGlazeMotionRequired") is False, "motion tokens require Experimental runtime")

    css = text("css/glaze-v1.2-living-glaze.candidate.css")
    for marker in ('data-glaze-clarity="clear"','data-glaze-clarity="dense"','data-material-state="pressed"','data-material-state="dragged"','data-glaze-navigation-capsule','prefers-reduced-motion','forced-colors','data-glaze-tier="0"','--glaze-v12-living-material-mix: 82%','--glaze-v12-living-material-mix: 92%','--glaze-v12-living-material-mix: 98%'):
        require(marker in css, f"CSS marker missing: {marker}")
    runtime = text("js/glaze-v1.2-living-glaze.candidate.mjs")
    for export in ("setGlazeClarity", "setLivingGlazeState", "setBackdropComplexity", "setGlazeComplexityTier", "connectMaterialTransformation"):
        require(f"export function {export}" in runtime, f"runtime export missing: {export}")
    require("producer-or-renderer-supplied-complexity-only" in runtime, "runtime privacy boundary missing")

    reference = text("reference/v1.2/living-glaze.html")
    for marker in ("Living Glaze Material Lab", "Simple backdrop", "Complex backdrop", "Fail closed", "Adaptive Navigation Capsule", "glz12-glaze"):
        require(marker in reference, f"reference marker missing: {marker}")
    entry = text("css/glaze-v1.2.0-candidate.css")
    require('glaze-v1.2-living-glaze.candidate.css' in entry, "aggregate Candidate CSS does not import Living Glaze")

    print("GLAZE UI V1.2 Living Frosted Candidate contracts validated; Stable 1.1.0 authority preserved; no RC, Stable, human, native, or consumer acceptance implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
