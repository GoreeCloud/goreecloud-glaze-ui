from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "scripts" / "evaluate_glaze_v1_4_accessibility_qualification.py"
SPEC = importlib.util.spec_from_file_location(
    "evaluate_glaze_v1_4_accessibility_qualification", EVALUATOR_PATH
)
assert SPEC and SPEC.loader
evaluator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = evaluator
SPEC.loader.exec_module(evaluator)

with (
    ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json"
).open(encoding="utf-8") as handle:
    PLAN = json.load(handle)
with (
    ROOT
    / "evidence"
    / "v1.4"
    / "templates"
    / "accessibility-qualification-record.candidate.json"
).open(encoding="utf-8") as handle:
    TEMPLATE = json.load(handle)

SOURCE = "a" * 40
TREE = "b" * 40


def accepted_record() -> dict:
    record = copy.deepcopy(TEMPLATE)
    record["target"]["sourceRevision"] = SOURCE
    record["target"]["sourceTreeRevision"] = TREE
    record["status"] = "passed"
    record["observedAt"] = "2026-09-12T00:00:00Z"
    record["reviewAuthority"] = {
        "mode": "combined",
        "authority": "Authorized GoreeCloud accessibility reviewer plus repository validation",
        "humanReviewStatus": "accepted",
    }
    record["environment"] = {
        "platformFamily": "web",
        "operatingSystem": {"name": "Test OS", "version": "1"},
        "browser": {"name": "Test Browser", "version": "1"},
        "physicalDevice": True,
        "assistiveTechnologies": [
            {"name": "Keyboard", "version": "system", "mode": "keyboard"}
        ],
        "evidenceReferences": ["artifact:environment.json"],
    }
    for observation in record["preferenceCoverage"].values():
        observation["state"] = "tested-active"
        observation["evidenceReferences"] = ["artifact:preference.json"]
    for scenario in record["scenarioResults"]:
        if scenario["id"] in PLAN["requiredScenarios"]:
            scenario["result"] = "pass"
            scenario["evidenceReferences"] = [f"artifact:{scenario['id']}.json"]
        else:
            scenario["result"] = "not-applicable"
            scenario["evidenceReferences"] = []
    record["issues"] = []
    record["disposition"] = {
        "evaluatorDisposition": "accepted",
        "acceptedForAccessibilityQualification": True,
        "acceptedForLifecycleGate": False,
        "notes": "Explicit bounded accessibility qualification acceptance only.",
    }
    return record


