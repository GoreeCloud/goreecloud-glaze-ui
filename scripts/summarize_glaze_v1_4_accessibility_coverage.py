#!/usr/bin/env python3
"""Summarize multiple Glaze UI V1.4 accessibility evidence records without promoting them.

This tool supports governed review of real qualification records. It detects exact-source
mismatches and duplicate environment/support-claim coverage, delegates each record to the
canonical evaluator, and produces a non-authorizing summary. It does not define a complete
browser/OS/AT matrix and cannot grant accessibility, browser-matrix, consumer, or lifecycle
acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluate_glaze_v1_4_accessibility_qualification import _load_json, evaluate_record

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json"


def _environment_key(record: dict[str, Any]) -> str:
    environment = record.get("environment", {}) if isinstance(record.get("environment"), dict) else {}
    os_value = environment.get("operatingSystem", {}) if isinstance(environment.get("operatingSystem"), dict) else {}
    browser = environment.get("browser", {}) if isinstance(environment.get("browser"), dict) else {}
    assistive = environment.get("assistiveTechnologies", [])
    if not isinstance(assistive, list):
        assistive = []
    claims = record.get("supportClaims", {}) if isinstance(record.get("supportClaims"), dict) else {}
    normalized = {
        "platformFamily": environment.get("platformFamily"),
        "operatingSystem": {"name": os_value.get("name"), "version": os_value.get("version")},
        "browser": {"name": browser.get("name"), "version": browser.get("version")},
        "physicalDevice": environment.get("physicalDevice"),
        "assistiveTechnologies": sorted(str(item) for item in assistive),
        "supportClaims": {key: claims.get(key) for key in sorted(claims)},
    }
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def summarize_records(
    records: list[dict[str, Any]],
    plan: dict[str, Any],
    *,
    expected_source_revision: str,
    expected_source_tree_revision: str,
) -> dict[str, Any]:
    reasons: list[str] = []
    results: list[dict[str, Any]] = []
    seen_environment_keys: dict[str, int] = {}

    if not records:
        reasons.append("no-qualification-records-supplied")

    for index, record in enumerate(records):
        target = record.get("target", {}) if isinstance(record.get("target"), dict) else {}
        if target.get("sourceRevision") != expected_source_revision:
            reasons.append(f"record-{index}:source-revision-mismatch")
        if target.get("sourceTreeRevision") != expected_source_tree_revision:
            reasons.append(f"record-{index}:source-tree-revision-mismatch")

        key = _environment_key(record)
        if key in seen_environment_keys:
            reasons.append(
                f"duplicate-environment-support-coverage:record-{seen_environment_keys[key]}:record-{index}"
            )
        else:
            seen_environment_keys[key] = index

        evaluation = evaluate_record(
            record,
            plan,
            expected_source_revision=expected_source_revision,
            expected_source_tree_revision=expected_source_tree_revision,
        )
        results.append(
            {
                "recordIndex": index,
                "evaluatorDisposition": evaluation["evaluatorDisposition"],
                "acceptedForAccessibilityQualification": evaluation[
                    "acceptedForAccessibilityQualification"
                ],
                "acceptedForLifecycleGate": False,
                "reasons": evaluation["reasons"],
            }
        )

    dispositions = [item["evaluatorDisposition"] for item in results]
    if "failed" in dispositions:
        coverage_disposition = "failed"
    elif reasons or "blocked" in dispositions or not records:
        coverage_disposition = "blocked"
    else:
        coverage_disposition = "review-ready"

    return {
        "coverageDisposition": coverage_disposition,
        "recordCount": len(records),
        "uniqueEnvironmentSupportCount": len(seen_environment_keys),
        "recordDispositionCounts": {
            disposition: dispositions.count(disposition)
            for disposition in ("blocked", "review-ready", "failed", "accepted")
        },
        "reasons": sorted(set(reasons)),
        "records": results,
        "acceptedForAccessibilityQualification": False,
        "acceptedForBrowserMatrixQualification": False,
        "acceptedForConsumerConformance": False,
        "acceptedForLifecycleGate": False,
        "matrixCompletenessEstablished": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="+", type=Path)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--source-tree-revision", required=True)
    args = parser.parse_args()

    plan = _load_json(args.plan)
    records = [_load_json(path) for path in args.records]
    print(
        json.dumps(
            summarize_records(
                records,
                plan,
                expected_source_revision=args.source_revision,
                expected_source_tree_revision=args.source_tree_revision,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
