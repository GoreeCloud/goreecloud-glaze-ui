#!/usr/bin/env python3
"""Validate the current GLAZE UI Stable consumer registry and guidance.

The registry is intentionally fail closed. A consumer can be recorded as accepted
for the current Glaze contract only with an exact source revision and evidence
reference. Historical adoption evidence may be retained only as complete migration
provenance on an adoption-required record. Even an accepted registry record never
makes the overall product production eligible; product/release authority remains
with the consumer's own acceptance and lifecycle records.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = re.compile(r"^GoreeCloud/.+$")
STATUSES = {"adoption-required", "unverified", "accepted-v1"}
SCHEMA_VERSION = 7


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Glaze UI consumer registry validation failed: {message}")


def load_json(path: str) -> dict[str, object]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    req(isinstance(value, dict), f"{path} root must be an object")
    return value


def validate_guidance(stable: str, label: str) -> None:
    guidance = (ROOT / "CONSUMERS.md").read_text(encoding="utf-8")
    req(label in guidance, "CONSUMERS.md must identify the official product label")
    req(stable in guidance, "CONSUMERS.md must identify the current Stable version")
    req(
        "Fresh repository-local V1.3 adoption and acceptance evidence is required" in guidance,
        "CONSUMERS.md must preserve the fresh-evidence boundary",
    )
    req(
        "may retain historical target/evidence fields as migration provenance" in guidance,
        "CONSUMERS.md must define the adoption-required provenance boundary",
    )
    req(
        "No consumer is production-eligible merely because" in guidance,
        "CONSUMERS.md must preserve independent product acceptance",
    )
    req(
        "consumer registry" in guidance.lower(),
        "CONSUMERS.md must identify the registry authority",
    )


def validate_schema_contract() -> None:
    schema = load_json("schemas/consumer-registry.schema.json")
    properties = schema.get("properties")
    req(isinstance(properties, dict), "consumer registry schema properties")
    schema_version = properties.get("schemaVersion")
    req(
        isinstance(schema_version, dict) and schema_version.get("const") == SCHEMA_VERSION,
        f"schema must describe registry schemaVersion {SCHEMA_VERSION}",
    )
    consumers = properties.get("consumers")
    req(isinstance(consumers, dict), "schema consumers declaration")
    serialized = json.dumps(schema, sort_keys=True)
    for status in sorted(STATUSES):
        req(status in serialized, f"schema must recognize status {status}")
    req(
        "officialBaseline" in properties and "officialProductLabel" in properties,
        "schema must describe current official baseline fields",
    )
    req(
        "candidateAssessment" not in properties,
        "current registry schema must not require retired Candidate assessment state",
    )


def main() -> None:
    stable = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    req(SEMVER.fullmatch(stable) is not None, "VERSION must contain a semantic Stable version")

    data = load_json("consumers/registry.json")
    lifecycle = load_json("registry/lifecycle.json")

    req(
        data.get("schemaVersion") == SCHEMA_VERSION,
        f"registry schemaVersion must be {SCHEMA_VERSION}",
    )
    req(data.get("officialBaseline") == stable, "officialBaseline must match VERSION")
    req(
        data.get("requiredConsumerVersion") == stable,
        "requiredConsumerVersion must match VERSION",
    )

    label = data.get("officialProductLabel")
    req(isinstance(label, str) and label.strip(), "officialProductLabel")
    req(lifecycle.get("currentStable") == stable, "lifecycle currentStable must match VERSION")
    req(
        lifecycle.get("currentOfficial") == stable,
        "lifecycle currentOfficial must match VERSION",
    )
    req(
        lifecycle.get("officialProductLabel") == label,
        "registry/lifecycle product label mismatch",
    )
    req(
        lifecycle.get("activeCandidate") is None,
        "Stable registry must not retain an active Candidate",
    )

    releases = lifecycle.get("releases")
    req(isinstance(releases, list), "lifecycle releases list")
    stable_releases = [
        release
        for release in releases
        if isinstance(release, dict) and release.get("version") == stable
    ]
    req(
        len(stable_releases) == 1,
        "exactly one lifecycle record must match current Stable",
    )
    stable_release = stable_releases[0]
    req(stable_release.get("status") == "stable", "current Stable lifecycle status")
    req(
        stable_release.get("consumerEligible") is True,
        "current Stable must be consumer-eligible",
    )
    anchor = stable_release.get("sourceQualificationAnchor")
    req(
        isinstance(anchor, str) and SHA40.fullmatch(anchor) is not None,
        "current Stable source qualification anchor",
    )

    vocabulary = data.get("statusVocabulary")
    req(
        isinstance(vocabulary, list)
        and set(vocabulary) == STATUSES
        and len(vocabulary) == len(STATUSES),
        f"statusVocabulary must exactly match the schema {SCHEMA_VERSION} vocabulary",
    )

    enforcement = data.get("enforcement")
    req(isinstance(enforcement, dict), "enforcement object")
    req(
        enforcement.get("officialCurrentRequired") is True,
        "officialCurrentRequired must be true",
    )
    req(
        enforcement.get("productionExceptionsAllowed") is False,
        "productionExceptionsAllowed must be false",
    )
    platform_scope = enforcement.get("platformScope")
    req(
        isinstance(platform_scope, list)
        and platform_scope
        and len(platform_scope) == len(set(platform_scope)),
        "platformScope must be a non-empty unique list",
    )
    rule = enforcement.get("unsupportedPlatformRule")
    req(isinstance(rule, str) and rule.strip(), "unsupportedPlatformRule")

    audited_at = data.get("auditedAt")
    req(isinstance(audited_at, str), "auditedAt")
    try:
        date.fromisoformat(audited_at)
    except ValueError as exc:
        raise SystemExit(
            f"Glaze UI consumer registry validation failed: auditedAt must be YYYY-MM-DD: {exc}"
        ) from exc

    consumers = data.get("consumers")
    req(isinstance(consumers, list) and consumers, "consumers must be a non-empty list")
    seen_repositories: set[str] = set()
    seen_names: set[str] = set()
    accepted = 0
    historical_provenance = 0

    for index, consumer in enumerate(consumers):
        req(isinstance(consumer, dict), f"consumers[{index}] must be an object")
        required_keys = {
            "name",
            "repository",
            "status",
            "targetVersion",
            "requiredTargetVersion",
            "referenceRevision",
            "evidence",
            "productionEligible",
            "notes",
        }
        req(set(consumer) == required_keys, f"consumers[{index}] field drift")

        name = consumer.get("name")
        repo = consumer.get("repository")
        status = consumer.get("status")
        req(isinstance(name, str) and name.strip(), f"consumers[{index}].name")
        req(
            isinstance(repo, str) and REPOSITORY.fullmatch(repo) is not None,
            f"consumers[{index}].repository",
        )
        req(repo not in seen_repositories, f"duplicate consumer repository {repo}")
        req(name not in seen_names, f"duplicate consumer name {name}")
        seen_repositories.add(repo)
        seen_names.add(name)

        req(status in STATUSES, f"{repo} status")
        req(
            consumer.get("requiredTargetVersion") == stable,
            f"{repo} required target must be current Stable",
        )
        req(
            consumer.get("productionEligible") is False,
            f"{repo} must not become production-eligible from Glaze registry state alone",
        )
        notes = consumer.get("notes")
        req(isinstance(notes, str) and notes.strip(), f"{repo} notes")

        target = consumer.get("targetVersion")
        revision = consumer.get("referenceRevision")
        evidence = consumer.get("evidence")

        if status == "unverified":
            req(
                target is None and revision is None and evidence is None,
                f"{repo} unverified status must not carry adoption or acceptance evidence",
            )
        elif status == "adoption-required":
            provenance_values = (target, revision, evidence)
            if any(value is not None for value in provenance_values):
                historical_provenance += 1
                req(
                    all(value is not None for value in provenance_values),
                    f"{repo} historical adoption provenance must be complete",
                )
                req(
                    isinstance(target, str) and SEMVER.fullmatch(target) is not None,
                    f"{repo} historical target must be semantic",
                )
                req(
                    target != stable,
                    f"{repo} adoption-required provenance must not masquerade as current Stable acceptance",
                )
                req(
                    isinstance(revision, str) and SHA40.fullmatch(revision) is not None,
                    f"{repo} historical provenance revision",
                )
                req(
                    isinstance(evidence, str) and evidence.strip(),
                    f"{repo} historical provenance evidence",
                )
        else:
            accepted += 1
            req(target == stable, f"{repo} accepted target must equal current Stable")
            req(
                isinstance(revision, str) and SHA40.fullmatch(revision) is not None,
                f"{repo} accepted revision",
            )
            req(
                isinstance(evidence, str) and evidence.strip(),
                f"{repo} accepted evidence",
            )

    validate_schema_contract()
    validate_guidance(stable, label)
    print(
        "Glaze UI consumer registry validated: "
        f"{len(consumers)} consumers, {accepted} accepted for {label} / {stable}, "
        f"{historical_provenance} historical adoption record(s) retained; "
        "product production eligibility remains independently gated"
    )


if __name__ == "__main__":
    main()
