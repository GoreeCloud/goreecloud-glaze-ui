#!/usr/bin/env python3
"""Tests for the fail-closed GLAZE UI V1.3 qualification draft helper."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "prepare_glaze_v1_3_qualification_record.py"
SPEC = importlib.util.spec_from_file_location("prepare_glaze_v1_3_qualification_record", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

REVISION = "1" * 40
OBSERVED_AT = "2026-09-07T00:00:00Z"


class QualificationDraftHelperTests(unittest.TestCase):
    def test_all_six_workstreams_initialize_fail_closed(self) -> None:
        self.assertEqual(len(module.WORKSTREAMS), 6)
        for alias, workstream_id in module.WORKSTREAMS.items():
            with self.subTest(alias=alias):
                record = module.build_record(
                    alias,
                    "Qualification Reviewer",
                    REVISION,
                    platform="test-platform",
                    device="test-device",
                    observed_at=OBSERVED_AT,
                )
                self.assertEqual(record["schema_version"], 2)
                self.assertEqual(record["workstream_id"], workstream_id)
                self.assertEqual(record["target"]["product"], "GLAZE UI V1.3")
                self.assertEqual(record["target"]["target_version"], "1.3.0-candidate")
                self.assertEqual(record["target"]["source_revision"], REVISION)
                self.assertEqual(record["status"], "in_progress")
                self.assertFalse(record["disposition"]["accepted_for_lifecycle_gate"])
                self.assertNotIn("quality_review", record)
                self.assertTrue(record["environment"]["draft"])
                self.assertTrue(record["evidence_references"][0].startswith("DRAFT:"))
                self.assertTrue(any(not issue["resolved"] for issue in record["issues"]))

    def test_human_optical_draft_does_not_claim_55_rule_review(self) -> None:
        record = module.build_record(
            "human-optical",
            "Optical Reviewer",
            REVISION,
            observed_at=OBSERVED_AT,
        )
        self.assertNotIn("quality_review", record)
        self.assertIn("55 rules", record["issues"][0]["summary"])
        self.assertEqual(record["status"], "in_progress")
        self.assertFalse(record["disposition"]["accepted_for_lifecycle_gate"])

    def test_physical_tracks_explicitly_reject_simulation_substitution(self) -> None:
        device = module.build_record("physical-device", "Device Reviewer", REVISION, observed_at=OBSERVED_AT)
        performance = module.build_record("physical-performance", "Performance Reviewer", REVISION, observed_at=OBSERVED_AT)
        self.assertIn("Simulation", device["issues"][0]["summary"])
        self.assertIn("simulated", performance["issues"][0]["summary"])

    def test_stable_activation_draft_grants_no_promotion(self) -> None:
        record = module.build_record("stable-activation", "Release Reviewer", REVISION, observed_at=OBSERVED_AT)
        notes = record["disposition"]["notes"]
        self.assertIn("No lifecycle promotion", notes)
        self.assertIn("Stable activation", record["issues"][0]["summary"])
        self.assertFalse(record["disposition"]["accepted_for_lifecycle_gate"])

    def test_revision_validation_rejects_non_immutable_values(self) -> None:
        for value in ("main", "HEAD", "ABC" * 14, "a" * 39, "g" * 40):
            with self.subTest(value=value):
                with self.assertRaises(module.PreparationError):
                    module.validate_revision(value)
        self.assertEqual(module.validate_revision(REVISION), REVISION)

    def test_output_is_restricted_to_nonaccepted_draft_tree(self) -> None:
        allowed = module.resolve_output(Path("artifacts/v1.3/qualification-drafts/human-optical.json"))
        self.assertEqual(allowed.parent, module.DRAFT_ROOT)
        with self.assertRaises(module.PreparationError):
            module.resolve_output(Path("evidence/v1.3/human-optical.json"))
        with self.assertRaises(module.PreparationError):
            module.resolve_output(Path("artifacts/v1.3/qualification-drafts/not-json.txt"))

    def test_empty_operator_is_rejected(self) -> None:
        with self.assertRaises(module.PreparationError):
            module.build_record("human-optical", "   ", REVISION, observed_at=OBSERVED_AT)


if __name__ == "__main__":
    unittest.main()
