#!/usr/bin/env python3
"""Validate the active GLAZE UI V1.3 Stable migration and consumer boundary."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "GLAZE UI V1.3 — Adaptive Resonance"
STABLE_VERSION = "1.3.0"
CONTRACT = "contracts/v1.3/migration.candidate.json"
SCHEMA = "contracts/v1.3/consumer-adoption-record.schema.json"
RUNTIME = "js/glaze-v1.3-migration.candidate.mjs"
TESTS = "tests/glaze-v1.3-migration.test.mjs"
GUIDE = "MIGRATION_V1_2_TO_V1_3.md"
REGISTRY = "consumers/registry.json"
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
        CONTRACT,
        SCHEMA,
        RUNTIME,
        TESTS,
        GUIDE,
        REGISTRY,
        "CONSUMERS.md",
        "acceptance/v1.3-stable.md",
        "acceptance/v1.3.1-hardening.md",
        "tokens/glaze-v1.3.json",
        "js/glaze-v1.3.0.mjs",
        "VERSION",
        "registry/lifecycle.json",
    ]
    for path in required:
        req((ROOT / path).is_file(), f"missing migration artifact or Stable dependency: {path}")

    if errors:
        print("GLAZE UI V1.3 Migration and Consumer Boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    req((ROOT / "VERSION").read_text(encoding="utf-8").strip() == STABLE_VERSION, "VERSION must be 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE_VERSION, "currentStable must be 1.3.0")
    req(lifecycle.get("currentOfficial") == STABLE_VERSION, "currentOfficial must be 1.3.0")
    req(lifecycle.get("officialProductLabel") == PRODUCT, "current product label mismatch")
    req(lifecycle.get("activeCandidate") is None, "Stable release must not retain an active Candidate")
    req(lifecycle.get("plannedNext") == "1.3.1", "plannedNext must be 1.3.1 hardening")

    consumer_registry = load(REGISTRY)
    req(consumer_registry.get("officialBaseline") == STABLE_VERSION, "consumer registry officialBaseline must be 1.3.0")
    req(consumer_registry.get("requiredConsumerVersion") == STABLE_VERSION, "live consumers must require 1.3.0")
    req(consumer_registry.get("officialProductLabel") == PRODUCT, "consumer registry product label mismatch")
    req(consumer_registry.get("enforcement", {}).get("officialCurrentRequired") is True, "consumer registry must require the official current release")
    req(consumer_registry.get("enforcement", {}).get("productionExceptionsAllowed") is False, "consumer registry production exceptions must remain prohibited")
    for item in consumer_registry.get("consumers", []):
        req(item.get("requiredTargetVersion") == STABLE_VERSION, f"consumer {item.get('name')!r} must require 1.3.0")
        req(item.get("productionEligible") is False, f"consumer {item.get('name')!r} must not receive product production eligibility from Glaze")

    # The migration contract/runtime retain their historical `.candidate` source-stage
    # names and pre-promotion policy fixture values. They are policy artifacts, not
    # current lifecycle authority. Their fail-closed consumer rules remain binding.
    contract = load(CONTRACT)
    req(contract.get("product") == PRODUCT, "migration product mismatch")
    req(contract.get("targetVersion") == "1.3.0-candidate", "historical migration target fixture mismatch")
    req(contract.get("releaseLifecycle") == "proposed", "historical migration lifecycle fixture must remain Proposed")
    req(contract.get("artifactLifecycle") == "implementation-candidate-artifact", "migration artifact lifecycle mismatch")
    req(contract.get("lifecycleAuthority") is False, "migration policy artifact must not carry lifecycle authority")
    req(contract.get("consumerEligible") is False, "historical migration policy fixture must not itself grant consumer eligibility")

    evaluation = contract.get("evaluationBoundary", {})
    for key in (
        "productionMigrationRequiresLifecycleEligibleRelease",
        "productionMigrationRequiresConsumerEligibleRelease",
        "productionMigrationRequiresExactDesignSystemAnchor",
        "productionMigrationRequiresExactConsumerRevision",
    ):
        req(evaluation.get(key) is True, f"migration requirement must remain true: {key}")
    for key in (
        "sharedDesignSystemEvidenceGrantsConsumerConformance",
        "importedTokensOrStylesGrantConformance",
        "versionLabelChangeGrantsConformance",
        "candidateArtifactNameGrantsLifecycleEligibility",
    ):
        req(evaluation.get(key) is False, f"migration evidence shortcut must remain false: {key}")

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
        req(evidence.get(key) is True, f"consumer evidence rule must remain true: {key}")

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
        req(rollback.get(key) is True, f"rollback rule must remain true: {key}")
    req(rollback.get("rollbackMayRewriteImmutableDesignSystemHistory") is False, "rollback may not rewrite immutable design-system history")

    schema = load(SCHEMA)
    req(schema.get("type") == "object", "consumer adoption schema root must be object")
    req(schema.get("additionalProperties") is False, "consumer adoption schema must fail closed on unknown top-level fields")
    required_schema_fields = set(schema.get("required", []))
    for field in (
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

    runtime = (ROOT / RUNTIME).read_text(encoding="utf-8")
    for symbol in ("MIGRATION_EVIDENCE_CATEGORIES", "validateConsumerAdoptionRecord", "evaluateConsumerMigration", "migrationCandidate"):
        req(symbol in runtime, f"migration runtime missing API: {symbol}")
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "localStorage", "sessionStorage", "indexedDB", "child_process", "exec(", "spawn("):
        req(forbidden not in runtime, f"migration runtime contains forbidden network/persistence/process primitive: {forbidden}")
    req("conformanceGranted: false" in runtime, "migration runtime must never grant conformance")
    req("release.lifecycle === 'stable'" in runtime, "production eligibility must require a Stable release input")
    req("release.consumerEligible" in runtime, "production eligibility must require consumer-eligible release input")

    guide = (ROOT / GUIDE).read_text(encoding="utf-8")
    for phrase in (
        "**Current Stable authority:** GLAZE UI V1.3 — Adaptive Resonance / `1.3.0`",
        "**Current required consumer target:** `1.3.0`",
        "No consumer is automatically V1.3 conformant",
        "V1.3.1 hardening",
        "does not establish that any consumer has migrated",
    ):
        req(phrase in guide, f"migration guide missing current Stable boundary text: {phrase}")
    req("css/glaze-v1.3.0.css" in guide, "migration guide must explicitly reject a fabricated V1.3 CSS aggregate")
    req("js/glaze-v1.3.0.mjs" in guide, "migration guide must identify the Stable runtime")

    req(not (ROOT / "css/glaze-v1.3.0.css").exists(), "do not fabricate a V1.3 CSS aggregate absent from the integrated implementation")
    req((ROOT / "js/glaze-v1.3.0.mjs").is_file(), "Stable V1.3 runtime entrypoint is required")

    if errors:
        print("GLAZE UI V1.3 Migration and Consumer Boundary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.3 Stable Migration and Consumer Boundary: PASS")
    print("Boundary: V1.3 is eligible for independent adoption; every consumer remains exact-revision and repository-local acceptance gated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
