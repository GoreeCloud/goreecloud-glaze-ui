#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

from report_glaze_v1_3_qualification_readiness import build_report


REVISION_A = "a" * 40
REVISION_B = "b" * 40
WORKSTREAM = "human-optical-and-icon-collision-qualification"


class ReadinessReporterTests(unittest.TestCase):
    def make_root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "contracts" / "v1.3").mkdir(parents=True)
        (root / "evidence" / "v1.3").mkdir(parents=True)
        matrix = {
            "schemaVersion": 1,
            "product": "GLAZE UI V1.3",
            "targetVersion": "1.3.0-candidate",
            "lifecycle": "planned",
            "sourceStable": "1.2.0",
            "workstreams": [
                {
                    "id": WORKSTREAM,
                    "title": "Human optical qualification",
                    "mode": "human",
                    "blockingForLifecyclePromotion": True,
                    "requiredEvidence": ["authorized-review record", "light appearance review"],
                }
            ],
        }
        (root / "contracts" / "v1.3" / "qualification-matrix.json").write_text(
            json.dumps(matrix), encoding="utf-8"
        )
        return root

    def write_record(self, root: Path, name: str, revision: str, status: str = "passed", accepted: bool = True) -> None:
        record = {
            "schema_version": 1,
            "workstream_id": WORKSTREAM,
            "target": {
                "product": "GLAZE UI V1.3",
                "target_version": "1.3.0-candidate",
                "source_revision": revision,
            },
            "status": status,
            "observed_at": "2026-09-07T12:00:00Z",
            "review_authority": {"mode": "human", "authority": "authorized reviewer"},
            "evidence_references": ["evidence://one", "evidence://two"],
            "disposition": {
                "accepted_for_lifecycle_gate": accepted,
                "notes": "fixture",
            },
        }
        (root / "evidence" / "v1.3" / name).write_text(json.dumps(record), encoding="utf-8")

    def test_no_evidence_remains_blocked_and_non_promotional(self) -> None:
        root = self.make_root()
        report = build_report(root, REVISION_A)
        self.assertFalse(report["all_blocking_workstreams_ready_for_exact_revision"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["consumer_eligible"])
        self.assertEqual(report["workstreams"][0]["record_count"], 0)

    def test_exact_revision_pass_is_reported_ready_but_not_promoted(self) -> None:
        root = self.make_root()
        self.write_record(root, "optical.json", REVISION_A)
        report = build_report(root, REVISION_A)
        self.assertTrue(report["workstreams"][0]["exact_revision_ready"])
        self.assertTrue(report["all_blocking_workstreams_ready_for_exact_revision"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["consumer_eligible"])

    def test_conflicting_active_revisions_fail_closed(self) -> None:
        root = self.make_root()
        self.write_record(root, "optical-a.json", REVISION_A)
        self.write_record(root, "optical-b.json", REVISION_B)
        report = build_report(root, REVISION_A)
        workstream = report["workstreams"][0]
        self.assertTrue(workstream["conflicting_source_revisions"])
        self.assertTrue(workstream["multiple_active_accepted_passes"])
        self.assertFalse(workstream["exact_revision_ready"])
        self.assertTrue(report["has_evidence_conflicts"])
        self.assertFalse(report["all_blocking_workstreams_ready_for_exact_revision"])

    def test_invalid_pass_disposition_is_reported_invalid(self) -> None:
        root = self.make_root()
        self.write_record(root, "invalid.json", REVISION_A, status="passed", accepted=False)
        report = build_report(root, REVISION_A)
        self.assertTrue(report["has_invalid_records"])
        self.assertFalse(report["all_blocking_workstreams_ready_for_exact_revision"])
        self.assertTrue(any("accepted_for_lifecycle_gate=true" in item for item in report["invalid_records"]))


if __name__ == "__main__":
    unittest.main()
