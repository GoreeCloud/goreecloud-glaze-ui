#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from summarize_glaze_v1_4_accessibility_coverage import summarize_records

SOURCE = "a" * 40
TREE = "b" * 40
PLAN = json.loads(
    (ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json").read_text(
        encoding="utf-8"
    )
)
TEMPLATE = json.loads(
    (ROOT / "evidence" / "v1.4" / "templates" / "accessibility-qualification-record.candidate.json").read_text(
        encoding="utf-8"
    )
)


def record() -> dict:
    value = copy.deepcopy(TEMPLATE)
    value["target"]["sourceRevision"] = SOURCE
    value["target"]["sourceTreeRevision"] = TREE
    return value


class AccessibilityCoverageSummaryTests(unittest.TestCase):
    def test_prepared_blocked_record_cannot_promote_coverage(self):
        summary = summarize_records(
            [record()],
            PLAN,
            expected_source_revision=SOURCE,
            expected_source_tree_revision=TREE,
        )
        self.assertEqual(summary["coverageDisposition"], "blocked")
        self.assertFalse(summary["acceptedForAccessibilityQualification"])
        self.assertFalse(summary["acceptedForBrowserMatrixQualification"])
        self.assertFalse(summary["acceptedForConsumerConformance"])
        self.assertFalse(summary["acceptedForLifecycleGate"])
        self.assertFalse(summary["matrixCompletenessEstablished"])

    def test_duplicate_environment_and_support_claim_coverage_blocks_summary(self):
        summary = summarize_records(
            [record(), record()],
            PLAN,
            expected_source_revision=SOURCE,
            expected_source_tree_revision=TREE,
        )
        self.assertEqual(summary["coverageDisposition"], "blocked")
        self.assertTrue(any(reason.startswith("duplicate-environment-support-coverage") for reason in summary["reasons"]))
        self.assertEqual(summary["uniqueEnvironmentSupportCount"], 1)

    def test_source_or_tree_mismatch_is_explicit_blocker(self):
        wrong = record()
        wrong["target"]["sourceRevision"] = "c" * 40
        summary = summarize_records(
            [wrong],
            PLAN,
            expected_source_revision=SOURCE,
            expected_source_tree_revision=TREE,
        )
        self.assertEqual(summary["coverageDisposition"], "blocked")
        self.assertIn("record-0:source-revision-mismatch", summary["reasons"])

    def test_even_individually_accepted_records_do_not_create_matrix_or_lifecycle_acceptance(self):
        accepted = {
            "evaluatorDisposition": "accepted",
            "acceptedForAccessibilityQualification": True,
            "acceptedForLifecycleGate": False,
            "reasons": [],
        }
        with patch(
            "summarize_glaze_v1_4_accessibility_coverage.evaluate_record",
            return_value=accepted,
        ):
            summary = summarize_records(
                [record()],
                PLAN,
                expected_source_revision=SOURCE,
                expected_source_tree_revision=TREE,
            )
        self.assertEqual(summary["coverageDisposition"], "review-ready")
        self.assertEqual(summary["recordDispositionCounts"]["accepted"], 1)
        self.assertFalse(summary["acceptedForAccessibilityQualification"])
        self.assertFalse(summary["acceptedForBrowserMatrixQualification"])
        self.assertFalse(summary["acceptedForLifecycleGate"])
        self.assertFalse(summary["matrixCompletenessEstablished"])

    def test_failed_individual_record_fails_coverage_summary(self):
        failed = {
            "evaluatorDisposition": "failed",
            "acceptedForAccessibilityQualification": False,
            "acceptedForLifecycleGate": False,
            "reasons": ["record-or-human-review-explicitly-failed"],
        }
        with patch(
            "summarize_glaze_v1_4_accessibility_coverage.evaluate_record",
            return_value=failed,
        ):
            summary = summarize_records(
                [record()],
                PLAN,
                expected_source_revision=SOURCE,
                expected_source_tree_revision=TREE,
            )
        self.assertEqual(summary["coverageDisposition"], "failed")


if __name__ == "__main__":
    unittest.main()