class GlazeV14AccessibilityQualificationTests(unittest.TestCase):
    def test_draft_template_is_blocked(self) -> None:
        result = evaluator.evaluate_record(copy.deepcopy(TEMPLATE), PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertFalse(result["acceptedForAccessibilityQualification"])
        self.assertFalse(result["acceptedForLifecycleGate"])

    def test_complete_human_accepted_record_is_accepted_only_for_accessibility_slice(
        self,
    ) -> None:
        result = evaluator.evaluate_record(
            accepted_record(),
            PLAN,
            expected_source_revision=SOURCE,
            expected_source_tree_revision=TREE,
        )
        self.assertEqual(result["evaluatorDisposition"], "accepted")
        self.assertTrue(result["acceptedForAccessibilityQualification"])
        self.assertFalse(result["acceptedForLifecycleGate"])

    def test_hidden_top_level_field_is_blocked(self) -> None:
        record = accepted_record()
        record["stableApproved"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("record-fields-invalid", result["reasons"])

    def test_hidden_target_override_is_blocked(self) -> None:
        record = accepted_record()
        record["target"]["productionAccepted"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("target-fields-invalid", result["reasons"])

    def test_hidden_review_authority_field_is_blocked(self) -> None:
        record = accepted_record()
        record["reviewAuthority"]["autoAccepted"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("review-authority-fields-invalid", result["reasons"])

    def test_hidden_disposition_field_is_blocked(self) -> None:
        record = accepted_record()
        record["disposition"]["acceptedForStable"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("disposition-fields-invalid", result["reasons"])

    def test_hidden_support_claim_is_blocked(self) -> None:
        record = accepted_record()
        record["supportClaims"]["automaticConformanceClaimed"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("support-claims-invalid", result["reasons"])

    def test_hidden_scenario_field_is_blocked(self) -> None:
        record = accepted_record()
        record["scenarioResults"][0]["acceptedForStable"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("invalid-scenario-entry", result["reasons"])

    def test_hidden_preference_observation_field_is_blocked(self) -> None:
        record = accepted_record()
        record["preferenceCoverage"]["reducedMotion"]["autoAccepted"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn(
            "preference-evidence-shape-invalid:reducedMotion", result["reasons"]
        )

    def test_unknown_preference_key_is_blocked(self) -> None:
        record = accepted_record()
        record["preferenceCoverage"]["futureAutoQualification"] = {
            "state": "tested-active",
            "evidenceReferences": ["artifact:future.json"],
        }
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("preference-coverage-fields-invalid", result["reasons"])

    def test_hidden_issue_field_is_blocked(self) -> None:
        record = accepted_record()
        record["issues"] = [
            {
                "summary": "Informational issue",
                "severity": "info",
                "resolved": True,
                "reference": "issue:info",
                "qualificationOverride": True,
            }
        ]
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("invalid-issue-entry", result["reasons"])

    def test_oversized_scenario_and_issue_arrays_are_blocked(self) -> None:
        scenario_record = accepted_record()
        scenario_record["scenarioResults"] = [
            copy.deepcopy(scenario_record["scenarioResults"][0]) for _ in range(101)
        ]
        scenario_result = evaluator.evaluate_record(scenario_record, PLAN)
        self.assertEqual(scenario_result["evaluatorDisposition"], "blocked")
        self.assertIn("scenario-results-invalid", scenario_result["reasons"])

        issue_record = accepted_record()
        issue_record["issues"] = [
            {
                "summary": f"issue-{index}",
                "severity": "info",
                "resolved": True,
                "reference": f"issue:{index}",
            }
            for index in range(101)
        ]
        issue_result = evaluator.evaluate_record(issue_record, PLAN)
        self.assertEqual(issue_result["evaluatorDisposition"], "blocked")
        self.assertIn("issues-array-invalid", issue_result["reasons"])

    def test_observation_time_without_timezone_is_blocked(self) -> None:
        record = accepted_record()
        record["observedAt"] = "2026-09-12T00:00:00"
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("observation-time-invalid", result["reasons"])

    def test_observation_time_with_surrounding_whitespace_is_blocked(self) -> None:
        record = accepted_record()
        record["observedAt"] = " 2026-09-12T00:00:00Z"
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("observation-time-invalid", result["reasons"])

    def test_environment_reference_with_surrounding_whitespace_is_blocked(self) -> None:
        record = accepted_record()
        record["environment"]["evidenceReferences"] = [" artifact:environment.json"]
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("environment-evidence-references-invalid", result["reasons"])

    def test_passing_scenario_reference_with_surrounding_whitespace_is_blocked(self) -> None:
        record = accepted_record()
        for scenario in record["scenarioResults"]:
            if scenario["id"] == "keyboard-focus-order":
                scenario["evidenceReferences"] = [" artifact:keyboard-focus-order.json"]
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("keyboard-focus-order", result["missingScenarioIds"])

    def test_web_record_without_browser_identity_is_blocked(self) -> None:
        record = accepted_record()
        record["environment"].pop("browser")
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("browser-evidence-invalid", result["reasons"])
        self.assertFalse(result["acceptedForAccessibilityQualification"])

    def test_environment_with_unknown_field_is_blocked(self) -> None:
        record = accepted_record()
        record["environment"]["automaticQualification"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("environment-fields-invalid", result["reasons"])

    def test_duplicate_assistive_technology_entry_is_blocked(self) -> None:
        record = accepted_record()
        record["environment"]["assistiveTechnologies"].append(
            copy.deepcopy(record["environment"]["assistiveTechnologies"][0])
        )
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("duplicate-assistive-technology", result["reasons"])

    def test_invalid_assistive_technology_mode_is_blocked(self) -> None:
        record = accepted_record()
        record["environment"]["assistiveTechnologies"][0]["mode"] = "auto-accepted"
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("assistive-technology-inventory-invalid", result["reasons"])

    def test_duplicate_environment_evidence_reference_is_blocked(self) -> None:
        record = accepted_record()
        record["environment"]["evidenceReferences"].append(
            record["environment"]["evidenceReferences"][0]
        )
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("environment-evidence-references-invalid", result["reasons"])

    def test_machine_complete_record_with_pending_human_review_is_review_ready(
        self,
    ) -> None:
        record = accepted_record()
        record["status"] = "review-ready"
        record["reviewAuthority"]["humanReviewStatus"] = "pending"
        record["disposition"]["evaluatorDisposition"] = "review-ready"
        record["disposition"]["acceptedForAccessibilityQualification"] = False
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "review-ready")
        self.assertIn("human-review-acceptance-pending", result["reasons"])

    def test_missing_required_scenario_is_blocked(self) -> None:
        record = accepted_record()
        record["scenarioResults"] = [
            scenario
            for scenario in record["scenarioResults"]
            if scenario["id"] != "keyboard-focus-order"
        ]
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("keyboard-focus-order", result["missingScenarioIds"])

    def test_claimed_screen_reader_requires_real_screen_reader_scenario(self) -> None:
        record = accepted_record()
        record["supportClaims"]["screenReaderClaimed"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn(
            "screen-reader-semantics-and-announcements", result["missingScenarioIds"]
        )

    def test_required_scenario_failure_fails_qualification(self) -> None:
        record = accepted_record()
        for scenario in record["scenarioResults"]:
            if scenario["id"] == "forced-colors-system-color-path":
                scenario["result"] = "fail"
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "failed")
        self.assertIn("forced-colors-system-color-path", result["failedScenarioIds"])

    def test_source_mismatch_is_blocked(self) -> None:
        result = evaluator.evaluate_record(
            accepted_record(),
            PLAN,
            expected_source_revision="c" * 40,
            expected_source_tree_revision=TREE,
        )
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn(
            "source-revision-does-not-match-expected-revision", result["reasons"]
        )

    def test_unresolved_high_issue_is_blocked(self) -> None:
        record = accepted_record()
        record["issues"] = [
            {
                "summary": "Blocking accessibility defect",
                "severity": "high",
                "resolved": False,
                "reference": "issue:1",
            }
        ]
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("unresolved-high-or-critical-issue", result["reasons"])

    def test_lifecycle_gate_claim_is_failed_closed(self) -> None:
        record = accepted_record()
        record["disposition"]["acceptedForLifecycleGate"] = True
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "failed")
        self.assertFalse(result["acceptedForLifecycleGate"])
        self.assertIn(
            "accessibility-evidence-may-not-grant-lifecycle-gate", result["reasons"]
        )

    def test_automated_only_review_cannot_accept(self) -> None:
        record = accepted_record()
        record["reviewAuthority"]["mode"] = "automated"
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "review-ready")
        self.assertFalse(result["acceptedForAccessibilityQualification"])

    def test_evaluator_does_not_mutate_record(self) -> None:
        record = accepted_record()
        original = copy.deepcopy(record)
        evaluator.evaluate_record(record, PLAN)
        self.assertEqual(record, original)


if __name__ == "__main__":
    unittest.main()
