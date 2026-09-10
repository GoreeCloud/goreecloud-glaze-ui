#!/usr/bin/env python3
"""Validate the Proposed GLAZE UI V1.3 Variable Responsive Typography workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
CURRENT_STABLE_VERSION = "1.3.0"
SOURCE_STABLE_VERSION = "1.2.0"
CONTRACT = "contracts/v1.3/typography.candidate.json"
TOKENS = "tokens/glaze-v1.3-type.candidate.json"
RUNTIME = "js/glaze-v1.3-typography.candidate.mjs"
TESTS = "tests/glaze-v1.3-typography.test.mjs"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
BASELINE = "tokens/glaze-v1.2-typography.candidate.json"


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def resolve_pointer(document: Any, pointer: str) -> Any:
    current = document
    for raw_part in pointer.lstrip("/").split("/"):
        if not raw_part:
            continue
        part = raw_part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    for path in (CONTRACT, TOKENS, RUNTIME, TESTS, PLAN, BASELINE, "VERSION", "registry/lifecycle.json"):
        req((ROOT / path).is_file(), f"missing responsive-typography artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Variable Responsive Typography validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == CURRENT_STABLE_VERSION, "VERSION must remain 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == CURRENT_STABLE_VERSION, "currentStable must remain 1.3.0")
    req(lifecycle.get("currentOfficial") == CURRENT_STABLE_VERSION, "currentOfficial must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "Responsive Typography must not activate release lifecycle Candidate")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    req(workstreams.get("contract-and-token-architecture", {}).get("status") == "implemented-and-validated", "Responsive Typography requires validated token architecture")
    req(
        workstreams.get("variable-responsive-typography", {}).get("status") in {
            "planned",
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "Responsive Typography workstream must use governed status vocabulary",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "typography product identity mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "typography target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "typography release lifecycle must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "typography artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "typography contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "typography contract must not be consumer eligible")
    req(contract.get("sourceStable") == SOURCE_STABLE_VERSION, "typography must preserve the V1.2 source baseline")
    req(contract.get("extends") == BASELINE, "typography inheritance mismatch")

    expected_roles = {"display", "title", "heading", "body", "label", "caption", "numeral"}
    semantic_roles = contract.get("semanticRoles", {})
    req(set(semantic_roles) == expected_roles, "semantic typography role set mismatch")
    for role, entry in semantic_roles.items():
        req(isinstance(entry, dict) and bool(entry.get("purpose")), f"semantic typography role {role!r} needs a purpose")
        req(isinstance(entry, dict) and bool(entry.get("sourceRole")), f"semantic typography role {role!r} needs a source role")

    expected_environments = {"compact", "medium", "expanded", "workspace", "farView", "wearable"}
    environments = contract.get("layoutEnvironments", {})
    req(set(environments) == expected_environments, "layout environment set mismatch")
    for environment, entry in environments.items():
        sizes = entry.get("roleSizeRem", {}) if isinstance(entry, dict) else {}
        req(set(sizes) == expected_roles, f"{environment} must define every semantic type role")
        for role, value in sizes.items():
            req(isinstance(value, (int, float)) and value > 0, f"{environment}/{role} type size must be positive")
    req(environments.get("compact", {}).get("roleSizeRem", {}).get("body", 0) >= 1.0, "compact body must retain the 1rem readable floor")
    req(environments.get("workspace", {}).get("roleSizeRem", {}).get("caption", 0) >= 0.75, "workspace caption must retain the 0.75rem floor")
    req(environments.get("farView", {}).get("roleSizeRem", {}).get("body", 0) >= 1.25, "far-view body must be intentionally distance-readable")
    req(environments.get("wearable", {}).get("roleSizeRem", {}).get("label", 0) >= 0.8125, "wearable labels must retain a readable floor")

    environment_rules = contract.get("environmentRules", {})
    req(environment_rules.get("uniformScaleOnly") is False, "environment typography must not be uniform scaling only")
    req(environment_rules.get("phoneTypographyIsScaledDesktopTypographyOnly") is False, "phone typography must not be scaled desktop only")
    req(environment_rules.get("farViewTypographyIsScaledPhoneTypographyOnly") is False, "far-view typography must not be scaled phone only")
    req(environment_rules.get("semanticRoleIdentityMustPersistAcrossEnvironments") is True, "semantic roles must persist across environments")
    req(environment_rules.get("environmentChangeMayAlterSemanticMeaning") is False, "environment changes may not alter semantic meaning")

    axes = contract.get("variableAxes", {})
    axis_map = axes.get("axes", {})
    req(set(axis_map) == {"weight", "width", "opticalSize", "grade"}, "variable axis semantic set mismatch")
    req({entry.get("cssTag") for entry in axis_map.values() if isinstance(entry, dict)} == {"wght", "wdth", "opsz", "GRAD"}, "variable axis CSS tag set mismatch")
    req(axes.get("runtimeMayAssumeAxisExists") is False, "runtime may not assume variable axes exist")
    req(axes.get("runtimeMustClampToDeclaredCapabilityRange") is True, "axis requests must clamp to adapter capabilities")
    req(axes.get("unsupportedAxisFallback") == "omit-axis-and-preserve-semantic-static-style", "unsupported-axis fallback mismatch")
    req(axes.get("remoteFontProbeAllowed") is False, "remote font probing must be prohibited")
    req(axes.get("continuousAutonomousAxisAnimationAllowed") is False, "continuous autonomous type-axis animation must be prohibited")

    expected_profiles = {"calm", "balanced", "expressive"}
    profiles = contract.get("expressionProfiles", {})
    req(set(profiles) == expected_profiles, "typography expression profile set mismatch")
    req(profiles.get("calm", {}).get("stateWeightDelta") == 0, "Calm typography must not force state weight expression")
    req(profiles.get("balanced", {}).get("stateWeightDelta") <= profiles.get("expressive", {}).get("stateWeightDelta", -1), "Balanced type expression must not exceed Expressive")
    req(profiles.get("balanced", {}).get("compressedWidthPercentRequest", 0) >= profiles.get("expressive", {}).get("compressedWidthPercentRequest", 101), "Expressive width request may be stronger but not inverted")

    state_use = contract.get("stateUse", {})
    req(state_use.get("stateMayChangeSemanticRole") is False, "state-driven type may not change semantic role")
    req(state_use.get("typeMayBeOnlyStateSignal") is False, "type must not become the only state signal")
    req(state_use.get("continuousWobblePulseOrMorphAllowed") is False, "continuous type wobble/pulse/morph must remain prohibited")

    accessibility = contract.get("accessibility", {})
    req(accessibility.get("largeTextReferencePercent") == 200, "large-text reference must remain 200 percent")
    req(accessibility.get("largeTextDisablesWidthCompression") is True, "large text must disable width compression")
    req(accessibility.get("largeTextMayNotBeCounteractedByNegativeScaleOrCondensation") is True, "large text must not be counteracted by condensation")
    req(accessibility.get("reflowMustNotDependOnVariableFontAvailability") is True, "reflow must work without variable fonts")
    precedence = accessibility.get("precedence", [])
    req(precedence[:2] == ["platform-accessibility", "large-text-and-reflow"], "accessibility and large-text precedence must lead typography resolution")
    req("expression" in precedence and precedence.index("large-text-and-reflow") < precedence.index("expression"), "large text must outrank expression")

    font_policy = contract.get("fontSourcePolicy", {})
    req(font_policy.get("default") == "system-platform-native-first", "font source default must remain platform-native first")
    req(font_policy.get("remoteRuntimeFontDependencyAllowed") is False, "remote runtime font dependency must be prohibited")
    req(font_policy.get("thirdPartyRuntimeFontDeliveryAllowed") is False, "third-party runtime font delivery must be prohibited")
    req(font_policy.get("runtimeNetworkFetchAllowed") is False, "typography runtime network fetch must be prohibited")

    token = load(TOKENS)
    req(token.get("product") == PRODUCT, "typography token product mismatch")
    req(token.get("releaseLifecycle") == "proposed", "typography tokens must remain Proposed")
    req(token.get("lifecycleAuthority") is False, "typography tokens must not carry lifecycle authority")
    req(token.get("consumerEligible") is False, "typography tokens must not be consumer eligible")
    req(token.get("namespace") == "typography", "typography token namespace mismatch")
    req(set(token.get("semanticTokens", {})) == {f"type.{role}" for role in expected_roles}, "typography semantic token coverage mismatch")

    implementations = token.get("implementationValues", {})
    for role in expected_roles:
        entry = implementations.get(role, {})
        source = entry.get("source")
        pointer = entry.get("pointer")
        req(source == BASELINE, f"{role} must inherit from the V1.2 typography authority")
        if source == BASELINE and pointer:
            try:
                resolve_pointer(load(source), pointer)
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                errors.append(f"typography token pointer {pointer!r} does not resolve in {source}: {exc}")

    token_axes = implementations.get("variableAxes", {})
    req(token_axes.get("status") == "implemented-candidate-runtime", "variable axis token implementation must be established")
    req(token_axes.get("capabilityModel") == "adapter-declared-local-font-axis-capabilities", "variable axis capability model mismatch")
    req(set(token_axes.get("allowedAxes", {}).values()) == {"wght", "wdth", "opsz", "GRAD"}, "token axis tag set mismatch")

    token_environment = implementations.get("layoutEnvironmentAdaptation", {})
    req(token_environment.get("status") == "implemented-candidate-runtime", "layout environment type adaptation must be established")
    req(token_environment.get("uniformScaleOnly") is False, "token environment adaptation may not be uniform scaling only")
    contract_sizes = {name: entry.get("roleSizeRem", {}) for name, entry in environments.items()}
    req(token_environment.get("roleSizeRem") == contract_sizes, "typography contract and token environment values drifted")

    token_state = implementations.get("stateDrivenAdjustments", {})
    req(token_state.get("status") == "implemented-candidate-runtime", "state-driven type adjustments must be established")
    req(token_state.get("expressionProfiles") == profiles, "typography contract and token expression values drifted")

    rules = token.get("rules", {})
    for key in (
        "semanticHierarchyBeforeRawFontValues",
        "variableAxisChangesMustBeRestrained",
        "variableAxisCapabilityMustBeDeclaredByAdapter",
        "variableAxisRequestsMustClampToDeclaredRange",
        "unsupportedVariableAxesMustFallBackToStaticTypography",
        "largeTextAndReflowOverrideExpression",
        "largeTextDisablesWidthCompression",
        "rtlLogicalAlignmentRequired",
    ):
        req(rules.get(key) is True, f"typography token rule must be true: {key}")
    for key in (
        "continuousWobblePulseOrMorphAllowed",
        "remoteRuntimeFontDependencyAllowed",
        "phoneTypographyIsScaledDesktopTypographyOnly",
        "farViewTypographyIsScaledPhoneTypographyOnly",
        "semanticTokensMayContainRawFontValues",
    ):
        req(rules.get(key) is False, f"typography token rule must be false: {key}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "new FontFace(", "document.fonts.add"):
        req(forbidden not in runtime, f"typography runtime must remain local-only; forbidden network/font-loading primitive found: {forbidden}")
    for symbol in ("resolveTypographyEnvironment", "resolveTypography", "applyTypography", "responsiveTypographyCandidate"):
        req(symbol in runtime, f"typography runtime missing required API: {symbol}")
    for tag in ("wght", "wdth", "opsz", "GRAD"):
        req(tag in runtime, f"typography runtime missing governed variable-axis tag: {tag}")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in (
        "specific-variable-font-family-authority",
        "platform-font-axis-calibration",
        "human-readability-acceptance",
        "assistive-technology-acceptance",
        "physical-device-rendering-acceptance",
        "far-view-physical-distance-acceptance",
        "release-candidate",
        "stable",
        "consumer-conformance",
    ):
        req(item in not_established, f"typography evidence boundary must leave {item!r} unestablished")

    if errors:
        print("GLAZE UI V1.3 Variable Responsive Typography validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Variable Responsive Typography: PASS")
    print("Boundary: V1.3.0 remains current Stable; semantic environment-aware typography preserves its V1.2 source baseline while font-family, human, physical-device, V1.3.1, and consumer acceptance claims remain unestablished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
