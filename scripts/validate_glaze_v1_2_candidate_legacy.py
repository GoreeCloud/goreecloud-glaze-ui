#!/usr/bin/env python3
"""Fail closed when the GLAZE UI V1.2 Frosted Neutral Candidate drifts."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = ROOT / "tokens/glaze-v1.2-frosted-neutral.candidate.json"
CSS_PATH = ROOT / "css/glaze-v1.2-frosted-neutral.candidate.css"
COMPONENT_CSS_PATH = ROOT / "css/glaze-v1.2-components.candidate.css"
SYSTEM_SHELL_CSS_PATH = ROOT / "css/glaze-v1.2-system-shell.candidate.css"
ENTRYPOINT_PATH = ROOT / "css/glaze-v1.2.0-candidate.css"
REFERENCE_PATH = ROOT / "reference/v1.2/frosted-neutral.html"
COMPONENT_REFERENCE_PATH = ROOT / "reference/v1.2/component-gallery.html"
SYSTEM_SHELL_REFERENCE_PATH = ROOT / "reference/v1.2/system-shell.html"
CONTRACT_PATH = ROOT / "GLAZE_UI_V1_2_CANDIDATE.md"
COMPONENT_CONTRACT_PATH = ROOT / "contracts/v1.2/component-materials.candidate.json"
COMPONENT_CATALOG_PATH = ROOT / "contracts/components/v1/catalog.json"
SYSTEM_SHELL_CONTRACT_PATH = ROOT / "contracts/v1.2/system-shell-materials.candidate.json"
INHERITED_SYSTEM_SHELL_PATH = ROOT / "contracts/system-shell/glaze-system-shell-v1.json"
LIFECYCLE_PATH = ROOT / "registry/lifecycle.json"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"GLAZE UI V1.2 Candidate validation failed: {message}")


def text(path: Path) -> str:
    req(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def rgba_channels(value: str) -> tuple[int, int, int, float]:
    match = re.fullmatch(
        r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*\)",
        value,
    )
    req(match is not None, f"expected rgba token, got {value!r}")
    assert match is not None
    r, g, b = (int(match.group(i)) for i in range(1, 4))
    alpha = float(match.group(4))
    req(all(0 <= channel <= 255 for channel in (r, g, b)), f"invalid rgba channel in {value!r}")
    req(0 <= alpha <= 1, f"invalid alpha in {value!r}")
    return r, g, b, alpha


def near_neutral(value: str, tolerance: int = 4) -> bool:
    r, g, b, _ = rgba_channels(value)
    return max(r, g, b) - min(r, g, b) <= tolerance


def main() -> None:
    tokens = json.loads(text(TOKEN_PATH))
    css = text(CSS_PATH)
    component_css = text(COMPONENT_CSS_PATH)
    system_shell_css = text(SYSTEM_SHELL_CSS_PATH)
    entrypoint = text(ENTRYPOINT_PATH)
    reference = text(REFERENCE_PATH)
    component_reference = text(COMPONENT_REFERENCE_PATH)
    system_shell_reference = text(SYSTEM_SHELL_REFERENCE_PATH)
    contract = text(CONTRACT_PATH)
    component_contract = json.loads(text(COMPONENT_CONTRACT_PATH))
    component_catalog = json.loads(text(COMPONENT_CATALOG_PATH))
    system_shell_contract = json.loads(text(SYSTEM_SHELL_CONTRACT_PATH))
    inherited_system_shell = json.loads(text(INHERITED_SYSTEM_SHELL_PATH))
    lifecycle = json.loads(text(LIFECYCLE_PATH))

    req(tokens.get("lifecycle") == "candidate", "token lifecycle must remain Candidate")
    req(tokens.get("stableBaseline") == "1.1.0", "Candidate must remain based on V1.1 Stable")
    req(tokens.get("currentStableToken") is False, "Candidate token must not claim Stable authority")
    req(
        tokens.get("governingRule") == "Neutral glass is the material. Color is an accent.",
        "governing visual rule drifted",
    )

    req(lifecycle.get("currentStable") == "1.1.0", "V1.2 Candidate must not replace V1.1 Stable authority")
    req(lifecycle.get("currentOfficial") == "1.1.0", "V1.2 Candidate must not replace current official version")
    req(lifecycle.get("activeCandidate") == "1.2.0-candidate", "V1.2 must be registered as the active Candidate")
    candidate_release = next(
        (
            item
            for item in lifecycle.get("releases", [])
            if isinstance(item, dict) and item.get("version") == "1.2.0-candidate"
        ),
        None,
    )
    req(candidate_release is not None, "V1.2 Candidate lifecycle record missing")
    assert candidate_release is not None
    req(candidate_release.get("status") == "candidate", "V1.2 lifecycle status must remain Candidate")
    req(candidate_release.get("consumerEligible") is False, "Candidate must not be consumer eligible")
    req(candidate_release.get("stableBaseline") == "1.1.0", "Candidate lifecycle Stable baseline drifted")
    req(candidate_release.get("contract") == "GLAZE_UI_V1_2_CANDIDATE.md", "Candidate lifecycle contract binding drifted")

    capabilities = lifecycle.get("capabilities", {})
    shell_capability = capabilities.get("frosted-neutral-system-shell", {})
    req(shell_capability.get("status") == "candidate", "System Shell Candidate capability must be registered")
    req(shell_capability.get("since") == "1.2.0-candidate", "System Shell capability version drifted")
    req(
        shell_capability.get("implementation") == "contracts/v1.2/system-shell-materials.candidate.json",
        "System Shell capability contract binding drifted",
    )
    req(
        shell_capability.get("webPreview") == "reference/v1.2/system-shell.html",
        "System Shell capability preview binding drifted",
    )

    materials = tokens.get("materials", {})
    for appearance in ("light", "dark", "deepDark"):
        role = materials.get(appearance)
        req(isinstance(role, dict), f"missing {appearance} material tokens")
        assert isinstance(role, dict)
        for key in ("baseGlass", "raisedGlass", "overlayGlass", "panelGlass"):
            value = role.get(key)
            req(isinstance(value, str), f"missing {appearance}.{key}")
            assert isinstance(value, str)
            req(near_neutral(value), f"{appearance}.{key} must remain chromatically neutral: {value}")

    chroma = tokens.get("chromaticMaterialPolicy", {})
    req(chroma.get("defaultChromaticMaterialTint") == 0, "default chromatic substrate tint must be zero")
    for key in (
        "tealAsBaseMaterialAllowed",
        "greenAsBaseMaterialAllowed",
        "aquaAsBaseMaterialAllowed",
        "amberAsBaseMaterialAllowed",
        "brandColorMayDefineSubstrate",
        "semanticColorMayDefineSubstrate",
    ):
        req(chroma.get(key) is False, f"{key} must remain false")

    hierarchy = tokens.get("hierarchyRules", {})
    req(hierarchy.get("depthBeforeHue") is True, "depth-before-hue invariant missing")
    req(hierarchy.get("nestedBackdropBlurDefaultAllowed") is False, "nested backdrop blur must remain disabled by default")
    req(hierarchy.get("dominantGlazeRegionsMax") == 1, "dominant Glaze budget changed")
    req(hierarchy.get("smallFloatingGlazeControlsMax") == 3, "floating Glaze budget changed")

    accessibility = tokens.get("accessibility", {})
    req(accessibility.get("reducedTransparency", {}).get("backdropBlur") == "off", "Reduced Transparency must disable blur")
    req(accessibility.get("forcedColors", {}).get("customMaterialPigmentation") == "off", "Forced Colors must disable custom material pigmentation")

    activation = 'html[data-glaze-version="1.1"][data-glaze-upgrade="v1.2-frosted-neutral"]'
    req(activation in css, "Candidate CSS activation selector missing")
    req("--glz11-tint-glaze-teal: transparent" in css, "V1.1 teal material tint is not neutralized")
    req("--glz11-tint-glaze-amber: transparent" in css, "V1.1 amber material tint is not neutralized")
    req("background-image: none" in css, "inherited chromatic background images are not explicitly removed")
    req("@media (forced-colors: active)" in css, "Forced Colors fallback missing")
    req('data-glz-transparency="reduced"' in css, "Reduced Transparency fallback missing")
    req("backdrop-filter: none" in css, "no-backdrop fallback missing")

    req('@import url("./glaze-v1.1.0.css")' in entrypoint, "Candidate entrypoint must inherit V1.1 Stable")
    req(
        '@import url("./glaze-v1.2-frosted-neutral.candidate.css")' in entrypoint,
        "Candidate entrypoint must import Frosted Neutral layer",
    )
    req(
        '@import url("./glaze-v1.2-components.candidate.css")' in entrypoint,
        "Candidate entrypoint must import component material expansion",
    )
    req(
        '@import url("./glaze-v1.2-system-shell.candidate.css")' in entrypoint,
        "Candidate entrypoint must import System Shell material expansion",
    )

    # The component-material contract must cover the exact inherited 32-component catalog.
    catalog_tiers = component_catalog.get("tiers", {})
    req(isinstance(catalog_tiers, dict), "V1 component catalog tiers missing")
    catalog_components: dict[str, str] = {}
    for tier, names in catalog_tiers.items():
        req(isinstance(names, list), f"catalog tier {tier!r} must be an array")
        for name in names:
            req(isinstance(name, str), f"catalog tier {tier!r} contains non-string component")
            req(name not in catalog_components, f"duplicate catalog component {name}")
            catalog_components[name] = tier
    req(component_catalog.get("componentCount") == 32, "inherited component catalog count must remain 32")
    req(len(catalog_components) == 32, "inherited component catalog must contain exactly 32 unique components")

    req(component_contract.get("product") == "GLAZE UI V1.2", "component material contract product mismatch")
    req(component_contract.get("version") == "1.2.0-candidate", "component material contract version mismatch")
    req(component_contract.get("lifecycle") == "candidate", "component material contract lifecycle mismatch")
    req(component_contract.get("stableBaseline") == "1.1.0", "component material contract baseline mismatch")
    req(
        component_contract.get("governingRule") == "Neutral glass is the material. Color is an accent.",
        "component material governing rule drifted",
    )
    component_rules = component_contract.get("rules", {})
    req(component_rules.get("readingSurfacesDefaultToGlass") is False, "reading surfaces must not default to glass")
    req(component_rules.get("consequentialDecisionSurfacesDefaultToGlass") is False, "decision surfaces must not default to glass")
    req(component_rules.get("nestedBackdropBlurDefaultAllowed") is False, "component contract must forbid default nested blur")
    req(component_rules.get("depthBeforeHue") is True, "component contract must preserve depth-before-hue")

    allowed_roles = set(component_contract.get("materialRoles", []))
    req(
        {"surface", "raised", "soft-glaze", "glaze", "deep-glaze", "live-glaze", "control-local", "inherited", "composite"}.issubset(allowed_roles),
        "component material roles incomplete",
    )
    components = component_contract.get("components", {})
    req(isinstance(components, dict), "component material mapping must be an object")
    req(set(components) == set(catalog_components), "component material mapping must exactly cover the inherited 32-component catalog")
    req(len(components) == 32, "component material mapping must contain exactly 32 components")

    for name, mapping in components.items():
        req(isinstance(mapping, dict), f"component material mapping for {name} must be an object")
        assert isinstance(mapping, dict)
        req(mapping.get("tier") == catalog_components[name], f"component tier drifted for {name}")
        default_material = mapping.get("defaultMaterial")
        req(default_material in allowed_roles, f"unknown default material role for {name}: {default_material}")
        targets = mapping.get("frostedTargets", [])
        req(isinstance(targets, list), f"frostedTargets for {name} must be an array")
        for target in targets:
            req(isinstance(target, dict), f"frosted target for {name} must be an object")
            assert isinstance(target, dict)
            req(isinstance(target.get("selector"), str) and target.get("selector"), f"frosted target selector missing for {name}")
            req(target.get("role") in allowed_roles, f"unknown frosted role for {name}: {target.get('role')}")

    for name in ("GlzCard", "GlzList", "GlzTable", "GlzDialog", "GlzAISuggestion", "GlzAIAnswer", "GlzSmartSummary"):
        req(
            components[name].get("defaultMaterial") not in {"soft-glaze", "glaze", "deep-glaze", "live-glaze"},
            f"{name} must remain readability/decision-first by default",
        )

    req(activation in component_css, "component Candidate CSS activation selector missing")
    for marker in (
        '.glz1-dock',
        '.glz1-sheet',
        '.glz1-search-panel',
        '.glz1-dialog',
        'Reading surfaces remain Solid/Raised',
        'must not add a second blur',
        '@supports not ((backdrop-filter: blur(1px))',
        '@media (forced-colors: active)',
        'data-glz-transparency="reduced"',
    ):
        req(marker in component_css, f"component Candidate CSS missing required marker {marker!r}")

    # System Shell specialization must preserve the exact inherited region set and budget.
    inherited_regions = inherited_system_shell.get("regions", [])
    req(isinstance(inherited_regions, list), "inherited System Shell regions must be an array")
    req(len(inherited_regions) == 5 and len(set(inherited_regions)) == 5, "inherited System Shell must retain five unique regions")
    shell_regions = system_shell_contract.get("regions", {})
    req(isinstance(shell_regions, dict), "V1.2 System Shell region mapping must be an object")
    req(set(shell_regions) == set(inherited_regions), "V1.2 System Shell mapping must exactly preserve inherited region keys")

    req(system_shell_contract.get("product") == "GLAZE UI V1.2", "System Shell Candidate product mismatch")
    req(system_shell_contract.get("version") == "1.2.0-candidate", "System Shell Candidate version mismatch")
    req(system_shell_contract.get("lifecycle") == "candidate", "System Shell Candidate lifecycle mismatch")
    req(system_shell_contract.get("stableBaseline") == "1.1.0", "System Shell Candidate baseline mismatch")
    req(
        system_shell_contract.get("inherits") == "contracts/system-shell/glaze-system-shell-v1.json",
        "System Shell Candidate inheritance binding drifted",
    )
    req(
        system_shell_contract.get("governingRule") == "Neutral glass is the material. Color is an accent.",
        "System Shell Candidate governing rule drifted",
    )

    inherited_budget = inherited_system_shell.get("materialBudget", {})
    shell_budget = system_shell_contract.get("materialBudget", {})
    req(
        shell_budget.get("dominantGlazePanels") == inherited_budget.get("dominantGlazePanels") == 1,
        "System Shell dominant Glaze budget must remain one",
    )
    req(
        shell_budget.get("smallFloatingGlazeControlsMax") == inherited_budget.get("smallFloatingGlazeControlsMax") == 3,
        "System Shell floating Glaze budget must remain three",
    )
    req(shell_budget.get("nestedBackdropBlurDefaultAllowed") is False, "System Shell Candidate must forbid default nested blur")

    workspace = shell_regions["workspace"]
    navigation = shell_regions["navigation"]
    search = shell_regions["universal-search"]
    control_center = shell_regions["control-center"]
    critical = shell_regions["critical-system"]
    req(workspace.get("defaultMaterial") == "surface" and workspace.get("backdropBlur") is False, "workspace must remain non-blurred Surface")
    req(navigation.get("persistentMaterial") == "surface", "persistent navigation must remain Surface")
    req(navigation.get("floatingMaterial") == "glaze", "floating navigation must use Glaze")
    req(search.get("entryMaterial") == "glaze" and search.get("panelMaterial") == "deep-glaze", "Universal Search material mapping drifted")
    req(search.get("nestedBackdropBlurDefaultAllowed") is False, "Universal Search nested blur must remain disabled")
    req(control_center.get("containerMaterial") == "deep-glaze", "Control Center must be Deep Glaze")
    req(control_center.get("tileMaterial") == "raised", "Control Center tiles must remain local Raised surfaces")
    req(control_center.get("nestedBackdropBlurDefaultAllowed") is False, "Control Center nested blur must remain disabled")
    req(critical.get("defaultMaterial") == "raised" and critical.get("backdropBlur") is False, "Critical System must remain non-blurred Raised")

    target_floors = inherited_system_shell.get("targetFloorsPx", {})
    control_center_contract = system_shell_contract.get("controlCenter", {})
    req(control_center_contract.get("minimumTargetPx") == target_floors.get("touch") == 48, "Control Center touch target floor drifted")
    req(
        control_center_contract.get("touchAssistanceTargetPx") == target_floors.get("touchAssistanceOrFarView") == 56,
        "Control Center assisted/far-view target floor drifted",
    )
    req(control_center_contract.get("tileState", {}).get("colorOnlyCommunicationAllowed") is False, "Control Center state must not depend on color alone")

    req(activation in system_shell_css, "System Shell Candidate CSS activation selector missing")
    for marker in (
        'data-glz-shell-region="workspace"',
        'data-glz-shell-region="navigation"',
        'data-glz-shell-region="control-center"',
        'data-glz-shell-region="universal-search"',
        'data-glz-shell-region="critical-system"',
        '.glz12-control-tile',
        'Critical System remains high-opacity',
        '200% text reflows controls',
        '@supports not ((backdrop-filter: blur(1px))',
        '@media (forced-colors: active)',
        'data-glz-transparency="reduced"',
    ):
        req(marker in system_shell_css, f"System Shell Candidate CSS missing required marker {marker!r}")

    req('data-glaze-upgrade="v1.2-frosted-neutral"' in reference, "reference does not activate Candidate")
    req("../../css/glaze-v1.2.0-candidate.css" in reference, "reference does not use Candidate entrypoint")
    req("Neutral glass is the material." in reference, "reference does not state the governing rule")
    req("Quick Settings" in reference, "reference must exercise a system-panel control surface")

    req('data-glaze-upgrade="v1.2-frosted-neutral"' in component_reference, "component gallery does not activate Candidate")
    req("../../css/glaze-v1.2.0-candidate.css" in component_reference, "component gallery does not use Candidate entrypoint")
    represented = re.findall(r'data-component="([^"]+)"', component_reference)
    req(len(represented) == 32, "component gallery must contain exactly 32 component samples")
    req(len(set(represented)) == 32, "component gallery must not duplicate component samples")
    req(set(represented) == set(catalog_components), "component gallery must represent every catalog component exactly once")

    req('data-glaze-upgrade="v1.2-frosted-neutral"' in system_shell_reference, "System Shell reference does not activate Candidate")
    req("../../css/glaze-v1.2.0-candidate.css" in system_shell_reference, "System Shell reference does not use Candidate entrypoint")
    represented_shell_regions = re.findall(r'data-glz-shell-region="([^"]+)"', system_shell_reference)
    req(len(represented_shell_regions) == 5, "System Shell reference must represent exactly five shell regions")
    req(len(set(represented_shell_regions)) == 5, "System Shell reference must not duplicate shell region markers")
    req(set(represented_shell_regions) == set(inherited_regions), "System Shell reference must represent every inherited region exactly once")
    req("Control Center" in system_shell_reference, "System Shell reference must exercise Control Center")
    req("Critical System" in system_shell_reference, "System Shell reference must exercise Critical System separation")

    req("Neutral glass is the material. Color is an accent." in contract, "Candidate contract governing rule missing")
    req("default material tint from teal, aqua, green, or amber is `0`" in contract, "Candidate contract substrate rule missing")
    req("V1.1 / 1.1.0" in contract, "Candidate contract Stable baseline missing")
    req("component-material contract" in contract, "Candidate contract must document component-material expansion")
    req("32-component" in contract, "Candidate contract must document exact catalog coverage")
    req("System Shell material expansion" in contract, "Candidate contract must document System Shell material expansion")
    req("five-region System Shell contract" in contract, "Candidate contract must preserve five-region System Shell authority")

    print("GLAZE UI V1.2 Frosted Neutral Candidate validated; 32-component and five-region System Shell material expansions are complete; V1.1 remains current Stable")


if __name__ == "__main__":
    main()
