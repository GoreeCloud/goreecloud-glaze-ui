#!/usr/bin/env python3
"""Validate the V1.2 physical-device / production-performance qualification protocol.

Protocol validation and self-tests are not physical-device evidence. Real evidence is
validated only when supplied with --record and must match the exact checked-out source
revision. Production acceptance remains impossible while the canonical budget is
revalidation-required.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/v1.2/device-performance-qualification.candidate.json"
BUDGET = ROOT / "contracts/performance/glaze-v1-performance-budget.json"
PERFORMANCE = ROOT / "contracts/v1.2/performance-testing.candidate.json"
LIFECYCLE = ROOT / "registry/lifecycle.json"
VERSION = ROOT / "VERSION"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDERS = {"", "todo", "tbd", "unknown", "n/a", "na", "placeholder", "example", "none", "null"}


class QualificationError(RuntimeError):
    pass


def req(ok: bool, message: str) -> None:
    if not ok:
        raise QualificationError(message)


def read_json(path: Path, *, external: bool = False) -> dict[str, Any]:
    label = str(path) if external else str(path.relative_to(ROOT))
    req(path.is_file(), f"missing required JSON file: {label}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QualificationError(f"invalid JSON file {label}: {exc}") from exc
    req(isinstance(value, dict), f"expected JSON object: {label}")
    return value


def revision() -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    req(bool(HEX40.fullmatch(value)), f"invalid Git revision: {value!r}")
    return value


def meaningful(value: Any, label: str) -> str:
    req(isinstance(value, str), f"{label} must be a string")
    text = value.strip()
    req(text.lower() not in PLACEHOLDERS, f"{label} contains a placeholder value")
    return text


def valid_timestamp(value: Any, label: str) -> str:
    text = meaningful(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise QualificationError(f"{label} must be ISO-8601: {text!r}") from exc
    req(parsed.tzinfo is not None, f"{label} must include an explicit timezone")
    return text


def finite(value: Any, label: str, minimum: float | None = None, maximum: float | None = None) -> float:
    req(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label} must be numeric")
    number = float(value)
    req(math.isfinite(number), f"{label} must be finite")
    if minimum is not None:
        req(number >= minimum, f"{label} must be >= {minimum}")
    if maximum is not None:
        req(number <= maximum, f"{label} must be <= {maximum}")
    return number


def validate_source() -> tuple[dict[str, Any], dict[str, Any]]:
    contract = read_json(CONTRACT)
    budget = read_json(BUDGET)
    performance = read_json(PERFORMANCE)
    lifecycle = read_json(LIFECYCLE)
    req(VERSION.read_text(encoding="utf-8").strip() == "1.1.0", "VERSION must remain V1.1 Stable")
    req(lifecycle.get("currentStable") == "1.1.0" and lifecycle.get("currentOfficial") == "1.1.0", "Stable/official lifecycle authority drifted")
    req(lifecycle.get("activeCandidate") == "1.2.0-candidate", "active Candidate authority drifted")
    req(contract.get("version") == "1.2.0-candidate" and contract.get("lifecycle") == "candidate", "qualification contract lifecycle drifted")
    req(contract.get("stableBaseline") == "1.1.0" and contract.get("consumerEligible") is False, "qualification contract overclaimed lifecycle authority")
    authority = contract.get("authority", {})
    req(authority.get("canonicalBudget") == "contracts/performance/glaze-v1-performance-budget.json", "canonical budget binding drifted")
    req(authority.get("performanceTesting") == "contracts/v1.2/performance-testing.candidate.json", "Performance Testing binding drifted")
    req(budget.get("status") == authority.get("requiredBudgetStatusUntilAccepted") == "revalidation-required", "canonical budget must remain revalidation-required until explicitly accepted")
    boundary = contract.get("currentBoundary", {})
    req(boundary.get("protocolEstablished") is True, "qualification protocol must be established")
    for key in ("physicalDeviceEvidenceEstablished", "acceptedNumericRuntimeBudgetEstablished", "acceptedPlatformBudgetEstablished", "productionPerformanceAcceptanceEstablished", "releaseCandidateEstablished", "stableEstablished"):
        req(boundary.get(key) is False, f"qualification protocol overclaimed {key}")
    perf_boundary = performance.get("canonicalBudgetBoundary", {})
    for key in ("numericRuntimeBudgetEstablished", "platformBudgetEstablished", "productionPerformanceAcceptanceEstablished"):
        req(perf_boundary.get(key) is False, f"Performance Testing unexpectedly claims {key}")
    rules = contract.get("acceptanceRules", {})
    for key in ("ciSelfTestIsEvidence", "browserCiIsPhysicalDeviceEvidence", "androidEmulatorIsPhysicalDeviceEvidence", "simulatorIsPhysicalDeviceEvidence", "oneDeviceImpliesPlatformQualification", "onePlatformImpliesCompleteNativeParity", "protocolValidationImpliesProductionAcceptance", "protocolValidationImpliesReleaseCandidate", "protocolValidationImpliesStable", "protocolValidationImpliesConsumerConformance"):
        req(rules.get(key) is False, f"overclaim guard drifted: {key}")
    spec = contract.get("record", {})
    scenario_ids = spec.get("requiredScenarioIds", [])
    metrics = spec.get("requiredMetricFamilies", [])
    req(isinstance(scenario_ids, list) and len(scenario_ids) >= 8 and len(set(scenario_ids)) == len(scenario_ids), "required scenario set is incomplete or duplicated")
    req(set(metrics) == {"frameTiming", "interactionLatency", "memory", "compositorOrGpu", "power", "thermal"}, "required metric families drifted")
    blockers = set(contract.get("notEstablished", []))
    req({"accepted-numeric-runtime-budget", "accepted-platform-performance-budget", "physical-device-performance-acceptance", "production-performance-acceptance", "release-candidate", "stable"}.issubset(blockers), "qualification blockers were removed")
    return contract, budget


def validate_metric(metric: Any, label: str, allowed: set[str]) -> bool:
    req(isinstance(metric, dict), f"{label} must be an object")
    status = metric.get("status")
    req(status in allowed, f"{label}.status invalid: {status!r}")
    if status == "measured":
        finite(metric.get("value"), f"{label}.value")
        meaningful(metric.get("unit"), f"{label}.unit")
        return True
    meaningful(metric.get("reason"), f"{label}.reason")
    req("value" not in metric, f"{label} may not carry a value when unavailable")
    return False


def validate_record(record: dict[str, Any], contract: dict[str, Any], budget: dict[str, Any], head: str) -> None:
    spec = contract["record"]
    for field in spec["requiredTopLevelFields"]:
        req(field in record, f"record missing top-level field {field}")
    req(record.get("schemaVersion") == 1, "record schemaVersion must be 1")
    req(record.get("recordType") == "glaze-v1.2-device-performance-qualification", "recordType mismatch")
    source = meaningful(record.get("sourceRevision"), "sourceRevision")
    req(bool(HEX40.fullmatch(source)), "sourceRevision must be 40 lowercase hex characters")
    req(source == head, f"stale evidence revision {source}; expected exact head {head}")
    req(record.get("repository") == spec["repository"], "record repository mismatch")
    valid_timestamp(record.get("capturedAt"), "capturedAt")
    meaningful(record.get("capturedBy"), "capturedBy")

    device = record.get("device")
    req(isinstance(device, dict), "device must be an object")
    for field in spec["deviceRequiredFields"]:
        req(field in device, f"device missing {field}")
    req(device.get("physicalDevice") is True, "physicalDevice must be true")
    req(device.get("emulator") is False, "emulator/simulator evidence cannot satisfy physical qualification")
    for field in ("manufacturer", "model", "osName", "osVersion", "osBuild", "architecture", "gpu"):
        meaningful(device.get(field), f"device.{field}")
    finite(device.get("displayRefreshHz"), "device.displayRefreshHz", 1)

    env = record.get("environment")
    req(isinstance(env, dict), "environment must be an object")
    for field in spec["environmentRequiredFields"]:
        req(field in env, f"environment missing {field}")
    meaningful(env.get("powerSource"), "environment.powerSource")
    finite(env.get("batteryPercent"), "environment.batteryPercent", 0, 100)
    for field in ("thermalStateBefore", "thermalStateAfter", "backgroundLoad", "appearanceMode"):
        meaningful(env.get(field), f"environment.{field}")
    modes = env.get("accessibilityModes")
    req(isinstance(modes, list), "environment.accessibilityModes must be an array")
    for i, mode in enumerate(modes):
        meaningful(mode, f"environment.accessibilityModes[{i}]")

    required_ids = list(spec["requiredScenarioIds"])
    scenarios = record.get("scenarios")
    req(isinstance(scenarios, list), "scenarios must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    for i, scenario in enumerate(scenarios):
        req(isinstance(scenario, dict), f"scenarios[{i}] must be an object")
        sid = meaningful(scenario.get("id"), f"scenarios[{i}].id")
        req(sid in required_ids and sid not in by_id, f"unexpected or duplicate scenario {sid}")
        req(scenario.get("status") in set(spec["scenarioStatus"]), f"invalid scenario status for {sid}")
        metrics = scenario.get("metrics")
        req(isinstance(metrics, dict), f"scenario {sid} metrics must be an object")
        for family in spec["requiredMetricFamilies"]:
            req(family in metrics, f"scenario {sid} missing metric family {family}")
        by_id[sid] = scenario
    req(set(by_id) == set(required_ids), "record does not contain the exact required scenario set")

    all_measured = True
    all_observed = True
    statuses = set(spec["metricObservationStatus"])
    for sid in required_ids:
        scenario = by_id[sid]
        all_observed = all_observed and scenario.get("status") == "observed"
        for family in spec["requiredMetricFamilies"]:
            all_measured = validate_metric(scenario["metrics"][family], f"{sid}.{family}", statuses) and all_measured
        if scenario.get("notes") is not None:
            meaningful(scenario["notes"], f"{sid}.notes")

    decision = record.get("decision")
    req(decision in set(spec["decisionValues"]), f"invalid record decision: {decision!r}")
    if decision == "accepted":
        req(budget.get("status") == "accepted", "accepted decision prohibited while canonical budget is not accepted")
        req(isinstance(budget.get("numericRuntimeBudgets"), dict) and budget["numericRuntimeBudgets"], "accepted decision requires canonical numeric runtime budgets")
        req(isinstance(budget.get("platformBudgets"), dict) and budget["platformBudgets"], "accepted decision requires canonical platform budgets")
        req(all_observed and all_measured, "accepted decision requires all scenarios and metric families measured")
    meaningful(record.get("decisionRationale", "observation record; no production acceptance claimed"), "decisionRationale")


def sample(head: str, contract: dict[str, Any]) -> dict[str, Any]:
    metric = {"status": "measured", "value": 1.0, "unit": "self-test-unit"}
    return {
        "schemaVersion": 1,
        "recordType": "glaze-v1.2-device-performance-qualification",
        "sourceRevision": head,
        "repository": "GoreeCloud/goreecloud-glaze-ui",
        "capturedAt": "2026-09-06T18:00:00Z",
        "capturedBy": "qualification-self-test",
        "device": {"physicalDevice": True, "emulator": False, "manufacturer": "SelfTest Manufacturer", "model": "SelfTest Device", "osName": "SelfTest OS", "osVersion": "1.0", "osBuild": "build-1", "architecture": "arm64", "gpu": "SelfTest GPU", "displayRefreshHz": 60},
        "environment": {"powerSource": "battery", "batteryPercent": 80, "thermalStateBefore": "nominal", "thermalStateAfter": "nominal", "backgroundLoad": "controlled-low", "appearanceMode": "light-dark-deep-dark-matrix", "accessibilityModes": ["default", "large-text-200", "touch-assistance", "reduced-transparency", "reduced-motion"]},
        "scenarios": [{"id": sid, "status": "observed", "metrics": {family: copy.deepcopy(metric) for family in contract["record"]["requiredMetricFamilies"]}} for sid in contract["record"]["requiredScenarioIds"]],
        "decision": "observation-only",
        "decisionRationale": "Synthetic validator self-test only; not physical-device evidence."
    }


def reject(record: dict[str, Any], contract: dict[str, Any], budget: dict[str, Any], head: str, label: str) -> None:
    try:
        validate_record(record, contract, budget, head)
    except QualificationError:
        return
    raise QualificationError(f"self-test expected rejection but accepted {label}")


def self_test(contract: dict[str, Any], budget: dict[str, Any], head: str) -> None:
    valid = sample(head, contract)
    validate_record(valid, contract, budget, head)
    stale = copy.deepcopy(valid); stale["sourceRevision"] = "0" * 40 if head != "0" * 40 else "1" * 40; reject(stale, contract, budget, head, "stale revision")
    emulator = copy.deepcopy(valid); emulator["device"].update({"physicalDevice": False, "emulator": True}); reject(emulator, contract, budget, head, "emulator as physical evidence")
    placeholder = copy.deepcopy(valid); placeholder["device"]["gpu"] = "TBD"; reject(placeholder, contract, budget, head, "placeholder device data")
    accepted = copy.deepcopy(valid); accepted["decision"] = "accepted"; reject(accepted, contract, budget, head, "production acceptance without accepted budget")
    missing = copy.deepcopy(valid); del missing["scenarios"][0]["metrics"][contract["record"]["requiredMetricFamilies"][0]]; reject(missing, contract, budget, head, "missing metric family")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    contract, budget = validate_source()
    head = revision()
    if args.record:
        validate_record(read_json(args.record.expanduser().resolve(), external=True), contract, budget, head)
        print(f"Validated physical-device/performance qualification record for exact revision {head}")
    if args.self_test:
        self_test(contract, budget, head)
        print("Physical-device/performance qualification protocol self-test passed")
        print("Synthetic self-test records are not physical-device or production evidence")
    if not args.record and not args.self_test:
        print("Physical-device/performance qualification protocol source validation passed")
    print("Canonical performance budget remains revalidation-required; production acceptance remains false")
    print("Lifecycle authority unchanged: V1.1 / 1.1.0 Stable; V1.2 Candidate")


if __name__ == "__main__":
    try:
        main()
    except QualificationError as exc:
        raise SystemExit(f"GLAZE UI V1.2 device/performance qualification failed: {exc}")
