#!/usr/bin/env python3
"""Validate the GLAZE UI V1.3 Migration and Consumer Boundary control plane."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
CURRENT_STABLE_VERSION = "1.3.0"
SOURCE_STABLE_VERSION = "1.2.0"
PLAN = "contracts/v1.3/adaptive-resonance.plan.json"
CONTRACT = "contracts/v1.3/migration.candidate.json"
SCHEMA = "contracts/v1.3/consumer-adoption-record.schema.json"
RUNTIME = "js/glaze-v1.3-migration.candidate.mjs"
TESTS = "tests/glaze-v1.3-migration.test.mjs"
GUIDE = "MIGRATION_V1_2_TO_V1_3.md"
REGISTRY = "consumers/registry.json"
V12_MIGRATION = "contracts/v1.2/migration.candidate.json"
DEPENDENCIES = {
    "accessibility-and-resilience": "contracts/v1.3/accessibility.candidate.json",
    "signature-components-and-reference-suite": "contracts/v1.3/component-experience.candidate.json",
}
EXPECTED_EVIDENCE = [
    "rendered-or-native",
    "interaction",
    "accessibility",
    "responsive-form-factor",
    "platform-integration",
    "product-workflows",
    "performance",
    "production-approval",
]
EXPECTED_STATES = [
    "evaluation-only",
    "blocked",
    "ready-for-consumer-acceptance",
    "eligible-after-independent-acceptance",
]


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    required = [
        PLAN,
        CONTRACT,
        SCHEMA,
        RUNTIME,
        TESTS,
        GUIDE,
        REGISTRY,
        V12_MIGRATION,
        "ADOPTION.md",
        "CONFORMANCE.md",
        "CONSUMERS.md",
        *DEPENDENCIES.values(),
        "VERSION",
        "registry/lifecycle.json",
    ]
    for path in required:
        req((ROOT / path).is_file(), f"missing migration artifact or dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Migration and Consumer Boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req(
        (ROOT / "VERSION").read_text(encoding="utf-8").strip() == CURRENT_STABLE_VERSION,
        "VERSION must remain 1.3.0",
    )
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == CURRENT_STABLE_VERSION, "currentStable must remain 1.3.0")
    req(lifecycle.get("currentOfficial") == CURRENT_STABLE_VERSION, "currentOfficial must remain 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "migration work must not activate a lifecycle Candidate")
    req(lifecycle.get("plannedNext") == "1.3.1-candidate", "plannedNext must retain the governed V1.3.1 candidate line")

    consumer_registry = load(REGISTRY)
    req(consumer_registry.get("officialBaseline") == CURRENT_STABLE_VERSION, "consumer registry officialBaseline must be 1.3.0")
    req(consumer_registry.get("requiredConsumerVersion") == CURRENT_STABLE_VERSION, "live consumers must require current Stable 1.3.0")
    req(consumer_registry.get("enforcement", {}).get("officialCurrentRequired") is True, "consumer registry must require the official current release")
    req(consumer_registry.get("enforcement", {}).get("productionExceptionsAllowed") is False, "consumer registry production exceptions must remain prohibited")
    for item in consumer_registry.get("consumers", []):
        req(item.get("requiredTargetVersion") == CURRENT_STABLE_VERSION, f"consumer {item.get('name')!r} must target current Stable 1.3.0")

    plan = load(PLAN)
    workstreams = {item.get("id"): item for item in plan.get("workstreams", [])}
    for dep in DEPENDENCIES:
        req(workstreams.get(dep, {}).get("status") == "implemented-and-validated", f"Migration requires validated dependency {dep}")
    req(
        workstreams.get("migration-and-consumer-boundary", {}).get("status") in {
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "Migration and Consumer Boundary workstream must be active or validated",
    )
    req(
        workstreams.get("fresh-v1.3-qualification", {}).get("status") in {
            "planned",
            "implementation-in-progress",
            "implementation-complete-validation-pending",
            "implemented-and-validated",
        },
        "fresh qualification status must remain within the governed V1.3 workstream vocabulary",
    )

    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "migration product mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "migration source target mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "migration source artifact lifecycle must preserve Proposed provenance")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "migration artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "migration contract must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "candidate-named migration source artifact must remain non-consumer-eligible")
    req(contract.get("sourceStable") == SOURCE_STABLE_VERSION, "migration source provenance must extend V1.2 Stable")

    extends = set(contract.get("extends", []))
    for path in [V12_MIGRATION, "ADOPTION.md", "CONFORMANCE.md", "CONSUMERS.md", REGISTRY, *DEPENDENCIES.values()]:
        req(path in extends, f"migration inheritance missing {path}")

    live = contract.get("liveAuthority", {})
    req(live.get("currentStable") == CURRENT_STABLE_VERSION, "migration live Stable boundary mismatch")
    req(live.get("currentOfficial") == CURRENT_STABLE_VERSION, "migration live official boundary mismatch")
    req(live.get("requiredConsumerVersion") == CURRENT_STABLE_VERSION, "migration live consumer version boundary mismatch")
    req(live.get("consumerRegistry") == REGISTRY, "migration consumer registry authority mismatch")
    for key in (
        "v1_3MayChangeLiveConsumerTargetInThisWorkstream",
        "v1_3MayChangeVersionFileInThisWorkstream",
        "v1_3MayChangeLifecycleRegistryInThisWorkstream",
        "v1_3CandidateEntrypointMayBeCreatedInThisWorkstream",
    ):
        req(live.get(key) is False, f"migration source workstream must not independently mutate lifecycle authority: {key}")

    evaluation = contract.get("evaluationBoundary", {})
    req(evaluation.get("proposedOrCandidateEvaluation") == "explicit-non-production-opt-in-only", "historical pre-Stable evaluation boundary changed unexpectedly")
    for key in (
        "productionMigrationRequiresLifecycleEligibleRelease",
        "productionMigrationRequiresConsumerEligibleRelease",
        "productionMigrationRequiresExactDesignSystemAnchor",
        "productionMigrationRequiresExactConsumerRevision",
    ):
        req(evaluation.get(key) is True, f"migration requirement must be true: {key}")
    for key in (
        "sharedDesignSystemEvidenceGrantsConsumerConformance",
        "importedTokensOrStylesGrantConformance",
        "versionLabelChangeGrantsConformance",
        "candidateArtifactNameGrantsLifecycleEligibility",
    ):
        req(evaluation.get(key) is False, f"migration evidence shortcut must be false: {key}")

    evidence = contract.get("consumerEvidence", {})
    req(evidence.get("requiredRecordSchema") == SCHEMA, "consumer adoption schema path mismatch")
    req(evidence.get("evidenceCategories") == EXPECTED_EVIDENCE, "consumer evidence category set mismatch")
    for key in (
        "repositoryLocalRequired",
        "exactRevisionRequired",
        "missingApplicableEvidenceFailsClosed",
        "staleEvidenceFailsClosed",
        "unsupportedOrUnvalidatedPlatformProductionBlocked",
        "truthDomainAuthorityMustRemainWithOwningSystem",
    ):
        req(evidence.get(key) is True, f"consumer evidence rule must be true: {key}")

    evaluator = contract.get("readinessEvaluator", {})
    req(evaluator.get("runtime") == RUNTIME, "migration runtime path mismatch")
    req(evaluator.get("failClosed") is True, "migration readiness evaluator must fail closed")
    req(evaluator.get("resultStates") == EXPECTED_STATES, "migration readiness states mismatch")
    for key in ("canMutateConsumerRepository", "canMutateLifecycle", "canGrantConformance", "canGrantProductionApproval"):
        req(evaluator.get(key) is False, f"migration evaluator capability must remain false: {key}")

    rollback = contract.get("rollback", {})
    for key in (
        "lastKnownGoodConsumerIntegrationRequired",
        "rollbackRevisionMustBeRecordedBeforeProductionMigration",
        "rollbackMustBeRepositoryLocal",
        "consumerMustVerifyNoDataMigrationAssumption",
        "independentlyReversible",
    ):
        req(rollback.get(key) is True, f"rollback rule must be true: {key}")
    req(rollback.get("rollbackMayRewriteImmutableDesignSystemHistory") is False, "rollback may not rewrite immutable design-system history")

    truth = contract.get("truthDomains", {})
    req(truth.get("glazeUiAuthority") == "presentation-and-interaction-contract", "Glaze UI truth-domain scope mismatch")
    req(truth.get("presentationMayManufactureUnderlyingTruth") is False, "presentation may not manufacture underlying truth")
    req(truth.get("presentationMayStrengthenUnverifiedSecurityOrPrivacyClaims") is False, "presentation may not strengthen unverified security/privacy claims")

    rollout = contract.get("laterRollout", {})
    req(rollout.get("automatic") is False, "consumer rollout may not be automatic")
    req(rollout.get("requiresStablePromotionFirst") is True, "rollout policy must preserve Stable-first requirement")
    req(rollout.get("eachConsumerMustPassIndependently") is True, "every consumer must pass independently")
    req(rollout.get("waveEvidenceMaySubstituteForConsumerEvidence") is False, "wave evidence may not substitute for consumer evidence")
    req([item.get("id") for item in rollout.get("waves", [])] == ["wave-1", "wave-2", "wave-3"], "rollout wave order mismatch")

    schema = load(SCHEMA)
    req(schema.get("type") == "object", "consumer adoption schema root must be object")
    req(schema.get("additionalProperties") is False, "consumer adoption schema must fail closed on unknown top-level fields")
    required_schema_fields = set(schema.get("required", []))
    for field in (
        "schemaVersion",
        "consumerName",
        "repository",
        "consumerRevision",
        "designSystemVersion",
        "designSystemRevision",
        "supportedPlatforms",
        "evidence",
        "rollback",
        "productionApproval",
    ):
        req(field in required_schema_fields, f"consumer adoption schema missing required field {field}")
    props = schema.get("properties", {})
    req(props.get("consumerRevision", {}).get("pattern") == "^[0-9a-f]{40}$", "consumer revision schema must require exact lowercase SHA-40")
    req(props.get("designSystemRevision", {}).get("pattern") == "^[0-9a-f]{40}$", "design-system revision schema must require exact lowercase SHA-40")
    evidence_required = set(props.get("evidence", {}).get("required", []))
    for field in ("renderedOrNative", "interaction", "accessibility", "responsiveFormFactor", "platformIntegration", "productWorkflows", "performance"):
        req(field in evidence_required, f"consumer adoption schema missing evidence field {field}")

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for symbol in (
        "MIGRATION_EVIDENCE_CATEGORIES",
        "validateConsumerAdoptionRecord",
        "evaluateConsumerMigration",
        "migrationCandidate",
    ):
        req(symbol in runtime, f"migration runtime missing API: {symbol}")
    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "sendBeacon",
        "WebSocket(",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "child_process",
        "exec(",
        "spawn(",
    ):
        req(forbidden not in runtime, f"migration runtime contains forbidden network/persistence/process primitive: {forbidden}")
    req("conformanceGranted: false" in runtime, "migration runtime must never grant conformance")
    req("release.lifecycle === 'stable'" in runtime, "production eligibility must require Stable lifecycle")
    req("release.consumerEligible" in runtime, "production eligibility must require consumer-eligible release")

    guide = (ROOT / GUIDE).read_text(encoding="utf-8")
    for phrase in (
        "**Status:** Active Stable migration control plane",
        "**Previous Stable baseline:** GLAZE UI V1.2 / `1.2.0`",
        "**Current Stable authority:** GLAZE UI V1.3 — Adaptive Resonance / `1.3.0`",
        "**Current required consumer target:** GLAZE UI V1.3 / `1.3.0`",
        "does not automatically grant conformance or production approval",
        "No wave is automatic.",
        "V1.2.0 remains available as the immediately preceding rollback baseline",
    ):
        req(phrase in guide, f"migration guide missing required post-promotion boundary text: {phrase}")
    req("glaze-v1.3.0-candidate.css" not in guide, "migration guide must not instruct use of a V1.3 Candidate release CSS entrypoint")
    req("glaze-v1.3.0-candidate.mjs" not in guide, "migration guide must not instruct use of a V1.3 Candidate release runtime entrypoint")

    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    for item in (
        "automatic-consumer-v1.3-migration",
        "automatic-consumer-v1.3-conformance",
        "automatic-consumer-v1.3-production-eligibility",
        "retroactive-v1.3-lifecycle-promotion-evidence",
        "native-platform-consumer-acceptance",
        "assistive-technology-consumer-acceptance",
        "physical-device-consumer-acceptance",
        "production-performance-consumer-acceptance",
        "cross-repository-rollout-execution",
    ):
        req(item in not_established, f"migration evidence boundary must leave {item!r} unestablished")

    req(not (ROOT / "css/glaze-v1.3.0-candidate.css").exists(), "migration control plane must not create a V1.3 Candidate CSS release entrypoint")
    req(not (ROOT / "js/glaze-v1.3.0-candidate.mjs").exists(), "migration control plane must not create a V1.3 Candidate runtime release entrypoint")

    if errors:
        print("GLAZE UI V1.3 Migration and Consumer Boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Migration and Consumer Boundary: PASS")
    print("Boundary: V1.3.0 is current Stable and required for consumers; migration remains repository-local, fail-closed, independently accepted, and incapable of granting downstream conformance or production approval by itself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
