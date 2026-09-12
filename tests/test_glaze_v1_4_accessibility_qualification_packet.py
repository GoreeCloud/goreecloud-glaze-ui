from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "prepare_glaze_v1_4_accessibility_qualification_packet.py"
EVALUATOR_PATH = ROOT / "scripts" / "evaluate_glaze_v1_4_accessibility_qualification.py"

GENERATOR_SPEC = importlib.util.spec_from_file_location("prepare_glaze_v1_4_accessibility_qualification_packet", GENERATOR_PATH)
assert GENERATOR_SPEC and GENERATOR_SPEC.loader
generator = importlib.util.module_from_spec(GENERATOR_SPEC)
sys.modules[GENERATOR_SPEC.name] = generator
GENERATOR_SPEC.loader.exec_module(generator)

EVALUATOR_SPEC = importlib.util.spec_from_file_location("evaluate_glaze_v1_4_accessibility_qualification_packet_test", EVALUATOR_PATH)
assert EVALUATOR_SPEC and EVALUATOR_SPEC.loader
evaluator = importlib.util.module_from_spec(EVALUATOR_SPEC)
sys.modules[EVALUATOR_SPEC.name] = evaluator
EVALUATOR_SPEC.loader.exec_module(evaluator)

with (ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json").open(encoding="utf-8") as handle:
    PLAN = json.load(handle)

SOURCE = "1" * 40
TREE = "2" * 40


def prepared_record(**overrides):
    values = {
        "authority": "Authorized GoreeCloud accessibility reviewer",
        "review_mode": "combined",
        "source_revision": SOURCE,
        "source_tree_revision": TREE,
        "platform_family": "web",
        "os_name": "Qualification OS",
        "os_version": "1",
        "browser_name": "Qualification Browser",
        "browser_version": "1",
        "physical_device": True,
        "screen_reader_claimed": False,
        "voice_control_claimed": False,
        "switch_control_claimed": False,
        "observed_at": "2026-09-12T00:00:00Z",
    }
    values.update(overrides)
    return generator.build_record(**values)


class GlazeV14AccessibilityQualificationPacketTests(unittest.TestCase):
    def test_prepared_packet_is_exact_source_bound_and_blocked(self) -> None:
        record = prepared_record()
        self.assertEqual(record["target"]["sourceRevision"], SOURCE)
        self.assertEqual(record["target"]["sourceTreeRevision"], TREE)
        self.assertEqual(record["status"], "in-progress")
        self.assertEqual(record["reviewAuthority"]["humanReviewStatus"], "pending")
        self.assertEqual(record["disposition"]["evaluatorDisposition"], "blocked")
        self.assertFalse(record["disposition"]["acceptedForAccessibilityQualification"])
        self.assertFalse(record["disposition"]["acceptedForLifecycleGate"])
        result = evaluator.evaluate_record(record, PLAN, expected_source_revision=SOURCE, expected_source_tree_revision=TREE)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertFalse(result["acceptedForAccessibilityQualification"])
        self.assertFalse(result["acceptedForLifecycleGate"])

    def test_prepared_packet_never_fabricates_observation_evidence(self) -> None:
        record = prepared_record()
        self.assertEqual(record["environment"]["evidenceReferences"], [])
        for observation in record["preferenceCoverage"].values():
            self.assertEqual(observation["state"], "not-tested")
            self.assertEqual(observation["evidenceReferences"], [])
        for scenario in record["scenarioResults"]:
            self.assertIn(scenario["result"], {"not-tested", "not-applicable"})
            self.assertEqual(scenario["evidenceReferences"], [])

    def test_claimed_screen_reader_scenario_becomes_not_tested_not_applicable(self) -> None:
        record = prepared_record(screen_reader_claimed=True)
        scenario = next(item for item in record["scenarioResults"] if item["id"] == "screen-reader-semantics-and-announcements")
        self.assertEqual(scenario["result"], "not-tested")
        result = evaluator.evaluate_record(record, PLAN)
        self.assertEqual(result["evaluatorDisposition"], "blocked")
        self.assertIn("screen-reader-semantics-and-announcements", result["missingScenarioIds"])

    def test_unclaimed_assistive_scenarios_remain_not_applicable(self) -> None:
        record = prepared_record()
        conditional_ids = set(PLAN["claimConditionalScenarios"].values())
        for scenario in record["scenarioResults"]:
            if scenario["id"] in conditional_ids:
                self.assertEqual(scenario["result"], "not-applicable")

    def test_checklist_contains_exact_binding_and_required_scenarios(self) -> None:
        record = prepared_record(voice_control_claimed=True)
        checklist = generator.build_checklist(record)
        self.assertIn(SOURCE, checklist)
        self.assertIn(TREE, checklist)
        for scenario_id in PLAN["requiredScenarios"]:
            self.assertIn(scenario_id, checklist)
        self.assertIn("voice-control-purpose-and-operation", checklist)
        self.assertIn("acceptedForLifecycleGate: false", checklist)

    def test_zero_source_revision_is_rejected(self) -> None:
        with self.assertRaises(generator.PreparationError):
            prepared_record(source_revision="0" * 40)

    def test_browser_name_and_version_must_be_paired(self) -> None:
        with self.assertRaises(generator.PreparationError):
            prepared_record(browser_version=None)

    def test_output_path_must_stay_under_draft_root(self) -> None:
        with self.assertRaises(generator.PreparationError):
            generator.resolve_output_dir(ROOT / "evidence" / "v1.4" / "not-a-draft")

    def test_assertion_rejects_manual_acceptance_in_prepared_record(self) -> None:
        record = prepared_record()
        record["disposition"]["acceptedForAccessibilityQualification"] = True
        with self.assertRaises(generator.PreparationError):
            generator.assert_prepared_fail_closed(record)

    def test_generator_does_not_mutate_template(self) -> None:
        template = generator.load_json(generator.TEMPLATE)
        original = copy.deepcopy(template)
        prepared_record()
        self.assertEqual(generator.load_json(generator.TEMPLATE), original)


if __name__ == "__main__":
    unittest.main()
