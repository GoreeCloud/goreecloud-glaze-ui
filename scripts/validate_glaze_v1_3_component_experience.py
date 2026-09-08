#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Signature Components and Reference Suite workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.2.0"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
CONTRACT = "contracts/v1.3/component-experience.candidate.json"
RUNTIME = "js/glaze-v1.3-component-experience.candidate.mjs"
TESTS = "tests/glaze-v1.3-component-experience.test.mjs"
MANIFEST = "reference/v1.3/signature-components-and-compositions.json"
REFERENCE_HTML = "reference/v1.3/signature-components-and-compositions.html"
CATALOG = "contracts/components/v1/catalog.json"
V12_COMPONENT = "contracts/v1.2/component-experience.candidate.json"
V12_SIGNATURE = "contracts/v1.2/signature-components.candidate.json"
V12_COMPOSITION = "contracts/v1.2/composition-reference-library.candidate.json"
SYSTEM_SHELL = "contracts/v1.3/system-shell.candidate.json"
MULTI_PANE = "contracts/v1.3/multi-pane.candidate.json"
PERSONALIZATION = "contracts/v1.3/personalization.candidate.json"
ACCESSIBILITY = "contracts/v1.3/accessibility.candidate.json"
EXPECTED_COMPONENTS = ["GlzCapsule", "GlzMorphCard", "GlzSmartRail", "GlzAuroraSurface", "GlzUniversalSearch"]
EXPECTED_SCENES = ["home-dashboard", "data-heavy-administration", "settings", "file-browser", "search", "form", "detail-inspector", "media"]
EXPECTED_ENVIRONMENTS = ["compact", "medium", "expanded", "workspace", "farView", "wearable"]


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = [PLAN, CONTRACT, RUNTIME, TESTS, MANIFEST, REFERENCE_HTML, CATALOG, V12_COMPONENT, V12_SIGNATURE, V12_COMPOSITION, SYSTEM_SHELL, MULTI_PANE, PERSONALIZATION, ACCESSIBILITY, "VERSION", "registry/lifecycle.json"]
    for path in required:
        req((ROOT / path).is_file(), f"missing component/reference artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Signature Components + Reference Suite validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must remain 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "Phase 14 must not activate lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    for dep in ("system-shell-and-control-center", "personalization", "multi-pane-foldable-desktop"):
        req(workstreams.get(dep, {}).get("status") == "implemented-and-validated", f"Phase 14 requires validated dependency {dep}")
    req(workstreams.get("signature-components-and-reference-suite", {}).get("status") in {"implementation-in-progress", "implementation-complete-validation-pending", "implemented-and-validated"}, "Signature Components and Reference Suite workstream must be active or validated")

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "component-experience product mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "component-experience target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "component-experience lifecycle must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "component-experience contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "component-experience contract must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "component-experience must extend V1.2 Stable")
    req(contract.get("catalogAuthority") == CATALOG, "V1 component catalog must remain authoritative")
    req(set(contract.get("extends", [])) == {V12_COMPONENT, V12_SIGNATURE, V12_COMPOSITION, SYSTEM_SHELL, MULTI_PANE, PERSONALIZATION, ACCESSIBILITY}, "component-experience inheritance set mismatch")

    catalog = load(CATALOG)
    req(catalog.get("tiers", {}).get("signature") == EXPECTED_COMPONENTS, "canonical catalog Signature identities changed")
    components = contract.get("signatureComponents", {})
    req(list(components) == EXPECTED_COMPONENTS, "V1.3 Signature component identity/order mismatch")
    for component_id in EXPECTED_COMPONENTS:
        req(components.get(component_id, {}).get("v1IdentityPreserved") is True, f"{component_id} must preserve V1 identity")
    req(components["GlzCapsule"].get("criticalContentExclusiveProhibited") is True, "GlzCapsule may not exclusively carry critical content")
    req(components["GlzMorphCard"].get("durableReadingBackdropDependent") is False, "GlzMorphCard durable reading may not depend on backdrop")
    req(components["GlzSmartRail"].get("primaryNavigationOrderMayBePersonalized") is False, "GlzSmartRail primary order may not be personalized")
    req(components["GlzSmartRail"].get("currentStateDistinctFromFocus") is True, "GlzSmartRail current state must remain distinct from focus")
    req(components["GlzAuroraSurface"].get("semanticMeaningMayDependOnAtmosphere") is False, "GlzAuroraSurface atmosphere may not define semantic meaning")
    req(components["GlzUniversalSearch"].get("scopeMustBeVisible") is True, "GlzUniversalSearch scope must remain visible")
    req(components["GlzUniversalSearch"].get("generatedResultsDistinctFromSystemTruth") is True, "generated search results must remain distinct from system truth")
    req(components["GlzUniversalSearch"].get("destructiveActionRequiresConfirmation") is True, "destructive search actions require confirmation")
    req(components["GlzUniversalSearch"].get("nestedBackdropBlurAllowed") is False, "Universal Search nested backdrop blur must remain prohibited")

    v12_composition = load(V12_COMPOSITION)
    req(v12_composition.get("referenceCompositions") == EXPECTED_SCENES, "V1.2 canonical reference scene set changed")
    scenes = contract.get("referenceScenes", {})
    req(list(scenes) == EXPECTED_SCENES, "V1.3 reference scene identity/order mismatch")
    req(scenes["data-heavy-administration"].get("secondaryTaskValue") is True and scenes["data-heavy-administration"].get("inspectorTaskValue") is True, "administration scene requires secondary and inspector task value")
    req(scenes["detail-inspector"].get("inspectorTaskValue") is True, "detail-inspector scene requires inspector task value")

    reference_authority = contract.get("referenceAuthority", {})
    req(reference_authority.get("manifest") == MANIFEST, "reference manifest path mismatch")
    req(reference_authority.get("browserReference") == REFERENCE_HTML, "reference HTML path mismatch")
    for key in ("createsNewTokenAuthority", "createsNewMaterialAuthority", "createsNewSemanticAuthority", "createsNewLifecycleAuthority"):
        req(reference_authority.get(key) is False, f"reference suite authority rule must be false: {key}")

    environments = contract.get("environmentPolicy", {})
    req(environments.get("supported") == EXPECTED_ENVIRONMENTS, "environment set mismatch")
    req(environments.get("selectionAuthority") == "platform-or-layout-adapter", "environment selection must remain adapter-owned")
    req(environments.get("rawViewportWidthAuthority") is False, "raw viewport width may not be composition authority")
    req(environments.get("deviceBrandBreakpointsCanonical") is False, "device-brand breakpoints may not be canonical")
    req(environments.get("largerLayoutsMustAddTaskValue") is True, "larger layouts must add task value")

    rules = contract.get("compositionRules", {})
    for key in ("primaryTaskVisuallyDominant", "semanticOrderPreservedAcrossTransformation", "additionalPaneRequiresTaskValue", "responsiveTransformationRequired", "accessibilityMayRecomposePresentation", "accessibilityMayCollapsePaneCount", "focusDistinctFromCurrentOrSelectedState"):
        req(rules.get(key) is True, f"composition rule must be true: {key}")
    for key in ("durableReadingBackdropDependent", "personalizationMayChangeSemanticMeaning", "personalizationMayReplaceProductIdentity", "stateMayDependOnColorOnly", "motionMayDefineState"):
        req(rules.get(key) is False, f"composition rule must be false: {key}")

    accessibility = contract.get("accessibility", {})
    req(accessibility.get("minimumInteractiveTargetPx") == 48, "default component target floor must remain 48px")
    req(accessibility.get("touchAssistanceMinimumInteractiveTargetPx") == 56, "Touch Assistance target floor must remain 56px")
    req(accessibility.get("farViewMinimumInteractiveTargetPx") == 56, "far-view target floor must remain 56px")
    req(accessibility.get("textScalePercent") == 200, "reference text scale gate must remain 200 percent")
    req(accessibility.get("largeTextMayReducePaneCount") is True, "large text must be able to reduce pane count")
    req(accessibility.get("horizontalPageOverflowToPreserveCompositionProhibited") is True, "page overflow may not preserve composition")

    manifest = load(MANIFEST)
    req(manifest.get("product") == PRODUCT, "reference manifest product mismatch")
    req(manifest.get("releaseLifecycle") == "proposed", "reference manifest lifecycle must remain Proposed")
    req(manifest.get("referenceOnly") is True, "reference manifest must identify itself as reference-only")
    req([item.get("id") for item in manifest.get("signatureComponents", [])] == EXPECTED_COMPONENTS, "reference manifest component set mismatch")
    req([item.get("id") for item in manifest.get("referenceScenes", [])] == EXPECTED_SCENES, "reference manifest scene set mismatch")
    req(manifest.get("environments") == EXPECTED_ENVIRONMENTS, "reference manifest environments mismatch")
    manifest_rules = manifest.get("rules", {})
    for key in ("referenceSuiteCreatesNewTokenAuthority", "referenceSuiteCreatesNewMaterialAuthority", "referenceSuiteCreatesNewSemanticAuthority", "personalizationMayChangeSemanticMeaning", "durableReadingBackdropDependent", "rawViewportWidthAuthority", "deviceBrandBreakpointsCanonical", "complete32ComponentCoverageClaimed"):
        req(manifest_rules.get(key) is False, f"reference manifest rule must be false: {key}")
    for key in ("accessibilityMayRecomposePresentation", "additionalPaneRequiresTaskValue"):
        req(manifest_rules.get(key) is True, f"reference manifest rule must be true: {key}")

    html = (ROOT / REFERENCE_HTML).read_text(encoding="utf-8")
    req("../../css/glaze-v1.2.0.css" in html, "reference HTML must inherit the current Stable CSS entrypoint")
    req("glaze-v1.3.0-candidate" not in html, "reference HTML must not introduce V1.3 Candidate entrypoints")
    for component_id in EXPECTED_COMPONENTS:
        req(f'data-signature-component="{component_id}"' in html, f"reference HTML missing {component_id}")
    for scene_id in EXPECTED_SCENES:
        req(f'data-reference-scene="{scene_id}"' in html, f"reference HTML missing scene {scene_id}")
    req("glaze-v1.3-component-experience.candidate.mjs" in html, "reference HTML must use the Phase 14 resolver")
    req("fetch(" not in html, "reference HTML must not require network acquisition")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for dependency in ("glaze-v1.3-system-shell.candidate.mjs", "glaze-v1.3-multi-pane.candidate.mjs", "glaze-v1.3-personalization.candidate.mjs"):
        req(dependency in runtime, f"component resolver must compose {dependency}")
    for symbol in ("SIGNATURE_COMPONENT_IDS", "REFERENCE_SCENE_IDS", "resolveSignatureComponent", "resolveReferenceScene", "validateReferenceManifest", "componentExperienceCandidate"):
        req(symbol in runtime, f"component resolver missing API: {symbol}")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "innerWidth", "outerWidth", "localStorage", "sessionStorage", "indexedDB"):
        req(forbidden not in runtime, f"component resolver contains forbidden network/viewport/persistence primitive: {forbidden}")

    personalization = load(PERSONALIZATION)
    req(personalization.get("releaseLifecycle") == "proposed", "Personalization dependency must remain Proposed")
    req(personalization.get("consumerEligible") is False, "Personalization dependency must remain non-consumer-eligible")
    req(personalization.get("principle") == "Personalize expression, not truth or control semantics.", "Personalization principle changed")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in ("complete-32-component-v1.3-coverage", "native-signature-component-parity", "native-reference-scene-parity", "assistive-technology-human-acceptance", "human-optical-component-acceptance", "physical-device-component-acceptance", "production-component-performance-acceptance", "release-candidate", "stable", "consumer-conformance"):
        req(item in not_established, f"component/reference evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Signature Components + Reference Suite validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Signature Components + Reference Suite: PASS")
    print("Boundary: canonical Signature components and reference scenes compose validated V1.3 authorities without creating new token/material/semantic/lifecycle authority or claiming complete catalog, native, human, physical-device, production, release, or consumer acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
