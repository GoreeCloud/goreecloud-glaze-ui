#!/usr/bin/env python3
"""Tests for the fail-closed GLAZE UI V1.3 qualification draft helper."""
from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODULE_PATH=ROOT/"scripts"/"prepare_glaze_v1_3_qualification_record.py"
SPEC=importlib.util.spec_from_file_location("prepare_glaze_v1_3_qualification_record",MODULE_PATH); assert SPEC and SPEC.loader
module=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(module)
REVISION="1"*40; CANDIDATE="2"*40; OBSERVED_AT="2026-09-07T00:00:00Z"

class QualificationDraftHelperTests(unittest.TestCase):
    def build(self, alias):
        kwargs={"observed_at":OBSERVED_AT}
        if alias=="stable-activation": kwargs["qualified_candidate_source_revision"]=CANDIDATE
        return module.build_record(alias,"Qualification Reviewer",REVISION,platform="test-platform",device="test-device",**kwargs)

    def test_all_six_workstreams_initialize_fail_closed(self):
        self.assertEqual(len(module.WORKSTREAMS),6); self.assertEqual(set(module.WORKSTREAMS),set(module.DEFAULT_REVIEW_MODES))
        for alias,workstream_id in module.WORKSTREAMS.items():
            with self.subTest(alias=alias):
                record=self.build(alias)
                self.assertEqual(record["schema_version"],2); self.assertEqual(record["workstream_id"],workstream_id); self.assertEqual(record["target"]["source_revision"],REVISION); self.assertEqual(record["status"],"in_progress"); self.assertEqual(record["review_authority"]["mode"],module.DEFAULT_REVIEW_MODES[alias]); self.assertFalse(record["disposition"]["accepted_for_lifecycle_gate"]); self.assertNotIn("quality_review",record); self.assertTrue(record["environment"]["draft"]); self.assertTrue(record["evidence_references"][0].startswith("DRAFT:")); self.assertTrue(any(not issue["resolved"] for issue in record["issues"]))

    def test_stable_draft_requires_candidate_provenance_and_remains_unaccepted(self):
        with self.assertRaises(module.PreparationError): module.build_record("stable-activation","Reviewer",REVISION,observed_at=OBSERVED_AT)
        record=module.build_record("stable-activation","Reviewer",REVISION,qualified_candidate_source_revision=CANDIDATE,observed_at=OBSERVED_AT)
        env=record["environment"]
        self.assertEqual(record["review_authority"]["mode"],"combined"); self.assertEqual(env["qualified_candidate_source_revision"],CANDIDATE); self.assertEqual(env["stable_promotion_source_revision"],REVISION); self.assertEqual(env["candidate_lifecycle_observed"],"draft-unverified"); self.assertFalse(env["equivalence_review_completed"]); self.assertFalse(env["import_closure_validated"]); self.assertFalse(env["rollback_verified"]); self.assertFalse(record["disposition"]["accepted_for_lifecycle_gate"])

    def test_candidate_provenance_arg_is_rejected_for_pre_candidate_tracks(self):
        with self.assertRaises(module.PreparationError): module.build_record("human-optical","Reviewer",REVISION,qualified_candidate_source_revision=CANDIDATE,observed_at=OBSERVED_AT)

    def test_human_optical_draft_does_not_claim_quality_review(self):
        record=self.build("human-optical"); self.assertNotIn("quality_review",record); self.assertIn("55",record["issues"][0]["summary"])

    def test_physical_tracks_require_combined_mode_and_reject_simulation_substitution(self):
        device=self.build("physical-device"); performance=self.build("physical-performance")
        self.assertEqual(device["review_authority"]["mode"],"combined"); self.assertEqual(performance["review_authority"]["mode"],"combined"); self.assertIn("Simulation",device["issues"][0]["summary"]); self.assertIn("simulated",performance["issues"][0]["summary"])

    def test_revision_validation_rejects_non_immutable_values(self):
        for value in ("main","HEAD","ABC"*14,"a"*39,"g"*40):
            with self.subTest(value=value):
                with self.assertRaises(module.PreparationError): module.validate_revision(value)
        self.assertEqual(module.validate_revision(REVISION),REVISION)

    def test_output_is_restricted_to_nonaccepted_draft_tree(self):
        allowed=module.resolve_output(Path("artifacts/v1.3/qualification-drafts/human-optical.json")); self.assertEqual(allowed.parent,module.DRAFT_ROOT)
        with self.assertRaises(module.PreparationError): module.resolve_output(Path("evidence/v1.3/human-optical.json"))
        with self.assertRaises(module.PreparationError): module.resolve_output(Path("artifacts/v1.3/qualification-drafts/not-json.txt"))

    def test_empty_operator_is_rejected(self):
        with self.assertRaises(module.PreparationError): module.build_record("human-optical","   ",REVISION,observed_at=OBSERVED_AT)

if __name__=="__main__": unittest.main()
