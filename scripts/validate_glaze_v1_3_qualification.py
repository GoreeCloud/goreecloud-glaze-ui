#!/usr/bin/env python3
"""Validate the preserved V1.3 qualification evidence boundary after Stable release."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE = "1.3.0"
WORKSTREAMS = {
    "human-optical-and-icon-collision-qualification",
    "manual-assistive-technology-qualification",
    "physical-device-native-platform-qualification",
    "physical-device-production-performance-qualification",
    "native-personalization-adapter-qualification",
    "stable-activation-and-source-namespace-cleanup",
}


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha40(value):
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def semver_tuple(value: str):
    try:
        return tuple(int(part) for part in value.split("."))
    except (AttributeError, ValueError):
        return None


def main() -> int:
    errors = []

    def req(ok, msg):
        if not ok:
            errors.append(msg)

    for path in [
        "contracts/v1.3/qualification-matrix.json",
        "contracts/v1.3/qualification-evidence.schema.json",
        "contracts/v1.3/quality-rules.candidate.json",
        "acceptance/v1.3-stable.md",
        "acceptance/v1.3-candidate.md",
        "acceptance/v1.3-deferred-qualification.md",
        "GLAZE_UI_V1_3_1_HARDENING.md",
        "registry/lifecycle.json",
        "VERSION",
    ]:
        req((ROOT / path).is_file(), f"missing preserved qualification authority: {path}")

    if errors:
        print("GLAZE UI V1.3 qualification boundary validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    lifecycle = load("registry/lifecycle.json")
    current = lifecycle.get("currentStable")
    version = (ROOT / "VERSION").read_text().strip()
    req(current == lifecycle.get("currentOfficial") == version,
        "VERSION/currentStable/currentOfficial must agree on the live current release")
    current_tuple = semver_tuple(current)
    stable_tuple = semver_tuple(STABLE)
    req(current_tuple is not None and stable_tuple is not None and current_tuple >= stable_tuple,
        "live current Stable may not regress below V1.3.0")

    release = next((item for item in lifecycle.get("releases", []) if item.get("version") == STABLE), None)
    req(bool(release), "lifecycle must retain the V1.3.0 historical release record")
    req(bool(release) and release.get("status") == "stable", "V1.3.0 historical record must remain Stable")
    req(bool(release) and release.get("consumerEligible") is True, "V1.3.0 historical consumer eligibility must remain recorded")

    matrix = load("contracts/v1.3/qualification-matrix.json")
    items = {item.get("id"): item for item in matrix.get("workstreams", []) if isinstance(item, dict)}
    req(set(items) == WORKSTREAMS, "qualification matrix must retain the six historical workstreams")

    schema = load("contracts/v1.3/qualification-evidence.schema.json")
    enum = set(schema.get("properties", {}).get("workstream_id", {}).get("enum", []))
    req(enum == WORKSTREAMS, "evidence schema must retain all six workstream IDs")

    quality = load("contracts/v1.3/quality-rules.candidate.json")
    req(len(quality.get("rules", [])) == 55, "55-rule V1.3 human quality authority must remain intact")
    req(quality.get("humanReviewRequired") is True, "human review requirement must remain intact")
    req(quality.get("automatedValidationSufficient") is False, "automation must not substitute for human review")

    for path in sorted((ROOT / "evidence/v1.3").glob("*.json")):
        value = json.loads(path.read_text())
        req(value.get("workstream_id") in WORKSTREAMS, f"{path.name}: unknown workstream")
        target = value.get("target", {})
        revision = target.get("source_revision")
        if revision is not None:
            req(sha40(revision), f"{path.name}: invalid source revision")
        if value.get("status") != "passed":
            req(value.get("disposition", {}).get("accepted_for_lifecycle_gate") is not True,
                f"{path.name}: non-passed evidence cannot be lifecycle-accepted")

    candidate = (ROOT / "acceptance/v1.3-candidate.md").read_text()
    deferred = (ROOT / "acceptance/v1.3-deferred-qualification.md").read_text()
    stable = (ROOT / "acceptance/v1.3-stable.md").read_text()
    hardening = (ROOT / "GLAZE_UI_V1_3_1_HARDENING.md").read_text()
    req("Historical Candidate Qualification Ledger" in candidate, "Candidate ledger must be historical/superseded")
    req("V1.3.1" in deferred and "V1.3.1" in hardening, "deferred qualification must be carried into V1.3.1")
    req("not represented as passed" in stable or "not rewritten as a pass" in stable,
        "Stable acceptance must reject fabricated qualification passes")

    if errors:
        print("GLAZE UI V1.3 qualification boundary validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("GLAZE UI V1.3 qualification boundary: PASS")
    print(f"Historical qualification records are preserved while live current Stable remains {current}; unresolved V1.3.1 work is not represented as passed V1.3.0 evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
