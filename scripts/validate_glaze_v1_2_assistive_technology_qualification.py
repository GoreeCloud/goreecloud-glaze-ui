#!/usr/bin/env python3
"""Validate exact-revision manual assistive-technology qualification records.

The self-test validates only the evidence format. It is never TalkBack, VoiceOver,
Voice Access, switch-control, human accessibility, or physical-device evidence.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/v1.2/assistive-technology-qualification.candidate.json"
ACCESSIBILITY = ROOT / "contracts/v1.2/accessibility-testing.candidate.json"
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


def validate_source() -> dict[str, Any]:
    contract = read_json(CONTRACT)
    accessibility = read_json(ACCESSIBILITY)
    lifecycle = read_json(LIFECYCLE)
    req(VERSION.read_text(encoding="utf-8").strip() == "1.1.0", "VERSION must remain V1.1 Stable")
    req(lifecycle.get("currentStable") == "1.1.0" and lifecycle.get("currentOfficial") == "1.1.0", "Stable/official lifecycle authority drifted")
    req(lifecycle.get("activeCandidate") == "1.2.0-candidate", "active Candidate authority drifted")
    req(contract.get("version") == "1.2.0-candidate" and contract.get("lifecycle") == "candidate", "assistive-technology protocol lifecycle drifted")
    req(contract.get("stableBaseline") == "1.1.0" and contract.get("consumerEligible") is False, "assistive-technology protocol overclaimed lifecycle authority")
    req(contract.get("authority", {}).get("accessibilityTesting") == "contracts/v1.2/accessibility-testing.candidate.json", "Accessibility Testing binding drifted")
    boundary = contract.get("currentBoundary", {})
    req(boundary.get("protocolEstablished") is True, "assistive-technology protocol must be established")
    for key in ("manualAssistiveTechnologyEvidenceEstablished", "humanAccessibilityAcceptanceEstablished", "physicalDeviceAccessibilityAcceptanceEstablished", "releaseCandidateEstablished", "stableEstablished"):
        req(boundary.get(key) is False, f"assistive-technology protocol overclaimed {key}")
    rules = contract.get("acceptanceRules", {})
    req(rules.get("operatorIdentityRequired") is True and rules.get("technologyVersionRequired") is True and rules.get("manualExecutionRequired") is True, "manual evidence requirements drifted")
    for key in ("machineAccessibilityTreeAloneIsManualEvidence", "androidUiAutomatorAloneIsTalkBackEvidence", "browserAccessibilityTreeAloneIsScreenReaderEvidence", "sessionPassImpliesFullAccessibilityAcceptance", "singleTechnologyPassImpliesSupportMatrixAcceptance", "singlePlatformPassImpliesCompleteNativeParity", "protocolValidationImpliesHumanAcceptance", "protocolValidationImpliesReleaseCandidate", "protocolValidationImpliesStable", "protocolValidationImpliesConsumerConformance"):
        req(rules.get(key) is False, f"assistive-technology overclaim guard drifted: {key}")
    req(accessibility.get("evidenceBoundary", {}).get("phase5AccessibilityTestingComplete") is False, "machine accessibility may not close Phase 5")
    blockers = set(accessibility.get("evidenceBoundary", {}).get("notEstablished", []))
    req({"screen-reader-acceptance", "talkback-acceptance", "voiceover-acceptance", "switch-control-acceptance", "voice-access-acceptance", "physical-device-accessibility-acceptance", "release-candidate", "stable"}.issubset(blockers), "Accessibility Testing lost required manual blockers")
    required = contract.get("record", {}).get("requiredScenarioIds", [])
    req(isinstance(required, list) and len(required) >= 9 and len(required) == len(set(required)), "assistive-technology required scenarios are incomplete or duplicated")
    return contract


def validate_record(record: dict[str, Any], contract: dict[str, Any], head: str) -> None:
    spec = contract["record"]
    for field in spec["requiredTopLevelFields"]:
        req(field in record, f"record missing top-level field {field}")
    req(record.get("schemaVersion") == 1, "record schemaVersion must be 1")
    req(record.get("recordType") == "glaze-v1.2-assistive-technology-qualification", "recordType mismatch")
    source = meaningful(record.get("sourceRevision"), "sourceRevision")
    req(bool(HEX40.fullmatch(source)), "sourceRevision must be 40 lowercase hex characters")
    req(source == head, f"stale assistive-technology evidence {source}; expected exact head {head}")
    req(record.get("repository") == spec["repository"], "record repository mismatch")
    valid_timestamp(record.get("capturedAt"), "capturedAt")
    meaningful(record.get("operator"), "operator")
    req(record.get("manualExecution") is True, "manualExecution must be true; machine-only evidence is not a manual session")
    meaningful(record.get("platform"), "platform")

    device = record.get("device")
    req(isinstance(device, dict), "device must be an object")
    for field in spec["deviceRequiredFields"]:
        req(field in device, f"device missing {field}")
    req(device.get("physicalDevice") is True, "assistive-technology qualification requires a physical device")
    req(device.get("emulator") is False, "emulator/simulator session cannot satisfy physical assistive-technology qualification")
    for field in ("manufacturer", "model", "osName", "osVersion", "osBuild"):
        meaningful(device.get(field), f"device.{field}")

    technology = record.get("assistiveTechnology")
    req(isinstance(technology, dict), "assistiveTechnology must be an object")
    for field in spec["assistiveTechnologyRequiredFields"]:
        req(field in technology, f"assistiveTechnology missing {field}")
    name = meaningful(technology.get("name"), "assistiveTechnology.name")
    req(name in set(spec["recognizedTechnologies"]), f"unrecognized assistive technology {name!r}")
    meaningful(technology.get("version"), "assistiveTechnology.version")
    meaningful(technology.get("inputMode"), "assistiveTechnology.inputMode")
    if name == "Other":
        meaningful(technology.get("otherName"), "assistiveTechnology.otherName")

    required_ids = list(spec["requiredScenarioIds"])
    statuses = set(spec["scenarioStatus"])
    scenarios = record.get("scenarios")
    req(isinstance(scenarios, list), "scenarios must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    has_failure = False
    for i, scenario in enumerate(scenarios):
        req(isinstance(scenario, dict), f"scenarios[{i}] must be an object")
        sid = meaningful(scenario.get("id"), f"scenarios[{i}].id")
        req(sid in required_ids and sid not in by_id, f"unexpected or duplicate scenario {sid}")
        status = scenario.get("status")
        req(status in statuses, f"invalid scenario status for {sid}: {status!r}")
        if status == "not-applicable-with-reason":
            meaningful(scenario.get("reason"), f"{sid}.reason")
        else:
            meaningful(scenario.get("observation"), f"{sid}.observation")
        if status == "fail":
            has_failure = True
            meaningful(scenario.get("defectOrFinding"), f"{sid}.defectOrFinding")
        by_id[sid] = scenario
    req(set(by_id) == set(required_ids), "record does not contain the exact required assistive-technology scenario set")

    decision = record.get("sessionDecision")
    req(decision in set(spec["sessionDecisionValues"]), f"invalid sessionDecision {decision!r}")
    if decision == "session-pass":
        req(not has_failure, "session-pass cannot contain a failed scenario")
    if decision == "session-fail":
        req(has_failure, "session-fail must identify at least one failed scenario")
    meaningful(record.get("sessionSummary"), "sessionSummary")


def sample(head: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "recordType": "glaze-v1.2-assistive-technology-qualification",
        "sourceRevision": head,
        "repository": "GoreeCloud/goreecloud-glaze-ui",
        "capturedAt": "2026-09-06T18:00:00Z",
        "operator": "qualification-self-test",
        "manualExecution": True,
        "platform": "Android self-test",
        "device": {"physicalDevice": True, "emulator": False, "manufacturer": "SelfTest Manufacturer", "model": "SelfTest Device", "osName": "Android", "osVersion": "self-test-version", "osBuild": "self-test-build"},
        "assistiveTechnology": {"name": "TalkBack", "version": "self-test-version", "inputMode": "touch-exploration"},
        "scenarios": [{"id": sid, "status": "pass", "observation": f"Synthetic format observation for {sid}; not evidence."} for sid in contract["record"]["requiredScenarioIds"]],
        "sessionDecision": "session-pass",
        "sessionSummary": "Synthetic validator self-test only; not a manual or physical-device session."
    }


def reject(record: dict[str, Any], contract: dict[str, Any], head: str, label: str) -> None:
    try:
        validate_record(record, contract, head)
    except QualificationError:
        return
    raise QualificationError(f"self-test expected rejection but accepted {label}")


def self_test(contract: dict[str, Any], head: str) -> None:
    valid = sample(head, contract)
    validate_record(valid, contract, head)
    stale = copy.deepcopy(valid); stale["sourceRevision"] = "0" * 40 if head != "0" * 40 else "1" * 40; reject(stale, contract, head, "stale revision")
    machine = copy.deepcopy(valid); machine["manualExecution"] = False; reject(machine, contract, head, "machine-only session")
    emulator = copy.deepcopy(valid); emulator["device"].update({"physicalDevice": False, "emulator": True}); reject(emulator, contract, head, "emulator as physical session")
    placeholder = copy.deepcopy(valid); placeholder["assistiveTechnology"]["version"] = "TBD"; reject(placeholder, contract, head, "placeholder technology version")
    failed_pass = copy.deepcopy(valid); failed_pass["scenarios"][0].update({"status": "fail", "defectOrFinding": "Synthetic failure"}); reject(failed_pass, contract, head, "session-pass with failed scenario")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    contract = validate_source()
    head = revision()
    if args.record:
        validate_record(read_json(args.record.expanduser().resolve(), external=True), contract, head)
        print(f"Validated manual assistive-technology session record for exact revision {head}")
    if args.self_test:
        self_test(contract, head)
        print("Assistive-technology qualification protocol self-test passed")
        print("Synthetic self-test records are not manual, screen-reader, or physical-device evidence")
    if not args.record and not args.self_test:
        print("Assistive-technology qualification protocol source validation passed")
    print("Manual support-matrix acceptance remains pending until real exact-revision sessions are attached")
    print("Lifecycle authority unchanged: V1.1 / 1.1.0 Stable; V1.2 Candidate")


if __name__ == "__main__":
    try:
        main()
    except QualificationError as exc:
        raise SystemExit(f"GLAZE UI V1.2 assistive-technology qualification failed: {exc}")
