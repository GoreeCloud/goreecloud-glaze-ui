#!/usr/bin/env python3
"""Validate V1.3 release provenance and the V1.3.1 deferred-qualification boundary."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE = "1.3.0"
QUALITY = "contracts/v1.3/quality-rules.candidate.json"
RULE_IDS = {f"quality-{i:02d}" for i in range(1, 56)}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    errors = []

    def req(ok, msg):
        if not ok:
            errors.append(msg)

    for path in [
        "acceptance/v1.3-stable.md",
        "acceptance/v1.3-deferred-qualification.md",
        "GLAZE_UI_V1_3_1_HARDENING.md",
        "contracts/v1.3/deferred-qualification.plan.json",
        "contracts/v1.3/qualification-matrix.json",
        "contracts/v1.3/qualification-evidence.schema.json",
        QUALITY,
        "registry/lifecycle.json",
        "consumers/registry.json",
        "VERSION",
    ]:
        req((ROOT / path).is_file(), f"missing V1.3/V1.3.1 authority: {path}")

    if errors:
        print("GLAZE UI V1.3 release/deferred qualification validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    req((ROOT / "VERSION").read_text().strip() == STABLE, "VERSION must be 1.3.0")
    lifecycle = load("registry/lifecycle.json")
    req(lifecycle.get("currentStable") == STABLE, "currentStable must be 1.3.0")
    req(lifecycle.get("currentOfficial") == STABLE, "currentOfficial must be 1.3.0")
    release = next((x for x in lifecycle.get("releases", []) if x.get("version") == STABLE), None)
    req(bool(release) and release.get("status") == "stable", "1.3.0 release record must be Stable")
    req(bool(release) and release.get("consumerEligible") is True, "1.3.0 must be consumer-eligible")

    consumers = load("consumers/registry.json")
    req(consumers.get("requiredConsumerVersion") == STABLE, "shared required consumer target must be 1.3.0")

    quality = load(QUALITY)
    qrules = quality.get("rules", [])
    req(len(qrules) == 55 and {x.get("id") for x in qrules if isinstance(x, dict)} == RULE_IDS,
        "quality contract must retain exactly quality-01 through quality-55")
    req(quality.get("humanReviewRequired") is True, "human quality review requirement must remain recorded")
    req(quality.get("automatedValidationSufficient") is False, "automation must not be represented as sufficient human review")

    schema = load("contracts/v1.3/qualification-evidence.schema.json")
    props = schema.get("properties", {})
    req(props.get("schema_version", {}).get("const") == 2, "evidence schema_version must remain 2")

    stable_acceptance = (ROOT / "acceptance/v1.3-stable.md").read_text()
    deferred = (ROOT / "acceptance/v1.3-deferred-qualification.md").read_text()
    hardening = (ROOT / "GLAZE_UI_V1_3_1_HARDENING.md").read_text()
    for text, name in [(stable_acceptance, "Stable acceptance"), (deferred, "deferred qualification"), (hardening, "V1.3.1 hardening")]:
        req("V1.3.1" in text, f"{name} must identify V1.3.1 follow-up")
    stable_integrity_language = (
        "must not be represented as passed" in stable_acceptance
        and "not rewritten as a pass" in stable_acceptance
    )
    req(stable_integrity_language, "Stable acceptance must not fabricate deferred passes")
    deferred_integrity_language = (
        "does **not** manufacture" in deferred
        and "missing evidence as passed" in deferred
    )
    req(deferred_integrity_language, "deferred qualification must preserve evidence integrity")

    if errors:
        print("GLAZE UI V1.3 release/deferred qualification validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("GLAZE UI V1.3 release/deferred qualification boundary: PASS")
    print("V1.3.0 is Stable/consumer-eligible; unresolved qualification is preserved as V1.3.1 follow-up, not passed evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
