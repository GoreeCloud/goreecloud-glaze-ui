from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_glaze_v1_4_browser_capabilities.py"
SPEC = importlib.util.spec_from_file_location("validate_glaze_v1_4_browser_capabilities", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

with (ROOT / "contracts" / "v1.4" / "browser-capabilities.candidate.json").open(encoding="utf-8") as handle:
    BASE = json.load(handle)


class GlazeV14BrowserCapabilityTests(unittest.TestCase):
    def test_candidate_contract_passes(self) -> None:
        validator.validate_contract(copy.deepcopy(BASE))

    def test_stable_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["releaseLifecycle"] = "stable"
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_consumer_eligibility_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["consumerEligible"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_user_agent_sniffing_permission_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["detectionPolicy"]["userAgentSniffingAllowed"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_hardware_fingerprinting_permission_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["detectionPolicy"]["hardwareFingerprintingAllowed"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_environmental_sampling_must_never_auto_declare(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["automaticCapabilityDetection"]["neverAutoDeclare"].remove("environmental-sampling")
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_accessibility_recommendation_cannot_be_qualification_evidence(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["accessibilityPreferenceDetection"]["recommendationIsQualificationEvidence"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_remote_asset_requirement_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["privacyBoundary"]["requiresRemoteAssets"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_result_transmission_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["qualificationHarness"]["transmitsResults"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_browser_matrix_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["qualificationHarness"]["browserMatrixQualificationEstablished"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)


if __name__ == "__main__":
    unittest.main()
