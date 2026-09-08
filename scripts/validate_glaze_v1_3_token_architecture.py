#!/usr/bin/env python3
"""Validate the GLAZE UI V1.3 Adaptive Resonance token architecture workstream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = "1.2.0"
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
CONTRACT_PATH = "contracts/v1.3/adaptive-resonance.candidate.json"
TOKEN_PATHS = {
    "color": "tokens/glaze-v1.3-color.candidate.json",
    "material": "tokens/glaze-v1.3-material.candidate.json",
    "shape": "tokens/glaze-v1.3-shape.candidate.json",
    "typography": "tokens/glaze-v1.3-type.candidate.json",
    "motion": "tokens/glaze-v1.3-motion.candidate.json",
    "layout": "tokens/glaze-v1.3-layout.candidate.json",
}
EXPECTED_NAMESPACES = {
    "color",
    "material",
    "shape",
    "typography",
    "motion",
    "layout",
    "navigation",
    "state",
    "accessibility",
    "personalization",
    "platform",
}


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer in ("", "/"):
        return document
    current = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = [CONTRACT_PATH, *TOKEN_PATHS.values(), "VERSION", "registry/lifecycle.json"]
    for path in required:
        req((ROOT / path).is_file(), f"missing required token architecture artifact: {path}")

    if errors:
        print("GLAZE UI V1.3 token architecture validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must remain 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "token architecture must not activate V1.3 Candidate")

    contract = load(CONTRACT_PATH)
    req(contract.get("product") == PRODUCT, "architecture product identity mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "architecture releaseLifecycle must remain proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "unexpected architecture artifact lifecycle")
    req(contract.get("lifecycleAuthority") is False, "architecture artifact must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "architecture artifact must not be consumer eligible")
    req(contract.get("sourceStable") == STABLE_VERSION, "architecture sourceStable must be 1.2.0")
    req(set(contract.get("semanticNamespaces", [])) == EXPECTED_NAMESPACES, "semantic namespace set is incomplete or unexpected")

    principles = contract.get("principles", {})
    for key in (
        "semanticTokensBeforeImplementationValues",
        "semanticAndImplementationLayersMustRemainDistinct",
        "oneOwnerPerTokenNamespace",
        "accessibilityOutranksExpression",
        "semanticTruthCannotBePersonalizedAway",
        "productIdentityCannotBeErasedByUserPersonalization",
        "effectsDegradeBeforeCorrectness",
        "v1_2CompatibilityRemainsValidUntilExplicitAdoption",
        "candidateFilenameDoesNotActivateReleaseCandidate",
    ):
        req(principles.get(key) is True, f"architecture principle must be true: {key}")

    layer_contract = contract.get("layerContract", {})
    req(layer_contract.get("semanticTokens", {}).get("mayContainRawPlatformValues") is False, "semantic tokens may not contain raw platform values")
    req(layer_contract.get("componentBindings", {}).get("mayBypassSemanticTokens") is False, "component bindings may not bypass semantic tokens")

    profiles = contract.get("profileAxes", {})
    req(profiles.get("clarity", {}).get("values") == ["clear", "balanced", "dense"], "clarity axis must preserve V1.2 Clear/Balanced/Dense")
    req(profiles.get("expression", {}).get("values") == ["calm", "balanced", "expressive"], "expression axis must be Calm/Balanced/Expressive")
    req(profiles.get("expression", {}).get("default") == "balanced", "Balanced expression must be default")
    req(profiles.get("independent") is True, "clarity and expression axes must remain independent")
    req(profiles.get("accessibilityOverridesBoth") is True, "accessibility must override clarity and expression")

    architecture_artifacts = set(contract.get("architectureArtifacts", []))
    req(architecture_artifacts == set(TOKEN_PATHS.values()), "architecture artifact list must match the six V1.3 token category files")

    owners = contract.get("tokenOwners", {})
    for namespace, path in TOKEN_PATHS.items():
        owner = owners.get(namespace, {})
        req(owner.get("status") == "v1.3-architecture-established", f"{namespace} ownership must be architecture-established")
        req(owner.get("owner") == path, f"{namespace} owner path mismatch")

    for namespace, path in TOKEN_PATHS.items():
        data = load(path)
        req(data.get("product") == PRODUCT, f"{path}: product identity mismatch")
        req(data.get("releaseLifecycle") == "proposed", f"{path}: releaseLifecycle must remain proposed")
        req(data.get("artifactLifecycle") == "implementation-candidate-artifact", f"{path}: artifact lifecycle mismatch")
        req(data.get("lifecycleAuthority") is False, f"{path}: must not carry lifecycle authority")
        req(data.get("consumerEligible") is False, f"{path}: must not be consumer eligible")
        req(data.get("sourceStable") == STABLE_VERSION, f"{path}: sourceStable must be 1.2.0")
        req(data.get("namespace") == namespace, f"{path}: namespace mismatch")

        semantic = data.get("semanticTokens")
        implementation = data.get("implementationValues")
        req(isinstance(semantic, dict) and bool(semantic), f"{path}: semanticTokens must be a non-empty object")
        req(isinstance(implementation, dict) and bool(implementation), f"{path}: implementationValues must be a non-empty object")
        if not isinstance(semantic, dict) or not isinstance(implementation, dict):
            continue

        for token_name, token in semantic.items():
            req(token_name.startswith(namespace + ".") or (namespace == "typography" and token_name.startswith("type.")), f"{path}: semantic token outside namespace: {token_name}")
            req(isinstance(token, dict), f"{path}: semantic token {token_name} must be an object")
            if not isinstance(token, dict):
                continue
            implementation_key = token.get("implementation")
            req(isinstance(implementation_key, str), f"{path}: semantic token {token_name} must reference implementation by key")
            if isinstance(implementation_key, str):
                req(implementation_key in implementation, f"{path}: semantic token {token_name} references missing implementation {implementation_key}")
            req("value" not in token, f"{path}: semantic token {token_name} must not embed raw value")

        for key, implementation_entry in implementation.items():
            if not isinstance(implementation_entry, dict):
                errors.append(f"{path}: implementation entry {key} must be an object")
                continue
            source = implementation_entry.get("source")
            pointer = implementation_entry.get("pointer")
            if source is not None:
                source_path = ROOT / source
                req(source_path.is_file(), f"{path}: implementation source does not exist: {source}")
                if source_path.is_file() and pointer is not None:
                    try:
                        resolve_pointer(load(source), pointer)
                    except (KeyError, IndexError, ValueError, TypeError) as exc:
                        errors.append(f"{path}: pointer {pointer!r} does not resolve in {source}: {exc}")
            else:
                req("status" in implementation_entry, f"{path}: implementation entry {key} needs source or explicit status")

    color = load(TOKEN_PATHS["color"])
    req(color.get("authorities") == [
        "neutral-material-palette",
        "user-accent-palette",
        "product-identity-palette",
        "semantic-palette",
        "context-palette",
    ], "color architecture must define all five V1.3 color authorities")
    req(color.get("rules", {}).get("personalizationMayRedefineSemanticRoles") is False, "personalization must not redefine semantic roles")
    req(color.get("rules", {}).get("personalizationMayEraseProductIdentity") is False, "personalization must not erase product identity")

    shape = load(TOKEN_PATHS["shape"])
    expected_shape_tokens = {
        "shape.container",
        "shape.containerInner",
        "shape.control",
        "shape.controlInset",
        "shape.overlay",
        "shape.overlayInner",
    }
    req(expected_shape_tokens.issubset(shape.get("semanticTokens", {})), "shape architecture is missing required concentric semantic roles")

    if errors:
        print("GLAZE UI V1.3 token architecture validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Adaptive Resonance token architecture: PASS")
    print("Boundary: six semantic token categories established; later adaptive runtimes remain unestablished; V1.2 remains Stable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
