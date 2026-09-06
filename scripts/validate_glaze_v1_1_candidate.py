#!/usr/bin/env python3
"""Validate the historical GLAZE UI V1.1 specification-stable candidate.

This validator intentionally fails closed if the retained candidate source relaxes
inherited V1 semantic, accessibility, material, or release boundaries. Passing
this script does not promote V1.1 or establish current production acceptance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str):
    with (ROOT / relative).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    current_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    performance = load_json("contracts/performance/glaze-v1-performance-budget.json")
    materials = load_json("tokens/materials.json")
    semantics = load_json("tokens/semantic-colors.json")
    accessibility = load_json("contracts/accessibility/resolution-matrix.json")
    candidate = load_json("contracts/v1.1/optical-refinement.candidate.json")
    atmosphere = load_json("tokens/glaze-v1.1-atmosphere.candidate.json")

    # Historical Candidate source remains valid to audit after later governed Stable promotions.
    require(
        current_version in {"1.0.0", "1.1.0", "1.2.0"},
        "V1.1 candidate history may be validated only within the governed V1 product line",
    )
    require(candidate["releaseBoundary"]["currentTarget"] is False, "V1.1 candidate must not declare itself current")
    require(candidate["releaseBoundary"]["productionStable"] is False, "V1.1 candidate must not declare production stability")
    require(candidate["releaseBoundary"]["mergeDoesNotPromote"] is True, "merge must not imply lifecycle promotion")
    require(atmosphere["currentV1Token"] is False, "candidate atmosphere tokens must not present as current V1 tokens")

    # V1 structural material constraints are inherited, not weakened.
    rules = performance["rules"]
    require(rules["nestedBackdropBlurAllowed"] is False, "current V1 must prohibit default nested backdrop blur")
    require(rules["dominantGlazePanelsMax"] == 1, "current V1 dominant Glaze panel budget must remain 1")
    require(rules["smallFloatingGlazeControlsMax"] == 3, "current V1 small floating Glaze control budget must remain 3")
    require(rules["effectsMayBeRemovedBeforeSemantics"] is True, "effects must remain removable before semantics")

    functional = materials["roles"]["functionalGlass"]
    inherited = candidate["materialCompatibility"]["functionalGlassBaseline"]
    require(inherited["blurPx"] == functional["blurPx"] == 24, "V1.1 candidate must inherit 24px functional glass blur baseline")
    require(inherited["saturationPercent"] == functional["saturationPercent"] == 145, "V1.1 candidate must inherit 145% functional glass saturation")
    require(inherited["opacity"] == functional["opacity"] == 0.78, "V1.1 candidate must inherit 0.78 functional glass opacity")
    require(candidate["materialCompatibility"]["nestedBackdropBlurAllowed"] is False, "V1.1 candidate must not enable nested backdrop blur")
    require(candidate["materialCompatibility"]["dominantGlazePanelsMax"] == 1, "V1.1 candidate must preserve dominant Glaze panel budget")
    require(candidate["materialCompatibility"]["smallFloatingGlazeControlsMax"] == 3, "V1.1 candidate must preserve small floating control budget")

    # Semantic truth and non-color-only meaning are non-negotiable.
    require(semantics["color_only_communication_allowed"] is False, "current semantic contract must prohibit color-only communication")
    require(semantics["branding_may_override_semantics"] is False, "branding must not override semantics")
    require(atmosphere["semanticPrecedence"]["atmosphereIsLowestPriority"] is True, "V1.1 atmosphere must be lowest-priority color layer")
    require(atmosphere["semanticPrecedence"]["tealOrAmberMayRepresentProtectedSemanticState"] is False, "teal/amber atmosphere must not represent protected state")
    require(atmosphere["semanticPrecedence"]["brandingMayOverrideSemantics"] is False, "V1.1 branding must not override semantics")
    require(atmosphere["semanticPrecedence"]["colorOnlyCommunicationAllowed"] is False, "V1.1 must prohibit color-only communication")

    # Preserve the current accessibility precedence before V1.1 expression.
    expected_accessibility_prefix = [
        "protected-semantic-meaning",
        "forced-colors",
        "reduced-motion",
        "reduced-transparency",
        "increased-contrast-and-show-boundaries",
        "large-text-and-touch-assistance",
    ]
    require(accessibility["resolutionOrder"][:6] == expected_accessibility_prefix, "current accessibility resolution order changed unexpectedly")
    require(candidate["authorityResolutionOrder"][0] == "producer-authoritative-protected-semantic-meaning", "candidate must resolve protected semantic meaning first")
    require(candidate["authorityResolutionOrder"][1:4] == ["forced-colors", "reduced-motion", "reduced-transparency"], "candidate must preserve top accessibility override ordering")
    require(candidate["authorityResolutionOrder"][-1] == "v1.1-optical-atmosphere-application-identity-and-personalization", "V1.1 expression must resolve last")

    # Frozen atmospheric identity and restrained caps.
    expected_primitives = {
        "canvasBlack": "#081016",
        "deepGraphite": "#101A20",
        "slateGraphite": "#18252B",
        "deepTeal": "#0F6B6F",
        "mineralTeal": "#1C8A8D",
        "softAqua": "#8FD6D2",
        "softAmber": "#D9A35F",
        "champagneGold": "#E7C78A",
        "warmGlow": "#F2D7A6",
    }
    require(atmosphere["primitives"] == expected_primitives, "canonical V1.1 atmospheric primitive palette does not match stabilized contract")
    require(atmosphere["compositingRoles"]["tealMist"] == {"source": "deepTeal", "alpha": 0.08}, "Teal Mist must remain Deep Teal at 8% alpha")
    require(atmosphere["compositingRoles"]["amberMist"] == {"source": "softAmber", "alpha": 0.05}, "Amber Mist must remain Soft Amber at 5% alpha")
    require("muted-coral" in atmosphere["excludedCanonicalColors"], "Muted Coral must remain outside frozen V1.1 canonical palette")

    aura = atmosphere["auraMaxCompositedAlpha"]
    require(aura == {
        "light": {"teal": 0.08, "amber": 0.04},
        "dark": {"teal": 0.12, "amber": 0.06},
        "deepDark": {"teal": 0.16, "amber": 0.08},
    }, "Aura caps must match stabilized Light/Dark/Deep Dark contract")

    for appearance, values in aura.items():
        require(values["amber"] < values["teal"], f"amber Aura must remain secondary to teal in {appearance}")
        require(values["teal"] <= 0.16, f"teal Aura exceeds V1.1 cap in {appearance}")
        require(values["amber"] <= 0.08, f"amber Aura exceeds V1.1 cap in {appearance}")

    require(atmosphere["regionRules"]["defaultAuraFieldsMax"] == 2, "default Aura field count must remain bounded to 2")
    require(atmosphere["regionRules"]["amberMustRemainSecondaryToTeal"] is True, "amber must remain secondary to teal")

    # Environmental Color Memory is optional, local by default, bounded and non-semantic.
    ecm_contract = candidate["environmentalColorMemory"]
    ecm_atmosphere = atmosphere["environmentalColorMemory"]
    require(ecm_contract["requiredForConformance"] is False, "environmental sampling must not be required for V1.1 conformance")
    require(ecm_contract["localRenderingOnlyByDefault"] is True, "environmental color derivation must be local by default")
    require(ecm_contract["remoteTransmissionForColorDerivationAllowed"] is False, "V1.1 contract must not authorize remote transmission for color derivation")
    require(ecm_contract["persistentSampleHistoryAllowedByThisContract"] is False, "V1.1 contract must not authorize persistent sample history")
    require(ecm_contract["semanticInferenceAllowed"] is False, "environmental color must not infer semantics")
    require(ecm_atmosphere["derivedInfluenceMaxFractionOfAuraCap"] == 0.5, "environmental influence must be clamped to 50% of Aura cap")

    # Scope guards keep V1.1 incremental.
    excluded = set(candidate["frozenScope"]["excluded"])
    for required_exclusion in {
        "glaze-motion-lifecycle-promotion",
        "canonical-component-catalog-expansion",
        "new-protected-system-semantics",
        "default-nested-backdrop-blur",
        "required-environmental-content-sampling",
        "muted-coral-as-canonical-v1.1-atmosphere",
    }:
        require(required_exclusion in excluded, f"frozen V1.1 scope must exclude {required_exclusion}")

    # Candidate acceptance cannot be reduced to automation alone.
    require(candidate["referenceScenes"]["humanOpticalReviewRequired"] is True, "V1.1 acceptance must require human optical review")
    require(candidate["referenceScenes"]["automatedRegressionDoesNotReplaceHumanReview"] is True, "automation must not replace human optical review")
    require("governed-release-decision-promotes-v1.1" in candidate["releaseGates"], "V1.1 must require explicit governed release promotion")

    if errors:
        print("GLAZE UI V1.1 candidate validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.1 historical specification-stable Candidate source: PASS")
    print(f"Boundary: historical source validation only under current repository VERSION {current_version}; no lifecycle promotion or consumer acceptance implied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
