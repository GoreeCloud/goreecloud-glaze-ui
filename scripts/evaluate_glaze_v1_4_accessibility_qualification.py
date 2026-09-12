#!/usr/bin/env python3
"""Deterministic, fail-closed evaluator for Glaze UI V1.4 accessibility qualification evidence.

This evaluator does not mutate evidence, perform a human review, or grant lifecycle status.
It only evaluates whether a candidate evidence record is blocked, review-ready, failed, or
accepted for the bounded accessibility qualification slice.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ZERO_SHA = "0" * 40
BLOCKING_SEVERITIES = {"high", "critical"}
EXPECTED_PRODUCT = "Glaze UI V1.4 — Optical Material and Chromatic Depth"
EXPECTED_VERSION = "1.4.0-candidate"
EXPECTED_RECORD_KIND = "glaze-v1.4-accessibility-qualification-evidence-candidate"
VALID_STATUSES = {"in-progress", "review-ready", "passed", "failed", "superseded"}
VALID_REVIEW_MODES = {"human", "combined", "automated"}
VALID_HUMAN_STATUSES = {"pending", "accepted", "rejected"}
VALID_PLATFORM_FAMILIES = {"web", "android", "linux", "other"}
VALID_ASSISTIVE_MODES = {
    "screen-reader",
    "voice-control",
    "switch-control",
    "keyboard",
    "other",
}
RECORD_FIELDS = {
    "schemaVersion",
    "recordKind",
    "target",
    "status",
    "observedAt",
    "reviewAuthority",
    "environment",
    "supportClaims",
    "preferenceCoverage",
    "scenarioResults",
    "issues",
    "disposition",
}
TARGET_FIELDS = {"product", "targetVersion", "sourceRevision", "sourceTreeRevision"}
REVIEW_AUTHORITY_FIELDS = {"mode", "authority", "humanReviewStatus"}
DISPOSITION_FIELDS = {
    "evaluatorDisposition",
    "acceptedForAccessibilityQualification",
    "acceptedForLifecycleGate",
    "notes",
}
ENVIRONMENT_FIELDS = {
    "platformFamily",
    "operatingSystem",
    "browser",
    "physicalDevice",
    "assistiveTechnologies",
    "evidenceReferences",
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _bounded_text(value: Any, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or normalized != value or len(value) > maximum:
        return None
    if any(unicodedata.category(char).startswith("C") for char in value):
        return None
    return value


def _valid_reference_list(value: Any, maximum_items: int) -> bool:
    if not isinstance(value, list) or len(value) > maximum_items:
        return False
    normalized = [_bounded_text(item, 1000) for item in value]
    return all(item is not None for item in normalized) and len(set(normalized)) == len(normalized)


def _valid_observed_at(value: Any) -> bool:
    """Require an RFC3339-style timestamp with explicit timezone information."""
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _result(disposition: str, reasons: list[str], *, required: list[str], missing: list[str], failed: list[str]) -> dict[str, Any]:
    return {
        "evaluatorDisposition": disposition,
        "acceptedForAccessibilityQualification": disposition == "accepted",
        "acceptedForLifecycleGate": False,
        "reasons": sorted(set(reasons)),
        "requiredScenarioIds": required,
        "missingScenarioIds": sorted(set(missing)),
        "failedScenarioIds": sorted(set(failed)),
    }


def evaluate_record(
    record: dict[str, Any],
    plan: dict[str, Any],
    *,
    expected_source_revision: str | None = None,
    expected_source_tree_revision: str | None = None,
) -> dict[str, Any]:
    """Evaluate one evidence record without mutating it."""
    record = copy.deepcopy(record)
    reasons: list[str] = []
    missing: list[str] = []
    failed: list[str] = []
    structural_blockers = False

    required = list(plan.get("requiredScenarios", []))
    conditional = plan.get("claimConditionalScenarios", {})
    claims = record.get("supportClaims", {}) if isinstance(record.get("supportClaims"), dict) else {}
    for claim_key, scenario_id in conditional.items():
        if claims.get(claim_key) is True:
            required.append(scenario_id)

    disposition = record.get("disposition", {}) if isinstance(record.get("disposition"), dict) else {}
    if disposition.get("acceptedForLifecycleGate") is not False:
        return _result(
            "failed",
            ["accessibility-evidence-may-not-grant-lifecycle-gate"],
            required=required,
            missing=missing,
            failed=failed,
        )

    if set(record) != RECORD_FIELDS:
        reasons.append("record-fields-invalid")
        structural_blockers = True
    if record.get("schemaVersion") != 1:
        reasons.append("record-schema-version-invalid")
        structural_blockers = True
    if record.get("recordKind") != EXPECTED_RECORD_KIND:
        reasons.append("record-kind-invalid")
        structural_blockers = True
    if not _valid_observed_at(record.get("observedAt")):
        reasons.append("observation-time-invalid")
        structural_blockers = True

    target = record.get("target", {}) if isinstance(record.get("target"), dict) else {}
    if set(target) != TARGET_FIELDS:
        reasons.append("target-fields-invalid")
        structural_blockers = True
    if target.get("product") != EXPECTED_PRODUCT:
        reasons.append("target-product-invalid")
        structural_blockers = True
    if target.get("targetVersion") != EXPECTED_VERSION:
        reasons.append("target-version-invalid")
        structural_blockers = True
    source_revision = target.get("sourceRevision")
    source_tree_revision = target.get("sourceTreeRevision")
    if not isinstance(source_revision, str) or not HEX40.fullmatch(source_revision) or source_revision == ZERO_SHA:
        reasons.append("exact-source-revision-missing-or-placeholder")
    if not isinstance(source_tree_revision, str) or not HEX40.fullmatch(source_tree_revision) or source_tree_revision == ZERO_SHA:
        reasons.append("exact-source-tree-revision-missing-or-placeholder")
    if expected_source_revision is not None and source_revision != expected_source_revision:
        reasons.append("source-revision-does-not-match-expected-revision")
    if expected_source_tree_revision is not None and source_tree_revision != expected_source_tree_revision:
        reasons.append("source-tree-revision-does-not-match-expected-tree")

    status = record.get("status")
    if status not in VALID_STATUSES:
        reasons.append("record-status-invalid")
        structural_blockers = True
    review = record.get("reviewAuthority", {}) if isinstance(record.get("reviewAuthority"), dict) else {}
    if set(review) != REVIEW_AUTHORITY_FIELDS:
        reasons.append("review-authority-fields-invalid")
        structural_blockers = True
    human_status = review.get("humanReviewStatus")
    review_mode = review.get("mode")
    if review_mode not in VALID_REVIEW_MODES or _bounded_text(review.get("authority"), 240) is None:
        reasons.append("review-authority-invalid")
        structural_blockers = True
    if human_status not in VALID_HUMAN_STATUSES:
        reasons.append("human-review-status-invalid")
        structural_blockers = True
    if status == "failed" or human_status == "rejected":
        reasons.append("record-or-human-review-explicitly-failed")
        return _result("failed", reasons, required=required, missing=missing, failed=failed)
    if status == "superseded":
        reasons.append("record-is-superseded")

    if not isinstance(record.get("supportClaims"), dict) or set(claims) != set(conditional) or any(
        claims.get(key) not in {True, False} for key in conditional
    ):
        reasons.append("support-claims-invalid")
        structural_blockers = True

    if set(disposition) != DISPOSITION_FIELDS:
        reasons.append("disposition-fields-invalid")
        structural_blockers = True
    if _bounded_text(disposition.get("evaluatorDisposition"), 80) is None:
        reasons.append("disposition-value-invalid")
        structural_blockers = True
    if disposition.get("acceptedForAccessibilityQualification") not in {True, False}:
        reasons.append("accessibility-disposition-invalid")
        structural_blockers = True
    if _bounded_text(disposition.get("notes"), 2000) is None:
        reasons.append("disposition-notes-invalid")
        structural_blockers = True

    environment = record.get("environment")
    if not isinstance(environment, dict):
        reasons.append("environment-missing")
        structural_blockers = True
    else:
        if set(environment) - ENVIRONMENT_FIELDS:
            reasons.append("environment-fields-invalid")
            structural_blockers = True
        platform_family = environment.get("platformFamily")
        if platform_family not in VALID_PLATFORM_FAMILIES:
            reasons.append("platform-family-invalid")
            structural_blockers = True

        operating_system = environment.get("operatingSystem")
        if (
            not isinstance(operating_system, dict)
            or set(operating_system) != {"name", "version"}
            or _bounded_text(operating_system.get("name"), 120) is None
            or _bounded_text(operating_system.get("version"), 120) is None
        ):
            reasons.append("operating-system-evidence-invalid")
            structural_blockers = True

        browser = environment.get("browser")
        if platform_family == "web":
            if (
                not isinstance(browser, dict)
                or set(browser) != {"name", "version"}
                or _bounded_text(browser.get("name"), 120) is None
                or _bounded_text(browser.get("version"), 120) is None
            ):
                reasons.append("browser-evidence-invalid")
                structural_blockers = True
        elif browser is not None and (
            not isinstance(browser, dict)
            or set(browser) != {"name", "version"}
            or _bounded_text(browser.get("name"), 120) is None
            or _bounded_text(browser.get("version"), 120) is None
        ):
            reasons.append("browser-evidence-invalid")
            structural_blockers = True

        if environment.get("physicalDevice") not in {True, False}:
            reasons.append("physical-device-field-invalid")
            structural_blockers = True

        assistive = environment.get("assistiveTechnologies")
        if not isinstance(assistive, list) or len(assistive) > 50:
            reasons.append("assistive-technology-inventory-invalid")
            structural_blockers = True
        else:
            seen_assistive: set[tuple[str, str, str]] = set()
            for item in assistive:
                if (
                    not isinstance(item, dict)
                    or set(item) != {"name", "version", "mode"}
                    or _bounded_text(item.get("name"), 120) is None
                    or _bounded_text(item.get("version"), 120) is None
                    or item.get("mode") not in VALID_ASSISTIVE_MODES
                ):
                    reasons.append("assistive-technology-inventory-invalid")
                    structural_blockers = True
                    continue
                key = (
                    item["name"],
                    item["version"],
                    item["mode"],
                )
                if key in seen_assistive:
                    reasons.append("duplicate-assistive-technology")
                    structural_blockers = True
                seen_assistive.add(key)

        if not _valid_reference_list(environment.get("evidenceReferences"), 100):
            reasons.append("environment-evidence-references-invalid")
            structural_blockers = True

    scenarios = record.get("scenarioResults")
    scenario_map: dict[str, dict[str, Any]] = {}
    duplicate_ids: set[str] = set()
    if isinstance(scenarios, list):
        for entry in scenarios:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                reasons.append("invalid-scenario-entry")
                continue
            scenario_id = entry["id"]
            if scenario_id in scenario_map:
                duplicate_ids.add(scenario_id)
            else:
                scenario_map[scenario_id] = entry
    else:
        reasons.append("scenario-results-missing")
    if duplicate_ids:
        reasons.append("duplicate-scenario-ids")

    required_base = set(plan.get("requiredScenarios", []))
    conditional_values = set(conditional.values())
    for scenario_id in required:
        entry = scenario_map.get(scenario_id)
        if entry is None:
            missing.append(scenario_id)
            continue
        result = entry.get("result")
        evidence = entry.get("evidenceReferences")
        if result == "fail":
            failed.append(scenario_id)
        elif result in (None, "not-tested"):
            missing.append(scenario_id)
        elif result == "not-applicable":
            if scenario_id in required_base:
                missing.append(scenario_id)
                reasons.append(f"required-scenario-cannot-be-not-applicable:{scenario_id}")
            elif scenario_id in conditional_values:
                missing.append(scenario_id)
                reasons.append(f"claimed-assistive-scenario-cannot-be-not-applicable:{scenario_id}")
        elif result == "pass":
            if not _valid_reference_list(evidence, 100) or not evidence:
                missing.append(scenario_id)
                reasons.append(f"passing-scenario-missing-evidence:{scenario_id}")
        else:
            missing.append(scenario_id)
            reasons.append(f"invalid-scenario-result:{scenario_id}")

    preferences = record.get("preferenceCoverage")
    required_preferences = plan.get("preferenceEvidence", {}).get("requiredPreferences", [])
    if not isinstance(preferences, dict):
        reasons.append("preference-coverage-missing")
    else:
        for preference in required_preferences:
            observation = preferences.get(preference)
            if not isinstance(observation, dict):
                reasons.append(f"preference-evidence-missing:{preference}")
                continue
            state = observation.get("state")
            evidence = observation.get("evidenceReferences")
            if state == "not-tested" or state is None:
                reasons.append(f"preference-not-tested:{preference}")
            elif state == "not-supported":
                if not _valid_reference_list(evidence, 25) or not evidence:
                    reasons.append(f"unsupported-preference-missing-evidence:{preference}")
            elif state in ("tested-active", "tested-inactive"):
                if not _valid_reference_list(evidence, 25) or not evidence:
                    reasons.append(f"tested-preference-missing-evidence:{preference}")
            else:
                reasons.append(f"invalid-preference-state:{preference}")

    unresolved_blocking = []
    issues = record.get("issues")
    if isinstance(issues, list):
        for issue in issues:
            if isinstance(issue, dict) and issue.get("severity") in BLOCKING_SEVERITIES and issue.get("resolved") is not True:
                unresolved_blocking.append(issue.get("summary", "unnamed issue"))
    else:
        reasons.append("issues-array-missing")
        structural_blockers = True
    if unresolved_blocking:
        reasons.append("unresolved-high-or-critical-issue")

    if failed:
        reasons.append("required-or-claimed-scenario-failed")
        return _result("failed", reasons, required=required, missing=missing, failed=failed)

    evidence_blockers = bool(
        structural_blockers
        or missing
        or duplicate_ids
        or unresolved_blocking
        or any(reason.startswith((
            "exact-source-",
            "source-revision-does-not-match",
            "source-tree-revision-does-not-match",
            "preference-",
            "unsupported-preference-",
            "tested-preference-",
            "invalid-preference-",
            "scenario-results-",
            "invalid-scenario-",
            "duplicate-scenario-",
        )) for reason in reasons)
    )
    if evidence_blockers or status == "superseded":
        return _result("blocked", reasons, required=required, missing=missing, failed=failed)

    if human_status != "accepted":
        reasons.append("human-review-acceptance-pending")
        return _result("review-ready", reasons, required=required, missing=missing, failed=failed)

    if review_mode not in {"human", "combined"}:
        reasons.append("automated-only-review-cannot-accept-accessibility-qualification")
        return _result("review-ready", reasons, required=required, missing=missing, failed=failed)

    if status != "passed" or disposition.get("acceptedForAccessibilityQualification") is not True:
        reasons.append("explicit-passed-record-and-accessibility-disposition-required")
        return _result("review-ready", reasons, required=required, missing=missing, failed=failed)

    return _result("accepted", reasons, required=required, missing=missing, failed=failed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Accessibility qualification evidence record JSON")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--expected-source-revision")
    parser.add_argument("--expected-source-tree-revision")
    args = parser.parse_args()

    result = evaluate_record(
        _load_json(args.record),
        _load_json(args.plan),
        expected_source_revision=args.expected_source_revision,
        expected_source_tree_revision=args.expected_source_tree_revision,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
