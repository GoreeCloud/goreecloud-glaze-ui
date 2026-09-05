#!/usr/bin/env python3
"""Validate bounded GLAZE UI V1.2 form-factor token authority."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "tokens/glaze-v1.2-form-factor.candidate.json"
CONTRACT = ROOT / "contracts/v1.2/form-factor-tokens.candidate.json"
SPATIAL = ROOT / "tokens/glaze-v1.2-spatial-foundation.candidate.json"
CORE = ROOT / "contracts/v1.2/core-tokens.candidate.json"
MANIFEST = ROOT / "tokens/glaze-v1.2-core.candidate.json"
README = ROOT / "tokens/README.md"
VERSION = ROOT / "VERSION"
LIFECYCLE = ROOT / "registry/lifecycle.json"
ARTIFACTS = ROOT / "artifacts"
REPORT = ARTIFACTS / "glaze-v1.2-form-factor-token-report.json"

COMPOSITION_STATES = ["compact", "medium", "expanded", "largeFarView", "wearable", "spatial"]
LAYOUT_CLASSES = {
    "compact": "compact",
    "medium": "medium",
    "expanded": "expanded",
    "largeFarView": "large",
    "wearable": "wearable",
    "spatial": "spatial",
}
SPATIAL_REFS = {
    "compact": ("/guttersPx/compact", "/gridColumns/compact", 16, 4),
    "medium": ("/guttersPx/medium", "/gridColumns/medium", 24, 8),
    "expanded": ("/guttersPx/expanded", "/gridColumns/expanded", 32, 12),
    "largeFarView": ("/guttersPx/large", "/gridColumns/large", 48, 12),
}
INPUT_MODALITIES = {
    "touch",
    "pointer",
    "keyboard",
    "directional",
    "rotary",
    "voice",
    "assistiveSwitch",
    "gaze",
    "hand",
}


class ValidationError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValidationError(message)


def load(path: Path) -> dict:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def pointer(document: dict, pointer_value: str):
    require(pointer_value.startswith("/"), f"invalid JSON pointer {pointer_value!r}")
    current = document
    for raw in pointer_value[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        require(isinstance(current, dict) and key in current, f"unresolved JSON pointer {pointer_value!r} at {key!r}")
        current = current[key]
    return current


def validate_candidate(document: dict, label: str) -> None:
    require(document.get("version") == "1.2.0-candidate", f"{label} version drifted")
    require(document.get("lifecycle") == "candidate", f"{label} lifecycle drifted")
    require(document.get("consumerEligible") is False, f"{label} consumer boundary drifted")
    require(document.get("stableBaseline") == "1.1.0", f"{label} Stable baseline drifted")


def main() -> int:
    tokens = load(TOKENS)
    contract = load(CONTRACT)
    spatial = load(SPATIAL)
    core = load(CORE)
    manifest = load(MANIFEST)
    lifecycle = load(LIFECYCLE)

    require(VERSION.read_text().strip() == "1.1.0", "VERSION no longer preserves V1.1 Stable")
    require(
        lifecycle.get("currentStable") == "1.1.0" and lifecycle.get("currentOfficial") == "1.1.0",
        "lifecycle no longer preserves V1.1 Stable/Official",
    )
    validate_candidate(tokens, "form-factor token owner")
    validate_candidate(contract, "form-factor contract")
    validate_candidate(spatial, "spatial token authority")
    validate_candidate(core, "core token contract")
    validate_candidate(manifest, "core token manifest")

    require(contract.get("status") == "bounded-form-factor-token-authority", "form-factor contract status drifted")
    require(contract.get("compositionClasses") == COMPOSITION_STATES, "form-factor contract composition class order drifted")
    require(
        contract.get("authority", {}).get("companionSpecification") == "Glaze UI V1.2 — Responsive and Form-Factor Adaptation.docx",
        "form-factor companion authority drifted",
    )

    states = tokens.get("compositionStates", {})
    require(list(states) == COMPOSITION_STATES, "form-factor composition-state set/order drifted")
    for state_name, expected_layout_class in LAYOUT_CLASSES.items():
        require(states[state_name].get("layoutClass") == expected_layout_class, f"layout class drifted for {state_name}")
        require(states[state_name].get("navigation"), f"navigation mapping missing for {state_name}")
        require(states[state_name].get("primaryContentFlow"), f"primary content flow missing for {state_name}")
        require("minWidthPx" not in states[state_name] and "maxWidthPx" not in states[state_name], f"device-like breakpoint threshold leaked into {state_name}")

    for state_name, (gutter_pointer, grid_pointer, gutter_value, grid_value) in SPATIAL_REFS.items():
        state = states[state_name]
        require(
            state.get("gutterRef") == {"source": "tokens/glaze-v1.2-spatial-foundation.candidate.json", "pointer": gutter_pointer},
            f"spatial gutter alias drifted for {state_name}",
        )
        require(
            state.get("gridColumnsRef") == {"source": "tokens/glaze-v1.2-spatial-foundation.candidate.json", "pointer": grid_pointer},
            f"spatial grid alias drifted for {state_name}",
        )
        require(pointer(spatial, gutter_pointer) == gutter_value, f"spatial gutter authority drifted for {state_name}")
        require(pointer(spatial, grid_pointer) == grid_value, f"spatial grid authority drifted for {state_name}")

    rules = tokens.get("adaptationRules", {})
    for key, expected in {
        "widthIsDeviceIdentity": False,
        "deviceBrandBreakpointsCanonical": False,
        "platformAdapterOwnsCapabilitySelection": True,
        "semanticMeaningPreservedAcrossRecomposition": True,
        "currentLocationPreservedAcrossRecomposition": True,
        "userEnteredDataPreservedAcrossRecomposition": True,
        "desktopSqueezedIntoMobileProhibited": True,
        "mobileFirstClassDesignSurface": True,
        "touchCompletenessRequiredOnTouchCapableDesktop": True,
    }.items():
        require(rules.get(key) is expected, f"form-factor adaptation rule drifted: {key}")

    safe_area = tokens.get("safeAreaPolicy", {})
    require(safe_area.get("platformProvidedInsetsRequired") is True, "platform safe-area authority missing")
    require(safe_area.get("hardCodedDeviceCutoutInsetsProhibited") is True, "hard-coded cutout inset prohibition missing")
    require(safe_area.get("keyboardOcclusionIsLayoutConstraint") is True, "on-screen keyboard layout constraint missing")
    require(safe_area.get("regions") == ["top", "inline-start", "inline-end", "bottom"], "safe-area logical region set drifted")

    require(set(tokens.get("inputModalities", {})) == INPUT_MODALITIES, "form-factor input-modality authority drifted")
    require(tokens["inputModalities"]["keyboard"].get("completeCoreOperationRequired") is True, "keyboard completeness rule missing")
    require(tokens["inputModalities"]["directional"].get("spatiallyLogicalFocusPathRequired") is True, "far-view directional focus rule missing")
    require(tokens["inputModalities"]["gaze"].get("focusBeforeActivationRequired") is True, "gaze focus-before-activation rule missing")

    acceptance = tokens.get("acceptanceBoundaries", {})
    require(acceptance.get("narrowWebWidthClassPx") == 320, "320 px-class acceptance boundary drifted")
    require(acceptance.get("minimumInteractiveTargetPx") == 48, "interactive target floor drifted")
    require(acceptance.get("farViewMinimumInteractiveTargetPx") == 56, "far-view target floor drifted")
    require(acceptance.get("textScalePercent") == 200, "200% text acceptance boundary drifted")
    require(
        acceptance.get("rtlRequiredWhereApplicable") is True and acceptance.get("reducedTransparencyRequired") is True,
        "form-factor accessibility acceptance boundary drifted",
    )

    token_rules = tokens.get("rules", {})
    require(token_rules.get("routineAdaptationRulesCentralized") is True, "routine adaptation centralization rule missing")
    require(token_rules.get("numericGuttersRemainSpatialTokenAuthority") is True, "gutter authority duplication boundary drifted")
    require(token_rules.get("densityRemainsSpatialTokenAuthority") is True, "density authority duplication boundary drifted")
    require(token_rules.get("tokenOwnerDoesNotEstablishPlatformAcceptance") is True, "platform acceptance boundary missing")
    require(token_rules.get("consumerClaimBlockedUntilGovernedPromotion") is True, "consumer promotion boundary missing")

    family = core.get("families", {}).get("formFactor", {})
    require(
        family.get("status") == "candidate-owned"
        and family.get("owner") == "tokens/glaze-v1.2-form-factor.candidate.json"
        and family.get("pointer") == "/compositionStates"
        and family.get("consumerClaimBlocked") is True,
        "core form-factor ownership map drifted",
    )
    require(
        manifest.get("aliases", {}).get("formFactor.compositionStates")
        == {"source": "tokens/glaze-v1.2-form-factor.candidate.json", "pointer": "/compositionStates"},
        "core form-factor alias drifted",
    )
    require(manifest.get("unestablished") == {}, "stale form-factor unestablished marker remains in core manifest")

    ownership = contract.get("tokenOwnership", {})
    require(ownership.get("duplicatesSpatialGutterValues") is False, "form-factor contract permits duplicated gutter authority")
    require(ownership.get("duplicatesSpatialDensityValues") is False, "form-factor contract permits duplicated density authority")
    require(contract.get("rules", {}).get("formFactorTokenPresenceDoesNotEstablishPlatformParity") is True, "contract platform parity boundary missing")
    require(contract.get("rules", {}).get("consumerClaimBlocked") is True, "contract consumer boundary missing")

    readme = README.read_text(encoding="utf-8")
    for marker in (
        "glaze-v1.2-form-factor.candidate.json",
        "capability-class selection remains platform-adapter owned",
        "does not establish platform or form-factor acceptance",
    ):
        require(marker in readme, f"form-factor token documentation missing marker: {marker}")

    ARTIFACTS.mkdir(exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "id": contract["id"],
                "version": contract["version"],
                "consumerEligible": contract["consumerEligible"],
                "compositionStates": COMPOSITION_STATES,
                "inputModalities": sorted(INPUT_MODALITIES),
                "spatialAliasStates": sorted(SPATIAL_REFS),
                "result": "pass",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("GLAZE UI V1.2 form-factor token authority validated: Candidate owner established; platform acceptance remains blocked")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as error:
        print(f"GLAZE UI V1.2 form-factor token validation failed: {error}")
        raise SystemExit(1)
