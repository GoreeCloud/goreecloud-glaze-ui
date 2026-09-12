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
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ZERO_SHA = "0" * 40
BLOCKING_SEVERITIES = {"high", "critical"}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


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

    target = record.get("target", {}) if isinstance(record.get("target"), dict) else {}
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
    review = record.get("reviewAuthority", {}) if isinstance(record.get("reviewAuthority"), dict) else {}
    human_status = review.get("humanReviewStatus")
    review_mode = review.get("mode")
    if status == "failed" or human_status == "rejected":
        reasons.append("record-or-human-review-explicitly-failed")
        return _result("failed", reasons, required=required, missing=missing, failed=failed)
    if status == "superseded":
        reasons.append("record-is-superseded")

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
            if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
                missing.append(scenario_id)
                reasons.append(f"passing-scenario-missing-evidence:{scenario_id}")
        else:
            missing.append(scenario_id)
            reasons.append(f"invalid-scenario-result:{scenario_id}")

    for claim_key, scenario_id in conditional.items():
        if claims.get(claim_key) is not True:
            entry = scenario_map.get(scenario_id)
            if entry is not None and entry.get("result") not in ("not-applicable", "not-tested"):
                reasons.append(f"unclaimed-assistive-scenario-recorded:{scenario_id}")

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
                if not isinstance(evidence, list) or not evidence:
                    reasons.append(f"unsupported-preference-missing-evidence:{preference}")
            elif state in ("tested-active", "tested-inactive"):
                if not isinstance(evidence, list) or not evidence:
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
    if unresolved_blocking:
        reasons.append("unresolved-high-or-critical-issue")

    if failed:
        reasons.append("required-or-claimed-scenario-failed")
        return _result("failed", reasons, required=required, missing=missing, failed=failed)

    evidence_blockers = bool(
        missing
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
